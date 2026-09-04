# -*- coding: utf-8 -*-
"""
SUMBER DATA TUNGGAL (Single Source of Truth) — Monitoring Susut ULP Samboja
===========================================================================
Modul ini membaca berkas CSV di `data/master/` lalu menghitung seluruh angka
turunan yang dipakai oleh:
  1. Dashboard Excel        (scripts/build_excel.py)
  2. Seed database Supabase (scripts/build_sql.py -> supabase/migrations)
  3. Dashboard Web/Vercel   (lib/fallback/dataset.json)
  4. Dokumen work plan      (scripts/build_docs.py)

MENGISI DATA
------------
Seluruh angka masukan ada di `data/master/*.csv`. Berkas CSV dapat dibuka
langsung dengan Excel atau LibreOffice — tidak perlu menyentuh kode ini.

  unit.csv             identitas ULP
  parameter.csv        tarif, target susut, ambang status, besaran aset
  penyulang.csv        master penyulang + profil kondisi terkini
  neraca.csv           kWh salur & jual per bulan
  program.csv          katalog item work plan + faktor kWh diselamatkan
  program_bulanan.csv  target & realisasi tiap item per bulan
  susut_penyulang.csv  susut per penyulang per bulan
  action_plan.csv      rencana aksi percepatan

Sesudah menyunting, jalankan:  python3 scripts/build_all.py
Periksa konsistensinya dengan:  python3 scripts/validate_master.py

PENTING — TENTANG ANGKA BAWAAN
------------------------------
Isi CSV bawaan adalah DATA CONTOH yang disusun agar realistis dan konsisten
secara matematis, BUKAN data operasional PLN yang sebenarnya. Ganti dengan
data riil dari:
  * AP2T / TUL          -> kWh jual, DIL, DLPD, rekening
  * XPower / EIS-Susut  -> kWh salur per penyulang (APP outgoing GI)
  * Aplikasi P2TL       -> temuan, kWh temuan, tagihan susulan
  * SCADA / AMR         -> arus fasa, cos phi, tegangan, unbalance
  * Aplikasi Gardu/JDN  -> aset gardu, panjang JTM/JTR, SR
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MASTER_DIR = DATA_DIR / "master"

BULAN_NAMA = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
              "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


# ---------------------------------------------------------------------------
# PEMBACAAN CSV
# ---------------------------------------------------------------------------
def baca_csv(nama: str) -> list[dict[str, str]]:
    """Baca satu berkas master. Berkas yang hilang dilaporkan dengan jelas."""
    berkas = MASTER_DIR / nama
    if not berkas.exists():
        raise SystemExit(
            f"✗ Berkas master tidak ditemukan: {berkas.relative_to(ROOT)}\n"
            f"  Seluruh berkas masukan harus ada di {MASTER_DIR.relative_to(ROOT)}/"
        )
    with berkas.open(encoding="utf-8-sig", newline="") as f:
        return [b for b in csv.DictReader(f) if any(v.strip() for v in b.values())]


def angka(nilai: str, bawaan: float | None = None) -> float | None:
    """Ubah teks CSV menjadi angka. Sel kosong menjadi None (atau nilai bawaan)."""
    t = (nilai or "").strip().replace(" ", "")
    if not t:
        return bawaan
    # Terima gaya Indonesia (1.234,5) maupun gaya Inggris (1234.5)
    if "," in t and "." in t:
        t = t.replace(".", "").replace(",", ".")
    elif "," in t:
        t = t.replace(",", ".")
    return float(t)


def bulat(nilai: str, bawaan: int | None = None) -> int | None:
    v = angka(nilai, None)
    return bawaan if v is None else int(round(v))


# ---------------------------------------------------------------------------
# 0. UNIT & PARAMETER
# ---------------------------------------------------------------------------
_unit_baris = baca_csv("unit.csv")[0]
UNIT = {
    "kode": _unit_baris["kode"],
    "nama": _unit_baris["nama"],
    "up3": _unit_baris["up3"],
    "uid": _unit_baris["uid"],
    "manager": _unit_baris["manager"],
    "tahun": int(_unit_baris["tahun"]),
}
TAHUN = UNIT["tahun"]

PARAM: dict[str, float] = {}
PARAM_KETERANGAN: dict[str, tuple[str, str]] = {}
for _b in baca_csv("parameter.csv"):
    PARAM[_b["kunci"]] = angka(_b["nilai"], 0.0) or 0.0
    PARAM_KETERANGAN[_b["kunci"]] = (_b.get("satuan", ""), _b.get("keterangan", ""))


# ---------------------------------------------------------------------------
# 1. NERACA ENERGI BULANAN
# ---------------------------------------------------------------------------
_NERACA = sorted(baca_csv("neraca.csv"), key=lambda b: int(b["bulan"]))
_PORSI_TEKNIS = [angka(b["porsi_teknis"], 0.55) for b in _NERACA]

BULAN_REALISASI = max(
    (int(b["bulan"]) for b in _NERACA if b["status_data"].upper() == "REALISASI"),
    default=0,
)
BULAN_SISA = 12 - BULAN_REALISASI


def build_neraca() -> list[dict]:
    rows: list[dict] = []
    kum_salur = kum_susut = 0
    for i, b in enumerate(_NERACA):
        bulan = int(b["bulan"])
        salur = bulat(b["kwh_salur"], 0) or 0
        jual = bulat(b["kwh_jual"], 0) or 0
        susut = salur - jual
        pct = round(susut / salur * 100, 4) if salur else 0.0
        target_pct = angka(b["target_persen"], 0.0) or 0.0
        real = b["status_data"].upper() == "REALISASI"
        porsi = _PORSI_TEKNIS[i]

        teknis_pct = round(pct * porsi, 4)
        kwh_teknis = round(susut * porsi)

        if real:
            kum_salur += salur
            kum_susut += susut
            ytd = round(kum_susut / kum_salur * 100, 4) if kum_salur else 0.0
        else:
            ytd = None

        rows.append({
            "tahun": TAHUN, "bulan": bulan,
            "bulan_nama": BULAN_NAMA[bulan - 1],
            "bulan_panjang": BULAN_PANJANG[bulan - 1],
            "status_data": "REALISASI" if real else "PROYEKSI",
            "kwh_salur": salur, "kwh_jual": jual, "kwh_susut": susut,
            "susut_persen": pct, "target_persen": target_pct,
            "deviasi_persen": round(pct - target_pct, 4) if real else None,
            "susut_teknis_persen": teknis_pct,
            "susut_nonteknis_persen": round(pct - teknis_pct, 4),
            "kwh_susut_teknis": kwh_teknis,
            "kwh_susut_nonteknis": susut - kwh_teknis,
            "susut_ytd_persen": ytd,
            "rupiah_susut": round(susut * PARAM["tarif_rata_rata"]),
        })
    return rows


# ---------------------------------------------------------------------------
# 2. PENYULANG & PROFIL SUSUT TEKNIS
# ---------------------------------------------------------------------------
_PENYULANG = baca_csv("penyulang.csv")
_SUSUT_PENYULANG = baca_csv("susut_penyulang.csv")

# Komposisi rugi teknis (praktik distribusi): trafo, JTR, SR+APP, JTM, konektor
_KOMPOSISI_TEKNIS = {
    "trafo_distribusi": 0.272,
    "jaringan_tegangan_rendah": 0.318,
    "sambungan_rumah_app": 0.221,
    "jaringan_tegangan_menengah": 0.147,
    "konektor_sambungan": 0.042,
}


def build_penyulang(neraca: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    total_plg = sum(bulat(p["jumlah_pelanggan"], 0) or 0 for p in _PENYULANG)
    if not total_plg:
        raise SystemExit("✗ Jumlah pelanggan seluruh penyulang bernilai nol.")
    idx_akhir = BULAN_REALISASI - 1
    akhir = neraca[idx_akhir]

    susut_per_kode: dict[str, dict[int, float]] = {}
    for r in _SUSUT_PENYULANG:
        susut_per_kode.setdefault(r["penyulang_kode"], {})[int(r["bulan"])] = \
            angka(r["susut_persen"], 0.0) or 0.0

    penyulang, susut_bulanan, rugi_teknis = [], [], []

    for p in _PENYULANG:
        kode = p["kode"]
        plg = bulat(p["jumlah_pelanggan"], 0) or 0
        susut_pct = angka(p["susut_persen"], 0.0) or 0.0
        unbal = angka(p["unbalance_persen"], 0.0) or 0.0
        cosphi = angka(p["cos_phi"], 0.9) or 0.9
        drop_v = angka(p["drop_tegangan_persen"], 0.0) or 0.0
        sr_panjang = bulat(p["sr_lebih_30m"], 0) or 0

        share = plg / total_plg
        salur_akhir = round(akhir["kwh_salur"] * share)

        # Indeks prioritas: gabungan besaran susut, unbalance, cos phi, drop tegangan
        indeks = ((susut_pct / 8.0) * 40 + (unbal / 25.0) * 25 +
                  ((0.95 - cosphi) / 0.12) * 20 + (drop_v / 8.0) * 15)

        penyulang.append({
            "kode": kode, "nama": p["nama"],
            "jumlah_gardu": bulat(p["jumlah_gardu"], 0),
            "kapasitas_kva": bulat(p["kapasitas_kva"], 0),
            "panjang_jtm_kms": angka(p["panjang_jtm_kms"], 0.0),
            "panjang_jtr_kms": angka(p["panjang_jtr_kms"], 0.0),
            "jumlah_pelanggan": plg,
            "susut_persen": susut_pct,
            "unbalance_persen": unbal,
            "cos_phi": cosphi,
            "drop_tegangan_persen": drop_v,
            "sr_lebih_30m": sr_panjang,
            "kwh_salur_bulan": salur_akhir,
            "kwh_susut_bulan": round(salur_akhir * susut_pct / 100.0),
            "rupiah_susut_bulan": round(salur_akhir * susut_pct / 100.0
                                        * PARAM["tarif_rata_rata"]),
            "indeks_prioritas": round(indeks, 1),
            "kelas_prioritas": ("KRITIS" if indeks >= 70 else
                                "TINGGI" if indeks >= 55 else
                                "SEDANG" if indeks >= 42 else "RENDAH"),
        })

        # Susut bulanan per penyulang (hanya bulan yang sudah realisasi)
        for n in neraca:
            if n["status_data"] != "REALISASI":
                continue
            pct = susut_per_kode.get(kode, {}).get(n["bulan"])
            if pct is None:
                continue
            salur_m = round(n["kwh_salur"] * share)
            susut_bulanan.append({
                "penyulang_kode": kode, "tahun": TAHUN, "bulan": n["bulan"],
                "bulan_nama": BULAN_NAMA[n["bulan"] - 1],
                "kwh_salur": salur_m,
                "kwh_susut": round(salur_m * pct / 100.0),
                "susut_persen": pct,
            })

        # Dekomposisi rugi teknis penyulang pada bulan realisasi terakhir
        kwh_teknis = round(salur_akhir * susut_pct / 100.0 * _PORSI_TEKNIS[idx_akhir])
        for komp, bobot in _KOMPOSISI_TEKNIS.items():
            koreksi = 1.0
            if komp in ("jaringan_tegangan_rendah", "trafo_distribusi"):
                # Unbalance tinggi memperbesar rugi pada JTR dan trafo
                koreksi = 1 + (unbal - 14.0) / 100.0
            elif komp == "sambungan_rumah_app":
                # Semakin banyak SR panjang, semakin besar rugi sisi sambungan
                koreksi = 1 + (sr_panjang / plg - 0.04) * 1.6
            rugi_teknis.append({
                "penyulang_kode": kode,
                "komponen": komp,
                "kwh_rugi": round(kwh_teknis * bobot * koreksi),
                "persen_dari_teknis": round(bobot * koreksi * 100, 2),
            })

    return penyulang, susut_bulanan, rugi_teknis


# ---------------------------------------------------------------------------
# 3. WORK PLAN: KATALOG + TARGET & REALISASI BULANAN
# ---------------------------------------------------------------------------
_PROGRAM = baca_csv("program.csv")
_PROGRAM_BULANAN = baca_csv("program_bulanan.csv")


def _status_capaian(pct: float) -> str:
    """Empat tingkat status capaian."""
    if pct >= PARAM["ambang_tercapai"]:
        return "TERCAPAI"
    if pct >= PARAM["ambang_waspada"]:
        return "WASPADA"
    if pct >= PARAM["ambang_terlambat"]:
        return "TERLAMBAT"
    return "KRITIS"


def build_program() -> tuple[list[dict], list[dict]]:
    per_kode: dict[str, dict[int, dict]] = {}
    for r in _PROGRAM_BULANAN:
        per_kode.setdefault(r["program_kode"], {})[int(r["bulan"])] = r

    katalog, bulanan = [], []

    for p in _PROGRAM:
        kode = p["kode"]
        kwh_unit = angka(p["kwh_selamat_per_unit"], 0.0) or 0.0
        target_thn = angka(p["target_tahun"], 0.0) or 0.0
        baris_bulan = per_kode.get(kode, {})

        target_ytd = real_ytd = 0.0
        for m in range(1, 13):
            b = baris_bulan.get(m, {})
            t = angka(b.get("target_volume", ""), 0.0) or 0.0
            r = angka(b.get("realisasi_volume", ""), None)
            if m <= BULAN_REALISASI:
                target_ytd += t
                real_ytd += r or 0.0
            bulanan.append({
                "program_kode": kode, "tahun": TAHUN, "bulan": m,
                "bulan_nama": BULAN_NAMA[m - 1],
                "target_volume": round(t, 2),
                "realisasi_volume": None if r is None else round(r, 2),
                "target_kwh": round(t * kwh_unit),
                "realisasi_kwh": None if r is None else round(r * kwh_unit),
                "capaian_persen": round(r / t * 100, 2) if (r is not None and t) else None,
            })

        sisa = target_thn - real_ytd
        run_rate = real_ytd / BULAN_REALISASI if BULAN_REALISASI else 0.0
        kebutuhan = sisa / BULAN_SISA if BULAN_SISA else 0.0
        capaian = real_ytd / target_ytd * 100 if target_ytd else 0.0

        katalog.append({
            "kode": kode, "nama": p["nama"], "kategori": p["kategori"],
            "sub_kategori": p["sub_kategori"], "satuan": p["satuan"],
            "pic": p["pic"], "siklus": p["siklus"],
            "kwh_selamat_per_unit": kwh_unit,
            "target_tahun": target_thn,
            "target_ytd": round(target_ytd, 2),
            "realisasi_ytd": round(real_ytd, 2),
            "capaian_ytd_persen": round(capaian, 2),
            "capaian_thd_target_tahun_persen": round(
                real_ytd / target_thn * 100, 2) if target_thn else 0.0,
            "sisa_target": round(sisa, 2),
            "kebutuhan_per_bulan_sisa": round(kebutuhan, 2),
            "run_rate_bulanan": round(run_rate, 2),
            "faktor_kejar": round(kebutuhan / run_rate, 2) if run_rate > 0 else None,
            "kwh_selamat_ytd": round(real_ytd * kwh_unit),
            "kwh_selamat_target_tahun": round(target_thn * kwh_unit),
            "rupiah_selamat_ytd": round(real_ytd * kwh_unit * PARAM["tarif_rata_rata"]),
            "status": _status_capaian(capaian) if target_ytd else "N/A",
        })

    return katalog, bulanan


# ---------------------------------------------------------------------------
# 4. P2TL — REKAP TEMUAN PELANGGARAN
# ---------------------------------------------------------------------------
_GOL_P2TL = [
    ("P-I",   "Mempengaruhi batas daya",                     0.31),
    ("P-II",  "Mempengaruhi pengukuran energi",              0.44),
    ("P-III", "Mempengaruhi batas daya & pengukuran energi", 0.19),
    ("P-IV",  "Bukan pelanggan (sambungan langsung)",        0.06),
]


def build_p2tl(program_bulanan: list[dict]) -> list[dict]:
    """Rekap P2TL diturunkan dari realisasi item N-01 (pemeriksaan),
    N-02 (kWh temuan), dan N-03 (penagihan tagihan susulan)."""
    def ambil(kode: str) -> dict[int, dict]:
        return {r["bulan"]: r for r in program_bulanan if r["program_kode"] == kode}

    to, kwh, rp = ambil("N-01"), ambil("N-02"), ambil("N-03")
    rows = []
    for m in range(1, 13):
        periksa = to.get(m, {}).get("realisasi_volume")
        if periksa is None:
            continue
        # Hit rate temuan naik seiring membaiknya kualitas penetapan sasaran
        hit = 0.081 + m * 0.0042
        temuan = round(periksa * hit)
        # Rasio tagihan susulan yang benar-benar terbayar pada bulan tersebut
        bayar = _RASIO_BAYAR.get(m, 0.78)
        tagsus_bulan = (rp.get(m, {}).get("realisasi_volume") or 0.0) * 1_000_000

        for gol, ket, bobot in _GOL_P2TL:
            rows.append({
                "tahun": TAHUN, "bulan": m, "bulan_nama": BULAN_NAMA[m - 1],
                "golongan": gol, "keterangan": ket,
                "jumlah_pemeriksaan": round(periksa * bobot),
                "jumlah_temuan": round(temuan * bobot),
                "kwh_temuan": round((kwh.get(m, {}).get("realisasi_kwh") or 0) * bobot),
                "rupiah_tagsus": round(tagsus_bulan * bobot),
                "rupiah_terbayar": round(tagsus_bulan * bobot * bayar),
            })
    return rows


# Rasio penagihan tagihan susulan per bulan (data contoh; ganti bila ada data riil)
_RASIO_BAYAR = {1: 0.6459, 2: 0.6707, 3: 0.7098, 4: 0.7254, 5: 0.7790,
                6: 0.8338, 7: 0.7905, 8: 0.8750}


# ---------------------------------------------------------------------------
# 5. RENCANA AKSI
# ---------------------------------------------------------------------------
def build_action_plan() -> list[dict]:
    return [{
        "no": bulat(a["no"], 0),
        "prioritas": a["prioritas"],
        "kategori": a["kategori"],
        "program_kode": a["program_kode"],
        "aksi": a["aksi"],
        "akar_masalah": a["akar_masalah"],
        "target_selesai": a["target_selesai"],
        "pic": a["pic"],
        "status": a["status"],
        "progres_persen": angka(a["progres_persen"], 0.0),
    } for a in baca_csv("action_plan.csv")]


def _sinkron_action_plan(aksi: list[dict], katalog: list[dict]) -> None:
    """Selaraskan dampak kWh tiap aksi dengan sisa target program terkait."""
    idx = {k["kode"]: k for k in katalog}
    for a in aksi:
        k = idx.get(a["program_kode"])
        if not k:
            a.update(dampak_kwh_bulan=0, dampak_kwh_sisa_tahun=0,
                     dampak_rupiah_sisa_tahun=0, sisa_volume=0, satuan="",
                     kebutuhan_per_bulan=0, capaian_ytd_persen=0,
                     status_program="N/A")
            continue
        sisa_kwh = round(max(k["sisa_target"], 0) * k["kwh_selamat_per_unit"])
        a["dampak_kwh_bulan"] = round(sisa_kwh / BULAN_SISA) if BULAN_SISA else 0
        a["dampak_kwh_sisa_tahun"] = sisa_kwh
        a["dampak_rupiah_sisa_tahun"] = round(sisa_kwh * PARAM["tarif_rata_rata"])
        a["sisa_volume"] = k["sisa_target"]
        a["satuan"] = k["satuan"]
        a["kebutuhan_per_bulan"] = k["kebutuhan_per_bulan_sisa"]
        a["capaian_ytd_persen"] = k["capaian_ytd_persen"]
        a["status_program"] = k["status"]


# ---------------------------------------------------------------------------
# 6. RANGKUMAN KPI & SIMULASI PENCAPAIAN TARGET
# ---------------------------------------------------------------------------
def build_kpi(neraca: list[dict], katalog: list[dict]) -> dict:
    real = [n for n in neraca if n["status_data"] == "REALISASI"]
    proj = [n for n in neraca if n["status_data"] == "PROYEKSI"]

    kum_salur = sum(n["kwh_salur"] for n in real)
    kum_susut = sum(n["kwh_susut"] for n in real)
    susut_ytd = kum_susut / kum_salur * 100 if kum_salur else 0.0

    salur_setahun = sum(n["kwh_salur"] for n in neraca)
    salur_sisa = sum(n["kwh_salur"] for n in proj)
    akhir = real[-1]
    target = PARAM["target_susut_akhir_tahun"]

    # SKENARIO A: target dimaknai susut kumulatif (YTD) akhir tahun
    kwh_susut_max = salur_setahun * target / 100
    izin_sisa = kwh_susut_max - kum_susut
    izin_sisa_pct = izin_sisa / salur_sisa * 100 if salur_sisa else 0.0
    tanpa_aksi = salur_sisa * akhir["susut_persen"] / 100
    gap_a = tanpa_aksi - izin_sisa

    # SKENARIO B: target dimaknai susut bulan Desember (exit rate)
    salur_des = neraca[11]["kwh_salur"]
    gap_b = salur_des * (akhir["susut_persen"] - target) / 100

    kwh_selamat_ytd = sum(k["kwh_selamat_ytd"] for k in katalog)
    kwh_selamat_target = sum(k["kwh_selamat_target_tahun"] for k in katalog)
    kwh_selamat_sisa = kwh_selamat_target - kwh_selamat_ytd

    def agregat(kategori: str) -> dict:
        sub = [k for k in katalog if k["kategori"] == kategori]
        if not sub:
            return {"kwh_target_tahun": 0, "kwh_ytd": 0, "kwh_sisa": 0,
                    "capaian_persen": 0}
        t = sum(k["kwh_selamat_target_tahun"] for k in sub)
        r = sum(k["kwh_selamat_ytd"] for k in sub)
        return {"kwh_target_tahun": t, "kwh_ytd": r, "kwh_sisa": t - r,
                "capaian_persen": round(
                    sum(k["capaian_ytd_persen"] for k in sub) / len(sub), 2)}

    per_status: dict[str, int] = {}
    for k in katalog:
        per_status[k["status"]] = per_status.get(k["status"], 0) + 1

    return {
        "periode_data": f"{BULAN_PANJANG[BULAN_REALISASI-1]} {TAHUN}",
        "bulan_realisasi": BULAN_REALISASI,
        "bulan_tersisa": BULAN_SISA,
        "susut_bulan_ini_persen": akhir["susut_persen"],
        "target_bulan_ini_persen": akhir["target_persen"],
        "deviasi_bulan_ini": round(akhir["susut_persen"] - akhir["target_persen"], 3),
        "susut_ytd_persen": round(susut_ytd, 3),
        "target_ytd_persen": round(
            sum(n["kwh_salur"] * n["target_persen"] / 100 for n in real)
            / kum_salur * 100, 3) if kum_salur else 0.0,
        "target_akhir_tahun_persen": target,
        "baseline_tahun_lalu_persen": PARAM["baseline_susut_2025"],
        "perbaikan_vs_baseline": round(PARAM["baseline_susut_2025"] - susut_ytd, 3),
        "kwh_salur_ytd": kum_salur,
        "kwh_jual_ytd": kum_salur - kum_susut,
        "kwh_susut_ytd": kum_susut,
        "rupiah_susut_ytd": round(kum_susut * PARAM["tarif_rata_rata"]),
        "susut_teknis_persen": akhir["susut_teknis_persen"],
        "susut_nonteknis_persen": akhir["susut_nonteknis_persen"],

        "skenario_a_kumulatif": {
            "label": "Target 5,85% sebagai SUSUT KUMULATIF (YTD) akhir tahun",
            "kwh_susut_maks_setahun": round(kwh_susut_max),
            "kwh_susut_sisa_diizinkan": round(izin_sisa),
            "susut_sisa_diizinkan_persen": round(izin_sisa_pct, 3),
            "gap_kwh_harus_diselamatkan": round(gap_a),
            "gap_kwh_per_bulan": round(gap_a / BULAN_SISA) if BULAN_SISA else 0,
            "gap_rupiah": round(gap_a * PARAM["tarif_rata_rata"]),
            "tingkat_kesulitan": (
                "SANGAT BERAT" if izin_sisa_pct < akhir["susut_persen"] - 1.0
                else "BERAT" if izin_sisa_pct < akhir["susut_persen"] - 0.4
                else "MODERAT"),
        },
        "skenario_b_exit_rate": {
            "label": "Target 5,85% sebagai SUSUT BULAN DESEMBER (exit rate)",
            "kwh_susut_maks_desember": round(salur_des * target / 100),
            "penurunan_pp_dibutuhkan": round(akhir["susut_persen"] - target, 3),
            "gap_kwh_harus_diselamatkan": round(gap_b),
            "gap_kwh_per_bulan": round(gap_b / BULAN_SISA) if BULAN_SISA else 0,
            "gap_rupiah": round(gap_b * PARAM["tarif_rata_rata"]),
            "tingkat_kesulitan": "MODERAT",
        },

        "kwh_selamat_ytd": kwh_selamat_ytd,
        "kwh_selamat_target_tahun": kwh_selamat_target,
        "kwh_selamat_sisa": kwh_selamat_sisa,
        "kwh_selamat_sisa_per_bulan": round(kwh_selamat_sisa / BULAN_SISA) if BULAN_SISA else 0,
        "rupiah_selamat_ytd": round(kwh_selamat_ytd * PARAM["tarif_rata_rata"]),
        "rupiah_selamat_sisa": round(kwh_selamat_sisa * PARAM["tarif_rata_rata"]),
        "kontribusi_teknis": agregat("TEKNIS"),
        "kontribusi_nonteknis": agregat("NON_TEKNIS"),

        "capaian_program_rata_rata": round(
            sum(k["capaian_ytd_persen"] for k in katalog) / len(katalog), 2),
        "jumlah_program": len(katalog),
        "jumlah_tercapai": per_status.get("TERCAPAI", 0),
        "jumlah_waspada": per_status.get("WASPADA", 0),
        "jumlah_terlambat": per_status.get("TERLAMBAT", 0),
        "jumlah_kritis": per_status.get("KRITIS", 0),
        "program_kritis": [k["kode"] for k in katalog if k["status"] == "KRITIS"],
        "status_keseluruhan": ("ON TRACK" if susut_ytd <= target + 0.15
                               else "PERLU AKSELERASI"),
    }


# ---------------------------------------------------------------------------
# BUILD & EXPORT
# ---------------------------------------------------------------------------
def build_all() -> dict:
    neraca = build_neraca()
    penyulang, susut_penyulang, rugi_teknis = build_penyulang(neraca)
    katalog, program_bulanan = build_program()
    p2tl = build_p2tl(program_bulanan)
    aksi = build_action_plan()
    _sinkron_action_plan(aksi, katalog)
    kpi = build_kpi(neraca, katalog)

    return {
        "meta": {
            "unit": UNIT, "parameter": PARAM,
            "tahun": TAHUN, "bulan_realisasi": BULAN_REALISASI,
            "bulan_nama": BULAN_NAMA, "bulan_panjang": BULAN_PANJANG,
            "catatan": ("Data pada berkas ini adalah CONTOH untuk keperluan "
                        "pembangunan dashboard. Ganti dengan data riil dari "
                        "AP2T, XPower, Aplikasi P2TL, dan SCADA/AMR."),
        },
        "kpi": kpi,
        "neraca_energi": neraca,
        "penyulang": penyulang,
        "susut_penyulang_bulanan": susut_penyulang,
        "rugi_teknis": rugi_teknis,
        "program": katalog,
        "program_bulanan": program_bulanan,
        "p2tl": p2tl,
        "action_plan": aksi,
    }


def main() -> None:
    ds = build_all()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "dataset.json"
    out.write_text(json.dumps(ds, indent=2, ensure_ascii=False), encoding="utf-8")

    for key in ("neraca_energi", "penyulang", "program", "program_bulanan",
                "p2tl", "action_plan", "rugi_teknis", "susut_penyulang_bulanan"):
        (DATA_DIR / f"{key}.json").write_text(
            json.dumps(ds[key], indent=2, ensure_ascii=False), encoding="utf-8")

    k = ds["kpi"]
    print(f"[OK] dataset dibangun dari data/master/*.csv -> {out.name}")
    print(f"     Periode          : {k['periode_data']} "
          f"({k['bulan_realisasi']} bulan realisasi, {k['bulan_tersisa']} tersisa)")
    print(f"     Susut YTD        : {k['susut_ytd_persen']}%  "
          f"(target akhir tahun {k['target_akhir_tahun_persen']}%)")
    print(f"     Capaian program  : {k['capaian_program_rata_rata']}%  "
          f"({k['jumlah_tercapai']} tercapai / {k['jumlah_waspada']} waspada / "
          f"{k['jumlah_terlambat']} terlambat / {k['jumlah_kritis']} kritis)")
    print(f"     kWh diselamatkan : {k['kwh_selamat_ytd']:,} kWh  "
          f"(Rp {k['rupiah_selamat_ytd']:,})")


if __name__ == "__main__":
    main()
