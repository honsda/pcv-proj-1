import random
import time

import cv2
import numpy as np

CAM_INDEX = 0
CAM_W, CAM_H = 360, 270

BOX_LEFT = (25, 95, 135, 205)
BOX_RIGHT = (225, 95, 335, 205)

HAND_LOW = np.array([0, 40, 80])
HAND_HIGH = np.array([25, 255, 255])
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
DARK = (28, 30, 34)


def text(img, s, org, color, scale=0.6, thickness=1):
    cv2.putText(img, s, org, cv2.FONT_HERSHEY_SIMPLEX, scale, color,
                thickness, cv2.LINE_AA)


def text_right(img, s, x, y, color, scale=0.6, thickness=1):
    w = cv2.getTextSize(s, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)[0][0]
    text(img, s, (x - w, y), color, scale, thickness)


def overlap(a, b):
    return (a["x"] < b["x"] + b["w"] and a["x"] + a["w"] > b["x"] and
            a["y"] < b["y"] + b["h"] and a["y"] + a["h"] > b["y"])


def hand_ratio(hsv, box):
    x1, y1, x2, y2 = box
    mask = cv2.inRange(hsv[y1:y2, x1:x2], HAND_LOW, HAND_HIGH)
    return cv2.countNonZero(mask) / mask.size


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
                   GAME_W - 16, GAME_H - 18, (200, 200, 200), 0.5)

        if self.flash > 0:
            text_right(img, "TERTABRAK!", GAME_W // 2 + 110, 130, RED, 1.4, 4)

        return img


def draw_camera(cam, left_on, right_on, ratio_l, ratio_r):
    for box, on, ratio, label in ((BOX_LEFT, left_on, ratio_l, "KIRI"),
                                  (BOX_RIGHT, right_on, ratio_r, "KANAN")):
        color = GREEN if on else RED
        cv2.rectangle(cam, box[:2], box[2:], color, 2)
        text(cam, "%s %d (%.0f%%)" % (label, on, ratio * 100),
             (box[0], box[1] - 8), color, 0.5, 2)
    text(cam, "q / ESC = keluar", (12, CAM_H - 12), WHITE, 0.5)
    return cam


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

        cam = cv2.flip(cv2.resize(frame, (CAM_W, CAM_H)), 1)
        hsv = cv2.cvtColor(cam, cv2.COLOR_BGR2HSV)
        rl = hand_ratio(hsv, BOX_LEFT)
        rr = hand_ratio(hsv, BOX_RIGHT)
        left_on = rl > HAND_MAJORITY
        right_on = rr > HAND_MAJORITY

        now = time.perf_counter()
        dt = min(0.05, now - last)
        last = now
        game.update(dt, left_on, right_on)

        draw_camera(cam, left_on, right_on, rl, rr)

        cv2.imshow("Kamera", cam)
        cv2.imshow("Game", game.draw(left_on, right_on, rl, rr))

        if cv2.waitKey(1) & 0xFF in (27, ord("q")):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
