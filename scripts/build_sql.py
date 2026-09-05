# -*- coding: utf-8 -*-
"""
Membangkitkan migrasi seed Supabase dari data/dataset.json.
Output: supabase/migrations/20260901000003_seed.sql
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8"))
OUT = ROOT / "supabase" / "migrations" / "20260901000003_seed.sql"

META, PARAM, UNIT = DATA["meta"], DATA["meta"]["parameter"], DATA["meta"]["unit"]


def q(v) -> str:
    """Escape nilai ke literal SQL."""
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def rows(values: list[str], per_line: int = 1) -> str:
    return ",\n  ".join(values)


def main() -> None:
    L: list[str] = []
    add = L.append

    add("-- " + "=" * 74)
    add("--  MONITORING SUSUT ULP SAMBOJA — DATA AWAL (SEED)")
    add("--  Migrasi 004 : dibangkitkan otomatis oleh scripts/build_sql.py")
    add("--")
    add("--  PERINGATAN: isi berkas ini adalah DATA CONTOH untuk membangun dashboard.")
    add("--  Ganti dengan data riil dari AP2T / XPower / Aplikasi P2TL / SCADA-AMR,")
    add("--  lalu jalankan ulang `python3 scripts/build_all.py`.")
    add("-- " + "=" * 74)
    add("")
    add("begin;")
    add("")

    # ---- Bersihkan data lama (idempoten) -----------------------------------
    add("-- Bersihkan data lama agar seed dapat dijalankan berulang")
    add("truncate table susut.rugi_teknis, susut.susut_penyulang, susut.p2tl,")
    add("               susut.action_plan, susut.program_periode restart identity cascade;")
    add("delete from susut.program;")
    add("delete from susut.neraca_energi;")
    add("delete from susut.penyulang;")
    add("delete from susut.parameter;")
    add("delete from susut.unit;")
    add("")

    # ---- UNIT --------------------------------------------------------------
    add("-- 1. UNIT")
    add("insert into susut.unit (kode, nama, up3, uid, jumlah_pelanggan, jumlah_gardu,")
    add("                        jumlah_penyulang, panjang_jtm_kms, panjang_jtr_kms) values")
    add(f"  ({q(UNIT['kode'])}, {q(UNIT['nama'])}, {q(UNIT['up3'])}, {q(UNIT['uid'])},")
    add(f"   {PARAM['jumlah_pelanggan']}, {PARAM['jumlah_gardu']}, {PARAM['jumlah_penyulang']},")
    add(f"   {PARAM['panjang_jtm_kms']}, {PARAM['panjang_jtr_kms']});")
    add("")

    # ---- PARAMETER ---------------------------------------------------------
    ket = {
        "tarif_rata_rata": ("Rp/kWh", "Harga jual rata-rata untuk konversi kWh ke Rupiah"),
        "target_susut_akhir_tahun": ("%", "Target susut jaringan distribusi akhir tahun (RKAP)"),
        "baseline_susut_2025": ("%", "Realisasi susut tahun sebelumnya"),
        "floor_susut_teknis": ("%", "Batas bawah susut teknis yang realistis pada jaringan eksisting"),
        "ambang_tercapai": ("%", "Ambang status TERCAPAI"),
        "ambang_waspada": ("%", "Ambang status WASPADA"),
        "ambang_terlambat": ("%", "Ambang status TERLAMBAT"),
        "jumlah_pelanggan": ("pelanggan", "Jumlah pelanggan terpasang"),
        "jumlah_gardu": ("unit", "Jumlah gardu distribusi"),
        "jumlah_penyulang": ("unit", "Jumlah penyulang 20 kV"),
        "panjang_jtm_kms": ("kms", "Panjang jaringan tegangan menengah"),
        "panjang_jtr_kms": ("kms", "Panjang jaringan tegangan rendah"),
    }
    add("-- 2. PARAMETER")
    add("insert into susut.parameter (kunci, nilai, satuan, keterangan) values")
    vals = [f"({q(k)}, {v}, {q(ket.get(k, ('',''))[0])}, {q(ket.get(k, ('',''))[1])})"
            for k, v in PARAM.items()]
    add("  " + rows(vals) + ";")
    add("")

    # ---- PENYULANG ---------------------------------------------------------
    add("-- 3. PENYULANG")
    add("insert into susut.penyulang (unit_id, kode, nama, jumlah_gardu, kapasitas_kva,")
    add("       panjang_jtm_kms, panjang_jtr_kms, jumlah_pelanggan, susut_persen,")
    add("       unbalance_persen, cos_phi, drop_tegangan_persen, sr_lebih_30m,")
    add("       indeks_prioritas, kelas_prioritas)")
    add("select u.id, x.* from susut.unit u,")
    add("(values")
    vals = []
    for p in DATA["penyulang"]:
        vals.append(
            f"({q(p['kode'])}, {q(p['nama'])}, {p['jumlah_gardu']}, {p['kapasitas_kva']}, "
            f"{p['panjang_jtm_kms']}, {p['panjang_jtr_kms']}, {p['jumlah_pelanggan']}, "
            f"{p['susut_persen']}, {p['unbalance_persen']}, {p['cos_phi']}, "
            f"{p['drop_tegangan_persen']}, {p['sr_lebih_30m']}, "
            f"{p['indeks_prioritas']}, {q(p['kelas_prioritas'])})")
    add("  " + rows(vals))
    add(") as x(kode, nama, jumlah_gardu, kapasitas_kva, panjang_jtm_kms, panjang_jtr_kms,")
    add("        jumlah_pelanggan, susut_persen, unbalance_persen, cos_phi,")
    add("        drop_tegangan_persen, sr_lebih_30m, indeks_prioritas, kelas_prioritas)")
    add(f"where u.kode = {q(UNIT['kode'])};")
    add("")

    # ---- NERACA ENERGI -----------------------------------------------------
    add("-- 4. NERACA ENERGI BULANAN")
    add("insert into susut.neraca_energi (unit_id, tahun, bulan, status_data, kwh_salur,")
    add("       kwh_jual, susut_persen, target_persen, susut_teknis_persen, susut_nonteknis_persen)")
    add("select u.id, x.* from susut.unit u,")
    add("(values")
    vals = []
    for n in DATA["neraca_energi"]:
        vals.append(
            f"({n['tahun']}::smallint, {n['bulan']}::smallint, "
            f"{q(n['status_data'])}::susut.status_data, {n['kwh_salur']}::bigint, "
            f"{n['kwh_jual']}::bigint, {n['susut_persen']}, {n['target_persen']}, "
            f"{n['susut_teknis_persen']}, {n['susut_nonteknis_persen']})")
    add("  " + rows(vals))
    add(") as x(tahun, bulan, status_data, kwh_salur, kwh_jual, susut_persen,")
    add("        target_persen, susut_teknis_persen, susut_nonteknis_persen)")
    add(f"where u.kode = {q(UNIT['kode'])};")
    add("")

    # ---- PROGRAM -----------------------------------------------------------
    add("-- 5. KATALOG PROGRAM (WORK PLAN)")
    add("insert into susut.program (unit_id, kode, nama, kategori, sub_kategori, satuan,")
    add("       siklus, pic, kwh_selamat_per_unit, target_tahun, urutan)")
    add("select u.id, x.* from susut.unit u,")
    add("(values")
    vals = []
    for i, p in enumerate(DATA["program"], start=1):
        vals.append(
            f"({q(p['kode'])}, {q(p['nama'])}, {q(p['kategori'])}::susut.kategori_susut, "
            f"{q(p['sub_kategori'])}, {q(p['satuan'])}, {q(p['siklus'])}, {q(p['pic'])}, "
            f"{p['kwh_selamat_per_unit']}, {p['target_tahun']}, {i}::smallint)")
    add("  " + rows(vals))
    add(") as x(kode, nama, kategori, sub_kategori, satuan, siklus, pic,")
    add("        kwh_selamat_per_unit, target_tahun, urutan)")
    add(f"where u.kode = {q(UNIT['kode'])};")
    add("")

    # ---- PROGRAM PERIODE ---------------------------------------------------
    add("-- 6. TARGET & REALISASI PROGRAM PER BULAN")
    add("insert into susut.program_periode (program_id, tahun, bulan, target_volume, realisasi_volume)")
    add("select pr.id, x.tahun, x.bulan, x.target_volume, x.realisasi_volume")
    add("from (values")
    vals = []
    for r in DATA["program_bulanan"]:
        vals.append(
            f"({q(r['program_kode'])}, {r['tahun']}::smallint, {r['bulan']}::smallint, "
            f"{r['target_volume']}, {q(r['realisasi_volume']) if r['realisasi_volume'] is None else r['realisasi_volume']})")
    add("  " + rows(vals))
    add(") as x(program_kode, tahun, bulan, target_volume, realisasi_volume)")
    add("join susut.program pr on pr.kode = x.program_kode;")
    add("")

    # ---- SUSUT PER PENYULANG ----------------------------------------------
    add("-- 7. SUSUT PER PENYULANG PER BULAN")
    add("insert into susut.susut_penyulang (penyulang_id, tahun, bulan, kwh_salur, kwh_susut, susut_persen)")
    add("select py.id, x.tahun, x.bulan, x.kwh_salur, x.kwh_susut, x.susut_persen")
    add("from (values")
    vals = []
    for r in DATA["susut_penyulang_bulanan"]:
        vals.append(
            f"({q(r['penyulang_kode'])}, {r['tahun']}::smallint, {r['bulan']}::smallint, "
            f"{r['kwh_salur']}::bigint, {r['kwh_susut']}::bigint, {r['susut_persen']})")
    add("  " + rows(vals))
    add(") as x(penyulang_kode, tahun, bulan, kwh_salur, kwh_susut, susut_persen)")
    add("join susut.penyulang py on py.kode = x.penyulang_kode;")
    add("")

    # ---- RUGI TEKNIS -------------------------------------------------------
    bln = META["bulan_realisasi"]
    add("-- 8. DEKOMPOSISI RUGI TEKNIS PER PENYULANG")
    add("insert into susut.rugi_teknis (penyulang_id, tahun, bulan, komponen, kwh_rugi, persen_dari_teknis)")
    add("select py.id, x.tahun, x.bulan, x.komponen, x.kwh_rugi, x.persen_dari_teknis")
    add("from (values")
    vals = []
    for r in DATA["rugi_teknis"]:
        vals.append(
            f"({q(r['penyulang_kode'])}, {META['tahun']}::smallint, {bln}::smallint, "
            f"{q(r['komponen'])}, {r['kwh_rugi']}::bigint, {r['persen_dari_teknis']})")
    add("  " + rows(vals))
    add(") as x(penyulang_kode, tahun, bulan, komponen, kwh_rugi, persen_dari_teknis)")
    add("join susut.penyulang py on py.kode = x.penyulang_kode;")
    add("")

    # ---- P2TL --------------------------------------------------------------
    add("-- 9. REKAP P2TL")
    add("insert into susut.p2tl (unit_id, tahun, bulan, golongan, keterangan,")
    add("       jumlah_pemeriksaan, jumlah_temuan, kwh_temuan, rupiah_tagsus, rupiah_terbayar)")
    add("select u.id, x.* from susut.unit u,")
    add("(values")
    vals = []
    for r in DATA["p2tl"]:
        vals.append(
            f"({r['tahun']}::smallint, {r['bulan']}::smallint, {q(r['golongan'])}, "
            f"{q(r['keterangan'])}, {r['jumlah_pemeriksaan']}, {r['jumlah_temuan']}, "
            f"{r['kwh_temuan']}::bigint, {r['rupiah_tagsus']}::bigint, {r['rupiah_terbayar']}::bigint)")
    add("  " + rows(vals))
    add(") as x(tahun, bulan, golongan, keterangan, jumlah_pemeriksaan, jumlah_temuan,")
    add("        kwh_temuan, rupiah_tagsus, rupiah_terbayar)")
    add(f"where u.kode = {q(UNIT['kode'])};")
    add("")

    # ---- ACTION PLAN -------------------------------------------------------
    add("-- 10. RENCANA AKSI")
    add("insert into susut.action_plan (unit_id, program_id, nomor, prioritas, kategori,")
    add("       aksi, akar_masalah, dampak_kwh_bulan, target_selesai, pic, status, progres_persen)")
    add("select u.id, pr.id, x.nomor, x.prioritas, x.kategori::susut.kategori_susut,")
    add("       x.aksi, x.akar_masalah, x.dampak_kwh_bulan, x.target_selesai, x.pic,")
    add("       x.status::susut.status_aksi, x.progres_persen")
    add("from susut.unit u")
    add("cross join (values")
    vals = []
    for a in DATA["action_plan"]:
        vals.append(
            f"({a['no']}::smallint, {q(a['prioritas'])}, {q(a['kategori'])}, "
            f"{q(a['program_kode'])}, {q(a['aksi'])}, {q(a['akar_masalah'])}, "
            f"{a['dampak_kwh_bulan']}::bigint, {q(a['target_selesai'])}, {q(a['pic'])}, "
            f"{q(a['status'])}, {a['progres_persen']})")
    add("  " + rows(vals))
    add(") as x(nomor, prioritas, kategori, program_kode, aksi, akar_masalah,")
    add("        dampak_kwh_bulan, target_selesai, pic, status, progres_persen)")
    add("left join susut.program pr on pr.kode = x.program_kode")
    add(f"where u.kode = {q(UNIT['kode'])};")
    add("")
    add("commit;")
    add("")

    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"[OK] seed SQL -> {OUT}  ({len(L)} baris, {OUT.stat().st_size/1024:.1f} KB)")


if __name__ == "__main__":
    main()
