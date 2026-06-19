# =============================================================================
# FILE: main.py
# Mô tả: Điểm khởi chạy chương trình (Entry Point) - Vòng lặp game chính
#        Sweet Cake Match-3 | Bánh Ngọt Kết Đôi
# =============================================================================

import pygame
import sys
import os
import save_manager                          # ← THÊM: module lưu/tải dữ liệu
from typing import Optional, Dict

# Import các module game
from settings import (
    SCREEN_W, SCREEN_H, FPS,
    State, GameMode, PieceType,
    IMAGE_BG, IMAGE_CAKES, PIECE_COLORS, CELL_SIZE,
    GRID_ROWS, GRID_COLS, GRID_OFFSET_X, GRID_OFFSET_Y,
    MISSION_SCROLL_SPEED
)
from piece import CakePiece, clear_particles
from grid import Grid
from manager import GameEngine
from UI import UIManager
from sound_manager import SoundManager  # ← THÊM: âm thanh


# =============================================================================
# LOAD ẢNH AN TOÀN
# =============================================================================

def load_image_safe(path: str,
                    size: tuple = (CELL_SIZE, CELL_SIZE)) -> Optional[pygame.Surface]:
    """
    Load ảnh nền (JPG/PNG không cần alpha) - dùng convert() để có nền solid.
    """
    if not os.path.isfile(path):
        return None
    try:
        img = pygame.image.load(path).convert()
        return pygame.transform.smoothscale(img, size)
    except Exception as e:
        print(f"[WARN] Khong the load anh nen '{path}': {e}")
        return None


def remove_checker_background(pil_img):
    """
    Xoa nen checkerboard xam den khoi anh PNG dung Pillow + numpy.
    Pixel co R~G~B (xam, it mau sac) va do sang 55-165 se thanh trong suot.
    """
    import numpy as np
    from PIL import Image as PILImage
    arr = np.array(pil_img.convert("RGBA"))
    r = arr[:,:,0].astype(int)
    g = arr[:,:,1].astype(int)
    b = arr[:,:,2].astype(int)
    saturation = np.max([np.abs(r-g), np.abs(g-b), np.abs(r-b)], axis=0)
    brightness = (r + g + b) // 3
    is_checker = (saturation < 30) & (brightness > 55) & (brightness < 165)
    arr[:,:,3] = np.where(is_checker, 0, 255)
    return PILImage.fromarray(arr)


def load_piece_image(path: str, size: tuple = (CELL_SIZE, CELL_SIZE)) -> Optional[pygame.Surface]:
    if not os.path.isfile(path):
        print(f"[DEBUG] Khong tim thay: {os.path.abspath(path)}")
        return None
    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, size)
        print(f"[OK] Loaded: {path}")
        return img
    except Exception as e:
        print(f"[WARN] Load that bai '{path}': {e}")
        return None


def load_all_images() -> tuple:
    """
    Load toàn bộ ảnh cần thiết cho game.
    - Ảnh nền Game.jpg  → convert() (không alpha)
    - Ảnh bánh cake*.png → convert_alpha() (giữ trong suốt)
    """
    # Ảnh nền - dùng convert() bình thường
    bg = load_image_safe(IMAGE_BG, (SCREEN_W, SCREEN_H))
    if bg is None:
        print("[INFO] Khong tim thay Game.jpg - se dung mau nen mac dinh.")

    # Ảnh từng loại bánh - dùng load_piece_image để giữ alpha
    pieces: Dict[PieceType, Optional[pygame.Surface]] = {}
    for ptype, filename in IMAGE_CAKES.items():
        if filename is None:
            pieces[ptype] = None
            continue
        img = load_piece_image(filename, (CELL_SIZE, CELL_SIZE))
        if img is None:
            print(f"[INFO] Khong tim thay {filename} - se dung hinh ve thay the.")
        pieces[ptype] = img

    return bg, pieces


# =============================================================================
# VÒNG LẶP GAME CHÍNH
# =============================================================================

