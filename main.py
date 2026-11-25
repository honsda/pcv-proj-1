"""Mini game simpang jalan yang dikendalikan warna tangan.

Aturan main:
  - Tangan di kotak KIRI    -> pejalan kaki BERHENTI.
  - Tangan di kotak KANAN   -> pejalan kaki JALAN.
  - Dua-duanya / tidak ada  -> pejalan kaki jalan ACAK.

Jalankan : python main.py
Keluar   : tekan q atau ESC
"""

import random
import time

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Pengaturan kamera & deteksi tangan
# ---------------------------------------------------------------------------
CAM_INDEX = 0                  # ganti kalau webcam bukan kamera 0
CAM_W, CAM_H = 360, 270        # ukuran tampilan kamera

# Kotak deteksi pada tampilan kamera (x1, y1, x2, y2)
BOX_LEFT = (25, 95, 135, 205)
BOX_RIGHT = (225, 95, 335, 205)

# Rentang warna tangan di HSV (default = warna kulit).
# Kalau tangan / kertas warnamu tidak terdeteksi, ubah dua baris ini.
HAND_LOW = np.array([0, 40, 80])
HAND_HIGH = np.array([25, 255, 255])

# Porsi minimal piksel "warna tangan" di dalam kotak supaya dianggap 1 (true).
HAND_MAJORITY = 0.50

# ---------------------------------------------------------------------------
# Pengaturan game
# ---------------------------------------------------------------------------
GAME_W, GAME_H = 900, 520
ROAD_TOP, ROAD_BOTTOM = 200, 370      # batas jalan raya
LANES = (240, 330)                    # titik tengah 2 lajur
CROSS_X1, CROSS_X2 = 600, 690         # area zebra cross

# Kesulitan game (detik / piksel per detik)
CAR_GAP = (3.5, 5.5)                  # jeda antar mobil
PED_GAP = (1.4, 2.6)                  # jeda antar pejalan kaki
CAR_SPEED = (120, 200)
PED_SPEED = (105, 135)
MAX_PEDS = 5

BG = (40, 42, 46)
SIDEWALK = (92, 94, 98)
ROAD = (58, 59, 63)
STRIPE = (215, 216, 218)
LANE_MARK = (165, 167, 171)

GREEN = (80, 200, 90)
RED = (70, 70, 225)
YELLOW = (60, 210, 240)
WHITE = (240, 240, 240)
DARK = (28, 30, 34)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def text(img, s, org, color, scale=0.6, thickness=1):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                thickness, cv2.LINE_AA)


def text_right(img, s, x_right, y, color, scale=0.6, thickness=1):
    (w, _), _ = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    text(img, s, (x_right - w, y), color, scale, thickness)


def random_color():
    return (random.randint(70, 240), random.randint(70, 240), random.randint(70, 240))


def overlap(a, b):
    """True kalau dua kotak (dict dengan x, y, w, h) bertabrakan."""
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"]
            and a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])


