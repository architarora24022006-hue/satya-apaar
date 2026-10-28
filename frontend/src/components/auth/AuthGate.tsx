"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import {
  ShieldAlert,
  Lock,
  Unlock,
  KeyRound,
  Mail,
  ShieldCheck,
  Building2,
  Users,
  Scale,
  RefreshCw,
  AlertTriangle,
  ArrowRight,
  LogOut,
  CheckCircle2,
} from "lucide-react";

// Strict Role-Based Route Authorization Matrix
const ROLE_PERMISSIONS: Record<string, string[]> = {
  AICTE_ADMIN: [
    "/dashboard",
    "/upload",
    "/cases",
    "/verify",
    "/consent",
    "/audit",
    "/intelligence",
    "/sentinel",
  ],
  REGIONAL_OFFICER: [
    "/dashboard",
    "/cases",
    "/verify",
    "/audit",
    "/sentinel",
  ],
  INSTITUTION_ADMIN: [
    "/dashboard",
    "/upload",
    "/cases",
  ],
  UNIVERSITY_REGULATOR: [
    "/dashboard",
    "/cases",
    "/verify",
  ],
  EMPLOYER_VERIFIER: [
    "/verify",
  ],
  STUDENT: [
    "/consent",
    "/verify",
  ],
};

const MODULE_NAMES: Record<string, string> = {
  "/dashboard": "National & Institution Command Dashboard",
  "/upload": "Bulk Student Data Ingestion & Validation Engine",
  "/cases": "Compliance Inquiry & Dispute Cases Desk",
  "/verify": "Zero-Trust Offline Verifier & QR Credential",
  "/consent": "DPDP Act 2023 Granular Consent Wallet",
  "/audit": "Cryptographic SHA-256 Chained Audit Trail",
  "/intelligence": "ML Ghost Student Radar & Seat Allocation Suite",
  "/sentinel": "AICTE Sentinel Autonomous Agent & Human Approval Desk",
};

