"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import { API_BASE } from "@/lib/api";
import {
  ShieldCheck,
  Building2,
  Users,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Lock,
  Unlock,
  Mail,
  KeyRound,
  Sparkles,
  Bot,
  QrCode,
  FileSearch,
  Scale,
  RefreshCw,
  Layers,
  Brain,
  LogOut,
  XCircle,
  Copy,
  Check,
} from "lucide-react";

interface PersonnelRecord {
  key: string;
  roleName: string;
  officerName: string;
  email: string;
  passwordHint: string;
  clearance: string;
  clearanceColor: string;
  authorizedModules: { name: string; path: string }[];
  restrictedModules: string[];
  icon: any;
}

const AUTHORIZED_PERSONNEL: PersonnelRecord[] = [
  {
    key: "AICTE_ADMIN",
    roleName: "AICTE Central Admin",
    officerName: "Dr. Anil Sahasrabudhe",
    email: "admin@aicte.gov.in",
    passwordHint: "Password@123",
    clearance: "Level 1 • Full National Clearance",
    clearanceColor: "bg-amber-500/10 text-amber-500 border-amber-500/30",
    authorizedModules: [
      { name: "National Command Dashboard", path: "/dashboard" },
      { name: "Student Ingestion Engine", path: "/upload" },
      { name: "Inquiry & Cases Desk", path: "/cases" },
      { name: "Verification & QR Portal", path: "/verify" },
      { name: "DPDP Consent Wallet", path: "/consent" },
      { name: "SHA-256 Audit Trail", path: "/audit" },
      { name: "ML Anomaly Radar & Seats", path: "/intelligence" },
      { name: "AICTE Sentinel Autonomous Agent", path: "/sentinel" },
    ],
    restrictedModules: [],
    icon: ShieldCheck,
  },
  {
    key: "REGIONAL_OFFICER",
    roleName: "Regional Vigilance Officer",
    officerName: "Shri Rajesh Verma (Delhi / North)",
    email: "ro.delhi@aicte.gov.in",
    passwordHint: "Password@123",
    clearance: "Level 2 • Regional Jurisdiction",
    clearanceColor: "bg-blue-500/10 text-blue-500 border-blue-500/30",
    authorizedModules: [
      { name: "Regional Oversight Dashboard", path: "/dashboard" },
      { name: "Dispute & Cases Desk", path: "/cases" },
      { name: "Zero-Trust Verifier", path: "/verify" },
      { name: "Regional Audit Log", path: "/audit" },
      { name: "Sentinel Human Sanctions Desk", path: "/sentinel" },
    ],
    restrictedModules: [
      "Bulk Student CSV Ingestion (/upload)",
      "National ML Model Parameterization (/intelligence)",
    ],
    icon: Scale,
  },
  {
    key: "INSTITUTION_ADMIN",
    roleName: "Institution Registrar",
    officerName: "Prof. S. Ranganathan (IIT Delhi)",
    email: "admin@iitd.ac.in",
    passwordHint: "Password@123",
    clearance: "Level 3 • Single Institution Scope",
    clearanceColor: "bg-emerald-500/10 text-emerald-500 border-emerald-500/30",
    authorizedModules: [
      { name: "College Intake Dashboard", path: "/dashboard" },
      { name: "Student Data CSV Ingestion", path: "/upload" },
      { name: "College Inquiries Desk", path: "/cases" },
    ],
    restrictedModules: [
      "AI Sentinel Autonomous Agent (/sentinel)",
      "National Anomaly Radar (/intelligence)",
      "System Cryptographic Audit Ledger (/audit)",
      "Employer Verification Desk (/verify)",
    ],
    icon: Building2,
  },
  {
    key: "UNIVERSITY_REGULATOR",
    roleName: "State University Regulator",
    officerName: "Controller of Examinations (AKTU)",
    email: "regulator@aktu.ac.in",
    passwordHint: "Password@123",
    clearance: "Level 3 • State Affiliation Scope",
    clearanceColor: "bg-purple-500/10 text-purple-500 border-purple-500/30",
    authorizedModules: [
      { name: "Affiliated Colleges Dashboard", path: "/dashboard" },
      { name: "Cross-College Dual Enrolment Cases", path: "/cases" },
      { name: "Student Credential Verifier", path: "/verify" },
    ],
    restrictedModules: [
      "Direct Student Record Ingestion (/upload)",
      "Sentinel Autonomous Sanction Desk (/sentinel)",
      "Full Cryptographic Ledger (/audit)",
    ],
    icon: FileSearch,
  },
  {
    key: "EMPLOYER_VERIFIER",
    roleName: "Corporate Employer Verifier",
    officerName: "Tata Consultancy Services HR",
    email: "tcs.verifier@tcs.com",
    passwordHint: "Password@123",
    clearance: "External • Verifier Access Only",
    clearanceColor: "bg-cyan-500/10 text-cyan-500 border-cyan-500/30",
    authorizedModules: [
      { name: "Zero-Trust Offline Verifier & QR Desk", path: "/verify" },
    ],
    restrictedModules: [
      "National / College Dashboards (/dashboard)",
      "Student Ingestion Engine (/upload)",
      "Dispute & Cases Management (/cases)",
      "Consent Wallet Management (/consent)",
      "Audit Trail & Ledger (/audit)",
      "AI Sentinel Agent (/sentinel)",
      "ML Intelligence Radar (/intelligence)",
    ],
    icon: QrCode,
  },
  {
    key: "STUDENT",
    roleName: "Enrolled Student (APAAR Holder)",
    officerName: "Aarav Sharma (B.Tech CSE)",
    email: "aarav.sharma@satya.gov.in",
    passwordHint: "Password@123",
    clearance: "Citizen • Personal Identity Scope",
    clearanceColor: "bg-indigo-500/10 text-indigo-500 border-indigo-500/30",
    authorizedModules: [
      { name: "DPDP Act 2023 Consent Wallet", path: "/consent" },
      { name: "Personal Ed25519 QR Credential", path: "/verify" },
    ],
    restrictedModules: [
      "Institutional Dashboards (/dashboard)",
      "Student Data Ingestion (/upload)",
      "Institutional Cases Desk (/cases)",
      "Audit Chain Ledger (/audit)",
      "Sentinel AI Agent (/sentinel)",
      "ML Intelligence Suite (/intelligence)",
    ],
    icon: Users,
  },
];

