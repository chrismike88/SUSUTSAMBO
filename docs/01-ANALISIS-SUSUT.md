# Analisis Susut Teknis & Non-Teknis — ULP Samboja

> **Peringatan tentang angka.** Seluruh angka dalam dokumen ini berasal dari
> `data/dataset.json`, yaitu **data contoh** yang disusun agar realistis dan
> konsisten secara matematis untuk membangun dashboard. Angka ini **bukan**
> realisasi ULP Samboja yang sebenarnya. Ganti isinya dengan data riil dari
> AP2T, XPower/EIS-Susut, Aplikasi P2TL, dan SCADA/AMR, lalu jalankan
> `python3 scripts/build_all.py` — seluruh dashboard Excel, seed
> Supabase, dan situs web akan ikut terhitung ulang dengan sendirinya.
> Metode, struktur, dan rumusnya tetap berlaku apa pun angkanya.

---

## 1. Ringkasan eksekutif

Empat kalimat yang perlu dibawa ke rapat:

1. **Susut kumulatif 6,55%** terhadap target kumulatif 6,38% — tertinggal
   **0,16 pp**. Namun tren bulanan membaik tajam: dari 7,27% di Januari menjadi
   6,03% di Agustus, dan sejak Juni sudah menempel target bulanan.
2. **Masalah utama bukan jaringan, melainkan penagihan dan penertiban.** Dari
   sisa potensi penurunan susut sebesar 1,93 juta kWh, **68% ada di program
   non-teknis** yang tidak menunggu pengadaan material.
3. **Target akhir tahun masih dapat dicapai** — sisa potensi work plan 1,93 juta
   kWh berbanding gap 1,30 juta kWh, rasio **1,48×**. Tetapi marginnya tipis dan
   **hanya berlaku bila 11 item berstatus KRITIS dituntaskan penuh**.
4. **Ada risiko tafsir target.** Angka 5,85% berarti dua hal yang sangat berbeda
   (lihat bagian 5). Pastikan dulu ke UP3 tafsir mana yang dipakai sebelum
   menyusun rencana kerja September–Desember.

---

## 2. Posisi susut saat ini

Susut distribusi dihitung dari selisih energi yang disalurkan dan energi yang
tertagih:

```
Susut (%) = (kWh Salur − kWh Jual) / kWh Salur × 100
```

| Ukuran | Nilai | Pembanding |
|---|---|---|
| Susut kumulatif (Jan–Ags) | **6,55%** | target kumulatif 6,38% → tertinggal 0,16 pp |
| Susut bulan Agustus | **6,03%** | target bulanan 5,95% → tertinggal 0,08 pp |
| Realisasi tahun lalu | 7,12% | perbaikan **0,58 pp** dalam delapan bulan |
| Target akhir tahun | 5,85% | sisa penurunan yang dibutuhkan |
| kWh salur kumulatif | 164.676.505 kWh | |
| kWh susut kumulatif | 10.777.367 kWh | |
| Nilai energi yang hilang | **Rp 15,76 miliar** | pada tarif rata-rata Rp 1.462,50/kWh |

**Cara membaca tren.** Deviasi kumulatif (+0,16 pp) lebih besar daripada deviasi
bulanan (+0,08 pp). Ini bukan pertanda kinerja memburuk — justru sebaliknya.
Angka kumulatif masih menanggung beban Januari–Maret yang buruk (7,27%, 7,05%,
6,90%) dan beban itu tidak bisa dihapus lagi. Kinerja bulan berjalan sudah jauh
lebih baik daripada yang tercermin pada angka kumulatif. Konsekuensinya penting:
**semakin lama target dikejar, semakin mahal harganya**, karena bulan-bulan awal
terus menyeret rata-rata.

---

## 3. Membedah susut

Pada Agustus, susut 6,03% terpecah menjadi:

| Jenis | Besaran | Porsi | Sifat |
|---|---|---|---|
| Susut teknis | 3,51% | 58,2% | rugi alamiah — bisa ditekan, tidak bisa dinolkan |
| Susut non-teknis | 2,52% | 41,8% | energi tersalur yang tidak tertagih — **bisa didekatkan ke nol** |

Pemisahan ini menentukan strategi. Susut teknis punya lantai: dengan konfigurasi
jaringan ULP Samboja saat ini, batas bawah yang realistis diperkirakan **3,30%**.
Artinya ruang perbaikan teknis yang tersisa hanya sekitar **0,21 pp**. Sisa
penurunan harus datang dari sisi non-teknis.

