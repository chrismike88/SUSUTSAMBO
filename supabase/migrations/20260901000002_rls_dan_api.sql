-- ============================================================================
--  MONITORING SUSUT ULP SAMBOJA — KEAMANAN & EKSPOS API
--  Migrasi 003 : Row Level Security, peran, dan view publik untuk PostgREST
-- ============================================================================

-- ---------------------------------------------------------------------------
-- A. HAK AKSES SCHEMA
-- ---------------------------------------------------------------------------
grant usage on schema susut to anon, authenticated, service_role;

-- Pengunjung tanpa login: baca saja.
grant select on all tables in schema susut to anon, authenticated;

-- Log audit memuat isi baris sebelum dan sesudah perubahan, termasuk siapa
-- yang mengubahnya. Row Level Security sudah menyembunyikannya dari anon,
-- tetapi haknya dicabut juga agar satu kebijakan yang keliru di kemudian hari
-- tidak sampai membocorkannya.
revoke select on susut.audit_log from anon;

-- Pengguna yang sudah login juga memerlukan hak tulis di TINGKAT TABEL.
-- SIAPA yang benar-benar boleh menulis tetap ditentukan Row Level Security
-- pada bagian E di bawah. Tanpa grant ini, PostgreSQL menolak lebih dulu di
-- lapisan hak akses tabel sehingga seluruh kebijakan tulis tidak akan pernah
-- dievaluasi — pengisian realisasi bulanan pun mustahil dilakukan.
-- Tabel audit_log sengaja TIDAK diberi hak tulis: isinya hanya boleh
-- ditambah oleh pemicu susut.tulis_audit() yang berjalan sebagai pemilik.
grant insert, update, delete on
  susut.unit, susut.parameter, susut.penyulang, susut.program,
  susut.neraca_energi, susut.program_periode, susut.susut_penyulang,
  susut.rugi_teknis, susut.p2tl, susut.action_plan, susut.profil
to authenticated;

grant all    on all tables in schema susut to service_role;
grant execute on all functions in schema susut to anon, authenticated, service_role;

alter default privileges in schema susut
  grant select on tables to anon, authenticated;

-- ---------------------------------------------------------------------------
-- B. FUNGSI BANTU PERAN
-- ---------------------------------------------------------------------------
create or replace function susut.peran_saya()
returns susut.peran_pengguna language sql stable security definer
set search_path = susut, public as $$
  select coalesce((select peran from susut.profil where id = auth.uid()), 'PENGAMAT');
$$;

create or replace function susut.boleh_tulis()
returns boolean language sql stable as $$
  select susut.peran_saya() in ('ADMIN', 'MANAJER', 'SUPERVISOR', 'PELAKSANA');
$$;

create or replace function susut.boleh_kelola()
returns boolean language sql stable as $$
  select susut.peran_saya() in ('ADMIN', 'MANAJER');
$$;

-- Buat profil otomatis saat pengguna baru mendaftar
create or replace function susut.buat_profil_baru()
returns trigger language plpgsql security definer
set search_path = susut, public as $$
begin
  insert into susut.profil (id, nama, email, peran)
  values (new.id,
          coalesce(new.raw_user_meta_data->>'nama', split_part(new.email, '@', 1)),
          new.email, 'PENGAMAT')
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists trg_auth_user_baru on auth.users;
create trigger trg_auth_user_baru
  after insert on auth.users
  for each row execute function susut.buat_profil_baru();

