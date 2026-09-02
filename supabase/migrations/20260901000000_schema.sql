-- ============================================================================
--  MONITORING SUSUT ULP SAMBOJA — SKEMA DATABASE
--  Target platform : Supabase (PostgreSQL 15+)
--  Migrasi 001     : Tabel master, transaksi, dan indeks
-- ============================================================================

create schema if not exists susut;
comment on schema susut is 'Data monitoring susut teknis & non-teknis ULP Samboja';

-- ---------------------------------------------------------------------------
-- ENUM
-- ---------------------------------------------------------------------------
do $$ begin
  create type susut.kategori_susut as enum ('TEKNIS', 'NON_TEKNIS');
exception when duplicate_object then null; end $$;

do $$ begin
  create type susut.status_capaian as enum ('TERCAPAI', 'WASPADA', 'TERLAMBAT', 'KRITIS', 'N/A');
exception when duplicate_object then null; end $$;

do $$ begin
  create type susut.status_data as enum ('REALISASI', 'PROYEKSI');
exception when duplicate_object then null; end $$;

do $$ begin
  create type susut.status_aksi as enum ('RENCANA', 'BERJALAN', 'TERLAMBAT', 'TERCAPAI', 'BATAL');
exception when duplicate_object then null; end $$;

do $$ begin
  create type susut.peran_pengguna as enum ('ADMIN', 'MANAJER', 'SUPERVISOR', 'PELAKSANA', 'PENGAMAT');
exception when duplicate_object then null; end $$;

-- ---------------------------------------------------------------------------
-- 1. MASTER: UNIT
-- ---------------------------------------------------------------------------
create table if not exists susut.unit (
  id            uuid primary key default gen_random_uuid(),
  kode          text not null unique,
  nama          text not null,
  up3           text not null,
  uid           text not null,
  jumlah_pelanggan   integer not null default 0,
  jumlah_gardu       integer not null default 0,
  jumlah_penyulang   integer not null default 0,
  panjang_jtm_kms    numeric(10,2) not null default 0,
  panjang_jtr_kms    numeric(10,2) not null default 0,
  dibuat_pada   timestamptz not null default now(),
  diubah_pada   timestamptz not null default now()
);
comment on table susut.unit is 'Master unit layanan pelanggan (ULP)';

-- ---------------------------------------------------------------------------
-- 2. PARAMETER GLOBAL (tarif, target, ambang batas)
-- ---------------------------------------------------------------------------
create table if not exists susut.parameter (
  kunci       text primary key,
  nilai       numeric not null,
  satuan      text,
  keterangan  text,
  diubah_pada timestamptz not null default now()
);
comment on table susut.parameter is 'Parameter konfigurasi: tarif rata-rata, target susut, ambang status';

-- ---------------------------------------------------------------------------
-- 3. MASTER: PENYULANG (FEEDER)
-- ---------------------------------------------------------------------------
create table if not exists susut.penyulang (
  id                    uuid primary key default gen_random_uuid(),
  unit_id               uuid not null references susut.unit(id) on delete cascade,
  kode                  text not null unique,
  nama                  text not null,
  jumlah_gardu          integer not null default 0,
  kapasitas_kva         integer not null default 0,
  panjang_jtm_kms       numeric(10,2) not null default 0,
  panjang_jtr_kms       numeric(10,2) not null default 0,
  jumlah_pelanggan      integer not null default 0,
  -- profil kondisi terkini (di-refresh tiap bulan)
  susut_persen          numeric(6,3),
  unbalance_persen      numeric(6,2),
  cos_phi               numeric(4,3),
  drop_tegangan_persen  numeric(5,2),
  sr_lebih_30m          integer default 0,
  indeks_prioritas      numeric(6,2),
  kelas_prioritas       text,
  dibuat_pada           timestamptz not null default now(),
  diubah_pada           timestamptz not null default now()
);
comment on table susut.penyulang is 'Master penyulang/feeder 20 kV beserta profil kondisi jaringan';

