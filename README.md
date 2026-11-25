# PCV Project 1 — Mini Game Simpang Jalan

Game sederhana pakai kamera. Mobil (kotak dengan warna acak) lewat di jalan,
pejalan kaki menyeberang lewat zebra cross. Kamu mengatur pejalan kaki dengan
**warna tangan** di dua kotak deteksi.

| Kotak | Kondisi | Pejalan kaki |
|-------|---------|--------------|
| KIRI  | true (mayoritas warna tangan)  | berhenti |
| KANAN | true (mayoritas warna tangan)  | jalan |
| dua-duanya / tidak ada | — | jalan secara acak |

Kalau pejalan kaki kena mobil: **Tertabrak**. Kalau sampai seberang: **Selamat**.

## Jalankan

```bash
pip install -r requirements.txt
python main.py
```

Tekan `q` atau `ESC` untuk keluar.

## Cara main

1. Arahkan kamera ke latar yang polos (dinding / kertas putih).
2. Tangan di dalam kotak **KIRI** → pejalan kaki berhenti.
3. Tangan di dalam kotak **KANAN** → pejalan kaki jalan.
4. Tangan di dua kotak, atau tidak di mana pun → pejalan kaki jalan acak.

Kotak dianggap **1 (true)** kalau lebih dari separuh luas kotak
(`HAND_MAJORITY = 0.50`) berisi warna tangan. Jadi isi kotaknya sampai penuh,
jangan cuma ujung jari.

## Kalau tangan tidak terdeteksi

Semua pengaturan ada di bagian atas `main.py`:

- `HAND_LOW`, `HAND_HIGH` — rentang HSV warna tangan. Default warna kulit.
  Kalau pakai kertas warna / sarung tangan, sesuaikan rentangnya
  (contoh kuning: `[20, 100, 100]` sampai `[35, 255, 255]`).
- `HAND_MAJORITY` — porsi minimal piksel tangan di dalam kotak.
- `BOX_LEFT`, `BOX_RIGHT` — posisi & ukuran kotak deteksi di tampilan kamera.
- `CAM_INDEX` — ganti kalau webcam bukan kamera 0.

## Isi folder

```
main.py            satu file, semua logika + tampilan (tanpa pipeline)
requirements.txt   opencv-python, numpy
```
