import { getDataset } from "@/lib/data";
import { Kartu, Petak, JudulHalaman, Catatan, LencanaStatus, LencanaPenyulang } from "@/components/ui";
import { Tabel, TabelPendamping, type Kolom } from "@/components/Tabel";
import BatangPeringkat from "@/components/charts/BatangPeringkat";
import { angka, kwh, persen, rupiah } from "@/lib/format";
import type { Penyulang } from "@/lib/types";

export const metadata = { title: "Analisis Susut Teknis" };
export const revalidate = 300;

const NAMA_KOMPONEN: Record<string, { nama: string; program: string }> = {
  trafo_distribusi: { nama: "Trafo distribusi (rugi inti + belitan)", program: "T-01, T-03, T-09" },
  jaringan_tegangan_rendah: { nama: "Jaringan Tegangan Rendah (JTR)", program: "T-02, T-03" },
  sambungan_rumah_app: { nama: "Sambungan Rumah & APP", program: "T-04" },
  jaringan_tegangan_menengah: { nama: "Jaringan Tegangan Menengah (JTM)", program: "T-05, T-06, T-10" },
  konektor_sambungan: { nama: "Konektor & titik sambung", program: "T-07" },
};

const AMBANG = [
  ["Ketidakseimbangan arus antar fasa", "≤ 10%", "Di atas 15% wajib penyeimbangan beban dalam 7 hari"],
  ["Faktor daya (cos φ)", "≥ 0,90", "Di bawah 0,90 pasang kapasitor bank pada penyulang terkait"],
  ["Drop tegangan ujung jaringan", "≤ 5%", "Di atas 5% lakukan uprating konduktor atau pasang trafo sisip"],
  ["Panjang sambungan rumah (SR)", "≤ 30 m", "Di atas 30 m rugi SR signifikan — jadwalkan penggantian"],
  ["Pembebanan trafo distribusi", "≤ 80%", "Di atas 80% lakukan uprating trafo atau pasang trafo sisip"],
  ["Panjang JTR per gardu", "≤ 350 m", "Di atas 350 m pasang trafo sisip untuk memperpendek JTR"],
];

