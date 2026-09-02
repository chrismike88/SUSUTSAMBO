# -*- coding: utf-8 -*-
"""
SUMBER DATA TUNGGAL (Single Source of Truth) — Monitoring Susut ULP Samboja
===========================================================================
Modul ini membangkitkan seluruh dataset yang dipakai oleh:
  1. Dashboard Excel        (scripts/build_excel.py)
  2. Seed database Supabase (scripts/build_sql.py -> supabase/migrations)
  3. Dashboard Web/Vercel   (web/lib/data/dataset.json)

PENTING — TENTANG ANGKA DI SINI
-------------------------------
Angka pada modul ini adalah DATA CONTOH (dummy) yang disusun agar realistis
dan konsisten secara matematis, BUKAN data operasional PLN yang sebenarnya.
Ganti isi tabel di bawah dengan data riil dari:
  * AP2T / TUL          -> kWh jual, DIL, DLPD, rekening
  * XPower / EIS-Susut  -> kWh salur per penyulang (APP outgoing GI)
  * Aplikasi P2TL       -> temuan, kWh temuan, tagihan susulan
  * SCADA / AMR         -> arus fasa, cos phi, tegangan, unbalance
  * Aplikasi Gardu/JDN  -> aset gardu, panjang JTM/JTR, SR

Setelah data riil dimasukkan, jalankan ulang: `python3 scripts/build_all.py`
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

random.seed(20260902)  # deterministik: hasil selalu sama

# ---------------------------------------------------------------------------
# 0. KONFIGURASI UNIT & PARAMETER GLOBAL
# ---------------------------------------------------------------------------
TAHUN = 2026
BULAN_BERJALAN = 9            # September 2026 -> realisasi tersedia s/d Agustus (M8)
BULAN_REALISASI = 8

BULAN_NAMA = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
              "Jul", "Ags", "Sep", "Okt", "Nov", "Des"]
BULAN_PANJANG = ["Januari", "Februari", "Maret", "April", "Mei", "Juni",
                 "Juli", "Agustus", "September", "Oktober", "November", "Desember"]

UNIT = {
    "kode": "ULP-SBJ",
    "nama": "ULP Samboja",
    "up3": "UP3 Balikpapan",
    "uid": "UID Kalimantan Timur & Kalimantan Utara",
    "manager": "Manager Layanan ULP Samboja",
    "tahun": TAHUN,
}

PARAM = {
    # Harga jual rata-rata (Rp/kWh) — dipakai untuk konversi kWh -> Rupiah
    "tarif_rata_rata": 1462.50,
    # Target susut jaringan distribusi akhir tahun (%) — RKAP
    "target_susut_akhir_tahun": 5.85,
    # Realisasi susut tahun sebelumnya (%) — baseline
    "baseline_susut_2025": 7.12,
    # Batas bawah teknis yang realistis dicapai jaringan eksisting (%)
    "floor_susut_teknis": 3.30,
    # Ambang status capaian (%) — 4 tingkat
    "ambang_tercapai": 100.0,
    "ambang_waspada": 90.0,
    "ambang_terlambat": 75.0,
    "jumlah_pelanggan": 61482,
    "jumlah_gardu": 574,
    "jumlah_penyulang": 10,
    "panjang_jtm_kms": 612.4,
    "panjang_jtr_kms": 848.9,
}

# ---------------------------------------------------------------------------
# 1. NERACA ENERGI BULANAN  (kWh salur vs kWh jual)
# ---------------------------------------------------------------------------
# Format: (kwh_salur, susut_persen_realisasi, target_persen_bulanan)
_NERACA_INPUT = [
    (19_845_320, 7.27, 6.90),   # Jan
    (18_932_410, 7.05, 6.75),   # Feb
    (20_114_780, 6.90, 6.60),   # Mar
    (20_556_905, 6.65, 6.45),   # Apr
    (21_203_640, 6.39, 6.30),   # Mei
    (20_874_115, 6.14, 6.15),   # Jun
    (21_446_980, 6.06, 6.05),   # Jul
    (21_702_355, 6.03, 5.95),   # Ags
    (21_540_900, None, 5.92),   # Sep (proyeksi)
    (21_890_450, None, 5.90),   # Okt (proyeksi)
    (22_105_780, None, 5.87),   # Nov (proyeksi)
    (22_480_310, None, 5.85),   # Des (proyeksi)
]

# Porsi susut teknis dari total susut per bulan (sisanya non-teknis).
# Awal tahun non-teknis masih tinggi, membaik setelah program P2TL & AMR jalan.
_PORSI_TEKNIS = [0.512, 0.520, 0.530, 0.545, 0.556, 0.568, 0.575, 0.582,
                 0.586, 0.590, 0.593, 0.596]


def build_neraca() -> list[dict]:
    rows = []
    kum_salur = kum_jual = 0.0
    for i, (salur, susut_pct, target_pct) in enumerate(_NERACA_INPUT):
        is_real = susut_pct is not None
        pct = susut_pct if is_real else target_pct
        kwh_susut = round(salur * pct / 100.0)
        kwh_jual = salur - kwh_susut
        teknis_pct = round(pct * _PORSI_TEKNIS[i], 4)
        nonteknis_pct = round(pct - teknis_pct, 4)

        if is_real:
            kum_salur += salur
            kum_jual += kwh_jual
            ytd = round((kum_salur - kum_jual) / kum_salur * 100.0, 4) if kum_salur else 0.0
        else:
            ytd = None

        rows.append({
            "tahun": TAHUN,
            "bulan": i + 1,
            "bulan_nama": BULAN_NAMA[i],
            "bulan_panjang": BULAN_PANJANG[i],
            "status_data": "REALISASI" if is_real else "PROYEKSI",
            "kwh_salur": salur,
            "kwh_jual": kwh_jual,
            "kwh_susut": kwh_susut,
            "susut_persen": round(pct, 4),
            "target_persen": target_pct,
            "deviasi_persen": round(pct - target_pct, 4) if is_real else None,
            "susut_teknis_persen": teknis_pct,
            "susut_nonteknis_persen": nonteknis_pct,
            "kwh_susut_teknis": round(kwh_susut * _PORSI_TEKNIS[i]),
            "kwh_susut_nonteknis": kwh_susut - round(kwh_susut * _PORSI_TEKNIS[i]),
            "susut_ytd_persen": ytd,
            "rupiah_susut": round(kwh_susut * PARAM["tarif_rata_rata"]),
        })
    return rows


# ---------------------------------------------------------------------------
# 2. PENYULANG (FEEDER) & PROFIL SUSUT TEKNIS
# ---------------------------------------------------------------------------
# (kode, nama, gardu, kapasitas_kva, jtm_kms, jtr_kms, pelanggan,
#  susut_pct_ags, unbalance_pct, cos_phi, drop_tegangan_pct, sr_lebih_30m)
_PENYULANG_INPUT = [
    ("SBJ-01", "Kuala Samboja",  78, 8_450, 61.2,  96.4, 8_940, 7.94, 21.4, 0.86, 6.8, 412),
    ("SBJ-02", "Sungai Merdeka", 71, 7_900, 74.8, 103.7, 8_120, 7.41, 18.9, 0.88, 7.4, 388),
    ("SBJ-03", "Handil Baru",    64, 7_250, 58.6,  88.2, 7_365, 6.88, 16.2, 0.89, 5.9, 301),
    ("SBJ-04", "Argosari",       55, 6_100, 69.4,  81.5, 6_042, 6.42, 14.8, 0.90, 6.2, 254),
    ("SBJ-05", "Bukit Raya",     61, 6_800, 52.1,  79.8, 6_580, 5.97, 13.1, 0.91, 5.1, 226),
    ("SBJ-06", "Karya Merdeka",  49, 5_450, 63.9,  76.3, 5_318, 5.63, 12.4, 0.92, 5.6, 198),
    ("SBJ-07", "Amborawang",     52, 5_800, 57.3,  74.9, 5_704, 5.35, 11.7, 0.92, 4.8, 175),
    ("SBJ-08", "Tani Bhakti",    44, 4_900, 71.6,  92.1, 4_836, 5.11, 10.9, 0.93, 6.5, 163),
    ("SBJ-09", "Beringin Agung", 51, 5_650, 55.4,  81.6, 5_412, 4.86,  9.8, 0.93, 4.4, 141),
    ("SBJ-10", "Sungai Seluang", 49, 5_300, 48.1,  74.4, 3_165, 4.52,  8.6, 0.94, 4.1, 118),
]

# Komposisi rugi teknis (SPLN/praktik distribusi): trafo, JTR, SR+APP, JTM, konektor
_KOMPOSISI_TEKNIS = {
    "trafo_distribusi": 0.272,
    "jaringan_tegangan_rendah": 0.318,
    "sambungan_rumah_app": 0.221,
    "jaringan_tegangan_menengah": 0.147,
    "konektor_sambungan": 0.042,
}


def build_penyulang(neraca: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    total_plg = sum(p[6] for p in _PENYULANG_INPUT)
    ags = neraca[BULAN_REALISASI - 1]

    penyulang, susut_bulanan, rugi_teknis = [], [], []

    for (kode, nama, gardu, kva, jtm, jtr, plg, susut_pct,
         unbal, cosphi, drop_v, sr_panjang) in _PENYULANG_INPUT:

        share = plg / total_plg
        salur_ags = round(ags["kwh_salur"] * share)
        # Indeks prioritas: gabungan besaran susut, unbalance, cos phi, drop tegangan
        idx = (susut_pct / 8.0) * 40 + (unbal / 25.0) * 25 + \
              ((0.95 - cosphi) / 0.12) * 20 + (drop_v / 8.0) * 15
        penyulang.append({
            "kode": kode, "nama": nama,
            "jumlah_gardu": gardu, "kapasitas_kva": kva,
            "panjang_jtm_kms": jtm, "panjang_jtr_kms": jtr,
            "jumlah_pelanggan": plg,
            "susut_persen": susut_pct,
            "unbalance_persen": unbal,
            "cos_phi": cosphi,
            "drop_tegangan_persen": drop_v,
            "sr_lebih_30m": sr_panjang,
            "kwh_salur_bulan": salur_ags,
            "kwh_susut_bulan": round(salur_ags * susut_pct / 100.0),
            "rupiah_susut_bulan": round(salur_ags * susut_pct / 100.0 * PARAM["tarif_rata_rata"]),
            "indeks_prioritas": round(idx, 1),
            "kelas_prioritas": "KRITIS" if idx >= 70 else ("TINGGI" if idx >= 55 else
                               ("SEDANG" if idx >= 42 else "RENDAH")),
        })

        # Tren susut per penyulang sepanjang tahun (menurun mengikuti tren unit)
        for m, n in enumerate(neraca):
            if n["status_data"] != "REALISASI":
                continue
            faktor = n["susut_persen"] / ags["susut_persen"]
            jitter = 1 + random.uniform(-0.022, 0.022)
            pct = round(susut_pct * faktor * jitter, 3)
            salur_m = round(n["kwh_salur"] * share)
            susut_bulanan.append({
                "penyulang_kode": kode, "tahun": TAHUN, "bulan": m + 1,
                "bulan_nama": BULAN_NAMA[m],
                "kwh_salur": salur_m,
                "kwh_susut": round(salur_m * pct / 100.0),
                "susut_persen": pct,
            })

        # Dekomposisi rugi teknis penyulang (bulan Agustus)
        kwh_teknis = round(salur_ags * susut_pct / 100.0 * _PORSI_TEKNIS[BULAN_REALISASI - 1])
        for komp, bobot in _KOMPOSISI_TEKNIS.items():
            # Penyulang dengan unbalance tinggi -> rugi JTR & trafo lebih besar
            koreksi = 1.0
            if komp in ("jaringan_tegangan_rendah", "trafo_distribusi"):
                koreksi = 1 + (unbal - 14.0) / 100.0
            if komp == "sambungan_rumah_app":
                koreksi = 1 + (sr_panjang / plg - 0.04) * 1.6
            rugi_teknis.append({
                "penyulang_kode": kode,
                "komponen": komp,
                "kwh_rugi": round(kwh_teknis * bobot * koreksi),
                "persen_dari_teknis": round(bobot * koreksi * 100, 2),
            })

    return penyulang, susut_bulanan, rugi_teknis


# ---------------------------------------------------------------------------
# 3. KATALOG PROGRAM KERJA (WORK PLAN) PENURUNAN SUSUT
# ---------------------------------------------------------------------------
# kode, nama, kategori, sub_kategori, satuan, target_tahun, kwh_per_unit,
# capaian_ags_ratio (realisasi/target-prorata s/d Ags), pic, siklus
_PROGRAM_INPUT = [
    # ---------------- TEKNIS ----------------
    ("T-01", "Penyeimbangan beban trafo distribusi (balancing)", "TEKNIS", "Trafo",
     "gardu", 180, 950, 1.06, "Supervisor Teknik", "Bulanan"),
    ("T-02", "Penggantian konduktor JTR usang ke twisted cable", "TEKNIS", "JTR",
     "kms", 24.5, 6_200, 0.71, "Supervisor Teknik", "Triwulanan"),
    ("T-03", "Pemasangan trafo sisip / uprating trafo overload", "TEKNIS", "Trafo",
     "unit", 12, 11_500, 0.58, "Supervisor Teknik", "Triwulanan"),
    ("T-04", "Penggantian SR > 30 m & kabel SR usang", "TEKNIS", "SR/APP",
     "pelanggan", 1450, 62, 0.83, "Supervisor Teknik", "Bulanan"),
    ("T-05", "Rekonfigurasi / pemecahan beban penyulang", "TEKNIS", "JTM",
     "penyulang", 6, 21_000, 0.50, "Supervisor Teknik", "Semesteran"),
    ("T-06", "Pemasangan kapasitor bank (perbaikan cos phi)", "TEKNIS", "JTM",
     "unit", 8, 13_800, 0.44, "Supervisor Teknik", "Semesteran"),
    ("T-07", "Penggantian konektor & retensioning sambungan", "TEKNIS", "Konektor",
     "titik", 620, 145, 0.95, "Supervisor Teknik", "Bulanan"),
    ("T-08", "Pemasangan alat ukur (AMR) sisi gardu distribusi", "TEKNIS", "Trafo",
     "unit", 45, 1_350, 0.67, "Supervisor Teknik", "Triwulanan"),
    ("T-09", "Pemeliharaan preventif & perbaikan grounding gardu", "TEKNIS", "Trafo",
     "gardu", 240, 310, 1.02, "Supervisor Teknik", "Bulanan"),
    ("T-10", "Uprating konduktor JTM (AAAC 150 mm2)", "TEKNIS", "JTM",
     "kms", 9.8, 8_900, 0.36, "Supervisor Teknik", "Semesteran"),
    # -------------- NON-TEKNIS --------------
    ("N-01", "P2TL - pencapaian Target Operasi (TO)", "NON_TEKNIS", "P2TL",
     "pelanggan", 3600, 0, 0.92, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-02", "P2TL - perolehan kWh temuan pelanggaran", "NON_TEKNIS", "P2TL",
     "kWh", 1_150_000, 1.0, 0.88, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-03", "P2TL - realisasi penagihan tagihan susulan", "NON_TEKNIS", "P2TL",
     "Rp juta", 3400, 0, 0.74, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-04", "Penggantian kWh meter rusak / macet / buram", "NON_TEKNIS", "APP",
     "unit", 2750, 96, 0.86, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-05", "Penggantian kWh meter tua (> 15 tahun)", "NON_TEKNIS", "APP",
     "unit", 1900, 71, 0.63, "Supervisor Transaksi Energi", "Triwulanan"),
    ("N-06", "Pemasangan / normalisasi AMR pelanggan >= 41,5 kVA", "NON_TEKNIS", "AMR",
     "pelanggan", 168, 1_480, 0.79, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-07", "Pemeriksaan APP pelanggan potensial (>= 3.500 VA)", "NON_TEKNIS", "APP",
     "pelanggan", 2400, 58, 0.69, "Supervisor Transaksi Energi", "Bulanan"),
    ("N-08", "Penurunan DLPD (Daftar Langganan Perlu Diperhatikan)", "NON_TEKNIS", "Baca Meter",
     "rekening", 4200, 44, 0.81, "Supervisor Pelayanan Pelanggan", "Bulanan"),
    ("N-09", "Penertiban & pemeteran PJU ilegal", "NON_TEKNIS", "PJU",
     "titik", 320, 640, 0.55, "Supervisor Transaksi Energi", "Triwulanan"),
    ("N-10", "Validasi faktor kali & Data Induk Langganan (DIL)", "NON_TEKNIS", "Administrasi",
     "pelanggan", 1100, 118, 0.94, "Supervisor Pelayanan Pelanggan", "Bulanan"),
    ("N-11", "Peningkatan akurasi baca meter (foto stand / RBM)", "NON_TEKNIS", "Baca Meter",
     "rekening", 12000, 12, 0.97, "Supervisor Pelayanan Pelanggan", "Bulanan"),
    ("N-12", "Penormalan sambungan langsung / sambungan liar", "NON_TEKNIS", "P2TL",
     "titik", 210, 890, 0.61, "Supervisor Transaksi Energi", "Bulanan"),
]

# Pola distribusi target bulanan (12 bulan). Sebagian program musiman.
_POLA_RATA = [1 / 12] * 12
_POLA_TRIWULAN = [0.02, 0.05, 0.11, 0.05, 0.07, 0.12, 0.05, 0.07, 0.13, 0.08, 0.11, 0.14]
_POLA_SEMESTER = [0.0, 0.02, 0.06, 0.09, 0.12, 0.16, 0.04, 0.07, 0.10, 0.12, 0.10, 0.12]
_POLA = {"Bulanan": _POLA_RATA, "Triwulanan": _POLA_TRIWULAN, "Semesteran": _POLA_SEMESTER}


def _status_capaian(pct: float) -> str:
    """4 tingkat status capaian program."""
    if pct >= PARAM["ambang_tercapai"]:
        return "TERCAPAI"
    if pct >= PARAM["ambang_waspada"]:
        return "WASPADA"
    if pct >= PARAM["ambang_terlambat"]:
        return "TERLAMBAT"
    return "KRITIS"


def build_program() -> tuple[list[dict], list[dict]]:
    katalog, bulanan = [], []

    for (kode, nama, kat, sub, satuan, target_thn, kwh_unit,
         rasio, pic, siklus) in _PROGRAM_INPUT:

        pola = _POLA[siklus]
        target_ytd = target_thn * sum(pola[:BULAN_REALISASI])
        real_ytd_target = target_ytd * rasio

        # Sebar realisasi ke bulan Jan..Ags mengikuti pola + jitter
        bobot_real = [pola[m] * (1 + random.uniform(-0.18, 0.18))
                      for m in range(BULAN_REALISASI)]
        total_bobot = sum(bobot_real)

        real_kum = 0.0
        for m in range(12):
            t_bln = target_thn * pola[m]
            row = {
                "program_kode": kode, "tahun": TAHUN, "bulan": m + 1,
                "bulan_nama": BULAN_NAMA[m],
                "target_volume": round(t_bln, 2),
                "realisasi_volume": None,
                "target_kwh": round(t_bln * kwh_unit),
                "realisasi_kwh": None,
                "capaian_persen": None,
            }
            if m < BULAN_REALISASI:
                r = real_ytd_target * (bobot_real[m] / total_bobot)
                real_kum += r
                row["realisasi_volume"] = round(r, 2)
                row["realisasi_kwh"] = round(r * kwh_unit)
                row["capaian_persen"] = round(r / t_bln * 100, 2) if t_bln else None
            bulanan.append(row)

        real_ytd = real_kum
        sisa = target_thn - real_ytd
        bulan_sisa = 12 - BULAN_REALISASI
        katalog.append({
            "kode": kode, "nama": nama, "kategori": kat, "sub_kategori": sub,
            "satuan": satuan, "pic": pic, "siklus": siklus,
            "kwh_selamat_per_unit": kwh_unit,
            "target_tahun": target_thn,
            "target_ytd": round(target_ytd, 2),
            "realisasi_ytd": round(real_ytd, 2),
            "capaian_ytd_persen": round(real_ytd / target_ytd * 100, 2) if target_ytd else 0,
            "capaian_thd_target_tahun_persen": round(real_ytd / target_thn * 100, 2),
            "sisa_target": round(sisa, 2),
            "kebutuhan_per_bulan_sisa": round(sisa / bulan_sisa, 2),
            "run_rate_bulanan": round(real_ytd / BULAN_REALISASI, 2),
            "faktor_kejar": round((sisa / bulan_sisa) / (real_ytd / BULAN_REALISASI), 2)
                            if real_ytd > 0 else None,
            "kwh_selamat_ytd": round(real_ytd * kwh_unit),
            "kwh_selamat_target_tahun": round(target_thn * kwh_unit),
            "rupiah_selamat_ytd": round(real_ytd * kwh_unit * PARAM["tarif_rata_rata"]),
            "status": _status_capaian(real_ytd / target_ytd * 100) if target_ytd else "N/A",
        })

    return katalog, bulanan


# ---------------------------------------------------------------------------
# 4. P2TL — REKAP TEMUAN PELANGGARAN
# ---------------------------------------------------------------------------
_GOL_P2TL = [
    ("P-I",   "Mempengaruhi batas daya",                       0.31),
    ("P-II",  "Mempengaruhi pengukuran energi",                0.44),
    ("P-III", "Mempengaruhi batas daya & pengukuran energi",   0.19),
    ("P-IV",  "Bukan pelanggan (sambungan langsung)",          0.06),
]


def build_p2tl(program_bulanan: list[dict]) -> list[dict]:
    to = {r["bulan"]: r for r in program_bulanan if r["program_kode"] == "N-01"}
    kwh = {r["bulan"]: r for r in program_bulanan if r["program_kode"] == "N-02"}
    rp = {r["bulan"]: r for r in program_bulanan if r["program_kode"] == "N-03"}

    rows = []
    for m in range(1, 13):
        periksa = to[m]["realisasi_volume"] if to[m]["realisasi_volume"] is not None else None
        if periksa is None:
            continue
        # Hit rate temuan terhadap pemeriksaan (naik seiring kualitas targeting)
        hit = 0.081 + m * 0.0042
        temuan = round(periksa * hit)
        # Rasio tagihan susulan yang benar-benar terbayar pada bulan tersebut.
        # Membaik seiring berjalannya task force penagihan, dengan variasi wajar.
        bayar = min(0.92, 0.63 + m * 0.026 + random.uniform(-0.055, 0.055))
        for gol, ket, bobot in _GOL_P2TL:
            n = round(temuan * bobot)
            rows.append({
                "tahun": TAHUN, "bulan": m, "bulan_nama": BULAN_NAMA[m - 1],
                "golongan": gol, "keterangan": ket,
                "jumlah_pemeriksaan": round(periksa * bobot),
                "jumlah_temuan": n,
                "kwh_temuan": round(kwh[m]["realisasi_kwh"] * bobot),
                "rupiah_tagsus": round(rp[m]["target_volume"] * 1_000_000 * bobot *
                                       (rp[m]["realisasi_volume"] / rp[m]["target_volume"])),
                "rupiah_terbayar": round(rp[m]["target_volume"] * 1_000_000 * bobot *
                                         (rp[m]["realisasi_volume"] / rp[m]["target_volume"]) * bayar),
            })
    return rows


# ---------------------------------------------------------------------------
# 5. RENCANA AKSI (ACTION PLAN) MENUJU TARGET AKHIR TAHUN
# ---------------------------------------------------------------------------
def build_action_plan() -> list[dict]:
    return [
        # (prioritas, kategori, aksi, dampak_kwh, target_selesai, pic, status)
        {"no": 1, "prioritas": "SANGAT TINGGI", "kategori": "NON_TEKNIS", "program_kode": "N-09",
         "aksi": "Sensus & pemeteran PJU ilegal di 4 kecamatan (Samboja, Samboja Barat, Muara Jawa, Loa Janan Ilir) — bentuk tim gabungan dengan Pemda/Dishub",
         "akar_masalah": "PJU tanpa meter & sambungan langsung ke JTR; kWh terpakai tidak tercatat",
         "dampak_kwh_bulan": 78_600, "target_selesai": "2026-11-30",
         "pic": "Supervisor Transaksi Energi", "status": "BERJALAN", "progres_persen": 55},
        {"no": 2, "prioritas": "SANGAT TINGGI", "kategori": "NON_TEKNIS", "program_kode": "N-03",
         "aksi": "Task force penagihan tagihan susulan P2TL: rekonsiliasi piutang, surat panggilan, opsi cicilan, pemutusan bagi yang menunggak > 30 hari",
         "akar_masalah": "Temuan P2TL tinggi tetapi realisasi tagih hanya 74% — kWh temuan tidak berkonversi jadi pendapatan",
         "dampak_kwh_bulan": 0, "target_selesai": "2026-12-15",
         "pic": "Supervisor Transaksi Energi", "status": "BERJALAN", "progres_persen": 48},
        {"no": 3, "prioritas": "SANGAT TINGGI", "kategori": "TEKNIS", "program_kode": "T-10",
         "aksi": "Percepatan uprating konduktor JTM penyulang SBJ-02 Sungai Merdeka & SBJ-01 Kuala Samboja (segmen ujung, drop tegangan > 7%)",
         "akar_masalah": "Penyulang terpanjang dengan drop tegangan 6,8–7,4% dan penampang konduktor tidak memadai",
         "dampak_kwh_bulan": 51_400, "target_selesai": "2026-12-20",
         "pic": "Supervisor Teknik", "status": "TERLAMBAT", "progres_persen": 36},
        {"no": 4, "prioritas": "TINGGI", "kategori": "TEKNIS", "program_kode": "T-06",
         "aksi": "Pemasangan 5 unit kapasitor bank sisa pada penyulang cos phi < 0,90 (SBJ-01, SBJ-02, SBJ-03)",
         "akar_masalah": "Cos phi 0,86–0,89 menaikkan arus dan rugi I²R pada JTM/trafo",
         "dampak_kwh_bulan": 42_300, "target_selesai": "2026-11-30",
         "pic": "Supervisor Teknik", "status": "BERJALAN", "progres_persen": 44},
        {"no": 5, "prioritas": "TINGGI", "kategori": "TEKNIS", "program_kode": "T-05",
         "aksi": "Rekonfigurasi & pemecahan beban 3 penyulang tersisa; manuver beban ke SBJ-09 & SBJ-10 yang masih ringan",
         "akar_masalah": "Ketimpangan beban antar penyulang; SBJ-01/02 padat, SBJ-09/10 ringan",
         "dampak_kwh_bulan": 46_250, "target_selesai": "2026-12-10",
         "pic": "Supervisor Teknik", "status": "BERJALAN", "progres_persen": 50},
        {"no": 6, "prioritas": "TINGGI", "kategori": "NON_TEKNIS", "program_kode": "N-05",
         "aksi": "Pengadaan & penggantian 700 unit kWh meter tua > 15 tahun (prioritas daya >= 2.200 VA)",
         "akar_masalah": "Meter tua cenderung lambat/under-register 2–5%",
         "dampak_kwh_bulan": 34_300, "target_selesai": "2026-12-15",
         "pic": "Supervisor Transaksi Energi", "status": "TERLAMBAT", "progres_persen": 63},
        {"no": 7, "prioritas": "TINGGI", "kategori": "NON_TEKNIS", "program_kode": "N-12",
         "aksi": "Operasi penertiban sambungan langsung di area padat Handil Baru & Kuala Samboja bersama aparat",
         "akar_masalah": "Permukiman padat & pendatang proyek IKN; sambungan liar dari JTR",
         "dampak_kwh_bulan": 24_400, "target_selesai": "2026-11-15",
         "pic": "Supervisor Transaksi Energi", "status": "BERJALAN", "progres_persen": 61},
        {"no": 8, "prioritas": "SEDANG", "kategori": "NON_TEKNIS", "program_kode": "N-07",
         "aksi": "Pemeriksaan APP 745 pelanggan potensial sisa; prioritaskan pelanggan dengan penurunan pemakaian > 30% YoY",
         "akar_masalah": "Anomali pemakaian belum dianalisis sistematis",
         "dampak_kwh_bulan": 13_300, "target_selesai": "2026-12-20",
         "pic": "Supervisor Transaksi Energi", "status": "BERJALAN", "progres_persen": 69},
        {"no": 9, "prioritas": "SEDANG", "kategori": "TEKNIS", "program_kode": "T-03",
         "aksi": "Pemasangan 5 trafo sisip pada gardu overload > 80% & JTR > 350 m",
         "akar_masalah": "JTR terlalu panjang dari gardu menyebabkan rugi I²R besar",
         "dampak_kwh_bulan": 17_400, "target_selesai": "2026-12-05",
         "pic": "Supervisor Teknik", "status": "BERJALAN", "progres_persen": 58},
        {"no": 10, "prioritas": "SEDANG", "kategori": "TEKNIS", "program_kode": "T-02",
         "aksi": "Penggantian 7,1 kms JTR usang (kawat telanjang) menjadi twisted cable",
         "akar_masalah": "JTR kawat telanjang rawan rugi & pencurian",
         "dampak_kwh_bulan": 25_300, "target_selesai": "2026-12-20",
         "pic": "Supervisor Teknik", "status": "BERJALAN", "progres_persen": 71},
        {"no": 11, "prioritas": "SEDANG", "kategori": "NON_TEKNIS", "program_kode": "N-06",
         "aksi": "Normalisasi 35 AMR pelanggan besar yang gagal baca / offline > 3 hari",
         "akar_masalah": "Sinyal modem lemah & meter error, pembacaan jadi estimasi",
         "dampak_kwh_bulan": 8_600, "target_selesai": "2026-10-31",
         "pic": "Supervisor Transaksi Energi", "status": "BERJALAN", "progres_persen": 79},
        {"no": 12, "prioritas": "RUTIN", "kategori": "TEKNIS", "program_kode": "T-01",
         "aksi": "Lanjutkan pengukuran & penyeimbangan beban trafo (unbalance > 15% wajib ditindak dalam 7 hari)",
         "akar_masalah": "Unbalance rata-rata unit 13,8%; SBJ-01 mencapai 21,4%",
         "dampak_kwh_bulan": 9_450, "target_selesai": "Rutin bulanan",
         "pic": "Supervisor Teknik", "status": "TERCAPAI", "progres_persen": 106},
    ]


def _sinkron_action_plan(aksi: list[dict], katalog: list[dict]) -> None:
    """Selaraskan dampak kWh tiap aksi dengan sisa target program terkait."""
    idx = {k["kode"]: k for k in katalog}
    bulan_sisa = 12 - BULAN_REALISASI
    for a in aksi:
        k = idx.get(a["program_kode"])
        if not k:
            continue
        a["dampak_kwh_bulan"] = round(
            max(k["sisa_target"], 0) * k["kwh_selamat_per_unit"] / bulan_sisa)
        a["dampak_kwh_sisa_tahun"] = round(max(k["sisa_target"], 0) * k["kwh_selamat_per_unit"])
        a["dampak_rupiah_sisa_tahun"] = round(a["dampak_kwh_sisa_tahun"] * PARAM["tarif_rata_rata"])
        a["sisa_volume"] = k["sisa_target"]
        a["satuan"] = k["satuan"]
        a["kebutuhan_per_bulan"] = k["kebutuhan_per_bulan_sisa"]
        a["capaian_ytd_persen"] = k["capaian_ytd_persen"]
        a["status_program"] = k["status"]


# ---------------------------------------------------------------------------
# 6. RANGKUMAN KPI & SIMULASI PENCAPAIAN TARGET
# ---------------------------------------------------------------------------
def build_kpi(neraca, katalog) -> dict:
    real = [n for n in neraca if n["status_data"] == "REALISASI"]
    proj = [n for n in neraca if n["status_data"] == "PROYEKSI"]

    kum_salur = sum(n["kwh_salur"] for n in real)
    kum_susut = sum(n["kwh_susut"] for n in real)
    susut_ytd = kum_susut / kum_salur * 100

    salur_setahun = sum(n["kwh_salur"] for n in neraca)
    salur_sisa = sum(n["kwh_salur"] for n in proj)
    ags = real[-1]

    # --- SKENARIO A: target 5,85% dimaknai SUSUT KUMULATIF (YTD) akhir tahun ---
    kwh_susut_max = salur_setahun * PARAM["target_susut_akhir_tahun"] / 100
    kwh_susut_sisa_izin = kwh_susut_max - kum_susut
    susut_sisa_izin_pct = kwh_susut_sisa_izin / salur_sisa * 100
    # Jika tanpa aksi tambahan, susut Sep-Des diasumsikan bertahan di level Agustus
    kwh_susut_tanpa_aksi = salur_sisa * ags["susut_persen"] / 100
    gap_kwh_A = kwh_susut_tanpa_aksi - kwh_susut_sisa_izin

    # --- SKENARIO B: target 5,85% dimaknai SUSUT BULAN DESEMBER (exit rate) ---
    kwh_susut_des_max = neraca[11]["kwh_salur"] * PARAM["target_susut_akhir_tahun"] / 100
    kwh_susut_des_tanpa_aksi = neraca[11]["kwh_salur"] * ags["susut_persen"] / 100
    gap_kwh_B = kwh_susut_des_tanpa_aksi - kwh_susut_des_max

    kwh_selamat_ytd = sum(k["kwh_selamat_ytd"] for k in katalog)
    kwh_selamat_target = sum(k["kwh_selamat_target_tahun"] for k in katalog)
    kwh_selamat_sisa = kwh_selamat_target - kwh_selamat_ytd
    bulan_sisa = 12 - BULAN_REALISASI

    def _agg(kat):
        sub = [k for k in katalog if k["kategori"] == kat]
        t = sum(k["target_ytd"] * 0 + k["kwh_selamat_target_tahun"] for k in sub)
        r = sum(k["kwh_selamat_ytd"] for k in sub)
        return {"kwh_target_tahun": t, "kwh_ytd": r,
                "kwh_sisa": t - r,
                "capaian_persen": round(
                    sum(k["capaian_ytd_persen"] for k in sub) / len(sub), 2)}

    per_status = {}
    for k in katalog:
        per_status[k["status"]] = per_status.get(k["status"], 0) + 1

    return {
        "periode_data": f"{BULAN_PANJANG[BULAN_REALISASI-1]} {TAHUN}",
        "bulan_realisasi": BULAN_REALISASI,
        "bulan_tersisa": bulan_sisa,
        "susut_bulan_ini_persen": ags["susut_persen"],
        "target_bulan_ini_persen": ags["target_persen"],
        "deviasi_bulan_ini": round(ags["susut_persen"] - ags["target_persen"], 3),
        "susut_ytd_persen": round(susut_ytd, 3),
        "target_ytd_persen": round(
            sum(n["kwh_salur"] * n["target_persen"] / 100 for n in real) / kum_salur * 100, 3),
        "target_akhir_tahun_persen": PARAM["target_susut_akhir_tahun"],
        "baseline_tahun_lalu_persen": PARAM["baseline_susut_2025"],
        "perbaikan_vs_baseline": round(PARAM["baseline_susut_2025"] - susut_ytd, 3),
        "kwh_salur_ytd": kum_salur,
        "kwh_jual_ytd": kum_salur - kum_susut,
        "kwh_susut_ytd": kum_susut,
        "rupiah_susut_ytd": round(kum_susut * PARAM["tarif_rata_rata"]),
        "susut_teknis_persen": ags["susut_teknis_persen"],
        "susut_nonteknis_persen": ags["susut_nonteknis_persen"],

        "skenario_a_kumulatif": {
            "label": "Target 5,85% sebagai SUSUT KUMULATIF (YTD) akhir tahun",
            "kwh_susut_maks_setahun": round(kwh_susut_max),
            "kwh_susut_sisa_diizinkan": round(kwh_susut_sisa_izin),
            "susut_sisa_diizinkan_persen": round(susut_sisa_izin_pct, 3),
            "gap_kwh_harus_diselamatkan": round(gap_kwh_A),
            "gap_kwh_per_bulan": round(gap_kwh_A / bulan_sisa),
            "gap_rupiah": round(gap_kwh_A * PARAM["tarif_rata_rata"]),
            "tingkat_kesulitan": "SANGAT BERAT" if susut_sisa_izin_pct < ags["susut_persen"] - 1.0
                                 else ("BERAT" if susut_sisa_izin_pct < ags["susut_persen"] - 0.4
                                       else "MODERAT"),
        },
        "skenario_b_exit_rate": {
            "label": "Target 5,85% sebagai SUSUT BULAN DESEMBER (exit rate)",
            "kwh_susut_maks_desember": round(kwh_susut_des_max),
            "penurunan_pp_dibutuhkan": round(ags["susut_persen"] - PARAM["target_susut_akhir_tahun"], 3),
            "gap_kwh_harus_diselamatkan": round(gap_kwh_B),
            "gap_kwh_per_bulan": round(gap_kwh_B / bulan_sisa),
            "gap_rupiah": round(gap_kwh_B * PARAM["tarif_rata_rata"]),
            "tingkat_kesulitan": "MODERAT",
        },

        "kwh_selamat_ytd": kwh_selamat_ytd,
        "kwh_selamat_target_tahun": kwh_selamat_target,
        "kwh_selamat_sisa": kwh_selamat_sisa,
        "kwh_selamat_sisa_per_bulan": round(kwh_selamat_sisa / bulan_sisa),
        "rupiah_selamat_ytd": round(kwh_selamat_ytd * PARAM["tarif_rata_rata"]),
        "rupiah_selamat_sisa": round(kwh_selamat_sisa * PARAM["tarif_rata_rata"]),
        "kontribusi_teknis": _agg("TEKNIS"),
        "kontribusi_nonteknis": _agg("NON_TEKNIS"),

        "capaian_program_rata_rata": round(
            sum(k["capaian_ytd_persen"] for k in katalog) / len(katalog), 2),
        "jumlah_program": len(katalog),
        "jumlah_tercapai": per_status.get("TERCAPAI", 0),
        "jumlah_waspada": per_status.get("WASPADA", 0),
        "jumlah_terlambat": per_status.get("TERLAMBAT", 0),
        "jumlah_kritis": per_status.get("KRITIS", 0),
        "program_kritis": [k["kode"] for k in katalog if k["status"] == "KRITIS"],
        "status_keseluruhan": ("ON TRACK" if susut_ytd <= PARAM["target_susut_akhir_tahun"] + 0.15
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
    print(f"[OK] dataset dibangun -> {out}")
    print(f"     Susut YTD        : {k['susut_ytd_persen']}%  (target akhir tahun {k['target_akhir_tahun_persen']}%)")
    print(f"     Capaian program  : {k['capaian_program_rata_rata']}%  "
          f"({k['jumlah_tercapai']} tercapai / {k['jumlah_waspada']} waspada / {k['jumlah_kritis']} kritis)")
    print(f"     kWh diselamatkan : {k['kwh_selamat_ytd']:,} kWh  (Rp {k['rupiah_selamat_ytd']:,})")


if __name__ == "__main__":
    main()
