# -*- coding: utf-8 -*-
"""
Memeriksa konsistensi berkas master di data/master/ sebelum dipakai.

Jalankan setiap kali selesai menyunting CSV:
    python3 scripts/validate_master.py

Keluaran:
  ✗ GALAT     — harus diperbaiki, data tidak akan terhitung benar
  ⚠ PERINGATAN — mungkin wajar, tetapi sebaiknya diperiksa ulang
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dataset as ds  # noqa: E402

GALAT: list[str] = []
PERINGATAN: list[str] = []


def galat(pesan: str) -> None:
    """Catat galat. Pesan yang persis sama hanya dicatat sekali, tetapi
    jumlah kemunculannya ikut dilaporkan agar tidak menyesatkan."""
    GALAT.append(pesan)


def peringatan(pesan: str) -> None:
    PERINGATAN.append(pesan)


def galat_kelompok(pola: str, daftar: list) -> None:
    """Satu pesan untuk banyak baris bermasalah yang sejenis.

    Menghindari 12 baris 'kwh_salur harus lebih besar dari nol' saat kerangka
    kosong baru mulai diisi — jauh lebih mudah dibaca sebagai satu baris."""
    if not daftar:
        return
    isi = ", ".join(str(x) for x in daftar[:12])
    if len(daftar) > 12:
        isi += f", … ({len(daftar)} seluruhnya)"
    galat(f"{pola}: {isi}")


def ringkas(pesan_list: list[str]) -> list[str]:
    """Gabungkan pesan kembar menjadi satu baris beserta jumlahnya."""
    urut: list[str] = []
    hitung: dict[str, int] = {}
    for p in pesan_list:
        if p not in hitung:
            urut.append(p)
        hitung[p] = hitung.get(p, 0) + 1
    return [p if hitung[p] == 1 else f"{p}  (terjadi {hitung[p]}×)" for p in urut]


def selisih_persen(a: float, b: float) -> float:
    return abs(a - b) / b * 100 if b else 0.0


def fmt(v: float, desimal: int = 1) -> str:
    """Angka gaya Indonesia: pemisah ribuan titik, desimal koma."""
    return f"{v:,.{desimal}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


# ---------------------------------------------------------------------------
def periksa_kolom(nama: str, baris: list[dict], wajib: set[str],
                  boleh_kosong: bool = False) -> bool:
    """Pastikan berkas punya kolom yang dibutuhkan.

    `boleh_kosong` untuk berkas yang wajar belum terisi di awal — kekosongannya
    dilaporkan sebagai peringatan, bukan galat yang menghentikan build."""
    if not baris:
        if boleh_kosong:
            peringatan(f"{nama}: belum ada satu pun baris data.")
        else:
            galat(f"{nama}: tidak ada satu pun baris data.")
        return False
    kurang = wajib - set(baris[0].keys())
    if kurang:
        galat(f"{nama}: kolom hilang → {', '.join(sorted(kurang))}")
        return False
    return True


def periksa_unit() -> None:
    baris = ds.baca_csv("unit.csv")
    if len(baris) != 1:
        galat(f"unit.csv: harus berisi tepat satu baris, ditemukan {len(baris)}.")
    for k in ("kode", "nama", "up3", "uid"):
        if not baris[0].get(k, "").strip():
            galat(f"unit.csv: kolom '{k}' kosong.")


def periksa_parameter() -> None:
    wajib = {"tarif_rata_rata", "target_susut_akhir_tahun", "baseline_susut_2025",
             "ambang_tercapai", "ambang_waspada", "ambang_terlambat"}
    kurang = wajib - set(ds.PARAM)
    if kurang:
        galat(f"parameter.csv: parameter wajib belum ada → {', '.join(sorted(kurang))}")
    if ds.PARAM.get("tarif_rata_rata", 0) <= 0:
        galat("parameter.csv: tarif_rata_rata harus lebih besar dari nol.")
    t = ds.PARAM.get("target_susut_akhir_tahun", 0)
    if not 0 < t < 25:
        galat(f"parameter.csv: target_susut_akhir_tahun ({t}) di luar rentang wajar 0–25%.")
    if not (ds.PARAM.get("ambang_tercapai", 100) > ds.PARAM.get("ambang_waspada", 90)
            > ds.PARAM.get("ambang_terlambat", 75)):
        galat("parameter.csv: ambang status harus menurun "
              "(tercapai > waspada > terlambat).")


def periksa_penyulang() -> set[str]:
    baris = ds.baca_csv("penyulang.csv")
    if not periksa_kolom("penyulang.csv", baris, {
            "kode", "nama", "jumlah_gardu", "kapasitas_kva", "panjang_jtm_kms",
            "panjang_jtr_kms", "jumlah_pelanggan", "susut_persen",
            "unbalance_persen", "cos_phi", "drop_tegangan_persen", "sr_lebih_30m"}):
        return set()

    kode_set: set[str] = set()
    for b in baris:
        k = b["kode"].strip()
        if not k:
            galat("penyulang.csv: ada baris tanpa kode.")
            continue
        if k in kode_set:
            galat(f"penyulang.csv: kode '{k}' muncul lebih dari sekali.")
        kode_set.add(k)

        plg = ds.bulat(b["jumlah_pelanggan"], 0) or 0
        if plg <= 0:
            galat(f"penyulang.csv [{k}]: jumlah_pelanggan harus lebih besar dari nol.")
        susut = ds.angka(b["susut_persen"], 0.0) or 0.0
        if not 0 <= susut < 30:
            galat(f"penyulang.csv [{k}]: susut_persen {susut} di luar rentang wajar 0–30%.")
        cos = ds.angka(b["cos_phi"], 0.0) or 0.0
        if not 0.5 <= cos <= 1.0:
            galat(f"penyulang.csv [{k}]: cos_phi {cos} di luar rentang wajar 0,5–1,0.")
        unb = ds.angka(b["unbalance_persen"], 0.0) or 0.0
        if not 0 <= unb <= 100:
            galat(f"penyulang.csv [{k}]: unbalance_persen {unb} di luar rentang 0–100%.")
        sr = ds.bulat(b["sr_lebih_30m"], 0) or 0
        if sr > plg:
            galat(f"penyulang.csv [{k}]: sr_lebih_30m ({sr}) melebihi "
                  f"jumlah_pelanggan ({plg}).")

    # Cocokkan jumlah agregat dengan parameter unit
    for kolom, kunci, satuan in (
        ("jumlah_pelanggan", "jumlah_pelanggan", "pelanggan"),
        ("jumlah_gardu", "jumlah_gardu", "gardu"),
    ):
        total = sum(ds.bulat(b[kolom], 0) or 0 for b in baris)
        acuan = ds.PARAM.get(kunci)
        if acuan and selisih_persen(total, acuan) > 2:
            peringatan(f"Jumlah {satuan} pada penyulang.csv ({fmt(total, 0)}) berbeda "
                       f"{fmt(selisih_persen(total, acuan))}% dari parameter.csv "
                       f"({fmt(acuan, 0)}).")

    for kolom, kunci in (("panjang_jtm_kms", "panjang_jtm_kms"),
                         ("panjang_jtr_kms", "panjang_jtr_kms")):
        total = sum(ds.angka(b[kolom], 0.0) or 0.0 for b in baris)
        acuan = ds.PARAM.get(kunci)
        if acuan and selisih_persen(total, acuan) > 5:
            peringatan(f"Total {kolom} pada penyulang.csv ({fmt(total)}) berbeda "
                       f"{fmt(selisih_persen(total, acuan))}% dari parameter.csv "
                       f"({fmt(acuan)}).")

    jml = ds.PARAM.get("jumlah_penyulang")
    if jml and int(jml) != len(baris):
        peringatan(f"parameter.csv menyebut {int(jml)} penyulang, "
                   f"tetapi penyulang.csv berisi {len(baris)} baris.")
    return kode_set


def periksa_neraca() -> None:
    baris = ds.baca_csv("neraca.csv")
    if not periksa_kolom("neraca.csv", baris, {
            "bulan", "status_data", "kwh_salur", "kwh_jual",
            "target_persen", "porsi_teknis"}):
        return
    if len(baris) != 12:
        galat(f"neraca.csv: harus berisi 12 baris (satu per bulan), "
              f"ditemukan {len(baris)}.")

    bulan_ada = set()
    realisasi_bulan = []
    salur_kosong: list[int] = []
    jual_kosong: list[int] = []
    for b in baris:
        m = ds.bulat(b["bulan"], 0) or 0
        if not 1 <= m <= 12:
            galat(f"neraca.csv: nomor bulan '{b['bulan']}' tidak sah.")
            continue
        if m in bulan_ada:
            galat(f"neraca.csv: bulan {m} muncul lebih dari sekali.")
        bulan_ada.add(m)

        status = b["status_data"].strip().upper()
        if status not in ("REALISASI", "PROYEKSI"):
            galat(f"neraca.csv [bulan {m}]: status_data harus REALISASI atau "
                  f"PROYEKSI, ditemukan '{b['status_data']}'.")
        if status == "REALISASI":
            realisasi_bulan.append(m)

        salur = ds.bulat(b["kwh_salur"], 0) or 0
        jual = ds.bulat(b["kwh_jual"], 0) or 0
        if salur <= 0:
            salur_kosong.append(m)
            continue
        if jual <= 0:
            jual_kosong.append(m)
            continue
        if jual > salur:
            galat(f"neraca.csv [bulan {m}]: kwh_jual ({fmt(jual, 0)}) melebihi "
                  f"kwh_salur ({fmt(salur, 0)}) — susut menjadi negatif.")
            continue
        susut = (salur - jual) / salur * 100
        if susut > 20:
            peringatan(f"neraca.csv [bulan {m}]: susut {susut:.2f}% sangat tinggi. "
                       "Periksa keserentakan tanggal baca meter.")
        porsi = ds.angka(b["porsi_teknis"], 0.0) or 0.0
        if not 0 < porsi < 1:
            galat(f"neraca.csv [bulan {m}]: porsi_teknis {porsi} harus antara 0 dan 1.")

    galat_kelompok("neraca.csv: kwh_salur belum diisi pada bulan", salur_kosong)
    galat_kelompok("neraca.csv: kwh_jual belum diisi pada bulan", jual_kosong)

    if realisasi_bulan:
        harus = list(range(1, max(realisasi_bulan) + 1))
        if sorted(realisasi_bulan) != harus:
            galat("neraca.csv: bulan berstatus REALISASI harus berurutan mulai "
                  f"Januari. Ditemukan {sorted(realisasi_bulan)}.")
    else:
        galat("neraca.csv: belum ada satu pun bulan berstatus REALISASI.")


def periksa_program() -> set[str]:
    baris = ds.baca_csv("program.csv")
    if not periksa_kolom("program.csv", baris, {
            "kode", "nama", "kategori", "sub_kategori", "satuan", "siklus",
            "pic", "kwh_selamat_per_unit", "target_tahun"}):
        return set()

    kode_set: set[str] = set()
    target_kosong: list[str] = []
    pic_kosong: list[str] = []
    for b in baris:
        k = b["kode"].strip()
        if k in kode_set:
            galat(f"program.csv: kode '{k}' muncul lebih dari sekali.")
        kode_set.add(k)
        if b["kategori"].strip().upper() not in ("TEKNIS", "NON_TEKNIS"):
            galat(f"program.csv [{k}]: kategori harus TEKNIS atau NON_TEKNIS, "
                  f"ditemukan '{b['kategori']}'.")
        if (ds.angka(b["target_tahun"], 0.0) or 0.0) <= 0:
            target_kosong.append(k)
        if (ds.angka(b["kwh_selamat_per_unit"], 0.0) or 0.0) < 0:
            galat(f"program.csv [{k}]: kwh_selamat_per_unit tidak boleh negatif.")
        if not b["pic"].strip():
            pic_kosong.append(k)
    galat_kelompok("program.csv: target_tahun belum diisi pada item", target_kosong)
    if pic_kosong:
        peringatan("program.csv: kolom PIC masih kosong pada item "
                   + ", ".join(pic_kosong[:12]))
    return kode_set


def periksa_program_bulanan(kode_program: set[str]) -> None:
    baris = ds.baca_csv("program_bulanan.csv")
    if not periksa_kolom("program_bulanan.csv", baris,
                         {"program_kode", "bulan", "target_volume", "realisasi_volume"}):
        return

    per_kode: dict[str, dict[int, dict]] = {}
    for b in baris:
        k = b["program_kode"].strip()
        if k not in kode_program:
            galat(f"program_bulanan.csv: kode '{k}' tidak ada di program.csv.")
            continue
        m = ds.bulat(b["bulan"], 0) or 0
        if not 1 <= m <= 12:
            galat(f"program_bulanan.csv [{k}]: nomor bulan '{b['bulan']}' tidak sah.")
            continue
        if m in per_kode.setdefault(k, {}):
            galat(f"program_bulanan.csv [{k}]: bulan {m} muncul lebih dari sekali.")
        per_kode[k][m] = b

    target_tahun = {p["kode"]: ds.angka(p["target_tahun"], 0.0) or 0.0
                    for p in ds.baca_csv("program.csv")}

    kurang_baris: list[str] = []
    realisasi_kosong: list[str] = []
    for k in sorted(kode_program):
        bulan = per_kode.get(k, {})
        hilang = [m for m in range(1, 13) if m not in bulan]
        if hilang:
            kurang_baris.append(f"{k} (bulan {','.join(map(str, hilang))})")
            continue

        total_target = sum(ds.angka(bulan[m]["target_volume"], 0.0) or 0.0
                           for m in range(1, 13))
        if selisih_persen(total_target, target_tahun.get(k, 0)) > 1:
            peringatan(f"program_bulanan.csv [{k}]: jumlah target bulanan "
                       f"({fmt(total_target)}) berbeda dari target_tahun pada "
                       f"program.csv ({fmt(target_tahun.get(k, 0))}).")

        for m in range(1, 13):
            r = ds.angka(bulan[m]["realisasi_volume"], None)
            if m <= ds.BULAN_REALISASI and r is None:
                realisasi_kosong.append(f"{k}/bln{m}")
            if m > ds.BULAN_REALISASI and r is not None:
                galat(f"program_bulanan.csv [{k}]: bulan {m} sudah berisi realisasi "
                      "padahal neraca.csv masih menandainya PROYEKSI.")
            if r is not None and r < 0:
                galat(f"program_bulanan.csv [{k}]: realisasi bulan {m} negatif.")

    galat_kelompok("program_bulanan.csv: baris bulan belum lengkap untuk", kurang_baris)
    if realisasi_kosong:
        peringatan("program_bulanan.csv: realisasi masih kosong padahal bulannya "
                   "sudah REALISASI → " + ", ".join(realisasi_kosong[:12])
                   + (f", … ({len(realisasi_kosong)} seluruhnya)"
                      if len(realisasi_kosong) > 12 else ""))


def periksa_susut_penyulang(kode_penyulang: set[str]) -> None:
    baris = ds.baca_csv("susut_penyulang.csv")
    if not periksa_kolom("susut_penyulang.csv", baris,
                         {"penyulang_kode", "bulan", "susut_persen"},
                         boleh_kosong=True):
        return
    ada: dict[str, set[int]] = {}
    kode_asing: set[str] = set()
    for b in baris:
        k = b["penyulang_kode"].strip()
        if k not in kode_penyulang:
            kode_asing.add(k)
            continue
        m = ds.bulat(b["bulan"], 0) or 0
        ada.setdefault(k, set()).add(m)
        s = ds.angka(b["susut_persen"], 0.0) or 0.0
        if not 0 <= s < 30:
            galat(f"susut_penyulang.csv [{k} bulan {m}]: susut_persen {s} "
                  "di luar rentang wajar 0–30%.")
    galat_kelompok("susut_penyulang.csv: kode tidak ada di penyulang.csv",
                   sorted(kode_asing))
    belum: list[str] = []
    for k in sorted(kode_penyulang):
        hilang = [m for m in range(1, ds.BULAN_REALISASI + 1) if m not in ada.get(k, set())]
        if hilang:
            belum.append(f"{k} (bulan {','.join(map(str, hilang))})")
    if belum:
        peringatan("susut_penyulang.csv: belum ada data untuk " + ", ".join(belum[:8])
                   + (f", … ({len(belum)} penyulang)" if len(belum) > 8 else ""))


def periksa_action_plan(kode_program: set[str]) -> None:
    baris = ds.baca_csv("action_plan.csv")
    if not periksa_kolom("action_plan.csv", baris, {
            "no", "prioritas", "kategori", "program_kode", "aksi",
            "akar_masalah", "target_selesai", "pic", "status", "progres_persen"},
            boleh_kosong=True):
        return
    sah_status = {"RENCANA", "BERJALAN", "TERLAMBAT", "TERCAPAI", "BATAL"}
    for b in baris:
        k = b["program_kode"].strip()
        if k and k not in kode_program:
            galat(f"action_plan.csv [no {b['no']}]: program_kode '{k}' "
                  "tidak ada di program.csv.")
        if b["status"].strip().upper() not in sah_status:
            galat(f"action_plan.csv [no {b['no']}]: status '{b['status']}' tidak sah. "
                  f"Pilihan: {', '.join(sorted(sah_status))}.")
        p = ds.angka(b["progres_persen"], 0.0) or 0.0
        if not 0 <= p <= 150:
            galat(f"action_plan.csv [no {b['no']}]: progres_persen {p} tidak wajar.")
        if not b["aksi"].strip():
            galat(f"action_plan.csv [no {b['no']}]: kolom aksi kosong.")


# ---------------------------------------------------------------------------
def main() -> None:
    print(f"Memeriksa berkas master di {ds.MASTER_DIR.relative_to(ds.ROOT)}/\n")

    periksa_unit()
    periksa_parameter()
    kode_penyulang = periksa_penyulang()
    periksa_neraca()
    kode_program = periksa_program()
    periksa_program_bulanan(kode_program)
    periksa_susut_penyulang(kode_penyulang)
    periksa_action_plan(kode_program)

    galat_ringkas = ringkas(GALAT)
    peringatan_ringkas = ringkas(PERINGATAN)
    for pesan in galat_ringkas:
        print(f"  ✗ {pesan}")
    for pesan in peringatan_ringkas:
        print(f"  ⚠ {pesan}")

    print()
    if GALAT:
        print(f"✗ {len(galat_ringkas)} jenis galat ({len(GALAT)} kejadian) dan "
              f"{len(peringatan_ringkas)} peringatan. "
              "Perbaiki galat sebelum menjalankan build_all.py.")
        sys.exit(1)
    if PERINGATAN:
        print(f"✓ Tidak ada galat, {len(peringatan_ringkas)} peringatan untuk diperiksa.")
    else:
        print("✓ Seluruh berkas master lolos pemeriksaan.")
    print(f"  {len(kode_penyulang)} penyulang · {len(kode_program)} item work plan · "
          f"{ds.BULAN_REALISASI} bulan realisasi · {ds.BULAN_SISA} bulan tersisa")


if __name__ == "__main__":
    main()