def main():
    """Hàm khởi động và vận hành toàn bộ game."""

    # ---- Khởi tạo Pygame ----
    pygame.init()
    pygame.display.set_caption("Sweet Cake Match-3 🍰 ")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()

    # ---- Khởi tạo âm thanh (SFX sinh bằng code, không cần file) ----
    SoundManager.init()
    # Nhạc nền: đặt file của bạn vào thư mục "Audio/bg_music.mp3"
    # (hoặc đổi tên/đường dẫn cho khớp với file bạn có).
    SoundManager.play_music("Audio/bg_music.mp3", loop=True, volume=0.4)

    # Thiết lập icon cửa sổ (nếu có)
    try:
        icon = pygame.Surface((32, 32))
        icon.fill((255, 100, 150))
        pygame.draw.circle(icon, (255, 200, 220), (16, 16), 14)
        pygame.display.set_icon(icon)
    except Exception:
        pass

    # ---- Load tài nguyên ----
    print("[INFO] Đang load tài nguyên...")
    bg_image, pieces_images = load_all_images()

    # ---- Khởi tạo đối tượng chính ----
    grid = Grid()
    manager = GameEngine()
    ui = UIManager(screen)

    # ---- THÊM: Tải dữ liệu người chơi từ file JSON ----
    save_data = save_manager.load()
    save_manager.restore_to_engine(save_data, manager)
    print(save_manager.get_summary(save_data))   # In thống kê ra console

    print("[INFO] Khoi tao hoan tat. Game dang chay...")

    # Pre-scale background 1 lan de dung suot game (tranh scale moi frame)
    scaled_bg_cache = None
    board_bg_cache = None
    if bg_image:
        scaled_bg_cache = pygame.transform.scale(bg_image, (SCREEN_W, SCREEN_H))

        # Tao ban nen rieng cho khu vuc bang choi: phu lop trang nga
        # (lam mo nen) CHI trong khung luoi/cakepiece, giu nguyen nen
        # rieng cho phan con lai cua man hinh (sidebar, vien ngoai...).
        board_bg_cache = scaled_bg_cache.copy()
        ivory_overlay = pygame.Surface(
            (GRID_COLS * CELL_SIZE + 20, GRID_ROWS * CELL_SIZE + 20),
            pygame.SRCALPHA
        )
        ivory_overlay.fill((245, 240, 230, 130))
        board_bg_cache.blit(ivory_overlay, (GRID_OFFSET_X - 10, GRID_OFFSET_Y - 10))

    # ---- Biến trạng thái input ----
    dragging = False        # Đang kéo thả kẹo
    drag_start_cell = None  # Ô bắt đầu kéo (hàng, cột)
    drag_start_pos = None   # Vị trí pixel bắt đầu kéo

    # Bộ đếm pipeline xử lý match (state machine nhỏ)
    # Trạng thái: "idle" / "eliminating" / "falling" / "refilling" / "checking"
    process_state = "idle"
    process_timer = 0.0     # Delay giữa các bước xử lý

    # Cờ để tránh lưu nhiều lần cho cùng một ván kết thúc
    _game_end_saved = False

    # =========================================================================
    # VÒNG LẶP CHÍNH
    # =========================================================================
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time tính bằng giây

        # ---- Thu thập sự kiện ----
        for event in pygame.event.get():

            # Thoát game
            if event.type == pygame.QUIT:
                running = False
                break

            # Phím tắt
            if event.type == pygame.KEYDOWN:
                _handle_keydown(event, manager, grid, ui)

            # Click chuột xuống
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos

                # Xử lý click UI trước
                action = ui.handle_click(pos, manager, grid)
                if action:
                    # Nếu có action từ UI, reset pipeline
                    if action.startswith("start_") or action == "replay":
                        process_state = "checking"
                        process_timer = 0.0
                        _game_end_saved = False  # ← THÊM: reset cờ khi bắt đầu ván mới
                    elif action in ("back_menu", "to_menu"):
                        process_state = "idle"
                    # ← THÊM: lưu ngay khi mua đồ hoặc nhận thưởng nhiệm vụ
                    elif action.startswith("buy_") or action.startswith("claim_"):
                        save_manager.sync_from_engine(save_data, manager)
                        save_manager.save(save_data)
                else:
                    # Click vào bàn chơi (chỉ khi đang chơi)
                    if manager.state == State.PLAYING and process_state == "idle":
                        swapped = grid.handle_click(pos[0], pos[1], manager)
                        if swapped:
                            # Bắt đầu pipeline xử lý match
                            process_state = "eliminating"
                            process_timer = 0.0

                    # Bắt đầu kéo thả
                    if manager.state == State.PLAYING and process_state == "idle":
                        cell = grid.get_cell_at_pixel(pos[0], pos[1])
                        if cell and grid.grid[cell[0]][cell[1]]:
                            dragging = True
                            drag_start_cell = cell
                            drag_start_pos = pos

            # Kéo chuột (kéo thả)
            if event.type == pygame.MOUSEMOTION:
                grid.set_hover(event.pos[0], event.pos[1])
                ui.update(0, event.pos)  # Cập nhật vị trí chuột cho UI

            # Cuộn chuột (dùng để cuộn bảng Nhiệm Vụ khi đang mở)
            if event.type == pygame.MOUSEWHEEL:
                if manager.state == State.MISSION:
                    # event.y > 0 = cuộn lên (lăn lên), < 0 = cuộn xuống
                    ui.handle_mission_scroll(-event.y * MISSION_SCROLL_SPEED)

            # Thả chuột
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if dragging and drag_start_cell and manager.state == State.PLAYING:
                    pos = event.pos
                    _handle_drag_release(pos, drag_start_pos, drag_start_cell,
                                         grid, manager,
                                         process_state,
                                         lambda: _set_process(process_state, "eliminating"))
                    # Kiểm tra sau khi drag
                    if process_state == "idle":
                        process_state = "eliminating"

                dragging = False
                drag_start_cell = None
                drag_start_pos = None

        # =========================================================================
        # CẬP NHẬT LOGIC
        # =========================================================================

        # Cập nhật GameEngine (đếm thời gian, kiểm tra win/lose)
        manager.update(dt)
        manager.update_missions(dt)

        # Cập nhật Grid (hoạt ảnh Lerp của viên kẹo)
        if manager.state in (State.PLAYING, State.SHOP, State.MISSION):
            grid.update(dt)

        # Cập nhật UI
        mouse_pos = pygame.mouse.get_pos()
        ui.update(dt, mouse_pos)

        # ---- Pipeline xử lý Match-3 ----
        if manager.state == State.PLAYING:
            process_state, process_timer = _run_match_pipeline(
                process_state, process_timer, dt, grid, manager,
                save_data, _game_end_saved             # ← THÊM: truyền save_data
            )
            # Cập nhật lại cờ nếu pipeline vừa lưu
            if manager.state in (State.GAME_OVER, State.LEVEL_WIN):
                _game_end_saved = True

        # =========================================================================
        # VẼ
        # =========================================================================

        # Vẽ UI (bao gồm nền, menu, sidebar, overlay)
        ui.draw(manager, bg_image)

        # Vẽ bàn chơi (chỉ khi đang trong game)
        if manager.state == State.PLAYING:
            grid.draw(screen, pieces_images, board_bg_cache)

        # Vẽ con trỏ công cụ đặc biệt
        if manager.state == State.PLAYING and manager.active_tool == "hammer":
            _draw_hammer_cursor(screen, mouse_pos)

        # Cập nhật màn hình
        pygame.display.flip()

    # ---- THÊM: Lưu dữ liệu trước khi thoát ----
    save_manager.sync_from_engine(save_data, manager)
    save_manager.save(save_data)
    print("[INFO] Đã lưu dữ liệu. Tạm biệt!")

    pygame.quit()
    sys.exit(0)


