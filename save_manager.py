# =============================================================================
# FILE: save_manager.py
# Mô tả: Quản lý lưu và tải dữ liệu người chơi dưới dạng JSON
#        Sweet Cake Match-3 | Bánh Ngọt Kết Đôi
# =============================================================================

import json
import os
import time
from typing import Optional

from settings import MISSIONS  # ← Dùng danh sách nhiệm vụ chuẩn từ settings.py

# Đường dẫn file lưu (cùng thư mục với game)
SAVE_FILE = "player_data.json"

# Phiên bản cấu trúc save (tăng khi thay đổi schema để xử lý tương thích)
SAVE_VERSION = 2


# =============================================================================
# CẤU TRÚC DỮ LIỆU MẶC ĐỊNH
# =============================================================================

def _default_save_data() -> dict:
    """
    Trả về dict dữ liệu mặc định cho người chơi mới.
    Dùng khi file chưa tồn tại hoặc bị lỗi.
    """
    now = time.time()
    return {
        # --- Metadata ---
        "version": SAVE_VERSION,
        "created_at": now,           # Timestamp lần đầu tạo file
        "last_saved": now,           # Timestamp lần lưu gần nhất

        # --- Dữ liệu người chơi ---
        "player": {
            "coins": 50,             # Xu hiện tại
            "high_score": 0,         # Điểm cao nhất mọi thời đại
            "total_games_played": 0, # Tổng số ván đã chơi
            "total_pieces_destroyed": 0,  # Tổng viên kẹo đã phá (mọi ván)
            "total_combos": 0,       # Tổng combo đã tạo (mọi ván)
            "total_coins_earned": 50,     # Tổng xu đã kiếm được (bao gồm xu đầu)
            "total_coins_spent": 0,       # Tổng xu đã chi
        },

        # --- Kho vật phẩm ---
        "inventory": {
            "hammer": 0,
            "mixer": 0,
            "extra_time": 0,
            "extra_moves": 0,
        },

        # --- Thống kê theo chế độ chơi ---
        "stats": {
            "basic": {
                "games_played": 0,
                "best_score": 0,
                "total_score": 0,
                "best_time_survived": 0.0,   # Giây sống lâu nhất
                "wins": 0,                    # (không áp dụng cho basic, để sẵn)
                "losses": 0,
            },
            "challenge": {
                "games_played": 0,
                "best_score": 0,
                "total_score": 0,
                "wins": 0,                    # Số lần đạt điểm mục tiêu
                "losses": 0,
                "best_moves_remaining": 0,    # Số lượt còn lại nhiều nhất khi thắng
            },
        },

        # --- Lịch sử 10 ván gần nhất ---
        "recent_games": [],

        # --- Tiến độ nhiệm vụ ---
        # Tự động lấy từ danh sách MISSIONS trong settings.py, đảm bảo mọi
        # nhiệm vụ (hiện tại và sau này thêm vào) đều có chỗ lưu tiến độ.
        "missions": {
            m["id"]: {"progress": 0, "claimed": False, "last_reset": now}
            for m in MISSIONS
        },

        # --- Cài đặt người chơi ---
        "settings": {
            "sfx_volume": 1.0,       # 0.0 đến 1.0
            "music_volume": 0.5,
            "show_hints": True,
        },
    }


# =============================================================================
# CÁC HÀM CHÍNH
# =============================================================================

def load(filepath: str = SAVE_FILE) -> dict:
    """
    Tải dữ liệu người chơi từ file JSON.
    Nếu file không tồn tại hoặc bị lỗi, trả về dữ liệu mặc định.

    :param filepath: Đường dẫn đến file JSON
    :return: Dict dữ liệu người chơi
    """
    if not os.path.isfile(filepath):
        print(f"[SAVE] Không tìm thấy '{filepath}' — tạo mới dữ liệu mặc định.")
        return _default_save_data()

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Kiểm tra phiên bản và bổ sung các trường còn thiếu
        data = _migrate(data)
        print(f"[SAVE] Đã tải dữ liệu từ '{filepath}' thành công.")
        return data

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"[SAVE] Lỗi đọc file '{filepath}': {e} — dùng dữ liệu mặc định.")
        return _default_save_data()


