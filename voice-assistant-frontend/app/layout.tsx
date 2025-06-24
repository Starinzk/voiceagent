import "@livekit/components-styles";
import type { Metadata } from "next";
import { Inter, Noto_Serif } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const notoSerif = Noto_Serif({
  subsets: ["latin"],
  weight: ["400", "700"],
  variable: "--font-georgia",
});

export const metadata: Metadata = {
  title: "Enso Design Assistant",
  description: "A voice-enabled AI design assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} ${notoSerif.variable} font-sans bg-gradient-to-br from-charcoal-start to-charcoal-end text-white`}
      >
        {children}
      </body>
    </html>
  );
}