### 3.1 Susut teknis — di mana energi hilang

Rugi teknis terukur **798.831 kWh per bulan** (≈ Rp 1,17 miliar/bulan),
terdekomposisi sebagai berikut:

| Komponen jaringan | kWh/bulan | Porsi | Program penanganan |
|---|---:|---:|---|
| Jaringan Tegangan Rendah (JTR) | 255.517 | 31,99% | T-02, T-03 |
| Trafo distribusi (rugi inti + belitan) | 218.556 | 27,36% | T-01, T-03, T-09 |
| Sambungan Rumah & APP | 175.011 | 21,91% | T-04 |
| Jaringan Tegangan Menengah (JTM) | 116.471 | 14,58% | T-05, T-06, T-10 |
| Konektor & titik sambung | 33.276 | 4,17% | T-07 |

**Temuan pokok: 54% rugi teknis ada di sisi tegangan rendah dan trafo — bukan di
JTM.** Ini khas jaringan dengan JTR panjang dan gardu berbeban tinggi. Implikasi
praktisnya: uprating konduktor JTM yang mahal dan lama (T-10) bukan pengungkit
terbesar. Yang lebih berdampak adalah memperpendek JTR lewat trafo sisip (T-03),
mengganti JTR usang (T-02), dan menyeimbangkan beban trafo (T-01).

### 3.2 Susut terkonsentrasi pada sedikit penyulang

| Penyulang | Susut | Unbalance | Cos φ | Drop tegangan | SR > 30 m | Indeks | Prioritas |
|---|---:|---:|---:|---:|---:|---:|---|
| SBJ-01 Kuala Samboja | 7,94% | 21,4% | 0,86 | 6,8% | 412 | 88,8 | KRITIS |
| SBJ-02 Sungai Merdeka | 7,41% | 18,9% | 0,88 | 7,4% | 388 | 81,5 | KRITIS |
| SBJ-03 Handil Baru | 6,88% | 16,2% | 0,89 | 5,9% | 301 | 71,7 | KRITIS |
| SBJ-04 Argosari | 6,42% | 14,8% | 0,90 | 6,2% | 254 | 66,9 | TINGGI |
| SBJ-05 Bukit Raya | 5,97% | 13,1% | 0,91 | 5,1% | 226 | 59,2 | TINGGI |
| … | | | | | | | |
| SBJ-10 Sungai Seluang | 4,52% | 8,6% | 0,94 | 4,1% | 118 | 40,6 | RENDAH |

**Tiga penyulang teratas menanggung 47,1% seluruh kWh susut unit, padahal hanya
melayani 39,7% pelanggan.** Ketiganya melanggar ambang operasi secara bersamaan:
unbalance di atas 15% (ambang 10%), cos φ di bawah 0,90, dan drop tegangan di
atas 5%. Ini pola yang saling menguatkan — unbalance menaikkan arus netral,
cos φ rendah menaikkan arus total, dan keduanya memperbesar rugi I²R sekaligus
memperdalam drop tegangan.

**Konsekuensi manajerial:** memusatkan regu pada SBJ-01, SBJ-02, dan SBJ-03 akan
memberi hasil jauh lebih besar per hari kerja dibanding menyebar merata ke
sepuluh penyulang. Urutan tindakan pada ketiga penyulang itu:

1. **Penyeimbangan beban** (T-01) — paling murah, paling cepat, tanpa pengadaan.
   Unbalance 21,4% pada SBJ-01 adalah anomali yang harus dituntaskan dalam
   hitungan hari, bukan bulan.
2. **Kapasitor bank** (T-06) — memperbaiki cos φ 0,86–0,89 ke ≥ 0,90.
3. **Trafo sisip** (T-03) — memperpendek JTR sekaligus meredakan drop tegangan.
4. **Uprating konduktor JTM** (T-10) — terakhir, karena paling mahal dan lama.

### 3.3 Susut non-teknis — di mana energi tidak tertagih

Realisasi P2TL Januari–Agustus:

| Ukuran | Nilai |
|---|---:|
| Pemeriksaan | 2.208 pelanggan |
| Temuan pelanggaran | 222 |
| Hit rate | 10,05% |
| kWh temuan | 674.667 kWh |
| Tagihan susulan terbit | Rp 1,68 miliar |
| Tagihan susulan terbayar | Rp 1,27 miliar |
| **Efektivitas penagihan** | **75,76%** |