def hand_ratio(hsv, box):
    """Porsi piksel warna tangan di dalam kotak deteksi (0.0 - 1.0)."""
    x1, y1, x2, y2 = box
    roi = hsv[y1:y2, x1:x2]
    if roi.size == 0:
        return 0.0
    mask = cv2.inRange(roi, HAND_LOW, HAND_HIGH)
    return cv2.countNonZero(mask) / float(roi.shape[0] * roi.shape[1])


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------
class Game:
    def __init__(self):
        self.cars = []        # {x, y, w, h, speed, color}
        self.peds = []        # {x, y, w, h, dir, speed, color, go, timer}
        self.car_timer = 0.4
        self.ped_timer = 0.6
        self.saved = 0        # pejalan kaki yang selamat sampai seberang
        self.crashed = 0      # pejalan kaki yang tertabrak
        self.flash = 0.0

    # ---------------- logika ----------------
    def update(self, dt, left_on, right_on):
        self.flash = max(0.0, self.flash - dt)

        # mobil: spawn acak, jalan ke kiri
        self.car_timer -= dt
        if self.car_timer <= 0:
            self.spawn_car()
            self.car_timer = random.uniform(*CAR_GAP)

        for car in self.cars:
            car["x"] -= car["speed"] * dt
        self.cars = [c for c in self.cars if c["x"] + c["w"] > -20]

        # pejalan kaki: spawn acak
        self.ped_timer -= dt
        if self.ped_timer <= 0 and len(self.peds) < MAX_PEDS:
            self.spawn_ped()
            self.ped_timer = random.uniform(*PED_GAP)

        # kiri = berhenti, kanan = jalan, lainnya = acak
        if left_on and not right_on:
            go = False
        elif right_on and not left_on:
            go = True
        else:
            go = None

        for ped in self.peds:
            if go is None:
                # acak: ganti keputusan tiap 0.3 - 0.9 detik
                ped["timer"] -= dt
                if ped["timer"] <= 0:
                    ped["go"] = random.random() < 0.5
                    ped["timer"] = random.uniform(0.3, 0.9)
            else:
                ped["go"] = go
                ped["timer"] = random.uniform(0.3, 0.9)

            if ped["go"]:
                ped["y"] += ped["dir"] * ped["speed"] * dt

        # cek tabrakan & pejalan kaki yang sudah sampai
        alive = []
        for ped in self.peds:
            if any(overlap(ped, car) for car in self.cars):
                self.crashed += 1
                self.flash = 1.0
                continue
            if ped["dir"] < 0 and ped["y"] + ped["h"] < ROAD_TOP - 30:
                self.saved += 1
                continue
            if ped["dir"] > 0 and ped["y"] > ROAD_BOTTOM + 30:
                self.saved += 1
                continue
            alive.append(ped)
        self.peds = alive

    def spawn_car(self):
        w = random.randint(70, 130)
        h = random.randint(44, 54)
        lane_y = random.choice(LANES)
        self.cars.append({
            "x": float(GAME_W + 20),
            "y": lane_y - h // 2,
            "w": w,
            "h": h,
            "speed": random.uniform(*CAR_SPEED),
            "color": random_color(),
        })

    def spawn_ped(self):
        d = random.choice((-1, 1))            # -1 = jalan ke atas, 1 = ke bawah
        w = random.randint(12, 16)
        h = random.randint(24, 30)
        x = random.randint(CROSS_X1 + 6, CROSS_X2 - 6 - w)
        y = ROAD_BOTTOM + 12 if d < 0 else ROAD_TOP - 12 - h
        self.peds.append({
            "x": x,
            "y": y,
            "w": w,
            "h": h,
            "dir": d,
            "speed": random.uniform(*PED_SPEED),
            "color": (60, 200, 250),
            "go": True,
            "timer": 0.0,
        })

    # ---------------- gambar ----------------
    def draw(self, left_on, right_on, ratio_l, ratio_r):
        img = np.full((GAME_H, GAME_W, 3), BG, np.uint8)

        # trotoar & jalan
        cv2.rectangle(img, (0, 0), (GAME_W, ROAD_TOP), SIDEWALK, -1)
        cv2.rectangle(img, (0, ROAD_BOTTOM), (GAME_W, GAME_H), SIDEWALK, -1)
        cv2.rectangle(img, (0, ROAD_TOP), (GAME_W, ROAD_BOTTOM), ROAD, -1)

        # marka lajur putus-putus
        mid = (ROAD_TOP + ROAD_BOTTOM) // 2
        for x in range(10, GAME_W, 70):
            cv2.rectangle(img, (x, mid - 2), (x + 34, mid + 2), LANE_MARK, -1)

        # zebra cross
        for x in range(CROSS_X1, CROSS_X2, 26):
            cv2.rectangle(img, (x, ROAD_TOP + 4), (x + 12, ROAD_BOTTOM - 4),
                          STRIPE, -1)

        # mobil (kotak warna acak)
        for car in self.cars:
            x, y, w, h = int(car["x"]), car["y"], car["w"], car["h"]
            cv2.rectangle(img, (x, y), (x + w, y + h), car["color"], -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), DARK, 2)
            cv2.rectangle(img, (x + w // 4, y + 9),
                          (x + w // 4 + w // 3, y + h - 9), DARK, -1)

        # pejalan kaki
        for ped in self.peds:
            x, y, w, h = int(ped["x"]), int(ped["y"]), ped["w"], ped["h"]
            cv2.rectangle(img, (x, y), (x + w, y + h), ped["color"], -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), DARK, 1)

        # panel status deteksi
        cv2.rectangle(img, (12, 12), (300, 96), DARK, -1)
        cv2.rectangle(img, (12, 12), (300, 96), (90, 92, 98), 1)
        c = GREEN if left_on else RED
        text(img, "KIRI   : %d  (%2.0f%%)" % (left_on, ratio_l * 100), (26, 44), c, 0.6)
        c = GREEN if right_on else RED
        text(img, "KANAN  : %d  (%2.0f%%)" % (right_on, ratio_r * 100), (26, 80), c, 0.6)

        # mode pejalan kaki
        if left_on and not right_on:
            mode, mc = "PEJALAN KAKI: BERHENTI", RED
        elif right_on and not left_on:
            mode, mc = "PEJALAN KAKI: JALAN", GREEN
        else:
            mode, mc = "PEJALAN KAKI: ACAK", YELLOW
        text_right(img, mode, GAME_W - 16, 44, mc, 0.7, 2)

        # skor
        text(img, "Selamat: %d    Tertabrak: %d" % (self.saved, self.crashed),
             (16, GAME_H - 18), WHITE, 0.7)

        # hint
        text_right(img, "tangan di KIRI = stop, tangan di KANAN = jalan",
                   GAME_W - 16, GAME_H - 18, (200, 200, 200), 0.5)

        # efek tertabrak
        if self.flash > 0:
            msg = "TERTABRAK!"
            (mw, _), _ = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1.4, 4)
            text(img, msg, ((GAME_W - mw) // 2, 130), RED, 1.4, 4)

        return img


# ---------------------------------------------------------------------------
# Tampilan kamera
# ---------------------------------------------------------------------------
def draw_camera(cam, left_on, right_on, ratio_l, ratio_r):
    for box, on, ratio, label in ((BOX_LEFT, left_on, ratio_l, "KIRI"),
                                  (BOX_RIGHT, right_on, ratio_r, "KANAN")):
        color = GREEN if on else RED
        cv2.rectangle(cam, box[:2], box[2:], color, 2)
        text(cam, "%s %d (%.0f%%)" % (label, on, ratio * 100),
             (box[0], box[1] - 8), color, 0.5, 2)
    text(cam, "q / ESC = keluar", (12, CAM_H - 12), WHITE, 0.5)
    return cam


# ---------------------------------------------------------------------------
# Program utama
# ---------------------------------------------------------------------------
def main():
    cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        raise SystemExit("Kamera tidak bisa dibuka. Cek CAM_INDEX / izin kamera.")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cv2.namedWindow("Kamera")
    cv2.namedWindow("Game")
    cv2.moveWindow("Game", 10, 10)
    cv2.moveWindow("Kamera", 930, 10)

    game = Game()
    last = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        # kamera dibuat seperti cermin (flip kiri-kanan)
        cam = cv2.flip(cv2.resize(frame, (CAM_W, CAM_H)), 1)
        hsv = cv2.cvtColor(cam, cv2.COLOR_BGR2HSV)
        rl = hand_ratio(hsv, BOX_LEFT)
        rr = hand_ratio(hsv, BOX_RIGHT)
        left_on = rl > HAND_MAJORITY
        right_on = rr > HAND_MAJORITY

        now = time.perf_counter()
        dt = min(0.05, now - last)     # dibatasi supaya game tidak "lompat"
        last = now
        game.update(dt, left_on, right_on)

        # tampilan kamera + kotak deteksi
        draw_camera(cam, left_on, right_on, rl, rr)

        cv2.imshow("Kamera", cam)
        cv2.imshow("Game", game.draw(left_on, right_on, rl, rr))

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
