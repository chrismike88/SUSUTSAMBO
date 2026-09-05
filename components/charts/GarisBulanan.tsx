"use client";

import {
  CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, Legend,
} from "recharts";
import { pakaiFormat, type FormatNama } from "@/lib/format";
import { useWarnaViz, gayaSumbu } from "./viz";
import { KotakTooltip } from "./Tooltip";

export interface SeriGaris {
  kunci: string;
  nama: string;
  slot: 0 | 1 | 2;
  putus?: boolean;
}

export default function GarisBulanan({
  data,
  seri,
  format,
  formatSumbu,
  tinggi = 280,
  domain,
}: {
  data: Record<string, string | number | null>[];
  seri: SeriGaris[];
  format: FormatNama;
  formatSumbu: FormatNama;
  tinggi?: number;
  domain?: [number, number];
}) {
  const w = useWarnaViz();
  const gaya = gayaSumbu(w);
  const formatNilai = pakaiFormat(format);
  const fSumbu = pakaiFormat(formatSumbu);
  return (
    <div className="gulir-x">
      <div style={{ minWidth: 460, height: tinggi }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: -6 }}>
          <CartesianGrid stroke={w.kisi} vertical={false} />
          <XAxis dataKey="bulan" {...gaya} />
          <YAxis domain={domain ?? ["auto", "auto"]} tickFormatter={fSumbu} width={58} {...gaya} />
          <Tooltip
            cursor={{ stroke: w.sumbu, strokeWidth: 1 }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              return (
                <KotakTooltip
                  judul={String(label)}
                  baris={payload
                    .filter((p) => p.value != null)
                    .map((p) => {
                      const s = seri.find((x) => x.kunci === p.dataKey);
                      return {
                        warna: w.seri[s?.slot ?? 0],
                        label: s?.nama ?? String(p.dataKey),
                        nilai: formatNilai(Number(p.value)),
                      };
                    })}
                />
              );
            }}
          />
          {seri.length > 1 && (
            <Legend
              verticalAlign="bottom"
              height={28}
              iconType="plainline"
              wrapperStyle={{ fontSize: 12, color: w.tinta2 }}
            />
          )}
          {seri.map((s) => (
            <Line
              key={s.kunci}
              name={s.nama}
              type="monotone"
              dataKey={s.kunci}
              stroke={w.seri[s.slot]}
              strokeWidth={2}
              strokeDasharray={s.putus ? "5 4" : undefined}
              dot={{ r: 3, strokeWidth: 0, fill: w.seri[s.slot] }}
              activeDot={{ r: 6, strokeWidth: 2, stroke: w.permukaan }}
              connectNulls={false}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
