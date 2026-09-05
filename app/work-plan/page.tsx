import { getDataset } from "@/lib/data";
import { Kartu, Petak, JudulHalaman, Catatan } from "@/components/ui";
import { TabelPendamping, Tabel } from "@/components/Tabel";
import TabelWorkPlan from "@/components/TabelWorkPlan";
import GarisBulanan from "@/components/charts/GarisBulanan";
import { angka, kwh, persen } from "@/lib/format";

export const metadata = { title: "Capaian Work Plan" };
export const revalidate = 300;

export default async function HalamanWorkPlan() {
  const ds = await getDataset();
  const k = ds.kpi;
  const tarif = ds.meta.parameter.tarif_rata_rata ?? 1462.5;

  // Kurva kumulatif kWh diselamatkan: realisasi vs target
  const perBulan = ds.meta.bulan_nama.map((nama, i) => {
    const bulan = i + 1;
    const rows = ds.program_bulanan.filter((r) => r.bulan === bulan);
    return {
      bulan: nama,
      targetKwh: rows.reduce((a, r) => a + r.target_kwh, 0),
      realKwh: bulan <= k.bulan_realisasi ? rows.reduce((a, r) => a + (r.realisasi_kwh ?? 0), 0) : null,
    };
  });
  let kt = 0;
  let kr = 0;
  const kumulatif = perBulan.map((b) => {
    kt += b.targetKwh;
    if (b.realKwh !== null) kr += b.realKwh;
    return {
      bulan: b.bulan,
      target: Math.round(kt),
      realisasi: b.realKwh !== null ? Math.round(kr) : null,
    };
  });

  const perStatus = [
    { nama: "TERCAPAI", jml: k.jumlah_tercapai, nada: "baik" as const },
    { nama: "WASPADA", jml: k.jumlah_waspada, nada: "sorot" as const },
    { nama: "TERLAMBAT", jml: k.jumlah_terlambat, nada: "peringatan" as const },
    { nama: "KRITIS", jml: k.jumlah_kritis, nada: "buruk" as const },
  ];

  return (
    <>
      <JudulHalaman
        judul="Capaian per Item Work Plan"
        keterangan={`Realisasi ${k.jumlah_program} item program penurunan susut s/d ${k.periode_data}, terhadap target bulanan maupun target akhir tahun. Kolom faktor kejar menunjukkan berapa kali lipat kecepatan kerja harus dinaikkan pada ${k.bulan_tersisa} bulan tersisa.`}
      />

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        {perStatus.map((s) => (
          <Petak
            key={s.nama}
            label={s.nama}
            nilai={String(s.jml)}
            satuan="item"
            nada={s.nada}
            catatan={
              s.nama === "TERCAPAI" ? "Capaian ≥ 100% target s/d bulan berjalan"
              : s.nama === "WASPADA" ? "Capaian 90–99%, masih bisa dikejar"
              : s.nama === "TERLAMBAT" ? "Capaian 75–89%, butuh percepatan"
              : "Capaian < 75%, wajib masuk rapat mingguan"
            }
          />
        ))}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Kartu
          className="lg:col-span-2"
          judul="Kurva kumulatif kWh yang diselamatkan"
          keterangan="Jarak vertikal antara kedua garis adalah utang pekerjaan yang harus dilunasi sampai Desember."
        >
          <GarisBulanan
            data={kumulatif}
            seri={[
              { kunci: "target", nama: "Target kumulatif", slot: 1, putus: true },
              { kunci: "realisasi", nama: "Realisasi kumulatif", slot: 0 },
            ]}
            format="kwh"
            formatSumbu="juta1"
            tinggi={300}
          />
          <TabelPendamping>
            <Tabel
              kolom={[
                { kunci: "b", judul: "Bulan", render: (r) => r.bulan },
                { kunci: "t", judul: "Target kumulatif (kWh)", num: true, render: (r) => angka(r.target) },
                { kunci: "r", judul: "Realisasi kumulatif (kWh)", num: true,
                  render: (r) => (r.realisasi === null ? "–" : angka(r.realisasi)) },
                { kunci: "g", judul: "Selisih (kWh)", num: true,
                  render: (r) => (r.realisasi === null ? "–" : angka(r.realisasi - r.target)) },
              ]}
              data={kumulatif}
              kunciBaris={(r) => r.bulan}
            />
          </TabelPendamping>
        </Kartu>

        <Kartu judul="Kontribusi per kategori" keterangan="Target kWh diselamatkan setahun dan posisinya sekarang.">
          <div className="space-y-4">
            {[
              { nama: "Program teknis", d: k.kontribusi_teknis },
              { nama: "Program non-teknis", d: k.kontribusi_nonteknis },
            ].map((x) => (
              <div key={x.nama} className="rounded-lg border p-3.5" style={{ borderColor: "var(--line)" }}>
                <p className="text-sm font-semibold">{x.nama}</p>
                <p className="angka-hero mt-1.5" style={{ fontSize: "1.5rem", color: "var(--viz-1)" }}>
                  {persen(x.d.capaian_persen, 1)}
                </p>
                <dl className="mt-3 space-y-1.5 text-xs">
                  {[
                    ["Target setahun", kwh(x.d.kwh_target_tahun)],
                    ["Terealisasi", kwh(x.d.kwh_ytd)],
                    ["Sisa", kwh(x.d.kwh_sisa)],
                  ].map(([a, b]) => (
                    <div key={a} className="flex justify-between gap-3">
                      <dt style={{ color: "var(--ink-muted)" }}>{a}</dt>
                      <dd className="font-semibold tabular-nums">{b}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </Kartu>
      </div>

      <div className="mt-4">
        <Kartu
          judul={`Rincian ${k.jumlah_program} item work plan`}
          keterangan="Gunakan penyaring untuk memusatkan perhatian; urutan bawaan menampilkan capaian terendah lebih dulu."
        >
          <TabelWorkPlan program={ds.program} tarif={tarif} />
        </Kartu>
      </div>

      <div className="mt-4 space-y-2">
        <Catatan>
          <strong>Cara membaca faktor kejar.</strong> Faktor kejar = kebutuhan volume per bulan
          tersisa dibagi kecepatan rata-rata bulanan yang sudah tercapai. Nilai 1,0 berarti cukup
          mempertahankan kecepatan sekarang. Nilai 3,0 berarti pekerjaan harus tiga kali lebih cepat
          dari yang selama ini mampu dikerjakan — biasanya menandakan kebutuhan tambahan regu,
          material, atau anggaran, bukan sekadar imbauan.
        </Catatan>
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
