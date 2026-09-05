# -*- coding: utf-8 -*-
"""
Membangun ulang SELURUH keluaran dari satu sumber data.

Urutan:
  0. scripts/validate_master.py                     (periksa data/master/*.csv)
  1. scripts/dataset.py     -> data/*.json          (sumber data tunggal)
  2. scripts/build_sql.py   -> supabase/migrations/ (seed basis data)
  3. scripts/build_excel.py -> dist/*.xlsx          (dashboard Excel)
     scripts/build_docs.py  -> docs/02-WORK-PLAN.md (tabel capaian per item)
  4. salin dataset          -> lib/fallback/        (data cadangan dashboard web)

Jalankan setiap kali data bulanan diperbarui:  python3 scripts/build_all.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def jalankan(skrip: str) -> None:
    print(f"\n▶ {skrip}")
    hasil = subprocess.run([sys.executable, str(ROOT / "scripts" / skrip)],
                           cwd=ROOT, text=True)
    if hasil.returncode != 0:
        sys.exit(f"✗ gagal menjalankan {skrip}")


def main() -> None:
    jalankan("validate_master.py")
    jalankan("dataset.py")
    jalankan("build_sql.py")
    jalankan("build_excel.py")
    jalankan("build_docs.py")

    asal = ROOT / "data" / "dataset.json"
    tujuan = ROOT / "lib" / "fallback" / "dataset.json"
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(asal, tujuan)
    print(f"\n▶ salin data cadangan web\n[OK] {asal.name} -> {tujuan.relative_to(ROOT)}")

    print("\n✓ Selesai. Langkah berikutnya:")
    print("  · Excel   : buka dist/Dashboard_Susut_ULP_Samboja_2026.xlsx")
    print("  · Supabase: jalankan supabase/migrations/*.sql (atau `supabase db push`)")
    print("  · Web     : npm run build && npm start  (atau push ke GitHub -> Vercel)")


if __name__ == "__main__":
    main()