def save(data: dict, filepath: str = SAVE_FILE) -> bool:
    """
    Lưu dữ liệu người chơi vào file JSON.

    :param data: Dict dữ liệu cần lưu
    :param filepath: Đường dẫn đến file JSON
    :return: True nếu lưu thành công, False nếu có lỗi
    """
    try:
        data["last_saved"] = time.time()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Đã lưu dữ liệu vào '{filepath}'.")
        return True

    except (OSError, TypeError) as e:
        print(f"[SAVE] Lỗi lưu file '{filepath}': {e}")
        return False


def _migrate(data: dict) -> dict:
    """
    Cập nhật (migrate) dữ liệu cũ sang schema mới nhất.
    Bổ sung các trường còn thiếu mà không xóa dữ liệu cũ.

    :param data: Dict dữ liệu đã tải từ file
    :return: Dict đã được cập nhật
    """
    default = _default_save_data()

    # Đảm bảo tất cả các key cấp cao có mặt
    for key, value in default.items():
        if key not in data:
            data[key] = value

    # Đảm bảo các key lồng nhau cũng có mặt
    for section in ("player", "inventory", "stats", "settings"):
        if section not in data:
            data[section] = default[section]
        else:
            for k, v in default[section].items():
                if k not in data[section]:
                    data[section][k] = v

    # Đảm bảo stats theo chế độ có đủ trường
    for mode in ("basic", "challenge"):
        if mode not in data["stats"]:
            data["stats"][mode] = default["stats"][mode]
        else:
            for k, v in default["stats"][mode].items():
                if k not in data["stats"][mode]:
                    data["stats"][mode][k] = v

    # Đảm bảo missions có đủ trường
    if "missions" not in data:
        data["missions"] = default["missions"]
    else:
        for mid, mval in default["missions"].items():
            if mid not in data["missions"]:
                data["missions"][mid] = mval

    # Đảm bảo recent_games là list
    if not isinstance(data.get("recent_games"), list):
        data["recent_games"] = []

    # Cập nhật phiên bản
    data["version"] = SAVE_VERSION
    return data


# =============================================================================
# HÀM TIỆN ÍCH: ĐỌC / GHI TỪNG PHẦN
# =============================================================================

def update_after_game(data: dict, result: dict) -> dict:
    """
    Cập nhật dữ liệu sau khi kết thúc một ván chơi.

    :param data: Dict dữ liệu hiện tại
    :param result: Dict kết quả ván vừa chơi, gồm:
        - mode (str): "basic" hoặc "challenge"
        - score (int): Điểm đạt được
        - won (bool): Thắng hay thua
        - pieces_destroyed (int): Viên kẹo đã phá
        - combos (int): Số combo đã tạo
        - frozen_broken (int): Ô băng đã phá
        - time_survived (float): Giây đã sống (basic mode)
        - moves_remaining (int): Lượt còn lại khi thắng (challenge mode)
        - coins_earned (int): Xu kiếm được trong ván
    :return: Dict dữ liệu đã cập nhật
    """
    mode       = result.get("mode", "basic")
    score      = result.get("score", 0)
    won        = result.get("won", False)
    pieces     = result.get("pieces_destroyed", 0)
    combos     = result.get("combos", 0)
    frozen     = result.get("frozen_broken", 0)
    t_survived = result.get("time_survived", 0.0)
    moves_rem  = result.get("moves_remaining", 0)
    coins_earn = result.get("coins_earned", 0)

    p = data["player"]
    s = data["stats"][mode]

    # --- Cập nhật player ---
    p["total_games_played"] += 1
    p["total_pieces_destroyed"] += pieces
    p["total_combos"] += combos
    p["total_coins_earned"] += coins_earn
    if score > p["high_score"]:
        p["high_score"] = score

    # --- Cập nhật stats theo mode ---
    s["games_played"] += 1
    s["total_score"] += score
    if score > s["best_score"]:
        s["best_score"] = score
    if won:
        s["wins"] += 1
    else:
        s["losses"] += 1

    if mode == "basic":
        if t_survived > s["best_time_survived"]:
            s["best_time_survived"] = t_survived
    elif mode == "challenge" and won:
        if moves_rem > s["best_moves_remaining"]:
            s["best_moves_remaining"] = moves_rem

    # --- Lưu vào lịch sử (tối đa 10 ván) ---
    entry = {
        "timestamp": time.time(),
        "mode": mode,
        "score": score,
        "won": won,
        "pieces_destroyed": pieces,
        "combos": combos,
        "frozen_broken": frozen,
        "coins_earned": coins_earn,
    }
    if mode == "basic":
        entry["time_survived"] = round(t_survived, 1)
    else:
        entry["moves_remaining"] = moves_rem

    data["recent_games"].insert(0, entry)
    data["recent_games"] = data["recent_games"][:10]  # Chỉ giữ 10 ván gần nhất

    return data


