import random
import sys
import time

import cv2
import numpy as np

CAMERA = 0
CAM_W, CAM_H = 360, 270
REC_FRAMES = 20

BOX_LEFT = (25, 95, 135, 205)
BOX_RIGHT = (225, 95, 335, 205)

HAND_MAJORITY = 0.50

GAME_W, GAME_H = 900, 520
ROAD_TOP, ROAD_BOTTOM = 200, 370
LANES = (240, 330)
CROSS_X1, CROSS_X2 = 600, 690

CAR_GAP = (3.5, 5.5)
PED_GAP = (1.4, 2.6)
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
GREY = (190, 190, 190)
DARK = (28, 30, 34)


def text(img, s, org, color, scale=0.6, thickness=1):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                thickness, cv2.LINE_AA)


def text_right(img, s, x, y, color, scale=0.6, thickness=1):
    w = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0][0]
    text(img, s, (x - w, y), color, scale, thickness)


def text_center(img, s, y, color, scale=0.7, thickness=1):
    w = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0][0]
    text(img, s, ((GAME_W - w) // 2, y), color, scale, thickness)


def overlap(a, b):
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and
            a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])


def box_mean(img, box):
    x1, y1, x2, y2 = box
    return img[y1:y2, x1:x2].mean(axis=(0, 1))


def hand_ratio(img, box, bg, hand):
    x1, y1, x2, y2 = box
    roi = img[y1:y2, x1:x2].astype(np.float32)
    d_bg = ((roi - bg) ** 2).sum(axis=2)
    d_hand = ((roi - hand) ** 2).sum(axis=2)
    return float((d_hand < d_bg).mean())