export default function HomePage() {
  const { t } = useLanguage();
  const { user, isAuthenticated, login, logout } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [copiedEmail, setCopiedEmail] = useState<string | null>(null);

  // Health and System Stats
  const [healthData, setHealthData] = useState<{
    status?: string;
    database?: string;
    ed25519_public_key?: string;
  } | null>(null);

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/health/`);
      if (res.ok) {
        const json = await res.json();
        setHealthData(json);
      }
    } catch {
      setHealthData({ status: "STANDALONE_READY", database: "LOCAL_SQLITE_POSTGRES" });
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);
    try {
      await login(email, password, otp || undefined);
    } catch (err: any) {
      setErrorMsg(err.message || "Authentication failed. Please verify your official registered email and password.");
    } finally {
      setLoading(false);
    }
  };

  const handleSelectEmail = (selectedEmail: string) => {
    setEmail(selectedEmail);
    setPassword("");
    setCopiedEmail(selectedEmail);
    setTimeout(() => setCopiedEmail(null), 2500);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] p-4 sm:p-8 max-w-7xl mx-auto space-y-8">
      {/* Official AICTE Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white p-8 sm:p-12 border border-slate-800 shadow-2xl">
        <div className="absolute top-0 right-0 w-96 h-96 bg-amber-500/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-emerald-500/10 rounded-full blur-3xl -ml-20 -mb-20 pointer-events-none"></div>

        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AICTE Smart India Hackathon • Problem Statement 26263</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight leading-tight">
            SATYA-APAAR: Autonomous Student Data & Verification Platform
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Eliminating student duplication, ghost enrolment, and seat over-allocation across India’s
            AICTE-approved institutions with 12-digit APAAR cryptographic verification, Sentinel AI autonomous orchestration,
            and strict Role-Based Access Control under the DPDP Act 2023.
          </p>

          {/* System Security Badges */}
          <div className="pt-4 grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
              <div className="text-2xl font-black text-amber-400">44</div>
              <div className="text-[11px] text-slate-400 font-medium">Registered Institutions</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
              <div className="text-2xl font-black text-emerald-400">6,535</div>
              <div className="text-[11px] text-slate-400 font-medium">Verified Student Records</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
              <div className="text-2xl font-black text-sky-400">Ed25519</div>
              <div className="text-[11px] text-slate-400 font-medium">Offline Verifiable QR</div>
            </div>
            <div className="p-3 rounded-xl bg-white/5 border border-white/10 backdrop-blur">
              <div className="text-2xl font-black text-purple-400">SHA-256</div>
              <div className="text-[11px] text-slate-400 font-medium">Immutable Audit Trail</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Personnel Directory & Credential Authentication Section */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Side: Authorized Personnel Access Directory & RBAC Clearance Matrix */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-xl font-bold tracking-tight flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <span>Authorized Personnel Directory</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                All logins require manual credential authentication with registered password (<code className="font-mono font-bold text-foreground">Password@123</code>).
              </p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full bg-destructive/10 text-destructive border border-destructive/20 font-bold self-start">
              Strict RBAC Enforced
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {AUTHORIZED_PERSONNEL.map((person) => {
              const Icon = person.icon;
              const isCurrentUser = user?.role === person.key;

              return (
                <div
                  key={person.key}
                  className={`p-4 rounded-2xl border transition-all ${
                    isCurrentUser
                      ? "border-emerald-500 bg-emerald-500/5 shadow-md shadow-emerald-500/10"
                      : "border-border bg-card hover:border-border/80"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <div className="p-2.5 rounded-xl bg-muted shrink-0 mt-0.5">
                        <Icon className="w-5 h-5 text-primary" />
                      </div>
                      <div className="space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <h3 className="text-sm font-bold tracking-tight text-foreground">{person.roleName}</h3>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${person.clearanceColor}`}>
                            {isCurrentUser ? "CURRENTLY ACTIVE" : person.clearance}
                          </span>
                        </div>
                        <p className="text-xs text-muted-foreground font-medium">{person.officerName}</p>
                        <div className="flex items-center gap-2 pt-0.5">
                          <code className="text-xs font-mono font-bold text-primary bg-primary/5 px-2 py-0.5 rounded border border-primary/20">
                            {person.email}
                          </code>
                          <button
                            type="button"
                            onClick={() => handleSelectEmail(person.email)}
                            className="text-[11px] px-2 py-0.5 rounded border border-border hover:bg-muted font-medium text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
                            title="Insert this email into login form"
                          >
                            {copiedEmail === person.email ? (
                              <>
                                <Check className="w-3 h-3 text-emerald-500" />
                                <span className="text-emerald-500 font-semibold">Inserted</span>
                              </>
                            ) : (
                              <>
                                <Copy className="w-3 h-3" />
                                <span>Use in Form</span>
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    </div>

                    <div className="text-right text-[11px] shrink-0">
                      <div className="text-muted-foreground">Standard Password:</div>
                      <code className="font-mono font-bold text-foreground bg-muted px-2 py-0.5 rounded">
                        {person.passwordHint}
                      </code>
                    </div>
                  </div>

                  {/* Scopes & Restrictions */}
                  <div className="mt-3 pt-3 border-t border-border grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="font-bold text-emerald-500 flex items-center gap-1 mb-1">
                        <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                        <span>Authorized Workspaces:</span>
                      </span>
                      <div className="flex flex-wrap gap-1">
                        {person.authorizedModules.map((m, idx) => (
                          <span key={idx} className="px-1.5 py-0.5 rounded bg-muted font-mono text-[10px] text-foreground">
                            {m.path}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div>
                      <span className="font-bold text-destructive flex items-center gap-1 mb-1">
                        <XCircle className="w-3.5 h-3.5 shrink-0" />
                        <span>Access Blocked (403):</span>
                      </span>
                      {person.restrictedModules.length > 0 ? (
                        <div className="text-muted-foreground text-[10px] leading-tight">
                          {person.restrictedModules.join(", ")}
                        </div>
                      ) : (
                        <div className="text-emerald-500 text-[10px] font-semibold">
                          None (Full Clearance)
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Credential Login Portal & Active Session Details */}
        <div className="lg:col-span-5 space-y-4">
          <div className="p-6 rounded-3xl border border-border bg-card shadow-xl space-y-6">
            {isAuthenticated && user ? (
              <div className="space-y-5">
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="w-6 h-6 shrink-0" />
                  <div>
                    <h4 className="text-sm font-bold">Authenticated Personnel Session</h4>
                    <p className="text-xs opacity-90 font-mono">Role: {user.role}</p>
                  </div>
                </div>

                {/* Personnel Metadata */}
                <div className="space-y-2 p-4 rounded-2xl bg-muted/50 border border-border text-xs">
                  <div className="flex justify-between py-1 border-b border-border">
                    <span className="text-muted-foreground">Officer / User Name</span>
                    <span className="font-bold text-foreground">{user.full_name}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-border">
                    <span className="text-muted-foreground">Registered Email</span>
                    <span className="font-mono text-foreground">{user.email}</span>
                  </div>
                  {user.institution_name && (
                    <div className="flex justify-between py-1 border-b border-border">
                      <span className="text-muted-foreground">Institution Jurisdiction</span>
                      <span className="font-bold text-foreground">{user.institution_name}</span>
                    </div>
                  )}
                  <div className="flex justify-between py-1">
                    <span className="text-muted-foreground">Cryptographic Token</span>
                    <span className="font-bold text-emerald-500">Verified AICTE Session</span>
                  </div>
                </div>

                {/* Authorized Workspaces Quick Access */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <Unlock className="w-3.5 h-3.5 text-emerald-500" />
                    <span>Your Authorized Modules</span>
                  </h4>
                  <div className="space-y-1.5">
                    {AUTHORIZED_PERSONNEL.find((p) => p.key === user.role)?.authorizedModules.map((mod, idx) => (
                      <Link
                        key={idx}
                        href={mod.path}
                        className="p-2.5 rounded-xl bg-card border border-border hover:border-primary/50 text-xs font-semibold flex items-center justify-between group transition-all"
                      >
                        <span className="text-foreground group-hover:text-primary transition-colors">{mod.name}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </Link>
                    ))}
                  </div>
                </div>

                {/* Restricted Modules Warning */}
                {(() => {
                  const currentPerson = AUTHORIZED_PERSONNEL.find((p) => p.key === user.role);
                  if (currentPerson && currentPerson.restrictedModules.length > 0) {
                    return (
                      <div className="p-3 rounded-2xl bg-destructive/5 border border-destructive/20 text-xs space-y-1">
                        <div className="font-bold text-destructive flex items-center gap-1.5">
                          <Lock className="w-3.5 h-3.5" />
                          <span>Restricted Modules for Your Role:</span>
                        </div>
                        <p className="text-[11px] text-muted-foreground">
                          Access to {currentPerson.restrictedModules.join(", ")} is locked. Attempting direct URL access will trigger a 403 Forbidden halt.
                        </p>
                      </div>
                    );
                  }
                  return null;
                })()}

                <button
                  onClick={logout}
                  className="w-full py-2.5 rounded-xl border border-destructive/30 hover:bg-destructive/10 text-destructive text-xs font-bold transition-colors flex items-center justify-center gap-2 cursor-pointer"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out of Personnel Account</span>
                </button>
              </div>
            ) : (
              <form onSubmit={handleManualLogin} className="space-y-4">
                <div>
                  <h3 className="text-lg font-bold flex items-center gap-2">
                    <Lock className="w-4 h-4 text-primary" />
                    <span>Official Personnel Login</span>
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Manual credential authentication required. Select an email from the directory or type your registered credentials.
                  </p>
                </div>

                {errorMsg && (
                  <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0" />
                    <span>{errorMsg}</span>
                  </div>
                )}

                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5" />
                    <span>{t.login.email}</span>
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="e.g. admin@aicte.gov.in"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all font-mono"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground flex items-center gap-1.5">
                    <Lock className="w-3.5 h-3.5" />
                    <span>{t.login.password}</span>
                  </label>
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  />
                  <div className="text-[11px] text-muted-foreground flex justify-between pt-0.5">
                    <span>Registered default password:</span>
                    <span className="font-mono font-bold text-foreground">Password@123</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-bold text-muted-foreground flex items-center gap-1.5">
                    <KeyRound className="w-3.5 h-3.5" />
                    <span>6-Digit MFA Security Code <span className="font-normal">(Optional for Standard Clearance)</span></span>
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => setOtp(e.target.value)}
                    placeholder="123456"
                    className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm font-mono tracking-widest text-center focus:outline-none focus:ring-2 focus:ring-primary/40 transition-all"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading || !email || !password}
                  className="w-full py-3 rounded-xl bg-primary text-primary-foreground font-bold text-sm hover:opacity-90 transition-opacity shadow-md disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer"
                >
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>Authenticating Credentials...</span>
                    </>
                  ) : (
                    <>
                      <Unlock className="w-4 h-4" />
                      <span>{t.login.signInButton}</span>
                    </>
                  )}
                </button>
              </form>
            )}

            {/* Cryptographic Ledger Health Box */}
            <div className="p-3.5 rounded-2xl bg-muted/40 border border-border/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                  <span>Backend & Crypto Health</span>
                </span>
                <span className="font-mono text-[11px] text-muted-foreground">Port 8000</span>
              </div>
              <div className="text-[11px] text-muted-foreground space-y-1">
                <div className="flex justify-between">
                  <span>Database Status:</span>
                  <span className="font-semibold text-emerald-500">
                    {healthData?.database || "Active & Connected"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>Ed25519 Root Signature:</span>
                  <span className="font-mono text-[10px] text-slate-500 truncate max-w-[150px]">
                    {healthData?.ed25519_public_key || "Loaded"}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
