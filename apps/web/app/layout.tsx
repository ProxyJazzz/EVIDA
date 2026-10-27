import type { Metadata } from "next";
import "./globals.css";
import { Navbar } from "@/components/Navbar";

export const metadata: Metadata = {
  title: "EVIDA — Evidence-Driven AI Software Repair",
  description: "AI proposes. Evidence decides. Production-grade software repair verified in isolated sandboxes.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-gray-100 antialiased min-h-screen flex flex-col">
        <Navbar />
        <main className="flex-1 flex flex-col">{children}</main>
        <footer className="border-t border-surface-border py-6 text-center text-xs text-gray-500">
          <p>© 2026 EVIDA. Powered by Nebius Token Factory & NVIDIA Open Models.</p>
        </footer>
      </body>
    </html>
  );
}
