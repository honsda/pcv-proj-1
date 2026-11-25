# PCV Project 1 — Mini Game Simpang Jalan

Game sederhana pakai kamera. Mobil (kotak warna acak) lewat di jalan, pejalan
kaki menyeberang lewat zebra cross. Kamu mengatur pejalan kaki dengan
**warna tangan** di dua kotak deteksi.

| Kotak | Kondisi | Pejalan kaki |
|-------|---------|--------------|
| KIRI  | true  | berhenti |
| KANAN | true  | jalan |
| dua-duanya / tidak ada | — | jalan secara acak |

Kena mobil = **Tertabrak**, sampai seberang = **Selamat**.

## Jalankan

```bash
pip install -r requirements.txt
python main.py
```

## Alur

1. **Menu** — tekan `SPASI` untuk mulai.
2. **Kalibrasi** (3 langkah, tiap langkah tekan `SPASI` untuk merekam ±0,7 detik):
   1. kosongkan kedua kotak → direkam sebagai "tidak ada tangan"
   2. angkat tangan di kotak **KIRI** → direkam sebagai "ada tangan"
   3. angkat tangan di kotak **KANAN** → direkam sebagai "ada tangan"
3. **Game** — kotak dianggap `1` (true) kalau lebih dari separuh isinya mirip
   warna tangan hasil rekaman, bukan warna kotak kosong hasil rekaman.

Saat kalibrasi, kotak yang sedang direkam ditandai kuning di jendela **Kamera**.
Tekan `R` saat bermain untuk kalibrasi ulang. `q` / `ESC` untuk keluar.

## Tes pakai OBS Virtual Camera

1. Buka OBS, tambah sumber (mis. **Media Source** berisi video tangan, atau
   **Video Capture Device**).
2. Klik **Start Virtual Camera** di panel Controls.
3. Jalankan game dengan kamera OBS:

```bash
python main.py "OBS Virtual Camera"
```

Atau set `CAMERA = "OBS Virtual Camera"` di `main.py`.

Kalau mau pakai index angka:

```bash
python -c "from pygrabber.dshow_graph import FilterGraph; print(FilterGraph().get_input_devices())"
python main.py 4
```

Nama kamera dicocokkan tanpa peduli huruf besar/kecil, jadi `"obs"` juga bisa.
Resolusi OBS (mis. 1920x1080) otomatis diperkecil ke 360x270 untuk deteksi.

## Tips

- Rekam dengan latar kotak yang tidak berubah-ubah (dinding polos paling aman).
- Isi kotak sampai lebih dari separuh — ujung jari saja tidak cukup.
- Kalau warna tangan mirip latar, deteksi jadi ragu-ragu; pakai sarung tangan
  atau kertas warna yang kontras.

## Pengaturan di `main.py`

- `REC_FRAMES` — jumlah frame yang direkam per langkah kalibrasi.
- `HAND_MAJORITY` — porsi minimal kotak yang harus mirip tangan (default 0,50).
- `BOX_LEFT`, `BOX_RIGHT` — posisi & ukuran kotak di tampilan kamera.
- `CAMERA` — index angka (`0`, `1`, ...) atau nama kamera (`"OBS Virtual Camera"`).
  Bisa juga lewat terminal: `python main.py "OBS Virtual Camera"`.
- `CAR_GAP`, `CAR_SPEED`, `PED_SPEED`, `MAX_PEDS` — tingkat kesulitan.

## Isi folder

```
main.py            satu file, semua logika + tampilan (tanpa pipeline)
requirements.txt   opencv-python, numpy
```