Sebaran golongan pelanggaran: P-II (mempengaruhi pengukuran energi) menyumbang
porsi kWh terbesar, disusul P-I (mempengaruhi batas daya). Pola ini menunjukkan
bahwa mayoritas kehilangan berasal dari manipulasi pengukuran pada pelanggan
terdaftar, bukan dari sambungan liar — sehingga jalur pemulihannya adalah
penagihan, bukan sekadar penertiban fisik.

**Kebocoran paling mahal ada di penagihan, bukan di lapangan.** Regu P2TL bekerja
baik (hit rate 10% tergolong sehat), tetapi **Rp 407 juta tagihan susulan belum
tertagih**. Temuan yang tidak tertagih tidak menurunkan susut sama sekali — ia
hanya berpindah dari kolom "susut" ke kolom "piutang". Ini bukan pekerjaan regu
teknik, melainkan pekerjaan administrasi dan penagihan yang sering luput dari
rapat susut.

---

## 4. Capaian work plan per item

Rata-rata capaian 22 item terhadap target sampai Agustus: **75,05%**.

| Status | Jumlah | Arti |
|---|---:|---|
| TERCAPAI (≥ 100%) | 2 | T-01, T-09 |
| WASPADA (90–99%) | 4 | N-01, N-10, N-11, T-07 |
| TERLAMBAT (75–89%) | 5 | N-02, N-04, N-06, N-08, T-04 |
| **KRITIS (< 75%)** | **11** | T-02, T-03, T-05, T-06, T-08, T-10, N-03, N-05, N-07, N-09, N-12 |

Perbandingan kategori:

| Kategori | Target kWh setahun | Terealisasi | Sisa | Capaian rata-rata |
|---|---:|---:|---:|---:|
| Program teknis (10 item) | 1.099.470 | 481.827 | 617.644 | 71,20% |
| Program non-teknis (12 item) | 2.787.040 | 1.477.981 | 1.309.059 | 78,25% |
| **Total** | **3.886.510** | **1.959.808** | **1.926.703** | **75,05%** |

### Delapan item dengan sisa potensi kWh terbesar

Urutan berdasarkan energi yang belum diselamatkan — bukan berdasarkan besarnya
target. Inilah tempat gap paling mungkin ditutup.

| Kode | Program | Capaian | Faktor kejar | Sisa potensi |
|---|---|---:|---:|---:|
| N-02 | P2TL — perolehan kWh temuan | 88,0% | 1,41× | 475.333 kWh |
| N-09 | Penertiban & pemeteran PJU ilegal | 55,0% | 4,73× | 143.974 kWh |
| N-06 | Pemasangan/normalisasi AMR ≥ 41,5 kVA | 79,0% | 1,80× | 117.690 kWh |
| N-04 | Penggantian kWh meter rusak/macet | 86,0% | 1,49× | 112.640 kWh |
| N-12 | Penormalan sambungan langsung | 61,0% | 2,92× | 110.894 kWh |
| T-03 | Trafo sisip / uprating trafo overload | 58,0% | 4,39× | 94.760 kWh |
| T-02 | Penggantian JTR usang → twisted cable | 71,0% | 3,22× | 93.682 kWh |
| T-05 | Rekonfigurasi/pemecahan beban penyulang | 50,0% | 5,14× | 90.720 kWh |

**Faktor kejar** adalah alat baca terpenting di tabel ini:

```
Faktor kejar = (sisa target ÷ bulan tersisa) ÷ (realisasi ÷ bulan berjalan)
```

Nilai **1,0** berarti cukup mempertahankan kecepatan sekarang. Nilai **5,14×**
pada T-05 berarti pekerjaan harus lima kali lebih cepat daripada yang selama ini
mampu dikerjakan. Angka semacam itu **tidak bisa diselesaikan dengan imbauan**.
Ia menandakan salah satu dari tiga hal: kurang regu, material belum datang, atau
targetnya memang tidak realistis sejak awal. Ketiganya keputusan manajerial, dan
lebih baik diputuskan sekarang daripada di bulan Desember.

Enam item dengan faktor kejar ≥ 2,9 (T-05, N-09, T-10, T-06, T-03, N-05, T-02,
N-12) sebaiknya dibicarakan sebagai **permintaan sumber daya**, bukan sebagai
teguran capaian.

---

## 5. Analisis gap: dua tafsir target yang berbeda jauh

Angka target 5,85% bisa dibaca dua cara, dan konsekuensi kerjanya sangat berbeda.

### Skenario A — target sebagai susut kumulatif (YTD) akhir tahun

Tafsir yang lazim dipakai menilai kinerja RKAP.

