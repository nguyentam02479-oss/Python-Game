# =============================================================================
# FILE: piece.py
# Mô tả: Định nghĩa thực thể viên bánh ngọt CakePiece
# =============================================================================

import pygame
import math
import random  # THÊM DÒNG NÀY
from settings import (
    CELL_SIZE, PieceType, PIECE_COLORS,
    COLOR_BLUE_ICE, COLOR_YELLOW, COLOR_WHITE,
    LERP_SPEED, GRID_OFFSET_X, GRID_OFFSET_Y
)
from sound_manager import SoundManager  # ← THÊM: âm thanh nổ


class CakePiece:
    """
    Đại diện cho một viên bánh ngọt trên bàn chơi Match-3.
    Quản lý vị trí pixel, trạng thái đặc biệt và hiệu ứng vẽ.
    """

    def __init__(self, piece_type: PieceType, row: int, col: int):
        """
        Khởi tạo viên bánh ngọt.

        :param piece_type: Loại bánh (PieceType Enum)
        :param row: Hàng trong lưới (0-indexed)
        :param col: Cột trong lưới (0-indexed)
        """
        self.piece_type = piece_type
        self.row = row
        self.col = col

        # Tọa độ pixel hiện tại (dùng để vẽ, có thể khác target khi đang Lerp)
        self.x = float(GRID_OFFSET_X + col * CELL_SIZE)
        self.y = float(GRID_OFFSET_Y + row * CELL_SIZE)

        # Tọa độ đích đến (vị trí logic cuối cùng trên lưới)
        self.target_x = self.x
        self.target_y = self.y

        # ----- Trạng thái đặc biệt -----
        self.is_frozen = False  # True: ô bị đóng băng (chỉ trong Challenge)
        self.has_coin = False  # True: ô chứa xu thưởng

        # ----- Trạng thái hiệu ứng -----
        self.is_selected = False  # Đang được người chơi chọn
        self.is_matched = False  # Đã tìm thấy trong match (chuẩn bị xóa)
        self.explode_timer = 0.0  # Bộ đếm hiệu ứng nổ (giây)
        self.explode_active = False  # Đang chạy hiệu ứng nổ
        self.alpha = 255  # Độ trong suốt (255 = không trong suốt)

        # ----- Hiệu ứng lấp lánh của xu -----
        self._coin_anim_t = 0.0  # Bộ đếm hoạt ảnh xu (để tạo nhấp nháy)

    # -------------------------------------------------------------------------
    # CẬP NHẬT TRẠNG THÁI
    # -------------------------------------------------------------------------
    def update(self, dt: float):
        """
        Cập nhật vị trí pixel mượt mà bằng Linear Interpolation (Lerp).
        Gọi mỗi frame với dt = thời gian giây kể từ frame trước.

        :param dt: Delta time (giây)
        """
        # Lerp vị trí X
        dx = self.target_x - self.x
        dy = self.target_y - self.y

        # Nếu khoảng cách còn lại đủ nhỏ, snap thẳng vào đích
        if abs(dx) < 0.5:
            self.x = self.target_x
        else:
            self.x += dx * LERP_SPEED * dt

        if abs(dy) < 0.5:
            self.y = self.target_y
        else:
            self.y += dy * LERP_SPEED * dt

        # Cập nhật bộ đếm hoạt ảnh hiệu ứng nổ
        if self.explode_active:
            self.explode_timer += dt
            # Fade out khi nổ
            progress = min(self.explode_timer / 0.3, 1.0)
            self.alpha = int(255 * (1.0 - progress))

        # Cập nhật hoạt ảnh nhấp nháy xu
        if self.has_coin:
            self._coin_anim_t += dt * 3.0  # Tốc độ nhấp nháy

    def set_target(self, row: int, col: int):
        """
        Cập nhật hàng/cột logic và đặt tọa độ đích để Lerp.
        Đồng thời phát một hiệu ứng nổ nhỏ (sparkle) ngay tại vị trí
        xuất phát để báo hiệu viên bánh bắt đầu di chuyển.

        :param row: Hàng mới
        :param col: Cột mới
        """
        self.row = row
        self.col = col
        self.target_x = float(GRID_OFFSET_X + col * CELL_SIZE)
        self.target_y = float(GRID_OFFSET_Y + row * CELL_SIZE)

        # Chỉ tạo hiệu ứng nếu thực sự đổi vị trí (tránh spam khi không di chuyển)
        if abs(self.x - self.target_x) > 1.0 or abs(self.y - self.target_y) > 1.0:
            self._spawn_move_sparkle()

    def _spawn_move_sparkle(self):
        """Tạo hiệu ứng hạt nhỏ (sparkle nổ) khi viên bánh bắt đầu di chuyển."""
        color = PIECE_COLORS.get(self.piece_type, (255, 220, 220))
        effect = ParticleEffect(
            self.x + CELL_SIZE // 2,
            self.y + CELL_SIZE // 2,
            color,
            count=6  # Ít hạt hơn so với nổ khi match để không quá rối mắt
        )
        PARTICLE_EFFECTS.append(effect)

    def snap_to_target(self):
        """Ngay lập tức di chuyển đến vị trí đích (không lerp)."""
        self.x = self.target_x
        self.y = self.target_y

    # piece.py - SỬA HÀM start_explode (THAY THẾ HÀM CŨ)

    def start_explode(self):
        """Bắt đầu hiệu ứng nổ khi viên kẹo bị xóa."""
        self.explode_active = True
        self.explode_timer = 0.0
        self.is_matched = True

        SoundManager.play("explode")  # ← THÊM: âm thanh nổ

        # Tạo hiệu ứng hạt
        color = PIECE_COLORS.get(self.piece_type, (255, 200, 200))
        effect = ParticleEffect(
            self.x + CELL_SIZE // 2,
            self.y + CELL_SIZE // 2,
            color,
            count=15
        )
        PARTICLE_EFFECTS.append(effect)

    def is_at_target(self) -> bool:
        """Kiểm tra viên kẹo đã đến đích chưa."""
        return abs(self.x - self.target_x) < 1.0 and abs(self.y - self.target_y) < 1.0

    # -------------------------------------------------------------------------
    # VẼ
    # -------------------------------------------------------------------------
    def draw(self, surface: pygame.Surface, images_dict: dict, bg_surface=None):
        """
        Ve vien banh ngot. bg_surface la anh nen de blit truoc vung alpha.
        """
        # Tinh vi tri ve (goc tren trai cua o)
        draw_x = int(self.x)
        draw_y = int(self.y)

        # Blit background vao dung vi tri piece nay truoc
        # de vung alpha=0 hien ra nen thay vi mau xam
        if bg_surface is not None:
            src_rect = pygame.Rect(draw_x, draw_y, CELL_SIZE, CELL_SIZE)
            surface.blit(bg_surface, (draw_x, draw_y), src_rect)

        # Lấy ảnh từ dict
        img = images_dict.get(self.piece_type)

        if img is not None:
            # === QUAN TRỌNG: VẼ TRỰC TIẾP ẢNH, KHÔNG TẠO SURFACE MỚI ===
            if self.explode_active and self.explode_timer < 0.3:
                # Nếu đang nổ, copy ảnh và set alpha
                temp = img.copy()
                temp.set_alpha(self.alpha)
                surface.blit(temp, (draw_x, draw_y))
            else:
                # Vẽ ảnh trực tiếp lên surface game
                surface.blit(img, (draw_x, draw_y))
        else:
            # Fallback: vẽ hình tròn (không có nền)
            temp_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
            temp_surf.fill((0, 0, 0, 0))  # Nền trong suốt

            color = PIECE_COLORS.get(self.piece_type, (200, 200, 200))
            center = (CELL_SIZE // 2, CELL_SIZE // 2)
            radius = (CELL_SIZE // 2) - 4

            # Vẽ hình tròn trong suốt
            pygame.draw.circle(temp_surf, color, center, radius)
            pygame.draw.circle(temp_surf, (255, 255, 255, 80), center, radius, 2)

            if self.alpha < 255:
                temp_surf.set_alpha(self.alpha)

            surface.blit(temp_surf, (draw_x, draw_y))

        # Vẽ icon xu (nếu có)
        if self.has_coin:
            self._draw_coin_icon(surface, draw_x, draw_y)

        # Vẽ lớp băng (nếu có)
        if self.is_frozen:
            self._draw_ice_overlay(surface, draw_x, draw_y)

        # Vẽ hiệu ứng nổ (nếu đang nổ)
        if self.explode_active and self.explode_timer < 0.3:
            self._draw_explode_effect(surface, draw_x, draw_y)

    def _draw_ice_overlay(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ lớp băng mờ - KHÔNG VẼ NỀN Ô.
        """
        # Tạo surface trong suốt
        ice_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        ice_surf.fill((0, 0, 0, 0))  # Nền trong suốt

        # Vẽ hiệu ứng băng (chỉ vẽ viền và hoa văn)
        # KHÔNG vẽ nền màu xanh bao phủ cả ô
        pygame.draw.rect(ice_surf, (150, 210, 255, 80),
                         (4, 4, CELL_SIZE - 8, CELL_SIZE - 8), 2, border_radius=8)

        # Vẽ hoa văn tinh thể
        cx, cy = CELL_SIZE // 2, CELL_SIZE // 2
        crystal_color = (200, 230, 255, 150)

        # Vẽ các đường tinh thể
        for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
            rad = math.radians(angle)
            x1 = cx + int(8 * math.cos(rad))
            y1 = cy + int(8 * math.sin(rad))
            x2 = cx + int(25 * math.cos(rad))
            y2 = cy + int(25 * math.sin(rad))
            pygame.draw.line(ice_surf, crystal_color, (x1, y1), (x2, y2), 2)

        # Blit lên surface
        surface.blit(ice_surf, (dx, dy))

    def _draw_coin_icon(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ icon đồng xu trong suốt ở góc dưới phải.
        """
        brightness = int(200 + 55 * math.sin(self._coin_anim_t))
        coin_color = (brightness, int(brightness * 0.85), 0)

        # Vị trí xu ở góc dưới phải
        cx = dx + CELL_SIZE - 16
        cy = dy + CELL_SIZE - 16

        # Vẽ xu (trong suốt)
        pygame.draw.circle(surface, (*coin_color, 200), (cx, cy), 10)
        pygame.draw.circle(surface, (255, 255, 200, 150), (cx, cy), 10, 2)
        pygame.draw.circle(surface, (255, 255, 255, 200), (cx - 3, cy - 3), 3)

        # Chữ $ (nếu có font)
        try:
            font = pygame.font.SysFont("arial", 10, bold=True)
            txt = font.render("$", True, (50, 30, 0, 200))
            surface.blit(txt, txt.get_rect(center=(cx, cy)))
        except:
            pass

    def _draw_explode_effect(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ hiệu ứng particles khi viên kẹo nổ.

        :param surface: Màn hình game
        :param dx: Tọa độ x góc trên trái của ô
        :param dy: Tọa độ y góc trên trái của ô
        """
        color = PIECE_COLORS.get(self.piece_type, (255, 255, 255))
        cx = dx + CELL_SIZE // 2
        cy = dy + CELL_SIZE // 2

        # Số particle và vị trí xung quanh
        num_particles = 8
        max_radius = 30
        t = self.explode_timer / 0.3  # Tiến trình 0 -> 1
        spread = int(max_radius * t)

        for i in range(num_particles):
            angle = (2 * math.pi * i) / num_particles
            px = cx + int(math.cos(angle) * spread)
            py = cy + int(math.sin(angle) * spread)
            size = max(1, int(5 * (1.0 - t)))
            alpha = int(255 * (1.0 - t))

            # Vẽ particle nhỏ
            p_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*color, alpha), (size, size), size)
            surface.blit(p_surf, (px - size, py - size))

    # -------------------------------------------------------------------------
    # CÁC HÀM TIỆN ÍCH
    # -------------------------------------------------------------------------
    def matches_with(self, other: 'CakePiece') -> bool:
        """
        Kiểm tra viên kẹo này có thể match với viên kẹo khác không.
        Wildcard có thể match với bất kỳ loại nào.

        :param other: Viên kẹo khác
        :return: True nếu có thể match
        """
        if self.piece_type == PieceType.WILDCARD:
            return True
        if other.piece_type == PieceType.WILDCARD:
            return True
        return self.piece_type == other.piece_type

    def __repr__(self):
        return (f"CakePiece({self.piece_type.name}, "
                f"row={self.row}, col={self.col}, "
                f"frozen={self.is_frozen}, coin={self.has_coin})")


# piece.py - THÊM CLASS PARTICLE EFFECT SAU CLASS CakePiece

# =============================================================================
# HIỆU ỨNG HẠT
# =============================================================================

class ParticleEffect:
    """Hiệu ứng hạt khi match-3"""

    def __init__(self, x, y, color, count=12):
        self.particles = []
        self.active = True
        self.life = 0.0
        self.max_life = 0.6

        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 200)
            self.particles.append({
                'x': x,
                'y': y,
                'vx': math.cos(angle) * speed,
                'vy': math.sin(angle) * speed - 50,
                'size': random.uniform(3, 8),
                'color': color,
                'life': random.uniform(0, 0.3),
                'gravity': 200
            })

    def update(self, dt):
        self.life += dt
        if self.life >= self.max_life:
            self.active = False
            return

        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['vy'] += p['gravity'] * dt
            p['life'] += dt

    def draw(self, surface):
        if not self.active:
            return

        alpha = int(255 * (1 - self.life / self.max_life))
        for p in self.particles:
            size = max(1, int(p['size'] * (1 - self.life / self.max_life)))
            color = (*p['color'][:3], alpha)
            pygame.draw.circle(surface, color, (int(p['x']), int(p['y'])), size)


# Biến toàn cục cho hiệu ứng
PARTICLE_EFFECTS = []


# HÀM QUẢN LÝ HIỆU ỨNG TOÀN CỤC
def update_particles(dt):
    """Cập nhật tất cả hiệu ứng hạt."""
    global PARTICLE_EFFECTS
    for effect in PARTICLE_EFFECTS[:]:
        effect.update(dt)
        if not effect.active:
            PARTICLE_EFFECTS.remove(effect)


def draw_particles(surface):
    """Vẽ tất cả hiệu ứng hạt."""
    for effect in PARTICLE_EFFECTS:
        effect.draw(surface)


def clear_particles():
    """Xóa tất cả hiệu ứng hạt."""
    global PARTICLE_EFFECTS
    PARTICLE_EFFECTS.clear()