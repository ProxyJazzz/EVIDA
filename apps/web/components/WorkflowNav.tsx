"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

interface WorkflowNavProps {
  activeScreen?: string;
  investigationId?: string;
}

export function WorkflowNav({
  activeScreen = "dashboard",
  investigationId = "33333333-3333-3333-3333-333333333333",
}: WorkflowNavProps) {
  const pathname = usePathname();
  const isDashboard = pathname === "/dashboard" || pathname === "/";
  const isInvestigation = pathname?.includes("/investigations");

  const navItems = [
    { id: "dashboard", label: "1. Dashboard & Ledger", href: "/dashboard" },
    {
      id: "repository",
      label: "2. Repository Intake",
      href: `/investigations/${investigationId}#repository`,
    },
    {
      id: "reproduction",
      label: "3. Repro Execution",
      href: `/investigations/${investigationId}#reproduction`,
    },
    {
      id: "hypothesis",
      label: "4. AI Hypothesis",
      href: `/investigations/${investigationId}#hypothesis`,
    },
    {
      id: "regression",
      label: "5. Regression Proof",
      href: `/investigations/${investigationId}#regression`,
    },
    {
      id: "patch",
      label: "6. Patch & Validation",
      href: `/investigations/${investigationId}#patch`,
    },
    {
      id: "verification",
      label: "7. Double Verification",
      href: `/investigations/${investigationId}#verification`,
    },
    {
      id: "evidence",
      label: "8. Evidence Bundle & Audit",
      href: `/investigations/${investigationId}#evidence`,
    },
  ];

  return (
    <nav
      className="bg-surface/95 border-b border-surface-border sticky top-0 z-40 shadow-sm backdrop-blur-md"
      aria-label="Workflow Navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center space-x-1 sm:space-x-2 overflow-x-auto py-2 no-scrollbar font-mono text-xs">
          {navItems.map((item) => {
            const isActive =
              (item.id === "dashboard" && isDashboard) ||
              (item.id !== "dashboard" && isInvestigation && activeScreen === item.id);

            return (
              <Link
                key={item.id}
                href={item.href}
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded text-xs font-semibold whitespace-nowrap transition-colors ${
                  isActive
                    ? "bg-blue-600 text-white shadow-xs"
                    : "text-slate-300 hover:text-white hover:bg-surface-card"
                }`}
              >
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
