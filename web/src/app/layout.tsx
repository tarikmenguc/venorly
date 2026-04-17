import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/context/AuthContext";
import { ErrorBoundary } from "@/components/ErrorBoundary";
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
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-sans antialiased`}>
        <AuthProvider>
          <ErrorBoundary>
            {children}
          </ErrorBoundary>
        </AuthProvider>
      </body>
    </html>
  );
}