def sync_from_engine(data: dict, engine) -> dict:
    """
    Đồng bộ dữ liệu runtime từ GameEngine vào dict save.
    Gọi trước khi lưu file để đảm bảo dữ liệu mới nhất.

    :param data: Dict dữ liệu hiện tại
    :param engine: Đối tượng GameEngine
    :return: Dict đã đồng bộ
    """
    data["player"]["coins"] = engine.coins
    data["player"]["high_score"] = max(data["player"]["high_score"], engine.high_score)
    data["inventory"] = dict(engine.inventory)

    # Đồng bộ tiến độ nhiệm vụ
    for m in engine.missions:
        mid = m["id"]
        if mid in data["missions"]:
            data["missions"][mid]["progress"] = m["progress"]
            data["missions"][mid]["claimed"]  = m["claimed"]

    return data


def restore_to_engine(data: dict, engine) -> None:
    """
    Phục hồi dữ liệu đã lưu vào GameEngine khi khởi động.

    :param data: Dict dữ liệu đã tải từ file
    :param engine: Đối tượng GameEngine
    """
    p = data["player"]
    engine.coins      = p.get("coins", 50)
    engine.high_score = p.get("high_score", 0)
    engine.inventory  = dict(data.get("inventory", {
        "hammer": 0, "mixer": 0, "extra_time": 0, "extra_moves": 0
    }))

    # Phục hồi tiến độ nhiệm vụ
    saved_missions = data.get("missions", {})
    for m in engine.missions:
        mid = m["id"]
        if mid in saved_missions:
            # Kiểm tra reset theo thời gian trước khi phục hồi
            saved = saved_missions[mid]
            last_reset = saved.get("last_reset", 0)
            now = time.time()

            should_reset = False
            if m.get("type") == "daily"   and (now - last_reset) >= 86400:
                should_reset = True
            elif m.get("type") == "hourly" and (now - last_reset) >= 3600:
                should_reset = True
            elif m.get("type") == "session":
                should_reset = True  # Session luôn reset khi khởi động

            if should_reset:
                m["progress"] = 0
                m["claimed"]  = False
            else:
                m["progress"] = saved.get("progress", 0)
                m["claimed"]  = saved.get("claimed", False)

    print("[SAVE] Đã phục hồi dữ liệu vào GameEngine.")


# =============================================================================
# TIỆN ÍCH BỔ SUNG
# =============================================================================

def get_summary(data: dict) -> str:
    """
    Trả về chuỗi tóm tắt thống kê người chơi để debug/hiển thị.

    :param data: Dict dữ liệu người chơi
    :return: Chuỗi nhiều dòng
    """
    p = data["player"]
    sb = data["stats"]["basic"]
    sc = data["stats"]["challenge"]
    lines = [
        "========== DỮ LIỆU NGƯỜI CHƠI ==========",
        f"  Xu hiện tại      : {p['coins']}",
        f"  Điểm cao nhất    : {p['high_score']}",
        f"  Tổng ván đã chơi : {p['total_games_played']}",
        f"  Tổng viên đã phá : {p['total_pieces_destroyed']}",
        f"  Tổng combo       : {p['total_combos']}",
        "",
        "  [Basic Mode]",
        f"    Ván đã chơi    : {sb['games_played']}",
        f"    Điểm cao nhất  : {sb['best_score']}",
        f"    Thời gian dài nhất: {sb['best_time_survived']:.1f}s",
        "",
        "  [Challenge Mode]",
        f"    Ván đã chơi    : {sc['games_played']}",
        f"    Thắng / Thua   : {sc['wins']} / {sc['losses']}",
        f"    Điểm cao nhất  : {sc['best_score']}",
        "=========================================",
    ]
    return "\n".join(lines)


def delete_save(filepath: str = SAVE_FILE) -> bool:
    """
    Xóa file lưu (reset toàn bộ tiến trình).

    :param filepath: Đường dẫn file cần xóa
    :return: True nếu xóa thành công hoặc file không tồn tại
    """
    if not os.path.isfile(filepath):
        return True
    try:
        os.remove(filepath)
        print(f"[SAVE] Đã xóa file '{filepath}'.")
        return True
    except OSError as e:
        print(f"[SAVE] Không thể xóa '{filepath}': {e}")
        return False