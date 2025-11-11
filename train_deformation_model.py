#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
幕布形变识别模型训练脚本
========================

概述
----
该脚本基于 PyTorch，读取 `collect_deformation_samples.py` 导出的样本目录，
训练一个轻量级 U-Net 模型，将撞击形变图像映射为撞击热力图，并同时回归像素坐标。

数据组织约定
------------
dataset/
├── raw/
│   └── 20250101/
│       └── game_0001_ball_001_20250101_120000/
│           ├── pre_0.png
│           ├── pre_1.png
│           ├── impact.png        # 必填
│           ├── diff.png          # 推荐
│           ├── label.json        # {"coord": {"x": .., "y": ..}, "quality": "manual"}
│           └── meta.json
└── processed/                    # 可选，用于放置清洗后的样本

快速开始
--------
    pip install torch torchvision
    python train_deformation_model.py \
        --data-root dataset/raw \
        --only-manual \
        --epochs 30 \
        --batch-size 8 \
        --export-path models/deformation_unet.pth
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def gaussian_2d(shape: Tuple[int, int], center: Tuple[float, float], sigma: float) -> np.ndarray:
    """根据中心坐标生成二维高斯热力图。"""
    h, w = shape
    xs = np.arange(w, dtype=np.float32)
    ys = np.arange(h, dtype=np.float32)[:, None]
    x0, y0 = center
    heatmap = np.exp(-(((xs - x0) ** 2 + (ys - y0) ** 2) / (2 * sigma ** 2)))
    heatmap /= heatmap.max() + 1e-8
    return heatmap.astype(np.float32)


