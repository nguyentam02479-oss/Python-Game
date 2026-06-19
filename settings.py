# =============================================================================
# FILE: settings.py
# Mô tả: Toàn bộ các hằng số cấu hình cho game Sweet Cake Match-3
# =============================================================================

from enum import Enum, auto

# -----------------------------------------------------------------------------
# CẤU HÌNH MÀN HÌNH
# -----------------------------------------------------------------------------
SCREEN_W = 1100          # Chiều rộng màn hình (pixel)
SCREEN_H = 720           # Chiều cao màn hình (pixel)
FPS      = 60            # Tốc độ khung hình mỗi giây

# -----------------------------------------------------------------------------
# CẤU HÌNH LƯỚI BÀN CHƠI
# -----------------------------------------------------------------------------
GRID_ROWS  = 8           # Số hàng lưới
GRID_COLS  = 8           # Số cột lưới
CELL_SIZE  = 72          # Kích thước mỗi ô vuông (pixel)
GRID_OFFSET_X = 60       # Khoảng cách lưới so với mép trái màn hình
GRID_OFFSET_Y = 80       # Khoảng cách lưới so với mép trên màn hình

# -----------------------------------------------------------------------------
# CẤU HÌNH SIDEBAR (HUD bên phải)
# -----------------------------------------------------------------------------
SIDEBAR_X = GRID_OFFSET_X + GRID_COLS * CELL_SIZE + 30   # Vị trí bắt đầu sidebar
SIDEBAR_W = SCREEN_W - SIDEBAR_X - 20                     # Chiều rộng sidebar

# -----------------------------------------------------------------------------
# ENUM: Trạng thái game
# -----------------------------------------------------------------------------
class State(Enum):
    MENU      = auto()   # Màn hình chính / chọn chế độ
    PLAYING   = auto()   # Đang trong phiên chơi
    SHOP      = auto()   # Đang xem cửa hàng
    MISSION   = auto()   # Đang xem bảng nhiệm vụ
    GAME_OVER = auto()   # Kết thúc (thua)
    LEVEL_WIN = auto()   # Thắng màn

# -----------------------------------------------------------------------------
# ENUM: Chế độ chơi
# -----------------------------------------------------------------------------
class GameMode(Enum):
    BASIC     = auto()   # Chế độ thời gian đếm ngược
    CHALLENGE = auto()   # Chế độ thử thách hạn chế lượt đi

# -----------------------------------------------------------------------------
# ENUM: Loại viên bánh ngọt
# -----------------------------------------------------------------------------
class PieceType(Enum):
    CAKE1    = 1
    CAKE2    = 2
    CAKE3    = 3
    CAKE4    = 4
    CAKE5    = 5
    CAKE6    = 6
    CAKE7    = 7
    WILDCARD = 8   # Viên đặc biệt có thể ghép với bất kỳ loại nào

# -----------------------------------------------------------------------------
# MÀUSẮC GIAO DIỆN
# -----------------------------------------------------------------------------
# Màu nền chính
COLOR_BG_DARK      = (30,  15,  50)    # Tím đậm nền
COLOR_BG_PANEL     = (50,  25,  80)    # Tím nhạt hơn cho panel
COLOR_BG_SIDEBAR   = (40,  20,  65)    # Sidebar
COLOR_OVERLAY_LIGHT = (245, 240, 230)  # THÊM: Trắng ngà cho lớp phủ

# Màu UI chính
COLOR_WHITE        = (255, 255, 255)
COLOR_BLACK        = (0,   0,   0)
COLOR_YELLOW       = (255, 215, 0)     # Vàng đồng xu
COLOR_GOLD         = (255, 185, 15)
COLOR_RED          = (220, 50,  50)
COLOR_GREEN        = (50,  200, 100)
COLOR_BLUE_ICE     = (100, 180, 255)   # Màu băng đá
COLOR_BLUE_ICE_BG  = (150, 210, 255, 120)  # Băng mờ (alpha)

# Màu nút bấm
COLOR_BTN_PRIMARY  = (160, 80,  220)   # Tím chính
COLOR_BTN_HOVER    = (200, 120, 255)   # Tím sáng khi hover
COLOR_BTN_DISABLED = (80,  60,  100)   # Xám tím khi không dùng được
COLOR_BTN_BUY      = (50,  180, 90)    # Xanh lá - nút mua
COLOR_BTN_CLAIM    = (220, 160, 20)    # Vàng - nút nhận thưởng

# Màu chữ
COLOR_TEXT_TITLE   = (255, 230, 100)   # Vàng nhạt tiêu đề
COLOR_TEXT_BODY    = (230, 220, 255)   # Tím trắng nội dung
COLOR_TEXT_COIN    = (255, 215, 0)     # Vàng đồng xu

# Màu viền ô lưới
COLOR_GRID_LINE    = (100, 60,  140)
COLOR_CELL_HOVER   = (255, 255, 100, 80)   # Vàng mờ khi rê chuột
COLOR_CELL_SELECT  = (100, 255, 100, 120)  # Xanh sáng khi chọn