-- ---------------------------------------------------------------------------
-- 4. NERACA ENERGI BULANAN (kWh salur vs kWh jual)
-- ---------------------------------------------------------------------------
create table if not exists susut.neraca_energi (
  id                      uuid primary key default gen_random_uuid(),
  unit_id                 uuid not null references susut.unit(id) on delete cascade,
  tahun                   smallint not null,
  bulan                   smallint not null check (bulan between 1 and 12),
  status_data             susut.status_data not null default 'REALISASI',
  kwh_salur               bigint not null,
  kwh_jual                bigint not null,
  kwh_susut               bigint generated always as (kwh_salur - kwh_jual) stored,
  susut_persen            numeric(6,3) not null,
  target_persen           numeric(6,3) not null,
  susut_teknis_persen     numeric(6,3),
  susut_nonteknis_persen  numeric(6,3),
  catatan                 text,
  dibuat_pada             timestamptz not null default now(),
  diubah_pada             timestamptz not null default now(),
  unique (unit_id, tahun, bulan)
);
comment on table susut.neraca_energi is
  'Neraca energi bulanan: kWh salur (APP outgoing GI) vs kWh jual (AP2T/TUL)';

create index if not exists idx_neraca_periode on susut.neraca_energi (tahun, bulan);

-- ---------------------------------------------------------------------------
-- 5. KATALOG PROGRAM KERJA PENURUNAN SUSUT (WORK PLAN)
-- ---------------------------------------------------------------------------
create table if not exists susut.program (
  id                    uuid primary key default gen_random_uuid(),
  unit_id               uuid not null references susut.unit(id) on delete cascade,
  kode                  text not null unique,
  nama                  text not null,
  kategori              susut.kategori_susut not null,
  sub_kategori          text,
  satuan                text not null,
  siklus                text not null default 'Bulanan',
  pic                   text,
  kwh_selamat_per_unit  numeric(14,4) not null default 0,
  target_tahun          numeric(16,2) not null,
  aktif                 boolean not null default true,
  urutan                smallint,
  keterangan            text,
  dibuat_pada           timestamptz not null default now(),
  diubah_pada           timestamptz not null default now()
);
comment on table susut.program is
  'Katalog item work plan penurunan susut (teknis & non-teknis) beserta faktor konversi kWh';

-- ---------------------------------------------------------------------------
-- 6. TARGET & REALISASI PROGRAM PER BULAN
-- ---------------------------------------------------------------------------
create table if not exists susut.program_periode (
  id                 uuid primary key default gen_random_uuid(),
  program_id         uuid not null references susut.program(id) on delete cascade,
  tahun              smallint not null,
  bulan              smallint not null check (bulan between 1 and 12),
  target_volume      numeric(16,2) not null default 0,
  realisasi_volume   numeric(16,2),
  catatan            text,
  diinput_oleh       uuid,
  dibuat_pada        timestamptz not null default now(),
  diubah_pada        timestamptz not null default now(),
  unique (program_id, tahun, bulan)
);
comment on table susut.program_periode is
  'Target dan realisasi volume tiap item work plan per bulan. kWh dihitung otomatis di view.';

create index if not exists idx_program_periode on susut.program_periode (tahun, bulan);

-- ---------------------------------------------------------------------------
-- 7. SUSUT PER PENYULANG PER BULAN
-- ---------------------------------------------------------------------------
create table if not exists susut.susut_penyulang (
  id            uuid primary key default gen_random_uuid(),
  penyulang_id  uuid not null references susut.penyulang(id) on delete cascade,
  tahun         smallint not null,
  bulan         smallint not null check (bulan between 1 and 12),
  kwh_salur     bigint not null,
  kwh_susut     bigint not null,
  susut_persen  numeric(6,3) not null,
  dibuat_pada   timestamptz not null default now(),
  unique (penyulang_id, tahun, bulan)
);

create index if not exists idx_susut_penyulang on susut.susut_penyulang (tahun, bulan);

-- ---------------------------------------------------------------------------
-- 8. DEKOMPOSISI RUGI TEKNIS PER PENYULANG
-- ---------------------------------------------------------------------------
create table if not exists susut.rugi_teknis (
  id                 uuid primary key default gen_random_uuid(),
  penyulang_id       uuid not null references susut.penyulang(id) on delete cascade,
  tahun              smallint not null,
  bulan              smallint not null check (bulan between 1 and 12),
  komponen           text not null,
  kwh_rugi           bigint not null,
  persen_dari_teknis numeric(6,2),
  unique (penyulang_id, tahun, bulan, komponen)
);
comment on table susut.rugi_teknis is
  'Dekomposisi rugi teknis: trafo, JTM, JTR, SR/APP, konektor';

