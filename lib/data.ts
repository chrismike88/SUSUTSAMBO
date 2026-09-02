import contoh from "@/lib/fallback/dataset.json";
import { getSupabase, supabaseAktif } from "@/lib/supabase";
import type { Dataset, Kpi, Neraca, Program, Penyulang, P2tl, Aksi } from "@/lib/types";

/** Dataset contoh yang selalu tersedia — dipakai bila Supabase belum disetel
 *  atau sedang tidak dapat dihubungi, sehingga dashboard tidak pernah kosong. */
export const datasetContoh = contoh as unknown as Dataset;

export const revalidate = 300; // detik

type Baris = Record<string, unknown>;
const n = (v: unknown, bawaan = 0): number =>
  v === null || v === undefined ? bawaan : Number(v);
const s = (v: unknown, bawaan = ""): string =>
  v === null || v === undefined ? bawaan : String(v);

/** Susun objek Dataset dari view-view Supabase. */
function dariSupabase(
  kpiRow: Baris,
  neraca: Baris[],
  program: Baris[],
  penyulang: Baris[],
  rugi: Baris[],
  p2tl: Baris[],
  aksi: Baris[],
): Dataset {
  const meta = datasetContoh.meta;
  const bulanRealisasi = n(kpiRow.bulan_terakhir, meta.bulan_realisasi);
  const bulanTersisa = 12 - bulanRealisasi;

  const salurSisa = neraca
    .filter((r) => s(r.status_data) === "PROYEKSI")
    .reduce((a, r) => a + n(r.kwh_salur), 0);

  const kpi: Kpi = {
    periode_data: `${meta.bulan_panjang[bulanRealisasi - 1]} ${n(kpiRow.tahun, meta.tahun)}`,
    bulan_realisasi: bulanRealisasi,
    bulan_tersisa: bulanTersisa,
    susut_bulan_ini_persen: n(kpiRow.susut_bulan_ini_persen),
    target_bulan_ini_persen: n(kpiRow.target_bulan_ini_persen),
    deviasi_bulan_ini: n(kpiRow.deviasi_bulan_ini),
    susut_ytd_persen: n(kpiRow.susut_ytd_persen),
    target_ytd_persen: n(kpiRow.target_bulan_ini_persen),
    target_akhir_tahun_persen: n(kpiRow.target_akhir_tahun_persen),
    baseline_tahun_lalu_persen: n(kpiRow.baseline_tahun_lalu_persen),
    perbaikan_vs_baseline: n(kpiRow.perbaikan_vs_baseline),
    kwh_salur_ytd: n(kpiRow.kwh_salur_ytd),
    kwh_jual_ytd: n(kpiRow.kwh_salur_ytd) - n(kpiRow.kwh_susut_ytd),
    kwh_susut_ytd: n(kpiRow.kwh_susut_ytd),
    rupiah_susut_ytd: n(kpiRow.rupiah_susut_ytd),
    susut_teknis_persen: n(kpiRow.susut_teknis_persen),
    susut_nonteknis_persen: n(kpiRow.susut_nonteknis_persen),
    skenario_a_kumulatif: {
      label: "Target dimaknai SUSUT KUMULATIF (YTD) akhir tahun",
      gap_kwh_harus_diselamatkan: n(kpiRow.a_gap_kwh),
      gap_kwh_per_bulan: bulanTersisa ? n(kpiRow.a_gap_kwh) / bulanTersisa : 0,
      gap_rupiah: n(kpiRow.a_gap_kwh) * n(meta.parameter.tarif_rata_rata, 1462.5),
      tingkat_kesulitan:
        n(kpiRow.a_susut_sisa_diizinkan_persen) < n(kpiRow.susut_bulan_ini_persen) - 1
          ? "SANGAT BERAT"
          : "BERAT",
      susut_sisa_diizinkan_persen: n(kpiRow.a_susut_sisa_diizinkan_persen),
    },
    skenario_b_exit_rate: {
      label: "Target dimaknai SUSUT BULAN DESEMBER (exit rate)",
      gap_kwh_harus_diselamatkan: n(kpiRow.b_gap_kwh),
      gap_kwh_per_bulan: bulanTersisa ? n(kpiRow.b_gap_kwh) / bulanTersisa : 0,
      gap_rupiah: n(kpiRow.b_gap_kwh) * n(meta.parameter.tarif_rata_rata, 1462.5),
      tingkat_kesulitan: "MODERAT",
      penurunan_pp_dibutuhkan: n(kpiRow.b_penurunan_pp_dibutuhkan),
    },
    kwh_selamat_ytd: n(kpiRow.kwh_selamat_ytd),
    kwh_selamat_target_tahun: n(kpiRow.kwh_selamat_target_tahun),
    kwh_selamat_sisa: n(kpiRow.kwh_selamat_sisa),
    kwh_selamat_sisa_per_bulan: bulanTersisa ? n(kpiRow.kwh_selamat_sisa) / bulanTersisa : 0,
    rupiah_selamat_ytd: n(kpiRow.rupiah_selamat_ytd),
    rupiah_selamat_sisa: n(kpiRow.rupiah_selamat_sisa),
    kontribusi_teknis: ringkasKategori(program, "TEKNIS"),
    kontribusi_nonteknis: ringkasKategori(program, "NON_TEKNIS"),
    capaian_program_rata_rata: n(kpiRow.capaian_rata_rata),
    jumlah_program: n(kpiRow.jumlah_program),
    jumlah_tercapai: n(kpiRow.jml_tercapai),
    jumlah_waspada: n(kpiRow.jml_waspada),
    jumlah_terlambat: n(kpiRow.jml_terlambat),
    jumlah_kritis: n(kpiRow.jml_kritis),
    program_kritis: program.filter((p) => s(p.status) === "KRITIS").map((p) => s(p.kode)),
    status_keseluruhan: s(kpiRow.status_keseluruhan, "PERLU AKSELERASI"),
  };
  void salurSisa;

  return {
    meta,
    kpi,
    neraca_energi: neraca.map<Neraca>((r) => ({
      tahun: n(r.tahun), bulan: n(r.bulan), bulan_nama: s(r.bulan_nama),
      bulan_panjang: meta.bulan_panjang[n(r.bulan) - 1] ?? s(r.bulan_nama),
      status_data: s(r.status_data) === "PROYEKSI" ? "PROYEKSI" : "REALISASI",
      kwh_salur: n(r.kwh_salur), kwh_jual: n(r.kwh_jual), kwh_susut: n(r.kwh_susut),
      susut_persen: n(r.susut_persen), target_persen: n(r.target_persen),
      deviasi_persen: r.deviasi_persen === null ? null : n(r.deviasi_persen),
      susut_teknis_persen: n(r.susut_teknis_persen),
      susut_nonteknis_persen: n(r.susut_nonteknis_persen),
      kwh_susut_teknis: n(r.kwh_susut_teknis),
      kwh_susut_nonteknis: n(r.kwh_susut_nonteknis),
      susut_ytd_persen: r.susut_ytd_persen === null ? null : n(r.susut_ytd_persen),
      rupiah_susut: n(r.rupiah_susut),
    })),
    penyulang: penyulang.map<Penyulang>((r) => ({
      kode: s(r.kode), nama: s(r.nama), jumlah_gardu: n(r.jumlah_gardu),
      kapasitas_kva: n(r.kapasitas_kva), panjang_jtm_kms: n(r.panjang_jtm_kms),
      panjang_jtr_kms: n(r.panjang_jtr_kms), jumlah_pelanggan: n(r.jumlah_pelanggan),
      susut_persen: n(r.susut_persen), unbalance_persen: n(r.unbalance_persen),
      cos_phi: n(r.cos_phi), drop_tegangan_persen: n(r.drop_tegangan_persen),
      sr_lebih_30m: n(r.sr_lebih_30m), kwh_salur_bulan: n(r.kwh_salur_bulan),
      kwh_susut_bulan: n(r.kwh_susut_bulan), rupiah_susut_bulan: n(r.rupiah_susut_bulan),
      indeks_prioritas: n(r.indeks_prioritas),
      kelas_prioritas: (s(r.kelas_prioritas, "SEDANG") as Penyulang["kelas_prioritas"]),
    })),
    susut_penyulang_bulanan: datasetContoh.susut_penyulang_bulanan,
    rugi_teknis: rugi.map((r) => ({
      penyulang_kode: "-", komponen: s(r.komponen),
      kwh_rugi: n(r.kwh_rugi), persen_dari_teknis: n(r.persen_dari_teknis),
    })),
    program: program.map<Program>((r) => ({
      kode: s(r.kode), nama: s(r.nama),
      kategori: s(r.kategori) === "TEKNIS" ? "TEKNIS" : "NON_TEKNIS",
      sub_kategori: s(r.sub_kategori), satuan: s(r.satuan), pic: s(r.pic),
      siklus: s(r.siklus), kwh_selamat_per_unit: n(r.kwh_selamat_per_unit),
      target_tahun: n(r.target_tahun), target_ytd: n(r.target_ytd),
      realisasi_ytd: n(r.realisasi_ytd), capaian_ytd_persen: n(r.capaian_ytd_persen),
      capaian_thd_target_tahun_persen: n(r.capaian_thd_tahun_persen),
      sisa_target: n(r.sisa_target),
      kebutuhan_per_bulan_sisa: n(r.kebutuhan_per_bulan_sisa),
      run_rate_bulanan: n(r.run_rate_bulanan),
      faktor_kejar: r.faktor_kejar === null ? null : n(r.faktor_kejar),
      kwh_selamat_ytd: n(r.kwh_selamat_ytd),
      kwh_selamat_target_tahun: n(r.kwh_selamat_target_tahun),
      rupiah_selamat_ytd: n(r.rupiah_selamat_ytd),
      status: s(r.status, "N/A") as Program["status"],
    })),
    program_bulanan: datasetContoh.program_bulanan,
    p2tl: p2tl.flatMap<P2tl>((r) => [{
      tahun: n(r.tahun), bulan: n(r.bulan), bulan_nama: s(r.bulan_nama),
      golongan: "SEMUA", keterangan: "Rekap seluruh golongan",
      jumlah_pemeriksaan: n(r.jumlah_pemeriksaan), jumlah_temuan: n(r.jumlah_temuan),
      kwh_temuan: n(r.kwh_temuan), rupiah_tagsus: n(r.rupiah_tagsus),
      rupiah_terbayar: n(r.rupiah_terbayar),
    }]),
    action_plan: aksi.map<Aksi>((r) => ({
      no: n(r.nomor), prioritas: s(r.prioritas),
      kategori: s(r.kategori) === "TEKNIS" ? "TEKNIS" : "NON_TEKNIS",
      program_kode: s(r.program_kode), aksi: s(r.aksi),
      akar_masalah: s(r.akar_masalah), dampak_kwh_bulan: n(r.dampak_kwh_bulan),
      dampak_kwh_sisa_tahun: n(r.dampak_kwh_bulan) * bulanTersisa,
      dampak_rupiah_sisa_tahun: n(r.dampak_rupiah_bulan) * bulanTersisa,
      sisa_volume: n(r.sisa_target), satuan: s(r.satuan),
      kebutuhan_per_bulan: n(r.kebutuhan_per_bulan_sisa),
      capaian_ytd_persen: n(r.capaian_ytd_persen),
      status_program: s(r.status_program, "N/A") as Aksi["status_program"],
      target_selesai: s(r.target_selesai), pic: s(r.pic),
      status: s(r.status), progres_persen: n(r.progres_persen),
    })),
    sumber: "supabase",
  };
}