# =============================================================================
# HÀM HỖ TRỢ VÒNG LẶP
# =============================================================================

def _handle_keydown(event: pygame.event.Event, manager, grid, ui):
    """
    Xử lý phím tắt bàn phím.

    Phím tắt:
    - ESC: Quay về menu / hủy công cụ
    - F5: Khởi động lại màn (nếu đang chơi)
    - S: Mở/đóng Shop nhanh
    - M: Mở/đóng Mission nhanh
    """
    if event.key == pygame.K_ESCAPE:
        if manager.active_tool:
            manager.cancel_active_tool()
        elif manager.state in (State.SHOP, State.MISSION):
            manager.state = manager.return_state
        elif manager.state == State.PLAYING:
            manager.reset_to_menu()

    elif event.key == pygame.K_F5:
        if manager.state in (State.PLAYING, State.GAME_OVER, State.LEVEL_WIN):
            manager.start_game(manager.mode)
            grid.initialize(manager.mode)

    elif event.key == pygame.K_s:
        if manager.state in (State.PLAYING, State.MENU):
            manager.return_state = manager.state
            manager.state = State.SHOP
        elif manager.state == State.SHOP:
            manager.state = manager.return_state

    elif event.key == pygame.K_m:
        if manager.state in (State.PLAYING, State.MENU):
            manager.return_state = manager.state
            manager.state = State.MISSION
        elif manager.state == State.MISSION:
            manager.state = manager.return_state