def load_grayscale(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Failed to read {path}")
    return image.astype(np.float32) / 255.0


@dataclass
class SampleRecord:
    directory: Path
    label_path: Path
    image_paths: Dict[str, Path]
    coord: Tuple[float, float]
    quality: str


class DeformationDataset(Dataset):
    """从样本目录中加载撞击形变数据。"""

    def __init__(
        self,
        root: Path,
        image_size: Tuple[int, int] = (360, 640),
        include_auto: bool = False,
        augment: bool = True,
        sigma: float = 15.0,
    ):
        self.root = Path(root)
        self.image_size = image_size
        self.include_auto = include_auto
        self.augment = augment
        self.sigma = sigma
        self.records: List[SampleRecord] = self._discover_samples()
        if not self.records:
            raise RuntimeError(f"No valid samples found under {self.root}")

    def _discover_samples(self) -> List[SampleRecord]:
        records: List[SampleRecord] = []
        for label_path in self.root.rglob("label.json"):
            directory = label_path.parent
            try:
                with label_path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
            except json.JSONDecodeError:
                continue

            quality = payload.get("quality", "unknown")
            if (quality != "manual") and (not self.include_auto):
                continue

            coord = payload.get("coord")
            if not coord or "x" not in coord or "y" not in coord:
                continue

            image_paths = {
                "impact": directory / "impact.png",
                "diff": directory / "diff.png",
                "pre": directory / "pre_0.png",
            }

            if not image_paths["impact"].exists():
                continue

            records.append(
                SampleRecord(
                    directory=directory,
                    label_path=label_path,
                    image_paths=image_paths,
                    coord=(float(coord["x"]), float(coord["y"])),
                    quality=quality,
                )
            )

        return records

    def __len__(self) -> int:
        return len(self.records)

    def _resize(self, image: np.ndarray) -> np.ndarray:
        return cv2.resize(image, self.image_size[::-1], interpolation=cv2.INTER_AREA)

    def _augment(self, tensor: torch.Tensor) -> torch.Tensor:
        if not self.augment:
            return tensor
        if torch.rand(1).item() < 0.5:
            tensor = torch.flip(tensor, dims=[2])
        if torch.rand(1).item() < 0.5:
            tensor = torch.flip(tensor, dims=[1])
        noise = torch.randn_like(tensor) * 0.01
        return torch.clamp(tensor + noise, 0.0, 1.0)

    def __getitem__(self, index: int):
        record = self.records[index]
        impact = self._resize(load_grayscale(record.image_paths["impact"]))
        diff = (
            self._resize(load_grayscale(record.image_paths["diff"]))
            if record.image_paths["diff"].exists()
            else np.zeros_like(impact)
        )
        pre = (
            self._resize(load_grayscale(record.image_paths["pre"]))
            if record.image_paths["pre"].exists()
            else np.zeros_like(impact)
        )

        stacked = np.stack([impact, diff, pre], axis=0)
        input_tensor = torch.from_numpy(stacked).float()
        input_tensor = self._augment(input_tensor)

        scale_x = self.image_size[1] / impact.shape[1]
        scale_y = self.image_size[0] / impact.shape[0]
        center = (
            record.coord[0] * scale_x,
            record.coord[1] * scale_y,
        )

        heatmap = gaussian_2d(self.image_size, center, sigma=self.sigma)
        heatmap_tensor = torch.from_numpy(heatmap).unsqueeze(0)

        target_coords = torch.tensor(center, dtype=torch.float32)

        return input_tensor, heatmap_tensor, target_coords


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.block(x)


class MiniUNet(nn.Module):
    """轻量级 U-Net，同时输出热力图和坐标。"""

    def __init__(self, in_channels: int = 3):
        super().__init__()
        self.enc1 = ConvBlock(in_channels, 32)
        self.enc2 = ConvBlock(32, 64)
        self.enc3 = ConvBlock(64, 128)

        self.pool = nn.MaxPool2d(2)

        self.bottleneck = ConvBlock(128, 256)

        self.up2 = nn.ConvTranspose2d(256, 128, kernel_size=2, stride=2)
        self.dec2 = ConvBlock(256, 128)
        self.up1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
        self.dec1 = ConvBlock(128, 64)
        self.up0 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
        self.dec0 = ConvBlock(64, 32)

        self.heatmap_head = nn.Conv2d(32, 1, kernel_size=1)

        self.coord_head = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Flatten(),
            nn.Linear(32, 32),
            nn.ReLU(inplace=True),
            nn.Linear(32, 2),
        )

    def forward(self, x):
        e1 = self.enc1(x)
        e2 = self.enc2(self.pool(e1))
        e3 = self.enc3(self.pool(e2))

        b = self.bottleneck(self.pool(e3))

        d2 = self.up2(b)
        d2 = torch.cat([d2, e3], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e2], dim=1)
        d1 = self.dec1(d1)

        d0 = self.up0(d1)
        d0 = torch.cat([d0, e1], dim=1)
        d0 = self.dec0(d0)

        heatmap = self.heatmap_head(d0)
        coords = self.coord_head(d0)

        return heatmap, coords


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    heatmap_weight: float = 1.0,
    coord_weight: float = 1.0,
) -> Tuple[float, float]:
    model.train()
    heatmap_loss_meter = 0.0
    coord_loss_meter = 0.0

    for inputs, heatmaps, coords in dataloader:
        inputs = inputs.to(device)
        heatmaps = heatmaps.to(device)
        coords = coords.to(device)

        optimizer.zero_grad()
        pred_heatmaps, pred_coords = model(inputs)

        heatmap_loss = F.mse_loss(pred_heatmaps, heatmaps)
        coord_loss = F.smooth_l1_loss(pred_coords, coords)
        loss = heatmap_weight * heatmap_loss + coord_weight * coord_loss
        loss.backward()
        optimizer.step()

        heatmap_loss_meter += heatmap_loss.item() * inputs.size(0)
        coord_loss_meter += coord_loss.item() * inputs.size(0)

    dataset_size = len(dataloader.dataset)
    return heatmap_loss_meter / dataset_size, coord_loss_meter / dataset_size


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
) -> Tuple[float, float, float]:
    model.eval()
    heatmap_loss_meter = 0.0
    coord_loss_meter = 0.0
    pixel_error_meter = 0.0

    for inputs, heatmaps, coords in dataloader:
        inputs = inputs.to(device)
        heatmaps = heatmaps.to(device)
        coords = coords.to(device)

        pred_heatmaps, pred_coords = model(inputs)

        heatmap_loss = F.mse_loss(pred_heatmaps, heatmaps)
        coord_loss = F.smooth_l1_loss(pred_coords, coords)

        pred_xy = pred_coords.cpu().numpy()
        true_xy = coords.cpu().numpy()
        pixel_error = np.linalg.norm(pred_xy - true_xy, axis=1).mean()

        batch_size = inputs.size(0)
        heatmap_loss_meter += heatmap_loss.item() * batch_size
        coord_loss_meter += coord_loss.item() * batch_size
        pixel_error_meter += pixel_error * batch_size

    dataset_size = len(dataloader.dataset)
    return (
        heatmap_loss_meter / dataset_size,
        coord_loss_meter / dataset_size,
        pixel_error_meter / dataset_size,
    )


