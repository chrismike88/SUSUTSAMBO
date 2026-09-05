/** Bentuk data yang dipakai seluruh dashboard.
 *  Sumbernya bisa Supabase (produksi) atau berkas contoh (fallback). */

export type Kategori = "TEKNIS" | "NON_TEKNIS";
export type StatusCapaian = "TERCAPAI" | "WASPADA" | "TERLAMBAT" | "KRITIS" | "N/A";

export interface Skenario {
  label: string;
  gap_kwh_harus_diselamatkan: number;
  gap_kwh_per_bulan: number;
  gap_rupiah: number;
  tingkat_kesulitan: string;
  susut_sisa_diizinkan_persen?: number;
  penurunan_pp_dibutuhkan?: number;
  kwh_susut_maks_setahun?: number;
  kwh_susut_sisa_diizinkan?: number;
  kwh_susut_maks_desember?: number;
}

export interface Kpi {
  periode_data: string;
  bulan_realisasi: number;
  bulan_tersisa: number;
  susut_bulan_ini_persen: number;
  target_bulan_ini_persen: number;
  deviasi_bulan_ini: number;
  susut_ytd_persen: number;
  target_ytd_persen: number;
  target_akhir_tahun_persen: number;
  baseline_tahun_lalu_persen: number;
  perbaikan_vs_baseline: number;
  kwh_salur_ytd: number;
  kwh_jual_ytd: number;
  kwh_susut_ytd: number;
  rupiah_susut_ytd: number;
  susut_teknis_persen: number;
  susut_nonteknis_persen: number;
  skenario_a_kumulatif: Skenario;
  skenario_b_exit_rate: Skenario;
  kwh_selamat_ytd: number;
  kwh_selamat_target_tahun: number;
  kwh_selamat_sisa: number;
  kwh_selamat_sisa_per_bulan: number;
  rupiah_selamat_ytd: number;
  rupiah_selamat_sisa: number;
  kontribusi_teknis: KontribusiKategori;
  kontribusi_nonteknis: KontribusiKategori;
  capaian_program_rata_rata: number;
  jumlah_program: number;
  jumlah_tercapai: number;
  jumlah_waspada: number;
  jumlah_terlambat: number;
  jumlah_kritis: number;
  program_kritis: string[];
  status_keseluruhan: string;
}

export interface KontribusiKategori {
  kwh_target_tahun: number;
  kwh_ytd: number;
  kwh_sisa: number;
  capaian_persen: number;
}

export interface Neraca {
  tahun: number;
  bulan: number;
  bulan_nama: string;
  bulan_panjang: string;
  status_data: "REALISASI" | "PROYEKSI";
  kwh_salur: number;
  kwh_jual: number;
  kwh_susut: number;
  susut_persen: number;
  target_persen: number;
  deviasi_persen: number | null;
  susut_teknis_persen: number;
  susut_nonteknis_persen: number;
  kwh_susut_teknis: number;
  kwh_susut_nonteknis: number;
  susut_ytd_persen: number | null;
  rupiah_susut: number;
}

export interface Program {
  kode: string;
  nama: string;
  kategori: Kategori;
  sub_kategori: string;
  satuan: string;
  pic: string;
  siklus: string;
  kwh_selamat_per_unit: number;
  target_tahun: number;
  target_ytd: number;
  realisasi_ytd: number;
  capaian_ytd_persen: number;
  capaian_thd_target_tahun_persen: number;
  sisa_target: number;
  kebutuhan_per_bulan_sisa: number;
  run_rate_bulanan: number;
  faktor_kejar: number | null;
  kwh_selamat_ytd: number;
  kwh_selamat_target_tahun: number;
  rupiah_selamat_ytd: number;
  status: StatusCapaian;
}

export interface ProgramBulanan {
  program_kode: string;
  tahun: number;
  bulan: number;
  bulan_nama: string;
  target_volume: number;
  realisasi_volume: number | null;
  target_kwh: number;
  realisasi_kwh: number | null;
  capaian_persen: number | null;
}

export interface Penyulang {
  kode: string;
  nama: string;
  jumlah_gardu: number;
  kapasitas_kva: number;
  panjang_jtm_kms: number;
  panjang_jtr_kms: number;
  jumlah_pelanggan: number;
  susut_persen: number;
  unbalance_persen: number;
  cos_phi: number;
  drop_tegangan_persen: number;
  sr_lebih_30m: number;
  kwh_salur_bulan: number;
  kwh_susut_bulan: number;
  rupiah_susut_bulan: number;
  indeks_prioritas: number;
  kelas_prioritas: "KRITIS" | "TINGGI" | "SEDANG" | "RENDAH";
}

export interface RugiTeknis {
  penyulang_kode: string;
  komponen: string;
  kwh_rugi: number;
  persen_dari_teknis: number;
}

export interface P2tl {
  tahun: number;
  bulan: number;
  bulan_nama: string;
  golongan: string;
  keterangan: string;
  jumlah_pemeriksaan: number;
  jumlah_temuan: number;
  kwh_temuan: number;
  rupiah_tagsus: number;
  rupiah_terbayar: number;
}

export interface Aksi {
  no: number;
  prioritas: string;
  kategori: Kategori;
  program_kode: string;
  aksi: string;
  akar_masalah: string;
  dampak_kwh_bulan: number;
  dampak_kwh_sisa_tahun: number;
  dampak_rupiah_sisa_tahun: number;
  sisa_volume: number;
  satuan: string;
  kebutuhan_per_bulan: number;
  capaian_ytd_persen: number;
  status_program: StatusCapaian;
  target_selesai: string;
  pic: string;
  status: string;
  progres_persen: number;
}

export interface Meta {
  unit: {
    kode: string; nama: string; up3: string; uid: string;
    manager: string; tahun: number;
  };
  parameter: Record<string, number>;
  tahun: number;
  bulan_realisasi: number;
  bulan_nama: string[];
  bulan_panjang: string[];
  catatan: string;
}

export interface Dataset {
  meta: Meta;
  kpi: Kpi;
  neraca_energi: Neraca[];
  penyulang: Penyulang[];
  susut_penyulang_bulanan: { penyulang_kode: string; tahun: number; bulan: number;
    bulan_nama: string; kwh_salur: number; kwh_susut: number; susut_persen: number }[];
  rugi_teknis: RugiTeknis[];
  program: Program[];
  program_bulanan: ProgramBulanan[];
  p2tl: P2tl[];
  action_plan: Aksi[];
  /** Menandai apakah angka berasal dari Supabase atau berkas contoh. */
  sumber?: "supabase" | "contoh";
}
