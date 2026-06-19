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

        # ----- Hiệu ứng chọn (selection glow) -----
        self._select_anim_t = 0.0  # Bộ đếm hoạt ảnh vòng sáng khi chọn

        # ----- Hoạt ảnh băng (shimmer) -----
        self._ice_anim_t = 0.0    # Bộ đếm hiệu ứng lấp lánh băng

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

        # Cập nhật hoạt ảnh vòng sáng khi chọn
        if self.is_selected:
            self._select_anim_t += dt * 4.0
        else:
            self._select_anim_t = 0.0

        # Cập nhật hoạt ảnh lấp lánh băng
        if self.is_frozen:
            self._ice_anim_t += dt * 1.5

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

        # Vẽ vòng sáng chọn TRƯỚC khi vẽ băng (nằm dưới)
        if self.is_selected:
            self._draw_selection_glow(surface, draw_x, draw_y)

        # Vẽ icon xu (nếu có)
        if self.has_coin:
            self._draw_coin_icon(surface, draw_x, draw_y)

        # Vẽ lớp băng (nếu có) - vẽ SAU piece ảnh để phủ lên trên
        if self.is_frozen:
            self._draw_ice_overlay(surface, draw_x, draw_y)

        # Vẽ hiệu ứng nổ (nếu đang nổ)
        if self.explode_active and self.explode_timer < 0.3:
            self._draw_explode_effect(surface, draw_x, draw_y)

    def _draw_ice_overlay(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ lớp băng dày kiểu Candy Crush - phủ đặc lên piece,
        có vết nứt, phản chiếu sáng và hiệu ứng lấp lánh.
        """
        cs = CELL_SIZE
        ice_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

        # --- Lớp nền băng đặc (xanh lam nhạt, alpha ~190) ---
        # Tạo hiệu ứng gradient bằng nhiều lớp hình chữ nhật bo góc
        pygame.draw.rect(ice_surf, (180, 225, 255, 190),
                         (0, 0, cs, cs), border_radius=6)
        pygame.draw.rect(ice_surf, (210, 240, 255, 120),
                         (2, 2, cs - 4, cs - 4), border_radius=5)

        # --- Vết nứt (cracks) - tĩnh, như Candy Crush ---
        crack_color = (100, 170, 220, 200)
        cx, cy = cs // 2, cs // 2

        # Vết nứt chính (đường xiên dài)
        pygame.draw.line(ice_surf, crack_color,
                         (cx - 12, cy - 18), (cx + 8, cy + 6), 2)
        pygame.draw.line(ice_surf, crack_color,
                         (cx + 8, cy + 6), (cx + 16, cy - 4), 2)

        # Vết nứt phụ (ngắn hơn)
        pygame.draw.line(ice_surf, crack_color,
                         (cx - 5, cy + 8), (cx + 6, cy + 18), 2)
        pygame.draw.line(ice_surf, crack_color,
                         (cx - 16, cy + 2), (cx - 8, cy + 10), 1)
        pygame.draw.line(ice_surf, crack_color,
                         (cx + 10, cy - 14), (cx + 18, cy - 8), 1)

        # Đốm nhỏ tại điểm giao vết nứt
        pygame.draw.circle(ice_surf, (80, 150, 210, 230), (cx + 8, cy + 6), 3)

        # --- Phản chiếu sáng (highlight) - góc trên trái ---
        highlight_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
        # Hình elipse lớn sáng bóng
        pygame.draw.ellipse(highlight_surf, (255, 255, 255, 90),
                            (4, 4, cs // 2 + 4, cs // 3))
        # Chấm sáng nhỏ
        pygame.draw.ellipse(highlight_surf, (255, 255, 255, 160),
                            (6, 6, cs // 4, cs // 6))
        ice_surf.blit(highlight_surf, (0, 0))

        # --- Viền băng dày (2 lớp viền) ---
        pygame.draw.rect(ice_surf, (100, 180, 240, 220),
                         (0, 0, cs, cs), 3, border_radius=6)
        pygame.draw.rect(ice_surf, (200, 235, 255, 160),
                         (2, 2, cs - 4, cs - 4), 1, border_radius=5)

        # --- Hiệu ứng lấp lánh (shimmer) theo thời gian ---
        shimmer_alpha = int(40 + 30 * math.sin(self._ice_anim_t * 2.0))
        shimmer_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)
        shimmer_x = int((cs + 20) * ((math.sin(self._ice_anim_t * 0.7) + 1) / 2)) - 10
        for i in range(8):
            sx = shimmer_x + i * 2 - 4
            if 0 <= sx < cs:
                alpha_val = max(0, min(255, shimmer_alpha - i * 4))
                pygame.draw.line(shimmer_surf,
                                 (255, 255, 255, alpha_val),
                                 (sx, 0), (sx + cs // 3, cs), 1)
        ice_surf.blit(shimmer_surf, (0, 0))

        # Blit toàn bộ lên surface game
        surface.blit(ice_surf, (dx, dy))

    def _draw_selection_glow(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ hiệu ứng vòng sáng nhấp nháy khi piece được chọn.
        Phong cách Candy Crush: viền vàng sáng + hào quang mờ bên ngoài + scale nhẹ.
        """
        cs = CELL_SIZE
        t = self._select_anim_t

        # --- Nhịp đập (pulse): thay đổi alpha và độ dày theo sin ---
        pulse = (math.sin(t) + 1) / 2  # 0.0 -> 1.0

        # Hào quang ngoài (glow) - surface lớn hơn ô một chút
        pad = 8  # Pixels mở rộng ra ngoài mỗi phía
        glow_size = cs + pad * 2
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)

        # Vẽ nhiều lớp hào quang từ ngoài vào trong (mờ dần)
        glow_alpha_base = int(80 + 60 * pulse)
        for i in range(5):
            layer_pad = pad - i
            layer_alpha = max(0, glow_alpha_base - i * 18)
            layer_color = (255, 230, 60, layer_alpha)  # Vàng sáng
            rect = pygame.Rect(i, i, glow_size - i * 2, glow_size - i * 2)
            pygame.draw.rect(glow_surf, layer_color, rect, max(1, pad - i),
                             border_radius=10 - i)

        surface.blit(glow_surf, (dx - pad, dy - pad))

        # --- Viền vàng chính (1-2 lớp) ---
        border_surf = pygame.Surface((cs, cs), pygame.SRCALPHA)

        # Viền ngoài vàng đậm
        border_alpha = int(200 + 55 * pulse)
        pygame.draw.rect(border_surf, (255, 220, 30, border_alpha),
                         (0, 0, cs, cs), 3, border_radius=7)

        # Viền trong trắng mỏng (highlight)
        inner_alpha = int(120 + 80 * pulse)
        pygame.draw.rect(border_surf, (255, 255, 200, inner_alpha),
                         (3, 3, cs - 6, cs - 6), 1, border_radius=5)

        surface.blit(border_surf, (dx, dy))

        # --- 4 góc sáng (corner sparks) ---
        spark_alpha = int(180 + 75 * pulse)
        spark_color = (255, 245, 100, spark_alpha)
        spark_size = int(4 + 2 * pulse)

        corners = [
            (dx + 2, dy + 2),
            (dx + cs - 6, dy + 2),
            (dx + 2, dy + cs - 6),
            (dx + cs - 6, dy + cs - 6),
        ]
        # Vẽ sparks lên SRCALPHA surface riêng để hỗ trợ alpha
        spark_surf = pygame.Surface((cs + pad * 2 + 10, cs + pad * 2 + 10), pygame.SRCALPHA)
        off = pad + 5  # offset để tọa độ góc khớp với surface nhỏ
        for (sx, sy) in corners:
            lx = sx - dx + off - pad
            ly = sy - dy + off - pad
            pygame.draw.line(spark_surf, spark_color,
                             (lx + spark_size, ly), (lx - spark_size + 4, ly), 2)
            pygame.draw.line(spark_surf, spark_color,
                             (lx + 2, ly - spark_size + 2), (lx + 2, ly + spark_size), 2)
        surface.blit(spark_surf, (dx - off + pad, dy - off + pad))

    def _draw_coin_icon(self, surface: pygame.Surface, dx: int, dy: int):
        """
        Vẽ icon đồng xu trong suốt ở góc dưới phải.
        """
        brightness = int(200 + 55 * math.sin(self._coin_anim_t))
        coin_color = (brightness, int(brightness * 0.85), 0)

        # Vị trí xu ở góc dưới phải
        cx = dx + CELL_SIZE - 16
        cy = dy + CELL_SIZE - 16

        # Vẽ xu lên surface riêng để hỗ trợ alpha
        coin_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
        lcx = CELL_SIZE - 16
        lcy = CELL_SIZE - 16
        pygame.draw.circle(coin_surf, (*coin_color, 200), (lcx, lcy), 10)
        pygame.draw.circle(coin_surf, (255, 255, 200, 150), (lcx, lcy), 10, 2)
        pygame.draw.circle(coin_surf, (255, 255, 255, 200), (lcx - 3, lcy - 3), 3)
        surface.blit(coin_surf, (dx, dy))

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