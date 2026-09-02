-- ============================================================================
--  MONITORING SUSUT ULP SAMBOJA — LAPISAN ANALITIK
--  Migrasi 002 : Fungsi bantu + View perhitungan KPI
-- ============================================================================

-- ---------------------------------------------------------------------------
-- Fungsi bantu: ambil nilai parameter
-- ---------------------------------------------------------------------------
create or replace function susut.p(kunci_param text)
returns numeric language sql stable as $$
  select nilai from susut.parameter where kunci = kunci_param;
$$;

-- Fungsi bantu: klasifikasi status capaian (4 tingkat)
create or replace function susut.klasifikasi_capaian(pct numeric)
returns susut.status_capaian language sql immutable as $$
  select case
    when pct is null then 'N/A'::susut.status_capaian
    when pct >= 100 then 'TERCAPAI'::susut.status_capaian
    when pct >=  90 then 'WASPADA'::susut.status_capaian
    when pct >=  75 then 'TERLAMBAT'::susut.status_capaian
    else 'KRITIS'::susut.status_capaian
  end;
$$;

-- Nama bulan Indonesia
create or replace function susut.nama_bulan(b smallint)
returns text language sql immutable as $$
  select (array['Jan','Feb','Mar','Apr','Mei','Jun',
                'Jul','Ags','Sep','Okt','Nov','Des'])[b];
$$;

-- ---------------------------------------------------------------------------
-- V1. NERACA ENERGI + KUMULATIF (YTD)
-- ---------------------------------------------------------------------------
create or replace view susut.v_neraca as
select
  n.id, n.unit_id, u.kode as unit_kode, n.tahun, n.bulan,
  susut.nama_bulan(n.bulan)                                   as bulan_nama,
  n.status_data,
  n.kwh_salur, n.kwh_jual, n.kwh_susut,
  n.susut_persen, n.target_persen,
  round(n.susut_persen - n.target_persen, 3)                  as deviasi_persen,
  n.susut_teknis_persen, n.susut_nonteknis_persen,
  round(n.kwh_susut * n.susut_teknis_persen / nullif(n.susut_persen,0))     as kwh_susut_teknis,
  round(n.kwh_susut * n.susut_nonteknis_persen / nullif(n.susut_persen,0))  as kwh_susut_nonteknis,
  round(n.kwh_susut * susut.p('tarif_rata_rata'))             as rupiah_susut,
  -- kumulatif hanya untuk baris REALISASI
  case when n.status_data = 'REALISASI' then round(
    sum(n.kwh_susut) filter (where n.status_data = 'REALISASI')
      over (partition by n.unit_id, n.tahun order by n.bulan)::numeric * 100
    / nullif(sum(n.kwh_salur) filter (where n.status_data = 'REALISASI')
      over (partition by n.unit_id, n.tahun order by n.bulan), 0), 3)
  end                                                         as susut_ytd_persen,
  sum(n.kwh_salur) filter (where n.status_data = 'REALISASI')
    over (partition by n.unit_id, n.tahun order by n.bulan)   as kwh_salur_kumulatif,
  sum(n.kwh_susut) filter (where n.status_data = 'REALISASI')
    over (partition by n.unit_id, n.tahun order by n.bulan)   as kwh_susut_kumulatif
from susut.neraca_energi n
join susut.unit u on u.id = n.unit_id;

-- ---------------------------------------------------------------------------
-- V2. TARGET & REALISASI PROGRAM PER BULAN (+ konversi kWh & capaian)
-- ---------------------------------------------------------------------------
create or replace view susut.v_program_periode as
select
  pp.id, pp.program_id,
  pr.kode as program_kode, pr.nama as program_nama,
  pr.kategori, pr.sub_kategori, pr.satuan, pr.pic, pr.siklus,
  pp.tahun, pp.bulan, susut.nama_bulan(pp.bulan) as bulan_nama,
  pp.target_volume, pp.realisasi_volume,
  round(pp.target_volume    * pr.kwh_selamat_per_unit)  as target_kwh,
  round(pp.realisasi_volume * pr.kwh_selamat_per_unit)  as realisasi_kwh,
  round(pp.realisasi_volume * 100 / nullif(pp.target_volume, 0), 2) as capaian_persen,
  susut.klasifikasi_capaian(
    round(pp.realisasi_volume * 100 / nullif(pp.target_volume, 0), 2)) as status,
  round(pp.realisasi_volume * pr.kwh_selamat_per_unit
        * susut.p('tarif_rata_rata'))                   as realisasi_rupiah,
  pp.catatan
from susut.program_periode pp
join susut.program pr on pr.id = pp.program_id;

