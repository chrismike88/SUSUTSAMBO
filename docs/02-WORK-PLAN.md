# Work Plan Penurunan Susut & Capaian per Item

> Dibangkitkan otomatis oleh `scripts/build_docs.py` dari `data/dataset.json`.
> Jangan disunting langsung — sunting datanya lalu jalankan `python3 scripts/build_all.py`.
>
> **Angka di bawah adalah data contoh**, bukan realisasi ULP Samboja yang sebenarnya.

**Periode data:** Agustus 2026  ·  **Bulan tersisa:** 4  ·  **Capaian rata-rata:** 75,05%

## Ringkasan status

| Status | Ambang | Jumlah item | Arti |
|---|---|---:|---|
| **TERCAPAI** | ≥ 100% | 2 | Sudah melampaui target sampai bulan berjalan |
| **WASPADA** | 90–99% | 4 | Sedikit tertinggal, masih terkejar dengan ritme sekarang |
| **TERLAMBAT** | 75–89% | 5 | Butuh percepatan terukur |
| **KRITIS** | < 75% | 11 | Wajib dibahas di rapat mingguan unit |

## Rekap per kategori

| Kategori | Item | Target kWh setahun | Terealisasi | Sisa | Capaian |
|---|---:|---:|---:|---:|---:|
| Teknis | 10 | 1.099.470 | 481.827 | 617.643 | 71,20% |
| Non-teknis | 12 | 2.787.040 | 1.477.981 | 1.309.059 | 78,25% |
| **Total** | **22** | **3.886.510** | **1.959.808** | **1.926.702** | **75,05%** |

## Program teknis

| Kode | Item work plan | Satuan | Target tahun | Target s/d bln | Realisasi | Capaian | Sisa target | Kebutuhan/bln | Faktor kejar | Sisa potensi kWh | Status | PIC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| T-10 | Uprating konduktor JTM (AAAC 150 mm2) | kms | 9,8 | 5,5 | 2,0 | 35,6% | 7,8 | 2,0 | 8,00× | 69.776 | KRITIS | SPV Teknik |
| T-06 | Pemasangan kapasitor bank (perbaikan cos phi) | unit | 8,0 | 4,5 | 2,0 | 44,2% | 6,0 | 1,5 | 6,08× | 83.076 | KRITIS | SPV Teknik |
| T-05 | Rekonfigurasi / pemecahan beban penyulang | penyulang | 6,0 | 3,4 | 1,7 | 50,3% | 4,3 | 1,1 | 5,10× | 90.510 | KRITIS | SPV Teknik |
| T-03 | Pemasangan trafo sisip / uprating trafo overload | unit | 12,0 | 6,5 | 3,8 | 57,9% | 8,2 | 2,1 | 4,40× | 94.875 | KRITIS | SPV Teknik |
| T-08 | Pemasangan alat ukur (AMR) sisi gardu distribusi | unit | 45,0 | 24,3 | 16,3 | 67,0% | 28,7 | 7,2 | 3,53× | 38.772 | KRITIS | SPV Teknik |
| T-02 | Penggantian konduktor JTR usang ke twisted cable | kms | 24,5 | 13,2 | 9,4 | 71,0% | 15,1 | 3,8 | 3,21× | 93.558 | KRITIS | SPV Teknik |
| T-04 | Penggantian SR > 30 m & kabel SR usang | pelanggan | 1.450,0 | 966,6 | 802,3 | 83,0% | 647,7 | 161,9 | 1,61× | 40.155 | TERLAMBAT | SPV Teknik |
| T-07 | Penggantian konektor & retensioning sambungan | titik | 620,0 | 413,4 | 392,7 | 95,0% | 227,3 | 56,8 | 1,16× | 32.963 | WASPADA | SPV Teknik |
| T-09 | Pemeliharaan preventif & perbaikan grounding gardu | gardu | 240,0 | 160,0 | 163,2 | 102,0% | 76,8 | 19,2 | 0,94× | 23.808 | TERCAPAI | SPV Teknik |
| T-01 | Penyeimbangan beban trafo distribusi (balancing) | gardu | 180,0 | 120,0 | 127,2 | 106,0% | 52,8 | 13,2 | 0,83× | 50.150 | TERCAPAI | SPV Teknik |

## Program non-teknis

