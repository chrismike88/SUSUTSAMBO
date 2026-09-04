# Berkas Master — panduan pengisian

Seluruh angka yang dipakai dashboard berasal dari berkas CSV di folder ini.
Berkas CSV dapat dibuka langsung dengan **Excel** atau **LibreOffice** — tidak
perlu menyentuh kode.

Sesudah menyunting:

```bash
python3 scripts/validate_master.py   # periksa dulu, pastikan tidak ada galat
python3 scripts/build_all.py         # bangun ulang Excel, seed SQL, dokumen, web
```

> **Menyimpan dari Excel:** pilih **CSV UTF-8 (Comma delimited)**. Jangan
> memakai "CSV (Macintosh)" atau "CSV (MS-DOS)" agar huruf beraksen tidak rusak.
> Angka desimal boleh ditulis `0,88` maupun `0.88` — keduanya dikenali.
> Jangan menambahkan pemisah ribuan pada kolom angka.

---

## unit.csv — identitas unit

Satu baris saja.

| Kolom | Isi |
|---|---|
| `kode` | Kode unit, misal `ULP-SBJ` |
| `nama` | Nama unit, misal `ULP Samboja` |
| `up3` | Nama UP3 induk |
| `uid` | Nama UID |
| `manager` | Jabatan/nama penanggung jawab |
| `tahun` | Tahun anggaran yang dipantau |

## parameter.csv — angka acuan

| Kunci | Satuan | Arti |
|---|---|---|
| `tarif_rata_rata` | Rp/kWh | Harga jual rata-rata untuk mengubah kWh menjadi rupiah |
| `target_susut_akhir_tahun` | % | Target susut RKAP |
| `baseline_susut_2025` | % | Realisasi susut tahun sebelumnya |
| `floor_susut_teknis` | % | Perkiraan batas bawah susut teknis jaringan eksisting |
| `ambang_tercapai` / `ambang_waspada` / `ambang_terlambat` | % | Ambang status capaian, harus menurun berurutan |
| `jumlah_pelanggan`, `jumlah_gardu`, `jumlah_penyulang` | | Besaran unit — dicocokkan dengan `penyulang.csv` |
| `panjang_jtm_kms`, `panjang_jtr_kms` | kms | Panjang jaringan — dicocokkan dengan `penyulang.csv` |

## penyulang.csv — master penyulang

Satu baris per penyulang. **Ganti seluruhnya dengan penyulang riil ULP Samboja.**

| Kolom | Sumber | Catatan |
|---|---|---|
| `kode` | Penomoran unit | Harus unik |
| `nama` | Nama penyulang | |
| `jumlah_gardu` | Aplikasi jaringan distribusi | |
| `kapasitas_kva` | idem | Total kapasitas trafo pada penyulang |
| `panjang_jtm_kms`, `panjang_jtr_kms` | idem | |
| `jumlah_pelanggan` | AP2T | Jumlah seluruh baris harus mendekati `parameter.csv` |
| `susut_persen` | EIS-Susut | Susut penyulang pada bulan realisasi terakhir |
| `unbalance_persen` | SCADA / AMR / pengukuran | Ambang ≤ 10% |
| `cos_phi` | idem | Ambang ≥ 0,90 |
| `drop_tegangan_persen` | idem | Ambang ≤ 5% |
| `sr_lebih_30m` | Survei SR | Jumlah pelanggan dengan SR lebih dari 30 m |

Indeks prioritas dan kelas prioritas **dihitung otomatis** dari empat kolom
terakhir — tidak perlu diisi.

## neraca.csv — kWh salur & jual bulanan

Dua belas baris, satu per bulan.

| Kolom | Isi |
|---|---|
| `bulan` | 1–12 |
| `status_data` | `REALISASI` untuk bulan yang sudah tutup, `PROYEKSI` untuk rencana. Bulan REALISASI harus berurutan mulai Januari |
| `kwh_salur` | XPower / EIS-Susut — pembacaan APP outgoing penyulang di GI |
| `kwh_jual` | AP2T — rekening terbit bulan itu |
| `target_persen` | Target susut bulanan dari RKAP |
| `porsi_teknis` | Porsi susut teknis terhadap total susut, antara 0 dan 1 (misal `0.58`) |

