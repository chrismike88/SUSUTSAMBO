import { getDataset } from "@/lib/data";
import { JudulHalaman, Catatan, Kartu } from "@/components/ui";
import Simulator from "@/components/Simulator";
import { Tabel } from "@/components/Tabel";
import { angka, kwh, persen, rupiah } from "@/lib/format";

export const metadata = { title: "Simulasi Target" };
export const revalidate = 300;

export default async function HalamanSimulasi() {
  const ds = await getDataset();
  const k = ds.kpi;
  const tarif = ds.meta.parameter.tarif_rata_rata ?? 1462.5;

  const proyeksi = ds.neraca_energi.filter((n) => n.status_data === "PROYEKSI");
  const salurSisa = proyeksi.reduce((a, n) => a + n.kwh_salur, 0);
  const desember = ds.neraca_energi.find((n) => n.bulan === 12);

  const bandingan = [
    {
      aspek: "Cara menghitung",
      a: "Seluruh kWh susut setahun dibagi seluruh kWh salur setahun",
      b: "kWh susut bulan Desember dibagi kWh salur bulan Desember",
    },
    {
      aspek: "Beban bulan-bulan awal",
      a: "Ikut terhitung dan tidak bisa dihapus",
      b: "Tidak berpengaruh",
    },
    {
      aspek: "Susut yang harus dicapai Sep–Des",
      a: persen(k.skenario_a_kumulatif.susut_sisa_diizinkan_persen ?? 0),
      b: `${persen(k.target_akhir_tahun_persen)} pada bulan Desember saja`,
    },
    {
      aspek: "Gap kWh yang harus ditutup",
      a: angka(k.skenario_a_kumulatif.gap_kwh_harus_diselamatkan),
      b: angka(k.skenario_b_exit_rate.gap_kwh_harus_diselamatkan),
    },
    {
      aspek: "Nilai finansial gap",
      a: rupiah(k.skenario_a_kumulatif.gap_rupiah),
      b: rupiah(k.skenario_b_exit_rate.gap_rupiah),
    },
    {
      aspek: "Tingkat kesulitan",
      a: k.skenario_a_kumulatif.tingkat_kesulitan,
      b: k.skenario_b_exit_rate.tingkat_kesulitan,
    },
  ];

  return (
    <>
      <JudulHalaman
        judul="Simulasi Pencapaian Target Akhir Tahun"
        keterangan={`Angka target ${persen(k.target_akhir_tahun_persen)} bisa dibaca dengan dua cara, dan konsekuensi kerjanya berbeda jauh. Halaman ini menghitung keduanya sekaligus dan membiarkan asumsinya diubah.`}
      />

      <Simulator
        m={{
          kwhSalurYtd: k.kwh_salur_ytd,
          kwhSusutYtd: k.kwh_susut_ytd,
          salurSisa,
          salurDesember: desember?.kwh_salur ?? 0,
          susutBulanTerakhir: k.susut_bulan_ini_persen,
          targetAwal: k.target_akhir_tahun_persen,
          kwhSelamatSisa: k.kwh_selamat_sisa,
          bulanSisa: k.bulan_tersisa,
          tarif,
        }}
      />

      <div className="mt-4">
        <Kartu
          judul="Perbandingan dua tafsir target"
          keterangan="Sebelum menyusun rencana kerja semester dua, pastikan lebih dulu ke UP3 tafsir mana yang dipakai untuk menilai unit — karena keduanya menuntut kecepatan kerja yang sangat berbeda."
        >
          <Tabel
            kolom={[
              { kunci: "aspek", judul: "Aspek", render: (r) => <strong>{r.aspek}</strong> },
              { kunci: "a", judul: "Skenario A — susut kumulatif (YTD)", render: (r) => r.a },
              { kunci: "b", judul: "Skenario B — susut Desember (exit rate)", render: (r) => r.b },
            ]}
            data={bandingan}
            kunciBaris={(r) => r.aspek}
          />
        </Kartu>
      </div>

      <div className="mt-4 space-y-2">
        <Catatan>
          <strong>Kesimpulan pada asumsi awal.</strong> Gap skenario A sebesar{" "}
          {kwh(k.skenario_a_kumulatif.gap_kwh_harus_diselamatkan)} masih lebih kecil daripada sisa
          potensi work plan {kwh(k.kwh_selamat_sisa)} — rasio{" "}
          {angka(k.kwh_selamat_sisa / k.skenario_a_kumulatif.gap_kwh_harus_diselamatkan, 2)}×.
          Artinya target masih dapat dicapai tanpa program baru, tetapi hanya bila{" "}
          {k.jumlah_kritis} item berstatus KRITIS benar-benar dituntaskan. Geser penggeser
          &ldquo;tingkat eksekusi&rdquo; untuk melihat pada level berapa target mulai lepas.
        </Catatan>
        <Catatan>{ds.meta.catatan}</Catatan>
      </div>
    </>
  );
}
