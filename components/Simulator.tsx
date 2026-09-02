"use client";

import { useMemo, useState } from "react";
import { angka, kwh, persen, rupiah, rupiahPenuh } from "@/lib/format";

export interface MasukanSimulasi {
  kwhSalurYtd: number;
  kwhSusutYtd: number;
  salurSisa: number;
  salurDesember: number;
  susutBulanTerakhir: number;
  targetAwal: number;
  kwhSelamatSisa: number;
  bulanSisa: number;
  tarif: number;
}

function Penggeser({
  label,
  nilai,
  min,
  maks,
  langkah,
  ubah,
  tampil,
  bantuan,
}: {
  label: string;
  nilai: number;
  min: number;
  maks: number;
  langkah: number;
  ubah: (v: number) => void;
  tampil: string;
  bantuan?: string;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label className="text-sm font-medium" htmlFor={label}>
          {label}
        </label>
        <output className="text-sm font-bold tabular-nums" style={{ color: "var(--viz-1)" }}>
          {tampil}
        </output>
      </div>
      <input
        id={label}
        type="range"
        min={min}
        max={maks}
        step={langkah}
        value={nilai}
        onChange={(e) => ubah(Number(e.target.value))}
        className="mt-2 h-1.5 w-full cursor-pointer appearance-none rounded-full"
        style={{ background: "var(--line)", accentColor: "var(--viz-1)" }}
      />
      {bantuan && (
        <p className="mt-1 text-xs" style={{ color: "var(--ink-muted)" }}>
          {bantuan}
        </p>
      )}
    </div>
  );
}

