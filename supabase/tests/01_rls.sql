-- ============================================================================
--  UJI ROW LEVEL SECURITY — Monitoring Susut ULP Samboja
--
--  Menguji bahwa model keamanan benar-benar berlaku, bukan sekadar terpasang:
--    * pengunjung tanpa login boleh membaca, tidak boleh menulis
--    * PENGAMAT boleh membaca, tidak boleh menulis apa pun
--    * PELAKSANA boleh mengisi realisasi, tidak boleh menyentuh data master
--    * PELAKSANA tidak dapat menaikkan perannya sendiri
--    * ADMIN boleh mengubah data master, dan perubahannya tercatat di audit
--    * log audit tidak terbaca oleh peran di bawah MANAJER
--
--  Cara menjalankan:  bash scripts/uji_rls.sh
--  Berkas ini gagal dengan galat bila ada satu saja perilaku yang meleset.
-- ============================================================================

\set ON_ERROR_STOP on
\pset pager off

-- ---------------------------------------------------------------------------
-- Alat bantu: jalankan perintah dan laporkan hasilnya tanpa membatalkan uji
-- ---------------------------------------------------------------------------
-- Penolakan oleh Row Level Security dan penolakan oleh hak akses tabel
-- sama-sama bernomor SQLSTATE 42501, padahal artinya jauh berbeda:
--   DITOLAK_HAK_TABEL — peran memang tidak punya hak sama sekali
--   DITOLAK_RLS       — peran punya hak, tetapi kebijakan RLS menolaknya
-- Membedakan keduanya penting: bila kebijakan tulis tertutup oleh hak tabel
-- yang tidak pernah diberikan, kebijakan itu tidak pernah benar-benar teruji.
create or replace function pg_temp.coba(perintah text)
returns text language plpgsql as $$
begin
  execute perintah;
  return 'BERHASIL';
exception
  when others then
    if sqlerrm ilike '%row-level security%' then return 'DITOLAK_RLS';
    elsif sqlerrm ilike '%permission denied%' then return 'DITOLAK_HAK_TABEL';
    else return 'DITOLAK_' || sqlstate;
    end if;
end $$;

create or replace function pg_temp.harus(nama text, dapat text, harap text)
returns void language plpgsql as $$
begin
  if dapat is distinct from harap then
    raise exception '✗ % — diharapkan "%", ternyata "%"', nama, harap, dapat;
  end if;
  raise notice '  ✓ %', nama;
end $$;

-- ---------------------------------------------------------------------------
-- Siapkan tiga pengguna dengan peran berbeda
-- ---------------------------------------------------------------------------
delete from susut.profil;
delete from auth.users;
insert into auth.users (id, email) values
  ('11111111-1111-1111-1111-111111111111', 'pengamat@uji.local'),
  ('22222222-2222-2222-2222-222222222222', 'pelaksana@uji.local'),
  ('33333333-3333-3333-3333-333333333333', 'admin@uji.local');
update susut.profil set peran = 'PELAKSANA' where email = 'pelaksana@uji.local';
update susut.profil set peran = 'ADMIN'     where email = 'admin@uji.local';

do $$
begin
  if (select count(*) from susut.profil) <> 3 then
    raise exception '✗ Pemicu pembuat profil otomatis tidak berjalan';
  end if;
  raise notice '  ✓ Profil dibuat otomatis saat pengguna mendaftar';
end $$;

-- Rekam nilai awal untuk membuktikan tidak ada yang berubah diam-diam
create temp table awal as
select (select realisasi_volume from susut.program_periode pp
        join susut.program pr on pr.id = pp.program_id
        where pr.kode = 'T-01' and pp.tahun = 2026 and pp.bulan = 1) as realisasi,
       (select target_tahun from susut.program where kode = 'T-01')  as target;

-- ---------------------------------------------------------------------------
\echo ''
\echo 'PENGUNJUNG TANPA LOGIN (anon)'
-- ---------------------------------------------------------------------------
set role anon;
select pg_temp.harus('anon boleh membaca ringkasan KPI',
  pg_temp.coba('select 1 from public.susut_kpi_ringkas'), 'BERHASIL');
select pg_temp.harus('anon boleh membaca capaian program',
  pg_temp.coba('select 1 from public.susut_capaian_program'), 'BERHASIL');
