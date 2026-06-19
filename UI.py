# =============================================================================
# FILE: UI.py
# Mô tả: Xử lý hiển thị toàn bộ giao diện người dùng ngoài bàn chơi
# =============================================================================

import pygame
import math
from typing import Optional, Tuple

from settings import (
    SCREEN_W, SCREEN_H, State, GameMode,
    SIDEBAR_X, SIDEBAR_W, GRID_OFFSET_X, GRID_OFFSET_Y, GRID_ROWS, GRID_COLS, CELL_SIZE,
    SHOP_ITEMS, MISSIONS,
    COLOR_BG_DARK, COLOR_BG_PANEL, COLOR_BG_SIDEBAR,
    COLOR_WHITE, COLOR_BLACK, COLOR_YELLOW, COLOR_GOLD,
    COLOR_RED, COLOR_GREEN, COLOR_BLUE_ICE,
    COLOR_BTN_PRIMARY, COLOR_BTN_HOVER, COLOR_BTN_DISABLED,
    COLOR_BTN_BUY, COLOR_BTN_CLAIM,
    COLOR_TEXT_TITLE, COLOR_TEXT_BODY, COLOR_TEXT_COIN,
    BASIC_TIME_LIMIT,
)


def _make_surface_with_alpha(w: int, h: int, color: tuple, alpha: int) -> pygame.Surface:
    """Tạo Surface với màu nền và độ trong suốt."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((*color[:3], alpha))
    return s


class UIManager:
    """
    Quản lý và vẽ toàn bộ giao diện người dùng:
    - Main Menu
    - HUD khi chơi (Sidebar)
    - Màn hình Shop
    - Màn hình Mission
    - Màn hình Game Over / Level Win
    """

    def __init__(self, screen: pygame.Surface):
        """
        Khởi tạo UIManager.

        :param screen: Surface màn hình chính của Pygame
        """
        self.screen = screen

        # ---- Khởi tạo font ----
        self._init_fonts()

        # ---- Trạng thái các nút (cho hover effect) ----
        self.mouse_pos: Tuple[int, int] = (0, 0)

        # ---- Vị trí các nút trong các màn hình ----
        # (Sẽ được tạo động khi vẽ, lưu lại để xử lý click)
        self.btn_rects: dict = {}

        # ---- Bộ đếm hoạt ảnh tiêu đề ----
        self._title_anim_t: float = 0.0
        self._bg_anim_t: float = 0.0

    def _init_fonts(self):
        """Khởi tạo font chữ (hỗ trợ tiếng Việt) và font emoji riêng."""
        import os

        # ---- Font cho text thường (giữ nguyên như cũ) ----
        try:
            font_options = [
                "Segoe UI",
                "Arial Unicode MS",
                "DejaVu Sans",
                "Times New Roman",
                "FreeSans",
                "arial"
            ]

            font_loaded = False
            for font_name in font_options:
                try:
                    self.font_title = pygame.font.SysFont(font_name, 48, bold=True)
                    self.font_large = pygame.font.SysFont(font_name, 32, bold=True)
                    self.font_medium = pygame.font.SysFont(font_name, 22, bold=True)
                    self.font_small = pygame.font.SysFont(font_name, 17, bold=True)
                    self.font_tiny = pygame.font.SysFont(font_name, 13, bold=True)
                    print(f"[INFO] Đã sử dụng font tiếng Việt: {font_name}")
                    font_loaded = True
                    break
                except:
                    continue

            if not font_loaded:
                raise Exception("Không tìm thấy font hỗ trợ")

        except Exception as e:
            print(f"[WARN] Lỗi font: {e}")
            self.font_title = pygame.font.Font(None, 56)
            self.font_large = pygame.font.Font(None, 38)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 22)
            self.font_tiny = pygame.font.Font(None, 16)

        # ---- Font cho Emoji (chỉ dùng để vẽ emoji) ----
        self.font_emoji = None
        emoji_paths = [
            "fonts/NotoColorEmoji-Regular.ttf",
            "NotoColorEmoji-Regular.ttf"
        ]

        for path in emoji_paths:
            if os.path.exists(path):
                try:
                    self.font_emoji = pygame.font.Font(path, 22)
                    print(f"[INFO] Đã tải font emoji: {path}")
                    break
                except Exception as e:
                    print(f"[WARN] Không thể tải font emoji: {e}")

        # Nếu không có font emoji, dùng font hệ thống có hỗ trợ emoji
        if self.font_emoji is None:
            try:
                self.font_emoji = pygame.font.SysFont("Segoe UI Emoji", 22)
                print("[INFO] Đã sử dụng font emoji hệ thống: Segoe UI Emoji")
            except:
                self.font_emoji = self.font_medium  # Fallback

    def _load_system_font(self):
        """Fallback: sử dụng font hệ thống hỗ trợ emoji và tiếng Việt"""
        try:
            # Thử các font hỗ trợ emoji và tiếng Việt
            font_options = [
                "Segoe UI Emoji",  # Windows - hỗ trợ emoji tốt
                "Segoe UI",  # Windows - hỗ trợ tiếng Việt
                "Apple Color Emoji",  # macOS
                "Arial Unicode MS",  # Windows/macOS - hỗ trợ Unicode
                "DejaVu Sans",  # Linux
                "FreeSans",  # Linux
                "Times New Roman",  # Windows
                "arial"  # Fallback
            ]

            for font_name in font_options:
                try:
                    # Test font có render được không
                    test_font = pygame.font.SysFont(font_name, 20)
                    test_surf = test_font.render("Test", True, (255, 255, 255))
                    if test_surf.get_width() > 0:
                        self.font_title = pygame.font.SysFont(font_name, 48, bold=True)
                        self.font_large = pygame.font.SysFont(font_name, 32, bold=True)
                        self.font_medium = pygame.font.SysFont(font_name, 22, bold=False)
                        self.font_small = pygame.font.SysFont(font_name, 17, bold=False)
                        self.font_tiny = pygame.font.SysFont(font_name, 13, bold=False)
                        print(f"[INFO] Đã sử dụng font hệ thống: {font_name}")
                        return
                except:
                    continue

            # Fallback cuối cùng: font mặc định của pygame
            print("[WARN] Không tìm thấy font nào, sử dụng font mặc định")
            self.font_title = pygame.font.Font(None, 56)
            self.font_large = pygame.font.Font(None, 38)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 22)
            self.font_tiny = pygame.font.Font(None, 16)

        except Exception as e:
            print(f"[ERROR] Lỗi khi load font: {e}")
            self.font_title = pygame.font.Font(None, 56)
            self.font_large = pygame.font.Font(None, 38)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_small = pygame.font.Font(None, 22)
            self.font_tiny = pygame.font.Font(None, 16)

    def _compose_text_emoji_surface(self, text: str, font: pygame.font.Font,
                                    color: tuple) -> pygame.Surface:
        """
        Ghép văn bản thường + emoji thành MỘT Surface duy nhất.
        Đây là hàm lõi dùng chung cho mọi nơi cần vẽ chữ có emoji
        (nút bấm, tiêu đề, label...) để tránh hiện ô vuông trống (tofu)
        khi font chữ tiếng Việt không có glyph emoji.

        :return: Surface đã ghép, căn giữa các phần theo chiều cao.
        """
        if not text:
            return pygame.Surface((0, 0), pygame.SRCALPHA)

        # Nếu không có font emoji nào khả dụng, vẽ bằng font thường (best-effort)
        if self.font_emoji is None:
            return font.render(text, True, color)

        # Danh sách emoji thay thế (một số emoji nhiều byte/biến thể quy về 1 dạng đơn giản)
        emoji_map = {
            '💰': '💰',
            '⏱': '⏰',
            '🔨': '⚒️',
            '🌀': '🌀',
            '🛒': '🛍️',
            '📋': '📝',
            '🎉': '✨',
            '💀': '💀',
            '🔄': '🔄',
            '🏠': '🏠',
            '🏃': '🏃',
            '✔': '✓',
        }

        parts = []
        current_text = ""
        for char in text:
            code = ord(char)
            is_emoji = (
                    (0x1F300 <= code <= 0x1FAFF) or
                    (0x2600 <= code <= 0x27BF) or
                    (0x2190 <= code <= 0x21FF) or
                    (0x2B00 <= code <= 0x2BFF) or
                    (0xFE00 <= code <= 0xFEFF) or
                    char in emoji_map
            )
            if is_emoji:
                if current_text:
                    parts.append(('text', current_text))
                    current_text = ""
                parts.append(('emoji', char))
            else:
                current_text += char
        if current_text:
            parts.append(('text', current_text))

        rendered = []
        for part_type, part_text in parts:
            if part_type == 'text':
                surf = font.render(part_text, True, color)
            else:
                surf = None
                try:
                    surf = self.font_emoji.render(part_text, True, color)
                    # Một số font hệ thống trả về glyph rỗng (width=0) cho emoji lạ
                    if surf.get_width() == 0:
                        surf = None
                except Exception:
                    surf = None
                if surf is None:
                    surf = self._render_emoji_fallback(part_text, color)
            rendered.append(surf)

        if not rendered:
            return pygame.Surface((0, 0), pygame.SRCALPHA)

        total_w = sum(s.get_width() for s in rendered)
        max_h = max(s.get_height() for s in rendered)
        combined = pygame.Surface((max(1, total_w), max(1, max_h)), pygame.SRCALPHA)
        cx = 0
        for s in rendered:
            # Căn giữa theo chiều cao để emoji không bị lệch dòng so với chữ
            combined.blit(s, (cx, (max_h - s.get_height()) // 2))
            cx += s.get_width()
        return combined

    def _draw_text_with_emoji(self, text: str, font: pygame.font.Font, color: tuple,
                              x: int, y: int, center: bool = False):
        """Vẽ văn bản với hỗ trợ emoji (dùng icon vẽ tay khi font không có glyph)."""
        if not text:
            return
        surf = self._compose_text_emoji_surface(text, font, color)
        if center:
            self.screen.blit(surf, surf.get_rect(center=(x, y)))
        else:
            self.screen.blit(surf, (x, y))

    def _render_emoji_fallback(self, emoji: str, color: tuple) -> pygame.Surface:
        """Vẽ icon thay thế cho emoji bị lỗi."""
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)

        # Vẽ các icon đơn giản
        if emoji == '💰' or emoji == '💰':
            # Vẽ đồng xu
            pygame.draw.circle(surf, (255, 215, 0), (12, 12), 10)
            pygame.draw.circle(surf, (200, 180, 0), (12, 12), 10, 2)
        elif emoji == '⏱' or emoji == '⏰':
            # Vẽ đồng hồ
            pygame.draw.circle(surf, (200, 200, 200), (12, 12), 10)
            pygame.draw.circle(surf, (100, 100, 100), (12, 12), 10, 2)
            pygame.draw.line(surf, (100, 100, 100), (12, 12), (12, 6), 2)
            pygame.draw.line(surf, (100, 100, 100), (12, 12), (16, 12), 2)
        elif emoji == '🔨':
            # Vẽ búa
            pygame.draw.rect(surf, (150, 100, 50), (8, 4, 8, 16))
            pygame.draw.rect(surf, (100, 70, 30), (6, 4, 4, 8))
        elif emoji == '🌀':
            # Vẽ xoáy
            for i in range(3):
                pygame.draw.circle(surf, (100, 200, 220), (12, 12), 6 + i * 3, 2)
        elif emoji == '🛒' or emoji == '🛍️' or emoji == '🛍':
            # Vẽ giỏ hàng
            pygame.draw.rect(surf, (150, 150, 150), (6, 8, 12, 10))
            pygame.draw.line(surf, (150, 150, 150), (4, 8), (6, 8), 2)
            pygame.draw.line(surf, (150, 150, 150), (18, 8), (20, 8), 2)
        elif emoji == '📋' or emoji == '📝':
            # Vẽ bảng
            pygame.draw.rect(surf, (200, 200, 200), (8, 4, 8, 16), 2)
            pygame.draw.line(surf, (200, 200, 200), (10, 8), (14, 8), 1)
            pygame.draw.line(surf, (200, 200, 200), (10, 12), (14, 12), 1)
        elif emoji in ('✓', '✔', '✔️'):
            # Vẽ dấu tick
            pygame.draw.line(surf, (90, 220, 100), (5, 13), (10, 18), 3)
            pygame.draw.line(surf, (90, 220, 100), (10, 18), (19, 6), 3)
        elif emoji == '🏃' or emoji == '🏃+':
            # Vẽ hình người chạy đơn giản
            pygame.draw.circle(surf, (220, 200, 150), (13, 4), 3)
            pygame.draw.line(surf, (220, 200, 150), (12, 7), (10, 14), 2)
            pygame.draw.line(surf, (220, 200, 150), (12, 9), (18, 11), 2)
            pygame.draw.line(surf, (220, 200, 150), (10, 14), (6, 20), 2)
            pygame.draw.line(surf, (220, 200, 150), (10, 14), (16, 18), 2)
        elif emoji == '⚡':
            # Vẽ tia sét
            pygame.draw.polygon(surf, (255, 230, 80),
                                [(14, 2), (6, 13), (11, 13), (9, 22), (18, 10), (13, 10)])
        elif emoji == '🔄':
            # Vẽ mũi tên xoay vòng
            pygame.draw.arc(surf, (150, 200, 255), (3, 3, 18, 18), 0.5, 5.5, 3)
            pygame.draw.polygon(surf, (150, 200, 255), [(18, 4), (21, 9), (15, 8)])
        elif emoji == '🏠':
            # Vẽ ngôi nhà
            pygame.draw.polygon(surf, (200, 160, 100), [(12, 3), (3, 11), (21, 11)])
            pygame.draw.rect(surf, (200, 160, 100), (6, 11, 12, 10))
        elif emoji == '←':
            # Vẽ mũi tên trái
            pygame.draw.line(surf, color[:3], (4, 12), (20, 12), 3)
            pygame.draw.polygon(surf, color[:3], [(4, 12), (10, 6), (10, 18)])
        elif emoji in ('🎉', '✨'):
            # Vẽ ngôi sao/pháo hoa đơn giản
            pygame.draw.circle(surf, (255, 220, 100), (12, 12), 3)
            for ang in (0, 60, 120, 180, 240, 300):
                rad = math.radians(ang)
                x1 = 12 + int(5 * math.cos(rad))
                y1 = 12 + int(5 * math.sin(rad))
                x2 = 12 + int(11 * math.cos(rad))
                y2 = 12 + int(11 * math.sin(rad))
                pygame.draw.line(surf, (255, 220, 100), (x1, y1), (x2, y2), 2)
        elif emoji == '💀':
            # Vẽ hộp sọ đơn giản
            pygame.draw.circle(surf, (230, 230, 230), (12, 10), 9)
            pygame.draw.circle(surf, (50, 30, 30), (8, 9), 2)
            pygame.draw.circle(surf, (50, 30, 30), (16, 9), 2)
            pygame.draw.rect(surf, (230, 230, 230), (8, 16, 8, 5))
        else:
            # Vẽ hình tròn màu vàng
            pygame.draw.circle(surf, color[:3], (12, 12), 8)

        return surf
    # =========================================================================
    # CẬP NHẬT
    # =========================================================================

    def update(self, dt: float, mouse_pos: Tuple[int, int]):
        """
        Cập nhật trạng thái UI mỗi frame.

        :param dt: Delta time (giây)
        :param mouse_pos: Vị trí chuột hiện tại
        """
        self.mouse_pos = mouse_pos
        self._title_anim_t += dt
        self._bg_anim_t += dt * 0.3

    # =========================================================================
    # VẼ THEO TRẠNG THÁI
    # =========================================================================

    def draw(self, manager, bg_image: Optional[pygame.Surface] = None):
        """
        Điểm vào vẽ UI - chọn màn hình cần vẽ dựa trên trạng thái.
        """
        self.btn_rects.clear()

        # Vẽ nền chung
        if bg_image:
            scaled_bg = pygame.transform.scale(bg_image, (SCREEN_W, SCREEN_H))
            self.screen.blit(scaled_bg, (0, 0))

            # LỚP PHỦ TRẮNG NGÀ CHO VÙNG BÀN CHƠI ĐƯỢC "NƯỚNG SẴN" (baked-in)
            # vào ảnh nền truyền cho grid.draw() ở main.py (xem board_bg_cache),
            # vì nếu vẽ overlay ở đây thì grid.draw() sẽ vẽ đè nền gốc lên trên,
            # làm mất tác dụng của lớp phủ. Ở đây ta KHÔNG phủ gì thêm lên màn hình
            # ngoài vùng board để giữ ảnh nền rõ nét bên ngoài bàn chơi.
            if manager.state not in (State.PLAYING, State.SHOP, State.MISSION):
                # Menu: giữ nguyên lớp phủ tối toàn màn hình
                overlay = _make_surface_with_alpha(SCREEN_W, SCREEN_H,
                                                   COLOR_BG_DARK, 160)
                self.screen.blit(overlay, (0, 0))
        else:
            self.screen.fill(COLOR_BG_DARK)

        # Chọn màn hình vẽ (giữ nguyên)
        if manager.state == State.MENU:
            self._draw_main_menu(manager)
        elif manager.state == State.PLAYING:
            self._draw_hud_sidebar(manager)
        elif manager.state == State.SHOP:
            self._draw_hud_sidebar(manager)
            self._draw_shop_overlay(manager)
        elif manager.state == State.MISSION:
            self._draw_hud_sidebar(manager)
            self._draw_mission_overlay(manager)
        elif manager.state == State.GAME_OVER:
            self._draw_game_over(manager)
        elif manager.state == State.LEVEL_WIN:
            self._draw_level_win(manager)

        # Vẽ thông báo nổi (luôn trên cùng)
        self._draw_notification(manager)
        self._draw_score_popups(manager)

    # =========================================================================
    # MAIN MENU
    # =========================================================================

    def _draw_main_menu(self, manager):
        """Vẽ màn hình Menu chính với các nút chọn chế độ chơi."""
        cx = SCREEN_W // 2

        # ---- Tiêu đề với hiệu ứng nổi ----
        wobble = math.sin(self._title_anim_t * 2.0) * 5
        title_text = "Sweet Cake Match-3"
        self._draw_text_shadow(title_text, self.font_title,
                               COLOR_TEXT_TITLE, cx, 140 + wobble, center=True)

        subtitle = "- Match-3 Puzzle Game -"
        self._draw_text(subtitle, self.font_medium, COLOR_TEXT_BODY,
                        cx, 200, center=True)

        # ---- Phân cách ----
        pygame.draw.line(self.screen, (100, 60, 150),
                         (cx - 200, 230), (cx + 200, 230), 2)

        # ---- Xu hiện có ----
        coin_txt = f"Xu của bạn: {manager.coins} 💰"
        self._draw_text_with_emoji(coin_txt, self.font_medium, COLOR_TEXT_COIN, cx, 260, center=True)

        # ---- Nút Chế Độ Basic ----
        btn_basic = pygame.Rect(cx - 180, 320, 360, 70)
        self._draw_button(btn_basic, " Chế Độ Thường",
                          self.font_large, key="menu_basic",
                          primary_color=(80, 160, 60))

        self._draw_text("Thời gian đếm ngược · Không giới hạn nước đi",
                        self.font_small, (180, 255, 160),
                        cx, 405, center=True)

        # ---- Nút Chế Độ Challenge ----
        btn_chall = pygame.Rect(cx - 180, 450, 360, 70)
        self._draw_button(btn_chall, "⚡ Chế Độ Thử Thách",
                          self.font_large, key="menu_challenge",
                          primary_color=(160, 60, 220))

        self._draw_text(f"Hạn chế {25} lượt đi · Ô băng · Xu ẩn",
                        self.font_small, (220, 160, 255),
                        cx, 535, center=True)

        # ---- Nút Nhiệm Vụ ----
        completable = manager.count_completable_missions()
        mission_label = f"📋 Nhiệm Vụ" + (f"  ({completable} sẵn sàng)" if completable else "")
        btn_miss = pygame.Rect(cx - 180, 580, 170, 50)
        self._draw_button(btn_miss, mission_label,
                          self.font_small, key="menu_mission",
                          primary_color=(180, 140, 40))

        # ---- Nút Cửa Hàng ----
        btn_shop = pygame.Rect(cx + 10, 580, 170, 50)
        self._draw_button(btn_shop, f"🛒 Cửa Hàng",
                          self.font_small, key="menu_shop",
                          primary_color=(40, 130, 160))

        # Lưu vị trí nút cho xử lý click
        self.btn_rects["menu_basic"] = btn_basic
        self.btn_rects["menu_challenge"] = btn_chall
        self.btn_rects["menu_mission"] = btn_miss
        self.btn_rects["menu_shop"] = btn_shop

        # ---- Điểm cao nhất ----
        if manager.high_score > 0:
            self._draw_text(f"Điểm cao nhất: {manager.high_score:,}",
                            self.font_small, COLOR_TEXT_BODY,
                            cx, SCREEN_H - 40, center=True)

    # =========================================================================
    # HUD SIDEBAR (KHI ĐANG CHƠI)
    # =========================================================================

    def _draw_hud_sidebar(self, manager):
        """
        Vẽ thanh thông tin bên phải (Sidebar HUD):
        - Điểm số, xu, thời gian/lượt đi
        - Kho vật phẩm và nút kích hoạt
        - Nút nhanh mở Shop / Mission
        - Nút quay về Menu
        """
        sx = SIDEBAR_X
        sw = SIDEBAR_W
        sy = GRID_OFFSET_Y

        # ---- Nền sidebar ----
        sidebar_surf = _make_surface_with_alpha(sw + 10, SCREEN_H - sy + 10,
                                                COLOR_BG_SIDEBAR, 210)
        pygame.draw.rect(sidebar_surf, (80, 40, 120),
                         (0, 0, sw + 10, SCREEN_H - sy + 10), 2, border_radius=10)
        self.screen.blit(sidebar_surf, (sx - 6, sy - 6))

        y = sy + 10

        # ---- Chế độ chơi ----
        mode_label = ("⏱ Chế Độ Thời Gian"
                      if manager.mode == GameMode.BASIC
                      else "⚡ Chế Độ Thử Thách")
        self._draw_text_with_emoji(mode_label, self.font_small, COLOR_TEXT_TITLE, sx + sw // 2, y, center=True)
        y += 30

        # ---- Điểm số ----
        self._draw_panel_label("ĐIỂM SỐ", sx, y, sw)
        y += 30
        score_txt = f"{manager.score:,}"
        self._draw_text(score_txt, self.font_large, COLOR_WHITE,
                        sx + sw // 2, y, center=True)
        y += 40

        # ---- Xu ----
        self._draw_panel_label("XU", sx, y, sw)
        y += 30
        coin_txt = f"💰 {manager.coins}"
        self._draw_text_with_emoji(coin_txt, self.font_large, COLOR_YELLOW, sx + sw // 2, y, center=True)
        y += 44

        # ---- Thời gian hoặc Lượt đi ----
        if manager.mode == GameMode.BASIC:
            self._draw_panel_label("THỜI GIAN", sx, y, sw)
            y += 30
            time_str = manager.get_time_formatted()
            time_color = manager.get_time_color()
            self._draw_text(time_str, self.font_large, time_color,
                            sx + sw // 2, y, center=True)
            y += 10

            # Thanh tiến trình thời gian
            bar_w = sw - 20
            ratio = manager.time_left / BASIC_TIME_LIMIT
            bar_rect = pygame.Rect(sx + 10, y + 30, bar_w, 14)
            pygame.draw.rect(self.screen, (40, 20, 60), bar_rect, border_radius=7)
            fill_w = int(bar_w * max(0.0, ratio))
            if fill_w > 0:
                fill_rect = pygame.Rect(sx + 10, y + 30, fill_w, 14)
                pygame.draw.rect(self.screen, time_color, fill_rect, border_radius=7)
            pygame.draw.rect(self.screen, (100, 60, 140), bar_rect, 2, border_radius=7)
            y += 56

        else:
            self._draw_panel_label("LƯỢT ĐI CÒN LẠI", sx, y, sw)
            y += 22
            moves_color = (COLOR_RED if manager.moves_left <= 5
                           else COLOR_GREEN if manager.moves_left > 10
            else COLOR_YELLOW)
            moves_txt = str(manager.moves_left)
            self._draw_text(moves_txt, self.font_large, moves_color,
                            sx + sw // 2, y, center=True)
            y += 10
            # Mục tiêu điểm
            target_txt = f"Mục tiêu: {manager.score_target:,}"
            self._draw_text(target_txt, self.font_small, COLOR_TEXT_BODY,
                            sx + sw // 2, y + 28, center=True)
            y += 56

        # ---- Vật phẩm trong kho ----
        self._draw_panel_label("KHO VẬT PHẨM", sx, y, sw)
        y += 24
        y = self._draw_inventory(manager, sx, y, sw)
        y += 10

        # ---- Nút Shop / Mission ----
        btn_shop = pygame.Rect(sx + 5, y, sw - 10, 40)
        self._draw_button(btn_shop, "🛒 Cửa Hàng", self.font_small,
                          key="open_shop", primary_color=(60, 120, 200))
        self.btn_rects["open_shop"] = btn_shop
        y += 50

        completable = manager.count_completable_missions()
        miss_label = f"📋 Nhiệm Vụ" + (f" ✔{completable}" if completable else "")
        btn_miss = pygame.Rect(sx + 5, y, sw - 10, 40)
        self._draw_button(btn_miss, miss_label, self.font_small,
                          key="open_mission", primary_color=(180, 140, 40))
        self.btn_rects["open_mission"] = btn_miss
        y += 60

        # ---- Nút Quay Về Menu ----
        btn_back = pygame.Rect(sx + 5, SCREEN_H - 55, sw - 10, 40)
        self._draw_button(btn_back, "< Quay Về Menu >", self.font_small,
                          key="back_menu", primary_color=(100, 40, 40))
        self.btn_rects["back_menu"] = btn_back

        # ---- Hiển thị công cụ đang kích hoạt ----
        if manager.active_tool:
            tool_names = {"hammer": "🔨 Cái Chày", "mixer": "🌀 Máy Trộn"}
            active_txt = f"Đang dùng: {tool_names.get(manager.active_tool, '')}"
            # Hộp thông báo công cụ
            notif_surf = _make_surface_with_alpha(sw - 10, 36, (200, 140, 0), 220)
            self.screen.blit(notif_surf, (sx + 5, GRID_OFFSET_Y + GRID_ROWS * CELL_SIZE - 50))
            self._draw_text_with_emoji(active_txt, self.font_small, COLOR_BLACK, sx + sw // 2,
                            GRID_OFFSET_Y + GRID_ROWS * CELL_SIZE - 33,
                            center=True)

    def _draw_inventory(self, manager, sx: int, y: int, sw: int) -> int:
        """
        Vẽ kho vật phẩm với nút kích hoạt.

        :return: Vị trí y tiếp theo sau khi vẽ xong
        """
        item_keys = ["hammer", "mixer", "extra_time", "extra_moves"]
        item_icons = {
            "hammer": "🔨",
            "mixer": "🌀",
            "extra_time": "⏱",
            "extra_moves": "🏃",
        }

        for key in item_keys:
            count = manager.inventory.get(key, 0)
            icon = item_icons[key]
            name = SHOP_ITEMS[key]["name"]

            # Nút vật phẩm
            btn = pygame.Rect(sx + 5, y, sw - 10, 34)
            active = (manager.active_tool == key)

            if count > 0:
                color = (80, 180, 80) if not active else (220, 160, 20)
            else:
                color = (50, 35, 60)

            self._draw_button(btn, f"{icon} {name}  x{count}",
                              self.font_small,
                              key=f"use_{key}",
                              primary_color=color,
                              disabled=(count == 0))
            self.btn_rects[f"use_{key}"] = btn
            y += 40

        return y

    # =========================================================================
    # SHOP OVERLAY
    # =========================================================================

    # =============================================================================
    # UI.py - SỬA HÀM _draw_shop_overlay (TĂNG CHIỀU CAO PANEL)
    # =============================================================================

    def _draw_shop_overlay(self, manager):
        """Vẽ bảng Cửa Hàng (Shop) dạng overlay trên màn hình."""
        panel_w = 520
        panel_h = 500  # Tăng từ 480 lên 500 để đủ chỗ cho 4 hàng
        panel_x = (SCREEN_W - panel_w) // 2
        panel_y = (SCREEN_H - panel_h) // 2

        # Nền tối mờ toàn màn hình
        dim = _make_surface_with_alpha(SCREEN_W, SCREEN_H, (0, 0, 0), 140)
        self.screen.blit(dim, (0, 0))

        # Panel chính
        panel = _make_surface_with_alpha(panel_w, panel_h, COLOR_BG_PANEL, 240)
        pygame.draw.rect(panel, (150, 80, 220),
                         (0, 0, panel_w, panel_h), 3, border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))

        # ---- Tiêu đề ----
        self._draw_text_shadow("🛒 CỬA HÀNG", self.font_large, COLOR_TEXT_TITLE,
                               SCREEN_W // 2, panel_y + 26, center=True)

        self._draw_text_with_emoji(f"Xu của bạn: {manager.coins} 💰",
                                   self.font_medium, COLOR_YELLOW,
                                   SCREEN_W // 2, panel_y + 62, center=True)

        pygame.draw.line(self.screen, (100, 60, 150),
                         (panel_x + 20, panel_y + 85),
                         (panel_x + panel_w - 20, panel_y + 85), 2)

        # ---- Danh sách vật phẩm (giảm khoảng cách) ----
        item_keys = list(SHOP_ITEMS.keys())
        item_y = panel_y + 96  # Giảm từ 100 xuống 96
        for key in item_keys:
            item = SHOP_ITEMS[key]
            self._draw_shop_item(manager, key, item, panel_x + 20,
                                 item_y, panel_w - 40)
            item_y += 86  # Tăng từ 82 lên 86 để phù hợp với chiều cao 80

        # ---- Nút Đóng ----
        btn_close = pygame.Rect(panel_x + panel_w // 2 - 80, panel_y + panel_h - 55, 160, 40)
        self._draw_button(btn_close, "✕ Đóng", self.font_medium,
                          key="close_shop", primary_color=(120, 40, 40))
        self.btn_rects["close_shop"] = btn_close

    # =============================================================================
    # UI.py - SỬA HÀM _draw_shop_item (BỐ CỤC LẠI VÀ DÙNG EMOJI)
    # =============================================================================

    # =============================================================================
    # UI.py - SỬA HÀM _draw_shop_item (TÁCH BIỆT HOÀN TOÀN)
    # =============================================================================

    # =============================================================================
    # UI.py - SỬA HÀM _draw_shop_item (BẢN 2 - RỘNG HƠN)
    # =============================================================================

    # =============================================================================
    # UI.py - SỬA HÀM _draw_shop_item (BẢN 3 - XU + NÚT CÙNG HÀNG NGANG)
    # =============================================================================

    def _draw_shop_item(self, manager, key: str, item: dict,
                        x: int, y: int, w: int):
        """Vẽ một hàng vật phẩm trong Shop."""
        # Nền hàng
        row_surf = _make_surface_with_alpha(w, 80, (40, 20, 70), 180)
        pygame.draw.rect(row_surf, (80, 50, 110),
                         (0, 0, w, 80), 1, border_radius=8)
        self.screen.blit(row_surf, (x, y))

        # ---- Icon (EMOJI) ----
        item_icons = {
            "hammer": "🔨",
            "mixer": "🌀",
            "extra_time": "⏱",
            "extra_moves": "🏃",
        }
        emoji = item_icons.get(key, "🛒")
        self._draw_text_with_emoji(emoji, self.font_large, COLOR_WHITE, x + 35, y + 40, center=True)

        # ---- Tên và mô tả (BÊN TRÁI) ----
        self._draw_text(item["name"], self.font_medium, COLOR_WHITE,
                        x + 72, y + 12)
        self._draw_text(item["description"], self.font_small, COLOR_TEXT_BODY,
                        x + 72, y + 38)

        # ============================================================
        # PHẦN BÊN PHẢI - KHO Ở TRÊN, XU + NÚT CÙNG HÀNG
        # ============================================================

        right_start = x + w - 155  # Vị trí bắt đầu cột bên phải

        # ---- Dòng 1: Kho (TRÊN CÙNG) ----
        count = manager.inventory.get(key, 0)
        kho_text = f"Kho: {count}"
        self._draw_text(kho_text, self.font_small, (200, 200, 200),
                        right_start, y + 8)

        # ---- Dòng 2: Giá xu + Nút Mua (CÙNG HÀNG NGANG) ----
        price = item["price"]
        can_buy = manager.coins >= price
        price_color = COLOR_YELLOW if can_buy else (150, 100, 50)

        # Vẽ giá xu bên trái
        self._draw_text_with_emoji(f"💰 {price}", self.font_medium, price_color,
                                   right_start, y + 34)

        # Vẽ nút Mua bên phải (cùng hàng với giá xu)
        btn = pygame.Rect(right_start + 70, y + 32, 68, 26)
        self._draw_button(btn, "Mua", self.font_tiny,
                          key=f"buy_{key}",
                          primary_color=COLOR_BTN_BUY if can_buy else COLOR_BTN_DISABLED,
                          disabled=not can_buy)
        self.btn_rects[f"buy_{key}"] = btn

    # =========================================================================
    # MISSION OVERLAY
    # =========================================================================

    def _draw_mission_overlay(self, manager):
        """Vẽ bảng Nhiệm Vụ (Mission) dạng overlay."""
        panel_w = 520
        panel_h = 490
        panel_x = (SCREEN_W - panel_w) // 2
        panel_y = (SCREEN_H - panel_h) // 2

        # Nền tối mờ
        dim = _make_surface_with_alpha(SCREEN_W, SCREEN_H, (0, 0, 0), 140)
        self.screen.blit(dim, (0, 0))

        # Panel chính
        panel = _make_surface_with_alpha(panel_w, panel_h, COLOR_BG_PANEL, 240)
        pygame.draw.rect(panel, (200, 150, 30),
                         (0, 0, panel_w, panel_h), 3, border_radius=14)
        self.screen.blit(panel, (panel_x, panel_y))

        # ---- Tiêu đề ----
        self._draw_text_shadow("📋 NHIỆM VỤ", self.font_large, COLOR_TEXT_TITLE,
                               SCREEN_W // 2, panel_y + 26, center=True)
        pygame.draw.line(self.screen, (150, 120, 30),
                         (panel_x + 20, panel_y + 60),
                         (panel_x + panel_w - 20, panel_y + 60), 2)

        # ---- Danh sách nhiệm vụ ----
        miss_y = panel_y + 76
        for m in manager.missions:
            self._draw_mission_item(manager, m, panel_x + 16,
                                    miss_y, panel_w - 32)
            miss_y += 88

        # ---- Nút Đóng ----
        btn_close = pygame.Rect(panel_x + panel_w // 2 - 80,
                                panel_y + panel_h - 55, 160, 40)
        self._draw_button(btn_close, "X Đóng", self.font_medium,
                          key="close_mission", primary_color=(100, 60, 20))
        self.btn_rects["close_mission"] = btn_close

    def _draw_mission_item(self, manager, mission: dict, x: int, y: int, w: int):
        """Vẽ một hàng nhiệm vụ trong bảng Mission."""
        completed = mission["progress"] >= mission["target"]
        claimed = mission["claimed"]

        # Nền hàng
        bg_color = (30, 60, 30) if completed and not claimed else (30, 20, 50)
        if claimed:
            bg_color = (20, 40, 20)
        row_surf = _make_surface_with_alpha(w, 78, bg_color, 200)
        border_c = (100, 200, 50) if completed and not claimed else (80, 50, 100)
        pygame.draw.rect(row_surf, border_c, (0, 0, w, 78), 2, border_radius=8)
        self.screen.blit(row_surf, (x, y))

        # Tên nhiệm vụ
        name_color = COLOR_YELLOW if completed and not claimed else COLOR_TEXT_BODY
        self._draw_text(mission["name"], self.font_medium, name_color, x + 12, y + 10)

        # ---- Mô tả + Progress (SỬA: CHỮ THƯỜNG VÀ CÙNG HÀNG) ----
        desc = mission["description"]
        prog = mission["progress"]
        target = mission["target"]

        # SỬA 1: Chữ thường (dùng lower() hoặc viết thường trong settings)
        # SỬA 2: Progress cùng hàng với mô tả
        prog_text = f"{desc}  ({prog}/{target})"

        # Màu cho progress
        prog_color = (100, 255, 100) if completed else COLOR_TEXT_BODY

        # Vẽ mô tả + progress trên cùng 1 dòng
        self._draw_text(prog_text, self.font_small, prog_color, x + 12, y + 34)

        # Thanh tiến độ
        bar_w = w - 160
        bar_rect = pygame.Rect(x + 12, y + 62, bar_w, 10)
        pygame.draw.rect(self.screen, (40, 30, 60), bar_rect, border_radius=5)
        fill_w = int(bar_w * min(1.0, prog / max(1, target)))
        if fill_w > 0:
            fill_color = (80, 200, 60) if completed else (100, 120, 220)
            fill_rect = pygame.Rect(x + 12, y + 62, fill_w, 10)
            pygame.draw.rect(self.screen, fill_color, fill_rect, border_radius=5)

        # Phần thưởng
        self._draw_text_with_emoji(f"💰 {mission['reward_coin']}",
                        self.font_small, COLOR_YELLOW,
                        x + w - 130, y + 14)

        # Nút Nhận Thưởng hoặc trạng thái
        if claimed:
            self._draw_text_with_emoji("✓ Đã nhận", self.font_small, COLOR_GREEN,
                            x + w - 115, y + 44)
        elif completed:
            btn = pygame.Rect(x + w - 130, y + 36, 118, 34)
            self._draw_button(btn, "Nhận Thưởng", self.font_tiny,
                              key=f"claim_{mission['id']}",
                              primary_color=COLOR_BTN_CLAIM)
            self.btn_rects[f"claim_{mission['id']}"] = btn
        else:
            self._draw_text("Chưa xong", self.font_tiny, (120, 100, 140),
                            x + w - 115, y + 44)

    # =========================================================================
    # GAME OVER / LEVEL WIN
    # =========================================================================

    def _draw_game_over(self, manager):
        """Vẽ màn hình kết thúc (thua)."""
        self._draw_end_screen(manager, win=False)

    def _draw_level_win(self, manager):
        """Vẽ màn hình kết thúc (thắng)."""
        self._draw_end_screen(manager, win=True)

    def _draw_end_screen(self, manager, win: bool):
        """
        Vẽ màn hình kết thúc chung.

        :param win: True = thắng, False = thua
        """
        cx = SCREEN_W // 2

        # Overlay tối
        dim = _make_surface_with_alpha(SCREEN_W, SCREEN_H, (0, 0, 0), 180)
        self.screen.blit(dim, (0, 0))

        # Panel trung tâm
        pw, ph = 420, 320
        px, py = cx - pw // 2, SCREEN_H // 2 - ph // 2
        panel = _make_surface_with_alpha(pw, ph, COLOR_BG_PANEL, 240)
        border_color = (80, 200, 80) if win else (200, 60, 60)
        pygame.draw.rect(panel, border_color, (0, 0, pw, ph), 3, border_radius=14)
        self.screen.blit(panel, (px, py))

        # Tiêu đề
        if win:
            title = "🎉 CHIẾN THẮNG! 🎉"
            title_color = (100, 255, 100)
        else:
            title = "💀 KẾT THÚC "
            title_color = (255, 100, 100)

        wobble = math.sin(self._title_anim_t * 3) * 4
        self._draw_text_shadow(title, self.font_large, title_color,
                               cx, py + 40 + wobble, center=True)

        # Thống kê
        self._draw_text(f"Điểm: {manager.score:,}", self.font_medium, COLOR_WHITE,
                        cx, py + 100, center=True)
        self._draw_text(f"Điểm cao nhất: {manager.high_score:,}",
                        self.font_small, COLOR_TEXT_BODY,
                        cx, py + 132, center=True)
        self._draw_text_with_emoji(f"Xu hiện tại: {manager.coins} 💰",
                        self.font_small, COLOR_YELLOW,
                        cx, py + 160, center=True)

        # Nút Chơi Lại và Menu
        btn_replay = pygame.Rect(cx - 180, py + 200, 170, 50)
        self._draw_button(btn_replay, "🔄 Chơi Lại", self.font_medium,
                          key="replay", primary_color=(60, 120, 200))
        self.btn_rects["replay"] = btn_replay

        btn_menu = pygame.Rect(cx + 10, py + 200, 170, 50)
        self._draw_button(btn_menu, "🏠 Menu Chính", self.font_medium,
                          key="to_menu", primary_color=(100, 50, 150))
        self.btn_rects["to_menu"] = btn_menu

    # =========================================================================
    # THÔNG BÁO VÀ POPUP ĐIỂM
    # =========================================================================

    def _draw_notification(self, manager):
        """Vẽ thông báo tạm thời ở trên cùng màn hình."""
        if not manager.notification:
            return

        # Fade in/out
        alpha = 255
        if manager.notification_timer < 0.4:
            alpha = int(255 * (manager.notification_timer / 0.4))

        notif_surf = pygame.Surface((600, 44), pygame.SRCALPHA)
        pygame.draw.rect(notif_surf, (20, 10, 40, int(alpha * 0.85)),
                         (0, 0, 600, 44), border_radius=10)
        pygame.draw.rect(notif_surf, (120, 80, 200, alpha),
                         (0, 0, 600, 44), 2, border_radius=10)

        txt = self.font_medium.render(manager.notification, True,
                                      (*COLOR_TEXT_TITLE, alpha))
        txt_rect = txt.get_rect(center=(300, 22))
        notif_surf.blit(txt, txt_rect)
        self.screen.blit(notif_surf, (SCREEN_W // 2 - 300, 14))

    def _draw_score_popups(self, manager):
        """Vẽ popup điểm nổi lên (floating score text)."""
        # Vị trí mặc định của popup (giữa bàn chơi)
        base_x = 370
        base_y = SCREEN_H // 2

        for i, p in enumerate(manager.score_popups[-5:]):
            t = p["timer"]
            alpha = int(255 * (1.0 - t / p["max"]))
            y_off = int(-60 * (t / p["max"]))

            if alpha <= 0:
                continue

            color = (*COLOR_YELLOW, alpha)
            txt = self.font_medium.render(p["text"], True, color[:3])
            txt.set_alpha(alpha)
            tx = base_x + i * 40 - 80
            ty = base_y + y_off - i * 20
            self.screen.blit(txt, (tx, ty))

    # =========================================================================
    # HELPER VẼ
    # =========================================================================

    def _draw_button(self, rect: pygame.Rect, text: str,
                     font: pygame.font.Font, key: str = "",
                     primary_color: tuple = (80, 40, 120),
                     disabled: bool = False):
        """
        Vẽ nút bấm với hiệu ứng hover.

        :param rect: Hình chữ nhật của nút
        :param text: Văn bản trên nút
        :param font: Font chữ
        :param key: Khóa nhận dạng (để kiểm tra hover)
        :param primary_color: Màu nền chính
        :param disabled: True = nút bị vô hiệu hóa
        """
        if disabled:
            color = (50, 35, 60)
        elif rect.collidepoint(self.mouse_pos):
            # Hover: sáng hơn 30%
            color = tuple(min(255, int(c * 1.3)) for c in primary_color)
        else:
            color = primary_color

        pygame.draw.rect(self.screen, color, rect, border_radius=8)
        pygame.draw.rect(self.screen, (min(255, color[0] + 60),
                                       min(255, color[1] + 60),
                                       min(255, color[2] + 60)),
                         rect, 2, border_radius=8)

        # Chữ (hỗ trợ emoji để tránh hiện ô vuông trống khi font chữ
        # tiếng Việt không có glyph emoji)
        txt_color = (150, 130, 150) if disabled else COLOR_WHITE
        surf = self._compose_text_emoji_surface(text, font, txt_color)
        self.screen.blit(surf, surf.get_rect(center=rect.center))

    def _draw_text(self, text: str, font: pygame.font.Font, color: tuple,
                   x: int, y: int, center: bool = False):
        """Vẽ văn bản lên màn hình."""
        surf = font.render(text, True, color)
        if center:
            self.screen.blit(surf, surf.get_rect(center=(x, y)))
        else:
            self.screen.blit(surf, (x, y))

    def _draw_text_shadow(self, text: str, font: pygame.font.Font, color: tuple,
                          x: int, y: int, center: bool = False,
                          shadow_offset: int = 3):
        """Vẽ văn bản có bóng đổ để nổi bật hơn (hỗ trợ emoji)."""
        shadow_surf = self._compose_text_emoji_surface(text, font, (0, 0, 0))
        if center:
            sr = shadow_surf.get_rect(center=(x + shadow_offset, y + shadow_offset))
            self.screen.blit(shadow_surf, sr)
        else:
            self.screen.blit(shadow_surf, (x + shadow_offset, y + shadow_offset))

        self._draw_text_with_emoji(text, font, color, x, y, center)

    def _draw_panel_label(self, text: str, x: int, y: int, w: int):
        """Vẽ nhãn section nhỏ trong Sidebar."""
        surf = self.font_tiny.render(text, True, (160, 130, 200))
        self.screen.blit(surf, (x + (w - surf.get_width()) // 2, y))

    # =========================================================================
    # XỬ LÝ SỰ KIỆN CLICK
    # =========================================================================

    def handle_click(self, pos: Tuple[int, int], manager, grid) -> str:
        """
        Xử lý click chuột vào các nút UI.
        Trả về tên hành động đã thực hiện (để main.py xử lý thêm nếu cần).

        :param pos: Tọa độ click (x, y)
        :param manager: GameEngine
        :param grid: Grid object
        :return: Chuỗi tên hành động hoặc "" nếu không có
        """
        for key, rect in self.btn_rects.items():
            if not rect.collidepoint(pos):
                continue

            # ---- Menu chính ----
            if key == "menu_basic":
                manager.start_game(GameMode.BASIC)
                grid.initialize(GameMode.BASIC)
                return "start_basic"

            if key == "menu_challenge":
                manager.start_game(GameMode.CHALLENGE)
                grid.initialize(GameMode.CHALLENGE)
                return "start_challenge"

            if key == "menu_mission":
                manager.return_state = manager.state
                manager.state = State.MISSION
                return "open_mission"

            if key == "menu_shop":
                manager.return_state = manager.state
                manager.state = State.SHOP
                return "open_shop"

            # ---- HUD Sidebar ----
            if key == "open_shop":
                manager.return_state = manager.state
                manager.state = State.SHOP
                return "open_shop"

            if key == "open_mission":
                manager.return_state = manager.state
                manager.state = State.MISSION
                return "open_mission"

            if key == "back_menu":
                manager.cancel_active_tool()
                manager.reset_to_menu()
                return "back_menu"

            # ---- Kho vật phẩm ----
            if key.startswith("use_"):
                item_key = key[4:]
                if item_key == "mixer":
                    manager.apply_mixer_to_grid(grid)
                else:
                    manager.use_item(item_key)
                return f"use_{item_key}"

            # ---- Shop ----
            if key.startswith("buy_"):
                item_key = key[4:]
                manager.buy_item(item_key)
                return f"buy_{item_key}"

            if key == "close_shop":
                manager.state = manager.return_state
                return "close_shop"

            # ---- Mission ----
            if key.startswith("claim_"):
                mission_id = key[6:]
                manager.claim_mission_reward(mission_id)
                return f"claim_{mission_id}"

            if key == "close_mission":
                manager.state = manager.return_state
                return "close_mission"

            # ---- End Screen ----
            if key == "replay":
                manager.start_game(manager.mode)
                grid.initialize(manager.mode)
                return "replay"

            if key == "to_menu":
                manager.reset_to_menu()
                return "to_menu"

        return ""