def split_dataset(
    dataset: DeformationDataset,
    val_ratio: float = 0.2,
    seed: int = 42,
) -> Tuple[torch.utils.data.Subset, torch.utils.data.Subset]:
    indices = list(range(len(dataset)))
    rng = random.Random(seed)
    rng.shuffle(indices)
    split = int(len(indices) * (1 - val_ratio))
    train_indices = indices[:split]
    val_indices = indices[split:]
    return (
        torch.utils.data.Subset(dataset, train_indices),
        torch.utils.data.Subset(dataset, val_indices),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train deformation heatmap model")
    parser.add_argument("--data-root", type=Path, required=True, help="样本根目录")
    parser.add_argument(
        "--image-height", type=int, default=360, help="模型输入高度"
    )
    parser.add_argument(
        "--image-width", type=int, default=640, help="模型输入宽度"
    )
    parser.add_argument("--sigma", type=float, default=12.0, help="热力图高斯 σ")
    parser.add_argument("--batch-size", type=int, default=8, help="训练 batch size")
    parser.add_argument("--epochs", type=int, default=30, help="训练轮数")
    parser.add_argument("--lr", type=float, default=1e-3, help="学习率")
    parser.add_argument("--val-ratio", type=float, default=0.2, help="验证集比例")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    parser.add_argument("--only-manual", action="store_true", help="仅使用人工确认样本")
    parser.add_argument("--no-augment", action="store_true", help="关闭数据增强")
    parser.add_argument("--export-path", type=Path, default=Path("models/deformation_unet.pth"))
    parser.add_argument("--heatmap-weight", type=float, default=1.0)
    parser.add_argument("--coord-weight", type=float, default=1.0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    dataset = DeformationDataset(
        root=args.data_root,
        image_size=(args.image_height, args.image_width),
        include_auto=not args.only_manual,
        augment=not args.no_augment,
        sigma=args.sigma,
    )

    train_subset, val_subset = split_dataset(dataset, val_ratio=args.val_ratio, seed=args.seed)

    train_loader = DataLoader(
        train_subset, batch_size=args.batch_size, shuffle=True, num_workers=4, pin_memory=True
    )
    val_loader = DataLoader(
        val_subset, batch_size=args.batch_size, shuffle=False, num_workers=4, pin_memory=True
    )

    device = torch.device(args.device)
    model = MiniUNet(in_channels=3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)

    best_val_error = math.inf
    args.export_path.parent.mkdir(parents=True, exist_ok=True)

    for epoch in range(1, args.epochs + 1):
        train_heatmap_loss, train_coord_loss = train_one_epoch(
            model,
            train_loader,
            optimizer,
            device,
            heatmap_weight=args.heatmap_weight,
            coord_weight=args.coord_weight,
        )

        val_heatmap_loss, val_coord_loss, val_pixel_error = evaluate(
            model,
            val_loader,
            device,
        )

        print(
            f"[Epoch {epoch:03d}] "
            f"train_heatmap={train_heatmap_loss:.4f} "
            f"train_coord={train_coord_loss:.4f} "
            f"val_heatmap={val_heatmap_loss:.4f} "
            f"val_coord={val_coord_loss:.4f} "
            f"val_pixel_err={val_pixel_error:.2f}px"
        )

        if val_pixel_error < best_val_error:
            best_val_error = val_pixel_error
            torch.save(
                {
                    "model_state": model.state_dict(),
                    "epoch": epoch,
                    "val_pixel_error": val_pixel_error,
                    "config": vars(args),
                },
                args.export_path,
            )
            print(f"  ↳ New best model saved to {args.export_path}")


if __name__ == "__main__":
    main()
