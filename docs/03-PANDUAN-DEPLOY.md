# Panduan Pemasangan: Supabase + GitHub + Vercel

Tiga bagian yang saling terhubung:

```
   GitHub  ──push──▶  Vercel  ──baca──▶  Supabase
  (kode &            (situs web)        (basis data
   riwayat)                              + hak akses)
```

- **GitHub** menyimpan kode, migrasi basis data, dan riwayat perubahan.
- **Vercel** membangun dan menerbitkan situs setiap kali ada `push`.
- **Supabase** menyimpan data susut dan mengatur siapa boleh membaca/menulis.

Dashboard **sengaja dirancang agar tetap berjalan tanpa Supabase**. Bila
variabel lingkungan belum diisi, situs memakai data contoh bawaan dan menandai
dirinya "Data contoh" di pojok kanan atas. Jadi Anda bisa menerbitkan situsnya
lebih dulu, lalu menyambungkan basis data belakangan.

---

## Bagian 1 — Supabase

### 1.1 Membuat proyek

1. Buka [supabase.com](https://supabase.com) → **New project**.
2. Isi: `Name` = `susut-ulp-samboja`, `Database Password` (simpan baik-baik),
   `Region` = **Southeast Asia (Singapore)** — paling dekat dengan Kalimantan.
3. Tunggu sekitar dua menit sampai proyek siap.

### 1.2 Menjalankan migrasi

Empat berkas di `supabase/migrations/` dijalankan **berurutan**. Ada dua cara.

**Cara A — lewat SQL Editor (paling sederhana, tanpa pemasangan apa pun)**

Buka **SQL Editor** di dashboard Supabase, lalu tempel dan jalankan isi tiap
berkas satu per satu dengan urutan ini:

| Urutan | Berkas | Isi |
|---|---|---|
| 1 | `20260901000000_schema.sql` | 12 tabel, tipe enum, indeks, pemicu audit |
| 2 | `20260901000001_views.sql` | 10 view perhitungan KPI |
| 3 | `20260901000002_rls_dan_api.sql` | Row Level Security, peran, view publik |
| 4 | `20260901000003_seed.sql` | data contoh (lewati bila langsung memakai data riil) |

**Cara B — lewat Supabase CLI**

```bash
npm install -g supabase
supabase login
supabase link --project-ref <ref-proyek-anda>
supabase db push
```

### 1.3 Memastikan berhasil

Jalankan di SQL Editor:

```sql
select susut_ytd_persen, capaian_rata_rata, verdict_target
from susut.v_kpi_ringkas;
```

Harus keluar satu baris berisi ringkasan KPI. Bila kosong, migrasi seed belum
dijalankan.

### 1.4 Mengambil kunci

**Project Settings → Data API**, salin dua nilai:

| Nilai | Dipakai sebagai |
|---|---|
| Project URL | `NEXT_PUBLIC_SUPABASE_URL` |
| `anon` / publishable key | `NEXT_PUBLIC_SUPABASE_ANON_KEY` |

> **Jangan pernah** memakai `service_role` key di situs web atau di variabel
> berawalan `NEXT_PUBLIC_`. Kunci itu melewati seluruh Row Level Security dan
> setara akses penuh ke basis data.

### 1.5 Model keamanan

Migrasi ketiga memasang Row Level Security pada seluruh tabel:

| Peran | Boleh membaca | Boleh menulis |
|---|---|---|
| `anon` (pengunjung tanpa login) | seluruh data agregat | tidak sama sekali |
| `PENGAMAT` | seluruh data agregat | tidak sama sekali |
| `PELAKSANA` | seluruh data agregat | realisasi, P2TL, rencana aksi |
| `SUPERVISOR` | seluruh data agregat | realisasi, P2TL, rencana aksi |
| `MANAJER` / `ADMIN` | semuanya termasuk log audit | semuanya termasuk data master |

Tabel di sini hanya memuat **angka agregat** — tidak ada nama, alamat, atau ID
pelanggan — sehingga akses baca publik aman. **Bila nantinya Anda menambahkan
data per pelanggan (misalnya daftar temuan P2TL beserta IDPEL), akses baca
publik harus dicabut lebih dulu.** Caranya: pada
`20260901000002_rls_dan_api.sql` bagian D, ganti `to anon, authenticated`
menjadi `to authenticated`, lalu jalankan ulang berkas itu.

Model ini punya dua lapis yang harus benar bersamaan:

1. **Hak akses tabel** — menentukan apakah sebuah peran boleh menulis sama
   sekali. `anon` hanya diberi `select`; `authenticated` juga diberi
   `insert`/`update`/`delete`.
2. **Row Level Security** — menentukan siapa di antara pengguna yang sudah
   login yang benar-benar boleh menulis, berdasarkan kolom `peran` pada
   `susut.profil`.

Kalau lapisan pertama lupa diberikan, seluruh kebijakan RLS tidak akan pernah
dievaluasi dan pengisian realisasi bulanan menjadi mustahil — PostgreSQL
menolak lebih dulu. Karena itu perilakunya diuji otomatis:

```bash
bash scripts/uji_rls.sh                        # PostgreSQL sementara
PGURL=postgres://... bash scripts/uji_rls.sh   # basis data yang sudah ada
```

Uji ini membuktikan pengunjung tanpa login hanya bisa membaca, PENGAMAT tidak
bisa menulis apa pun, PELAKSANA bisa mengisi realisasi tetapi tidak bisa
menyentuh data master, PELAKSANA tidak bisa menaikkan perannya sendiri, ADMIN
bisa mengelola data master, dan log audit tidak terbaca di bawah peran MANAJER.
Ia juga berjalan otomatis di CI setiap kali ada perubahan.

Setelah proyek Supabase disiapkan, jalankan sekali terhadap basis data
sungguhan memakai `PGURL` — tiruan lokal tidak sama persis dengan Supabase.

Menaikkan peran seseorang setelah ia mendaftar:

```sql
update susut.profil set peran = 'SUPERVISOR'
where email = 'nama@pln.co.id';
```

---

## Bagian 2 — GitHub

### 2.1 Repositori

Repositori ini sudah berisi seluruh berkas yang diperlukan. Bila memulai dari
nol:

```bash
git init
git add .
git commit -m "Dashboard monitoring susut ULP Samboja"
git branch -M main
git remote add origin https://github.com/<akun>/<repo>.git
git push -u origin main
```

### 2.2 Pemeriksaan otomatis

`.github/workflows/ci.yml` berjalan pada setiap `push` dan:

1. membangun ulang data, seed SQL, dokumen work plan, dan dashboard Excel;
2. **menolak** bila hasil generate berbeda dari yang di-commit — ini mencegah
   dashboard web dan Excel menampilkan angka yang berlainan;
3. membangun aplikasi web;
4. mengunggah dashboard Excel sebagai artefak yang bisa diunduh dari tab
   *Actions*.

### 2.3 Alur kerja bulanan

```bash
git pull
# sunting data bulan berjalan pada scripts/dataset.py
python3 scripts/build_all.py
git add -A
git commit -m "Realisasi susut September 2026"
git push
```

Vercel menerbitkan ulang situsnya secara otomatis dalam satu-dua menit.

---

## Bagian 3 — Vercel

### 3.1 Menghubungkan repositori

1. Buka [vercel.com](https://vercel.com) → **Add New → Project**.
2. Pilih repositori GitHub ini. Vercel mengenali Next.js dengan sendirinya —
   `Framework Preset`, `Build Command`, dan `Output Directory` tidak perlu
   diubah.
3. **Environment Variables** — tambahkan dua variabel dari langkah 1.4,
   centang ketiga lingkungan (Production, Preview, Development):

   | Name | Value |
   |---|---|
   | `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxx.supabase.co` |
   | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOi...` |

4. **Deploy**.

`vercel.json` sudah menetapkan wilayah `sin1` (Singapura) dan beberapa header
keamanan dasar.

### 3.2 Memastikan berhasil

Buka situsnya. Di pojok kanan atas ada penanda:

- **● Supabase** (hijau) — angka dibaca langsung dari basis data.
- **● Data contoh** (kuning) — Supabase belum tersambung. Periksa kembali
  ejaan variabel lingkungan, lalu **Redeploy**.

Menambahkan variabel lingkungan **tidak** otomatis membangun ulang situs.
Setelah menambahkannya, buka **Deployments → ⋯ → Redeploy**.

### 3.3 Nama domain

**Project Settings → Domains.** Vercel memberi `<nama>.vercel.app` secara
cuma-cuma. Untuk domain milik PLN, tambahkan domainnya lalu ikuti petunjuk
DNS yang ditampilkan.

---

## Pemecahan masalah

| Gejala | Sebab yang paling sering | Penanganan |
|---|---|---|
| Situs menampilkan "Data contoh" padahal Supabase sudah diisi | Variabel ditambahkan setelah deploy | Redeploy dari dashboard Vercel |
| `relation "susut_kpi_ringkas" does not exist` | Migrasi ketiga belum dijalankan | Jalankan `20260901000002_rls_dan_api.sql` |
| View kosong padahal tabel berisi | RLS memblokir peran `anon` | Periksa kebijakan `baca_publik` pada bagian D migrasi ketiga |
| Angka web berbeda dari Excel | Supabase dan berkas contoh tidak sinkron | Jalankan ulang `20260901000003_seed.sql`, atau `python3 scripts/build_all.py` |
| CI gagal di langkah "tidak sinkron" | Lupa menjalankan `build_all.py` sebelum commit | Jalankan, lalu commit ulang |
| Build Vercel gagal `Module not found` | `package-lock.json` tidak ikut ter-commit | `git add package-lock.json` |

---

## Memasukkan realisasi tanpa menyentuh kode

Setelah pengguna mendaftar dan diberi peran `PELAKSANA` ke atas, realisasi
bulanan bisa dimasukkan lewat fungsi RPC:

```sql
select public.susut_input_realisasi(
  p_program_kode := 'N-09',
  p_tahun        := 2026,
  p_bulan        := 9,
  p_realisasi    := 42,
  p_catatan      := 'Sensus PJU Kelurahan Sungai Merdeka'
);
```

Fungsi ini mengembalikan baris capaian program yang sudah diperbarui, sehingga
bisa langsung dipakai memperbarui tampilan. Seluruh perubahan pada
`neraca_energi`, `program_periode`, dan `action_plan` tercatat di
`susut.audit_log` beserta siapa yang mengubah dan kapan.
