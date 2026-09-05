import type { ReactNode } from "react";
import { WARNA_STATUS } from "@/lib/format";

export function Kartu({
  judul,
  keterangan,
  aksi,
  children,
  className = "",
}: {
  judul?: string;
  keterangan?: ReactNode;
  aksi?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`kartu p-4 sm:p-5 ${className}`}>
      {(judul || aksi) && (
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            {judul && (
              <h2 className="text-[0.95rem] font-semibold" style={{ color: "var(--ink)" }}>
                {judul}
              </h2>
            )}
            {keterangan && (
              <p className="mt-0.5 text-xs" style={{ color: "var(--ink-muted)" }}>
                {keterangan}
              </p>
            )}
          </div>
          {aksi}
        </div>
      )}
      {children}
    </section>
  );
}

export function Petak({
  label,
  nilai,
  satuan,
  catatan,
  nada = "netral",
}: {
  label: string;
  nilai: string;
  satuan?: string;
  catatan?: ReactNode;
  nada?: "netral" | "baik" | "peringatan" | "buruk" | "sorot";
}) {
  const warna: Record<string, string> = {
    netral: "var(--ink)",
    baik: "var(--st-good)",
    peringatan: "var(--st-warning)",
    buruk: "var(--st-critical)",
    sorot: "var(--viz-1)",
  };
  return (
    <div className="kartu flex flex-col justify-between p-4">
      <p className="kartu-judul">{label}</p>
      <p className="angka-hero mt-2" style={{ color: warna[nada] }}>
        {nilai}
        {satuan && (
          <span className="ml-1 text-base font-semibold" style={{ color: "var(--ink-2)" }}>
            {satuan}
          </span>
        )}
      </p>
      {catatan && (
        <p className="mt-2 text-xs leading-snug" style={{ color: "var(--ink-muted)" }}>
          {catatan}
        </p>
      )}
    </div>
  );
}

const IKON_STATUS: Record<string, string> = {
  TERCAPAI: "✓",
  WASPADA: "◐",
  TERLAMBAT: "▲",
  KRITIS: "✕",
  "N/A": "–",
};

/** Lencana status: warna SELALU disertai ikon dan teks, tidak pernah warna saja. */
export function LencanaStatus({ status }: { status: string }) {
  const w = WARNA_STATUS[status] ?? WARNA_STATUS["N/A"];
  return (
    <span className={`lencana ${w.latar} ${w.teks} ${w.garis}`}>
      <span aria-hidden>{IKON_STATUS[status] ?? "–"}</span>
      {status}
    </span>
  );
}

const KELAS_PENYULANG: Record<string, { warna: string; ikon: string; teks: string }> = {
  KRITIS: { warna: "var(--st-critical)", ikon: "✕", teks: "#fff" },
  TINGGI: { warna: "var(--st-serious)", ikon: "▲", teks: "#3B1A08" },
  SEDANG: { warna: "var(--st-warning)", ikon: "◐", teks: "#3B2A05" },
  RENDAH: { warna: "var(--st-good)", ikon: "✓", teks: "#fff" },
};

/** Kelas prioritas penanganan penyulang — punya skala sendiri, tidak meminjam
 *  istilah status capaian program agar tidak salah baca. */
export function LencanaPenyulang({ kelas }: { kelas: string }) {
  const k = KELAS_PENYULANG[kelas] ?? KELAS_PENYULANG.SEDANG;
  return (
    <span className="lencana" style={{ background: k.warna, color: k.teks }}>
      <span aria-hidden>{k.ikon}</span>
      {kelas}
    </span>
  );
}

export function LencanaPrioritas({ prioritas }: { prioritas: string }) {
  const gaya: Record<string, string> = {
    "SANGAT TINGGI": "bg-red-600 text-white",
    TINGGI: "bg-orange-500 text-white",
    SEDANG: "bg-amber-100 text-amber-900",
    RUTIN: "bg-slate-200 text-slate-700",
  };
  return <span className={`lencana ${gaya[prioritas] ?? gaya.RUTIN}`}>{prioritas}</span>;
}

/** Bilah progres dengan angka tercetak — bukan warna saja. */
export function Bilah({
  nilai,
  maks = 100,
  warna = "var(--viz-1)",
  tampilAngka = true,
}: {
  nilai: number;
  maks?: number;
  warna?: string;
  tampilAngka?: boolean;
}) {
  const lebar = Math.max(0, Math.min(100, (nilai / maks) * 100));
  return (
    <div className="flex items-center gap-2">
      <div
        className="h-1.5 min-w-[3rem] flex-1 overflow-hidden rounded-full"
        style={{ background: "var(--line)" }}
        role="img"
        aria-label={`${nilai.toFixed(1)} dari ${maks}`}
      >
        <div className="h-full rounded-full" style={{ width: `${lebar}%`, background: warna }} />
      </div>
      {tampilAngka && (
        <span className="w-12 shrink-0 text-right text-xs tabular-nums" style={{ color: "var(--ink-2)" }}>
          {nilai.toFixed(0)}%
        </span>
      )}
    </div>
  );
}

export function JudulHalaman({
  judul,
  keterangan,
}: {
  judul: string;
  keterangan?: string;
}) {
  return (
    <div className="mb-5">
      <h1 className="text-xl font-bold tracking-tight sm:text-2xl" style={{ color: "var(--ink)" }}>
        {judul}
      </h1>
      {keterangan && (
        <p className="mt-1 max-w-3xl text-sm" style={{ color: "var(--ink-2)" }}>
          {keterangan}
        </p>
      )}
    </div>
  );
}

export function Catatan({ children }: { children: ReactNode }) {
  return (
    <p
      className="rounded-lg border px-3 py-2 text-xs leading-relaxed"
      style={{
        borderColor: "var(--line)",
        background: "var(--surface-2)",
        color: "var(--ink-2)",
      }}
    >
      {children}
    </p>
  );
}
