#!/usr/bin/env bash
# ============================================================================
#  Uji Row Level Security — Monitoring Susut ULP Samboja
#
#  Membuktikan model keamanan benar-benar berlaku: siapa boleh membaca, siapa
#  boleh menulis, dan data mana yang harus tetap tidak tersentuh.
#
#      bash scripts/uji_rls.sh                        # PostgreSQL sementara
#      PGURL=postgres://... bash scripts/uji_rls.sh   # basis data yang ada
#
#  Keluar dengan kode bukan nol bila ada satu saja perilaku yang meleset.
# ============================================================================
set -euo pipefail

AKAR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIGRASI="$AKAR/supabase/migrations"
UJI="$AKAR/supabase/tests"

if [[ -n "${PGURL:-}" ]]; then
  PSQL=(psql "$PGURL")
else
  BIN=$(ls -d /usr/lib/postgresql/*/bin 2>/dev/null | tail -1 || true)
  [[ -n "$BIN" ]] || { echo "✗ PostgreSQL tidak ditemukan. Pasang paket postgresql, atau setel PGURL."; exit 1; }

  DATA=$(mktemp -d)
  chmod 777 "$DATA"

  # Basis data sementara ini HANYA mendengarkan soket Unix di dalam $DATA
  # (listen_addresses dikosongkan), sehingga tidak pernah berebut port TCP
  # dengan PostgreSQL lain di mesin yang sama dan tidak terjangkau dari luar.
  OPSI="-p 5432 -k $DATA -c listen_addresses="

  sebagai_postgres() {
    if [[ "$(id -u)" -eq 0 ]]; then su postgres -s /bin/bash -c "$1"; else bash -c "$1"; fi
  }
  bersihkan() {
    sebagai_postgres "$BIN/pg_ctl -D $DATA/db stop -m immediate" >/dev/null 2>&1 || true
    rm -rf "$DATA"
  }
  trap bersihkan EXIT

  mkdir -p "$DATA/db"
  if [[ "$(id -u)" -eq 0 ]]; then
    id -u postgres >/dev/null 2>&1 || { echo "✗ Butuh pengguna 'postgres' bila dijalankan sebagai root."; exit 1; }
    chown postgres:postgres "$DATA" "$DATA/db"
  fi
  chmod 700 "$DATA/db"

  sebagai_postgres "$BIN/initdb -D $DATA/db -A trust -U postgres" >/dev/null 2>&1 \
    || { echo "✗ initdb gagal"; exit 1; }
  sebagai_postgres "$BIN/pg_ctl -D $DATA/db -o '$OPSI' -l $DATA/log start" >/dev/null 2>&1 \
    || { echo "✗ PostgreSQL sementara gagal dijalankan:"; cat "$DATA/log" 2>/dev/null; exit 1; }

  PSQL=(psql -h "$DATA" -p 5432 -U postgres -d postgres)
fi

echo "▶ Menyiapkan skema"
PGOPTIONS='-c client_min_messages=warning' \
  "${PSQL[@]}" -q -v ON_ERROR_STOP=1 -f "$UJI/00_stub_auth.sql" >/dev/null
for f in "$MIGRASI"/*.sql; do
  echo "  · $(basename "$f")"
  PGOPTIONS='-c client_min_messages=warning' \
    "${PSQL[@]}" -q -v ON_ERROR_STOP=1 -f "$f" >/dev/null
done

echo "▶ Menjalankan uji Row Level Security"
set +e
KELUARAN=$(PGOPTIONS='-c client_min_messages=notice' \
  "${PSQL[@]}" -q -t -A -v ON_ERROR_STOP=1 -f "$UJI/01_rls.sql" 2>&1)
KODE=$?
set -e

echo "$KELUARAN" \
  | sed -E 's/^psql:[^ ]+ //; s/^NOTICE:  //; s/^ERROR:  /GAGAL: /' \
  | grep -vE '^(CONTEXT|DETAIL|HINT|LINE|STATEMENT)' \
  | grep -vE '^[0-9a-f]{8}-[0-9a-f]{4}' \
  | grep -v '^$'

exit $KODE
