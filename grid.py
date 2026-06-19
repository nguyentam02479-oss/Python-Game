# =============================================================================
# FILE: grid.py
# Mô tả: Quản lý ma trận lưới 8x8 và toàn bộ logic cốt lõi Match-3
# =============================================================================

import pygame
import random
from typing import List, Optional, Set, Tuple

from settings import (
    GRID_ROWS, GRID_COLS, CELL_SIZE, GameMode, PieceType,
    GRID_OFFSET_X, GRID_OFFSET_Y,
    COLOR_GRID_LINE, COLOR_CELL_HOVER, COLOR_CELL_SELECT,
    CHALLENGE_FROZEN_CHANCE, CHALLENGE_COIN_CHANCE,
    BASIC_SCORE_PER_PIECE, BASIC_COMBO_MULTIPLIER,
    CHALLENGE_SCORE_PER_PIECE, PIECE_COLORS
)
from piece import CakePiece
# grid.py - SỬA DÒNG IMPORT

from piece import CakePiece, PARTICLE_EFFECTS, ParticleEffect, update_particles, draw_particles, clear_particles
# Danh sách các loại bánh ngọt thông thường (không tính WILDCARD)
NORMAL_TYPES = [
    PieceType.CAKE1, PieceType.CAKE2, PieceType.CAKE3,
    PieceType.CAKE4, PieceType.CAKE5, PieceType.CAKE6, PieceType.CAKE7,
]


