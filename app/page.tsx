import Link from "next/link";
import { getDataset } from "@/lib/data";
import { Kartu, Petak, JudulHalaman, Catatan, LencanaPenyulang, Bilah } from "@/components/ui";
import { Tabel, TabelPendamping, type Kolom } from "@/components/Tabel";
import KomposisiSusut from "@/components/KomposisiSusut";
import TrenSusut from "@/components/charts/TrenSusut";
import BatangPeringkat from "@/components/charts/BatangPeringkat";
import { angka, kwh, persen, pp, rupiah } from "@/lib/format";
import type { Neraca, Program } from "@/lib/types";

export const revalidate = 300;

export default async function Ringkasan() {
  const ds = await getDataset();
  const k = ds.kpi;
  const A = k.skenario_a_kumulatif;
  const cukup = k.kwh_selamat_sisa >= A.gap_kwh_harus_diselamatkan;

  const gapProgram = [...ds.program]
    .map((p) => ({
      label: `${p.kode} · ${p.nama.length > 38 ? p.nama.slice(0, 37) + "…" : p.nama}`,
      nilai: Math.round(p.sisa_target * p.kwh_selamat_per_unit),
      kelompok: p.kategori === "TEKNIS" ? "Teknis" : "Non-Teknis",
      keterangan: `Capaian ${persen(p.capaian_ytd_persen, 1)} · sisa ${angka(p.sisa_target, 1)} ${p.satuan}`,
      p,
    }))
    .filter((r) => r.nilai > 0)
    .sort((a, b) => b.nilai - a.nilai)
    .slice(0, 10);

  const kolomNeraca: Kolom<Neraca>[] = [
    { kunci: "bulan", judul: "Bulan", render: (n) => n.bulan_nama },
    { kunci: "status", judul: "Status", render: (n) => (
        <span className="text-xs" style={{ color: "var(--ink-muted)" }}>{n.status_data}</span>) },
    { kunci: "susut", judul: "Susut", num: true, render: (n) => persen(n.susut_persen) },
    { kunci: "target", judul: "Target", num: true, render: (n) => persen(n.target_persen) },
    { kunci: "ytd", judul: "Kumulatif", num: true, render: (n) => persen(n.susut_ytd_persen) },
    { kunci: "salur", judul: "kWh salur", num: true, render: (n) => angka(n.kwh_salur) },
    { kunci: "susutkwh", judul: "kWh susut", num: true, render: (n) => angka(n.kwh_susut) },
  ];

  const kolomGap: Kolom<(typeof gapProgram)[number]>[] = [
    { kunci: "kode", judul: "Item", render: (r) => `${r.p.kode} · ${r.p.nama}` },
    { kunci: "kat", judul: "Kategori", render: (r) => r.kelompok },
    { kunci: "capaian", judul: "Capaian", num: true, render: (r) => persen(r.p.capaian_ytd_persen, 1) },
    { kunci: "sisa", judul: "Sisa target", num: true, render: (r) => `${angka(r.p.sisa_target, 1)} ${r.p.satuan}` },
    { kunci: "kwh", judul: "Sisa potensi kWh", num: true, render: (r) => angka(r.nilai) },
  ];

  const kategori: { nama: string; data: typeof k.kontribusi_teknis; program: Program[] }[] = [
    { nama: "Susut Teknis", data: k.kontribusi_teknis,
      program: ds.program.filter((p) => p.kategori === "TEKNIS") },
    { nama: "Susut Non-Teknis", data: k.kontribusi_nonteknis,
      program: ds.program.filter((p) => p.kategori === "NON_TEKNIS") },
  ];

  return (
    <>
      <JudulHalaman
        judul="Ringkasan Kinerja Susut"
        keterangan={`Posisi ${ds.meta.unit.nama} per ${k.periode_data} terhadap target akhir tahun ${persen(k.target_akhir_tahun_persen)}.`}
      />

      {/* Putusan besar — kesimpulan lebih dulu, rinciannya menyusul */}
      <div
        className="mb-5 flex flex-wrap items-center gap-x-6 gap-y-2 rounded-xl border px-4 py-3.5"
        style={{
          borderColor: !cukup ? "rgba(208,59,59,.35)"
            : k.status_keseluruhan === "ON TRACK" ? "rgba(12,163,12,.35)" : "rgba(250,178,25,.45)",
          background: !cukup ? "rgba(208,59,59,.08)"
            : k.status_keseluruhan === "ON TRACK" ? "rgba(12,163,12,.08)" : "rgba(250,178,25,.10)",
        }}
      >
        <span
          className="lencana"
          style={{
            background: k.status_keseluruhan === "ON TRACK" ? "var(--st-good)" : "var(--st-serious)",
            color: k.status_keseluruhan === "ON TRACK" ? "#fff" : "#3B1A08",
          }}
        >
          {k.status_keseluruhan === "ON TRACK" ? "✓" : "▲"} {k.status_keseluruhan}
        </span>
        <p className="text-sm leading-snug" style={{ color: "var(--ink)" }}>
          {cukup ? (
            <>
              Target <strong>masih bisa dicapai</strong>. Sisa potensi work plan{" "}
              <strong>{kwh(k.kwh_selamat_sisa)}</strong> melampaui gap{" "}
              <strong>{kwh(A.gap_kwh_harus_diselamatkan)}</strong> (
              {angka(k.kwh_selamat_sisa / A.gap_kwh_harus_diselamatkan, 2)}×) — syaratnya{" "}
              {k.jumlah_kritis} program berstatus KRITIS dieksekusi penuh sampai Desember.
            </>
          ) : (
            <>
              Sisa potensi work plan <strong>{kwh(k.kwh_selamat_sisa)}</strong> tidak cukup menutup
              gap <strong>{kwh(A.gap_kwh_harus_diselamatkan)}</strong>. Diperlukan program tambahan
              di luar work plan.
            </>
          )}{" "}
          <Link href="/simulasi" className="font-semibold underline underline-offset-2">
            Lihat simulasinya →
          </Link>
        </p>
      </div>

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Petak
          label="Susut kumulatif (YTD)"
          nilai={persen(k.susut_ytd_persen)}
          nada={k.susut_ytd_persen > k.target_ytd_persen ? "buruk" : "baik"}
          catatan={`Target YTD ${persen(k.target_ytd_persen)} · deviasi ${pp(k.susut_ytd_persen - k.target_ytd_persen)}`}
        />
        <Petak
          label={`Susut bulan ${k.periode_data.split(" ")[0]}`}
          nilai={persen(k.susut_bulan_ini_persen)}
          nada={k.deviasi_bulan_ini > 0 ? "peringatan" : "baik"}
          catatan={`Target ${persen(k.target_bulan_ini_persen)} · deviasi ${pp(k.deviasi_bulan_ini)}`}
        />
        <Petak
          label="Perbaikan vs tahun lalu"
          nilai={angka(k.perbaikan_vs_baseline, 2)}
          satuan="pp"
          nada="baik"
          catatan={`Dari ${persen(k.baseline_tahun_lalu_persen)} menjadi ${persen(k.susut_ytd_persen)}`}
        />
        <Petak
          label="Nilai susut YTD"
          nilai={rupiah(k.rupiah_susut_ytd)}
          nada="buruk"
          catatan={`${angka(k.kwh_susut_ytd)} kWh energi tersalur yang tidak menjadi pendapatan`}
        />
        <Petak
          label="Capaian work plan"
          nilai={persen(k.capaian_program_rata_rata, 1)}
          nada={k.capaian_program_rata_rata >= 90 ? "baik" : "peringatan"}
          catatan={`${k.jumlah_tercapai} tercapai · ${k.jumlah_waspada} waspada · ${k.jumlah_terlambat} terlambat · ${k.jumlah_kritis} kritis`}
        />
        <Petak
          label="kWh diselamatkan YTD"
          nilai={kwh(k.kwh_selamat_ytd, false)}
          satuan="kWh"
          nada="sorot"
          catatan={`Dari target ${kwh(k.kwh_selamat_target_tahun)} setahun · setara ${rupiah(k.rupiah_selamat_ytd)}`}
        />
        <Petak
          label={`Gap ke target (${k.bulan_tersisa} bulan tersisa)`}
          nilai={kwh(A.gap_kwh_harus_diselamatkan, false)}
          satuan="kWh"
          nada="buruk"
          catatan={`${angka(A.gap_kwh_per_bulan)} kWh/bulan · setara ${rupiah(A.gap_rupiah)}`}
        />
        <Petak
          label="Sisa potensi work plan"
          nilai={kwh(k.kwh_selamat_sisa, false)}
          satuan="kWh"
          nada={cukup ? "baik" : "buruk"}
          catatan={cukup ? "Cukup menutup gap bila dieksekusi penuh" : "Belum cukup menutup gap"}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Kartu
          className="lg:col-span-2"
          judul="Tren susut bulanan terhadap target"
          keterangan="Garis biru berhenti di bulan realisasi terakhir; bulan berikutnya masih berupa rencana."
        >
          <TrenSusut neraca={ds.neraca_energi} targetAkhirTahun={k.target_akhir_tahun_persen} />
          <TabelPendamping>
            <Tabel kolom={kolomNeraca} data={ds.neraca_energi} kunciBaris={(n) => String(n.bulan)} />
          </TabelPendamping>
        </Kartu>

        <Kartu
          judul="Komposisi susut bulan berjalan"
          keterangan="Susut teknis adalah rugi alamiah jaringan; non-teknis adalah energi tersalur yang tidak tertagih."
        >
          <KomposisiSusut teknis={k.susut_teknis_persen} nonTeknis={k.susut_nonteknis_persen} />
          <div className="mt-5 space-y-3">
            {kategori.map((kat) => (
              <div key={kat.nama} className="rounded-lg border p-3" style={{ borderColor: "var(--line)" }}>
                <div className="mb-2 flex items-baseline justify-between gap-2">
                  <p className="text-sm font-semibold">{kat.nama}</p>
                  <p className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {kat.program.length} item work plan
                  </p>
                </div>
                <Bilah
                  nilai={kat.data.capaian_persen}
                  warna={kat.data.capaian_persen >= 90 ? "var(--st-good)" : "var(--st-warning)"}
                />
                <p className="mt-2 text-xs" style={{ color: "var(--ink-2)" }}>
                  {kwh(kat.data.kwh_ytd)} dari target {kwh(kat.data.kwh_target_tahun)} — sisa{" "}
                  <strong>{kwh(kat.data.kwh_sisa)}</strong>
                </p>
              </div>
            ))}
          </div>
        </Kartu>

        <Kartu
          className="lg:col-span-3"
          judul="Sepuluh item work plan dengan sisa potensi kWh terbesar"
          keterangan="Inilah tempat gap ke target paling mungkin ditutup. Urutan berdasarkan kWh yang belum terealisasi, bukan besar targetnya."
          aksi={
            <Link
              href="/work-plan"
              className="rounded-lg border px-3 py-1.5 text-xs font-medium"
              style={{ borderColor: "var(--line-strong)", color: "var(--ink-2)" }}
            >
              Semua {k.jumlah_program} item →
            </Link>
          }
        >
          <BatangPeringkat
            data={gapProgram}
            format="angka"
            kelompokWarna={{ Teknis: 0, "Non-Teknis": 1 }}
            lebarLabel={250}
          />
          <TabelPendamping>
            <Tabel kolom={kolomGap} data={gapProgram} kunciBaris={(r) => r.p.kode} />
          </TabelPendamping>
        </Kartu>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Kartu
          judul="Lima penyulang prioritas"
          keterangan="Indeks prioritas menggabungkan besaran susut, ketidakseimbangan beban, faktor daya, dan drop tegangan."
          aksi={
            <Link
              href="/teknis"
              className="rounded-lg border px-3 py-1.5 text-xs font-medium"
              style={{ borderColor: "var(--line-strong)", color: "var(--ink-2)" }}
            >
              Analisis teknis →
            </Link>
          }
        >
          <Tabel
            kolom={[
              { kunci: "kode", judul: "Penyulang", render: (p) => `${p.kode} · ${p.nama}` },
              { kunci: "susut", judul: "Susut", num: true, render: (p) => persen(p.susut_persen) },
              { kunci: "unb", judul: "Unbalance", num: true, render: (p) => persen(p.unbalance_persen, 1) },
              { kunci: "cos", judul: "Cos φ", num: true, render: (p) => angka(p.cos_phi, 2) },
              { kunci: "idx", judul: "Indeks", num: true, render: (p) => angka(p.indeks_prioritas, 1) },
              { kunci: "kelas", judul: "Prioritas", render: (p) => (
                  <LencanaPenyulang kelas={p.kelas_prioritas} />) },
            ]}
            data={[...ds.penyulang].sort((a, b) => b.indeks_prioritas - a.indeks_prioritas).slice(0, 5)}
            kunciBaris={(p) => p.kode}
          />
        </Kartu>

        <Kartu
          judul="Tiga aksi paling mendesak"
          keterangan="Diambil dari rencana aksi berprioritas tertinggi."
          aksi={
            <Link
              href="/rencana-aksi"
              className="rounded-lg border px-3 py-1.5 text-xs font-medium"
              style={{ borderColor: "var(--line-strong)", color: "var(--ink-2)" }}
            >
              Semua aksi →
            </Link>
          }
        >
          <ol className="space-y-3">
            {ds.action_plan.slice(0, 3).map((a) => (
              <li key={a.no} className="rounded-lg border p-3" style={{ borderColor: "var(--line)" }}>
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <span className="lencana" style={{ background: "var(--st-critical)", color: "#fff" }}>
                    {a.prioritas}
                  </span>
                  <span className="text-xs" style={{ color: "var(--ink-muted)" }}>
                    {a.program_kode} · PIC {a.pic}
                  </span>
                </div>
                <p className="text-sm leading-snug">{a.aksi}</p>
                <p className="mt-1.5 text-xs" style={{ color: "var(--ink-2)" }}>
                  {a.dampak_kwh_bulan > 0
                    ? `Dampak ${kwh(a.dampak_kwh_bulan)}/bulan`
                    : "Dampak finansial (pemulihan piutang), bukan kWh"}{" "}
                  · target selesai {a.target_selesai}
                </p>
              </li>
            ))}
          </ol>
        </Kartu>
      </div>

      <div className="mt-4">
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