| Perhitungan | Nilai |
|---|---:|
| kWh susut maksimum setahun | 14.782.596 kWh |
| Sudah terpakai Jan–Ags | 10.777.367 kWh |
| Sisa jatah susut Sep–Des | 4.005.229 kWh |
| Setara susut Sep–Des maksimum | **4,55%** |
| Susut Sep–Des bila tanpa aksi tambahan (6,03%) | 5.307.452 kWh |
| **Gap yang harus ditutup** | **1.302.223 kWh** (325.556 kWh/bulan) |
| Nilai finansial gap | **Rp 1,90 miliar** |

Berat. Susut harus turun dari 6,03% ke 4,55% — anjlok 1,48 pp dalam empat bulan,
padahal delapan bulan pertama hanya berhasil menurunkan 1,24 pp.

### Skenario B — target sebagai susut bulan Desember (exit rate)

Tafsir yang menilai kondisi akhir jaringan.

| Perhitungan | Nilai |
|---|---:|
| Penurunan dibutuhkan dari Agustus | 0,18 pp |
| kWh susut maksimum di Desember | 1.315.098 kWh |
| **Gap yang harus ditutup** | **40.465 kWh** |
| Nilai finansial gap | Rp 59,2 juta |

Moderat. Tinggal melanjutkan tren yang sudah berjalan.

### Uji kecukupan

| | Skenario A | Skenario B |
|---|---:|---:|
| Gap | 1.302.223 kWh | 40.465 kWh |
| Sisa potensi work plan | 1.926.703 kWh | 1.926.703 kWh |
| **Rasio kecukupan** | **1,48×** | 47,6× |

**Kesimpulan: bahkan pada tafsir terberat, target masih dapat dicapai tanpa
program baru** — asalkan seluruh sisa work plan benar-benar dieksekusi. Namun
1,48× adalah margin yang tipis. Bila eksekusi hanya sampai ±68% dari sisa target,
skenario A akan lepas. Gunakan halaman **Simulasi Target** pada dashboard web
untuk menguji sendiri pada level eksekusi berapa target mulai lepas.

**Tindakan pertama yang disarankan: konfirmasikan tafsir target ke UP3.** Jika
yang berlaku skenario A, rencana kerja September–Desember harus disusun sebagai
operasi khusus dengan tambahan regu dan percepatan pengadaan. Jika skenario B,
melanjutkan ritme sekarang sudah memadai. Menyusun rencana tanpa memastikan hal
ini lebih dulu berisiko salah alokasi sumber daya selama empat bulan penuh.

---

## 6. Apa yang harus dilakukan

Disusun menurut rasio dampak terhadap usaha, bukan menurut urutan nomor program.

### Prioritas 1 — pekerjaan yang tidak menunggu pengadaan (mulai minggu ini)

| # | Aksi | Alasan | Dampak |
|---|---|---|---|
| 1 | **Task force penagihan tagihan susulan P2TL** (N-03) | Rp 407 juta sudah menjadi temuan sah tetapi belum tertagih. Tidak butuh material apa pun — hanya rekonsiliasi piutang, surat panggilan, opsi cicilan, dan pemutusan bagi penunggak > 30 hari. | Rp 407 jt langsung + memperbaiki efektivitas dari 75,8% |
| 2 | **Penyeimbangan beban SBJ-01, SBJ-02, SBJ-03** (T-01) | Unbalance 16–21% jauh melewati ambang 10%. Hanya butuh pengukuran dan pemindahan fasa. | Menurunkan rugi JTR & trafo yang menguasai 54% rugi teknis |
| 3 | **Sensus & pemeteran PJU ilegal** (N-09) | Capaian baru 55%, sisa potensi 143.974 kWh — terbesar kedua. Butuh koordinasi Pemda/Dishub, bukan material. | 143.974 kWh |
| 4 | **Percepatan target operasi P2TL** (N-02) | Faktor kejar hanya 1,41× — paling mudah dikejar di antara item besar. Sisa potensi terbesar. | 475.333 kWh |

### Prioritas 2 — pekerjaan berjadwal (perlu keputusan sumber daya sekarang)

| # | Aksi | Kendala | Dampak |
|---|---|---|---|
| 5 | Penormalan sambungan langsung (N-12) | Butuh operasi bersama aparat | 110.894 kWh |
| 6 | Penggantian kWh meter rusak & tua (N-04, N-05) | Butuh stok meter | 201.647 kWh |
| 7 | Normalisasi AMR pelanggan besar (N-06) | Butuh modem & sinyal | 117.690 kWh |
| 8 | Trafo sisip & JTR twisted (T-03, T-02) | Butuh pengadaan — **putuskan bulan ini atau relakan** | 188.442 kWh |

