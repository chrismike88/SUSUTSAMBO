"use client";

import {
  CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer,
  Tooltip, XAxis, YAxis, Legend,
} from "recharts";
import type { Neraca } from "@/lib/types";
import { angka, persen } from "@/lib/format";
import { useWarnaViz, gayaSumbu } from "./viz";
import { KotakTooltip } from "./Tooltip";

export default function TrenSusut({
  neraca,
  targetAkhirTahun,
}: {
  neraca: Neraca[];
  targetAkhirTahun: number;
}) {
  const w = useWarnaViz();
  const gaya = gayaSumbu(w);

  const data = neraca.map((n) => ({
    bulan: n.bulan_nama,
    realisasi: n.status_data === "REALISASI" ? n.susut_persen : null,
    ytd: n.susut_ytd_persen,
    target: n.target_persen,
    status: n.status_data,
  }));

  const nilai = data.flatMap((d) => [d.realisasi, d.ytd, d.target]).filter((v): v is number => v != null);
  const min = Math.floor((Math.min(...nilai, targetAkhirTahun) - 0.4) * 2) / 2;
  const maks = Math.ceil((Math.max(...nilai) + 0.3) * 2) / 2;

  return (
    <div className="gulir-x">
      <div style={{ minWidth: 520, height: 320 }}>
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 4, left: -8 }}>
          <CartesianGrid stroke={w.kisi} vertical={false} />
          <XAxis dataKey="bulan" {...gaya} />
          <YAxis
            domain={[min, maks]}
            tickFormatter={(v: number) => `${angka(v, 1)}%`}
            width={52}
            {...gaya}
          />
          <ReferenceLine
            y={targetAkhirTahun}
            stroke={w.seri[2]}
            strokeWidth={1.5}
            strokeDasharray="6 4"
            label={{
              value: `Target akhir tahun ${persen(targetAkhirTahun)}`,
              position: "insideBottomLeft",
              fill: w.seri[2],
              fontSize: 11,
              fontWeight: 600,
            }}
          />
          <Tooltip
            cursor={{ stroke: w.sumbu, strokeWidth: 1 }}
            content={({ active, payload, label }) => {
              if (!active || !payload?.length) return null;
              const d = payload[0].payload as (typeof data)[number];
              return (
                <KotakTooltip
                  judul={`${label} — ${d.status === "REALISASI" ? "realisasi" : "proyeksi"}`}
                  baris={[
                    ...(d.realisasi != null
                      ? [{ warna: w.seri[0], label: "Susut bulanan", nilai: persen(d.realisasi) }]
                      : []),
                    ...(d.ytd != null
                      ? [{ warna: w.seri[1], label: "Susut kumulatif", nilai: persen(d.ytd) }]
                      : []),
                    { warna: w.redup, label: "Target bulan ini", nilai: persen(d.target) },
                  ]}
                />
              );
            }}
          />
          <Legend
            verticalAlign="bottom"
            height={30}
            wrapperStyle={{ fontSize: 12, color: w.tinta2 }}
            iconType="plainline"
          />
          <Line
            name="Target bulanan"
            type="monotone"
            dataKey="target"
            stroke={w.redup}
            strokeWidth={1.5}
            strokeDasharray="5 4"
            dot={false}
            activeDot={false}
          />
          <Line
            name="Susut kumulatif (YTD)"
            type="monotone"
            dataKey="ytd"
            stroke={w.seri[1]}
            strokeWidth={2}
            dot={false}
            connectNulls={false}
            activeDot={{ r: 5, strokeWidth: 2, stroke: w.permukaan }}
          />
          <Line
            name="Susut bulanan (realisasi)"
            type="monotone"
            dataKey="realisasi"
            stroke={w.seri[0]}
            strokeWidth={2}
            dot={{ r: 3.5, strokeWidth: 0, fill: w.seri[0] }}
            connectNulls={false}
            activeDot={{ r: 6, strokeWidth: 2, stroke: w.permukaan }}
          />
        </LineChart>
      </ResponsiveContainer>
      </div>
    </div>
  );
}
