# -*- coding: utf-8 -*-
"""
Membangun Dashboard Excel Monitoring Susut ULP Samboja.

Karakter workbook:
  * Sheet INPUT adalah SATU-SATUNYA tempat mengetik realisasi bulanan.
  * Sheet WORK PLAN, DASHBOARD, dan SIMULASI memakai FORMULA yang menunjuk ke
    sheet INPUT, sehingga seluruh angka, warna status, dan grafik ikut berubah
    begitu realisasi diketik. Workbook ini alat kerja, bukan cetakan statis.

Output: dist/Dashboard_Susut_ULP_Samboja_2026.xlsx
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import xlsxwriter

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "data" / "dataset.json").read_text(encoding="utf-8"))
OUT = ROOT / "dist" / "Dashboard_Susut_ULP_Samboja_2026.xlsx"

META = DATA["meta"]
UNIT = META["unit"]
PARAM = META["parameter"]
BULAN = META["bulan_nama"]
KPI = DATA["kpi"]
MR = META["bulan_realisasi"]          # bulan terakhir realisasi (8 = Agustus)

# --- Palet warna -----------------------------------------------------------
C = {
    "navy":    "#0B2E4F",
    "navy2":   "#123E68",
    "blue":    "#1273B8",
    "cyan":    "#24A5D9",
    "teal":    "#0E9F9F",
    "green":   "#16A34A",
    "green_l": "#DCFCE7",
    "amber":   "#F59E0B",
    "amber_l": "#FEF3C7",
    "orange":  "#EA7317",
    "red":     "#DC2626",
    "red_l":   "#FEE2E2",
    "grey":    "#64748B",
    "grey_l":  "#E2E8F0",
    "bg":      "#F4F7FA",
    "white":   "#FFFFFF",
    "ink":     "#0F172A",
    # Palet seri grafik (tervalidasi: pemisahan buta warna & kontras)
    "viz1":    "#2A78D6",   # biru   — slot 1
    "viz2":    "#EB6834",   # oranye — slot 2
    "viz3":    "#1BAF7A",   # aqua   — slot 3
    "grid":    "#E1E0D9",   # garis kisi rambut
    "axis":    "#C3C2B7",
    "muted":   "#898781",
}

STATUS_WARNA = {
    "TERCAPAI":  (C["green"],  C["green_l"]),
    "WASPADA":   (C["teal"],   "#CCFBF1"),
    "TERLAMBAT": (C["amber"],  C["amber_l"]),
    "KRITIS":    (C["red"],    C["red_l"]),
}


def buat_format(wb) -> dict:
    """Kumpulan format sel yang dipakai di seluruh workbook."""
    F = {}
    F["judul"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 20, "bold": True,
        "font_color": C["white"], "bg_color": C["navy"],
        "align": "left", "valign": "vcenter", "indent": 1})
    F["subjudul"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 10, "font_color": "#B9D6EE",
        "bg_color": C["navy"], "align": "left", "valign": "vcenter", "indent": 1})
    F["banner_kanan"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 10, "bold": True,
        "font_color": C["white"], "bg_color": C["navy"],
        "align": "right", "valign": "vcenter"})

    F["seksi"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 12, "bold": True,
        "font_color": C["navy"], "bottom": 2, "border_color": C["cyan"],
        "align": "left", "valign": "vcenter"})

    F["kartu_judul"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "font_color": C["grey"], "bg_color": C["white"],
        "align": "left", "valign": "vcenter", "indent": 1,
        "top": 1, "left": 1, "right": 1, "border_color": C["grey_l"]})
    F["kartu_nilai"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 22, "bold": True,
        "font_color": C["navy"], "bg_color": C["white"],
        "align": "left", "valign": "vcenter", "indent": 1,
        "left": 1, "right": 1, "border_color": C["grey_l"]})
    F["kartu_ket"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9,
        "font_color": C["grey"], "bg_color": C["white"],
        "align": "left", "valign": "vcenter", "indent": 1,
        "bottom": 1, "left": 1, "right": 1, "border_color": C["grey_l"]})

    for nama, warna in (("hijau", C["green"]), ("merah", C["red"]),
                        ("amber", C["amber"]), ("biru", C["blue"])):
        F[f"kartu_nilai_{nama}"] = wb.add_format({
            "font_name": "Segoe UI", "font_size": 22, "bold": True,
            "font_color": warna, "bg_color": C["white"],
            "align": "left", "valign": "vcenter", "indent": 1,
            "left": 1, "right": 1, "border_color": C["grey_l"]})

    F["th"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "font_color": C["white"], "bg_color": C["navy2"],
        "align": "center", "valign": "vcenter", "text_wrap": True,
        "border": 1, "border_color": C["navy"]})
    F["th_kiri"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "font_color": C["white"], "bg_color": C["navy2"],
        "align": "left", "valign": "vcenter", "text_wrap": True, "indent": 1,
        "border": 1, "border_color": C["navy"]})

    base = {"font_name": "Segoe UI", "font_size": 9, "border": 1,
            "border_color": C["grey_l"], "valign": "vcenter"}
    F["td"] = wb.add_format({**base, "align": "left", "indent": 1})
    F["td_wrap"] = wb.add_format({**base, "align": "left", "indent": 1, "text_wrap": True})
    F["td_c"] = wb.add_format({**base, "align": "center"})
    F["td_num"] = wb.add_format({**base, "align": "right", "num_format": "#,##0"})
    F["td_num1"] = wb.add_format({**base, "align": "right", "num_format": "#,##0.0"})
    F["td_num2"] = wb.add_format({**base, "align": "right", "num_format": "#,##0.00"})
    F["td_pct"] = wb.add_format({**base, "align": "right", "num_format": '0.00"%"'})
    F["td_pct1"] = wb.add_format({**base, "align": "right", "num_format": '0.0"%"'})
    F["td_rp"] = wb.add_format({**base, "align": "right", "num_format": '"Rp" #,##0'})
    F["td_rpjt"] = wb.add_format({**base, "align": "right", "num_format": '"Rp" #,##0.0,,"  jt"'})
    F["td_bold"] = wb.add_format({**base, "align": "left", "indent": 1, "bold": True})

    F["input"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "align": "right",
        "num_format": "#,##0.00", "bg_color": "#FFFBEB", "border": 1,
        "border_color": "#FCD34D", "valign": "vcenter", "locked": False})

    F["total"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "bg_color": "#E8F1F8", "font_color": C["navy"],
        "border": 1, "border_color": C["blue"], "align": "right",
        "num_format": "#,##0", "valign": "vcenter"})
    F["total_kiri"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "bg_color": "#E8F1F8", "font_color": C["navy"],
        "border": 1, "border_color": C["blue"], "align": "left",
        "indent": 1, "valign": "vcenter"})
    F["total_pct"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "bg_color": "#E8F1F8", "font_color": C["navy"],
        "border": 1, "border_color": C["blue"], "align": "right",
        "num_format": '0.00"%"', "valign": "vcenter"})

    for nama, (fg, bg) in STATUS_WARNA.items():
        F[f"badge_{nama}"] = wb.add_format({
            "font_name": "Segoe UI", "font_size": 8, "bold": True,
            "font_color": fg, "bg_color": bg, "align": "center",
            "valign": "vcenter", "border": 1, "border_color": bg})

    F["catatan"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 8, "font_color": C["grey"],
        "italic": True, "valign": "top", "text_wrap": True})
    F["teks"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 10, "valign": "top",
        "text_wrap": True, "align": "left"})
    F["teks_bold"] = wb.add_format({
        "font_name": "Segoe UI", "font_size": 10, "bold": True,
        "valign": "top", "font_color": C["navy"]})
    return F


def banner(ws, F, judul: str, sub: str, kolom_akhir: int = 17) -> None:
    ws.set_row(0, 8)
    ws.set_row(1, 30)
    ws.set_row(2, 18)
    ws.set_row(3, 8)
    ws.merge_range(1, 0, 1, kolom_akhir - 4, judul, F["judul"])
    ws.merge_range(2, 0, 2, kolom_akhir - 4, sub, F["subjudul"])
    ws.merge_range(1, kolom_akhir - 3, 2, kolom_akhir,
                   f"{UNIT['nama']}  |  {UNIT['up3']}\nPeriode data: {KPI['periode_data']}",
                   F["banner_kanan"])


# ===========================================================================
#  SHEET 1 — DASHBOARD
# ===========================================================================
def sheet_dashboard(wb, F) -> None:
    ws = wb.add_worksheet("DASHBOARD")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["navy"])
    ws.set_paper(9); ws.set_landscape(); ws.fit_to_pages(1, 0)
    ws.set_column(0, 0, 2)
    ws.set_column(1, 20, 9.2)
    banner(ws, F,
           "DASHBOARD MONITORING SUSUT ENERGI",
           f"Susut Teknis & Non-Teknis · Tahun {META['tahun']} · "
           f"Target akhir tahun {PARAM['target_susut_akhir_tahun']}%", 20)

    # ---------------- KARTU KPI ----------------
    kartu = [
        ("SUSUT YTD (KUMULATIF)", f"{KPI['susut_ytd_persen']:.2f}%",
         f"Target YTD {KPI['target_ytd_persen']:.2f}%  ·  "
         f"deviasi {KPI['susut_ytd_persen']-KPI['target_ytd_persen']:+.2f} pp", "merah"),
        ("SUSUT BULAN BERJALAN", f"{KPI['susut_bulan_ini_persen']:.2f}%",
         f"Target {KPI['target_bulan_ini_persen']:.2f}%  ·  "
         f"deviasi {KPI['deviasi_bulan_ini']:+.2f} pp", "amber"),
        ("PERBAIKAN vs TAHUN LALU", f"{KPI['perbaikan_vs_baseline']:.2f} pp",
         f"Baseline {KPI['baseline_tahun_lalu_persen']:.2f}%  ->  "
         f"{KPI['susut_ytd_persen']:.2f}%", "hijau"),
        ("NILAI SUSUT YTD", f"Rp {KPI['rupiah_susut_ytd']/1e9:.2f} M",
         f"{KPI['kwh_susut_ytd']:,.0f} kWh energi hilang".replace(",", "."), "merah"),
        ("CAPAIAN WORK PLAN", f"{KPI['capaian_program_rata_rata']:.1f}%",
         f"{KPI['jumlah_tercapai']} tercapai · {KPI['jumlah_waspada']} waspada · "
         f"{KPI['jumlah_terlambat']} terlambat · {KPI['jumlah_kritis']} kritis", "amber"),
        ("kWh DISELAMATKAN YTD", f"{KPI['kwh_selamat_ytd']/1e6:.2f} juta",
         f"dari target {KPI['kwh_selamat_target_tahun']/1e6:.2f} juta kWh setahun", "biru"),
        ("GAP KE TARGET (SEP-DES)", f"{KPI['skenario_a_kumulatif']['gap_kwh_harus_diselamatkan']/1e6:.2f} juta kWh",
         f"setara Rp {KPI['skenario_a_kumulatif']['gap_rupiah']/1e9:.2f} M  ·  "
         f"{KPI['skenario_a_kumulatif']['gap_kwh_per_bulan']/1e3:.0f} rb kWh/bulan", "merah"),
        ("SISA POTENSI WORK PLAN", f"{KPI['kwh_selamat_sisa']/1e6:.2f} juta kWh",
         "CUKUP untuk menutup gap bila program dieksekusi penuh"
         if KPI['kwh_selamat_sisa'] >= KPI['skenario_a_kumulatif']['gap_kwh_harus_diselamatkan']
         else "TIDAK CUKUP — perlu program tambahan", "hijau"),
    ]

    baris_kartu = [5, 10]
    for i, (judul, nilai, ket, warna) in enumerate(kartu):
        r = baris_kartu[i // 4]
        c = 1 + (i % 4) * 5
        ws.set_row(r, 16); ws.set_row(r + 1, 30); ws.set_row(r + 2, 26)
        ws.merge_range(r, c, r, c + 4, judul, F["kartu_judul"])
        ws.merge_range(r + 1, c, r + 1, c + 4, nilai, F[f"kartu_nilai_{warna}"])
        ws.merge_range(r + 2, c, r + 2, c + 4, ket, F["kartu_ket"])

    # ---------------- Baris status besar ----------------
    ws.set_row(14, 10)
    fmt_status = wb.add_format({
        "font_name": "Segoe UI", "font_size": 11, "bold": True,
        "font_color": C["white"],
        "bg_color": C["red"] if KPI["status_keseluruhan"] == "PERLU AKSELERASI" else C["green"],
        "align": "center", "valign": "vcenter"})
    ws.set_row(15, 26)
    verdict = ("MASIH BISA DICAPAI — syaratnya seluruh program KRITIS dieksekusi penuh"
               if KPI["kwh_selamat_sisa"] >= KPI["skenario_a_kumulatif"]["gap_kwh_harus_diselamatkan"]
               else "TIDAK CUKUP — perlu program tambahan di luar work plan")
    ws.merge_range(15, 1, 15, 20,
                   f"STATUS UNIT: {KPI['status_keseluruhan']}   ·   "
                   f"PUTUSAN TARGET AKHIR TAHUN: {verdict}", fmt_status)

    # ---------------- GRAFIK ----------------
    ws.write(17, 1, "TREN SUSUT BULANAN vs TARGET", F["seksi"])
    ws.write(17, 11, "KOMPOSISI SUSUT TEKNIS vs NON-TEKNIS", F["seksi"])

    n_baris = len(DATA["neraca_energi"])
    ch1 = wb.add_chart({"type": "line"})
    ch1.add_series({
        "name":       "='NERACA ENERGI'!$D$6",
        "categories": f"='NERACA ENERGI'!$B$7:$B${6+n_baris}",
        "values":     f"='NERACA ENERGI'!$D$7:$D${6+n_baris}",
        "line":   {"color": C["viz1"], "width": 2.25},
        "marker": {"type": "circle", "size": 7,
                   "fill": {"color": C["viz1"]}, "border": {"none": True}},
    })
    ch1.add_series({
        "name":       "='NERACA ENERGI'!$E$6",
        "categories": f"='NERACA ENERGI'!$B$7:$B${6+n_baris}",
        "values":     f"='NERACA ENERGI'!$E$7:$E${6+n_baris}",
        "line":   {"color": C["muted"], "width": 1.5, "dash_type": "dash"},
        "marker": {"type": "none"},
    })
    ch1.add_series({
        "name":       "Susut kumulatif (YTD)",
        "categories": f"='NERACA ENERGI'!$B$7:$B${6+n_baris}",
        "values":     f"='NERACA ENERGI'!$F$7:$F${6+n_baris}",
        "line":   {"color": C["viz2"], "width": 2.25},
        "marker": {"type": "none"},
    })
    ch1.set_title({"none": True})
    ch1.set_legend({"position": "bottom", "font": {"name": "Segoe UI", "size": 8}})
    ch1.set_x_axis({"num_font": {"name": "Segoe UI", "size": 8},
                    "line": {"color": C["grey_l"]}})
    ch1.set_y_axis({"name": "Susut (%)", "min": 4.5, "max": 7.8,
                    "num_font": {"name": "Segoe UI", "size": 8},
                    "name_font": {"name": "Segoe UI", "size": 8},
                    "major_gridlines": {"visible": True,
                                        "line": {"color": C["grid"]}}})
    ch1.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch1.set_plotarea({"fill": {"color": C["white"]}})
    ch1.set_size({"width": 640, "height": 300})
    ws.insert_chart(18, 1, ch1)

    ch2 = wb.add_chart({"type": "bar", "subtype": "percent_stacked"})
    ch2.add_series({
        "name":       "Susut Teknis",
        "categories": "='ANALISIS TEKNIS'!$A$41:$A$41",
        "values":     "='ANALISIS TEKNIS'!$C$41:$C$41",
        "fill":       {"color": C["viz1"]},
        "gap":        60,
        "data_labels": {"value": True, "num_format": '0.00"%"',
                        "font": {"name": "Segoe UI", "size": 10, "bold": True,
                                 "color": C["white"]}},
    })
    ch2.add_series({
        "name":       "Susut Non-Teknis",
        "categories": "='ANALISIS TEKNIS'!$A$41:$A$41",
        "values":     "='ANALISIS TEKNIS'!$C$42:$C$42",
        "fill":       {"color": C["viz2"]},
        "data_labels": {"value": True, "num_format": '0.00"%"',
                        "font": {"name": "Segoe UI", "size": 10, "bold": True,
                                 "color": C["white"]}},
    })
    ch2.set_title({"none": True})
    ch2.set_legend({"position": "bottom", "font": {"name": "Segoe UI", "size": 8}})
    ch2.set_x_axis({"visible": False})
    ch2.set_y_axis({"visible": False, "major_gridlines": {"visible": False}})
    ch2.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch2.set_plotarea({"fill": {"color": C["white"]}})
    ch2.set_size({"width": 370, "height": 300})
    ws.insert_chart(18, 11, ch2)

    # --- Baris grafik kedua ---
    ws.write(35, 1, "PROGRAM DENGAN GAP TERBESAR (kWh belum terealisasi)", F["seksi"])
    ws.write(35, 11, "KOMPONEN RUGI TEKNIS (kWh/bulan)", F["seksi"])

    ch3 = wb.add_chart({"type": "bar"})
    ch3.add_series({
        "name":       "Sisa potensi kWh",
        "categories": "='DATA GRAFIK'!$B$4:$B$13",
        "values":     "='DATA GRAFIK'!$C$4:$C$13",
        "fill":       {"color": C["viz1"]},
        "gap":        45,
        "data_labels": {"value": True, "num_format": "#,##0",
                        "font": {"name": "Segoe UI", "size": 8}},
    })
    ch3.set_title({"none": True})
    ch3.set_legend({"none": True})
    ch3.set_x_axis({"visible": False, "major_gridlines": {"visible": False}})
    ch3.set_y_axis({"num_font": {"name": "Segoe UI", "size": 8},
                    "reverse": True})
    ch3.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch3.set_size({"width": 640, "height": 300})
    ws.insert_chart(36, 1, ch3)

    ch4 = wb.add_chart({"type": "bar"})
    ch4.add_series({
        "name":       "kWh rugi per bulan",
        "categories": "='DATA GRAFIK'!$F$4:$F$8",
        "values":     "='DATA GRAFIK'!$G$4:$G$8",
        "fill":       {"color": C["viz1"]},
        "gap":        45,
        "data_labels": {"value": True, "num_format": "#,##0",
                        "font": {"name": "Segoe UI", "size": 8}},
    })
    ch4.set_title({"none": True})
    ch4.set_legend({"none": True})
    ch4.set_x_axis({"visible": False, "major_gridlines": {"visible": False}})
    ch4.set_y_axis({"num_font": {"name": "Segoe UI", "size": 8}, "reverse": True})
    ch4.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch4.set_size({"width": 370, "height": 300})
    ws.insert_chart(36, 11, ch4)

    # --- Baris grafik ketiga ---
    ws.write(53, 1, "PERINGKAT PENYULANG BERDASARKAN SUSUT", F["seksi"])
    ws.write(53, 11, "CAPAIAN WORK PLAN PER KATEGORI", F["seksi"])

    ch5 = wb.add_chart({"type": "bar"})
    ch5.add_series({
        "name":       "Susut (%)",
        "categories": "='DATA GRAFIK'!$J$4:$J$13",
        "values":     "='DATA GRAFIK'!$K$4:$K$13",
        "fill":       {"color": C["viz2"]},
        "gap":        45,
        "data_labels": {"value": True, "num_format": '0.00"%"',
                        "font": {"name": "Segoe UI", "size": 8}},
    })
    ch5.set_title({"none": True}); ch5.set_legend({"none": True})
    ch5.set_x_axis({"visible": False, "major_gridlines": {"visible": False}})
    ch5.set_y_axis({"num_font": {"name": "Segoe UI", "size": 8}, "reverse": True})
    ch5.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch5.set_size({"width": 640, "height": 290})
    ws.insert_chart(54, 1, ch5)

    ch6 = wb.add_chart({"type": "column"})
    ch6.add_series({
        "name":       "Capaian (%)",
        "categories": "='DATA GRAFIK'!$N$4:$N$5",
        "values":     "='DATA GRAFIK'!$O$4:$O$5",
        "fill":       {"color": C["viz1"]},
        "gap":        90,
        "data_labels": {"value": True, "num_format": '0.0"%"',
                        "font": {"name": "Segoe UI", "size": 9, "bold": True}},
    })
    ch6.set_title({"none": True}); ch6.set_legend({"none": True})
    ch6.set_x_axis({"num_font": {"name": "Segoe UI", "size": 9}})
    ch6.set_y_axis({"max": 110, "num_font": {"name": "Segoe UI", "size": 8},
                    "major_gridlines": {"visible": True, "line": {"color": C["grid"]}}})
    ch6.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch6.set_size({"width": 370, "height": 290})
    ws.insert_chart(54, 11, ch6)

    ws.merge_range(71, 1, 72, 20, META["catatan"], F["catatan"])
    ws.freeze_panes(4, 0)


# ===========================================================================
#  SHEET 2 — NERACA ENERGI
# ===========================================================================
def sheet_neraca(wb, F) -> None:
    ws = wb.add_worksheet("NERACA ENERGI")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["blue"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 10)
    ws.set_column(2, 2, 12)
    ws.set_column(3, 6, 11)
    ws.set_column(7, 12, 13)
    banner(ws, F, "NERACA ENERGI BULANAN",
           "kWh Salur (APP outgoing GI) vs kWh Jual (AP2T/TUL) — dasar perhitungan susut", 13)

    hdr = ["Bulan", "Status", "Susut (%)", "Target (%)", "Susut YTD (%)",
           "Deviasi (pp)", "kWh Salur", "kWh Jual", "kWh Susut",
           "Susut Teknis (%)", "Susut Non-Teknis (%)", "Nilai Susut (Rp)"]
    ws.set_row(5, 30)
    for i, h in enumerate(hdr):
        ws.write(5, 1 + i, h, F["th"])

    r = 6
    for n in DATA["neraca_energi"]:
        proj = n["status_data"] == "PROYEKSI"
        ws.write(r, 1, n["bulan_nama"], F["td_bold"])
        ws.write(r, 2, n["status_data"], F["td_c"])
        ws.write(r, 3, n["susut_persen"], F["td_pct"])
        ws.write(r, 4, n["target_persen"], F["td_pct"])
        if n["susut_ytd_persen"] is not None:
            ws.write(r, 5, n["susut_ytd_persen"], F["td_pct"])
        else:
            ws.write_blank(r, 5, None, F["td_pct"])
        if n["deviasi_persen"] is not None:
            ws.write(r, 6, n["deviasi_persen"], F["td_num2"])
        else:
            ws.write_blank(r, 6, None, F["td_num2"])
        ws.write(r, 7, n["kwh_salur"], F["td_num"])
        ws.write(r, 8, n["kwh_jual"], F["td_num"])
        ws.write(r, 9, n["kwh_susut"], F["td_num"])
        ws.write(r, 10, n["susut_teknis_persen"], F["td_pct"])
        ws.write(r, 11, n["susut_nonteknis_persen"], F["td_pct"])
        ws.write(r, 12, n["rupiah_susut"], F["td_rp"])
        r += 1

    akhir = r - 1
    ws.write(r, 1, "TOTAL / RATA2", F["total_kiri"])
    ws.write(r, 2, "", F["total_kiri"])
    ws.write_formula(r, 3, f"=SUM(J7:J{akhir+1})/SUM(H7:H{akhir+1})*100", F["total_pct"])
    ws.write_formula(r, 4, f"=SUMPRODUCT(E7:E{akhir+1},H7:H{akhir+1})/SUM(H7:H{akhir+1})",
                     F["total_pct"])
    ws.write_blank(r, 5, None, F["total_pct"])
    ws.write_blank(r, 6, None, F["total"])
    for col in (7, 8, 9):
        L = chr(ord("A") + col)
        ws.write_formula(r, col, f"=SUM({L}7:{L}{akhir+1})", F["total"])
    ws.write_blank(r, 10, None, F["total_pct"])
    ws.write_blank(r, 11, None, F["total_pct"])
    ws.write_formula(r, 12, f"=SUM(M7:M{akhir+1})", F["total"])

    # Warna deviasi: hijau bila di bawah target, merah bila di atas
    ws.conditional_format(6, 6, akhir, 6, {
        "type": "cell", "criteria": ">", "value": 0,
        "format": wb.add_format({"font_color": C["red"], "bold": True,
                                 "num_format": "#,##0.00", "border": 1,
                                 "border_color": C["grey_l"], "font_size": 9,
                                 "font_name": "Segoe UI", "align": "right"})})
    ws.conditional_format(6, 6, akhir, 6, {
        "type": "cell", "criteria": "<=", "value": 0,
        "format": wb.add_format({"font_color": C["green"], "bold": True,
                                 "num_format": "#,##0.00", "border": 1,
                                 "border_color": C["grey_l"], "font_size": 9,
                                 "font_name": "Segoe UI", "align": "right"})})
    ws.conditional_format(6, 3, akhir, 3, {
        "type": "data_bar", "bar_color": C["orange"], "bar_solid": True})
    ws.conditional_format(6, 9, akhir, 9, {
        "type": "data_bar", "bar_color": C["cyan"], "bar_solid": True})

    ws.write(r + 2, 1,
             "Rumus susut = (kWh Salur - kWh Jual) / kWh Salur x 100%.  "
             "Baris PROYEKSI adalah rencana; ganti menjadi REALISASI setelah data bulan tersebut terbit.",
             F["catatan"])
    ws.freeze_panes(6, 2)
    ws.autofilter(5, 1, akhir, 12)


# ===========================================================================
#  SHEET 3 — INPUT REALISASI  (satu-satunya sheet yang diketik)
# ===========================================================================
def sheet_input(wb, F) -> None:
    ws = wb.add_worksheet("INPUT REALISASI")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["amber"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 8)
    ws.set_column(2, 2, 46)
    ws.set_column(3, 3, 11)
    ws.set_column(4, 15, 9.5)
    ws.set_column(16, 17, 12)
    banner(ws, F, "INPUT REALISASI BULANAN WORK PLAN",
           "Sel kuning = tempat mengetik. Seluruh sheet lain mengikuti isian di sini.", 17)

    fmt_note = wb.add_format({
        "font_name": "Segoe UI", "font_size": 9, "bold": True,
        "font_color": "#92400E", "bg_color": "#FEF3C7",
        "align": "left", "valign": "vcenter", "indent": 1,
        "border": 1, "border_color": "#FCD34D"})
    ws.set_row(4, 22)
    ws.merge_range(4, 1, 4, 17,
                   "  Isi HANYA sel berwarna kuning. Kolom target sudah terkunci "
                   "sesuai work plan; kolom capaian dihitung otomatis.", fmt_note)

    ws.set_row(6, 30)
    ws.write(6, 1, "Kode", F["th"])
    ws.write(6, 2, "Item Work Plan", F["th_kiri"])
    ws.write(6, 3, "Satuan", F["th"])
    for i, b in enumerate(BULAN):
        ws.write(6, 4 + i, b, F["th"])
    ws.write(6, 16, "Total Realisasi", F["th"])
    ws.write(6, 17, "Target Tahun", F["th"])

    per_program = {}
    for row in DATA["program_bulanan"]:
        per_program.setdefault(row["program_kode"], {})[row["bulan"]] = row

    r = 7
    baris_program = {}
    for p in DATA["program"]:
        warna_kat = C["blue"] if p["kategori"] == "TEKNIS" else C["teal"]
        fmt_kode = wb.add_format({
            "font_name": "Segoe UI", "font_size": 9, "bold": True,
            "font_color": C["white"], "bg_color": warna_kat,
            "align": "center", "valign": "vcenter",
            "border": 1, "border_color": warna_kat})
        ws.write(r, 1, p["kode"], fmt_kode)
        ws.write(r, 2, p["nama"], F["td"])
        ws.write(r, 3, p["satuan"], F["td_c"])
        for m in range(1, 13):
            v = per_program[p["kode"]][m]["realisasi_volume"]
            ws.write(r, 3 + m, v if v is not None else None, F["input"])
        ws.write_formula(r, 16, f"=SUM(E{r+1}:P{r+1})", F["total"])
        ws.write(r, 17, p["target_tahun"], F["td_num2"])
        baris_program[p["kode"]] = r + 1
        r += 1

    ws.freeze_panes(7, 4)
    ws.write(r + 1, 1,
             "Catatan: satuan mengikuti kolom Satuan. Untuk N-02 isikan kWh temuan; "
             "untuk N-03 isikan realisasi tagih dalam juta rupiah.", F["catatan"])
    return baris_program


# ===========================================================================
#  SHEET 4 — WORK PLAN (capaian per item, seluruhnya formula)
# ===========================================================================
def sheet_workplan(wb, F, baris_input: dict) -> None:
    ws = wb.add_worksheet("WORK PLAN")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["teal"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 7)
    ws.set_column(2, 2, 44)
    ws.set_column(3, 3, 11)
    ws.set_column(4, 4, 10)
    ws.set_column(5, 11, 11.5)
    ws.set_column(12, 14, 13)
    ws.set_column(15, 15, 13)
    ws.set_column(16, 16, 12)
    ws.set_column(17, 17, 26)
    banner(ws, F, "CAPAIAN PER ITEM WORK PLAN PENURUNAN SUSUT",
           f"Realisasi s/d {KPI['periode_data']} terhadap target bulanan dan target akhir tahun", 16)

    hdr = ["Kode", "Item Work Plan", "Satuan", "Kategori",
           "Target Tahun", "Target s/d Bln", "Realisasi s/d Bln",
           "Capaian YTD (%)", "Capaian thd Target Tahun (%)",
           "Sisa Target", "Kebutuhan / Bulan", "Run-rate Bulanan",
           "Faktor Kejar (x)", "kWh Selamat YTD", "Sisa Potensi kWh",
           "Status", "PIC"]
    ws.set_row(5, 34)
    for i, h in enumerate(hdr):
        ws.write(5, 1 + i, h, F["th_kiri"] if i == 1 else F["th"])

    bulan_sisa = 12 - MR
    r = 6
    for p in DATA["program"]:
        br = baris_input[p["kode"]]
        # Kolom E..P di INPUT REALISASI = bulan 1..12
        kol_akhir_real = chr(ord("E") + MR - 1)
        f_real = f"SUM('INPUT REALISASI'!E{br}:{kol_akhir_real}{br})"

        warna_kat = C["blue"] if p["kategori"] == "TEKNIS" else C["teal"]
        fmt_kode = wb.add_format({
            "font_name": "Segoe UI", "font_size": 9, "bold": True,
            "font_color": C["white"], "bg_color": warna_kat,
            "align": "center", "valign": "vcenter",
            "border": 1, "border_color": warna_kat})

        ws.write(r, 1, p["kode"], fmt_kode)
        ws.write(r, 2, p["nama"], F["td"])
        ws.write(r, 3, p["satuan"], F["td_c"])
        ws.write(r, 4, "Teknis" if p["kategori"] == "TEKNIS" else "Non-Teknis", F["td_c"])
        ws.write(r, 5, p["target_tahun"], F["td_num2"])
        ws.write(r, 6, p["target_ytd"], F["td_num2"])
        ws.write_formula(r, 7, f"={f_real}", F["td_num2"], p["realisasi_ytd"])
        ws.write_formula(r, 8, f"=IF(G{r+1}=0,0,H{r+1}/G{r+1}*100)", F["td_pct"],
                         p["capaian_ytd_persen"])
        ws.write_formula(r, 9, f"=IF(F{r+1}=0,0,H{r+1}/F{r+1}*100)", F["td_pct"],
                         p["capaian_thd_target_tahun_persen"])
        ws.write_formula(r, 10, f"=MAX(F{r+1}-H{r+1},0)", F["td_num2"], p["sisa_target"])
        ws.write_formula(r, 11, f"=K{r+1}/{bulan_sisa}", F["td_num2"],
                         p["kebutuhan_per_bulan_sisa"])
        ws.write_formula(r, 12, f"=H{r+1}/{MR}", F["td_num2"], p["run_rate_bulanan"])
        ws.write_formula(r, 13, f"=IF(M{r+1}=0,\"-\",L{r+1}/M{r+1})", F["td_num2"],
                         p["faktor_kejar"] if p["faktor_kejar"] else 0)
        ws.write_formula(r, 14, f"=H{r+1}*{p['kwh_selamat_per_unit']}", F["td_num"],
                         p["kwh_selamat_ytd"])
        ws.write_formula(r, 15, f"=K{r+1}*{p['kwh_selamat_per_unit']}", F["td_num"],
                         round(p["sisa_target"] * p["kwh_selamat_per_unit"]))
        ws.write_formula(
            r, 16,
            f'=IF(I{r+1}>=100,"TERCAPAI",IF(I{r+1}>=90,"WASPADA",'
            f'IF(I{r+1}>=75,"TERLAMBAT","KRITIS")))',
            F[f"badge_{p['status']}"], p["status"])
        ws.write(r, 17, p["pic"], F["td"])
        r += 1

    akhir = r - 1
    ws.write(r, 1, "", F["total_kiri"])
    ws.write(r, 2, "TOTAL / RATA-RATA", F["total_kiri"])
    ws.write(r, 3, "", F["total_kiri"]); ws.write(r, 4, "", F["total_kiri"])
    for col in (5, 6, 7):
        ws.write_blank(r, col, None, F["total"])
    ws.write_formula(r, 8, f"=AVERAGE(I7:I{akhir+1})", F["total_pct"])
    ws.write_formula(r, 9, f"=AVERAGE(J7:J{akhir+1})", F["total_pct"])
    for col in (10, 11, 12, 13):
        ws.write_blank(r, col, None, F["total"])
    ws.write_formula(r, 14, f"=SUM(O7:O{akhir+1})", F["total"])
    ws.write_formula(r, 15, f"=SUM(P7:P{akhir+1})", F["total"])
    ws.write_blank(r, 16, None, F["total"]); ws.write_blank(r, 17, None, F["total"])

    # Pewarnaan status otomatis (mengikuti formula, bukan nilai statis)
    for status, (fg, bg) in STATUS_WARNA.items():
        ws.conditional_format(6, 16, akhir, 16, {
            "type": "cell", "criteria": "equal to", "value": f'"{status}"',
            "format": wb.add_format({
                "font_name": "Segoe UI", "font_size": 8, "bold": True,
                "font_color": fg, "bg_color": bg, "align": "center",
                "border": 1, "border_color": bg})})

    ws.conditional_format(6, 8, akhir, 8, {
        "type": "3_color_scale",
        "min_color": C["red_l"], "mid_color": C["amber_l"], "max_color": C["green_l"],
        "min_type": "num", "min_value": 40, "mid_type": "num", "mid_value": 85,
        "max_type": "num", "max_value": 110})
    ws.conditional_format(6, 13, akhir, 13, {
        "type": "cell", "criteria": ">=", "value": 2,
        "format": wb.add_format({"bg_color": C["red_l"], "font_color": C["red"],
                                 "bold": True, "num_format": "#,##0.00",
                                 "border": 1, "border_color": C["grey_l"],
                                 "font_size": 9, "font_name": "Segoe UI",
                                 "align": "right"})})
    ws.conditional_format(6, 15, akhir, 15, {
        "type": "data_bar", "bar_color": C["orange"], "bar_solid": True})

    ws.freeze_panes(6, 3)
    ws.autofilter(5, 1, akhir, 17)
    ws.write(r + 2, 2,
             'FAKTOR KEJAR = kebutuhan per bulan tersisa dibagi run-rate bulanan saat ini. '
             'Nilai 1,0 berarti cukup mempertahankan kecepatan sekarang; nilai 3,0 berarti '
             'harus tiga kali lebih cepat. Item dengan faktor kejar >= 2 disorot merah dan '
             'wajib masuk rapat mingguan.', F["catatan"])


# ===========================================================================
#  SHEET 5 — ANALISIS SUSUT TEKNIS
# ===========================================================================
def sheet_teknis(wb, F) -> None:
    ws = wb.add_worksheet("ANALISIS TEKNIS")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["cyan"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 11)
    ws.set_column(2, 2, 20)
    ws.set_column(3, 14, 11.5)
    banner(ws, F, "ANALISIS SUSUT TEKNIS PER PENYULANG",
           "Profil jaringan, indeks prioritas penanganan, dan dekomposisi rugi teknis", 14)

    hdr = ["Kode", "Nama Penyulang", "Gardu", "Pelanggan", "Kapasitas (kVA)",
           "JTM (kms)", "JTR (kms)", "Susut (%)", "Unbalance (%)", "Cos phi",
           "Drop Tegangan (%)", "SR > 30 m", "Indeks Prioritas", "Kelas"]
    ws.set_row(5, 32)
    for i, h in enumerate(hdr):
        ws.write(5, 1 + i, h, F["th_kiri"] if i == 1 else F["th"])

    r = 6
    for p in sorted(DATA["penyulang"], key=lambda x: -x["indeks_prioritas"]):
        ws.write(r, 1, p["kode"], F["td_bold"])
        ws.write(r, 2, p["nama"], F["td"])
        ws.write(r, 3, p["jumlah_gardu"], F["td_num"])
        ws.write(r, 4, p["jumlah_pelanggan"], F["td_num"])
        ws.write(r, 5, p["kapasitas_kva"], F["td_num"])
        ws.write(r, 6, p["panjang_jtm_kms"], F["td_num1"])
        ws.write(r, 7, p["panjang_jtr_kms"], F["td_num1"])
        ws.write(r, 8, p["susut_persen"], F["td_pct"])
        ws.write(r, 9, p["unbalance_persen"], F["td_pct1"])
        ws.write(r, 10, p["cos_phi"], F["td_num2"])
        ws.write(r, 11, p["drop_tegangan_persen"], F["td_pct1"])
        ws.write(r, 12, p["sr_lebih_30m"], F["td_num"])
        ws.write(r, 13, p["indeks_prioritas"], F["td_num1"])
        kelas_fmt = {"KRITIS": "badge_KRITIS", "TINGGI": "badge_TERLAMBAT",
                     "SEDANG": "badge_WASPADA", "RENDAH": "badge_TERCAPAI"}
        ws.write(r, 14, p["kelas_prioritas"], F[kelas_fmt[p["kelas_prioritas"]]])
        r += 1

    akhir = r - 1
    for col, warna in ((8, C["red"]), (9, C["orange"]), (11, C["amber"]), (13, C["blue"])):
        ws.conditional_format(6, col, akhir, col, {
            "type": "data_bar", "bar_color": warna, "bar_solid": True})
    ws.conditional_format(6, 10, akhir, 10, {
        "type": "3_color_scale", "min_color": C["red_l"],
        "mid_color": C["amber_l"], "max_color": C["green_l"]})

    # --- Ambang batas acuan ---
    r += 2
    ws.write(r, 1, "AMBANG BATAS ACUAN (SPLN / praktik operasi distribusi)", F["seksi"])
    r += 1
    acuan = [
        ("Unbalance arus antar fasa", "<= 10%", "> 15% wajib penyeimbangan beban dalam 7 hari"),
        ("Cos phi (faktor daya)", ">= 0,90", "< 0,90 -> pasang kapasitor bank"),
        ("Drop tegangan ujung", "<= 5%", "> 5% -> uprating konduktor / trafo sisip"),
        ("Panjang SR", "<= 30 m", "> 30 m -> rugi SR signifikan, jadwalkan penggantian"),
        ("Pembebanan trafo", "<= 80%", "> 80% -> uprating atau trafo sisip"),
        ("Panjang JTR per gardu", "<= 350 m", "> 350 m -> pasang trafo sisip"),
    ]
    ws.set_row(r, 26)
    for i, h in enumerate(["Parameter", "Ambang Ideal"]):
        ws.write(r, 1 + i, h, F["th_kiri"])
    ws.merge_range(r, 3, r, 6, "Tindakan bila terlampaui", F["th_kiri"])
    r += 1
    for a in acuan:
        ws.set_row(r, 20)
        ws.write(r, 1, a[0], F["td"])
        ws.write(r, 2, a[1], F["td_c"])
        ws.merge_range(r, 3, r, 6, a[2], F["td_wrap"])
        r += 1

    # --- Blok komposisi susut (dipakai grafik donat DASHBOARD, baris 40-41) ---
    ws.write(38, 1, "KOMPOSISI SUSUT BULAN BERJALAN", F["seksi"])
    ws.write(39, 1, "Komponen", F["th_kiri"])
    ws.write(39, 2, "Persen", F["th"])
    ws.write(40, 1, "Susut Teknis", F["td"])
    ws.write(40, 2, KPI["susut_teknis_persen"], F["td_pct"])
    ws.write(41, 1, "Susut Non-Teknis", F["td"])
    ws.write(41, 2, KPI["susut_nonteknis_persen"], F["td_pct"])
    ws.write(42, 1, "TOTAL SUSUT", F["total_kiri"])
    ws.write_formula(42, 2, "=SUM(C41:C42)", F["total_pct"])

    # --- Dekomposisi rugi teknis per komponen ---
    ws.write(44, 1, "DEKOMPOSISI RUGI TEKNIS PER KOMPONEN JARINGAN", F["seksi"])
    ws.set_row(45, 26)
    for i, h in enumerate(["Komponen", "kWh Rugi / Bulan", "Porsi (%)",
                           "Nilai (Rp/bulan)", "Program penanganan"]):
        ws.write(45, 1 + i, h, F["th_kiri"])
    agg = {}
    for x in DATA["rugi_teknis"]:
        agg[x["komponen"]] = agg.get(x["komponen"], 0) + x["kwh_rugi"]
    total = sum(agg.values())
    label = {
        "trafo_distribusi": ("Trafo distribusi (rugi inti + belitan)", "T-01, T-03, T-09"),
        "jaringan_tegangan_rendah": ("Jaringan Tegangan Rendah (JTR)", "T-02, T-03"),
        "sambungan_rumah_app": ("Sambungan Rumah & APP", "T-04"),
        "jaringan_tegangan_menengah": ("Jaringan Tegangan Menengah (JTM)", "T-05, T-06, T-10"),
        "konektor_sambungan": ("Konektor & titik sambung", "T-07"),
    }
    rr = 46
    for k, v in sorted(agg.items(), key=lambda x: -x[1]):
        ws.write(rr, 1, label[k][0], F["td"])
        ws.write(rr, 2, v, F["td_num"])
        ws.write(rr, 3, round(v / total * 100, 2), F["td_pct"])
        ws.write(rr, 4, round(v * PARAM["tarif_rata_rata"]), F["td_rp"])
        ws.write(rr, 5, label[k][1], F["td_c"])
        rr += 1
    ws.write(rr, 1, "TOTAL RUGI TEKNIS", F["total_kiri"])
    ws.write_formula(rr, 2, f"=SUM(C47:C{rr})", F["total"])
    ws.write(rr, 3, 100, F["total_pct"])
    ws.write_formula(rr, 4, f"=SUM(E47:E{rr})", F["total"])
    ws.write_blank(rr, 5, None, F["total"])
    ws.conditional_format(46, 2, rr - 1, 2, {
        "type": "data_bar", "bar_color": C["blue"], "bar_solid": True})
    ws.freeze_panes(6, 3)


# ===========================================================================
#  SHEET 6 — P2TL
# ===========================================================================
def sheet_p2tl(wb, F) -> None:
    ws = wb.add_worksheet("P2TL")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["orange"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 10)
    ws.set_column(2, 8, 15)
    banner(ws, F, "PENERTIBAN PEMAKAIAN TENAGA LISTRIK (P2TL)",
           "Rekap pemeriksaan, temuan pelanggaran, dan efektivitas penagihan tagihan susulan", 9)

    bulanan = {}
    for x in DATA["p2tl"]:
        b = bulanan.setdefault(x["bulan"], {
            "periksa": 0, "temuan": 0, "kwh": 0, "tagsus": 0, "bayar": 0})
        b["periksa"] += x["jumlah_pemeriksaan"]
        b["temuan"] += x["jumlah_temuan"]
        b["kwh"] += x["kwh_temuan"]
        b["tagsus"] += x["rupiah_tagsus"]
        b["bayar"] += x["rupiah_terbayar"]

    ws.set_row(5, 30)
    hdr = ["Bulan", "Pemeriksaan", "Temuan", "Hit Rate (%)", "kWh Temuan",
           "Tagihan Susulan (Rp)", "Terbayar (Rp)", "Efektivitas Tagih (%)"]
    for i, h in enumerate(hdr):
        ws.write(5, 1 + i, h, F["th"])

    r = 6
    for m in sorted(bulanan):
        b = bulanan[m]
        ws.write(r, 1, BULAN[m - 1], F["td_bold"])
        ws.write(r, 2, b["periksa"], F["td_num"])
        ws.write(r, 3, b["temuan"], F["td_num"])
        ws.write_formula(r, 4, f"=IF(C{r+1}=0,0,D{r+1}/C{r+1}*100)", F["td_pct"])
        ws.write(r, 5, b["kwh"], F["td_num"])
        ws.write(r, 6, b["tagsus"], F["td_rp"])
        ws.write(r, 7, b["bayar"], F["td_rp"])
        ws.write_formula(r, 8, f"=IF(G{r+1}=0,0,H{r+1}/G{r+1}*100)", F["td_pct"])
        r += 1
    akhir = r - 1
    ws.write(r, 1, "TOTAL", F["total_kiri"])
    for col in (2, 3, 5, 6, 7):
        L = chr(ord("A") + col)
        ws.write_formula(r, col, f"=SUM({L}7:{L}{akhir+1})", F["total"])
    ws.write_formula(r, 4, f"=D{r+1}/C{r+1}*100", F["total_pct"])
    ws.write_formula(r, 8, f"=H{r+1}/G{r+1}*100", F["total_pct"])

    ws.conditional_format(6, 4, akhir, 4, {
        "type": "data_bar", "bar_color": C["green"], "bar_solid": True})
    ws.conditional_format(6, 8, akhir, 8, {
        "type": "3_color_scale", "min_color": C["red_l"],
        "mid_color": C["amber_l"], "max_color": C["green_l"]})

    # --- Rekap per golongan pelanggaran ---
    r += 2
    ws.write(r, 1, "REKAP PER GOLONGAN PELANGGARAN (s/d bulan berjalan)", F["seksi"])
    r += 1
    ws.set_row(r, 30)
    for i, h in enumerate(["Golongan", "Uraian", "Temuan", "kWh Temuan",
                           "Tagihan Susulan (Rp)", "Porsi kWh (%)"]):
        ws.write(r, 1 + i, h, F["th_kiri"] if i == 1 else F["th"])
    ws.set_column(2, 2, 42)
    gol = {}
    for x in DATA["p2tl"]:
        g = gol.setdefault(x["golongan"], {"ket": x["keterangan"], "t": 0, "k": 0, "rp": 0})
        g["t"] += x["jumlah_temuan"]; g["k"] += x["kwh_temuan"]; g["rp"] += x["rupiah_tagsus"]
    total_kwh = sum(g["k"] for g in gol.values())
    r += 1
    awal_gol = r
    for kode in sorted(gol):
        g = gol[kode]
        ws.write(r, 1, kode, F["td_bold"])
        ws.write(r, 2, g["ket"], F["td_wrap"])
        ws.write(r, 3, g["t"], F["td_num"])
        ws.write(r, 4, g["k"], F["td_num"])
        ws.write(r, 5, g["rp"], F["td_rp"])
        ws.write(r, 6, round(g["k"] / total_kwh * 100, 2), F["td_pct"])
        r += 1
    ws.conditional_format(awal_gol, 6, r - 1, 6, {
        "type": "data_bar", "bar_color": C["orange"], "bar_solid": True})

    ch = wb.add_chart({"type": "column"})
    ch.add_series({
        "name": "kWh temuan",
        "categories": f"=P2TL!$B$7:$B${akhir+1}",
        "values":     f"=P2TL!$F$7:$F${akhir+1}",
        "fill": {"color": C["viz1"]}, "gap": 45})
    ch.set_title({"name": "kWh Temuan P2TL per Bulan",
                  "name_font": {"name": "Segoe UI", "size": 11, "bold": True}})
    ch.set_legend({"none": True})
    ch.set_x_axis({"num_font": {"name": "Segoe UI", "size": 8}})
    ch.set_y_axis({"num_font": {"name": "Segoe UI", "size": 8},
                   "major_gridlines": {"visible": True, "line": {"color": C["grid"]}}})
    ch.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch.set_size({"width": 470, "height": 300})
    ws.insert_chart(r + 2, 1, ch)

    ch_b = wb.add_chart({"type": "line"})
    ch_b.add_series({
        "name": "Efektivitas tagih (%)",
        "categories": f"=P2TL!$B$7:$B${akhir+1}",
        "values":     f"=P2TL!$I$7:$I${akhir+1}",
        "line": {"color": C["viz2"], "width": 2.25},
        "marker": {"type": "circle", "size": 7,
                   "fill": {"color": C["viz2"]}, "border": {"none": True}}})
    ch_b.set_title({"name": "Efektivitas Penagihan Tagihan Susulan",
                    "name_font": {"name": "Segoe UI", "size": 11, "bold": True}})
    ch_b.set_legend({"none": True})
    ch_b.set_x_axis({"num_font": {"name": "Segoe UI", "size": 8}})
    ch_b.set_y_axis({"min": 0, "max": 100, "num_font": {"name": "Segoe UI", "size": 8},
                     "major_gridlines": {"visible": True, "line": {"color": C["grid"]}}})
    ch_b.set_chartarea({"border": {"color": C["grey_l"]}, "fill": {"color": C["white"]}})
    ch_b.set_size({"width": 470, "height": 300})
    ws.insert_chart(r + 2, 9, ch_b)
    ws.freeze_panes(6, 2)


# ===========================================================================
#  SHEET 7 — RENCANA AKSI
# ===========================================================================
def sheet_aksi(wb, F) -> None:
    ws = wb.add_worksheet("RENCANA AKSI")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["red"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 5)
    ws.set_column(2, 2, 14)
    ws.set_column(3, 3, 8)
    ws.set_column(4, 4, 50)
    ws.set_column(5, 5, 40)
    ws.set_column(6, 10, 13)
    ws.set_column(11, 11, 26)
    ws.set_column(12, 12, 12)
    banner(ws, F, "RENCANA AKSI PERCEPATAN PENCAPAIAN TARGET",
           "Apa yang harus dilakukan Sep-Des untuk menutup gap menuju target akhir tahun", 12)

    ws.set_row(5, 34)
    hdr = ["No", "Prioritas", "Kategori", "Aksi yang harus dilakukan",
           "Akar masalah", "Sisa Volume", "Kebutuhan/Bulan",
           "Dampak kWh/Bulan", "Dampak Rp (sisa tahun)", "Progres (%)",
           "PIC", "Target Selesai"]
    for i, h in enumerate(hdr):
        ws.write(5, 1 + i, h, F["th_kiri"] if i in (3, 4) else F["th"])

    prio_warna = {
        "SANGAT TINGGI": (C["white"], C["red"]),
        "TINGGI": (C["white"], C["orange"]),
        "SEDANG": (C["ink"], C["amber_l"]),
        "RUTIN": (C["ink"], C["grey_l"]),
    }
    r = 6
    for a in DATA["action_plan"]:
        fg, bg = prio_warna[a["prioritas"]]
        fmt_prio = wb.add_format({
            "font_name": "Segoe UI", "font_size": 8, "bold": True,
            "font_color": fg, "bg_color": bg, "align": "center",
            "valign": "vcenter", "border": 1, "border_color": bg, "text_wrap": True})
        ws.set_row(r, 44)
        ws.write(r, 1, a["no"], F["td_c"])
        ws.write(r, 2, a["prioritas"], fmt_prio)
        ws.write(r, 3, "Teknis" if a["kategori"] == "TEKNIS" else "Non-Tek", F["td_c"])
        ws.write(r, 4, a["aksi"], F["td_wrap"])
        ws.write(r, 5, a["akar_masalah"], F["td_wrap"])
        ws.write(r, 6, a["sisa_volume"], F["td_num2"])
        ws.write(r, 7, a["kebutuhan_per_bulan"], F["td_num2"])
        ws.write(r, 8, a["dampak_kwh_bulan"], F["td_num"])
        ws.write(r, 9, a["dampak_rupiah_sisa_tahun"], F["td_rpjt"])
        ws.write(r, 10, a["progres_persen"], F["td_pct1"])
        ws.write(r, 11, a["pic"], F["td"])
        ws.write(r, 12, a["target_selesai"], F["td_c"])
        r += 1
    akhir = r - 1
    ws.write(r, 1, "", F["total_kiri"]); ws.write(r, 2, "", F["total_kiri"])
    ws.write(r, 3, "", F["total_kiri"])
    ws.write(r, 4, "TOTAL DAMPAK RENCANA AKSI", F["total_kiri"])
    ws.write_blank(r, 5, None, F["total"])
    ws.write_blank(r, 6, None, F["total"]); ws.write_blank(r, 7, None, F["total"])
    ws.write_formula(r, 8, f"=SUM(I7:I{akhir+1})", F["total"])
    ws.write_formula(r, 9, f"=SUM(J7:J{akhir+1})", F["total"])
    ws.write_formula(r, 10, f"=AVERAGE(K7:K{akhir+1})", F["total_pct"])
    ws.write_blank(r, 11, None, F["total"]); ws.write_blank(r, 12, None, F["total"])

    ws.conditional_format(6, 10, akhir, 10, {
        "type": "data_bar", "bar_color": C["green"], "bar_solid": True,
        "min_type": "num", "min_value": 0, "max_type": "num", "max_value": 100})
    ws.conditional_format(6, 8, akhir, 8, {
        "type": "data_bar", "bar_color": C["cyan"], "bar_solid": True})

    gap = KPI["skenario_a_kumulatif"]["gap_kwh_harus_diselamatkan"]
    ws.write(r + 2, 4,
             f"Gap yang harus ditutup Sep-Des adalah {gap:,.0f} kWh".replace(",", ".") +
             f" (skenario susut kumulatif). Total dampak rencana aksi di atas dihitung dari "
             f"sisa target tiap program dikalikan faktor kWh selamat per satuan.", F["catatan"])
    ws.freeze_panes(6, 5)
    ws.autofilter(5, 1, akhir, 12)


# ===========================================================================
#  SHEET 8 — SIMULASI TARGET
# ===========================================================================
def sheet_simulasi(wb, F) -> None:
    ws = wb.add_worksheet("SIMULASI TARGET")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["green"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 46)
    ws.set_column(2, 4, 18)
    ws.set_column(5, 5, 44)
    banner(ws, F, "SIMULASI PENCAPAIAN TARGET AKHIR TAHUN",
           "Dua tafsir target 5,85% dan konsekuensi operasionalnya", 6)

    A = KPI["skenario_a_kumulatif"]
    B = KPI["skenario_b_exit_rate"]

    fmt_in = wb.add_format({
        "font_name": "Segoe UI", "font_size": 11, "bold": True,
        "bg_color": "#FFFBEB", "border": 1, "border_color": "#FCD34D",
        "align": "center", "valign": "vcenter", "num_format": "#,##0.00"})

    r = 5
    ws.write(r, 1, "ASUMSI YANG BISA DIUBAH", F["seksi"]); r += 1
    asumsi = [
        ("Target susut akhir tahun (%)", PARAM["target_susut_akhir_tahun"]),
        ("Susut bulan terakhir realisasi (%)", KPI["susut_bulan_ini_persen"]),
        ("kWh salur kumulatif s/d bulan realisasi", KPI["kwh_salur_ytd"]),
        ("kWh susut kumulatif s/d bulan realisasi", KPI["kwh_susut_ytd"]),
        ("Proyeksi kWh salur Sep-Des", sum(
            n["kwh_salur"] for n in DATA["neraca_energi"] if n["status_data"] == "PROYEKSI")),
        ("Proyeksi kWh salur Desember", DATA["neraca_energi"][11]["kwh_salur"]),
        ("Tarif rata-rata (Rp/kWh)", PARAM["tarif_rata_rata"]),
    ]
    baris_asumsi = {}
    for nama, nilai in asumsi:
        ws.write(r, 1, nama, F["td"])
        ws.write(r, 2, nilai, fmt_in)
        baris_asumsi[nama] = r + 1
        r += 1

    tgt = baris_asumsi["Target susut akhir tahun (%)"]
    sus = baris_asumsi["Susut bulan terakhir realisasi (%)"]
    sal = baris_asumsi["kWh salur kumulatif s/d bulan realisasi"]
    sut = baris_asumsi["kWh susut kumulatif s/d bulan realisasi"]
    sis = baris_asumsi["Proyeksi kWh salur Sep-Des"]
    des = baris_asumsi["Proyeksi kWh salur Desember"]
    trf = baris_asumsi["Tarif rata-rata (Rp/kWh)"]

    r += 2
    ws.write(r, 1, "SKENARIO A — target dimaknai SUSUT KUMULATIF (YTD) akhir tahun", F["seksi"])
    ws.write(r, 5, "Tafsir yang dipakai dalam evaluasi kinerja RKAP", F["catatan"])
    r += 1
    ws.set_row(r, 26)
    for i, h in enumerate(["Perhitungan", "Nilai", "Satuan"]):
        ws.write(r, 1 + i, h, F["th_kiri"] if i == 0 else F["th"])
    r += 1
    rows_a = [
        ("kWh susut maksimum setahun agar target tercapai",
         f"=(C{sal}+C{sis})*C{tgt}/100", "kWh", F["td_num"]),
        ("kWh susut yang masih boleh terjadi Sep-Des",
         f"=C{r+1}-C{sut}", "kWh", F["td_num"]),
        ("Setara susut Sep-Des maksimum",
         f"=C{r+2}/C{sis}*100", "%", F["td_pct"]),
        ("kWh susut Sep-Des bila tanpa aksi tambahan",
         f"=C{sis}*C{sus}/100", "kWh", F["td_num"]),
        ("GAP kWh yang harus diselamatkan",
         f"=C{r+4}-C{r+2}", "kWh", F["td_num"]),
        ("GAP per bulan (4 bulan tersisa)",
         f"=C{r+5}/4", "kWh/bulan", F["td_num"]),
        ("Nilai finansial gap",
         f"=C{r+5}*C{trf}", "Rp", F["td_rp"]),
    ]
    for nama, rumus, sat, fmt in rows_a:
        ws.write(r, 1, nama, F["td"])
        ws.write_formula(r, 2, rumus, fmt)
        ws.write(r, 3, sat, F["td_c"])
        r += 1
    baris_gap_a = r - 2

    r += 1
    ws.write(r, 1, "SKENARIO B — target dimaknai SUSUT BULAN DESEMBER (exit rate)", F["seksi"])
    ws.write(r, 5, "Tafsir yang dipakai untuk menilai 'kondisi akhir' jaringan", F["catatan"])
    r += 1
    ws.set_row(r, 26)
    for i, h in enumerate(["Perhitungan", "Nilai", "Satuan"]):
        ws.write(r, 1 + i, h, F["th_kiri"] if i == 0 else F["th"])
    r += 1
    rows_b = [
        ("Penurunan yang dibutuhkan dari bulan terakhir",
         f"=C{sus}-C{tgt}", "pp", F["td_num2"]),
        ("kWh susut maksimum di bulan Desember",
         f"=C{des}*C{tgt}/100", "kWh", F["td_num"]),
        ("kWh susut Desember bila tanpa aksi tambahan",
         f"=C{des}*C{sus}/100", "kWh", F["td_num"]),
        ("GAP kWh yang harus diselamatkan di Desember",
         f"=C{r+3}-C{r+2}", "kWh", F["td_num"]),
        ("Nilai finansial gap",
         f"=C{r+4}*C{trf}", "Rp", F["td_rp"]),
    ]
    for nama, rumus, sat, fmt in rows_b:
        ws.write(r, 1, nama, F["td"])
        ws.write_formula(r, 2, rumus, fmt)
        ws.write(r, 3, sat, F["td_c"])
        r += 1

    r += 1
    ws.write(r, 1, "UJI KECUKUPAN: apakah sisa work plan mampu menutup gap?", F["seksi"])
    r += 1
    ws.write(r, 1, "Sisa potensi kWh seluruh work plan (Sep-Des)", F["td"])
    ws.write_formula(r, 2, "='WORK PLAN'!P29", F["td_num"], KPI["kwh_selamat_sisa"])
    ws.write(r, 3, "kWh", F["td_c"])
    baris_sisa = r + 1
    r += 1
    ws.write(r, 1, "Gap skenario A", F["td"])
    ws.write_formula(r, 2, f"=C{baris_gap_a}", F["td_num"], A["gap_kwh_harus_diselamatkan"])
    ws.write(r, 3, "kWh", F["td_c"])
    baris_gap_ref = r + 1
    r += 1
    ws.write(r, 1, "Rasio kecukupan (sisa potensi / gap)", F["td_bold"])
    ws.write_formula(r, 2, f"=C{baris_sisa}/C{baris_gap_ref}", F["td_num2"])
    ws.write(r, 3, "x", F["td_c"])
    r += 1
    fmt_verdict = wb.add_format({
        "font_name": "Segoe UI", "font_size": 11, "bold": True,
        "font_color": C["white"], "bg_color": C["green"],
        "align": "center", "valign": "vcenter", "text_wrap": True})
    ws.set_row(r, 34)
    sisa_txt = f"{KPI['kwh_selamat_sisa']:,.0f}".replace(",", ".")
    gap_txt = f"{A['gap_kwh_harus_diselamatkan']:,.0f}".replace(",", ".")
    rasio = KPI["kwh_selamat_sisa"] / A["gap_kwh_harus_diselamatkan"]
    ws.merge_range(r, 1, r, 5,
                   f"PUTUSAN: sisa potensi work plan {sisa_txt} kWh vs gap {gap_txt} kWh "
                   f"= {rasio:.2f}x  ->  TARGET MASIH BISA DICAPAI, syaratnya seluruh "
                   "program KRITIS dieksekusi penuh sampai Desember.",
                   fmt_verdict)

    r += 3
    ws.write(r, 1, "CATATAN PENTING", F["seksi"]); r += 1
    for teks in [
        "Skenario A jauh lebih berat: susut Sep-Des harus turun ke "
        f"{A['susut_sisa_diizinkan_persen']:.2f}% padahal bulan terakhir masih "
        f"{KPI['susut_bulan_ini_persen']:.2f}%. Pastikan dulu ke UP3 tafsir mana yang dipakai "
        "untuk menilai kinerja unit, karena konsekuensi kerjanya berbeda jauh.",
        "Skenario B hanya memerlukan penurunan "
        f"{B['penurunan_pp_dibutuhkan']:.2f} pp pada bulan Desember dan realistis dicapai "
        "dengan menuntaskan program yang berstatus KRITIS.",
        "Ubah sel kuning pada blok ASUMSI untuk menguji what-if: mis. bila proyeksi kWh salur "
        "naik karena beban proyek IKN, atau bila target direvisi UP3.",
    ]:
        ws.set_row(r, 30)
        ws.merge_range(r, 1, r, 5, "•  " + teks, F["teks"])
        r += 1


# ===========================================================================
#  SHEET 9 — DATA GRAFIK (sumber grafik dashboard)
# ===========================================================================
def sheet_data_grafik(wb, F) -> None:
    ws = wb.add_worksheet("DATA GRAFIK")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["grey"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 34)
    ws.set_column(2, 2, 16)
    ws.set_column(5, 5, 30)
    ws.set_column(6, 6, 16)
    ws.set_column(9, 9, 24)
    ws.set_column(10, 10, 12)
    ws.set_column(13, 13, 16)
    ws.set_column(14, 14, 12)
    ws.write(1, 1, "SUMBER DATA GRAFIK DASHBOARD — jangan diubah manual", F["seksi"])

    # A. 10 program dengan sisa potensi kWh terbesar
    ws.write(2, 1, "Program", F["th_kiri"]); ws.write(2, 2, "Sisa Potensi kWh", F["th"])
    top = sorted(DATA["program"],
                 key=lambda p: -(p["sisa_target"] * p["kwh_selamat_per_unit"]))[:10]
    for i, p in enumerate(top):
        ws.write(3 + i, 1, f"{p['kode']}  {p['nama'][:34]}", F["td"])
        ws.write(3 + i, 2, round(p["sisa_target"] * p["kwh_selamat_per_unit"]), F["td_num"])

    # B. Komponen rugi teknis
    ws.write(2, 5, "Komponen Rugi Teknis", F["th_kiri"]); ws.write(2, 6, "kWh", F["th"])
    agg = {}
    for x in DATA["rugi_teknis"]:
        agg[x["komponen"]] = agg.get(x["komponen"], 0) + x["kwh_rugi"]
    nama_komp = {
        "trafo_distribusi": "Trafo distribusi",
        "jaringan_tegangan_rendah": "JTR",
        "sambungan_rumah_app": "Sambungan Rumah & APP",
        "jaringan_tegangan_menengah": "JTM",
        "konektor_sambungan": "Konektor",
    }
    for i, (k, v) in enumerate(sorted(agg.items(), key=lambda x: -x[1])):
        ws.write(3 + i, 5, nama_komp[k], F["td"])
        ws.write(3 + i, 6, v, F["td_num"])

    # C. Peringkat penyulang
    ws.write(2, 9, "Penyulang", F["th_kiri"]); ws.write(2, 10, "Susut (%)", F["th"])
    for i, p in enumerate(sorted(DATA["penyulang"], key=lambda x: -x["susut_persen"])):
        ws.write(3 + i, 9, f"{p['kode']} {p['nama']}", F["td"])
        ws.write(3 + i, 10, p["susut_persen"], F["td_pct"])

    # D. Capaian per kategori
    ws.write(2, 13, "Kategori", F["th_kiri"]); ws.write(2, 14, "Capaian (%)", F["th"])
    for i, (nama, kat) in enumerate([("Teknis", "TEKNIS"), ("Non-Teknis", "NON_TEKNIS")]):
        sub = [p for p in DATA["program"] if p["kategori"] == kat]
        ws.write(3 + i, 13, nama, F["td"])
        ws.write(3 + i, 14,
                 round(sum(p["capaian_ytd_persen"] for p in sub) / len(sub), 2), F["td_pct"])


# ===========================================================================
#  SHEET 10 — PANDUAN
# ===========================================================================
def sheet_panduan(wb, F) -> None:
    ws = wb.add_worksheet("PANDUAN")
    ws.hide_gridlines(2)
    ws.set_tab_color(C["ink"])
    ws.set_column(0, 0, 2)
    ws.set_column(1, 1, 26)
    ws.set_column(2, 2, 96)
    banner(ws, F, "PANDUAN PENGGUNAAN WORKBOOK",
           "Alur kerja bulanan, arti tiap sheet, dan definisi istilah", 6)

    r = 5
    ws.write(r, 1, "ALUR KERJA BULANAN", F["seksi"]); r += 1
    langkah = [
        ("Langkah 1 — tiap awal bulan",
         "Buka sheet NERACA ENERGI. Isi kWh Salur dan kWh Jual bulan yang baru tutup, "
         "lalu ubah kolom Status dari PROYEKSI menjadi REALISASI."),
        ("Langkah 2",
         "Buka sheet INPUT REALISASI. Isi realisasi tiap item work plan pada kolom bulan "
         "bersangkutan. Hanya sel kuning yang boleh diketik."),
        ("Langkah 3",
         "Buka sheet WORK PLAN. Kolom Capaian, Sisa Target, dan Faktor Kejar berubah otomatis. "
         "Perhatikan item berstatus KRITIS dan Faktor Kejar >= 2."),
        ("Langkah 4",
         "Buka sheet SIMULASI TARGET. Perbarui asumsi kWh salur bila proyeksi berubah, "
         "lalu baca ulang berapa gap yang tersisa."),
        ("Langkah 5",
         "Buka sheet RENCANA AKSI. Perbarui kolom Progres dan status. Bawa item prioritas "
         "SANGAT TINGGI ke rapat mingguan unit."),
        ("Langkah 6",
         "Buka sheet DASHBOARD untuk bahan laporan ke UP3. Sheet ini sudah siap cetak "
         "(A4 landscape, 1 halaman lebar)."),
    ]
    for judul, isi in langkah:
        ws.set_row(r, 34)
        ws.write(r, 1, judul, F["td_bold"])
        ws.write(r, 2, isi, F["td_wrap"])
        r += 1

    r += 1
    ws.write(r, 1, "ARTI TIAP SHEET", F["seksi"]); r += 1
    sheets = [
        ("DASHBOARD", "Ringkasan satu layar: kartu KPI, tren susut, komposisi, program dengan gap terbesar."),
        ("NERACA ENERGI", "Basis perhitungan susut: kWh salur vs kWh jual per bulan."),
        ("INPUT REALISASI", "Satu-satunya tempat mengetik realisasi bulanan work plan."),
        ("WORK PLAN", "Capaian per item terhadap target bulanan dan target akhir tahun."),
        ("ANALISIS TEKNIS", "Profil penyulang, indeks prioritas, dekomposisi rugi teknis, ambang batas acuan."),
        ("P2TL", "Rekap pemeriksaan, temuan, dan efektivitas penagihan tagihan susulan."),
        ("RENCANA AKSI", "Daftar aksi konkret Sep-Des beserta dampak kWh dan PIC."),
        ("SIMULASI TARGET", "Kalkulator what-if dua tafsir target akhir tahun."),
        ("DATA GRAFIK", "Sumber angka grafik dashboard. Tidak perlu diubah manual."),
    ]
    for nama, isi in sheets:
        ws.write(r, 1, nama, F["td_bold"])
        ws.write(r, 2, isi, F["td_wrap"])
        r += 1

    r += 1
    ws.write(r, 1, "DEFINISI ISTILAH", F["seksi"]); r += 1
    istilah = [
        ("Susut distribusi", "(kWh Salur - kWh Jual) / kWh Salur x 100%."),
        ("Susut teknis", "Rugi alamiah pada trafo, JTM, JTR, SR, dan konektor akibat I^2R "
                         "dan rugi inti. Tidak bisa nol, hanya bisa ditekan."),
        ("Susut non-teknis", "Energi tersalur yang tidak tertagih: pelanggaran pemakaian, "
                             "meter rusak/lambat, kesalahan baca, PJU ilegal, kesalahan administrasi."),
        ("Faktor kejar", "Kebutuhan volume per bulan tersisa dibagi run-rate bulanan saat ini. "
                         ">= 2 berarti harus dua kali lebih cepat dari kecepatan sekarang."),
        ("kWh selamat", "Perkiraan energi yang tidak jadi hilang karena satu satuan program "
                        "dikerjakan. Faktor konversi ada di kolom kwh_selamat_per_unit."),
        ("Unbalance", "Ketidakseimbangan arus antar fasa. Menimbulkan arus netral dan rugi tambahan."),
        ("DLPD", "Daftar Langganan Perlu Diperhatikan — rekening dengan stand meter anomali."),
        ("P2TL", "Penertiban Pemakaian Tenaga Listrik."),
        ("Tagihan susulan", "Tagihan atas pelanggaran hasil P2TL. Baru menurunkan susut "
                            "setelah benar-benar tertagih."),
    ]
    for nama, isi in istilah:
        ws.set_row(r, 28)
        ws.write(r, 1, nama, F["td_bold"])
        ws.write(r, 2, isi, F["td_wrap"])
        r += 1

    r += 1
    ws.write(r, 1, "SUMBER DATA", F["seksi"]); r += 1
    sumber = [
        ("kWh salur", "XPower / EIS-Susut — pembacaan APP outgoing penyulang di GI."),
        ("kWh jual", "AP2T / TUL — rekening terbit bulan berjalan."),
        ("Realisasi program teknis", "Laporan harian regu pemeliharaan & aplikasi Gardu/JDN."),
        ("Realisasi P2TL", "Aplikasi P2TL — berita acara pemeriksaan dan tagihan susulan."),
        ("Unbalance, cos phi, tegangan", "SCADA, AMR gardu, dan hasil pengukuran manual."),
        ("Data aset jaringan", "Aplikasi jaringan distribusi (panjang JTM/JTR, gardu, SR)."),
    ]
    for nama, isi in sumber:
        ws.write(r, 1, nama, F["td_bold"])
        ws.write(r, 2, isi, F["td_wrap"])
        r += 1

    r += 2
    fmt_warn = wb.add_format({
        "font_name": "Segoe UI", "font_size": 10, "bold": True,
        "font_color": "#92400E", "bg_color": "#FEF3C7", "text_wrap": True,
        "valign": "vcenter", "border": 1, "border_color": "#FCD34D", "indent": 1})
    ws.set_row(r, 46)
    ws.merge_range(r, 1, r, 2, META["catatan"], fmt_warn)


# ===========================================================================
def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb = xlsxwriter.Workbook(str(OUT), {"nan_inf_to_errors": True})
    # Tanggal dibuat sengaja diikat ke periode data, bukan ke waktu build.
    # Tanpa ini setiap build menghasilkan berkas yang berbeda hanya karena
    # stempel waktunya, sehingga riwayat git penuh perubahan semu.
    wb.set_properties({
        "title": "Dashboard Monitoring Susut ULP Samboja",
        "subject": "Monitoring susut teknis & non-teknis",
        "author": UNIT["nama"], "company": UNIT["up3"],
        "comments": META["catatan"],
        "created": dt.datetime(META["tahun"], MR, 1),
    })
    F = buat_format(wb)

    sheet_dashboard(wb, F)
    sheet_neraca(wb, F)
    baris_input = sheet_input(wb, F)
    sheet_workplan(wb, F, baris_input)
    sheet_teknis(wb, F)
    sheet_p2tl(wb, F)
    sheet_aksi(wb, F)
    sheet_simulasi(wb, F)
    sheet_data_grafik(wb, F)
    sheet_panduan(wb, F)

    wb.close()
    print(f"[OK] Dashboard Excel -> {OUT}  ({OUT.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