-- ---------------------------------------------------------------------------
-- V3. CAPAIAN PROGRAM YTD  (inti dashboard "pencapaian per item")
-- ---------------------------------------------------------------------------
create or replace view susut.v_capaian_program as
with real_ytd as (
  select program_id, tahun,
         max(bulan) filter (where realisasi_volume is not null) as bulan_terakhir,
         sum(realisasi_volume)                                   as realisasi_ytd,
         sum(target_volume) filter (
           where bulan <= (select max(bulan) from susut.program_periode x
                           where x.program_id = pp.program_id
                             and x.tahun = pp.tahun
                             and x.realisasi_volume is not null)) as target_ytd
  from susut.program_periode pp
  group by program_id, tahun
)
select
  pr.id as program_id, pr.unit_id, pr.kode, pr.nama, pr.kategori, pr.sub_kategori,
  pr.satuan, pr.pic, pr.siklus, pr.kwh_selamat_per_unit,
  r.tahun,
  r.bulan_terakhir,
  pr.target_tahun,
  round(r.target_ytd, 2)                                          as target_ytd,
  round(r.realisasi_ytd, 2)                                       as realisasi_ytd,
  round(r.realisasi_ytd * 100 / nullif(r.target_ytd, 0), 2)       as capaian_ytd_persen,
  round(r.realisasi_ytd * 100 / nullif(pr.target_tahun, 0), 2)    as capaian_thd_tahun_persen,
  round(pr.target_tahun - r.realisasi_ytd, 2)                     as sisa_target,
  round((pr.target_tahun - r.realisasi_ytd)
        / nullif(12 - r.bulan_terakhir, 0), 2)                    as kebutuhan_per_bulan_sisa,
  round(r.realisasi_ytd / nullif(r.bulan_terakhir, 0), 2)         as run_rate_bulanan,
  round(((pr.target_tahun - r.realisasi_ytd) / nullif(12 - r.bulan_terakhir, 0))
        / nullif(r.realisasi_ytd / nullif(r.bulan_terakhir, 0), 0), 2) as faktor_kejar,
  round(r.realisasi_ytd * pr.kwh_selamat_per_unit)                as kwh_selamat_ytd,
  round(pr.target_tahun * pr.kwh_selamat_per_unit)                as kwh_selamat_target_tahun,
  round((pr.target_tahun - r.realisasi_ytd) * pr.kwh_selamat_per_unit) as kwh_selamat_sisa,
  round(r.realisasi_ytd * pr.kwh_selamat_per_unit
        * susut.p('tarif_rata_rata'))                             as rupiah_selamat_ytd,
  susut.klasifikasi_capaian(
    round(r.realisasi_ytd * 100 / nullif(r.target_ytd, 0), 2))    as status
from susut.program pr
join real_ytd r on r.program_id = pr.id
where pr.aktif;

-- ---------------------------------------------------------------------------
-- V4. ROLLUP PER KATEGORI (TEKNIS vs NON-TEKNIS)
-- ---------------------------------------------------------------------------
create or replace view susut.v_capaian_kategori as
select
  tahun, kategori,
  count(*)                                              as jumlah_program,
  round(avg(capaian_ytd_persen), 2)                     as capaian_rata_rata,
  sum(kwh_selamat_ytd)                                  as kwh_selamat_ytd,
  sum(kwh_selamat_target_tahun)                         as kwh_selamat_target_tahun,
  sum(kwh_selamat_sisa)                                 as kwh_selamat_sisa,
  sum(rupiah_selamat_ytd)                               as rupiah_selamat_ytd,
  count(*) filter (where status = 'TERCAPAI')           as jml_tercapai,
  count(*) filter (where status = 'WASPADA')            as jml_waspada,
  count(*) filter (where status = 'TERLAMBAT')          as jml_terlambat,
  count(*) filter (where status = 'KRITIS')             as jml_kritis
from susut.v_capaian_program
group by tahun, kategori;

-- ---------------------------------------------------------------------------
-- V5. RANKING PENYULANG (prioritas penanganan)
-- ---------------------------------------------------------------------------
create or replace view susut.v_ranking_penyulang as
select
  p.id, p.kode, p.nama, p.jumlah_gardu, p.jumlah_pelanggan,
  p.kapasitas_kva, p.panjang_jtm_kms, p.panjang_jtr_kms,
  p.susut_persen, p.unbalance_persen, p.cos_phi,
  p.drop_tegangan_persen, p.sr_lebih_30m,
  p.indeks_prioritas, p.kelas_prioritas,
  sp.kwh_salur                                  as kwh_salur_bulan,
  sp.kwh_susut                                  as kwh_susut_bulan,
  round(sp.kwh_susut * susut.p('tarif_rata_rata')) as rupiah_susut_bulan,
  rank() over (order by p.indeks_prioritas desc)   as peringkat
