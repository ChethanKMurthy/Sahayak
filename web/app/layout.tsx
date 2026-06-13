import type { Metadata, Viewport } from "next";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const fraunces = Fraunces({ subsets: ["latin"], variable: "--font-display", display: "swap", weight: ["400", "600", "700"] });

export const metadata: Metadata = {
  title: "Sahayak — your government counter, on your phone",
  description:
    "Capture your documents, speak in your language, and out comes a correctly-filled, submittable government application — with a checklist and the schemes you didn't know you qualified for.",
};

export const viewport: Viewport = { themeColor: "#E8730C", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body className="min-h-dvh antialiased">{children}</body>
    </html>
  );
}