-- ---------------------------------------------------------------------------
-- C. AKTIFKAN RLS
-- ---------------------------------------------------------------------------
do $$
declare t text;
begin
  foreach t in array array['unit','parameter','penyulang','neraca_energi','program',
                           'program_periode','susut_penyulang','rugi_teknis','p2tl',
                           'action_plan','profil','audit_log']
  loop
    execute format('alter table susut.%I enable row level security;', t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- D. KEBIJAKAN BACA
--    Mode bawaan: dashboard bersifat "read-only publik" (agregat, tanpa data
--    pribadi pelanggan) sehingga situs Vercel dapat tampil tanpa login.
--    Untuk mengunci agar wajib login: ganti  `to anon, authenticated`
--    menjadi  `to authenticated`  pada blok di bawah, lalu jalankan ulang.
-- ---------------------------------------------------------------------------
do $$
declare t text;
begin
  foreach t in array array['unit','parameter','penyulang','neraca_energi','program',
                           'program_periode','susut_penyulang','rugi_teknis','p2tl',
                           'action_plan']
  loop
    execute format('drop policy if exists baca_publik on susut.%I;', t);
    execute format(
      'create policy baca_publik on susut.%I for select to anon, authenticated using (true);', t);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- E. KEBIJAKAN TULIS  (butuh login + peran)
-- ---------------------------------------------------------------------------
do $$
declare t text;
begin
  -- Data operasional harian: boleh diisi PELAKSANA ke atas
  foreach t in array array['neraca_energi','program_periode','susut_penyulang',
                           'rugi_teknis','p2tl','action_plan']
  loop
    execute format('drop policy if exists tulis_operasional on susut.%I;', t);
    execute format(
      'create policy tulis_operasional on susut.%I for all to authenticated
       using (susut.boleh_tulis()) with check (susut.boleh_tulis());', t);
  end loop;

  -- Data master & parameter: hanya ADMIN / MANAJER
  foreach t in array array['unit','parameter','penyulang','program']
  loop
    execute format('drop policy if exists kelola_master on susut.%I;', t);
    execute format(
      'create policy kelola_master on susut.%I for all to authenticated
       using (susut.boleh_kelola()) with check (susut.boleh_kelola());', t);
  end loop;
end $$;

-- Profil: setiap orang membaca/mengubah profilnya sendiri; ADMIN membaca semua
drop policy if exists profil_sendiri on susut.profil;
create policy profil_sendiri on susut.profil for select to authenticated
  using (id = auth.uid() or susut.boleh_kelola());

drop policy if exists profil_ubah_sendiri on susut.profil;
create policy profil_ubah_sendiri on susut.profil for update to authenticated
  using (id = auth.uid()) with check (id = auth.uid() and peran = susut.peran_saya());

drop policy if exists profil_kelola on susut.profil;
create policy profil_kelola on susut.profil for all to authenticated
  using (susut.boleh_kelola()) with check (susut.boleh_kelola());

-- Audit log: hanya ADMIN / MANAJER yang boleh membaca
drop policy if exists audit_baca on susut.audit_log;
create policy audit_baca on susut.audit_log for select to authenticated
  using (susut.boleh_kelola());

-- ---------------------------------------------------------------------------
-- F. VIEW MENGHORMATI RLS PEMANGGIL
-- ---------------------------------------------------------------------------
do $$
declare v text;
begin
  foreach v in array array['v_neraca','v_program_periode','v_capaian_program',
                           'v_capaian_kategori','v_ranking_penyulang',
                           'v_rugi_teknis_komponen','v_p2tl_bulanan',
                           'v_gap_target','v_kpi_ringkas','v_action_plan']
  loop
    execute format('alter view susut.%I set (security_invoker = on);', v);
  end loop;
end $$;

-- ---------------------------------------------------------------------------
-- G. EKSPOS KE POSTGREST LEWAT SCHEMA public
--    Supabase secara bawaan hanya mengekspos schema `public` ke REST API.
--    View pembungkus berikut membuat seluruh data dapat diakses melalui
--    supabase.from('susut_kpi_ringkas') tanpa perlu mengubah setelan API.
-- ---------------------------------------------------------------------------
create or replace view public.susut_kpi_ringkas      with (security_invoker = on) as select * from susut.v_kpi_ringkas;
create or replace view public.susut_neraca           with (security_invoker = on) as select * from susut.v_neraca;
create or replace view public.susut_capaian_program  with (security_invoker = on) as select * from susut.v_capaian_program;
create or replace view public.susut_capaian_kategori with (security_invoker = on) as select * from susut.v_capaian_kategori;
create or replace view public.susut_program_periode  with (security_invoker = on) as select * from susut.v_program_periode;
create or replace view public.susut_ranking_penyulang with (security_invoker = on) as select * from susut.v_ranking_penyulang;
create or replace view public.susut_rugi_teknis      with (security_invoker = on) as select * from susut.v_rugi_teknis_komponen;
create or replace view public.susut_p2tl             with (security_invoker = on) as select * from susut.v_p2tl_bulanan;
create or replace view public.susut_gap_target       with (security_invoker = on) as select * from susut.v_gap_target;
create or replace view public.susut_action_plan      with (security_invoker = on) as select * from susut.v_action_plan;
create or replace view public.susut_parameter        with (security_invoker = on) as select * from susut.parameter;

grant select on
  public.susut_kpi_ringkas, public.susut_neraca, public.susut_capaian_program,
  public.susut_capaian_kategori, public.susut_program_periode,
  public.susut_ranking_penyulang, public.susut_rugi_teknis, public.susut_p2tl,
  public.susut_gap_target, public.susut_action_plan, public.susut_parameter
to anon, authenticated;

-- ---------------------------------------------------------------------------
-- H. RPC: input realisasi bulanan dari dashboard
-- ---------------------------------------------------------------------------
create or replace function public.susut_input_realisasi(
  p_program_kode text,
  p_tahun        smallint,
  p_bulan        smallint,
  p_realisasi    numeric,
  p_catatan      text default null
) returns jsonb
language plpgsql security invoker
set search_path = susut, public as $$
declare
  v_program_id uuid;
  v_hasil      jsonb;
begin
  select id into v_program_id from susut.program where kode = p_program_kode;
  if v_program_id is null then
    raise exception 'Program % tidak ditemukan', p_program_kode;
  end if;

  insert into susut.program_periode (program_id, tahun, bulan, realisasi_volume, catatan, diinput_oleh)
  values (v_program_id, p_tahun, p_bulan, p_realisasi, p_catatan, auth.uid())
  on conflict (program_id, tahun, bulan) do update
    set realisasi_volume = excluded.realisasi_volume,
        catatan          = coalesce(excluded.catatan, susut.program_periode.catatan),
        diinput_oleh     = auth.uid(),
        diubah_pada      = now();

  select to_jsonb(v) into v_hasil
  from susut.v_capaian_program v where v.program_id = v_program_id;
  return v_hasil;
end $$;

grant execute on function public.susut_input_realisasi(text, smallint, smallint, numeric, text)
  to authenticated;
