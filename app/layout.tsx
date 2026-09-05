import type { Metadata, Viewport } from "next";
import "./globals.css";
import Navigasi from "@/components/Navigasi";
import { getDataset } from "@/lib/data";

export const metadata: Metadata = {
  title: {
    default: "SUSUTSAMBO — Monitoring Susut ULP Samboja",
    template: "%s · SUSUTSAMBO",
  },
  applicationName: "SUSUTSAMBO",
  description:
    "SUSUTSAMBO — dashboard monitoring penurunan susut teknis dan non-teknis ULP Samboja: " +
    "capaian work plan per item, analisis penyulang, P2TL, dan simulasi target akhir tahun.",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0B2E4F" },
    { media: "(prefers-color-scheme: dark)", color: "#0A2135" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const ds = await getDataset();
  return (
    <html lang="id">
      <body className="min-h-screen font-sans antialiased">
        <Navigasi
          unit={ds.meta.unit}
          periode={ds.kpi.periode_data}
          sumber={ds.sumber ?? "contoh"}
        />
        <main className="mx-auto w-full max-w-[1500px] px-4 pb-16 pt-6 sm:px-6 lg:px-8">
          {children}
        </main>
        <footer
          className="border-t px-4 py-6 text-center text-xs sm:px-6 lg:px-8"
          style={{ borderColor: "var(--line)", color: "var(--ink-muted)" }}
        >
          {ds.meta.unit.nama} · {ds.meta.unit.up3} · {ds.meta.unit.uid} — data periode{" "}
          {ds.kpi.periode_data}
        </footer>
      </body>
    </html>
  );
}