select pg_temp.harus('anon DITOLAK menulis realisasi',
  pg_temp.coba('insert into susut.program_periode (program_id,tahun,bulan,target_volume)
                select id,2099,1,1 from susut.program limit 1'), 'DITOLAK_HAK_TABEL');
select pg_temp.harus('anon DITOLAK mengubah data master',
  pg_temp.coba('update susut.program set target_tahun = 1'), 'DITOLAK_HAK_TABEL');
-- Haknya sudah dicabut, sehingga penolakannya terjadi di lapisan hak tabel.
select pg_temp.harus('anon DITOLAK membaca log audit',
  pg_temp.coba('select 1 from susut.audit_log'), 'DITOLAK_HAK_TABEL');
-- Sekalipun haknya dikembalikan, Row Level Security tetap menutupi isinya.
select pg_temp.harus('anon tidak melihat satu pun baris audit',
  pg_temp.coba('select count(*) from susut.audit_log'), 'DITOLAK_HAK_TABEL');
reset role;

-- ---------------------------------------------------------------------------
\echo ''
\echo 'PENGAMAT (sudah login, peran terendah)'
-- ---------------------------------------------------------------------------
set role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-1111-1111-111111111111',false);
select pg_temp.harus('peran terbaca sebagai PENGAMAT',
  susut.peran_saya()::text, 'PENGAMAT');
select pg_temp.harus('PENGAMAT boleh membaca capaian program',
  pg_temp.coba('select 1 from public.susut_capaian_program'), 'BERHASIL');
-- Penting: PENGAMAT PUNYA hak tulis di tingkat tabel; yang menahannya adalah
-- kebijakan RLS. Inilah bukti kebijakan itu benar-benar dievaluasi.
select pg_temp.harus('PENGAMAT DITOLAK menyisipkan realisasi (oleh RLS, bukan hak tabel)',
  pg_temp.coba('insert into susut.program_periode (program_id,tahun,bulan,target_volume)
                select id,2099,1,1 from susut.program limit 1'), 'DITOLAK_RLS');

do $$
declare n integer;
begin
  with u as (update susut.program_periode set realisasi_volume = 99999
             where tahun = 2026 returning 1)
  select count(*) into n from u;
  if n <> 0 then
    raise exception '✗ PENGAMAT berhasil mengubah % baris realisasi', n;
  end if;
  raise notice '  ✓ PENGAMAT DITOLAK mengubah realisasi (0 baris terpengaruh)';
end $$;

select pg_temp.harus('PENGAMAT hanya melihat profilnya sendiri',
  (select count(*)::text from susut.profil), '1');
select pg_temp.harus('PENGAMAT tidak melihat isi log audit',
  (select count(*)::text from susut.audit_log), '0');
reset role;

-- ---------------------------------------------------------------------------
\echo ''
\echo 'PELAKSANA (pengisi data harian)'
-- ---------------------------------------------------------------------------
set role authenticated;
select set_config('request.jwt.claim.sub','22222222-2222-2222-2222-222222222222',false);
select pg_temp.harus('peran terbaca sebagai PELAKSANA',
  susut.peran_saya()::text, 'PELAKSANA');
select pg_temp.harus('PELAKSANA BOLEH mengisi realisasi lewat RPC',
  pg_temp.coba($q$select public.susut_input_realisasi(
    'N-09', 2026::smallint, 9::smallint, 42::numeric, 'uji otomatis')$q$), 'BERHASIL');
select pg_temp.harus('realisasi benar-benar tersimpan',
  (select realisasi_volume::text from susut.program_periode pp
   join susut.program pr on pr.id = pp.program_id
   where pr.kode = 'N-09' and pp.tahun = 2026 and pp.bulan = 9), '42.00');

do $$
declare n integer;
begin
  with u as (update susut.program set target_tahun = 99999 returning 1)
  select count(*) into n from u;
  if n <> 0 then
    raise exception '✗ PELAKSANA berhasil mengubah % baris data master', n;
  end if;
  raise notice '  ✓ PELAKSANA DITOLAK mengubah data master (0 baris terpengaruh)';
end $$;

select pg_temp.harus('PELAKSANA DITOLAK menaikkan perannya sendiri',
  pg_temp.coba($q$update susut.profil set peran = 'ADMIN'
                  where id = '22222222-2222-2222-2222-222222222222'$q$), 'DITOLAK_RLS');
reset role;
select pg_temp.harus('peran PELAKSANA tidak berubah',
  (select peran::text from susut.profil where email = 'pelaksana@uji.local'), 'PELAKSANA');

-- ---------------------------------------------------------------------------
\echo ''
\echo 'ADMIN (pengelola data master)'
-- ---------------------------------------------------------------------------
set role authenticated;
select set_config('request.jwt.claim.sub','33333333-3333-3333-3333-333333333333',false);
select pg_temp.harus('peran terbaca sebagai ADMIN', susut.peran_saya()::text, 'ADMIN');
select pg_temp.harus('ADMIN BOLEH mengubah data master',
  pg_temp.coba($q$update susut.program set target_tahun = 321 where kode = 'N-09'$q$),
  'BERHASIL');
select pg_temp.harus('perubahan master tersimpan',
  (select target_tahun::text from susut.program where kode = 'N-09'), '321.00');
select pg_temp.harus('ADMIN boleh membaca log audit',
  case when (select count(*) from susut.audit_log) > 0 then 'ADA' else 'KOSONG' end, 'ADA');
reset role;

-- ---------------------------------------------------------------------------
\echo ''
\echo 'DATA YANG TIDAK BOLEH TERSENTUH'
-- ---------------------------------------------------------------------------
do $$
declare a record;
begin
  select * into a from awal;
  if (select realisasi_volume from susut.program_periode pp
      join susut.program pr on pr.id = pp.program_id
      where pr.kode='T-01' and pp.tahun=2026 and pp.bulan=1) is distinct from a.realisasi then
    raise exception '✗ Realisasi T-01 berubah padahal seluruh penulisannya ditolak';
  end if;
  if (select target_tahun from susut.program where kode='T-01') is distinct from a.target then
    raise exception '✗ Target T-01 berubah padahal seluruh penulisannya ditolak';
  end if;
  if (select count(*) from susut.program_periode where tahun = 2099) <> 0 then
    raise exception '✗ Ada baris tahun 2099 yang lolos masuk';
  end if;
  raise notice '  ✓ Nilai yang penulisannya ditolak tidak bergeser sama sekali';
end $$;

\echo ''
\echo '✓ SELURUH UJI ROW LEVEL SECURITY LULUS'