function ringkasKategori(program: Baris[], kategori: string) {
  const sub = program.filter((p) => s(p.kategori) === kategori);
  if (!sub.length) return { kwh_target_tahun: 0, kwh_ytd: 0, kwh_sisa: 0, capaian_persen: 0 };
  const target = sub.reduce((a, p) => a + n(p.kwh_selamat_target_tahun), 0);
  const ytd = sub.reduce((a, p) => a + n(p.kwh_selamat_ytd), 0);
  return {
    kwh_target_tahun: target,
    kwh_ytd: ytd,
    kwh_sisa: target - ytd,
    capaian_persen:
      Math.round((sub.reduce((a, p) => a + n(p.capaian_ytd_persen), 0) / sub.length) * 100) / 100,
  };
}

/** Ambil dataset. Urutan: Supabase -> data contoh. Tidak pernah melempar galat. */
export async function getDataset(): Promise<Dataset> {
  const sb = getSupabase();
  if (!sb) return { ...datasetContoh, sumber: "contoh" };

  try {
    const [kpi, neraca, program, penyulang, rugi, p2tl, aksi] = await Promise.all([
      sb.from("susut_kpi_ringkas").select("*").limit(1).maybeSingle(),
      sb.from("susut_neraca").select("*").order("bulan"),
      sb.from("susut_capaian_program").select("*").order("kode"),
      sb.from("susut_ranking_penyulang").select("*").order("peringkat"),
      sb.from("susut_rugi_teknis").select("*").order("kwh_rugi", { ascending: false }),
      sb.from("susut_p2tl").select("*").order("bulan"),
      sb.from("susut_action_plan").select("*").order("nomor"),
    ]);

    if (kpi.error || !kpi.data) throw kpi.error ?? new Error("KPI kosong");

    return dariSupabase(
      kpi.data as Baris,
      (neraca.data ?? []) as Baris[],
      (program.data ?? []) as Baris[],
      (penyulang.data ?? []) as Baris[],
      (rugi.data ?? []) as Baris[],
      (p2tl.data ?? []) as Baris[],
      (aksi.data ?? []) as Baris[],
    );
  } catch (err) {
    console.warn(
      "[susut] Supabase tidak dapat dibaca, memakai data contoh bawaan.",
      err instanceof Error ? err.message : err,
    );
    return { ...datasetContoh, sumber: "contoh" };
  }
}

export { supabaseAktif };
