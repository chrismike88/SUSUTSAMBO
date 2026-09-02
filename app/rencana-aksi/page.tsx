import { getDataset } from "@/lib/data";
import { Kartu, Petak, JudulHalaman, Catatan, LencanaPrioritas, LencanaStatus, Bilah } from "@/components/ui";
import BatangPeringkat from "@/components/charts/BatangPeringkat";
import { Tabel, TabelPendamping } from "@/components/Tabel";
import { angka, kwh, rupiah, persen } from "@/lib/format";

export const metadata = { title: "Rencana Aksi" };
export const revalidate = 300;

const WARNA_STATUS_AKSI: Record<string, string> = {
  TERCAPAI: "var(--st-good)",
  BERJALAN: "var(--viz-1)",
  TERLAMBAT: "var(--st-critical)",
  RENCANA: "var(--viz-muted)",
};

export default async function HalamanRencanaAksi() {
  const ds = await getDataset();
  const k = ds.kpi;
  const aksi = ds.action_plan;

  const totalDampakBulan = aksi.reduce((a, x) => a + x.dampak_kwh_bulan, 0);
  const totalDampakSisa = aksi.reduce((a, x) => a + x.dampak_kwh_sisa_tahun, 0);
  const gap = k.skenario_a_kumulatif.gap_kwh_harus_diselamatkan;
  const terlambat = aksi.filter((a) => a.status === "TERLAMBAT").length;

  const dampak = [...aksi]
    .filter((a) => a.dampak_kwh_sisa_tahun > 0)
    .sort((a, b) => b.dampak_kwh_sisa_tahun - a.dampak_kwh_sisa_tahun)
    .map((a) => ({
      label: `${a.program_kode} · ${a.aksi.slice(0, 32)}…`,
      nilai: a.dampak_kwh_sisa_tahun,
      kelompok: a.kategori === "TEKNIS" ? "Teknis" : "Non-Teknis",
      keterangan: `${a.prioritas} · PIC ${a.pic} · target ${a.target_selesai}`,
    }));

  return (
    <>
      <JudulHalaman
        judul="Rencana Aksi Menuju Target"
        keterangan={`Apa yang harus dikerjakan pada ${k.bulan_tersisa} bulan tersisa. Urutan mengikuti prioritas, bukan nomor program. Setiap aksi menyebut akar masalahnya agar tindakan tidak berhenti pada gejala.`}
      />

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Petak label="Jumlah aksi" nilai={String(aksi.length)} satuan="aksi"
          catatan={`${aksi.filter((a) => a.prioritas === "SANGAT TINGGI").length} berprioritas sangat tinggi`} />
        <Petak label="Aksi terlambat" nilai={String(terlambat)} satuan="aksi"
          nada={terlambat > 0 ? "buruk" : "baik"}
          catatan="Realisasi tertinggal dari jadwal — perlu keputusan penambahan sumber daya" />
        <Petak label="Total dampak per bulan" nilai={kwh(totalDampakBulan, false)} satuan="kWh"
          nada="sorot" catatan={`Setara ${rupiah(totalDampakBulan * (ds.meta.parameter.tarif_rata_rata ?? 1462.5))} per bulan`} />
        <Petak label="Dampak s/d akhir tahun" nilai={kwh(totalDampakSisa, false)} satuan="kWh"
          nada={totalDampakSisa >= gap ? "baik" : "buruk"}
          catatan={totalDampakSisa >= gap
            ? `Melampaui gap ${kwh(gap)} bila seluruhnya tuntas`
            : `Masih kurang dari gap ${kwh(gap)}`} />
      </div>

      <Kartu
        judul="Aksi menurut besarnya dampak"
        keterangan="Dampak dihitung dari sisa target program terkait dikalikan faktor kWh diselamatkan per satuan."
      >
        <BatangPeringkat
          data={dampak}
          format="angka"
          kelompokWarna={{ Teknis: 0, "Non-Teknis": 1 }}
          lebarLabel={260}
          tinggiBaris={32}
        />
        <TabelPendamping>
          <Tabel
            kolom={[
              { kunci: "k", judul: "Program", render: (d) => d.label },
              { kunci: "kat", judul: "Kategori", render: (d) => d.kelompok },
              { kunci: "n", judul: "Dampak kWh s/d Des", num: true, render: (d) => angka(d.nilai) },
            ]}
            data={dampak}
            kunciBaris={(d) => d.label}
          />
        </TabelPendamping>
      </Kartu>

      <div className="mt-4 space-y-3">
        {aksi.map((a) => (
          <article key={a.no} className="kartu p-4 sm:p-5">
            <div className="flex flex-wrap items-start gap-x-3 gap-y-2">
              <span
                className="grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-bold"
                style={{ background: "var(--surface-2)", color: "var(--ink-2)" }}
              >
                {a.no}
              </span>
              <div className="min-w-0 flex-1">
                <div className="mb-1.5 flex flex-wrap items-center gap-2">
                  <LencanaPrioritas prioritas={a.prioritas} />
                  <span className="lencana" style={{
                    background: "var(--surface-2)", color: "var(--ink-2)",
                    borderColor: "var(--line)",
                  }}>
                    {a.kategori === "TEKNIS" ? "Teknis" : "Non-Teknis"} · {a.program_kode}
                  </span>
                  <span className="lencana" style={{
                    background: WARNA_STATUS_AKSI[a.status] ?? "var(--viz-muted)", color: "#fff",
                  }}>
                    {a.status}
                  </span>
                  <LencanaStatus status={a.status_program} />
                </div>
                <p className="text-sm font-medium leading-snug">{a.aksi}</p>
                <p className="mt-1.5 text-xs leading-snug" style={{ color: "var(--ink-2)" }}>
                  <strong style={{ color: "var(--ink)" }}>Akar masalah:</strong> {a.akar_masalah}
                </p>
              </div>
            </div>

            <dl className="mt-3.5 grid grid-cols-2 gap-3 border-t pt-3 text-xs sm:grid-cols-3 lg:grid-cols-6"
                style={{ borderColor: "var(--line)" }}>
              {[
                ["Sisa volume", `${angka(a.sisa_volume, 1)} ${a.satuan}`],
                ["Kebutuhan / bulan", `${angka(a.kebutuhan_per_bulan, 1)} ${a.satuan}`],
                ["Dampak kWh / bulan", a.dampak_kwh_bulan > 0 ? angka(a.dampak_kwh_bulan) : "finansial"],
                ["Nilai s/d Desember", rupiah(a.dampak_rupiah_sisa_tahun)],
                ["Penanggung jawab", a.pic],
                ["Target selesai", a.target_selesai],
              ].map(([label, nilai]) => (
                <div key={label}>
                  <dt style={{ color: "var(--ink-muted)" }}>{label}</dt>
                  <dd className="mt-0.5 font-semibold tabular-nums">{nilai}</dd>
                </div>
              ))}
            </dl>

            <div className="mt-3 flex items-center gap-3">
              <span className="shrink-0 text-xs" style={{ color: "var(--ink-muted)" }}>
                Progres
              </span>
              <Bilah
                nilai={a.progres_persen}
                maks={Math.max(100, a.progres_persen)}
                warna={
                  a.progres_persen >= 100 ? "var(--st-good)"
                  : a.status === "TERLAMBAT" ? "var(--st-critical)" : "var(--viz-1)"
                }
              />
              <span className="shrink-0 text-xs" style={{ color: "var(--ink-muted)" }}>
                capaian program {persen(a.capaian_ytd_persen, 1)}
              </span>
            </div>
          </article>
        ))}
      </div>

      <div className="mt-4 space-y-2">
        <Catatan>
          <strong>Cara memakai halaman ini dalam rapat mingguan.</strong> Bahas hanya aksi
          berprioritas SANGAT TINGGI dan yang berstatus TERLAMBAT — biasanya lima sampai enam baris.
          Untuk tiap baris tanyakan tiga hal: berapa yang selesai minggu ini, apa penghambatnya
          (material, regu, izin, atau anggaran), dan apakah kebutuhan per bulan masih realistis.
          Bila kebutuhan per bulan sudah tidak masuk akal, keputusannya bukan menambah imbauan
          melainkan menambah sumber daya atau merevisi target ke UP3.
        </Catatan>
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