export function AuthGate({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user, isAuthenticated, isLoading, login, logout } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // The landing/login page ("/") is public
  if (pathname === "/") {
    return <>{children}</>;
  }

  // Loading state while verifying cryptographic session
  if (isLoading) {
    return (
      <div className="min-h-[80vh] flex flex-col items-center justify-center p-8 space-y-4">
        <div className="w-12 h-12 rounded-2xl bg-primary/10 border border-primary/30 flex items-center justify-center text-primary animate-pulse">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div className="space-y-1 text-center">
          <h3 className="text-base font-bold text-foreground">Verifying Cryptographic Session</h3>
          <p className="text-xs text-muted-foreground font-mono">
            Checking AICTE RBAC token & Ed25519 root authority credentials...
          </p>
        </div>
      </div>
    );
  }

  // ==================== 1. NOT AUTHENTICATED: STRICT LOGIN GATE ====================
  if (!isAuthenticated || !user) {
    const handleManualLogin = async (e: React.FormEvent) => {
      e.preventDefault();
      setIsSubmitting(true);
      setAuthError(null);
      try {
        await login(email, password, otp || undefined);
      } catch (err: any) {
        setAuthError(err.message || "Invalid credentials. Please verify your official email and password.");
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="min-h-[85vh] flex items-center justify-center p-4 sm:p-8 bg-gradient-to-b from-background via-muted/20 to-background">
        <div className="w-full max-w-4xl space-y-6">
          {/* Security Alert Header */}
          <div className="relative overflow-hidden rounded-3xl border border-destructive/40 bg-card p-6 sm:p-8 shadow-2xl text-center space-y-3">
            <div className="w-16 h-16 rounded-2xl bg-destructive/10 border border-destructive/30 flex items-center justify-center mx-auto text-destructive shadow-lg shadow-destructive/10">
              <Lock className="w-8 h-8 animate-bounce" />
            </div>

            <div className="space-y-1">
              <span className="text-[11px] font-extrabold uppercase tracking-widest px-3 py-1 rounded-full bg-destructive/10 text-destructive border border-destructive/20">
                Official Access Restricted
              </span>
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-foreground mt-2">
                Authentication Required for AICTE Portal Access
              </h2>
              <p className="text-xs sm:text-sm text-muted-foreground max-w-xl mx-auto">
                You are attempting to access <code className="px-2 py-0.5 rounded bg-muted font-mono text-foreground font-semibold">{pathname}</code>.
                In accordance with AICTE Central Academic Repository Regulations and DPDP Act 2023, access is strictly restricted to authorized personnel.
              </p>
            </div>
          </div>

          {authError && (
            <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/30 text-destructive text-xs flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {/* Login Form + Authorized Personnel Directory */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
            {/* Direct Official Login Form */}
            <div className="md:col-span-5 p-6 rounded-3xl bg-card border border-border space-y-4 shadow-sm">
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <KeyRound className="w-4 h-4 text-primary" />
                  <span>Official Personnel Login</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Enter your registered institutional credentials to proceed:
                </p>
              </div>

              <form onSubmit={handleManualLogin} className="space-y-3">
                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground">Registered Email Address</label>
                  <div className="relative mt-1">
                    <Mail className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="email"
                      required
                      placeholder="e.g. admin@aicte.gov.in"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-muted/50 border border-border text-xs focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground">Password</label>
                  <div className="relative mt-1">
                    <Lock className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
                    <input
                      type="password"
                      required
                      placeholder="••••••••••••"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      className="w-full pl-9 pr-3 py-2 rounded-xl bg-muted/50 border border-border text-xs focus:outline-none focus:border-primary"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-[11px] font-semibold text-muted-foreground">
                    6-Digit MFA Security Code <span className="text-[10px] text-muted-foreground/80">(Optional)</span>
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    placeholder="123456"
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-muted/50 border border-border text-xs font-mono tracking-widest text-center mt-1 focus:outline-none focus:border-primary"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || !email || !password}
                  className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs shadow-md shadow-primary/20 flex items-center justify-center gap-2 hover:opacity-90 transition-all disabled:opacity-50 cursor-pointer mt-2"
                >
                  {isSubmitting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Authenticating Credentials...</span>
                    </>
                  ) : (
                    <>
                      <Unlock className="w-3.5 h-3.5" />
                      <span>Authenticate & Access Portal</span>
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Official Authorized Personnel Directory */}
            <div className="md:col-span-7 p-6 rounded-3xl bg-card border border-border space-y-4 shadow-sm">
              <div className="space-y-1">
                <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-500" />
                  <span>Authorized Personnel Registry & Scope</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Credentials for registered institutional personnel (Password: <code className="font-mono font-bold text-foreground">Password@123</code>):
                </p>
              </div>

              <div className="space-y-2 max-h-[380px] overflow-y-auto pr-1">
                {[
                  {
                    role: "AICTE Central Admin",
                    email: "admin@aicte.gov.in",
                    scope: "Full National Oversight, ML Radar, AI Sentinel, Reports",
                    badge: "Full Clearance",
                    badgeColor: "bg-amber-500/10 text-amber-500 border-amber-500/30",
                  },
                  {
                    role: "Regional Vigilance Officer",
                    email: "ro.delhi@aicte.gov.in",
                    scope: "Regional Dashboard, Cases Desk, Sentinel Sanction Approvals",
                    badge: "Regional",
                    badgeColor: "bg-blue-500/10 text-blue-500 border-blue-500/30",
                  },
                  {
                    role: "Institution Registrar (IIT Delhi)",
                    email: "admin@iitd.ac.in",
                    scope: "College Dashboard, Student CSV Upload, Branch Quotas",
                    badge: "Institution",
                    badgeColor: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
                  },
                  {
                    role: "State University Regulator",
                    email: "regulator@aktu.ac.in",
                    scope: "Affiliated Colleges Intake Monitoring & Verification",
                    badge: "Regulator",
                    badgeColor: "bg-purple-500/10 text-purple-500 border-purple-500/30",
                  },
                  {
                    role: "Corporate Employer Verifier",
                    email: "tcs.verifier@tcs.com",
                    scope: "Offline QR Cryptographic Verifier & Selective Disclosure",
                    badge: "Verifier",
                    badgeColor: "bg-cyan-500/10 text-cyan-500 border-cyan-500/30",
                  },
                  {
                    role: "Enrolled Student (Aarav Sharma)",
                    email: "aarav.sharma@satya.gov.in",
                    scope: "Personal DPDP Consent Wallet & Verifiable QR Credential",
                    badge: "Student",
                    badgeColor: "bg-indigo-500/10 text-indigo-500 border-indigo-500/30",
                  },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-2xl bg-muted/40 border border-border text-xs space-y-1 hover:border-border/80 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-foreground">{item.role}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-semibold ${item.badgeColor}`}>
                        {item.badge}
                      </span>
                    </div>
                    <div className="text-[11px] font-mono text-primary font-semibold">{item.email}</div>
                    <div className="text-[11px] text-muted-foreground">{item.scope}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // ==================== 2. AUTHENTICATED: STRICT RBAC AUTHORIZATION ====================
  const userRole = user.role;
  const allowedRoutes = ROLE_PERMISSIONS[userRole] || [];
  const hasAccess = allowedRoutes.includes(pathname);

  if (!hasAccess) {
    const primaryRoute = allowedRoutes[0] || "/";
    const currentModuleName = MODULE_NAMES[pathname] || pathname;

    return (
      <div className="min-h-[85vh] flex items-center justify-center p-4 sm:p-8 bg-gradient-to-b from-background via-muted/20 to-background">
        <div className="w-full max-w-xl p-8 rounded-3xl border border-destructive/40 bg-card shadow-2xl text-center space-y-6">
          <div className="w-16 h-16 rounded-2xl bg-destructive/10 border border-destructive/30 flex items-center justify-center mx-auto text-destructive shadow-lg shadow-destructive/10">
            <AlertTriangle className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <span className="text-[11px] font-extrabold uppercase tracking-widest px-3 py-1 rounded-full bg-destructive/10 text-destructive border border-destructive/20">
              403 Forbidden • Access Denied
            </span>
            <h2 className="text-2xl font-black tracking-tight text-foreground mt-2">
              Unauthorized Personnel Role
            </h2>
            <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
              Your registered personnel account (<strong className="text-foreground">{user.full_name}</strong>, Role: <strong className="text-primary">{user.role}</strong>) is not authorized to access:
            </p>
            <div className="p-3 rounded-xl bg-muted/60 border border-border text-xs font-semibold text-foreground">
              {currentModuleName} (<code className="font-mono text-primary">{pathname}</code>)
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-muted/30 border border-border text-left text-xs space-y-2">
            <div className="font-bold text-foreground flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span>Your Authorized Workspace Modules:</span>
            </div>
            <ul className="list-disc list-inside text-muted-foreground space-y-1">
              {allowedRoutes.map((route, idx) => (
                <li key={idx}>
                  <Link href={route} className="text-primary hover:underline font-medium">
                    {MODULE_NAMES[route] || route}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 pt-2">
            <Link
              href={primaryRoute}
              className="flex-1 w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs flex items-center justify-center gap-2 shadow-md hover:opacity-90 transition-all"
            >
              <span>Return to Authorized Workspace</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <button
              onClick={logout}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl border border-destructive/30 hover:bg-destructive/10 text-destructive font-bold text-xs flex items-center justify-center gap-2 transition-all cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign In as Different Personnel</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // User is authenticated AND authorized for this specific route
  return <>{children}</>;
}