### Prioritas 3 — tinjau ulang kelayakan targetnya

T-05 (faktor kejar 5,14×), T-10 (8,00×), T-06 (6,08×), dan N-09 (4,73×) menuntut
kecepatan yang belum pernah dicapai unit sepanjang tahun ini. Bawa keempatnya ke
UP3 sebagai satu paket: **minta tambahan sumber daya, atau ajukan revisi target
secara tertulis**. Membiarkannya berjalan apa adanya sampai Desember adalah
pilihan terburuk — targetnya tetap tidak tercapai, dan tidak ada jejak bahwa
kendalanya pernah disampaikan.

### Ritme kerja yang disarankan

- **Mingguan** — rapat 30 menit dengan halaman *Rencana Aksi*. Bahas hanya
  prioritas SANGAT TINGGI dan yang berstatus TERLAMBAT. Tiga pertanyaan per baris:
  berapa yang selesai minggu ini, apa penghambatnya, apakah kebutuhan per bulan
  masih masuk akal.
- **Bulanan** — perbarui neraca energi dan realisasi work plan, lalu baca ulang
  faktor kejar. Faktor kejar yang naik dua bulan berturut-turut adalah alarm.
- **Triwulanan** — tinjau ulang asumsi pada halaman *Simulasi Target* dan
  laporkan posisi gap ke UP3.

---

## 7. Batas dari analisis ini

Beberapa hal yang perlu diketahui agar angkanya tidak dibaca berlebihan:

1. **Faktor kWh selamat per satuan adalah estimasi rekayasa**, bukan hasil
   pengukuran. Nilainya disimpan di kolom `kwh_selamat_per_unit` pada tabel
   `susut.program` dan sebaiknya dikalibrasi memakai hasil pengukuran sebelum
   dan sesudah pekerjaan pada beberapa gardu contoh.
2. **Pemisahan teknis dan non-teknis adalah hasil estimasi**, karena keduanya
   tidak terukur terpisah pada meter mana pun. Ia diperoleh dengan menghitung
   rugi teknis secara rekayasa, lalu menetapkan sisanya sebagai non-teknis.
   Semakin banyak AMR gardu terpasang (T-08), semakin sempit ketidakpastiannya.
3. **kWh susut sensitif terhadap ketidakserentakan pembacaan.** Bila stand meter
   pelanggan dan APP penyulang tidak dibaca pada tanggal yang sama, akan muncul
   susut semu. Beda satu hari pada unit sebesar ini sudah bergeser sekitar 0,1 pp.
4. **Simulasi menganggap penghematan terwujud dalam periode Sep–Des.** Pekerjaan
   yang selesai di penghujung Desember tidak akan sempat menyumbang penuh pada
   tahun berjalan.

---

## 8. Cara memperbarui analisis ini dengan data riil

| Data | Sumber | Masuk ke berkas |
|---|---|---|
| kWh salur & jual | XPower/EIS-Susut (APP outgoing GI) + AP2T | `data/master/neraca.csv` |
| Susut per penyulang | EIS-Susut | `data/master/susut_penyulang.csv` |
| Realisasi program | Laporan regu, aplikasi Gardu/JDN, aplikasi P2TL | `data/master/program_bulanan.csv` |
| Unbalance, cos φ, tegangan | SCADA, AMR gardu, pengukuran manual | `data/master/penyulang.csv` |
| Aset jaringan | Aplikasi jaringan distribusi | `data/master/penyulang.csv` |
| Daftar item work plan | Work plan unit | `data/master/program.csv` |

Dua cara memperbarui:

- **Lewat berkas CSV** — sunting `data/master/*.csv` (bisa dengan Excel),
  jalankan `python3 scripts/validate_master.py` lalu
  `python3 scripts/build_all.py`, commit, dan Vercel akan menerbitkan ulang
  situsnya secara otomatis. Panduan kolomnya ada di
  [`data/master/README.md`](../data/master/README.md).
- **Lewat basis data** — masukkan data ke Supabase (lihat
  [`03-PANDUAN-DEPLOY.md`](03-PANDUAN-DEPLOY.md)). Begitu variabel lingkungan
  Supabase terpasang, dashboard web membaca langsung dari basis data dan berkas
  contoh tidak lagi dipakai.