| Kode | Item work plan | Satuan | Target tahun | Target s/d bln | Realisasi | Capaian | Sisa target | Kebutuhan/bln | Faktor kejar | Sisa potensi kWh | Status | PIC |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| N-09 | Penertiban & pemeteran PJU ilegal | titik | 320,0 | 172,8 | 95,0 | 55,0% | 225,0 | 56,2 | 4,73× | 143.981 | KRITIS | SPV Transaksi Energi |
| N-12 | Penormalan sambungan langsung / sambungan liar | titik | 210,0 | 140,0 | 85,4 | 61,0% | 124,6 | 31,1 | 2,92× | 110.894 | KRITIS | SPV Transaksi Energi |
| N-05 | Penggantian kWh meter tua (> 15 tahun) | unit | 1.900,0 | 1.026,0 | 646,4 | 63,0% | 1.253,6 | 313,4 | 3,88× | 89.008 | KRITIS | SPV Transaksi Energi |
| N-07 | Pemeriksaan APP pelanggan potensial (>= 3.500 VA) | pelanggan | 2.400,0 | 1.600,0 | 1.104,0 | 69,0% | 1.296,0 | 324,0 | 2,35× | 75.167 | KRITIS | SPV Transaksi Energi |
| N-03 | P2TL - realisasi penagihan tagihan susulan | Rp juta | 3.400,0 | 2.266,6 | 1.677,3 | 74,0% | 1.722,7 | 430,7 | 2,05× | – | KRITIS | SPV Transaksi Energi |
| N-06 | Pemasangan / normalisasi AMR pelanggan >= 41,5 kVA | pelanggan | 168,0 | 112,0 | 88,5 | 79,0% | 79,5 | 19,9 | 1,80× | 117.690 | TERLAMBAT | SPV Transaksi Energi |
| N-08 | Penurunan DLPD (Daftar Langganan Perlu Diperhatikan) | rekening | 4.200,0 | 2.800,0 | 2.268,0 | 81,0% | 1.932,0 | 483,0 | 1,70× | 85.008 | TERLAMBAT | SPV Pelayanan Pelanggan |
| N-04 | Penggantian kWh meter rusak / macet / buram | unit | 2.750,0 | 1.833,4 | 1.576,7 | 86,0% | 1.173,3 | 293,3 | 1,49× | 112.640 | TERLAMBAT | SPV Transaksi Energi |
| N-02 | P2TL - perolehan kWh temuan pelanggaran | kWh | 1.150.000,0 | 766.666,6 | 674.666,7 | 88,0% | 475.333,3 | 118.833,3 | 1,41× | 475.333 | TERLAMBAT | SPV Transaksi Energi |
| N-01 | P2TL - pencapaian Target Operasi (TO) | pelanggan | 3.600,0 | 2.400,0 | 2.208,0 | 92,0% | 1.392,0 | 348,0 | 1,26× | – | WASPADA | SPV Transaksi Energi |
| N-10 | Validasi faktor kali & Data Induk Langganan (DIL) | pelanggan | 1.100,0 | 733,4 | 689,3 | 94,0% | 410,7 | 102,7 | 1,19× | 48.458 | WASPADA | SPV Pelayanan Pelanggan |
| N-11 | Peningkatan akurasi baca meter (foto stand / RBM) | rekening | 12.000,0 | 8.000,0 | 7.760,0 | 97,0% | 4.240,0 | 1.060,0 | 1,09× | 50.880 | WASPADA | SPV Pelayanan Pelanggan |

## Faktor konversi kWh diselamatkan

Faktor ini mengubah volume pekerjaan menjadi perkiraan energi yang tidak jadi hilang. Nilainya **estimasi rekayasa** dan sebaiknya dikalibrasi dengan pengukuran sebelum–sesudah pada beberapa lokasi contoh.

| Kode | Satuan | kWh diselamatkan per satuan | Siklus |
|---|---|---:|---|
| T-01 | gardu | 950 | Bulanan |
| T-02 | kms | 6.200 | Triwulanan |
| T-03 | unit | 11.500 | Triwulanan |
| T-04 | pelanggan | 62 | Bulanan |
| T-05 | penyulang | 21.000 | Semesteran |
| T-06 | unit | 13.800 | Semesteran |
| T-07 | titik | 145 | Bulanan |
| T-08 | unit | 1.350 | Triwulanan |
| T-09 | gardu | 310 | Bulanan |
| T-10 | kms | 8.900 | Semesteran |
| N-01 | pelanggan | – | Bulanan |
| N-02 | kWh | 1 | Bulanan |
| N-03 | Rp juta | – | Bulanan |
| N-04 | unit | 96 | Bulanan |
| N-05 | unit | 71 | Triwulanan |
| N-06 | pelanggan | 1.480 | Bulanan |
| N-07 | pelanggan | 58 | Bulanan |
| N-08 | rekening | 44 | Bulanan |
| N-09 | titik | 640 | Triwulanan |
| N-10 | pelanggan | 118 | Bulanan |
| N-11 | rekening | 12 | Bulanan |
| N-12 | titik | 890 | Bulanan |

Item dengan tanda `–` diukur secara finansial atau sebagai aktivitas; energinya sudah dihitung pada item lain agar tidak terhitung dua kali (misalnya N-01 dihitung energinya lewat N-02).

## Gap menuju target akhir tahun

| | Skenario A — susut kumulatif | Skenario B — susut Desember |
|---|---:|---:|
| Gap kWh | 1.302.223 | 40.465 |
| Per bulan (4 bulan) | 325.556 | 10.116 |
| Nilai finansial | Rp 1.904.500.917 | Rp 59.179.416 |
| Sisa potensi work plan | 1.926.702 | 1.926.702 |
| **Rasio kecukupan** | **1,48×** | **47,61×** |

Pada kedua tafsir, sisa potensi work plan masih melampaui gap. Namun pada skenario A marginnya hanya 1,48× — target akan lepas bila eksekusi turun di bawah sekitar 68% dari sisa target. Gunakan halaman **Simulasi Target** untuk mengujinya.

