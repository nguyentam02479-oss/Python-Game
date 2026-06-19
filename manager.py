# =============================================================================
# FILE: manager.py
# Mô tả: Quản lý toàn bộ trạng thái game, dữ liệu người chơi,
#        hệ thống Shop và Mission (class GameEngine)
# =============================================================================

import time
from typing import Dict, List, Optional

from settings import (
    State, GameMode,
    BASIC_TIME_LIMIT, BASIC_TIME_BONUS_MATCH,
    CHALLENGE_MOVES_LIMIT, CHALLENGE_SCORE_TARGET,
    SHOP_ITEMS, MISSIONS
)
from sound_manager import SoundManager  # ← THÊM: âm thanh


class GameEngine:
    """
    Trung tâm điều phối logic game:
    - Quản lý trạng thái (State Enum)
    - Điểm số, xu, thời gian/lượt đi
    - Kho vật phẩm Shop và lịch sử giao dịch
    - Nhiệm vụ (Mission) theo giờ/ngày/phiên
    """

    def __init__(self):
        """Khởi tạo engine với trạng thái mặc định."""

        # ----- Trạng thái game -----
        self.state: State = State.MENU
        # Màn hình cần quay lại khi đóng overlay Shop/Mission
        # (có thể là MENU nếu mở từ Menu chính, hoặc PLAYING nếu mở khi đang chơi)
        self.return_state: State = State.MENU
        self.mode: GameMode = GameMode.BASIC

        # ----- Dữ liệu người chơi -----
        self.score: int = 0
        self.coins: int = 50  # Xu ban đầu
        self.high_score: int = 0  # Điểm cao nhất trong phiên

        # ----- Chế độ Basic -----
        self.time_left: float = BASIC_TIME_LIMIT
        self._timer_active: bool = False

        # ----- Chế độ Challenge -----
        self.moves_left: int = CHALLENGE_MOVES_LIMIT
        self.score_target: int = CHALLENGE_SCORE_TARGET

        # ----- Kho vật phẩm Shop -----
        # Số lượng từng loại vật phẩm người chơi đang có
        self.inventory: Dict[str, int] = {
            "hammer": 0,
            "mixer": 0,
            "extra_time": 0,
            "extra_moves": 0,
        }

        # Vật phẩm đang được kích hoạt (None = không có)
        self.active_tool: Optional[str] = None

        # ----- Hệ thống Mission -----
        self.missions: List[dict] = self._init_missions()

        # Bộ đếm thời gian thực cho nhiệm vụ theo giờ/ngày
        self._mission_session_start: float = time.time()
        self._last_hour_reset: float = time.time()
        self._last_day_reset: float = time.time()

        # ----- Thống kê phiên chơi (dùng cho Mission) -----
        self.session_pieces_destroyed: int = 0  # Tổng viên kẹo đã phá
        self.session_combos: int = 0  # Tổng combo đã tạo
        self.session_frozen_broken: int = 0  # Tổng ô băng đã phá
        self.session_score: int = 0  # Điểm tích lũy trong giờ

        # ----- Thông báo UI -----
        self.notification: Optional[str] = None  # Văn bản thông báo tạm
        self.notification_timer: float = 0.0  # Bộ đếm hiển thị thông báo
        self.score_popups: List[dict] = []  # Hiển thị điểm nổi lên

    # =========================================================================
    # KHỞI TẠO / RESET GAME
    # =========================================================================

    def start_game(self, mode: GameMode):
        """
        Bắt đầu phiên chơi mới với chế độ được chọn.
        Reset toàn bộ trạng thái gameplay.

        :param mode: BASIC hoặc CHALLENGE
        """
        self.mode = mode
        self.state = State.PLAYING
        self.score = 0
        self.active_tool = None

        # Reset theo chế độ
        if mode == GameMode.BASIC:
            self.time_left = BASIC_TIME_LIMIT
            self._timer_active = True
        else:
            self.moves_left = CHALLENGE_MOVES_LIMIT
            self._timer_active = False

        # Reset thống kê phiên
        self.session_pieces_destroyed = 0
        self.session_combos = 0
        self.session_frozen_broken = 0
        self.session_score = 0

        # Reset nhiệm vụ loại "session"
        for m in self.missions:
            if m["type"] == "session":
                m["progress"] = 0
                m["claimed"] = False

        self._show_notification(
            f"Bắt đầu {'Chế Độ Thời Gian' if mode == GameMode.BASIC else 'Chế Độ Thử Thách'}!"
        )

        # Cập nhật tiến độ nhiệm vụ "chơi N ván"
        self._update_mission_progress("daily_games", 1)

    def reset_to_menu(self):
        """Quay về màn hình chính."""
        self.state = State.MENU
        self._timer_active = False
        self.active_tool = None

    # =========================================================================
    # CẬP NHẬT MỖI FRAME
    # =========================================================================

    def update(self, dt: float):
        """
        Cập nhật logic game mỗi frame:
        - Đếm ngược thời gian (Basic Mode)
        - Kiểm tra điều kiện thắng/thua
        - Cập nhật nhiệm vụ theo thời gian thực
        - Xóa thông báo hết hạn

        :param dt: Delta time (giây)
        """
        if self.state != State.PLAYING:
            # Cập nhật nhiệm vụ và thông báo ngay cả khi không đang chơi
            self._update_notification(dt)
            self._check_time_based_mission_resets()
            return

        # ---- Đếm ngược thời gian (Basic Mode) ----
        if self.mode == GameMode.BASIC and self._timer_active:
            self.time_left -= dt
            self.time_left = max(0.0, self.time_left)

            if self.time_left <= 0:
                self._trigger_game_over("Hết thời gian!")
                return

        # ---- Cập nhật thông báo ----
        self._update_notification(dt)

        # ---- Cập nhật popup điểm ----
        self._update_score_popups(dt)

        # ---- Kiểm tra reset nhiệm vụ theo thời gian ----
        self._check_time_based_mission_resets()

    # =========================================================================
    # ĐIỀU CHỈNH ĐIỂM SỐ VÀ TÀI NGUYÊN
    # =========================================================================

    def add_score(self, amount: int, combo: int = 1):
        """
        Cộng điểm và tạo popup hiển thị điểm nổi lên.

        :param amount: Lượng điểm cộng thêm
        :param combo: Số combo (để hiển thị)
        """
        self.score += amount
        self.session_score += amount

        if self.score > self.high_score:
            self.high_score = self.score

        # Cập nhật tiến độ nhiệm vụ "đạt tổng điểm trong ngày"
        if amount > 0:
            self._update_mission_progress("daily_score", amount)

        # Thêm popup điểm
        self.score_popups.append({
            "text": f"+{amount}" + (f" x{combo}" if combo > 1 else ""),
            "timer": 0.0,
            "max": 1.2,
            "x": 0,  # Vị trí sẽ được set bởi UI
            "y": 0,
        })

        # Kiểm tra thắng (Challenge Mode)
        if (self.mode == GameMode.CHALLENGE and
                self.score >= self.score_target and
                self.state == State.PLAYING):
            self._trigger_level_win()

    def add_coins(self, amount: int):
        """
        Cộng xu vào túi người chơi.

        :param amount: Lượng xu cộng thêm
        """
        self.coins += amount
        if amount > 0:
            SoundManager.play("coin")  # ← THÊM: âm thanh nhặt xu
            self._show_notification(f"+{amount} Xu!")
            # Cập nhật tiến độ nhiệm vụ "kiếm xu trong ngày"
            self._update_mission_progress("daily_coins", amount)

    def add_time(self, seconds: float):
        """
        Cộng thêm thời gian (chỉ dành cho Basic Mode).

        :param seconds: Số giây cộng thêm
        """
        if self.mode == GameMode.BASIC:
            self.time_left = min(self.time_left + seconds,
                                 BASIC_TIME_LIMIT * 2)  # Giới hạn max 2x

    def add_bonus_time_for_match(self):
        """Cộng thời gian thưởng khi có match hợp lệ (Basic Mode)."""
        self.add_time(BASIC_TIME_BONUS_MATCH)

    def use_move(self):
        """
        Trừ 1 lượt đi (Challenge Mode).
        Kiểm tra điều kiện thua khi hết lượt.
        """
        if self.mode == GameMode.CHALLENGE:
            self.moves_left -= 1
            self.moves_left = max(0, self.moves_left)

            if self.moves_left <= 0 and self.score < self.score_target:
                self._trigger_game_over("Hết lượt đi!")

    # =========================================================================
    # THỐNG KÊ PHIÊN (CHO MISSION)
    # =========================================================================

    def notify_pieces_destroyed(self, count: int, frozen_broken: int, combo: int):
        """
        Cập nhật thống kê phiên và tiến độ nhiệm vụ sau mỗi lần xóa kẹo.

        :param count: Số viên kẹo vừa phá
        :param frozen_broken: Số ô băng vừa phá
        :param combo: Số combo hiện tại
        """
        self.session_pieces_destroyed += count
        self.session_frozen_broken += frozen_broken

        if combo > 1:
            self.session_combos += 1

        # ← THÊM: âm thanh match (combo cao hơn dùng chime sáng hơn)
        if count > 0:
            SoundManager.play("combo" if combo > 1 else "match")
        if frozen_broken > 0:
            SoundManager.play("ice_break")

        # Cộng thời gian thưởng khi match (Basic Mode)
        if self.mode == GameMode.BASIC:
            self.add_bonus_time_for_match()

        # Cập nhật tiến độ nhiệm vụ
        self._update_mission_progress("daily_pieces", count)
        self._update_mission_progress("session_pieces", count)
        self._update_mission_progress("hourly_pieces", count)
        self._update_mission_progress("session_frozen", frozen_broken)
        if combo > 1:
            self._update_mission_progress("daily_combo", 1)
            self._update_mission_progress("session_combo", 1)
        self._update_mission_progress("hourly_score", 0)  # Score update riêng

    # =========================================================================
    # HỆ THỐNG SHOP
    # =========================================================================

    def buy_item(self, item_key: str) -> bool:
        """
        Mua vật phẩm từ Shop bằng xu.

        :param item_key: Tên vật phẩm (ví dụ: "hammer", "mixer")
        :return: True nếu mua thành công
        """
        if item_key not in SHOP_ITEMS:
            return False

        item = SHOP_ITEMS[item_key]
        price = item["price"]

        if self.coins < price:
            SoundManager.play("invalid")  # ← THÊM
            self._show_notification("Không đủ xu!")
            return False

        self.coins -= price
        self.inventory[item_key] += 1
        SoundManager.play("shop_buy")  # ← THÊM
        self._show_notification(f"Đã mua: {item['name']}!")

        # Cập nhật tiến độ nhiệm vụ "mua vật phẩm trong ngày"
        self._update_mission_progress("daily_shop", 1)
        return True

    # manager.py - SỬA HÀM use_item

    def use_item(self, item_key: str) -> bool:
        """
        Kích hoạt sử dụng vật phẩm từ kho đồ.
        """
        if self.inventory.get(item_key, 0) <= 0:
            SoundManager.play("invalid")
            self._show_notification("Không có vật phẩm này trong kho!")
            return False

        if self.state != State.PLAYING:
            SoundManager.play("invalid")
            self._show_notification("Hãy bắt đầu ván chơi trước khi dùng!")
            return False

        if item_key == "extra_time":
            if self.mode != GameMode.BASIC:
                SoundManager.play("invalid")
                self._show_notification("+30 Giây chỉ dùng được ở Chế Độ Thời Gian!")
                return False
            self.add_time(30.0)
            self.inventory["extra_time"] -= 1
            SoundManager.play("button")
            self._show_notification("+30 Giây đã được cộng!")
            self._update_mission_progress("daily_tool_use", 1)
            return True

        if item_key == "extra_moves":
            if self.mode != GameMode.CHALLENGE:
                SoundManager.play("invalid")
                self._show_notification("+5 Lượt chỉ dùng được ở Chế Độ Thử Thách!")
                return False
            self.moves_left += 5
            self.inventory["extra_moves"] -= 1
            SoundManager.play("button")
            self._show_notification("+5 Lượt đi!")
            self._update_mission_progress("daily_tool_use", 1)
            return True

        if item_key == "hammer":
            SoundManager.play("select")
            if self.active_tool == "hammer":
                self.active_tool = None
                self._show_notification("Đã hủy công cụ.")
            else:
                self.active_tool = "hammer"
                self.inventory["hammer"] -= 1  # TRỪ KHI KÍCH HOẠT
                self._show_notification("Đã kích hoạt Phá Ô! Click vào ô để phá.")
                self._update_mission_progress("daily_tool_use", 1)
            return True

        if item_key == "mixer":
            SoundManager.play("select")
            if self.active_tool == "mixer":
                self.active_tool = None
                self._show_notification("Đã hủy công cụ.")
            else:
                self.active_tool = "mixer"
                self.inventory["mixer"] -= 1  # TRỪ KHI KÍCH HOẠT
                self._show_notification("Đã kích hoạt Hoán Đổi! Click vào 2 ô để hoán đổi.")
                self._update_mission_progress("daily_tool_use", 1)
            return True

        return False

    def apply_mixer_to_grid(self, grid) -> bool:
        """
        Gọi Grid để hoán đổi ngẫu nhiên 2 viên kẹo (Hoán Đổi).

        :param grid: Tham chiếu đến đối tượng Grid
        :return: True nếu thực hiện được
        """
        if self.state != State.PLAYING:
            return False

        grid.random_swap_two()
        SoundManager.play("swap")  # ← THÊM
        self._show_notification("Đã hoán đổi 2 ô ngẫu nhiên!")
        return True

    # =========================================================================
    # HỆ THỐNG MISSION
    # =========================================================================

    def _init_missions(self) -> List[dict]:
        """
        Khởi tạo danh sách nhiệm vụ từ cấu hình settings.
        Mỗi nhiệm vụ có thêm trường progress và claimed.

        :return: Danh sách dict nhiệm vụ
        """
        missions = []
        for m_config in MISSIONS:
            m = dict(m_config)
            m["progress"] = 0
            m["claimed"] = False
            missions.append(m)
        return missions

    def _update_mission_progress(self, mission_id: str, increment: int):
        """
        Tăng tiến độ nhiệm vụ theo ID.

        :param mission_id: ID nhiệm vụ
        :param increment: Giá trị tăng thêm
        """
        for m in self.missions:
            if m["id"] == mission_id and not m["claimed"]:
                m["progress"] = min(m["progress"] + increment, m["target"])

    def _check_time_based_mission_resets(self):
        """
        Kiểm tra và reset nhiệm vụ theo giờ/ngày khi đến chu kỳ mới.
        """
        now = time.time()

        # Reset nhiệm vụ theo giờ (mỗi 3600 giây)
        if now - self._last_hour_reset >= 3600:
            self._last_hour_reset = now
            self.session_score = 0
            for m in self.missions:
                if m["type"] == "hourly":
                    m["progress"] = 0
                    m["claimed"] = False

        # Reset nhiệm vụ theo ngày (mỗi 86400 giây)
        if now - self._last_day_reset >= 86400:
            self._last_day_reset = now
            for m in self.missions:
                if m["type"] == "daily":
                    m["progress"] = 0
                    m["claimed"] = False

    def update_missions(self, dt: float):
        """
        Cập nhật nhiệm vụ loại "hourly_score" theo điểm tích lũy.
        (Nhiệm vụ khác được cập nhật trực tiếp qua notify_pieces_destroyed)

        :param dt: Delta time (không dùng trực tiếp nhưng có thể mở rộng)
        """
        for m in self.missions:
            if m["id"] == "hourly_score" and not m["claimed"]:
                m["progress"] = min(self.session_score, m["target"])

    def claim_mission_reward(self, mission_id: str) -> bool:
        for m in self.missions:
            if m["id"] != mission_id:
                continue
            if m["claimed"]:
                SoundManager.play("invalid")  # ← THÊM
                self._show_notification("Bạn đã nhận thưởng nhiệm vụ này rồi!")
                return False
            if m["progress"] < m["target"]:
                SoundManager.play("invalid")  # ← THÊM
                self._show_notification("Chưa hoàn thành nhiệm vụ!")
                return False

            reward = m["reward_coin"]
            self.coins += reward  # ← cộng xu trực tiếp, không qua add_coins
            m["claimed"] = True
            SoundManager.play("mission_complete")  # ← THÊM
            self._show_notification(  # ← chỉ 1 thông báo duy nhất
                f"Nhận thưởng '{m['name']}': +{reward} xu!"
            )
            return True
        return False

    def get_mission_by_id(self, mission_id: str) -> Optional[dict]:
        """Lấy dict dữ liệu nhiệm vụ theo ID."""
        for m in self.missions:
            if m["id"] == mission_id:
                return m
        return None

    def count_completable_missions(self) -> int:
        """Đếm số nhiệm vụ đã đủ điều kiện nhận thưởng (chưa claimed)."""
        return sum(
            1 for m in self.missions
            if m["progress"] >= m["target"] and not m["claimed"]
        )

    # =========================================================================
    # ĐIỀU KIỆN THẮNG / THUA
    # =========================================================================

    def _trigger_game_over(self, reason: str = ""):
        """
        Kết thúc game (trạng thái thua).

        :param reason: Lý do thua để hiển thị
        """
        self.state = State.GAME_OVER
        self._timer_active = False
        SoundManager.play("lose")  # ← THÊM
        if reason:
            self._show_notification(reason, duration=3.0)

    def _trigger_level_win(self):
        """Kết thúc game (trạng thái thắng)."""
        self.state = State.LEVEL_WIN
        self._timer_active = False
        SoundManager.play("win")  # ← THÊM
        self._show_notification("Chúc mừng! Bạn đã thắng!", duration=3.0)

        # Cập nhật tiến độ nhiệm vụ "thắng Chế Độ Thử Thách"
        if self.mode == GameMode.CHALLENGE:
            self._update_mission_progress("daily_win_challenge", 1)

    # =========================================================================
    # THÔNG BÁO VÀ POPUP
    # =========================================================================

    def _show_notification(self, text: str, duration: float = 2.0):
        """
        Hiển thị thông báo tạm thời ở vùng HUD.
        :param text: Văn bản thông báo
        :param duration: Thời gian hiển thị (giây)
        """
        self.notification = text
        self.notification_timer = duration

    def _update_notification(self, dt: float):
        """Đếm ngược thời gian hiển thị thông báo."""
        if self.notification_timer > 0:
            self.notification_timer -= dt
            if self.notification_timer <= 0:
                self.notification = None

    def _update_score_popups(self, dt: float):
        """Cập nhật và dọn dẹp các popup điểm hết hạn."""
        self.score_popups = [
            p for p in self.score_popups
            if p["timer"] < p["max"]
        ]
        for p in self.score_popups:
            p["timer"] += dt

    # =========================================================================
    # THÔNG TIN TRẠNG THÁI (CHO UI)
    # =========================================================================

    def get_time_formatted(self) -> str:
        """
        Trả về thời gian còn lại dưới dạng MM:SS.

        :return: Chuỗi định dạng "MM:SS"
        """
        total_sec = max(0, int(self.time_left))
        minutes = total_sec // 60
        seconds = total_sec % 60
        return f"{minutes:02d}:{seconds:02d}"

    def get_time_color(self) -> tuple:
        """
        Trả về màu sắc thanh thời gian dựa trên mức còn lại.
        Đỏ khi sắp hết, vàng khi ở mức trung bình, xanh khi còn nhiều.

        :return: Tuple màu RGB
        """
        ratio = self.time_left / BASIC_TIME_LIMIT
        if ratio > 0.5:
            return (50, 200, 100)  # Xanh lá
        elif ratio > 0.25:
            return (255, 200, 50)  # Vàng
        else:
            return (220, 60, 60)  # Đỏ

    def is_tool_active(self) -> bool:
        """Kiểm tra có công cụ nào đang được kích hoạt không."""
        return self.active_tool is not None

    def cancel_active_tool(self):
        """Hủy công cụ đang kích hoạt và hoàn trả vật phẩm."""
        if self.active_tool == "hammer":
            self.inventory["hammer"] += 1  # Hoàn trả chày
        self.active_tool = None

    # =========================================================================
    # LƯU / TẢI DỮ LIỆU (TÍCH HỢP VỚI save_manager)
    # =========================================================================

    def build_game_result(self) -> dict:
        """
        Đóng gói kết quả ván vừa chơi thành dict để truyền cho save_manager.
        Gọi ngay sau khi game kết thúc (win hoặc lose).
        """
        import time
        return {
            "mode": "basic" if self.mode == GameMode.BASIC else "challenge",
            "score": self.score,
            "won": self.state == State.LEVEL_WIN,
            "pieces_destroyed": self.session_pieces_destroyed,
            "combos": self.session_combos,
            "frozen_broken": self.session_frozen_broken,
            "time_survived": max(0.0, 90.0 - self.time_left),  # giây đã sống
            "moves_remaining": self.moves_left,
            "coins_earned": 0,  # xu nhặt từ bàn (có thể mở rộng sau)
        }

    def get_total_coins_spent(self) -> int:
        """Tổng xu đã chi trong phiên (dùng khi sync save)."""
        return 0  # Mở rộng sau nếu cần theo dõi chi tiêu