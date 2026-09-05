# Monitoring Susut — ULP Samboja

Sistem pemantauan penurunan **susut teknis** dan **susut non-teknis** untuk
ULP Samboja (UP3 Balikpapan, UID Kalimantan Timur & Kalimantan Utara), terdiri
atas tiga keluaran yang dibangun dari **satu sumber data yang sama**:

| Keluaran | Berkas | Untuk siapa |
|---|---|---|
| **Dashboard web** | Next.js → Vercel + Supabase | Manajemen unit & UP3, dibuka dari mana saja |
| **Dashboard Excel** | `dist/Dashboard_Susut_ULP_Samboja_2026.xlsx` | Kerja harian, input realisasi, lampiran laporan |
| **Analisis tertulis** | `docs/` | Bahan rapat dan pengambilan keputusan |

> **Angka bawaan adalah data contoh**, bukan realisasi ULP Samboja yang
> sebenarnya. Ia disusun agar realistis dan konsisten secara matematis supaya
> seluruh dashboard bisa dibangun dan diuji. Ganti dengan data riil dari AP2T,
> XPower/EIS-Susut, Aplikasi P2TL, dan SCADA/AMR, lalu jalankan
> `python3 scripts/build_all.py`.

---

## Mulai cepat

```bash
# 1. Pasang dependensi
npm install
pip install -r requirements.txt

# 2. Isi data di data/master/*.csv  (bisa dibuka dengan Excel)
python3 scripts/validate_master.py   # periksa konsistensinya

# 3. Bangun seluruh keluaran dari data itu
python3 scripts/build_all.py

# 4. Jalankan dashboard web
npm run dev          # http://localhost:3000
```

Seluruh angka masukan ada di **`data/master/`** sebagai berkas CSV biasa —
delapan berkas, semuanya bisa disunting di Excel tanpa menyentuh kode. Panduan
kolom per kolom ada di [`data/master/README.md`](data/master/README.md).

> **Sebelum data bulanan mulai diisi**, ganti data contoh dengan kondisi riil
> unit. Tersedia kerangka kosong agar nama penyulang rekaan tidak terbawa ke
> produksi:
> ```bash
> python3 scripts/siapkan_template.py          # buat kerangka kosong
> python3 scripts/siapkan_template.py --pakai  # pasang setelah diisi
> ```

Situs berjalan **tanpa perlu Supabase** — ia memakai data contoh bawaan dan
menandai dirinya "Data contoh". Untuk menyambungkannya ke basis data, ikuti
[`docs/03-PANDUAN-DEPLOY.md`](docs/03-PANDUAN-DEPLOY.md).

---

## Isi dashboard web

| Halaman | Isi |
|---|---|
| **Ringkasan** | Delapan kartu KPI, tren susut vs target, komposisi teknis/non-teknis, sepuluh item dengan sisa potensi terbesar, penyulang prioritas, aksi mendesak |
| **Work Plan** | Capaian 22 item terhadap target bulanan dan target akhir tahun, dengan penyaring dan kolom faktor kejar |
| **Susut Teknis** | Dekomposisi rugi per komponen jaringan, peringkat & profil sepuluh penyulang, ambang batas acuan operasi |
| **Susut Non-Teknis** | Rekap P2TL, hit rate, efektivitas penagihan, temuan per golongan pelanggaran |
| **Rencana Aksi** | Dua belas aksi berprioritas beserta akar masalah, dampak kWh, PIC, dan progres |
| **Simulasi Target** | Kalkulator *what-if* dua tafsir target akhir tahun |

Mendukung tema terang dan gelap, dapat dibuka dari ponsel, dan setiap grafik
punya pasangan tabel sehingga tidak ada angka yang hanya terbaca lewat warna.

## Isi dashboard Excel

Sepuluh sheet, dengan **satu sheet input** yang menghidupkan seluruh formula:

