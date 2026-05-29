import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SOP Operations Dashboard",
  description: "ElevateBox — Founder's Office",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-[#0f1117] text-white antialiased">{children}</body>
    </html>
  );
}
