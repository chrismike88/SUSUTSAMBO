import { persen } from "@/lib/format";

/**
 * Bagian-dari-keseluruhan dengan dua segmen. Sengaja dirender sebagai batang
 * bertumpuk (bukan diagram lingkaran dua irisan) dan setiap segmen diberi
 * label langsung, sehingga terbaca tanpa mengandalkan warna.
 */
export default function KomposisiSusut({
  teknis,
  nonTeknis,
}: {
  teknis: number;
  nonTeknis: number;
}) {
  const total = teknis + nonTeknis;
  const bagian = [
    { nama: "Susut teknis", nilai: teknis, warna: "var(--viz-1)" },
    { nama: "Susut non-teknis", nilai: nonTeknis, warna: "var(--viz-2)" },
  ];

  return (
    <div>
      <div className="flex h-11 w-full gap-[2px] overflow-hidden rounded-lg">
        {bagian.map((b) => (
          <div
            key={b.nama}
            className="grid place-items-center text-xs font-bold text-white"
            style={{ background: b.warna, width: `${(b.nilai / total) * 100}%` }}
            title={`${b.nama}: ${persen(b.nilai)} dari total susut ${persen(total)}`}
          >
            {persen(b.nilai)}
          </div>
        ))}
      </div>
      <ul className="mt-3 space-y-2">
        {bagian.map((b) => (
          <li key={b.nama} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2" style={{ color: "var(--ink-2)" }}>
              <span
                className="inline-block h-2.5 w-2.5 rounded-sm"
                style={{ background: b.warna }}
                aria-hidden
              />
              {b.nama}
            </span>
            <span className="tabular-nums font-semibold">
              {persen(b.nilai)}
              <span className="ml-1.5 text-xs font-normal" style={{ color: "var(--ink-muted)" }}>
                ({persen((b.nilai / total) * 100, 1)} dari susut)
              </span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