export default async function HalamanTeknis() {
  const ds = await getDataset();
  const k = ds.kpi;

  const agregat = new Map<string, number>();
  for (const r of ds.rugi_teknis) {
    agregat.set(r.komponen, (agregat.get(r.komponen) ?? 0) + r.kwh_rugi);
  }
  const totalRugi = [...agregat.values()].reduce((a, b) => a + b, 0);
  const komponen = [...agregat.entries()]
    .map(([kunci, nilai]) => ({
      kunci,
      label: NAMA_KOMPONEN[kunci]?.nama ?? kunci,
      nilai,
      porsi: (nilai / totalRugi) * 100,
      program: NAMA_KOMPONEN[kunci]?.program ?? "–",
    }))
    .sort((a, b) => b.nilai - a.nilai);

  const penyulang = [...ds.penyulang].sort((a, b) => b.indeks_prioritas - a.indeks_prioritas);
  const susutMin = Math.min(...penyulang.map((p) => p.susut_persen));
  const susutMaks = Math.max(...penyulang.map((p) => p.susut_persen));

  /** Peta panas: satu warna, terang→gelap. Warna teks mengikuti langkah ramp. */
  function petak(nilai: number) {
    const t = (nilai - susutMin) / (susutMaks - susutMin || 1);
    const i = Math.min(5, Math.max(0, Math.round(t * 5)));
    return {
      background: `var(--seq-${i + 1})`,
      color: i >= 3 ? "#FFFFFF" : "#0B1F33",
      indeks: i,
    };
  }

  const programTeknis = ds.program.filter((p) => p.kategori === "TEKNIS");

  const kolomPenyulang: Kolom<Penyulang>[] = [
    { kunci: "kode", judul: "Penyulang", render: (p) => (
        <span><strong>{p.kode}</strong> <span style={{ color: "var(--ink-2)" }}>{p.nama}</span></span>) },
    { kunci: "susut", judul: "Susut", num: true, render: (p) => {
        const g = petak(p.susut_persen);
        return (
          <span
            className="inline-block rounded px-1.5 py-0.5 font-semibold tabular-nums"
            style={{ background: g.background, color: g.color }}
          >
            {persen(p.susut_persen)}
          </span>
        );
      } },
    { kunci: "kwh", judul: "kWh susut/bln", num: true, render: (p) => angka(p.kwh_susut_bulan) },
    { kunci: "rp", judul: "Nilai/bln", num: true, render: (p) => rupiah(p.rupiah_susut_bulan) },
    { kunci: "unb", judul: "Unbalance", num: true, render: (p) => (
        <span style={{ color: p.unbalance_persen > 15 ? "var(--st-critical)" : undefined,
                       fontWeight: p.unbalance_persen > 15 ? 700 : undefined }}>
          {persen(p.unbalance_persen, 1)}
        </span>) },
    { kunci: "cos", judul: "Cos φ", num: true, render: (p) => (
        <span style={{ color: p.cos_phi < 0.9 ? "var(--st-critical)" : undefined,
                       fontWeight: p.cos_phi < 0.9 ? 700 : undefined }}>
          {angka(p.cos_phi, 2)}
        </span>) },
    { kunci: "drop", judul: "Drop tegangan", num: true, render: (p) => (
        <span style={{ color: p.drop_tegangan_persen > 5 ? "var(--st-critical)" : undefined,
                       fontWeight: p.drop_tegangan_persen > 5 ? 700 : undefined }}>
          {persen(p.drop_tegangan_persen, 1)}
        </span>) },
    { kunci: "sr", judul: "SR > 30 m", num: true, render: (p) => angka(p.sr_lebih_30m) },
    { kunci: "jtr", judul: "JTR (kms)", num: true, render: (p) => angka(p.panjang_jtr_kms, 1) },
    { kunci: "gardu", judul: "Gardu", num: true, render: (p) => angka(p.jumlah_gardu) },
    { kunci: "idx", judul: "Indeks", num: true, render: (p) => angka(p.indeks_prioritas, 1) },
    { kunci: "kelas", judul: "Prioritas", render: (p) => <LencanaPenyulang kelas={p.kelas_prioritas} /> },
  ];

  return (
    <>
      <JudulHalaman
        judul="Analisis Susut Teknis"
        keterangan="Susut teknis adalah rugi alamiah pada trafo, jaringan, sambungan rumah, dan konektor. Ia tidak pernah bisa nol — yang bisa dilakukan adalah menekannya mendekati batas wajar jaringan eksisting."
      />

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Petak label="Susut teknis bulan berjalan" nilai={persen(k.susut_teknis_persen)} nada="sorot"
          catatan={`${persen((k.susut_teknis_persen / (k.susut_teknis_persen + k.susut_nonteknis_persen)) * 100, 1)} dari total susut`} />
        <Petak label="Batas bawah wajar" nilai={persen(ds.meta.parameter.floor_susut_teknis ?? 3.3)}
          catatan="Perkiraan susut teknis minimum yang realistis untuk konfigurasi jaringan saat ini" />
        <Petak label="Ruang perbaikan tersisa"
          nilai={angka(k.susut_teknis_persen - (ds.meta.parameter.floor_susut_teknis ?? 3.3), 2)}
          satuan="pp" nada="peringatan"
          catatan="Selisih antara kondisi sekarang dan batas bawah wajar — inilah yang bisa dikejar program teknis" />
        <Petak label="Rugi teknis terukur" nilai={kwh(totalRugi, false)} satuan="kWh/bln" nada="buruk"
          catatan={`Setara ${rupiah(totalRugi * (ds.meta.parameter.tarif_rata_rata ?? 1462.5))} per bulan`} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Kartu
          judul="Di mana energi hilang secara teknis"
          keterangan="Dekomposisi rugi teknis per komponen jaringan pada bulan berjalan."
        >
          <BatangPeringkat
            data={komponen.map((c) => ({
              label: c.label.length > 34 ? c.label.slice(0, 33) + "…" : c.label,
              nilai: c.nilai,
              keterangan: `${persen(c.porsi, 1)} dari rugi teknis · ditangani program ${c.program}`,
            }))}
            format="angka"
            lebarLabel={210}
            tinggiBaris={38}
          />
          <TabelPendamping>
            <Tabel
              kolom={[
                { kunci: "n", judul: "Komponen", render: (c) => c.label },
                { kunci: "k", judul: "kWh rugi/bulan", num: true, render: (c) => angka(c.nilai) },
                { kunci: "p", judul: "Porsi", num: true, render: (c) => persen(c.porsi, 1) },
                { kunci: "pr", judul: "Program penanganan", render: (c) => c.program },
              ]}
              data={komponen}
              kunciBaris={(c) => c.kunci}
            />
          </TabelPendamping>
        </Kartu>

        <Kartu
          judul="Ambang batas acuan operasi"
          keterangan="Angka pembanding saat membaca tabel penyulang di bawah. Nilai yang melewati ambang ditandai merah."
        >
          <Tabel
            kolom={[
              { kunci: "p", judul: "Parameter", render: (a) => a[0] },
              { kunci: "a", judul: "Ambang", render: (a) => (
                  <span className="font-semibold tabular-nums">{a[1]}</span>) },
              { kunci: "t", judul: "Tindakan bila terlampaui", render: (a) => (
                  <span style={{ color: "var(--ink-2)" }}>{a[2]}</span>) },
            ]}
            data={AMBANG}
            kunciBaris={(a) => a[0]}
          />
        </Kartu>
      </div>

      <div className="mt-4">
        <Kartu
          judul="Profil dan peringkat penyulang"
          keterangan="Indeks prioritas menggabungkan besaran susut (bobot 40), ketidakseimbangan beban (25), faktor daya (20), dan drop tegangan (15). Kolom susut diwarnai dari terang ke gelap mengikuti besarnya."
          aksi={
            <div className="flex items-center gap-2 text-xs" style={{ color: "var(--ink-muted)" }}>
              <span>{persen(susutMin)}</span>
              <span className="flex h-3 overflow-hidden rounded" aria-hidden>
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <span key={i} className="block w-5" style={{ background: `var(--seq-${i})` }} />
                ))}
              </span>
              <span>{persen(susutMaks)}</span>
            </div>
          }
        >
          <Tabel kolom={kolomPenyulang} data={penyulang} kunciBaris={(p) => p.kode} />
        </Kartu>
      </div>

      <div className="mt-4">
        <Kartu
          judul="Capaian program teknis"
          keterangan="Sepuluh item work plan yang menyerang langsung penyebab rugi teknis."
        >
          <Tabel
            kolom={[
              { kunci: "kode", judul: "Kode", render: (p) => <strong>{p.kode}</strong> },
              { kunci: "nama", judul: "Program", render: (p) => p.nama },
              { kunci: "sub", judul: "Sasaran", render: (p) => p.sub_kategori },
              { kunci: "tgt", judul: "Target tahun", num: true, render: (p) => `${angka(p.target_tahun, 1)} ${p.satuan}` },
              { kunci: "real", judul: "Realisasi", num: true, render: (p) => angka(p.realisasi_ytd, 1) },
              { kunci: "cap", judul: "Capaian", num: true, render: (p) => persen(p.capaian_ytd_persen, 1) },
              { kunci: "sisa", judul: "Sisa potensi kWh", num: true,
                render: (p) => angka(Math.round(p.sisa_target * p.kwh_selamat_per_unit)) },
              { kunci: "st", judul: "Status", render: (p) => <LencanaStatus status={p.status} /> },
            ]}
            data={[...programTeknis].sort((a, b) => a.capaian_ytd_persen - b.capaian_ytd_persen)}
            kunciBaris={(p) => p.kode}
          />
        </Kartu>
      </div>

      <div className="mt-4">
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
