"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import {
  ShieldCheck,
  Globe,
  Sun,
  Moon,
  LogOut,
  User,
  FileCheck2,
  Layers,
  UploadCloud,
  Scale,
  LayoutDashboard,
  Brain,
  Bot,
  Lock,
} from "lucide-react";

interface NavItemConfig {
  href: string;
  label: string;
  icon: any;
  iconColor: string;
  isSpecial?: boolean;
  roles: string[];
}

const ALL_NAV_ITEMS: NavItemConfig[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
    icon: LayoutDashboard,
    iconColor: "text-sky-500",
    roles: ["AICTE_ADMIN", "REGIONAL_OFFICER", "INSTITUTION_ADMIN", "UNIVERSITY_REGULATOR"],
  },
  {
    href: "/upload",
    label: "Upload",
    icon: UploadCloud,
    iconColor: "text-emerald-500",
    roles: ["AICTE_ADMIN", "INSTITUTION_ADMIN"],
  },
  {
    href: "/cases",
    label: "Cases",
    icon: Scale,
    iconColor: "text-amber-500",
    roles: ["AICTE_ADMIN", "REGIONAL_OFFICER", "INSTITUTION_ADMIN", "UNIVERSITY_REGULATOR"],
  },
  {
    href: "/verify",
    label: "Verify & QR",
    icon: FileCheck2,
    iconColor: "text-cyan-500",
    roles: ["AICTE_ADMIN", "REGIONAL_OFFICER", "UNIVERSITY_REGULATOR", "EMPLOYER_VERIFIER", "STUDENT"],
  },
  {
    href: "/consent",
    label: "Consent Wallet",
    icon: ShieldCheck,
    iconColor: "text-indigo-500",
    roles: ["AICTE_ADMIN", "STUDENT"],
  },
  {
    href: "/audit",
    label: "Audit Chain",
    icon: Layers,
    iconColor: "text-amber-500",
    roles: ["AICTE_ADMIN", "REGIONAL_OFFICER"],
  },
  {
    href: "/intelligence",
    label: "AI ML Suite",
    icon: Brain,
    iconColor: "text-purple-500",
    roles: ["AICTE_ADMIN"],
  },
  {
    href: "/sentinel",
    label: "AI Sentinel",
    icon: Bot,
    iconColor: "text-pink-500",
    isSpecial: true,
    roles: ["AICTE_ADMIN", "REGIONAL_OFFICER"],
  },
];

