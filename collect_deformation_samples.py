#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
采集撞击形变数据的辅助脚本
--------------------------------

用途：
    1. 在 `score.py` 的撞击检测通过后调用 `save_sample`，将撞击前后帧落盘
    2. 自动生成 meta 信息和初始坐标标签，便于后续半自动标注
    3. 提供 CLI 工具快速验证采集目录或做离线回放

使用方式（示例）：
    ```python
    from collect_deformation_samples import FramePack, save_sample

    frame_pack = FramePack(
        pre_frames=[frame_t_minus_2, frame_t_minus_1],
        impact_frame=frame_t,
        post_frames=[frame_t_plus_1, frame_t_plus_2],
        diff_frame=diff_frame
    )
    save_sample(
        game_id=self.game_id,
        ball_number=self.ball_number,
        frame_pack=frame_pack,
        impact_result=impact_result,
        config_snapshot=collect_config_snapshot(self.config),
        output_root="dataset/raw",
        auto_label=self.get_score(center_x, center_y)[0],
        auto_coord={"x": center_x, "y": center_y}
    )
    ```
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import cv2
import numpy as np

LOGGER = logging.getLogger("collect_deformation_samples")


@dataclass
class FramePack:
    """承载一次撞击的关键帧集合。所有帧需为 BGR numpy 数组。"""

    pre_frames: List[np.ndarray]
    impact_frame: np.ndarray
    post_frames: List[np.ndarray]
    diff_frame: Optional[np.ndarray] = None
    mask: Optional[np.ndarray] = None
    extras: Dict[str, np.ndarray] = field(default_factory=dict)

    def iter_named_frames(self) -> Iterable[Tuple[str, np.ndarray]]:
        """生成带名称的帧，便于统一保存。"""
        for idx, frame in enumerate(self.pre_frames):
            yield f"pre_{idx}.png", frame
        yield "impact.png", self.impact_frame
        for idx, frame in enumerate(self.post_frames):
            yield f"post_{idx}.png", frame
        if self.diff_frame is not None:
            yield "diff.png", self.diff_frame
        if self.mask is not None:
            yield "mask.png", self.mask
        for name, frame in self.extras.items():
            suffix = "" if name.endswith(".png") else ".png"
            yield f"{name}{suffix}", frame


def _ensure_uint8(image: np.ndarray) -> np.ndarray:
    """将任意数值范围的数组安全转换为 0-255 的 uint8。"""
    if image.dtype == np.uint8:
        return image
    clipped = np.clip(image, 0, 255)
    return clipped.astype(np.uint8)


def _save_image(image: np.ndarray, dst_path: Path) -> None:
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    encoded = _ensure_uint8(image)
    cv2.imwrite(str(dst_path), encoded)


def collect_config_snapshot(config) -> Dict[str, Tuple[int, int]]:
    """
    从 ConfigLoader 实例提取与幕布形变相关的关键字段。
    仅使用属性访问，避免直接序列化 ConfigParser。
    """
    snapshot_fields = [
        "top_left_xy",
        "top_right_xy",
        "mid_left_xy",
        "mid_center_xy",
        "mid_right_xy",
        "bottom_left_xy",
        "bottom_center_xy",
        "bottom_right_xy",
        "circle_20_1_xy",
        "circle_20_2_xy",
        "circle_30_xy",
        "circle_50_1_xy",
        "circle_50_2_xy",
        "circle_20",
        "circle_30",
        "circle_50",
        "multiple",
        "y_offset",
    ]
    snapshot: Dict[str, object] = {}
    for field_name in snapshot_fields:
        if hasattr(config, field_name):
            value = getattr(config, field_name)
            if isinstance(value, tuple):
                snapshot[field_name] = tuple(int(v) for v in value)
            else:
                snapshot[field_name] = value
    return snapshot


