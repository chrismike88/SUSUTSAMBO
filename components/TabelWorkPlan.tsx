"use client";

import { useMemo, useState } from "react";
import type { Program } from "@/lib/types";
import { angka, kwh, persen, rupiah } from "@/lib/format";
import { LencanaStatus, Bilah } from "@/components/ui";

type Urut = "capaian" | "sisa_kwh" | "faktor" | "kode";

const STATUS = ["TERCAPAI", "WASPADA", "TERLAMBAT", "KRITIS"] as const;

export default function TabelWorkPlan({
  program,
  tarif,
}: {
  program: Program[];
  tarif: number;
}) {
  const [kategori, setKategori] = useState<"SEMUA" | "TEKNIS" | "NON_TEKNIS">("SEMUA");
  const [status, setStatus] = useState<string>("SEMUA");
  const [urut, setUrut] = useState<Urut>("capaian");

  const baris = useMemo(() => {
    const dengan = program
      .filter((p) => kategori === "SEMUA" || p.kategori === kategori)
      .filter((p) => status === "SEMUA" || p.status === status)
      .map((p) => ({ ...p, sisa_kwh: Math.round(p.sisa_target * p.kwh_selamat_per_unit) }));
    const bandingkan: Record<Urut, (a: typeof dengan[number], b: typeof dengan[number]) => number> = {
      capaian: (a, b) => a.capaian_ytd_persen - b.capaian_ytd_persen,
      sisa_kwh: (a, b) => b.sisa_kwh - a.sisa_kwh,
      faktor: (a, b) => (b.faktor_kejar ?? 0) - (a.faktor_kejar ?? 0),
      kode: (a, b) => a.kode.localeCompare(b.kode),
    };
    return dengan.sort(bandingkan[urut]);
  }, [program, kategori, status, urut]);

  const totalSisaKwh = baris.reduce((a, p) => a + p.sisa_kwh, 0);

  const chip = (aktif: boolean) =>
    `rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
      aktif ? "border-transparent text-white" : "hover:opacity-80"
    }`;
  const gayaChip = (aktif: boolean) =>
    aktif
      ? { background: "var(--brand-2)" }
      : { borderColor: "var(--line-strong)", color: "var(--ink-2)" };

  return (
    <div>
      {/* Satu baris penyaring di atas tabel — bukan penyaring per kolom */}
      <div className="mb-3 flex flex-wrap items-center gap-x-5 gap-y-2">
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold" style={{ color: "var(--ink-muted)" }}>
            Kategori
          </span>
          {(["SEMUA", "TEKNIS", "NON_TEKNIS"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setKategori(k)}
              className={chip(kategori === k)}
              style={gayaChip(kategori === k)}
            >
              {k === "SEMUA" ? "Semua" : k === "TEKNIS" ? "Teknis" : "Non-Teknis"}
            </button>
          ))}
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="mr-1 text-xs font-semibold" style={{ color: "var(--ink-muted)" }}>
            Status
          </span>
          {["SEMUA", ...STATUS].map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setStatus(k)}
              className={chip(status === k)}
              style={gayaChip(status === k)}
            >
              {k === "SEMUA" ? "Semua" : k}
            </button>
          ))}
        </div>
        <label className="ml-auto flex items-center gap-2 text-xs" style={{ color: "var(--ink-muted)" }}>
          Urutkan
          <select
            value={urut}
            onChange={(e) => setUrut(e.target.value as Urut)}
            className="rounded-lg border bg-transparent px-2 py-1 text-xs"
            style={{ borderColor: "var(--line-strong)", color: "var(--ink)" }}
          >
            <option value="capaian">Capaian terendah</option>
            <option value="sisa_kwh">Sisa potensi kWh terbesar</option>
            <option value="faktor">Faktor kejar tertinggi</option>
            <option value="kode">Kode item</option>
          </select>
        </label>
      </div>

      <div className="gulir-x rounded-lg border" style={{ borderColor: "var(--line)" }}>
        <table className="tabel">
          <thead>
            <tr>
              <th>Kode</th>
              <th style={{ minWidth: 260 }}>Item work plan</th>
              <th className="num">Target tahun</th>
              <th className="num">Target s/d bln</th>
              <th className="num">Realisasi</th>
              <th style={{ minWidth: 140 }}>Capaian YTD</th>
              <th className="num">Sisa target</th>
              <th className="num">Kebutuhan/bln</th>
              <th className="num">Faktor kejar</th>
              <th className="num">Sisa potensi kWh</th>
              <th>Status</th>
              <th>PIC</th>
            </tr>
          </thead>
          <tbody>
            {baris.map((p) => (
              <tr key={p.kode}>
                <td className="font-semibold">{p.kode}</td>
                <td>
                  <span className="block leading-snug">{p.nama}</span>
                  <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {p.sub_kategori} · {p.siklus} · satuan {p.satuan}
                  </span>
                </td>
                <td className="num">{angka(p.target_tahun, 1)}</td>
                <td className="num">{angka(p.target_ytd, 1)}</td>
                <td className="num">{angka(p.realisasi_ytd, 1)}</td>
                <td>
                  <div className="flex items-center gap-2">
                    <Bilah
                      nilai={Math.min(p.capaian_ytd_persen, 120)}
                      maks={120}
                      warna={
                        p.capaian_ytd_persen >= 100 ? "var(--st-good)"
                        : p.capaian_ytd_persen >= 90 ? "var(--viz-3)"
                        : p.capaian_ytd_persen >= 75 ? "var(--st-warning)"
                        : "var(--st-critical)"
                      }
                      tampilAngka={false}
                    />
                    <span className="w-14 shrink-0 text-right tabular-nums">
                      {persen(p.capaian_ytd_persen, 1)}
                    </span>
                  </div>
                </td>
                <td className="num">{angka(p.sisa_target, 1)}</td>
                <td className="num">{angka(p.kebutuhan_per_bulan_sisa, 1)}</td>
                <td className="num">
                  <span
                    className={p.faktor_kejar && p.faktor_kejar >= 2 ? "font-bold" : ""}
                    style={{ color: p.faktor_kejar && p.faktor_kejar >= 2 ? "var(--st-critical)" : undefined }}
                    title={
                      p.faktor_kejar && p.faktor_kejar >= 2
                        ? "Harus lebih dari dua kali lebih cepat dari kecepatan saat ini"
                        : undefined
                    }
                  >
                    {p.faktor_kejar ? `${angka(p.faktor_kejar, 2)}×` : "–"}
                  </span>
                </td>
                <td className="num">
                  {p.kwh_selamat_per_unit > 0 ? (
                    angka(p.sisa_kwh)
                  ) : (
                    <span title="Program ini diukur secara finansial atau sebagai aktivitas; kWh-nya dihitung pada item lain">
                      –
                    </span>
                  )}
                </td>
                <td><LencanaStatus status={p.status} /></td>
                <td className="whitespace-nowrap text-xs" style={{ color: "var(--ink-2)" }}>
                  {p.pic.replace("Supervisor ", "SPV ")}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={9} className="font-semibold" style={{ background: "var(--surface-2)" }}>
                {baris.length} item ditampilkan
              </td>
              <td className="num font-bold" style={{ background: "var(--surface-2)" }}>
                {angka(totalSisaKwh)}
              </td>
              <td colSpan={2} className="text-xs" style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}>
                setara {rupiah(totalSisaKwh * tarif)} — {kwh(totalSisaKwh)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  );
}