from susut.penyulang p
left join lateral (
  select kwh_salur, kwh_susut from susut.susut_penyulang s
  where s.penyulang_id = p.id order by tahun desc, bulan desc limit 1
) sp on true;

-- ---------------------------------------------------------------------------
-- V6. KOMPOSISI RUGI TEKNIS PER KOMPONEN (level unit)
-- ---------------------------------------------------------------------------
create or replace view susut.v_rugi_teknis_komponen as
select
  rt.tahun, rt.bulan, rt.komponen,
  sum(rt.kwh_rugi)                                                as kwh_rugi,
  round(sum(rt.kwh_rugi) * 100.0
        / nullif(sum(sum(rt.kwh_rugi)) over (partition by rt.tahun, rt.bulan), 0), 2)
                                                                  as persen_dari_teknis,
  round(sum(rt.kwh_rugi) * susut.p('tarif_rata_rata'))            as rupiah_rugi
from susut.rugi_teknis rt
group by rt.tahun, rt.bulan, rt.komponen;

-- ---------------------------------------------------------------------------
-- V7. REKAP P2TL BULANAN
-- ---------------------------------------------------------------------------
create or replace view susut.v_p2tl_bulanan as
select
  tahun, bulan, susut.nama_bulan(bulan) as bulan_nama,
  sum(jumlah_pemeriksaan)  as jumlah_pemeriksaan,
  sum(jumlah_temuan)       as jumlah_temuan,
  round(sum(jumlah_temuan) * 100.0
        / nullif(sum(jumlah_pemeriksaan), 0), 2) as hit_rate_persen,
  sum(kwh_temuan)          as kwh_temuan,
  sum(rupiah_tagsus)       as rupiah_tagsus,
  sum(rupiah_terbayar)     as rupiah_terbayar,
  round(sum(rupiah_terbayar) * 100.0
        / nullif(sum(rupiah_tagsus), 0), 2)      as efektivitas_tagih_persen
from susut.p2tl
group by tahun, bulan;

-- ---------------------------------------------------------------------------
-- V8. ANALISIS GAP MENUJU TARGET AKHIR TAHUN (2 skenario)
-- ---------------------------------------------------------------------------
create or replace view susut.v_gap_target as
with r as (
  select unit_id, tahun,
         sum(kwh_salur) as salur_ytd,
         sum(kwh_susut) as susut_ytd,
         max(bulan)     as bulan_terakhir
  from susut.neraca_energi where status_data = 'REALISASI'
  group by unit_id, tahun
),
sisa as (
  select unit_id, tahun, sum(kwh_salur) as salur_sisa, count(*) as bulan_sisa
  from susut.neraca_energi where status_data = 'PROYEKSI'
  group by unit_id, tahun
),
des as (
  select unit_id, tahun, kwh_salur as salur_des
  from susut.neraca_energi where bulan = 12
),
ags as (
  select distinct on (unit_id, tahun) unit_id, tahun, susut_persen as susut_terakhir
  from susut.neraca_energi where status_data = 'REALISASI'
  order by unit_id, tahun, bulan desc
)
select
  r.unit_id, r.tahun, r.bulan_terakhir, sisa.bulan_sisa,
  round(r.susut_ytd * 100.0 / r.salur_ytd, 3)          as susut_ytd_persen,
  a.susut_terakhir                                      as susut_bulan_terakhir_persen,
  susut.p('target_susut_akhir_tahun')                   as target_persen,
  -- SKENARIO A: target = susut kumulatif setahun
  round((r.salur_ytd + sisa.salur_sisa)
        * susut.p('target_susut_akhir_tahun') / 100)    as a_kwh_susut_maks_setahun,
  round((r.salur_ytd + sisa.salur_sisa)
        * susut.p('target_susut_akhir_tahun') / 100 - r.susut_ytd)
                                                        as a_kwh_susut_sisa_diizinkan,
  round(((r.salur_ytd + sisa.salur_sisa)
        * susut.p('target_susut_akhir_tahun') / 100 - r.susut_ytd)
        * 100.0 / sisa.salur_sisa, 3)                   as a_susut_sisa_diizinkan_persen,
  round(sisa.salur_sisa * a.susut_terakhir / 100
        - ((r.salur_ytd + sisa.salur_sisa)
           * susut.p('target_susut_akhir_tahun') / 100 - r.susut_ytd))
                                                        as a_gap_kwh,
  -- SKENARIO B: target = susut bulan Desember (exit rate)
  round(des.salur_des * susut.p('target_susut_akhir_tahun') / 100)
                                                        as b_kwh_susut_maks_desember,
  round(a.susut_terakhir - susut.p('target_susut_akhir_tahun'), 3)
                                                        as b_penurunan_pp_dibutuhkan,
  round(des.salur_des * (a.susut_terakhir - susut.p('target_susut_akhir_tahun')) / 100)
                                                        as b_gap_kwh
