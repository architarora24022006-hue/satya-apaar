import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LanguageProvider } from "@/hooks/useLanguage";
import { AuthProvider } from "@/hooks/useAuth";
import { Navbar } from "@/components/layout/Navbar";
import { AuthGate } from "@/components/auth/AuthGate";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SATYA-APAAR | AICTE Student Data Management & Verification Platform",
  description:
    "Smart India Hackathon 26263: Complete APAAR ID-based Student Data Management, Autonomous Sentinel AI Verification, and Offline Verifiable Credentials for AICTE-Approved Institutions.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <LanguageProvider>
          <AuthProvider>
            <div className="flex flex-col min-h-screen">
              <Navbar />
              <main className="flex-1">
                <AuthGate>{children}</AuthGate>
              </main>
              <footer className="border-t border-border py-4 px-6 text-center text-xs text-muted-foreground bg-background">
                <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
                  <span>
                    SATYA-APAAR © 2026 AICTE Central Academic Repository • Smart India Hackathon PS 26263
                  </span>
                  <div className="flex items-center gap-4">
                    <span>DPDP Act 2023 Aligned</span>
                    <span>•</span>
                    <span>Ed25519 Signed Credentials</span>
                    <span>•</span>
                    <span>SHA-256 Chained Ledger</span>
                  </div>
                </div>
              </footer>
            </div>
          </AuthProvider>
        </LanguageProvider>
      </body>
    </html>
  );
}
