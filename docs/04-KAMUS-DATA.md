# Kamus Data & Prosedur Bulanan

## 1. Istilah

| Istilah | Arti |
|---|---|
| **Susut distribusi** | `(kWh Salur − kWh Jual) ÷ kWh Salur × 100%` |
| **kWh Salur** | Energi yang masuk jaringan distribusi, dibaca dari APP *outgoing* penyulang di Gardu Induk |
| **kWh Jual** | Energi yang terbit sebagai rekening pada bulan berjalan (AP2T/TUL) |
| **Susut teknis** | Rugi alamiah pada trafo, JTM, JTR, SR, dan konektor akibat rugi I²R dan rugi inti besi. Tidak bisa nol |
| **Susut non-teknis** | Energi tersalur yang tidak menjadi rekening: pelanggaran pemakaian, meter rusak/lambat, kesalahan baca, PJU tanpa meter, kesalahan administrasi |
| **Susut kumulatif (YTD)** | Total kWh susut sejak Januari dibagi total kWh salur sejak Januari |
| **Exit rate** | Susut pada bulan Desember saja — menggambarkan kondisi akhir jaringan |
| **Unbalance** | Ketidakseimbangan arus antar fasa. Menimbulkan arus netral dan rugi tambahan. Ambang ≤ 10% |
| **Cos φ** | Faktor daya. Semakin rendah, semakin besar arus untuk daya nyata yang sama. Ambang ≥ 0,90 |
| **Faktor kejar** | `(sisa target ÷ bulan tersisa) ÷ (realisasi ÷ bulan berjalan)`. Berapa kali lipat kecepatan kerja harus dinaikkan |
| **kWh selamat** | Perkiraan energi yang tidak jadi hilang karena satu satuan pekerjaan dikerjakan |
| **P2TL** | Penertiban Pemakaian Tenaga Listrik |
| **Tagihan susulan** | Tagihan atas pelanggaran hasil P2TL. Baru menurunkan susut setelah benar-benar tertagih |
| **DLPD** | Daftar Langganan Perlu Diperhatikan — rekening dengan stand meter anomali |
| **DIL** | Data Induk Langganan |
| **APP** | Alat Pengukur dan Pembatas |
| **AMR** | *Automatic Meter Reading* — pembacaan meter jarak jauh |
| **Trafo sisip** | Trafo tambahan untuk memperpendek JTR dan meredakan pembebanan |

### Golongan pelanggaran P2TL

| Golongan | Uraian |
|---|---|
| P-I | Mempengaruhi batas daya |
| P-II | Mempengaruhi pengukuran energi |
| P-III | Mempengaruhi batas daya **dan** pengukuran energi |
| P-IV | Bukan pelanggan — sambungan langsung |

---

## 2. Tabel basis data

Seluruhnya berada di skema `susut`.

| Tabel | Isi | Sumber data |
|---|---|---|
| `unit` | Identitas ULP dan besaran asetnya | Master unit |
| `parameter` | Tarif, target, ambang status | Ditetapkan manajemen |
| `penyulang` | Master penyulang + profil kondisi terkini | Aplikasi jaringan, SCADA, AMR |
| `neraca_energi` | kWh salur & jual bulanan | XPower/EIS-Susut + AP2T |
| `program` | Katalog 22 item work plan + faktor konversi kWh | Work plan unit |
| `program_periode` | Target & realisasi tiap item per bulan | Laporan regu, aplikasi P2TL |
| `susut_penyulang` | Susut per penyulang per bulan | EIS-Susut |
| `rugi_teknis` | Dekomposisi rugi teknis per komponen | Perhitungan rekayasa |
| `p2tl` | Rekap pemeriksaan, temuan, tagihan susulan | Aplikasi P2TL |
| `action_plan` | Rencana aksi percepatan | Disusun manajemen unit |
| `profil` | Pengguna dashboard dan perannya | Terisi otomatis saat mendaftar |
| `audit_log` | Riwayat perubahan data transaksi | Terisi otomatis oleh pemicu |

### View utama

| View | Kegunaan |
|---|---|
| `v_kpi_ringkas` | Satu baris ringkasan seluruh KPI — konsumsi utama dashboard |
| `v_capaian_program` | Capaian tiap item + sisa target + faktor kejar |
| `v_capaian_kategori` | Rollup teknis vs non-teknis |
| `v_neraca` | Neraca energi + kolom kumulatif berjalan |
| `v_ranking_penyulang` | Peringkat penyulang menurut indeks prioritas |
| `v_rugi_teknis_komponen` | Rugi teknis per komponen jaringan |
| `v_p2tl_bulanan` | Rekap P2TL + hit rate + efektivitas penagihan |
| `v_gap_target` | Perhitungan dua skenario gap |
| `v_action_plan` | Rencana aksi diperkaya data capaian program |

Seluruhnya juga terekspos di skema `public` dengan awalan `susut_`
(misalnya `public.susut_kpi_ringkas`) agar dapat diakses REST API Supabase
tanpa mengubah setelan *exposed schemas*.

---

## 3. Rumus yang dipakai

```
Susut (%)              = (kWh Salur − kWh Jual) ÷ kWh Salur × 100
Susut kumulatif (%)    = Σ kWh Susut ÷ Σ kWh Salur × 100
Capaian item (%)       = realisasi s/d bulan ÷ target s/d bulan × 100
Sisa target            = target tahun − realisasi s/d bulan
Kebutuhan per bulan    = sisa target ÷ bulan tersisa
Run-rate bulanan       = realisasi s/d bulan ÷ bulan berjalan
Faktor kejar           = kebutuhan per bulan ÷ run-rate bulanan
kWh selamat            = realisasi volume × kWh selamat per satuan
Nilai rupiah           = kWh × tarif rata-rata
Indeks prioritas       = (susut/8)×40 + (unbalance/25)×25
                         + ((0,95 − cos φ)/0,12)×20 + (drop tegangan/8)×15
```