# Màu đại diện từng loại bánh (dùng khi không có ảnh)
PIECE_COLORS = {
    PieceType.CAKE1:    (255, 100, 150),   # Hồng - bánh dâu
    PieceType.CAKE2:    (255, 170, 50),    # Cam - bánh cam
    PieceType.CAKE3:    (100, 200, 100),   # Xanh lá - bánh matcha
    PieceType.CAKE4:    (100, 150, 255),   # Xanh dương - bánh việt quất
    PieceType.CAKE5:    (200, 100, 255),   # Tím - bánh nho
    PieceType.CAKE6:    (255, 240, 80),    # Vàng - bánh chanh
    PieceType.CAKE7:    (180, 100, 60),    # Nâu - bánh socola
    PieceType.WILDCARD: (255, 255, 255),   # Trắng - viên đặc biệt
}

# -----------------------------------------------------------------------------
# CẤU HÌNH GAMEPLAY - CHẾ ĐỘ BASIC
# -----------------------------------------------------------------------------
BASIC_TIME_LIMIT       = 90.0    # Giới hạn thời gian (giây)
BASIC_TIME_BONUS_MATCH = 2.0     # Cộng thêm giây mỗi khi match thành công
BASIC_SCORE_PER_PIECE  = 10      # Điểm mỗi viên kẹo bị xóa
BASIC_COMBO_MULTIPLIER = 0.5     # Nhân thêm khi combo (x1.5, x2, ...)

# -----------------------------------------------------------------------------
# CẤU HÌNH GAMEPLAY - CHẾ ĐỘ CHALLENGE
# -----------------------------------------------------------------------------
CHALLENGE_MOVES_LIMIT  = 25      # Số lượt di chuyển tối đa
CHALLENGE_SCORE_TARGET = 3000    # Điểm cần đạt để thắng
CHALLENGE_FROZEN_CHANCE = 0.12   # Xác suất xuất hiện ô đóng băng (12%)
CHALLENGE_COIN_CHANCE   = 0.10   # Xác suất xuất hiện xu trong ô (10%)
CHALLENGE_SCORE_PER_PIECE = 15   # Điểm mỗi viên kẹo (cao hơn basic)

# -----------------------------------------------------------------------------
# CẤU HÌNH SHOP (Cửa hàng)
# -----------------------------------------------------------------------------
SHOP_ITEMS = {
    "hammer": {
        "name":        "Phá Ô",
        "description": "Phá hủy 1 ô bất kỳ trên bàn",
        "price":       30,         # Giá tính bằng xu
        "icon_color":  (220, 180, 100),
    },
    "mixer": {
        "name":        "Hoán Đổi",
        "description": "Hoán đổi 2 ô ngẫu nhiên ",
        "price":       25,
        "icon_color":  (100, 200, 220),
    },
    "extra_time": {
        "name":        "+30 Giây",
        "description": "Cộng 30 giây "
                       "(Basic)",
        "price":       40,
        "icon_color":  (100, 255, 150),
    },
    "extra_moves": {
        "name":        "+5 Lượt",
        "description": "Cộng 5 lượt đi "
                       "(Challenge)",
        "price":       35,
        "icon_color":  (255, 150, 100),
    },
}

# -----------------------------------------------------------------------------
# CẤU HÌNH MISSION (Nhiệm vụ)
# -----------------------------------------------------------------------------
MISSIONS = [
    {
        "id":          "daily_pieces",
        "name":        "Thợ Bánh Ngọt",
        "description": "Phá 50 viên bánh trong ngày",
        "target":      50,
        "reward_coin": 20,
        "type":        "daily",     # daily = reset mỗi ngày
    },
    {
        "id":          "daily_combo",
        "name":        "Combo Huyền Thoại",
        "description": "Tạo 5 combo trong ngày",
        "target":      5,
        "reward_coin": 15,
        "type":        "daily",
    },
    {
        "id":          "hourly_score",
        "name":        "Ghi Điểm Nhanh",
        "description": "Đạt 500 điểm trong 1 giờ",
        "target":      500,
        "reward_coin": 10,
        "type":        "hourly",    # hourly = reset mỗi giờ
    },
    {
        "id":          "session_frozen",
        "name":        "Phá Băng",
        "description": "Phá 10 ô băng trong phiên này",
        "target":      10,
        "reward_coin": 25,
        "type":        "session",   # session = trong phiên chơi hiện tại
    },
]

# -----------------------------------------------------------------------------
# HIỆU ỨNG HOẠT ẢNH
# -----------------------------------------------------------------------------
LERP_SPEED      = 12.0     # Tốc độ di chuyển Lerp của viên kẹo
FALL_SPEED      = 10.0     # Tốc độ rơi kẹo từ trên xuống
EXPLODE_FRAMES  = 8        # Số frame hiệu ứng nổ

# -----------------------------------------------------------------------------
# CẤU HÌNH FILE ẢNH
# -----------------------------------------------------------------------------
IMAGE_BG    = "Icons/Game.jpg"
IMAGE_CAKES = {
    PieceType.CAKE1:    "Icons/cake1.png",
    PieceType.CAKE2:    "Icons/cake2.png",
    PieceType.CAKE3:    "Icons/cake3.png",
    PieceType.CAKE4:    "Icons/cake4.png",
    PieceType.CAKE5:    "Icons/cake5.png",
    PieceType.CAKE6:    "Icons/cake6.png",
    PieceType.CAKE7:    "Icons/cake7.png",
    PieceType.WILDCARD: None,    # Wildcard không có file ảnh riêng
}