class Grid:
    """
    Quản lý bàn chơi Match-3 dạng lưới 8x8.
    Chứa toàn bộ logic: tìm match, xóa viên, làm đầy bàn,
    hoán đổi viên, và vẽ lưới.
    """

    # grid.py - SỬA HÀM __init__

    def __init__(self):
        """Khởi tạo lưới rỗng."""
        self.grid: List[List[Optional[CakePiece]]] = [
            [None] * GRID_COLS for _ in range(GRID_ROWS)
        ]

        self.selected_pos: Optional[Tuple[int, int]] = None
        self.hover_pos: Optional[Tuple[int, int]] = None

        self.is_animating = False
        self.combo_count = 0
        self._free_swap = False
        self.current_mode: GameMode = GameMode.BASIC

    # =========================================================================
    # KHỞI TẠO VÀ LẤP ĐẦY BÀN CHƠI
    # =========================================================================

    # grid.py - SỬA HÀM initialize

    def initialize(self, mode: GameMode):
        """Khởi tạo/reset toàn bộ bàn chơi mới."""
        self.current_mode = mode
        self.combo_count = 0
        self.selected_pos = None
        clear_particles()  # THÊM DÒNG NÀY

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                ptype = self._pick_type_no_match(r, c)
                piece = CakePiece(ptype, r, c)
                piece.snap_to_target()
                self.grid[r][c] = piece

        if mode == GameMode.CHALLENGE:
            self._add_frozen_and_coins()

    def _pick_type_no_match(self, row: int, col: int) -> PieceType:
        """
        Chọn loại bánh ngẫu nhiên sao cho không tạo ra match-3 ngay lập tức
        với các ô bên trái và bên trên (đã được điền trước).

        :param row: Hàng hiện tại
        :param col: Cột hiện tại
        :return: PieceType không tạo match
        """
        excluded: Set[PieceType] = set()

        # Kiểm tra 2 ô bên trái
        if col >= 2:
            left1 = self.grid[row][col - 1]
            left2 = self.grid[row][col - 2]
            if left1 and left2 and left1.piece_type == left2.piece_type:
                excluded.add(left1.piece_type)

        # Kiểm tra 2 ô bên trên
        if row >= 2:
            up1 = self.grid[row - 1][col]
            up2 = self.grid[row - 2][col]
            if up1 and up2 and up1.piece_type == up2.piece_type:
                excluded.add(up1.piece_type)

        # Chọn ngẫu nhiên từ danh sách hợp lệ
        available = [t for t in NORMAL_TYPES if t not in excluded]
        if not available:
            available = NORMAL_TYPES[:]
        return random.choice(available)

    def _add_frozen_and_coins(self):
        """
        Thêm ngẫu nhiên ô đóng băng và xu vào bàn chơi (chỉ dành cho Challenge Mode).
        Tránh đặt băng và xu trên cùng một ô.
        """
        frozen_cells: Set[Tuple[int, int]] = set()
        coin_cells: Set[Tuple[int, int]] = set()

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if random.random() < CHALLENGE_FROZEN_CHANCE:
                    frozen_cells.add((r, c))

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                # Không đặt xu vào ô đã bị băng
                if (r, c) not in frozen_cells:
                    if random.random() < CHALLENGE_COIN_CHANCE:
                        coin_cells.add((r, c))

        for (r, c) in frozen_cells:
            if self.grid[r][c]:
                self.grid[r][c].is_frozen = True

        for (r, c) in coin_cells:
            if self.grid[r][c]:
                self.grid[r][c].has_coin = True

    # =========================================================================
    # LOGIC MATCH-3
    # =========================================================================

    def check_matches(self) -> List[Set[Tuple[int, int]]]:
        """
        Tìm tất cả các chuỗi match-3 trở lên trên bàn chơi,
        theo cả chiều ngang và chiều dọc.

        :return: Danh sách các nhóm ô match, mỗi nhóm là set các (row, col).
                 Có thể có ô thuộc nhiều nhóm (ô giao nhau).
        """
        matched_sets: List[Set[Tuple[int, int]]] = []
        all_matched: Set[Tuple[int, int]] = set()

        # ---- Quét theo chiều ngang ----
        for r in range(GRID_ROWS):
            c = 0
            while c < GRID_COLS:
                p = self.grid[r][c]
                if p is None or p.is_frozen:
                    c += 1
                    continue

                # Đếm số viên kế tiếp cùng loại
                run_end = c + 1
                while run_end < GRID_COLS:
                    q = self.grid[r][run_end]
                    if q and not q.is_frozen and p.matches_with(q):
                        run_end += 1
                    else:
                        break

                # Nếu có ít nhất 3 viên liên tiếp
                if run_end - c >= 3:
                    group = {(r, col) for col in range(c, run_end)}
                    matched_sets.append(group)
                    all_matched.update(group)

                c = run_end if run_end > c else c + 1

        # ---- Quét theo chiều dọc ----
        for c in range(GRID_COLS):
            r = 0
            while r < GRID_ROWS:
                p = self.grid[r][c]
                if p is None or p.is_frozen:
                    r += 1
                    continue

                run_end = r + 1
                while run_end < GRID_ROWS:
                    q = self.grid[run_end][c]
                    if q and not q.is_frozen and p.matches_with(q):
                        run_end += 1
                    else:
                        break

                if run_end - r >= 3:
                    group = {(row, c) for row in range(r, run_end)}
                    matched_sets.append(group)
                    all_matched.update(group)

                r = run_end if run_end > r else r + 1

        return matched_sets

    def eliminate_matches(self, manager) -> int:
        """
        Xóa tất cả các viên kẹo đang trong trạng thái match.
        - Tích điểm cho người chơi (qua manager)
        - Nếu viên chứa xu: cộng coin vào manager.coins
        - Nếu viên kề với ô đóng băng: phá băng ô đó
        - Nếu viên WILDCARD nằm trong match: tính điểm nhân đôi
        - Tăng combo_count khi liên tiếp

        :param manager: Tham chiếu đến GameEngine (để cộng điểm, xu, combo)
        :return: Tổng số viên kẹo đã xóa trong lần này
        """
        match_groups = self.check_matches()
        if not match_groups:
            self.combo_count = 0
            return 0

        # Gộp tất cả ô cần xóa
        to_eliminate: Set[Tuple[int, int]] = set()
        for group in match_groups:
            to_eliminate.update(group)

        if not to_eliminate:
            return 0

        # Tăng combo
        self.combo_count += 1

        # Tính điểm
        base_score = (CHALLENGE_SCORE_PER_PIECE
                      if self.current_mode == GameMode.CHALLENGE
                      else BASIC_SCORE_PER_PIECE)
        combo_mult = 1.0 + (self.combo_count - 1) * BASIC_COMBO_MULTIPLIER
        total_score = 0
        coins_earned = 0
        frozen_broken = 0
        pieces_destroyed = 0

        # Tập hợp các ô bị phá băng (ô kề với match)
        ice_to_break: Set[Tuple[int, int]] = set()

        for (r, c) in to_eliminate:
            piece = self.grid[r][c]
            if piece is None:
                continue

            # Điểm cho viên kẹo
            piece_score = base_score
            if piece.piece_type == PieceType.WILDCARD:
                piece_score *= 2
            total_score += piece_score

            # Nếu có xu: cộng coin
            if piece.has_coin:
                coins_earned += 5  # Mỗi xu = 5 coin

            # Kích hoạt hiệu ứng nổ
            piece.start_explode()
            pieces_destroyed += 1

            # Kiểm tra ô kề: phá băng nếu ô bên cạnh bị đóng băng
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < GRID_ROWS and 0 <= nc < GRID_COLS:
                    neighbor = self.grid[nr][nc]
                    if neighbor and neighbor.is_frozen:
                        ice_to_break.add((nr, nc))

        # Phá băng ô kề
        for (r, c) in ice_to_break:
            piece = self.grid[r][c]
            if piece:
                piece.is_frozen = False
                frozen_broken += 1

        # Ghi nhận vào manager
        final_score = int(total_score * combo_mult)
        manager.add_score(final_score, combo=self.combo_count)
        manager.add_coins(coins_earned)
        manager.notify_pieces_destroyed(pieces_destroyed, frozen_broken,
                                        self.combo_count)

        # Xóa các ô đã match khỏi lưới (set = None)
        for (r, c) in to_eliminate:
            self.grid[r][c] = None

        return pieces_destroyed

    # =========================================================================
    # HOÁN ĐỔI VIÊN KẸO
    # =========================================================================

    # grid.py - SỬA HÀM swap_pieces (THÊM HIỆU ỨNG KHI SWAP)

    def swap_pieces(self, r1: int, c1: int, r2: int, c2: int, free: bool = False) -> bool:
        """Hoán đổi hai viên kẹo và kiểm tra tính hợp lệ."""
        if not (0 <= r1 < GRID_ROWS and 0 <= c1 < GRID_COLS and
                0 <= r2 < GRID_ROWS and 0 <= c2 < GRID_COLS):
            return False

        p1 = self.grid[r1][c1]
        p2 = self.grid[r2][c2]

        if p1 is None or p2 is None:
            return False

        if not free and (p1.is_frozen or p2.is_frozen):
            return False

        self._do_swap(r1, c1, r2, c2)

        if not free:
            has_match = len(self.check_matches()) > 0
            if not has_match:
                self._do_swap(r1, c1, r2, c2)
                return False
            else:
                # THÊM HIỆU ỨNG KHI SWAP THÀNH CÔNG
                p1 = self.grid[r1][c1]
                p2 = self.grid[r2][c2]
                if p1 and p2:
                    color1 = PIECE_COLORS.get(p1.piece_type, (255, 255, 255))
                    color2 = PIECE_COLORS.get(p2.piece_type, (255, 255, 255))

                    effect1 = ParticleEffect(
                        p1.x + CELL_SIZE // 2,
                        p1.y + CELL_SIZE // 2,
                        color1,
                        count=8
                    )
                    effect2 = ParticleEffect(
                        p2.x + CELL_SIZE // 2,
                        p2.y + CELL_SIZE // 2,
                        color2,
                        count=8
                    )
                    PARTICLE_EFFECTS.append(effect1)
                    PARTICLE_EFFECTS.append(effect2)

        return True

    def _do_swap(self, r1: int, c1: int, r2: int, c2: int):
        """
        Thực hiện hoán đổi thực sự (không kiểm tra hợp lệ).
        Cập nhật cả lưới lẫn tọa độ target của từng viên.

        :param r1, c1, r2, c2: Vị trí hai ô cần đổi
        """
        self.grid[r1][c1], self.grid[r2][c2] = \
            self.grid[r2][c2], self.grid[r1][c1]

        # Cập nhật tọa độ logic cho từng viên
        if self.grid[r1][c1]:
            self.grid[r1][c1].set_target(r1, c1)
        if self.grid[r2][c2]:
            self.grid[r2][c2].set_target(r2, c2)

    def random_swap_two(self):
        """
        Hoán đổi ngẫu nhiên 2 ô trên bàn chơi (công cụ Máy Trộn).
        Không yêu cầu tạo match.
        """
        # Thu thập tất cả ô có viên kẹo không bị đóng băng
        available = [
            (r, c)
            for r in range(GRID_ROWS)
            for c in range(GRID_COLS)
            if self.grid[r][c] is not None and not self.grid[r][c].is_frozen
        ]

        if len(available) < 2:
            return

        (r1, c1), (r2, c2) = random.sample(available, 2)
        self._do_swap(r1, c1, r2, c2)

    def destroy_piece(self, r: int, c: int, manager) -> bool:
        """
        Phá hủy viên kẹo ở vị trí (r, c) bằng công cụ Cái Chày.
        Cộng điểm và xu nếu có.

        :param r, c: Vị trí cần phá
        :param manager: Tham chiếu GameEngine
        :return: True nếu thực hiện được
        """
        if not (0 <= r < GRID_ROWS and 0 <= c < GRID_COLS):
            return False

        piece = self.grid[r][c]
        if piece is None:
            return False

        # Cộng điểm
        base = (CHALLENGE_SCORE_PER_PIECE
                if self.current_mode == GameMode.CHALLENGE
                else BASIC_SCORE_PER_PIECE)
        manager.add_score(base * 2)  # Chày x2 điểm

        # Nếu có xu
        if piece.has_coin:
            manager.add_coins(5)

        # Phá băng nếu là ô đóng băng
        if piece.is_frozen:
            manager.notify_pieces_destroyed(1, 1, self.combo_count)
        else:
            manager.notify_pieces_destroyed(1, 0, self.combo_count)

        piece.start_explode()
        self.grid[r][c] = None
        return True

    # =========================================================================
    # LẤP ĐẦY BÀN CHƠI (RƠI XUỐNG VÀ TẠO MỚI)
    # =========================================================================

    def apply_gravity(self):
        """
        Áp dụng trọng lực: tất cả các viên kẹo rơi xuống để lấp đầy chỗ trống.
        Viên bị đóng băng KHÔNG rơi.
        """
        for c in range(GRID_COLS):
            # Từ hàng dưới lên trên, lấp đầy ô trống bằng cách kéo viên trên xuống
            write_row = GRID_ROWS - 1
            for read_row in range(GRID_ROWS - 1, -1, -1):
                piece = self.grid[read_row][c]
                if piece is not None:
                    if not piece.is_frozen:
                        # Di chuyển xuống write_row
                        self.grid[write_row][c] = piece
                        if write_row != read_row:
                            self.grid[read_row][c] = None
                            piece.set_target(write_row, c)
                        write_row -= 1
                    else:
                        # Ô đóng băng: không di chuyển, nhưng dời write_row
                        write_row = read_row - 1

    def refill_board(self):
        """
        Tạo viên kẹo mới lấp đầy các ô còn trống (sau khi gravity).
        Viên mới xuất hiện từ trên đỉnh lưới và rơi xuống (hiệu ứng Lerp).
        Ở chế độ Challenge: có xác suất nhỏ tạo viên bị đóng băng hoặc có xu.
        """
        for c in range(GRID_COLS):
            spawn_row = 0  # Bộ đếm số viên cần spawn từ trên

            for r in range(GRID_ROWS):
                if self.grid[r][c] is None:
                    # Tạo loại ngẫu nhiên
                    ptype = random.choice(NORMAL_TYPES)
                    piece = CakePiece(ptype, r, c)

                    # Spawn từ trên màn hình (rơi vào)
                    spawn_y = GRID_OFFSET_Y - (spawn_row + 1) * CELL_SIZE
                    piece.x = float(GRID_OFFSET_X + c * CELL_SIZE)
                    piece.y = float(spawn_y)
                    piece.target_x = float(GRID_OFFSET_X + c * CELL_SIZE)
                    piece.target_y = float(GRID_OFFSET_Y + r * CELL_SIZE)

                    # Thêm đặc tính đặc biệt nếu đang ở Challenge Mode
                    if self.current_mode == GameMode.CHALLENGE:
                        if random.random() < CHALLENGE_FROZEN_CHANCE * 0.5:
                            piece.is_frozen = True
                        elif random.random() < CHALLENGE_COIN_CHANCE * 0.5:
                            piece.has_coin = True

                    self.grid[r][c] = piece
                    spawn_row += 1

    def has_empty_cells(self) -> bool:
        """Kiểm tra có ô trống nào trên bàn không."""
        return any(self.grid[r][c] is None
                   for r in range(GRID_ROWS)
                   for c in range(GRID_COLS))

    def is_animating_pieces(self) -> bool:
        """
        Kiểm tra có viên kẹo nào đang di chuyển (chưa đến đích) không.
        Dùng để chặn input trong lúc hoạt ảnh đang chạy.
        """
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.grid[r][c]
                if p and not p.is_at_target():
                    return True
        return False

    def has_exploding_pieces(self) -> bool:
        """Kiểm tra có viên kẹo nào đang trong hiệu ứng nổ không."""
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.grid[r][c]
                if p and p.explode_active and p.explode_timer < 0.3:
                    return True
        return False

    # =========================================================================
    # INPUT XỬ LÝ
    # =========================================================================

    def get_cell_at_pixel(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        """
        Chuyển đổi tọa độ pixel chuột sang (hàng, cột) trong lưới.
        Trả về None nếu ngoài bàn chơi.

        :param px, py: Tọa độ pixel
        :return: (row, col) hoặc None
        """
        rel_x = px - GRID_OFFSET_X
        rel_y = py - GRID_OFFSET_Y

        if rel_x < 0 or rel_y < 0:
            return None

        c = rel_x // CELL_SIZE
        r = rel_y // CELL_SIZE

        if 0 <= r < GRID_ROWS and 0 <= c < GRID_COLS:
            return (r, c)
        return None

    def handle_click(self, px: int, py: int, manager) -> bool:
        """
        Xử lý click chuột trái vào bàn chơi.
        - Click lần 1: chọn ô
        - Click lần 2: nếu ô kề -> thử swap; nếu không kề -> đổi ô chọn

        :param px, py: Tọa độ pixel click
        :param manager: GameEngine để ghi nhận lượt đi
        :return: True nếu có swap xảy ra
        """
        cell = self.get_cell_at_pixel(px, py)
        if cell is None:
            self.selected_pos = None
            return False

        r, c = cell

        # Không cho chọn ô trống
        if self.grid[r][c] is None:
            self.selected_pos = None
            return False

        # Nếu đang dùng công cụ Chày
        if manager.active_tool == "hammer":
            success = self.destroy_piece(r, c, manager)
            manager.active_tool = None
            return success

        if self.selected_pos is None:
            # Lần chọn đầu tiên
            self.selected_pos = (r, c)
            if self.grid[r][c]:
                self.grid[r][c].is_selected = True
        else:
            prev_r, prev_c = self.selected_pos
            # Bỏ chọn ô cũ
            if self.grid[prev_r][prev_c]:
                self.grid[prev_r][prev_c].is_selected = False

            # Kiểm tra ô kề nhau (chỉ trên/dưới/trái/phải)
            is_adjacent = (abs(r - prev_r) + abs(c - prev_c) == 1)

            if is_adjacent:
                # Thử hoán đổi
                free_swap = (manager.active_tool == "mixer")
                success = self.swap_pieces(prev_r, prev_c, r, c, free=free_swap)
                if manager.active_tool == "mixer":
                    manager.active_tool = None
                if success:
                    manager.use_move()  # Trừ lượt đi
                self.selected_pos = None
                return success
            else:
                # Không kề: chọn lại ô mới
                self.selected_pos = (r, c)
                if self.grid[r][c]:
                    self.grid[r][c].is_selected = True

        return False

    def set_hover(self, px: int, py: int):
        """Cập nhật ô đang được rê chuột."""
        self.hover_pos = self.get_cell_at_pixel(px, py)

    # =========================================================================
    # CẬP NHẬT VÀ VẼ
    # =========================================================================

    # grid.py - SỬA HÀM update

    def update(self, dt: float):
        """Cập nhật tất cả viên kẹo và hiệu ứng trên lưới mỗi frame."""
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.grid[r][c]
                if p:
                    p.update(dt)

        update_particles(dt)  # THÊM DÒNG NÀY

    def draw(self, surface: pygame.Surface, images_dict: dict,
             bg_image=None):
        """
        Ve ban choi. Neu truyen bg_image, blit nen that vao tung o truoc
        khi ve piece de vung alpha=0 hien ra background thay vi mau xam.
        """
        # Ve toan bo vung luoi bang background truoc (1 lan duy nhat)
        if bg_image is not None:
            grid_rect = pygame.Rect(
                GRID_OFFSET_X, GRID_OFFSET_Y,
                GRID_COLS * CELL_SIZE, GRID_ROWS * CELL_SIZE
            )
            # Fill mau solid truoc de dam bao khong co alpha
            pygame.draw.rect(surface, (0, 0, 0), grid_rect)
            surface.blit(bg_image, grid_rect, grid_rect)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                p = self.grid[r][c]
                if p is None:
                    continue
                p.draw(surface, images_dict, bg_image)

        draw_particles(surface)