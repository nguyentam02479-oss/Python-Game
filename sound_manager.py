# =============================================================================
# FILE: sound_manager.py
# Mô tả: Sinh hiệu ứng âm thanh bằng code (synth) cho game Sweet Cake Match-3.
#        Không cần file .wav/.mp3 cho SFX — chỉ nhạc nền mới cần file thật.
# =============================================================================

import numpy as np
import pygame

SAMPLE_RATE = 44100


# -----------------------------------------------------------------------------
# CÁC HÀM SINH WAVEFORM CƠ BẢN
# -----------------------------------------------------------------------------
def _envelope(n_samples: int, attack: float = 0.01, release: float = 0.5) -> np.ndarray:
    """Tạo đường bao âm lượng (attack nhanh, decay/release mượt) để tránh tiếng 'tách'."""
    t = np.linspace(0, 1, n_samples)
    env = np.ones(n_samples)

    a_n = max(1, int(n_samples * attack))
    env[:a_n] = np.linspace(0, 1, a_n)

    r_n = max(1, int(n_samples * release))
    env[-r_n:] *= np.linspace(1, 0, r_n)
    return env


def _tone(freq: float, duration: float, wave: str = "sine", volume: float = 0.5) -> np.ndarray:
    """Sinh 1 nốt đơn (sine/square/triangle)."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)

    if wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    elif wave == "triangle":
        data = 2 * np.abs(2 * (t * freq - np.floor(t * freq + 0.5))) - 1
    else:  # sine
        data = np.sin(2 * np.pi * freq * t)

    data *= _envelope(n) * volume
    return data


def _noise(duration: float, volume: float = 0.3) -> np.ndarray:
    """Sinh tiếng ồn trắng (dùng cho hiệu ứng nổ/vỡ băng)."""
    n = int(SAMPLE_RATE * duration)
    data = np.random.uniform(-1, 1, n) * _envelope(n, attack=0.001, release=0.8) * volume
    return data


def _sweep(f_start: float, f_end: float, duration: float, volume: float = 0.5) -> np.ndarray:
    """Sinh âm trượt tần số (glide lên/xuống) — dùng cho 'swap', 'win', 'lose'."""
    n = int(SAMPLE_RATE * duration)
    t = np.linspace(0, duration, n, endpoint=False)
    freq_t = np.linspace(f_start, f_end, n)
    phase = 2 * np.pi * np.cumsum(freq_t) / SAMPLE_RATE
    data = np.sin(phase) * _envelope(n) * volume
    return data


def _mix(*tracks: np.ndarray) -> np.ndarray:
    """Trộn nhiều waveform có độ dài khác nhau (nối tiếp theo offset 0)."""
    max_len = max(len(t) for t in tracks)
    out = np.zeros(max_len)
    for t in tracks:
        out[:len(t)] += t
    return out


def _to_sound(data: np.ndarray) -> pygame.mixer.Sound:
    """Chuyển mảng numpy [-1, 1] thành pygame.mixer.Sound (stereo, 16-bit)."""
    data = np.clip(data, -1, 1)
    pcm = (data * 32767).astype(np.int16)
    stereo = np.column_stack([pcm, pcm])  # 2 kênh giống nhau
    return pygame.sndarray.make_sound(np.ascontiguousarray(stereo))


# -----------------------------------------------------------------------------
# QUẢN LÝ ÂM THANH
# -----------------------------------------------------------------------------
class SoundManager:
    """
    Quản lý toàn bộ SFX (sinh bằng code) + nhạc nền (load từ file).
    Gọi SoundManager.init() một lần khi khởi động game, trước khi tạo
    bất kỳ Sound nào (cần pygame.mixer.init() trước).
    """

    _sounds: dict = {}
    _enabled_sfx: bool = True
    _enabled_music: bool = True
    _sfx_volume: float = 0.6
    _music_volume: float = 0.4

    @classmethod
    def init(cls):
        """Sinh sẵn toàn bộ hiệu ứng âm thanh (gọi 1 lần lúc khởi động)."""
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2)

        cls._sounds["select"] = _to_sound(_tone(660, 0.06, "sine", 0.4))
        cls._sounds["swap"] = _to_sound(_sweep(300, 600, 0.12, 0.45))
        cls._sounds["invalid"] = _to_sound(_tone(140, 0.15, "square", 0.35))

        # Match: 3 nốt vang lên nhanh (kiểu "chime")
        cls._sounds["match"] = _to_sound(_mix(
            _tone(523, 0.10, "sine", 0.4),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.05)), _tone(659, 0.10, "sine", 0.4)]),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.10)), _tone(784, 0.15, "sine", 0.45)]),
        ))

        # Combo: chime cao hơn + sáng hơn match thường
        cls._sounds["combo"] = _to_sound(_mix(
            _tone(784, 0.08, "sine", 0.45),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.04)), _tone(988, 0.08, "sine", 0.45)]),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.08)), _tone(1175, 0.18, "sine", 0.5)]),
        ))

        cls._sounds["explode"] = _to_sound(_mix(
            _noise(0.18, 0.35),
            _tone(110, 0.18, "square", 0.25),
        ))

        cls._sounds["coin"] = _to_sound(_mix(
            _tone(988, 0.06, "sine", 0.4),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.05)), _tone(1318, 0.12, "sine", 0.45)]),
        ))

        cls._sounds["ice_break"] = _to_sound(_mix(
            _noise(0.12, 0.3),
            _tone(1800, 0.08, "triangle", 0.2),
        ))

        cls._sounds["fall"] = _to_sound(_sweep(500, 250, 0.10, 0.25))

        cls._sounds["win"] = _to_sound(_mix(
            _tone(523, 0.15, "sine", 0.4),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.12)), _tone(659, 0.15, "sine", 0.4)]),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.24)), _tone(784, 0.15, "sine", 0.4)]),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.36)), _tone(1046, 0.30, "sine", 0.45)]),
        ))

        cls._sounds["lose"] = _to_sound(_sweep(440, 110, 0.6, 0.4))

        cls._sounds["button"] = _to_sound(_tone(440, 0.05, "square", 0.3))

        cls._sounds["shop_buy"] = _to_sound(_mix(
            _tone(440, 0.05, "sine", 0.4),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.05)), _tone(880, 0.10, "sine", 0.45)]),
        ))

        cls._sounds["mission_complete"] = _to_sound(_mix(
            _tone(660, 0.10, "sine", 0.4),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.08)), _tone(880, 0.10, "sine", 0.4)]),
            np.concatenate([np.zeros(int(SAMPLE_RATE * 0.16)), _tone(1320, 0.20, "sine", 0.45)]),
        ))

    # -------------------------------------------------------------------
    @classmethod
    def play(cls, name: str):
        """Phát một hiệu ứng âm thanh theo tên (xem danh sách trong init())."""
        if not cls._enabled_sfx:
            return
        snd = cls._sounds.get(name)
        if snd is not None:
            snd.set_volume(cls._sfx_volume)
            snd.play()

    @classmethod
    def set_sfx_enabled(cls, enabled: bool):
        cls._enabled_sfx = enabled

    @classmethod
    def is_sfx_enabled(cls) -> bool:
        return cls._enabled_sfx

    @classmethod
    def toggle_sfx(cls) -> bool:
        """Đảo trạng thái bật/tắt SFX. Trả về trạng thái mới."""
        cls._enabled_sfx = not cls._enabled_sfx
        return cls._enabled_sfx

    @classmethod
    def set_sfx_volume(cls, vol: float):
        cls._sfx_volume = max(0.0, min(1.0, vol))

    # -------------------------------------------------------------------
    # NHẠC NỀN (load từ file thật, không synth)
    # -------------------------------------------------------------------
    @classmethod
    def play_music(cls, path: str, loop: bool = True, volume: float = None):
        if volume is not None:
            cls._music_volume = volume
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(cls._music_volume if cls._enabled_music else 0.0)
            pygame.mixer.music.play(-1 if loop else 0)
        except pygame.error as e:
            print(f"[SoundManager] Không thể tải nhạc nền '{path}': {e}")

    @classmethod
    def set_music_enabled(cls, enabled: bool):
        cls._enabled_music = enabled
        pygame.mixer.music.set_volume(cls._music_volume if enabled else 0.0)

    @classmethod
    def is_music_enabled(cls) -> bool:
        return cls._enabled_music

    @classmethod
    def toggle_music(cls) -> bool:
        """Đảo trạng thái bật/tắt nhạc nền. Trả về trạng thái mới."""
        cls._enabled_music = not cls._enabled_music
        pygame.mixer.music.set_volume(cls._music_volume if cls._enabled_music else 0.0)
        return cls._enabled_music

    @classmethod
    def set_music_volume(cls, vol: float):
        cls._music_volume = max(0.0, min(1.0, vol))
        if cls._enabled_music:
            pygame.mixer.music.set_volume(cls._music_volume)

    @classmethod
    def stop_music(cls):
        pygame.mixer.music.stop()