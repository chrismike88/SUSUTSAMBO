# -*- coding: utf-8 -*-
"""
Membangkitkan docs/02-WORK-PLAN.md dari data/dataset.json.

Dokumen ini sengaja dibangkitkan, bukan diketik manual, agar tabel capaian
per item tidak pernah berbeda dari dashboard Excel maupun situs web.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
D = json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "02-WORK-PLAN.md"

META, KPI, PARAM = D["meta"], D["kpi"], D["meta"]["parameter"]


def n(v, d=0) -> str:
    """Format angka gaya Indonesia: pemisah ribuan titik, desimal koma."""
    s = f"{v:,.{d}f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def main() -> None:
    L: list[str] = []
    a = L.append
    bulan_sisa = KPI["bulan_tersisa"]

    a("# Work Plan Penurunan Susut & Capaian per Item")
    a("")
    a(f"> Dibangkitkan otomatis oleh `scripts/build_docs.py` dari `data/dataset.json`.")
    a("> Jangan disunting langsung — sunting datanya lalu jalankan"
      " `python3 scripts/build_all.py`.")
    a(">")
    a("> **Angka di bawah adalah data contoh**, bukan realisasi ULP Samboja"
      " yang sebenarnya.")
    a("")
    a(f"**Periode data:** {KPI['periode_data']}  ·  "
      f"**Bulan tersisa:** {bulan_sisa}  ·  "
      f"**Capaian rata-rata:** {n(KPI['capaian_program_rata_rata'], 2)}%")
    a("")

    # --- Ringkasan status ---
    a("## Ringkasan status")
    a("")
    a("| Status | Ambang | Jumlah item | Arti |")
    a("|---|---|---:|---|")
    for nama, ambang, jml, arti in [
        ("TERCAPAI", "≥ 100%", KPI["jumlah_tercapai"],
         "Sudah melampaui target sampai bulan berjalan"),
        ("WASPADA", "90–99%", KPI["jumlah_waspada"],
         "Sedikit tertinggal, masih terkejar dengan ritme sekarang"),
        ("TERLAMBAT", "75–89%", KPI["jumlah_terlambat"],
         "Butuh percepatan terukur"),
        ("KRITIS", "< 75%", KPI["jumlah_kritis"],
         "Wajib dibahas di rapat mingguan unit"),
    ]:
        a(f"| **{nama}** | {ambang} | {jml} | {arti} |")
    a("")

    # --- Rekap kategori ---
    a("## Rekap per kategori")
    a("")
    a("| Kategori | Item | Target kWh setahun | Terealisasi | Sisa | Capaian |")
    a("|---|---:|---:|---:|---:|---:|")
    for nama, kunci, kat in [("Teknis", "kontribusi_teknis", "TEKNIS"),
                             ("Non-teknis", "kontribusi_nonteknis", "NON_TEKNIS")]:
        k = KPI[kunci]
        jml = len([p for p in D["program"] if p["kategori"] == kat])
        a(f"| {nama} | {jml} | {n(k['kwh_target_tahun'])} | {n(k['kwh_ytd'])} | "
          f"{n(k['kwh_sisa'])} | {n(k['capaian_persen'], 2)}% |")
    a(f"| **Total** | **{KPI['jumlah_program']}** | "
      f"**{n(KPI['kwh_selamat_target_tahun'])}** | "
      f"**{n(KPI['kwh_selamat_ytd'])}** | **{n(KPI['kwh_selamat_sisa'])}** | "
      f"**{n(KPI['capaian_program_rata_rata'], 2)}%** |")
    a("")

    # --- Tabel per item ---
    for kat, judul in [("TEKNIS", "Program teknis"), ("NON_TEKNIS", "Program non-teknis")]:
        a(f"## {judul}")
        a("")
        a("| Kode | Item work plan | Satuan | Target tahun | Target s/d bln | "
          "Realisasi | Capaian | Sisa target | Kebutuhan/bln | Faktor kejar | "
          "Sisa potensi kWh | Status | PIC |")
        a("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|")
        for p in sorted((x for x in D["program"] if x["kategori"] == kat),
                        key=lambda x: x["capaian_ytd_persen"]):
            sisa_kwh = round(p["sisa_target"] * p["kwh_selamat_per_unit"])
            fk = f"{n(p['faktor_kejar'], 2)}×" if p["faktor_kejar"] else "–"
            a(f"| {p['kode']} | {p['nama']} | {p['satuan']} | "
              f"{n(p['target_tahun'], 1)} | {n(p['target_ytd'], 1)} | "
              f"{n(p['realisasi_ytd'], 1)} | {n(p['capaian_ytd_persen'], 1)}% | "
              f"{n(p['sisa_target'], 1)} | {n(p['kebutuhan_per_bulan_sisa'], 1)} | "
              f"{fk} | {n(sisa_kwh) if sisa_kwh else '–'} | {p['status']} | "
              f"{p['pic'].replace('Supervisor ', 'SPV ')} |")
        a("")

    # --- Faktor konversi ---
    a("## Faktor konversi kWh diselamatkan")
    a("")
    a("Faktor ini mengubah volume pekerjaan menjadi perkiraan energi yang tidak"
      " jadi hilang. Nilainya **estimasi rekayasa** dan sebaiknya dikalibrasi"
      " dengan pengukuran sebelum–sesudah pada beberapa lokasi contoh.")
    a("")
    a("| Kode | Satuan | kWh diselamatkan per satuan | Siklus |")
    a("|---|---|---:|---|")
    for p in D["program"]:
        f = n(p["kwh_selamat_per_unit"], 0) if p["kwh_selamat_per_unit"] >= 1 else "–"
        a(f"| {p['kode']} | {p['satuan']} | {f} | {p['siklus']} |")
    a("")
    a("Item dengan tanda `–` diukur secara finansial atau sebagai aktivitas;"
      " energinya sudah dihitung pada item lain agar tidak terhitung dua kali"
      " (misalnya N-01 dihitung energinya lewat N-02).")
    a("")

    # --- Gap ---
    A, B = KPI["skenario_a_kumulatif"], KPI["skenario_b_exit_rate"]
    a("## Gap menuju target akhir tahun")
    a("")
    a("| | Skenario A — susut kumulatif | Skenario B — susut Desember |")
    a("|---|---:|---:|")
    a(f"| Gap kWh | {n(A['gap_kwh_harus_diselamatkan'])} | "
      f"{n(B['gap_kwh_harus_diselamatkan'])} |")
    a(f"| Per bulan ({bulan_sisa} bulan) | {n(A['gap_kwh_per_bulan'])} | "
      f"{n(B['gap_kwh_per_bulan'])} |")
    a(f"| Nilai finansial | Rp {n(A['gap_rupiah'])} | Rp {n(B['gap_rupiah'])} |")
    a(f"| Sisa potensi work plan | {n(KPI['kwh_selamat_sisa'])} | "
      f"{n(KPI['kwh_selamat_sisa'])} |")
    rasio_a = KPI["kwh_selamat_sisa"] / A["gap_kwh_harus_diselamatkan"]
    rasio_b = KPI["kwh_selamat_sisa"] / B["gap_kwh_harus_diselamatkan"]
    a(f"| **Rasio kecukupan** | **{n(rasio_a, 2)}×** | **{n(rasio_b, 2)}×** |")
    a("")
    a(f"Pada kedua tafsir, sisa potensi work plan masih melampaui gap. "
      f"Namun pada skenario A marginnya hanya {n(rasio_a, 2)}× — target akan lepas "
      f"bila eksekusi turun di bawah sekitar {n(100 / rasio_a, 0)}% dari sisa target. "
      f"Gunakan halaman **Simulasi Target** untuk mengujinya.")
    a("")

    OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"[OK] dokumen work plan -> {OUT.relative_to(ROOT)} ({len(L)} baris)")


if __name__ == "__main__":
    main()