### Ambang status capaian

| Status | Capaian terhadap target s/d bulan berjalan |
|---|---|
| TERCAPAI | ≥ 100% |
| WASPADA | 90–99,99% |
| TERLAMBAT | 75–89,99% |
| KRITIS | < 75% |

### Ambang operasi jaringan

| Parameter | Ambang | Tindakan bila terlampaui |
|---|---|---|
| Unbalance arus antar fasa | ≤ 10% | Di atas 15% wajib penyeimbangan beban dalam 7 hari |
| Cos φ | ≥ 0,90 | Pasang kapasitor bank |
| Drop tegangan ujung | ≤ 5% | Uprating konduktor atau trafo sisip |
| Panjang SR | ≤ 30 m | Jadwalkan penggantian |
| Pembebanan trafo | ≤ 80% | Uprating trafo atau trafo sisip |
| Panjang JTR per gardu | ≤ 350 m | Pasang trafo sisip |

---

## 4. Prosedur bulanan

### Langkah 1 — kumpulkan data (hari kerja ke-1 s/d ke-5)

| Data | Diambil dari | Penanggung jawab |
|---|---|---|
| kWh salur per penyulang | XPower / EIS-Susut | SPV Teknik |
| kWh jual | AP2T — rekening terbit | SPV Pelayanan Pelanggan |
| Realisasi program teknis | Laporan harian regu | SPV Teknik |
| Realisasi P2TL & tagihan | Aplikasi P2TL | SPV Transaksi Energi |
| Unbalance, cos φ, tegangan | SCADA / AMR / pengukuran | SPV Teknik |

> **Pastikan tanggal pembacaan serentak.** Bila stand meter pelanggan dan APP
> penyulang tidak dibaca pada tanggal yang sama, akan muncul susut semu. Pada
> unit sebesar ULP Samboja, selisih satu hari saja sudah menggeser angka susut
> sekitar 0,1 pp.

### Langkah 2 — perbarui sistem (hari kerja ke-6)

Pilih salah satu jalur.

**Jalur berkas** — cocok bila belum memakai Supabase:

1. Sunting `_NERACA_INPUT` pada `scripts/dataset.py`: masukkan kWh salur dan
   susut bulan yang baru tutup, ubah statusnya dari proyeksi menjadi realisasi.
2. Sunting realisasi tiap item work plan.
3. Jalankan `python3 scripts/build_all.py`.
4. `git add -A && git commit -m "Realisasi <bulan> <tahun>" && git push`.

**Jalur Excel** — cocok bila belum ingin menyentuh kode:

1. Buka `dist/Dashboard_Susut_ULP_Samboja_2026.xlsx`.
2. Sheet **NERACA ENERGI** — isi kWh salur & jual, ubah status menjadi REALISASI.
3. Sheet **INPUT REALISASI** — isi realisasi tiap item pada kolom bulan
   bersangkutan. Hanya sel kuning yang boleh diketik.
4. Sheet WORK PLAN, DASHBOARD, dan SIMULASI TARGET berubah dengan sendirinya.

**Jalur basis data** — cocok bila Supabase sudah terpasang: masukkan lewat
fungsi `public.susut_input_realisasi()` atau langsung ke tabel
`susut.program_periode` dan `susut.neraca_energi`.

### Langkah 3 — baca dan putuskan (hari kerja ke-7)

1. **Halaman Ringkasan** — apakah deviasi kumulatif melebar atau menyempit?
2. **Halaman Work Plan** — item mana yang berpindah status menjadi KRITIS?
   Faktor kejar mana yang naik dua bulan berturut-turut?
3. **Halaman Simulasi Target** — perbarui asumsi beban, baca ulang gap.
4. **Halaman Rencana Aksi** — perbarui progres, tetapkan aksi minggu berjalan.

### Langkah 4 — laporkan

Sheet **DASHBOARD** pada berkas Excel sudah disiapkan siap cetak (A4 lanskap,
muat satu halaman lebar) untuk lampiran laporan ke UP3.

---

## 5. Mengubah target atau parameter

| Yang diubah | Tempatnya |
|---|---|
| Target susut akhir tahun | `PARAM["target_susut_akhir_tahun"]` di `scripts/dataset.py`, atau tabel `susut.parameter` |
| Tarif rata-rata | `PARAM["tarif_rata_rata"]` |
| Ambang status capaian | `PARAM["ambang_tercapai"]`, `ambang_waspada`, `ambang_terlambat` |
| Target bulanan tiap item | Kolom ketiga `_PROGRAM_INPUT`, atau tabel `susut.program_periode` |
| Faktor kWh selamat per satuan | Kolom `kwh_selamat_per_unit` pada `_PROGRAM_INPUT` / `susut.program` |
| Menambah item work plan baru | Tambahkan satu baris pada `_PROGRAM_INPUT`, jalankan `build_all.py` |

Setelah mengubah apa pun di `scripts/dataset.py`, jalankan
`python3 scripts/build_all.py` supaya Excel, seed Supabase, dokumen work plan,
dan data cadangan situs web ikut terhitung ulang bersamaan.