def _handle_drag_release(end_pos, start_pos, start_cell, grid, manager,
                         process_state: str, trigger_eliminate):
    """
    Xử lý thao tác kéo thả viên kẹo.
    Tính hướng kéo (lên/xuống/trái/phải) và thực hiện swap.

    :param end_pos: Vị trí chuột khi thả
    :param start_pos: Vị trí chuột khi bắt đầu kéo
    :param start_cell: Ô bắt đầu kéo (hàng, cột)
    :param grid: Grid object
    :param manager: GameEngine
    :param process_state: Trạng thái pipeline hiện tại
    :param trigger_eliminate: Callback khi swap thành công
    """
    if start_pos is None or end_pos is None:
        return

    dx = end_pos[0] - start_pos[0]
    dy = end_pos[1] - start_pos[1]

    # Ngưỡng tối thiểu để nhận diện kéo (tránh click nhầm thành kéo)
    MIN_DRAG = 15
    if abs(dx) < MIN_DRAG and abs(dy) < MIN_DRAG:
        return

    r, c = start_cell
    # Xác định hướng kéo
    if abs(dx) >= abs(dy):
        # Kéo ngang
        target_c = c + (1 if dx > 0 else -1)
        target_cell = (r, target_c)
    else:
        # Kéo dọc
        target_r = r + (1 if dy > 0 else -1)
        target_cell = (target_r, c)

    tr, tc = target_cell
    if 0 <= tr < 8 and 0 <= tc < 8:
        # Bỏ chọn ô cũ nếu đang chọn
        if grid.grid[r][c]:
            grid.grid[r][c].is_selected = False
        grid.selected_pos = None

        swapped = grid.swap_pieces(r, c, tr, tc)
        if swapped:
            manager.use_move()


