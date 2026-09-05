# -*- coding: utf-8 -*-
"""
Menyiapkan kerangka kosong berkas master di data/master/template/.

Gunanya: memisahkan dengan tegas antara DATA CONTOH (yang dipakai membangun dan
mendemokan dashboard) dan DATA RIIL ULP Samboja, supaya nama penyulang rekaan
tidak pernah diam-diam terbawa ke produksi.

    python3 scripts/siapkan_template.py          # buat/segarkan kerangka kosong
    python3 scripts/siapkan_template.py --pakai  # salin kerangka menjadi data master

Kerangka mempertahankan dua hal yang memang layak dijadikan titik mulai:
  * daftar kunci parameter (tinggal diisi nilainya)
  * katalog 22 item work plan penurunan susut, yang sebagian besar sama di
    seluruh ULP — silakan tambah, hapus, atau ubah sesuai work plan unit

Baris bulanan pada program_bulanan.csv dibangkitkan otomatis mengikuti isi
program.csv, sehingga tidak perlu mengetik 12 baris per item secara manual.
"""
from __future__ import annotations

import csv
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / "data" / "master"
TEMPLATE = MASTER / "template"

BERKAS = [
    "unit.csv", "parameter.csv", "penyulang.csv", "neraca.csv",
    "program.csv", "program_bulanan.csv", "susut_penyulang.csv", "action_plan.csv",
]


def baca(nama: str) -> tuple[list[str], list[dict[str, str]]]:
    with (MASTER / nama).open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), list(r)


def tulis(nama: str, header: list[str], baris: list[list]) -> None:
    with (TEMPLATE / nama).open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(baris)
    print(f"  {nama:24} {len(baris):>4} baris")


def buat_template() -> None:
    TEMPLATE.mkdir(parents=True, exist_ok=True)
    print(f"Menyiapkan kerangka di {TEMPLATE.relative_to(ROOT)}/\n")

    # unit.csv — satu baris kosong siap diisi
    h, _ = baca("unit.csv")
    tulis("unit.csv", h, [["ULP-SBJ", "ULP Samboja", "UP3 Balikpapan",
                           "UID Kalimantan Timur & Kalimantan Utara",
                           "Manager Layanan ULP Samboja", 2026]])

    # parameter.csv — kunci dipertahankan, nilai dikosongkan
    h, baris = baca("parameter.csv")
    tulis("parameter.csv", h,
          [[b["kunci"], "", b.get("satuan", ""), b.get("keterangan", "")] for b in baris])

    # penyulang.csv — hanya satu baris contoh berlabel jelas
    h, _ = baca("penyulang.csv")
    tulis("penyulang.csv", h,
          [["GANTI-01", "Nama penyulang", "", "", "", "", "", "", "", "", "", ""]])

    # neraca.csv — dua belas bulan kosong, status bawaan PROYEKSI
    h, _ = baca("neraca.csv")
    tulis("neraca.csv", h, [[m, "PROYEKSI", "", "", "", ""] for m in range(1, 13)])

    # program.csv — katalog dipertahankan sebagai titik mulai, target dikosongkan
    h, baris = baca("program.csv")
    tulis("program.csv", h,
          [[b["kode"], b["nama"], b["kategori"], b["sub_kategori"], b["satuan"],
            b["siklus"], b["pic"], b["kwh_selamat_per_unit"], ""] for b in baris])

    # program_bulanan.csv — kerangka 12 bulan per item, dibangkitkan dari katalog
    tulis("program_bulanan.csv",
          ["program_kode", "bulan", "target_volume", "realisasi_volume"],
          [[b["kode"], m, "", ""] for b in baris for m in range(1, 13)])

    # susut_penyulang.csv — hanya header
    tulis("susut_penyulang.csv", ["penyulang_kode", "bulan", "susut_persen"], [])

    # action_plan.csv — hanya header
    h, _ = baca("action_plan.csv")
    tulis("action_plan.csv", h, [])

    print(f"\n✓ Kerangka siap. Isi berkas di {TEMPLATE.relative_to(ROOT)}/ "
          "dengan data riil, lalu jalankan:")
    print("    python3 scripts/siapkan_template.py --pakai")


def pakai_template() -> None:
    kurang = [n for n in BERKAS if not (TEMPLATE / n).exists()]
    if kurang:
        sys.exit(f"✗ Kerangka belum lengkap, kurang: {', '.join(kurang)}\n"
                 "  Jalankan dulu: python3 scripts/siapkan_template.py")

    cadangan = MASTER.parent / "master_contoh_cadangan"
    if cadangan.exists():
        shutil.rmtree(cadangan)
    cadangan.mkdir(parents=True)
    for n in BERKAS:
        shutil.copyfile(MASTER / n, cadangan / n)
    print(f"Data contoh dicadangkan ke {cadangan.relative_to(ROOT)}/")

    for n in BERKAS:
        shutil.copyfile(TEMPLATE / n, MASTER / n)
        print(f"  {n}")

    print("\n✓ Data master kini memakai isi kerangka. Langkah berikutnya:")
    print("    python3 scripts/validate_master.py")
    print("    python3 scripts/build_all.py")
    print("\n  Pemeriksa akan menyebutkan kolom mana saja yang masih kosong.")


if __name__ == "__main__":
    if "--pakai" in sys.argv:
        pakai_template()
    else:
        buat_template()