-- ---------------------------------------------------------------------------
-- 9. REKAP P2TL
-- ---------------------------------------------------------------------------
create table if not exists susut.p2tl (
  id                 uuid primary key default gen_random_uuid(),
  unit_id            uuid not null references susut.unit(id) on delete cascade,
  tahun              smallint not null,
  bulan              smallint not null check (bulan between 1 and 12),
  golongan           text not null,
  keterangan         text,
  jumlah_pemeriksaan integer not null default 0,
  jumlah_temuan      integer not null default 0,
  kwh_temuan         bigint not null default 0,
  rupiah_tagsus      bigint not null default 0,
  rupiah_terbayar    bigint not null default 0,
  dibuat_pada        timestamptz not null default now(),
  unique (unit_id, tahun, bulan, golongan)
);
comment on table susut.p2tl is
  'Rekap Penertiban Pemakaian Tenaga Listrik per golongan pelanggaran (P-I s/d P-IV)';

-- ---------------------------------------------------------------------------
-- 10. RENCANA AKSI (ACTION PLAN)
-- ---------------------------------------------------------------------------
create table if not exists susut.action_plan (
  id                uuid primary key default gen_random_uuid(),
  unit_id           uuid not null references susut.unit(id) on delete cascade,
  program_id        uuid references susut.program(id) on delete set null,
  nomor             smallint,
  prioritas         text not null,
  kategori          susut.kategori_susut not null,
  aksi              text not null,
  akar_masalah      text,
  dampak_kwh_bulan  bigint default 0,
  target_selesai    text,
  pic               text,
  status            susut.status_aksi not null default 'RENCANA',
  progres_persen    numeric(5,1) not null default 0,
  dibuat_pada       timestamptz not null default now(),
  diubah_pada       timestamptz not null default now()
);
comment on table susut.action_plan is 'Rencana aksi percepatan pencapaian target susut';

-- ---------------------------------------------------------------------------
-- 11. PROFIL PENGGUNA (terhubung ke auth.users Supabase)
-- ---------------------------------------------------------------------------
create table if not exists susut.profil (
  id          uuid primary key references auth.users(id) on delete cascade,
  nama        text,
  email       text,
  peran       susut.peran_pengguna not null default 'PENGAMAT',
  unit_id     uuid references susut.unit(id) on delete set null,
  dibuat_pada timestamptz not null default now()
);
comment on table susut.profil is 'Profil & peran pengguna dashboard';

-- ---------------------------------------------------------------------------
-- 12. LOG PERUBAHAN DATA
-- ---------------------------------------------------------------------------
create table if not exists susut.audit_log (
  id          bigserial primary key,
  tabel       text not null,
  aksi        text not null,
  baris_id    uuid,
  oleh        uuid,
  data_lama   jsonb,
  data_baru   jsonb,
  waktu       timestamptz not null default now()
);

create index if not exists idx_audit_waktu on susut.audit_log (waktu desc);

-- ---------------------------------------------------------------------------
-- TRIGGER: perbarui kolom diubah_pada
-- ---------------------------------------------------------------------------
create or replace function susut.set_diubah_pada()
returns trigger language plpgsql as $$
begin
  new.diubah_pada = now();
  return new;
end $$;

do $$
declare t text;
begin
  foreach t in array array['unit','penyulang','neraca_energi','program',
                           'program_periode','action_plan']
  loop
    execute format(
      'drop trigger if exists trg_%1$s_diubah on susut.%1$s;
       create trigger trg_%1$s_diubah before update on susut.%1$s
       for each row execute function susut.set_diubah_pada();', t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- TRIGGER: audit log untuk tabel transaksi utama
-- ---------------------------------------------------------------------------
create or replace function susut.tulis_audit()
returns trigger language plpgsql security definer as $$
begin
  insert into susut.audit_log (tabel, aksi, baris_id, oleh, data_lama, data_baru)
  values (
    tg_table_name, tg_op,
    coalesce(new.id, old.id), auth.uid(),
    case when tg_op in ('UPDATE','DELETE') then to_jsonb(old) end,
    case when tg_op in ('INSERT','UPDATE') then to_jsonb(new) end
  );
  return coalesce(new, old);
end $$;

do $$
declare t text;
begin
  foreach t in array array['neraca_energi','program_periode','action_plan']
  loop
    execute format(
      'drop trigger if exists trg_%1$s_audit on susut.%1$s;
       create trigger trg_%1$s_audit after insert or update or delete on susut.%1$s
       for each row execute function susut.tulis_audit();', t);
  end loop;
end $$;