from r
join sisa on sisa.unit_id = r.unit_id and sisa.tahun = r.tahun
join des  on des.unit_id  = r.unit_id and des.tahun  = r.tahun
join ags a on a.unit_id   = r.unit_id and a.tahun    = r.tahun;

-- ---------------------------------------------------------------------------
-- V9. KPI RINGKAS (satu baris — konsumsi utama dashboard)
-- ---------------------------------------------------------------------------
create or replace view susut.v_kpi_ringkas as
with terakhir as (
  select distinct on (unit_id, tahun) *
  from susut.v_neraca where status_data = 'REALISASI'
  order by unit_id, tahun, bulan desc
),
prog as (
  select tahun,
         round(avg(capaian_ytd_persen), 2)            as capaian_rata_rata,
         count(*)                                     as jumlah_program,
         count(*) filter (where status = 'TERCAPAI')  as jml_tercapai,
         count(*) filter (where status = 'WASPADA')   as jml_waspada,
         count(*) filter (where status = 'TERLAMBAT') as jml_terlambat,
         count(*) filter (where status = 'KRITIS')    as jml_kritis,
         sum(kwh_selamat_ytd)                         as kwh_selamat_ytd,
         sum(kwh_selamat_target_tahun)                as kwh_selamat_target_tahun,
         sum(kwh_selamat_sisa)                        as kwh_selamat_sisa
  from susut.v_capaian_program group by tahun
)
select
  t.unit_id, t.unit_kode, t.tahun, t.bulan as bulan_terakhir, t.bulan_nama,
  t.susut_persen              as susut_bulan_ini_persen,
  t.target_persen             as target_bulan_ini_persen,
  t.deviasi_persen            as deviasi_bulan_ini,
  t.susut_ytd_persen,
  t.susut_teknis_persen, t.susut_nonteknis_persen,
  t.kwh_salur_kumulatif       as kwh_salur_ytd,
  t.kwh_susut_kumulatif       as kwh_susut_ytd,
  round(t.kwh_susut_kumulatif * susut.p('tarif_rata_rata')) as rupiah_susut_ytd,
  susut.p('target_susut_akhir_tahun')  as target_akhir_tahun_persen,
  susut.p('baseline_susut_2025')       as baseline_tahun_lalu_persen,
  round(susut.p('baseline_susut_2025') - t.susut_ytd_persen, 3) as perbaikan_vs_baseline,
  g.a_susut_sisa_diizinkan_persen, g.a_gap_kwh, g.b_gap_kwh,
  g.b_penurunan_pp_dibutuhkan,
  p.capaian_rata_rata, p.jumlah_program,
  p.jml_tercapai, p.jml_waspada, p.jml_terlambat, p.jml_kritis,
  p.kwh_selamat_ytd, p.kwh_selamat_target_tahun, p.kwh_selamat_sisa,
  round(p.kwh_selamat_ytd * susut.p('tarif_rata_rata'))  as rupiah_selamat_ytd,
  round(p.kwh_selamat_sisa * susut.p('tarif_rata_rata')) as rupiah_selamat_sisa,
  -- apakah sisa potensi program cukup menutup gap skenario A?
  case when p.kwh_selamat_sisa >= g.a_gap_kwh then 'MASIH BISA DICAPAI'
       else 'TIDAK CUKUP - PERLU PROGRAM TAMBAHAN' end as verdict_target,
  case when t.susut_ytd_persen <= susut.p('target_susut_akhir_tahun') + 0.15
       then 'ON TRACK' else 'PERLU AKSELERASI' end      as status_keseluruhan
from terakhir t
join susut.v_gap_target g on g.unit_id = t.unit_id and g.tahun = t.tahun
join prog p on p.tahun = t.tahun;

-- ---------------------------------------------------------------------------
-- V10. RENCANA AKSI DIPERKAYA
-- ---------------------------------------------------------------------------
create or replace view susut.v_action_plan as
select
  a.id, a.unit_id, a.nomor, a.prioritas, a.kategori, a.aksi, a.akar_masalah,
  a.dampak_kwh_bulan, a.target_selesai, a.pic, a.status, a.progres_persen,
  pr.kode as program_kode, pr.nama as program_nama, pr.satuan,
  cp.capaian_ytd_persen, cp.sisa_target, cp.kebutuhan_per_bulan_sisa,
  cp.status as status_program,
  round(a.dampak_kwh_bulan * susut.p('tarif_rata_rata')) as dampak_rupiah_bulan
from susut.action_plan a
left join susut.program pr on pr.id = a.program_id
left join susut.v_capaian_program cp on cp.program_id = pr.id
order by a.nomor;