def _run_match_pipeline(process_state: str, process_timer: float,
                        dt: float, grid, manager,
                        save_data: dict = None,
                        already_saved: bool = False) -> tuple:
    """
    State machine xử lý chuỗi Match-3:

    idle → eliminating → (delay nổ) → falling → refilling → checking → idle

    :param process_state: Trạng thái hiện tại của pipeline
    :param process_timer: Bộ đếm delay
    :param dt: Delta time (giây)
    :param grid: Grid object
    :param manager: GameEngine
    :param save_data: Dict dữ liệu người chơi (để lưu khi ván kết thúc)
    :param already_saved: True nếu đã lưu ván này rồi (tránh lưu trùng)
    :return: (process_state mới, process_timer mới)
    """
    DELAY_EXPLODE = 0.38
    DELAY_FALL = 0.08
    DELAY_REFILL = 0.45

    if process_state == "idle":
        return process_state, process_timer

    elif process_state == "eliminating":
        # Bước 1: Tìm và xóa match, nếu có -> chờ hiệu ứng nổ
        count = grid.eliminate_matches(manager)
        if count > 0:
            return "wait_explode", 0.0
        else:
            grid.combo_count = 0
            return "idle", 0.0

    elif process_state == "wait_explode":
        # Bước 2: Chờ hiệu ứng nổ xong
        process_timer += dt
        if process_timer >= DELAY_EXPLODE and not grid.has_exploding_pieces():
            return "falling", 0.0
        return process_state, process_timer

    elif process_state == "falling":
        # Bước 3: Áp dụng trọng lực - kẹo rơi xuống
        process_timer += dt
        if process_timer >= DELAY_FALL:
            grid.apply_gravity()
            return "wait_fall", 0.0
        return process_state, process_timer

    elif process_state == "wait_fall":
        # Bước 4: Chờ hoạt ảnh rơi xong
        if not grid.is_animating_pieces():
            return "refilling", 0.0
        return process_state, process_timer

    elif process_state == "refilling":
        # Bước 5: Tạo viên kẹo mới lấp đầy chỗ trống
        grid.refill_board()
        return "wait_refill", 0.0

    elif process_state == "wait_refill":
        # Bước 6: Chờ hoạt ảnh rơi vào xong
        process_timer += dt
        if process_timer >= DELAY_REFILL and not grid.is_animating_pieces():
            return "checking", 0.0
        return process_state, process_timer

    elif process_state == "checking":
        # Bước 7: Kiểm tra xem còn match không (chain reaction)
        matches = grid.check_matches()
        if matches:
            return "eliminating", 0.0
        else:
            grid.combo_count = 0

            # ← THÊM: Lưu kết quả nếu ván vừa kết thúc (chỉ lưu 1 lần)
            if (manager.state in (State.GAME_OVER, State.LEVEL_WIN)
                    and save_data is not None
                    and not already_saved):
                _save_game_result(manager, save_data)

            return "idle", 0.0

    return process_state, process_timer


def _save_game_result(manager, save_data: dict):
    """
    Lưu kết quả ván vừa chơi xuống file JSON.
    Gọi một lần duy nhất khi game chuyển sang GAME_OVER hoặc LEVEL_WIN.

    :param manager: GameEngine chứa dữ liệu ván vừa chơi
    :param save_data: Dict dữ liệu người chơi để cập nhật và ghi xuống
    """
    result = manager.build_game_result()
    save_manager.update_after_game(save_data, result)
    save_manager.sync_from_engine(save_data, manager)
    save_manager.save(save_data)
    print(
        f"[SAVE] Đã lưu ván chơi: "
        f"chế độ={result['mode']} | "
        f"điểm={result['score']} | "
        f"thắng={result['won']}"
    )


def _set_process(current_state: str, new_state: str) -> str:
    """
    Hàm trợ giúp đặt trạng thái pipeline (dùng trong callback).
    Chỉ đặt nếu đang ở 'idle'.
    """
    if current_state == "idle":
        return new_state
    return current_state


def _draw_hammer_cursor(screen: pygame.Surface, pos: tuple):
    """
    Vẽ con trỏ đặc biệt hình búa khi công cụ Cái Chày đang được kích hoạt.

    :param screen: Màn hình game
    :param pos: Vị trí chuột
    """
    mx, my = pos
    # Vẽ vòng tròn đỏ nhỏ quanh chuột
    pygame.draw.circle(screen, (220, 60, 60), (mx, my), 18, 3)
    pygame.draw.line(screen, (220, 60, 60), (mx - 22, my), (mx + 22, my), 2)
    pygame.draw.line(screen, (220, 60, 60), (mx, my - 22), (mx, my + 22), 2)


# =============================================================================
# KHỞI CHẠY
# =============================================================================

if __name__ == "__main__":
    main()