def save_sample(
    game_id: int,
    ball_number: int,
    frame_pack: FramePack,
    impact_result: Optional[Dict] = None,
    config_snapshot: Optional[Dict] = None,
    output_root: str | Path = "dataset/raw",
    auto_coord: Optional[Dict[str, float]] = None,
    auto_label: Optional[int] = None,
    extra_meta: Optional[Dict] = None,
) -> Path:
    """
    将撞击形变相关帧落盘，并生成 meta/label 文件。

    返回值：
        Path - 当前样本目录，便于后续日志输出或测试。
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    output_root = Path(output_root)
    folder_name = f"game_{game_id:04d}_ball_{ball_number:03d}_{timestamp}"
    sample_dir = output_root / datetime.utcnow().strftime("%Y%m%d") / folder_name
    sample_dir.mkdir(parents=True, exist_ok=True)

    LOGGER.info("Saving deformation sample to %s", sample_dir)

    # 保存帧数据
    for file_name, frame in frame_pack.iter_named_frames():
        _save_image(frame, sample_dir / file_name)

    # 构建 meta 信息
    meta = {
        "game_id": game_id,
        "ball_number": ball_number,
        "captured_at_utc": timestamp,
        "frames": [name for name, _ in frame_pack.iter_named_frames()],
        "impact_result": impact_result or {},
        "config_snapshot": config_snapshot or {},
    }
    if extra_meta:
        meta.update(extra_meta)

    with (sample_dir / "meta.json").open("w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    # 初始标签（自动推断，待人工复核）
    label_payload = {
        "coord": auto_coord or {},
        "score": auto_label,
        "quality": "auto" if auto_coord else "unknown",
        "notes": "",
    }
    with (sample_dir / "label.json").open("w", encoding="utf-8") as f:
        json.dump(label_payload, f, ensure_ascii=False, indent=2)

    return sample_dir


def list_unverified_samples(root: str | Path = "dataset/raw") -> List[Path]:
    """
    返回所有标签质量不是 'manual' 的样本路径列表，便于人工复核。
    """
    root_path = Path(root)
    pending: List[Path] = []
    if not root_path.exists():
        return pending

    for label_path in root_path.rglob("label.json"):
        with label_path.open("r", encoding="utf-8") as f:
            label = json.load(f)
        if label.get("quality") != "manual":
            pending.append(label_path.parent)
    return sorted(pending)


def mark_label_as_manual(sample_dir: Path, x: float, y: float, notes: str = "") -> None:
    """
    更新 label.json，将坐标改为人工确认后的数值。
    """
    label_path = sample_dir / "label.json"
    if not label_path.exists():
        raise FileNotFoundError(f"label.json missing in {sample_dir}")

    with label_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    payload["coord"] = {"x": float(x), "y": float(y)}
    payload["quality"] = "manual"
    payload["notes"] = notes

    with label_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def demo_random_sample(output_root: str | Path = "dataset/raw") -> Path:
    """
    生成一个随机噪声样本，便于验证脚本是否正常工作。
    """
    rng = np.random.default_rng(seed=42)

    def random_image() -> np.ndarray:
        return rng.integers(0, 255, size=(720, 1280, 3), dtype=np.uint8)

    frame_pack = FramePack(
        pre_frames=[random_image(), random_image()],
        impact_frame=random_image(),
        post_frames=[random_image(), random_image()],
        diff_frame=rng.integers(0, 255, size=(720, 1280), dtype=np.uint8),
    )

    return save_sample(
        game_id=1,
        ball_number=1,
        frame_pack=frame_pack,
        impact_result={"detected": True, "confidence": 0.5},
        config_snapshot={"top_left_xy": (100, 50)},
        output_root=output_root,
        auto_coord={"x": 640.0, "y": 360.0},
        auto_label=10,
        extra_meta={"demo": True},
    )


def _setup_cli_logger(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="撞击形变数据采集工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo_parser = subparsers.add_parser("demo", help="生成一个随机样本验证落盘逻辑")
    demo_parser.add_argument("--output-root", default="dataset/raw")

    list_parser = subparsers.add_parser("list-pending", help="列出待人工确认标签的样本")
    list_parser.add_argument("--root", default="dataset/raw")

    mark_parser = subparsers.add_parser("mark-manual", help="手动更新某个样本的标签坐标")
    mark_parser.add_argument("sample_dir", help="样本目录路径")
    mark_parser.add_argument("--x", type=float, required=True)
    mark_parser.add_argument("--y", type=float, required=True)
    mark_parser.add_argument("--notes", default="")

    parser.add_argument("--verbose", action="store_true", help="打印调试日志")

    args = parser.parse_args()
    _setup_cli_logger(args.verbose)

    if args.command == "demo":
        sample_path = demo_random_sample(args.output_root)
        LOGGER.info("Demo sample saved to %s", sample_path)
    elif args.command == "list-pending":
        pending = list_unverified_samples(args.root)
        if not pending:
            LOGGER.info("All samples are verified. Great job!")
        else:
            LOGGER.info("Found %d samples awaiting manual verification:", len(pending))
            for path in pending:
                LOGGER.info(" - %s", path)
    elif args.command == "mark-manual":
        mark_label_as_manual(Path(args.sample_dir), args.x, args.y, args.notes)
        LOGGER.info("Updated manual label for %s", args.sample_dir)


if __name__ == "__main__":
    main()