`DASHBOARD` · `NERACA ENERGI` · `INPUT REALISASI` · `WORK PLAN` ·
`ANALISIS TEKNIS` · `P2TL` · `RENCANA AKSI` · `SIMULASI TARGET` ·
`DATA GRAFIK` · `PANDUAN`

Ketik realisasi di sheet **INPUT REALISASI**, dan capaian, status, warna, serta
seluruh grafik ikut berubah dengan sendirinya.

---

## Susunan berkas

```
├── app/                  Halaman dashboard web (Next.js App Router)
├── components/           Komponen UI dan grafik
├── lib/
│   ├── data.ts           Pembaca data: Supabase, cadangan ke berkas contoh
│   ├── supabase.ts       Klien Supabase
│   ├── format.ts         Pemformatan angka gaya Indonesia
│   └── fallback/         Salinan dataset untuk situs
├── data/master/          SUMBER DATA — 8 berkas CSV, sunting di sini
│   ├── unit.csv          identitas unit
│   ├── parameter.csv     tarif, target susut, ambang status
│   ├── penyulang.csv     master penyulang + profil kondisi
│   ├── neraca.csv        kWh salur & jual per bulan
│   ├── program.csv       katalog item work plan
│   ├── program_bulanan.csv  target & realisasi per item per bulan
│   ├── susut_penyulang.csv  susut per penyulang per bulan
│   └── action_plan.csv   rencana aksi
├── scripts/
│   ├── dataset.py        Membaca CSV master, menghitung angka turunan
│   ├── validate_master.py  Pemeriksa konsistensi data master
│   ├── siapkan_template.py Kerangka kosong untuk data riil
│   ├── build_sql.py      → seed Supabase
│   ├── build_excel.py    → dashboard Excel
│   ├── build_docs.py     → dokumen work plan
│   └── build_all.py      Menjalankan semuanya berurutan
├── supabase/migrations/  Skema, view, RLS, dan seed
├── docs/                 Analisis dan panduan
├── data/*.json           Dataset hasil generate
└── dist/                 Dashboard Excel hasil generate
```

**Prinsip yang dipegang:** seluruh angka berasal dari `data/master/*.csv`.
Excel, Supabase, dan situs web tidak pernah menghitung sendiri-sendiri, sehingga
tidak mungkin saling berbeda. Perhitungannya juga sepenuhnya deterministik —
membangun ulang dari data yang sama selalu menghasilkan berkas yang sama.

Alur kerja bulanannya: isi CSV → `validate_master.py` → `build_all.py` →
commit → Vercel menerbitkan ulang.

Pemeriksaan otomatis di GitHub Actions akan **menolak** commit yang berkas hasil
generate-nya tidak sinkron dengan sumbernya.

---

## Dokumentasi

| Berkas | Isi |
|---|---|
| [`docs/01-ANALISIS-SUSUT.md`](docs/01-ANALISIS-SUSUT.md) | Analisis mendalam: pembedahan susut teknis & non-teknis, konsentrasi susut per penyulang, analisis gap dua skenario, dan urutan tindakan |
| [`docs/02-WORK-PLAN.md`](docs/02-WORK-PLAN.md) | Tabel capaian 22 item (dibangkitkan otomatis) |
| [`docs/03-PANDUAN-DEPLOY.md`](docs/03-PANDUAN-DEPLOY.md) | Pemasangan Supabase + GitHub + Vercel, model keamanan, pemecahan masalah |
| [`docs/04-KAMUS-DATA.md`](docs/04-KAMUS-DATA.md) | Kamus istilah, tabel & view, rumus, prosedur bulanan |
| [`data/master/README.md`](data/master/README.md) | Panduan pengisian tiap kolom berkas master |

---

## Teknologi

Next.js 15 · React 19 · TypeScript · Tailwind CSS · Recharts · Supabase
(PostgreSQL 15+) · Python 3.11 dengan XlsxWriter · Vercel
