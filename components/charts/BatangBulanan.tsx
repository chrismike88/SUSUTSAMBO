"use client";

import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { pakaiFormat, type FormatNama } from "@/lib/format";
import { useWarnaViz, gayaSumbu } from "./viz";
import { KotakTooltip } from "./Tooltip";

/** Satu seri per bulan — satu warna, sumbu Y menanggung nilainya. */
export default function BatangBulanan({
  data,
  nama,
  format,
  formatSumbu,
  slot = 0,
  tinggi = 260,
}: {
  data: { bulan: string; nilai: number }[];
  nama: string;
  format: FormatNama;
  formatSumbu: FormatNama;
  slot?: 0 | 1 | 2;
  tinggi?: number;
}) {
  const w = useWarnaViz();
  const gaya = gayaSumbu(w);
  const formatNilai = pakaiFormat(format);
  const fSumbu = pakaiFormat(formatSumbu);
  return (
    <div className="gulir-x">
      <div style={{ minWidth: 460, height: tinggi }}>
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -6 }} barCategoryGap="26%">
          <CartesianGrid stroke={w.kisi} vertical={false} />
          <XAxis dataKey="bulan" {...gaya} />
          <YAxis tickFormatter={fSumbu} width={58} {...gaya} />
          <Tooltip
            cursor={{ fill: w.kisi, fillOpacity: 0.45 }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              return (
                <KotakTooltip
                  judul={String(label)}
                  baris={[{ warna: w.seri[slot], label: nama, nilai: formatNilai(Number(payload[0].value)) }]}
                />
              );
            }}
          />
          <Bar dataKey="nilai" fill={w.seri[slot]} radius={[4, 4, 0, 0]} isAnimationActive={false} />
        </BarChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
