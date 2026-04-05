import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { ClerkProvider } from "@clerk/nextjs";
import { dark } from "@clerk/themes";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Startup Idea Finder V7 — AI Pazar İstihbarat Motoru",
  description: "Yapay zeka destekli pazar araştırması ile kârlı Micro-SaaS fırsatlarını keşfedin. 6+ veri kaynağı, 5 analiz modu, çoklu AI ajanları.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        baseTheme: dark,
        elements: {
          card: "bg-card border border-white/10",
          formButtonPrimary: "bg-primary hover:bg-primary/80",
        },
      }}
    >
      <html lang="en" className="dark">
        <body
          className={`${inter.variable} font-sans antialiased`}
        >
          {children}
        </body>
      </html>
    </ClerkProvider>
  );
}