class Game:
    def __init__(self):
        self.cars = []
        self.peds = []
        self.car_timer = 0.4
        self.ped_timer = 0.6
        self.saved = 0
        self.crashed = 0
        self.flash = 0.0

    def update(self, dt, left_on, right_on):
        self.flash = max(0.0, self.flash - dt)

        self.car_timer -= dt
        if self.car_timer <= 0:
            self.spawn_car()
            self.car_timer = random.uniform(*CAR_GAP)

        for car in self.cars:
            car["x"] -= car["speed"] * dt
        self.cars = [c for c in self.cars if c["x"] + c["w"] > -20]

        self.ped_timer -= dt
        if self.ped_timer <= 0 and len(self.peds) < MAX_PEDS:
            self.spawn_ped()
            self.ped_timer = random.uniform(*PED_GAP)

        if left_on and not right_on:
            go = False
        elif right_on and not left_on:
            go = True
        else:
            go = None

        for ped in self.peds:
            if go is None:
                ped["timer"] -= dt
                if ped["timer"] <= 0:
                    ped["go"] = random.random() < 0.5
                    ped["timer"] = random.uniform(0.3, 0.9)
            else:
                ped["go"] = go
                ped["timer"] = random.uniform(0.3, 0.9)

            if ped["go"]:
                ped["y"] += ped["dir"] * ped["speed"] * dt

        alive = []
        for ped in self.peds:
            if any(overlap(ped, car) for car in self.cars):
                self.crashed += 1
                self.flash = 1.0
            elif ped["dir"] < 0 and ped["y"] + ped["h"] < ROAD_TOP - 30:
                self.saved += 1
            elif ped["dir"] > 0 and ped["y"] > ROAD_BOTTOM + 30:
                self.saved += 1
            else:
                alive.append(ped)
        self.peds = alive

    def spawn_car(self):
        w = random.randint(70, 130)
        h = random.randint(44, 54)
        y = random.choice(LANES) - h // 2
        color = (random.randint(70, 240), random.randint(70, 240),
                 random.randint(70, 240))
        self.cars.append({"x": float(GAME_W + 20), "y": y, "w": w, "h": h,
                          "speed": random.uniform(*CAR_SPEED), "color": color})

    def spawn_ped(self):
        d = random.choice((-1, 1))
        w = random.randint(12, 16)
        h = random.randint(24, 30)
        y = ROAD_BOTTOM + 12 if d < 0 else ROAD_TOP - 12 - h
        self.peds.append({
            "x": random.randint(CROSS_X1 + 6, CROSS_X2 - 6 - w),
            "y": y, "w": w, "h": h, "dir": d,
            "speed": random.uniform(*PED_SPEED),
            "color": (60, 200, 250), "go": True, "timer": 0.0,
        })

    def draw(self, left_on, right_on, ratio_l, ratio_r):
        img = np.full((GAME_H, GAME_W, 3), BG, np.uint8)

        cv2.rectangle(img, (0, 0), (GAME_W, ROAD_TOP), SIDEWALK, -1)
        cv2.rectangle(img, (0, ROAD_BOTTOM), (GAME_W, GAME_H), SIDEWALK, -1)
        cv2.rectangle(img, (0, ROAD_TOP), (GAME_W, ROAD_BOTTOM), ROAD, -1)

        mid = (ROAD_TOP + ROAD_BOTTOM) // 2
        for x in range(10, GAME_W, 70):
            cv2.rectangle(img, (x, mid - 2), (x + 34, mid + 2), LANE_MARK, -1)

        for x in range(CROSS_X1, CROSS_X2, 26):
            cv2.rectangle(img, (x, ROAD_TOP + 4), (x + 12, ROAD_BOTTOM - 4),
                          STRIPE, -1)

        for car in self.cars:
            x, y, w, h = int(car["x"]), car["y"], car["w"], car["h"]
            cv2.rectangle(img, (x, y), (x + w, y + h), car["color"], -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), DARK, 2)
            cv2.rectangle(img, (x + w // 4, y + 9),
                          (x + w // 4 + w // 3, y + h - 9), DARK, -1)

        for ped in self.peds:
            x, y, w, h = int(ped["x"]), int(ped["y"]), ped["w"], ped["h"]
            cv2.rectangle(img, (x, y), (x + w, y + h), ped["color"], -1)
            cv2.rectangle(img, (x, y), (x + w, y + h), DARK, 1)

        cv2.rectangle(img, (12, 12), (300, 96), DARK, -1)
        cv2.rectangle(img, (12, 12), (300, 96), (90, 92, 98), 1)
        text(img, "KIRI   : %d  (%2.0f%%)" % (left_on, ratio_l * 100),
             (26, 44), GREEN if left_on else RED)
        text(img, "KANAN  : %d  (%2.0f%%)" % (right_on, ratio_r * 100),
             (26, 80), GREEN if right_on else RED)

        if left_on and not right_on:
            mode, mc = "PEJALAN KAKI: BERHENTI", RED
        elif right_on and not left_on:
            mode, mc = "PEJALAN KAKI: JALAN", GREEN
        else:
            mode, mc = "PEJALAN KAKI: ACAK", YELLOW
        text_right(img, mode, GAME_W - 16, 44, mc, 0.7, 2)

        text(img, "Selamat: %d    Tertabrak: %d" % (self.saved, self.crashed),
             (16, GAME_H - 18), WHITE, 0.7)
        text_right(img, "tangan di KIRI = stop, tangan di KANAN = jalan",
                   GAME_W - 16, GAME_H - 18, GREY, 0.5)

        if self.flash > 0:
            text_right(img, "TERTABRAK!", GAME_W // 2 + 110, 130, RED, 1.4, 4)

        return img


def screen_menu():
    lines = ("1. rekam kotak kosong", "2. rekam tangan di kotak kiri",
             "3. rekam tangan di kotak kanan")
    x = (GAME_W - max(cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0][0]
                      for s in lines)) // 2
    img = np.full((GAME_H, GAME_W, 3), BG, np.uint8)
    text_center(img, "MINI GAME SIMPANG JALAN", 140, WHITE, 1.1, 3)
    text_center(img, "kendalikan pejalan kaki dengan warna tangan", 190, GREY, 0.7)
    for i, s in enumerate(lines):
        text(img, s, (x, 265 + i * 40), WHITE, 0.7)
    text_center(img, "tekan SPASI untuk mulai", 440, GREEN, 0.9, 2)
    return img


def screen_cal(step, rec):
    titles = ("kosongkan kedua kotak", "angkat tangan di kotak KIRI",
              "angkat tangan di kotak KANAN")
    img = np.full((GAME_H, GAME_W, 3), BG, np.uint8)
    text_center(img, "KALIBRASI %d / 3" % (step + 1), 150, WHITE, 1.0, 2)
    text_center(img, titles[step], 230, YELLOW, 0.8, 2)
    if rec == 0:
        text_center(img, "tekan SPASI untuk merekam", 330, GREEN, 0.8, 2)
    else:
        text_center(img, "merekam %d%%" % (rec * 100 // REC_FRAMES),
                    330, GREEN, 0.8, 2)
        cv2.rectangle(img, (300, 360), (600, 382), (80, 82, 88), -1)
        cv2.rectangle(img, (300, 360),
                      (300 + 300 * rec // REC_FRAMES, 382), GREEN, -1)
    if step > 0:
        text_center(img, "isi kotak sampai lebih dari separuh", 470, GREY, 0.6)
    return img


def draw_camera(cam, label_l, label_r, color_l, color_r, active=(),
                hint="q / ESC = keluar"):
    for i, (box, s, c) in enumerate(zip((BOX_LEFT, BOX_RIGHT),
                                        (label_l, label_r),
                                        (color_l, color_r))):
        c = YELLOW if i in active else c
        cv2.rectangle(cam, box[:2], box[2:], c, 3 if i in active else 2)
        text(cam, s, (box[0], box[1] - 8), c, 0.5, 2)
    text(cam, hint, (12, CAM_H - 12), WHITE, 0.5)
    return cam


def camera_names():
    try:
        from pygrabber.dshow_graph import FilterGraph
    except ImportError:
        return []
    return FilterGraph().get_input_devices()


def open_camera(src):
    if isinstance(src, str) and not src.isdigit():
        names = camera_names()
        for i, name in enumerate(names):
            if src.lower() in name.lower():
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    return cap
        raise SystemExit('Kamera "%s" tidak ada. Terdeteksi: %s' % (src, names))
    cap = cv2.VideoCapture(int(src), cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise SystemExit("Kamera %s tidak bisa dibuka. Cek izin kamera." % src)
    return cap


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else CAMERA
    cap = open_camera(src)
    print("kamera:", src)

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    cv2.namedWindow("Kamera")
    cv2.namedWindow("Game")
    cv2.moveWindow("Game", 10, 10)
    cv2.moveWindow("Kamera", 930, 10)

    game = Game()
    bg = [None, None]
    hand = [None, None]
    acc = [np.zeros(3, np.float32), np.zeros(3, np.float32)]
    state, step, rec = "menu", 0, 0
    last = time.perf_counter()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        cam = cv2.flip(cv2.resize(frame, (CAM_W, CAM_H)), 1)

        if state == "menu":
            screen = screen_menu()
            draw_camera(cam, "KIRI", "KANAN", WHITE, WHITE)

        elif state == "game":
            rl = hand_ratio(cam, BOX_LEFT, bg[0], hand[0])
            rr = hand_ratio(cam, BOX_RIGHT, bg[1], hand[1])
            left_on = rl > HAND_MAJORITY
            right_on = rr > HAND_MAJORITY

            now = time.perf_counter()
            game.update(min(0.05, now - last), left_on, right_on)
            last = now

            screen = game.draw(left_on, right_on, rl, rr)
            draw_camera(cam, "KIRI %d (%.0f%%)" % (left_on, rl * 100),
                        "KANAN %d (%.0f%%)" % (right_on, rr * 100),
                        GREEN if left_on else RED,
                        GREEN if right_on else RED,
                        hint="q / ESC keluar, R kalibrasi ulang")

        else:
            if state == "cal_rec":
                acc[0] += box_mean(cam, BOX_LEFT)
                acc[1] += box_mean(cam, BOX_RIGHT)
                rec += 1

            screen = screen_cal(step, rec if state == "cal_rec" else 0)
            draw_camera(cam, "KIRI", "KANAN", WHITE, WHITE,
                        (0, 1) if step == 0 else (step - 1,))

            if state == "cal_rec" and rec >= REC_FRAMES:
                m0 = (acc[0] / rec).astype(np.float32)
                m1 = (acc[1] / rec).astype(np.float32)
                if step == 0:
                    bg = [m0, m1]
                elif step == 1:
                    hand[0] = m0
                else:
                    hand[1] = m1
                acc[0][:] = 0
                acc[1][:] = 0
                rec = 0
                step += 1
                state = "game" if step == 3 else "cal_wait"
                last = time.perf_counter()

        cv2.imshow("Kamera", cam)
        cv2.imshow("Game", screen)

        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break
        if key == 32:
            if state == "menu":
                state, step, rec = "cal_wait", 0, 0
            elif state == "cal_wait":
                acc[0][:] = 0
                acc[1][:] = 0
                rec = 0
                state = "cal_rec"
        elif key == ord("r") and state == "game":
            state, step, rec = "menu", 0, 0
            game = Game()

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
