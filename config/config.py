import configparser


class ConfigLoader:
    def __init__(self, config_file='config.ini'):
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

        # 球馆名称
        self.court_name = self.config.get('Settings', 'court_name')
        self.court_name_font_size = self.config.getint('Settings', 'court_name_font_size')
        # 场地编号
        self.court_number = self.config.get('Settings', 'court_number')
        # 场地长度
        self.court_length = self.config.getint('Settings', 'court_length')
        # 球场长度调整值
        self.court_length_tuneup = self.config.getfloat('Settings', 'court_length_tuneup')
        # 发球机球速
        self.serve_speed = self.config.getint('Settings', 'serve_speed')
        # 点大小
        self.point_size = self.config.getint('ScoreBoard', 'point_size')
        # 点颜色
        point_color_str = self.config.get('ScoreBoard', 'point_color')
        self.point_color = tuple(map(int, point_color_str.split(',')))
        # 边线宽度
        self.line_width = self.config.getint('ScoreBoard', 'line_width')
        # 线颜色
        line_color_str = self.config.get('ScoreBoard', 'line_color')
        self.line_color = tuple(map(int, line_color_str.split(',')))
        # 得分框圈大小
        self.circle_20 = self.config.getint('ScoreBoard', 'circle_20')
        self.circle_30 = self.config.getint('ScoreBoard', 'circle_30')
        self.circle_50 = self.config.getint('ScoreBoard', 'circle_50')
        # 各得分框的坐标
        self.circle_20_1_xy = self._parse_tuple('ScoreBoard', 'circle_20_1_xy')
        self.circle_20_2_xy = self._parse_tuple('ScoreBoard', 'circle_20_2_xy')
        self.circle_30_xy = self._parse_tuple('ScoreBoard', 'circle_30_xy')
        self.circle_50_1_xy = self._parse_tuple('ScoreBoard', 'circle_50_1_xy')
        self.circle_50_2_xy = self._parse_tuple('ScoreBoard', 'circle_50_2_xy')
        # 顶端的左右坐标值
        self.top_left_xy = self._parse_tuple('ScoreBoard', 'top_left_xy')
        self.top_right_xy = self._parse_tuple('ScoreBoard', 'top_right_xy')
        # 中线左右坐标值
        self.mid_left_xy = self._parse_tuple('ScoreBoard', 'mid_left_xy')
        self.mid_center_xy = self._parse_tuple('ScoreBoard', 'mid_center_xy')
        self.mid_right_xy = self._parse_tuple('ScoreBoard', 'mid_right_xy')
        # 底线左右坐标值
        self.bottom_left_xy = self._parse_tuple('ScoreBoard', 'bottom_left_xy')
        self.bottom_center_xy = self._parse_tuple('ScoreBoard', 'bottom_center_xy')
        self.bottom_right_xy = self._parse_tuple('ScoreBoard', 'bottom_right_xy')
        # 球的颜色
        self.ball_color = tuple(map(int, self.config.get('ScoreBoard', 'ball_color').split(',')))
        # Y坐标补偿
        self.y_offset = self.config.getint('ScoreBoard', 'y_offset')
        # 亮灯倍数
        self.multiple = self.config.getint('ScoreBoard', 'multiple')

        # 保存图片
        self.save_image = self.config.getboolean('Settings', 'save_image')
        self.rtsp_url = self.config.get('Settings', 'rtsp_url')
        # 轮廓周长
        self.min_girth = self.config.getint('Settings', 'min_girth')
        # 圆形度阈值
        self.circularity = self.config.getfloat('Settings', 'circularity')
        # 挥拍时延
        self.swing_time = self.config.getint('Settings', 'swing_time')
        # 寻位时延
        self.locating_time = self.config.getint('Settings', 'locating_time')

    def _parse_tuple(self, section, option):
        value_str = self.config.get(section, option)
        return tuple(map(int, value_str.split(',')))