export function Navbar() {
  const pathname = usePathname();
  const { language, toggleLanguage, t } = useLanguage();
  const { user, isAuthenticated, logout } = useAuth();
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const isDarkMode =
        document.documentElement.classList.contains("dark") ||
        window.matchMedia("(prefers-color-scheme: dark)").matches;
      setIsDark(isDarkMode);
      if (isDarkMode) {
        document.documentElement.classList.add("dark");
      }
    }
  }, []);

  const toggleTheme = () => {
    if (isDark) {
      document.documentElement.classList.remove("dark");
      setIsDark(false);
    } else {
      document.documentElement.classList.add("dark");
      setIsDark(true);
    }
  };

  const getRoleBadgeColor = (role?: string) => {
    switch (role) {
      case "AICTE_ADMIN":
        return "bg-amber-500/10 text-amber-500 border-amber-500/30";
      case "REGIONAL_OFFICER":
        return "bg-blue-500/10 text-blue-500 border-blue-500/30";
      case "INSTITUTION_ADMIN":
        return "bg-emerald-500/10 text-emerald-500 border-emerald-500/30";
      case "UNIVERSITY_REGULATOR":
        return "bg-purple-500/10 text-purple-500 border-purple-500/30";
      case "EMPLOYER_VERIFIER":
        return "bg-cyan-500/10 text-cyan-500 border-cyan-500/30";
      case "STUDENT":
        return "bg-indigo-500/10 text-indigo-500 border-indigo-500/30";
      default:
        return "bg-slate-500/10 text-slate-500 border-slate-500/30";
    }
  };

  // Strictly filter navigation items to only what the authenticated personnel has permission to view
  const visibleNavItems = isAuthenticated && user
    ? ALL_NAV_ITEMS.filter((item) => item.roles.includes(user.role))
    : [];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-16 items-center justify-between px-4 sm:px-8 max-w-7xl mx-auto">
        {/* Brand & Emblem */}
        <Link href="/" className="flex items-center gap-3 group">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 via-white to-emerald-600 shadow-md p-[2px]">
            <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
            </div>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-amber-500 via-sky-400 to-emerald-400 bg-clip-text text-transparent">
                {t.platformName}
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-500 border border-amber-500/20">
                AICTE 26263
              </span>
            </div>
            <span className="text-[11px] text-muted-foreground hidden sm:inline-block truncate max-w-[320px]">
              {t.tagline}
            </span>
          </div>
        </Link>

        {/* Center Nav Links: Strictly filtered by Personnel Role */}
        <nav className="hidden lg:flex items-center gap-1 text-xs font-bold">
          {isAuthenticated && user ? (
            visibleNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;

              if (item.isSpecial) {
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 border border-pink-500/30 ${
                      isActive
                        ? "bg-pink-500/20 text-pink-400 font-extrabold"
                        : "bg-pink-500/10 text-pink-400/90 hover:bg-pink-500/20"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5 text-pink-500 animate-pulse" />
                    <span>{item.label}</span>
                  </Link>
                );
              }

              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                    isActive
                      ? "bg-primary text-primary-foreground font-extrabold"
                      : "hover:bg-muted text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? "text-primary-foreground" : item.iconColor}`} />
                  <span>{item.label}</span>
                </Link>
              );
            })
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground px-3 py-1 rounded-full bg-muted/40 border border-border">
              <Lock className="w-3.5 h-3.5 text-amber-500" />
              <span>Official Login Required to View Modules</span>
            </div>
          )}
        </nav>

        {/* Action Controls & User Info */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Real-time Crypto Status Pill */}
          <Link
            href={isAuthenticated && user?.role === "AICTE_ADMIN" ? "/audit" : "/"}
            className="hidden xl:flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 transition-colors"
            title="SHA-256 Chained Audit Trail & Ed25519"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>Ed25519 & SHA-256 Ledger</span>
          </Link>

          {/* Hindi / English Language Switcher */}
          <button
            onClick={toggleLanguage}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-border hover:bg-muted text-xs font-semibold transition-colors cursor-pointer"
            title="Toggle English / हिंदी"
          >
            <Globe className="w-3.5 h-3.5 text-muted-foreground" />
            <span>{language === "en" ? "हिन्दी" : "English"}</span>
          </button>

          {/* Dark / Light Mode Toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg border border-border hover:bg-muted text-muted-foreground transition-colors cursor-pointer"
            title="Toggle Dark / Light Theme"
          >
            {isDark ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
          </button>

          {/* Authenticated User Status */}
          {isAuthenticated && user ? (
            <div className="flex items-center gap-3 pl-2 border-l border-border">
              <div className="flex flex-col items-end text-right">
                <span className="text-xs font-bold leading-none">{user.full_name}</span>
                <span className={`text-[10px] font-semibold px-1.5 py-0.5 mt-1 rounded border ${getRoleBadgeColor(user.role)}`}>
                  {user.role.replace("_", " ")}
                </span>
              </div>
              <button
                onClick={logout}
                className="p-2 rounded-lg border border-destructive/30 hover:bg-destructive/10 text-destructive transition-colors cursor-pointer"
                title={t.nav.logout}
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              href="/"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground hover:opacity-90 text-xs font-semibold shadow-sm transition-all"
            >
              <User className="w-3.5 h-3.5" />
              <span>{t.nav.login}</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
