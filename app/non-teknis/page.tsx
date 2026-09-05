import { getDataset } from "@/lib/data";
import { Kartu, Petak, JudulHalaman, Catatan, LencanaStatus } from "@/components/ui";
import { Tabel, TabelPendamping } from "@/components/Tabel";
import BatangBulanan from "@/components/charts/BatangBulanan";
import GarisBulanan from "@/components/charts/GarisBulanan";
import { angka, kwh, persen, rupiah } from "@/lib/format";

export const metadata = { title: "Analisis Susut Non-Teknis" };
export const revalidate = 300;

export default async function HalamanNonTeknis() {
  const ds = await getDataset();
  const k = ds.kpi;
  const tarif = ds.meta.parameter.tarif_rata_rata ?? 1462.5;

  // Rekap P2TL per bulan
  const perBulan = new Map<number, {
    bulan: string; periksa: number; temuan: number;
    kwhTemuan: number; tagsus: number; bayar: number;
  }>();
  for (const r of ds.p2tl) {
    const b = perBulan.get(r.bulan) ?? {
      bulan: r.bulan_nama, periksa: 0, temuan: 0, kwhTemuan: 0, tagsus: 0, bayar: 0,
    };
    b.periksa += r.jumlah_pemeriksaan;
    b.temuan += r.jumlah_temuan;
    b.kwhTemuan += r.kwh_temuan;
    b.tagsus += r.rupiah_tagsus;
    b.bayar += r.rupiah_terbayar;
    perBulan.set(r.bulan, b);
  }
  const bulanan = [...perBulan.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([, v]) => ({
      ...v,
      hitRate: v.periksa ? (v.temuan / v.periksa) * 100 : 0,
      efektivitas: v.tagsus ? (v.bayar / v.tagsus) * 100 : 0,
    }));

  const total = bulanan.reduce(
    (a, b) => ({
      periksa: a.periksa + b.periksa, temuan: a.temuan + b.temuan,
      kwhTemuan: a.kwhTemuan + b.kwhTemuan, tagsus: a.tagsus + b.tagsus, bayar: a.bayar + b.bayar,
    }),
    { periksa: 0, temuan: 0, kwhTemuan: 0, tagsus: 0, bayar: 0 },
  );

  // Rekap per golongan pelanggaran
  const perGolongan = new Map<string, {
    golongan: string; keterangan: string; temuan: number; kwh: number; tagsus: number;
  }>();
  for (const r of ds.p2tl) {
    const g = perGolongan.get(r.golongan) ?? {
      golongan: r.golongan, keterangan: r.keterangan, temuan: 0, kwh: 0, tagsus: 0,
    };
    g.temuan += r.jumlah_temuan;
    g.kwh += r.kwh_temuan;
    g.tagsus += r.rupiah_tagsus;
    perGolongan.set(r.golongan, g);
  }
  const golongan = [...perGolongan.values()].sort((a, b) => b.kwh - a.kwh);
  const totalKwhGol = golongan.reduce((a, g) => a + g.kwh, 0);

  const programNonTeknis = ds.program.filter((p) => p.kategori === "NON_TEKNIS");
  const efektivitasTotal = total.tagsus ? (total.bayar / total.tagsus) * 100 : 0;

  return (
    <>
      <JudulHalaman
        judul="Analisis Susut Non-Teknis"
        keterangan="Susut non-teknis adalah energi yang benar-benar tersalur tetapi tidak menjadi rekening: pelanggaran pemakaian, meter rusak atau lambat, kesalahan baca, PJU tanpa meter, dan kesalahan administrasi. Berbeda dari susut teknis, bagian ini bisa ditekan mendekati nol."
      />

      <div className="mb-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Petak
          label="Susut non-teknis bulan berjalan"
          nilai={persen(k.susut_nonteknis_persen)}
          nada="peringatan"
          catatan={`${persen((k.susut_nonteknis_persen / (k.susut_teknis_persen + k.susut_nonteknis_persen)) * 100, 1)} dari total susut — seluruhnya berpotensi dipulihkan`}
        />
        <Petak
          label="kWh temuan P2TL"
          nilai={kwh(total.kwhTemuan, false)}
          satuan="kWh"
          nada="sorot"
          catatan={`${angka(total.temuan)} temuan dari ${angka(total.periksa)} pemeriksaan (hit rate ${persen((total.temuan / total.periksa) * 100, 1)})`}
        />
        <Petak
          label="Tagihan susulan terbit"
          nilai={rupiah(total.tagsus)}
          catatan={`Terbayar ${rupiah(total.bayar)}`}
        />
        <Petak
          label="Efektivitas penagihan"
          nilai={persen(efektivitasTotal, 1)}
          nada={efektivitasTotal >= 85 ? "baik" : "buruk"}
          catatan={`${rupiah(total.tagsus - total.bayar)} belum tertagih — temuan yang belum berubah menjadi pendapatan`}
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Kartu
          judul="Perolehan kWh temuan P2TL per bulan"
          keterangan="Energi yang berhasil ditarik kembali lewat penertiban pemakaian tenaga listrik."
        >
          <BatangBulanan
            data={bulanan.map((b) => ({ bulan: b.bulan, nilai: b.kwhTemuan }))}
            nama="kWh temuan"
            format="kwhAngka"
            formatSumbu="ribu"
          />
          <TabelPendamping>
            <Tabel
              kolom={[
                { kunci: "b", judul: "Bulan", render: (b) => b.bulan },
                { kunci: "p", judul: "Pemeriksaan", num: true, render: (b) => angka(b.periksa) },
                { kunci: "t", judul: "Temuan", num: true, render: (b) => angka(b.temuan) },
                { kunci: "h", judul: "Hit rate", num: true, render: (b) => persen(b.hitRate, 1) },
                { kunci: "k", judul: "kWh temuan", num: true, render: (b) => angka(b.kwhTemuan) },
              ]}
              data={bulanan}
              kunciBaris={(b) => b.bulan}
            />
          </TabelPendamping>
        </Kartu>

        <Kartu
          judul="Efektivitas penagihan tagihan susulan"
          keterangan="Temuan P2TL baru benar-benar menurunkan susut setelah tagihannya tertagih. Grafik ini sengaja dipisah dari grafik kWh agar kedua besaran tidak dibaca pada satu skala."
        >
          <GarisBulanan
            data={bulanan.map((b) => ({ bulan: b.bulan, efektivitas: Math.round(b.efektivitas * 10) / 10 }))}
            seri={[{ kunci: "efektivitas", nama: "Efektivitas tagih", slot: 1 }]}
            format="persen1"
            formatSumbu="persen1"
            domain={[0, 100]}
            tinggi={260}
          />
          <TabelPendamping>
            <Tabel
              kolom={[
                { kunci: "b", judul: "Bulan", render: (b) => b.bulan },
                { kunci: "tg", judul: "Tagihan terbit", num: true, render: (b) => rupiah(b.tagsus) },
                { kunci: "by", judul: "Terbayar", num: true, render: (b) => rupiah(b.bayar) },
                { kunci: "e", judul: "Efektivitas", num: true, render: (b) => persen(b.efektivitas, 1) },
              ]}
              data={bulanan}
              kunciBaris={(b) => b.bulan}
            />
          </TabelPendamping>
        </Kartu>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Kartu
          judul="Temuan menurut golongan pelanggaran"
          keterangan="Golongan menentukan rumus tagihan susulan dan cara penindakannya."
        >
          <Tabel
            kolom={[
              { kunci: "g", judul: "Golongan", render: (g) => <strong>{g.golongan}</strong> },
              { kunci: "k", judul: "Uraian", render: (g) => (
                  <span style={{ color: "var(--ink-2)" }}>{g.keterangan}</span>) },
              { kunci: "t", judul: "Temuan", num: true, render: (g) => angka(g.temuan) },
              { kunci: "kw", judul: "kWh temuan", num: true, render: (g) => angka(g.kwh) },
              { kunci: "p", judul: "Porsi kWh", num: true,
                render: (g) => persen((g.kwh / totalKwhGol) * 100, 1) },
              { kunci: "rp", judul: "Tagihan susulan", num: true, render: (g) => rupiah(g.tagsus) },
            ]}
            data={golongan}
            kunciBaris={(g) => g.golongan}
          />
          <div className="mt-3">
            <Catatan>
              P-I mempengaruhi batas daya · P-II mempengaruhi pengukuran energi · P-III mempengaruhi
              keduanya · P-IV bukan pelanggan (sambungan langsung). Golongan P-IV tidak menghasilkan
              rekening susulan yang bisa ditagih ke pelanggan terdaftar, sehingga penanganannya adalah
              penormalan sambungan atau proses hukum.
            </Catatan>
          </div>
        </Kartu>

        <Kartu
          judul="Capaian program non-teknis"
          keterangan="Dua belas item work plan yang menyerang penyebab susut non-teknis."
        >
          <Tabel
            kolom={[
              { kunci: "kode", judul: "Kode", render: (p) => <strong>{p.kode}</strong> },
              { kunci: "nama", judul: "Program", render: (p) => p.nama },
              { kunci: "tgt", judul: "Target tahun", num: true,
                render: (p) => `${angka(p.target_tahun, 0)} ${p.satuan}` },
              { kunci: "cap", judul: "Capaian", num: true, render: (p) => persen(p.capaian_ytd_persen, 1) },
              { kunci: "fk", judul: "Faktor kejar", num: true,
                render: (p) => (p.faktor_kejar ? `${angka(p.faktor_kejar, 2)}×` : "–") },
              { kunci: "st", judul: "Status", render: (p) => <LencanaStatus status={p.status} /> },
            ]}
            data={[...programNonTeknis].sort((a, b) => a.capaian_ytd_persen - b.capaian_ytd_persen)}
            kunciBaris={(p) => p.kode}
          />
        </Kartu>
      </div>

      <div className="mt-4 space-y-2">
        <Catatan>
          <strong>Prioritas pada susut non-teknis.</strong> Sisa potensi kWh program non-teknis{" "}
          {kwh(k.kontribusi_nonteknis.kwh_sisa)} — setara{" "}
          {rupiah(k.kontribusi_nonteknis.kwh_sisa * tarif)} — jauh lebih besar daripada program teknis{" "}
          {kwh(k.kontribusi_teknis.kwh_sisa)}. Program non-teknis juga umumnya lebih cepat berbuah
          karena tidak menunggu pengadaan material jaringan. Bila waktu dan sumber daya terbatas,
          bagian inilah yang lebih dulu dikejar.
        </Catatan>
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
