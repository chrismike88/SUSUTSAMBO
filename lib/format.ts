/** Pemformatan angka gaya Indonesia (pemisah ribuan titik, desimal koma). */

const nf = (min: number, max: number) =>
  new Intl.NumberFormat("id-ID", { minimumFractionDigits: min, maximumFractionDigits: max });

export const angka = (v: number | null | undefined, desimal = 0) =>
  v === null || v === undefined || Number.isNaN(v) ? "–" : nf(desimal, desimal).format(v);

export const persen = (v: number | null | undefined, desimal = 2) =>
  v === null || v === undefined || Number.isNaN(v) ? "–" : `${nf(desimal, desimal).format(v)}%`;

export const pp = (v: number | null | undefined, desimal = 2) => {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  const t = nf(desimal, desimal).format(Math.abs(v));
  return `${v > 0 ? "+" : v < 0 ? "−" : ""}${t} pp`;
};

/** Rupiah ringkas: 1.904.500.917 -> "Rp 1,90 M" */
export function rupiah(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  const abs = Math.abs(v);
  if (abs >= 1e12) return `Rp ${nf(2, 2).format(v / 1e12)} T`;
  if (abs >= 1e9) return `Rp ${nf(2, 2).format(v / 1e9)} M`;
  if (abs >= 1e6) return `Rp ${nf(1, 1).format(v / 1e6)} jt`;
  if (abs >= 1e3) return `Rp ${nf(0, 0).format(v / 1e3)} rb`;
  return `Rp ${nf(0, 0).format(v)}`;
}

export const rupiahPenuh = (v: number | null | undefined) =>
  v === null || v === undefined ? "–" : `Rp ${nf(0, 0).format(v)}`;

/** kWh ringkas: 1302223 -> "1,30 juta kWh" */
export function kwh(v: number | null | undefined, satuan = true): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "–";
  const s = satuan ? " kWh" : "";
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${nf(2, 2).format(v / 1e9)} miliar${s}`;
  if (abs >= 1e6) return `${nf(2, 2).format(v / 1e6)} juta${s}`;
  if (abs >= 1e3) return `${nf(1, 1).format(v / 1e3)} ribu${s}`;
  return `${nf(0, 0).format(v)}${s}`;
}

export const WARNA_STATUS: Record<string, { teks: string; latar: string; garis: string; hex: string }> = {
  TERCAPAI:  { teks: "text-emerald-700", latar: "bg-emerald-50", garis: "border-emerald-200", hex: "#16A34A" },
  WASPADA:   { teks: "text-teal-700",    latar: "bg-teal-50",    garis: "border-teal-200",    hex: "#0E9F9F" },
  TERLAMBAT: { teks: "text-amber-700",   latar: "bg-amber-50",   garis: "border-amber-200",   hex: "#F59E0B" },
  KRITIS:    { teks: "text-red-700",     latar: "bg-red-50",     garis: "border-red-200",     hex: "#DC2626" },
  "N/A":     { teks: "text-slate-600",   latar: "bg-slate-50",   garis: "border-slate-200",   hex: "#64748B" },
};

export const WARNA_PRIORITAS: Record<string, string> = {
  "SANGAT TINGGI": "bg-red-600 text-white",
  TINGGI: "bg-orange-500 text-white",
  SEDANG: "bg-amber-100 text-amber-900",
  RUTIN: "bg-slate-100 text-slate-700",
};

/** Nama format yang bisa dikirim dari Server Component ke Client Component
 *  (fungsi tidak boleh dilewatkan melintasi batas server/klien). */
export type FormatNama =
  | "angka" | "angka1" | "angka2"
  | "persen" | "persen1"
  | "kwh" | "kwhAngka"
  | "rupiah" | "rupiahPenuh" | "ribu" | "juta" | "juta1";

export function pakaiFormat(nama: FormatNama): (v: number) => string {
  switch (nama) {
    case "angka1": return (v) => angka(v, 1);
    case "angka2": return (v) => angka(v, 2);
    case "persen": return (v) => persen(v);
    case "persen1": return (v) => persen(v, 1);
    case "kwh": return (v) => kwh(v);
    case "kwhAngka": return (v) => `${angka(v)} kWh`;
    case "rupiah": return (v) => rupiah(v);
    case "ribu": return (v) => `${angka(v / 1e3, 0)} rb`;
    case "juta": return (v) => `${angka(v / 1e6, 2)} jt`;
    case "juta1": return (v) => `${angka(v / 1e6, 1)} jt`;
    case "rupiahPenuh": return (v) => rupiahPenuh(v);
    default: return (v) => angka(v);
  }
}
