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
pip install openpyxl xlsxwriter

# 2. Bangun seluruh keluaran dari sumber data
python3 scripts/build_all.py

# 3. Jalankan dashboard web
npm run dev          # http://localhost:3000
```

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
├── scripts/
│   ├── dataset.py        SUMBER DATA TUNGGAL — sunting di sini
│   ├── build_sql.py      → seed Supabase
│   ├── build_excel.py    → dashboard Excel
│   ├── build_docs.py     → dokumen work plan
│   └── build_all.py      Menjalankan semuanya berurutan
├── supabase/migrations/  Skema, view, RLS, dan seed
├── docs/                 Analisis dan panduan
├── data/                 Dataset hasil generate (JSON)
└── dist/                 Dashboard Excel hasil generate
```

**Prinsip yang dipegang:** seluruh angka berasal dari `scripts/dataset.py`.
Excel, Supabase, dan situs web tidak pernah menghitung sendiri-sendiri, sehingga
tidak mungkin saling berbeda. Alur kerja bulanannya: sunting data → jalankan
`build_all.py` → commit → Vercel menerbitkan ulang.

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

---

## Teknologi

Next.js 15 · React 19 · TypeScript · Tailwind CSS · Recharts · Supabase
(PostgreSQL 15+) · Python 3.11 dengan XlsxWriter · Vercel