export default function Simulator({ m }: { m: MasukanSimulasi }) {
  const [target, setTarget] = useState(m.targetAwal);
  const [eksekusi, setEksekusi] = useState(100);
  const [faktorBeban, setFaktorBeban] = useState(100);
  const [susutDasar, setSusutDasar] = useState(m.susutBulanTerakhir);

  const h = useMemo(() => {
    const salurSisa = m.salurSisa * (faktorBeban / 100);
    const salurDes = m.salurDesember * (faktorBeban / 100);
    const salurSetahun = m.kwhSalurYtd + salurSisa;

    const hemat = m.kwhSelamatSisa * (eksekusi / 100);
    const susutSisaTanpaAksi = salurSisa * (susutDasar / 100);
    const susutSisaDenganAksi = Math.max(susutSisaTanpaAksi - hemat, 0);

    // Skenario A — susut kumulatif setahun
    const susutMaksSetahun = salurSetahun * (target / 100);
    const izinSisa = susutMaksSetahun - m.kwhSusutYtd;
    const izinSisaPersen = (izinSisa / salurSisa) * 100;
    const gapA = susutSisaTanpaAksi - izinSisa;
    const proyeksiKumulatif =
      ((m.kwhSusutYtd + susutSisaDenganAksi) / salurSetahun) * 100;

    // Skenario B — susut bulan Desember (exit rate)
    const hematBulanan = hemat / m.bulanSisa;
    const susutDesTanpaAksi = salurDes * (susutDasar / 100);
    const susutDesDenganAksi = Math.max(susutDesTanpaAksi - hematBulanan, 0);
    const proyeksiDesember = (susutDesDenganAksi / salurDes) * 100;
    const gapB = susutDesTanpaAksi - salurDes * (target / 100);

    return {
      salurSisa, salurSetahun, hemat, hematBulanan,
      susutSisaTanpaAksi, susutSisaDenganAksi,
      susutMaksSetahun, izinSisa, izinSisaPersen, gapA, proyeksiKumulatif,
      proyeksiDesember, gapB,
      cukupA: proyeksiKumulatif <= target,
      cukupB: proyeksiDesember <= target,
      rasio: gapA > 0 ? m.kwhSelamatSisa / gapA : Infinity,
    };
  }, [m, target, eksekusi, faktorBeban, susutDasar]);

  const kotak = (
    judul: string,
    proyeksi: number,
    tercapai: boolean,
    baris: [string, string][],
    catatan: string,
  ) => (
    <div
      className="rounded-xl border p-4"
      style={{
        borderColor: tercapai ? "rgba(12,163,12,.4)" : "rgba(208,59,59,.4)",
        background: tercapai ? "rgba(12,163,12,.06)" : "rgba(208,59,59,.06)",
      }}
    >
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">{judul}</h3>
        <span
          className="lencana"
          style={{ background: tercapai ? "var(--st-good)" : "var(--st-critical)", color: "#fff" }}
        >
          {tercapai ? "✓ TARGET TERCAPAI" : "✕ TARGET TIDAK TERCAPAI"}
        </span>
      </div>
      <p className="angka-hero" style={{ color: tercapai ? "var(--st-good)" : "var(--st-critical)" }}>
        {persen(proyeksi)}
      </p>
      <p className="mt-1 text-xs" style={{ color: "var(--ink-2)" }}>
        proyeksi akhir tahun dengan asumsi di sebelah kiri · target {persen(target)}
      </p>
      <dl className="mt-3 space-y-1.5 border-t pt-3 text-xs" style={{ borderColor: "var(--line)" }}>
        {baris.map(([a, b]) => (
          <div key={a} className="flex justify-between gap-3">
            <dt style={{ color: "var(--ink-muted)" }}>{a}</dt>
            <dd className="font-semibold tabular-nums">{b}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs leading-snug" style={{ color: "var(--ink-2)" }}>
        {catatan}
      </p>
    </div>
  );

  return (
    <div className="grid gap-4 lg:grid-cols-3">
      <section className="kartu p-4 sm:p-5">
        <h2 className="text-[0.95rem] font-semibold">Asumsi</h2>
        <p className="mt-0.5 text-xs" style={{ color: "var(--ink-muted)" }}>
          Geser untuk menguji berbagai kemungkinan. Hasilnya berubah seketika.
        </p>
        <div className="mt-5 space-y-5">
          <Penggeser
            label="Target susut akhir tahun"
            nilai={target}
            min={4.5}
            maks={7.5}
            langkah={0.05}
            ubah={setTarget}
            tampil={persen(target)}
            bantuan={`Nilai RKAP saat ini ${persen(m.targetAwal)}`}
          />
          <Penggeser
            label="Tingkat eksekusi sisa work plan"
            nilai={eksekusi}
            min={0}
            maks={100}
            langkah={5}
            ubah={setEksekusi}
            tampil={`${eksekusi}%`}
            bantuan={`100% berarti seluruh sisa target ${kwh(m.kwhSelamatSisa)} tuntas sampai Desember`}
          />
          <Penggeser
            label="Susut dasar tanpa aksi tambahan"
            nilai={susutDasar}
            min={4}
            maks={8}
            langkah={0.01}
            ubah={setSusutDasar}
            tampil={persen(susutDasar)}
            bantuan={`Bawaan memakai realisasi bulan terakhir ${persen(m.susutBulanTerakhir)}`}
          />
          <Penggeser
            label="Proyeksi beban Sep–Des"
            nilai={faktorBeban}
            min={85}
            maks={125}
            langkah={1}
            ubah={setFaktorBeban}
            tampil={`${faktorBeban}%`}
            bantuan="Naikkan bila pertumbuhan beban di sekitar wilayah kerja melebihi rencana"
          />
        </div>

        <button
          type="button"
          onClick={() => {
            setTarget(m.targetAwal);
            setEksekusi(100);
            setFaktorBeban(100);
            setSusutDasar(m.susutBulanTerakhir);
          }}
          className="mt-6 w-full rounded-lg border px-3 py-2 text-xs font-medium"
          style={{ borderColor: "var(--line-strong)", color: "var(--ink-2)" }}
        >
          Kembalikan ke asumsi awal
        </button>

        <dl className="mt-5 space-y-1.5 border-t pt-4 text-xs" style={{ borderColor: "var(--line)" }}>
          {[
            ["kWh salur kumulatif (tetap)", angka(m.kwhSalurYtd)],
            ["kWh susut kumulatif (tetap)", angka(m.kwhSusutYtd)],
            ["Proyeksi kWh salur Sep–Des", angka(Math.round(h.salurSisa))],
            ["kWh diselamatkan dari eksekusi", angka(Math.round(h.hemat))],
          ].map(([a, b]) => (
            <div key={a} className="flex justify-between gap-3">
              <dt style={{ color: "var(--ink-muted)" }}>{a}</dt>
              <dd className="font-semibold tabular-nums">{b}</dd>
            </div>
          ))}
        </dl>
      </section>

      <div className="space-y-4 lg:col-span-2">
        {kotak(
          "Skenario A — target dibaca sebagai susut kumulatif (YTD) akhir tahun",
          h.proyeksiKumulatif,
          h.cukupA,
          [
            ["kWh susut maksimum setahun", angka(Math.round(h.susutMaksSetahun))],
            ["Masih boleh susut Sep–Des", angka(Math.round(h.izinSisa))],
            ["Setara susut Sep–Des maksimum", persen(h.izinSisaPersen)],
            ["Gap bila tanpa aksi tambahan", angka(Math.round(Math.max(h.gapA, 0)))],
            ["Nilai finansial gap", rupiah(Math.max(h.gapA, 0) * m.tarif)],
            ["Rasio kecukupan work plan", h.rasio === Infinity ? "—" : `${angka(h.rasio, 2)}×`],
          ],
          "Ini tafsir yang umum dipakai saat menilai kinerja RKAP, dan yang paling berat: satu bulan buruk di awal tahun ikut menyeret angka kumulatif sampai Desember.",
        )}
        {kotak(
          "Skenario B — target dibaca sebagai susut bulan Desember (exit rate)",
          h.proyeksiDesember,
          h.cukupB,
          [
            ["Penurunan dibutuhkan dari bulan terakhir", `${angka(susutDasar - target, 2)} pp`],
            ["kWh susut maksimum di Desember", angka(Math.round(m.salurDesember * (faktorBeban / 100) * (target / 100)))],
            ["Penghematan bulanan dari eksekusi", angka(Math.round(h.hematBulanan))],
            ["Gap bila tanpa aksi tambahan", angka(Math.round(Math.max(h.gapB, 0)))],
            ["Nilai finansial gap", rupiah(Math.max(h.gapB, 0) * m.tarif)],
          ],
          "Tafsir ini menilai kondisi akhir jaringan, bukan rata-rata setahun. Jauh lebih ringan dicapai, dan lebih jujur menggambarkan hasil kerja semester dua.",
        )}

        <div
          className="rounded-xl border p-4 text-xs leading-relaxed"
          style={{ borderColor: "var(--line)", background: "var(--surface-2)", color: "var(--ink-2)" }}
        >
          <p className="mb-1.5 font-semibold" style={{ color: "var(--ink)" }}>
            Asumsi yang dipakai perhitungan ini
          </p>
          <ul className="list-disc space-y-1 pl-4">
            <li>
              Sisa potensi kWh work plan dihitung dari sisa volume tiap item dikalikan faktor kWh
              diselamatkan per satuan, dan dianggap terwujud di dalam periode Sep–Des.
            </li>
            <li>
              Penghematan disebar rata ke {m.bulanSisa} bulan tersisa untuk perhitungan exit rate
              bulan Desember.
            </li>
            <li>
              kWh salur kumulatif dan kWh susut kumulatif adalah realisasi yang sudah terjadi,
              sehingga tidak dapat diubah oleh asumsi apa pun.
            </li>
            <li>
              Tarif konversi ke rupiah {rupiahPenuh(m.tarif)} per kWh mengikuti parameter unit.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