Susut persen, kWh susut, dan kumulatif YTD **dihitung otomatis**.

## program.csv — katalog work plan

Satu baris per item. **Sesuaikan dengan work plan ULP Samboja yang berlaku** —
tambah, hapus, atau ubah barisnya sesuai kebutuhan.

| Kolom | Isi |
|---|---|
| `kode` | Penomoran bebas, biasanya `T-xx` untuk teknis dan `N-xx` untuk non-teknis |
| `nama` | Nama item work plan |
| `kategori` | Wajib `TEKNIS` atau `NON_TEKNIS` |
| `sub_kategori` | Pengelompokan bebas: Trafo, JTR, JTM, SR/APP, P2TL, AMR, dst. |
| `satuan` | gardu, kms, unit, pelanggan, titik, kWh, rekening, Rp juta |
| `siklus` | Bulanan / Triwulanan / Semesteran — hanya keterangan |
| `pic` | Penanggung jawab |
| `kwh_selamat_per_unit` | Perkiraan kWh yang tidak jadi hilang per satu satuan pekerjaan. Isi `0` untuk item yang diukur finansial atau sekadar aktivitas, agar energinya tidak terhitung dua kali |
| `target_tahun` | Target volume setahun |

> **Faktor `kwh_selamat_per_unit` adalah estimasi rekayasa, bukan hasil ukur.**
> Sebaiknya dikalibrasi dengan pengukuran sebelum–sesudah pada beberapa gardu
> contoh sebelum dipakai untuk mengambil keputusan besar.

## program_bulanan.csv — target & realisasi bulanan

Satu baris per **item × bulan**. Untuk 22 item berarti 264 baris.

| Kolom | Isi |
|---|---|
| `program_kode` | Harus ada di `program.csv` |
| `bulan` | 1–12 |
| `target_volume` | Target bulan itu. Jumlah 12 bulan harus mendekati `target_tahun` |
| `realisasi_volume` | **Kolom yang diisi setiap bulan.** Kosongkan untuk bulan yang belum tutup |

Mengisi realisasi pada bulan yang masih `PROYEKSI` di `neraca.csv` akan
ditolak pemeriksa — ubah dulu status bulannya menjadi `REALISASI`.

## susut_penyulang.csv — susut per penyulang per bulan

| Kolom | Isi |
|---|---|
| `penyulang_kode` | Harus ada di `penyulang.csv` |
| `bulan` | 1–12 |
| `susut_persen` | Susut penyulang bulan itu, dari EIS-Susut |

Cukup diisi untuk bulan yang sudah `REALISASI`.

## action_plan.csv — rencana aksi

| Kolom | Isi |
|---|---|
| `no` | Nomor urut tampilan |
| `prioritas` | `SANGAT TINGGI`, `TINGGI`, `SEDANG`, atau `RUTIN` |
| `kategori` | `TEKNIS` atau `NON_TEKNIS` |
| `program_kode` | Item work plan yang disasar — dampak kWh dihitung dari sisa targetnya |
| `aksi` | Tindakan konkret, bukan slogan |
| `akar_masalah` | Sebab yang hendak dihilangkan |
| `target_selesai` | Tanggal atau keterangan bebas |
| `pic` | Penanggung jawab |
| `status` | `RENCANA`, `BERJALAN`, `TERLAMBAT`, `TERCAPAI`, atau `BATAL` |
| `progres_persen` | 0–100 |

Kolom dampak kWh dan rupiah **dihitung otomatis** dari sisa target program yang
disasar.

---

## Urutan penggantian data yang disarankan

1. `unit.csv` dan `parameter.csv` — identitas dan angka acuan.
2. `penyulang.csv` — ganti seluruh baris dengan penyulang riil.
3. `program.csv` — sesuaikan daftar item work plan.
4. `program_bulanan.csv` — sebar target setahun ke dua belas bulan.
5. `neraca.csv` — masukkan kWh salur dan jual bulan-bulan yang sudah tutup.
6. `susut_penyulang.csv` dan `action_plan.csv`.

Setelah langkah 3, jumlah baris `program_bulanan.csv` harus disesuaikan: setiap
item work plan memerlukan dua belas baris. Jalankan
`python3 scripts/validate_master.py` — pemeriksa akan menyebutkan bulan mana
yang masih kurang untuk tiap item.
