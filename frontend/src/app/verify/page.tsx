"use client";

import React, { useState, useEffect, useRef } from "react";
import QRCode from "qrcode";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  QrCode,
  Copy,
  Download,
  Lock,
  Unlock,
  Building,
  GraduationCap,
  Calendar,
  FileCheck2,
  KeyRound,
  RefreshCw,
  Search,
  ExternalLink,
  Printer,
  Sparkles,
} from "lucide-react";
import {
  verificationApi,
  VerificationResponseData,
  OfflineVerifyResult,
} from "@/lib/api";

export default function VerificationPortalPage() {
  const [activeTab, setActiveTab] = useState<"online" | "offline">("online");

  // Online Verification Form State
  const [apaarId, setApaarId] = useState("100000000015");
  const [verifierName, setVerifierName] = useState("Vikram Malhotra");
  const [verifierOrg, setVerifierOrg] = useState("Tata Consultancy Services");
  const [verifierRole, setVerifierRole] = useState("EMPLOYER_VERIFIER");
  const [purpose, setPurpose] = useState("Campus Recruitment Drive 2026");
  const [otpCode, setOtpCode] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [onlineResult, setOnlineResult] = useState<VerificationResponseData | null>(null);
  const [onlineError, setOnlineError] = useState<string | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState<string>("");

  // Offline Verifier State
  const [offlineClaimJson, setOfflineClaimJson] = useState("");
  const [offlineSignature, setOfflineSignature] = useState("");
  const [offlinePublicKey, setOfflinePublicKey] = useState("");
  const [offlineResult, setOfflineResult] = useState<OfflineVerifyResult | null>(null);
  const [isOfflineVerifying, setIsOfflineVerifying] = useState(false);
  const [originalClaimBackup, setOriginalClaimBackup] = useState("");
  const [isTamperedState, setIsTamperedState] = useState(false);

  // Generate QR Code whenever onlineResult changes
  useEffect(() => {
    if (onlineResult?.qr_payload) {
      QRCode.toDataURL(onlineResult.qr_payload, {
        width: 256,
        margin: 2,
        color: {
          dark: "#0f172a",
          light: "#ffffff",
        },
      })
        .then((url) => setQrDataUrl(url))
        .catch((err) => console.error("QR Code Error:", err));

      // Also pre-fill offline verifier with authentic claim for seamless demo
      setOfflineClaimJson(JSON.stringify(onlineResult.canonical_claim, null, 2));
      setOriginalClaimBackup(JSON.stringify(onlineResult.canonical_claim, null, 2));
      setOfflineSignature(onlineResult.signature_ed25519);
      setOfflinePublicKey(onlineResult.public_key_b64);
      setIsTamperedState(false);
    }
  }, [onlineResult]);

  const handleOnlineVerify = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoading(true);
    setOnlineError(null);
    try {
      const data = await verificationApi.verifyStudent({
        apaar_id: apaarId.replace(/\D/g, ""),
        verifier_name: verifierName,
        verifier_org: verifierOrg,
        verifier_role: verifierRole,
        purpose: purpose,
        otp_code: otpCode ? otpCode.trim() : undefined,
      });
      setOnlineResult(data);
    } catch (err: any) {
      setOnlineError(err.message || "Verification failed");
      setOnlineResult(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOfflineVerify = async () => {
    setIsOfflineVerifying(true);
    try {
      let parsedClaim = {};
      try {
        parsedClaim = JSON.parse(offlineClaimJson);
      } catch {
        setOfflineResult({
          is_valid: false,
          algorithm: "Ed25519",
          issuer: "LOCAL",
          verified_at: new Date().toISOString(),
          message: "Syntax Error: Claim input is not valid JSON.",
        });
        setIsOfflineVerifying(false);
        return;
      }

      const res = await verificationApi.verifyOffline({
        claim: parsedClaim,
        signature_ed25519: offlineSignature,
        public_key_b64: offlinePublicKey || undefined,
      });
      setOfflineResult(res);
    } catch (err: any) {
      setOfflineResult({
        is_valid: false,
        algorithm: "Ed25519",
        issuer: "UNKNOWN",
        verified_at: new Date().toISOString(),
        message: err.message || "Offline verification encountered an error",
      });
    } finally {
      setIsOfflineVerifying(false);
    }
  };

  const triggerTamperDemo = () => {
    try {
      const parsed = JSON.parse(offlineClaimJson);
      parsed.program = "Ph.D. in Cyber Forensics (FRAUDULENT_TAMPER)";
      parsed.enrollment_valid = true;
      setOfflineClaimJson(JSON.stringify(parsed, null, 2));
      setIsTamperedState(true);
      // Auto-trigger verification to immediately show the failure
      setTimeout(() => {
        handleOfflineVerify();
      }, 100);
    } catch (err) {
      console.error(err);
    }
  };

  const restoreOriginalClaim = () => {
    if (originalClaimBackup) {
      setOfflineClaimJson(originalClaimBackup);
      setIsTamperedState(false);
      setTimeout(() => {
        handleOfflineVerify();
      }, 100);
    }
  };

  const formatApaarDisplay = (raw: string) => {
    const cleaned = raw.replace(/\D/g, "");
    const parts = cleaned.match(/.{1,4}/g);
    return parts ? parts.join("-") : cleaned;
  };

  const downloadVerifiableJson = () => {
    if (!onlineResult) return;
    const blob = new Blob([onlineResult.qr_payload], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `SATYA-APAAR-${onlineResult.apaar_id}-credential.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4 sm:px-8 max-w-7xl mx-auto">
      {/* Top Banner & Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-cyan-500/10 text-cyan-500 border border-cyan-500/20 flex items-center gap-1.5">
              <FileCheck2 className="w-3.5 h-3.5" />
              <span>DPDP Act 2023 Compliant</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center gap-1.5">
              <KeyRound className="w-3.5 h-3.5" />
              <span>Ed25519 Root Attestation</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Universal Student Verification Portal
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Selective disclosure verification for employers, state boards, and public verifiers with offline cryptographic proof.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center bg-muted p-1 rounded-xl border border-border">
          <button
            onClick={() => setActiveTab("online")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "online"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-cyan-500" />
            <span>Authorized Verifier</span>
          </button>
          <button
            onClick={() => setActiveTab("offline")}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all ${
              activeTab === "offline"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <QrCode className="w-4 h-4 text-amber-500" />
            <span>Offline Cryptographic Verifier</span>
          </button>
        </div>
      </div>

      {activeTab === "online" ? (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mt-8">
          {/* Left Form: Search & Verification Request */}
          <div className="lg:col-span-5 space-y-6">
            <div className="p-6 rounded-2xl border border-border bg-card/60 backdrop-blur shadow-sm">
              <h2 className="text-base font-bold flex items-center gap-2 mb-4">
                <Search className="w-4 h-4 text-primary" />
                <span>Verification Request</span>
              </h2>

              {/* Quick Demo Pre-fills */}
              <div className="mb-5">
                <span className="text-[11px] font-semibold text-muted-foreground block mb-2">
                  Quick Demo Pre-fills (Judges 1-Click):
                </span>
                <div className="flex flex-wrap gap-1.5">
                  <button
                    type="button"
                    onClick={() => {
                      setApaarId("100000000015");
                      setVerifierName("TCS Recruitment Lead");
                      setVerifierOrg("Tata Consultancy Services");
                      setVerifierRole("EMPLOYER_VERIFIER");
                      setPurpose("Campus Recruitment Drive 2026");
                      setOtpCode("");
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg border border-border bg-muted/60 hover:bg-muted font-medium transition-colors"
                  >
                    Aarav Sharma (Merit Valid)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setApaarId("100000000028");
                      setVerifierName("Apex Rohtak Auditor");
                      setVerifierOrg("Haryana State Technical Board");
                      setVerifierRole("UNIVERSITY_REGULATOR");
                      setPurpose("Intake Limit Audit 2026");
                      setOtpCode("");
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg border border-border bg-muted/60 hover:bg-muted font-medium transition-colors"
                  >
                    Apex Rohtak Student
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setApaarId("100000000050");
                      setVerifierName("Audit Inspection Officer");
                      setVerifierOrg("AICTE Vigilance Cell");
                      setVerifierRole("AICTE_ADMIN");
                      setPurpose("Ghost Student Investigation");
                      setOtpCode("");
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg border border-border bg-muted/60 hover:bg-muted font-medium transition-colors"
                  >
                    Ghost Anomaly Student
                  </button>
                </div>
              </div>

              <form onSubmit={handleOnlineVerify} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1">
                    12-Digit APAAR ID:
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      maxLength={14}
                      value={formatApaarDisplay(apaarId)}
                      onChange={(e) => setApaarId(e.target.value.replace(/\D/g, ""))}
                      placeholder="1000-0000-0015"
                      className="w-full font-mono text-sm tracking-wider px-3 py-2 rounded-xl border border-border bg-background focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                      required
                    />
                    <span className="absolute right-3 top-2.5 text-[10px] text-muted-foreground font-mono">
                      {apaarId.length}/12
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground block mb-1">
                      Verifier Full Name:
                    </label>
                    <input
                      type="text"
                      value={verifierName}
                      onChange={(e) => setVerifierName(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-border bg-background outline-none"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground block mb-1">
                      Organization:
                    </label>
                    <input
                      type="text"
                      value={verifierOrg}
                      onChange={(e) => setVerifierOrg(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-border bg-background outline-none"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground block mb-1">
                      Verifier Role:
                    </label>
                    <select
                      value={verifierRole}
                      onChange={(e) => setVerifierRole(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-border bg-background outline-none font-medium"
                    >
                      <option value="EMPLOYER_VERIFIER">Employer Verifier</option>
                      <option value="UNIVERSITY_REGULATOR">University Regulator</option>
                      <option value="PUBLIC_VERIFIER">Public Verifier</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-muted-foreground block mb-1">
                      Purpose:
                    </label>
                    <input
                      type="text"
                      value={purpose}
                      onChange={(e) => setPurpose(e.target.value)}
                      className="w-full text-xs px-3 py-2 rounded-xl border border-border bg-background outline-none"
                      required
                    />
                  </div>
                </div>

                {/* Optional Elevated OTP */}
                <div className="p-3 rounded-xl bg-muted/40 border border-border">
                  <div className="flex items-center justify-between mb-1.5">
                    <label className="text-xs font-semibold text-muted-foreground flex items-center gap-1.5">
                      <KeyRound className="w-3.5 h-3.5 text-amber-500" />
                      <span>Student OTP (For Full PII Access):</span>
                    </label>
                    <span className="text-[10px] text-amber-600 dark:text-amber-400 font-medium">
                      Simulated: 123456
                    </span>
                  </div>
                  <input
                    type="text"
                    maxLength={6}
                    value={otpCode}
                    onChange={(e) => setOtpCode(e.target.value)}
                    placeholder="Enter 6-digit OTP (optional)"
                    className="w-full text-xs font-mono px-3 py-1.5 rounded-lg border border-border bg-background outline-none"
                  />
                  <p className="text-[10px] text-muted-foreground mt-1">
                    Without OTP, sensitive fields (DOB, Caste, Marks) are masked under DPDP Act 2023.
                  </p>
                </div>

                <button
                  type="submit"
                  disabled={isLoading || apaarId.length !== 12}
                  className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs shadow-md hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isLoading ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <ShieldCheck className="w-4 h-4" />
                  )}
                  <span>Execute Verification Request</span>
                </button>
              </form>
            </div>

            {/* DPDP Act Compliance Notice */}
            <div className="p-4 rounded-xl border border-blue-500/20 bg-blue-500/5 text-xs text-blue-600 dark:text-blue-400 space-y-1">
              <div className="flex items-center gap-1.5 font-bold">
                <Lock className="w-3.5 h-3.5" />
                <span>DPDP Act 2023 Principle of Data Minimization</span>
              </div>
              <p className="text-[11px] leading-relaxed opacity-90">
                Every verification access is cryptographically hash-chained in the audit ledger and visible in the student's transparent consent log. Sensitive identity attributes are redacted unless explicit temporary consent is granted.
              </p>
            </div>
          </div>

          {/* Right Area: Verification Results & Verifiable Credential */}
          <div className="lg:col-span-7">
            {onlineError && (
              <div className="p-6 rounded-2xl border border-destructive/30 bg-destructive/10 text-destructive flex items-start gap-3">
                <XCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                <div>
                  <h3 className="font-bold text-sm">Verification Query Failed</h3>
                  <p className="text-xs mt-1">{onlineError}</p>
                </div>
              </div>
            )}

            {!onlineResult && !onlineError && (
              <div className="h-full min-h-[420px] rounded-2xl border border-dashed border-border flex flex-col items-center justify-center p-8 text-center bg-card/30">
                <div className="w-16 h-16 rounded-2xl bg-muted flex items-center justify-center mb-3">
                  <ShieldCheck className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="font-bold text-base mb-1">Awaiting Verification Query</h3>
                <p className="text-xs text-muted-foreground max-w-md">
                  Enter an APAAR ID or click one of the quick demo pre-fills on the left to inspect the DPDP selective disclosure card and cryptographic Ed25519 credential.
                </p>
              </div>
            )}

            {onlineResult && (
              <div className="space-y-6">
                {/* Official Credential Header Card */}
                <div className="p-6 rounded-2xl border border-border bg-card/80 backdrop-blur shadow-lg relative overflow-hidden">
                  <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-amber-500 via-sky-400 to-emerald-500"></div>

                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-5">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>AICTE REPOSITORY VERIFIED</span>
                        </span>
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-500 border border-cyan-500/20">
                          {onlineResult.consent_status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <h2 className="text-xl font-extrabold tracking-tight">
                        {onlineResult.student_name}
                      </h2>
                      <p className="text-xs font-mono text-muted-foreground mt-0.5">
                        APAAR ID: {onlineResult.apaar_id_masked}
                      </p>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={downloadVerifiableJson}
                        className="px-3 py-1.5 rounded-lg border border-border bg-background hover:bg-muted text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-sm"
                        title="Download Verifiable JSON Certificate"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>JSON Proof</span>
                      </button>
                    </div>
                  </div>

                  {/* Selective Disclosure Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
                    <div className="p-3 rounded-xl bg-muted/50 border border-border/80">
                      <span className="text-[10px] font-bold text-muted-foreground block uppercase">
                        Institution & AICTE ID
                      </span>
                      <span className="text-xs font-bold block truncate mt-0.5">
                        {onlineResult.institution_name}
                      </span>
                      <span className="text-[10px] font-mono text-muted-foreground">
                        AICTE ID: {onlineResult.institution_aicte_id}
                      </span>
                    </div>

                    <div className="p-3 rounded-xl bg-muted/50 border border-border/80">
                      <span className="text-[10px] font-bold text-muted-foreground block uppercase">
                        Degree Program & Branch
                      </span>
                      <span className="text-xs font-bold block truncate mt-0.5">
                        {onlineResult.branch}
                      </span>
                      <span className="text-[10px] text-muted-foreground">
                        {onlineResult.program} • Year {onlineResult.year_of_study}
                      </span>
                    </div>
                  </div>

                  {/* Disclosed Fields Badges */}
                  <div className="mb-4">
                    <span className="text-[11px] font-bold text-muted-foreground block mb-2">
                      Disclosed Data Attributes:
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {Object.keys(onlineResult.disclosed_data).map((field) => (
                        <span
                          key={field}
                          className="px-2.5 py-1 rounded-lg text-[11px] font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>{field}: {String(onlineResult.disclosed_data[field])}</span>
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Restricted Sensitive Fields under DPDP Act */}
                  {onlineResult.restricted_fields.length > 0 && (
                    <div className="p-3 rounded-xl bg-amber-500/5 border border-amber-500/20">
                      <div className="flex items-center gap-1.5 text-xs font-bold text-amber-600 dark:text-amber-400 mb-1">
                        <Lock className="w-3.5 h-3.5" />
                        <span>Protected Under DPDP Act 2023 (Redacted by Consent):</span>
                      </div>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {onlineResult.restricted_fields.map((f) => (
                          <span
                            key={f}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                          >
                            [REDACTED: {f.toUpperCase()}]
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Signed Verifiable QR Credential Box */}
                <div className="p-6 rounded-2xl border border-border bg-card/60 backdrop-blur shadow-sm">
                  <div className="flex flex-col sm:flex-row items-center gap-6">
                    {/* Live Rendered QR Code */}
                    <div className="flex-shrink-0 flex flex-col items-center">
                      <div className="p-3 rounded-xl bg-white border border-border shadow-md">
                        {qrDataUrl ? (
                          <img
                            src={qrDataUrl}
                            alt="Verifiable Credential QR"
                            className="w-44 h-44 object-contain"
                          />
                        ) : (
                          <div className="w-44 h-44 flex items-center justify-center bg-slate-100">
                            <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
                          </div>
                        )}
                      </div>
                      <span className="text-[10px] font-mono font-bold text-muted-foreground mt-2">
                        SCAN TO VERIFY OFFLINE
                      </span>
                    </div>

                    {/* Cryptographic Details & Signature */}
                    <div className="flex-1 space-y-3 w-full">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                          AICTE Ed25519 Digital Signature:
                        </span>
                        <div className="mt-1 p-2 rounded-lg bg-muted/60 border border-border font-mono text-[11px] break-all select-all flex items-center justify-between">
                          <span className="truncate mr-2">
                            {onlineResult.signature_ed25519}
                          </span>
                          <button
                            onClick={() => navigator.clipboard.writeText(onlineResult.signature_ed25519)}
                            className="p-1 hover:bg-muted rounded"
                            title="Copy Signature"
                          >
                            <Copy className="w-3.5 h-3.5 text-muted-foreground" />
                          </button>
                        </div>
                      </div>

                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                          Issuer Public Key:
                        </span>
                        <div className="mt-1 p-2 rounded-lg bg-muted/60 border border-border font-mono text-[11px] break-all select-all">
                          {onlineResult.public_key_b64}
                        </div>
                      </div>

                      <div className="flex items-center gap-2 pt-1 text-[11px] text-muted-foreground">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        <span>Logged in DPDP Access Ledger #{onlineResult.access_log_id.slice(0, 8)}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Tab 2: Standalone Offline Cryptographic Verifier */
        <div className="mt-8 space-y-6">
          <div className="p-6 rounded-2xl border border-border bg-card/60 backdrop-blur">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <KeyRound className="w-5 h-5 text-amber-500" />
                  <span>Zero-Trust Standalone Offline Verifier</span>
                </h2>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Validates Ed25519 signatures completely offline without database connection. Proves the student's degree cannot be forged.
                </p>
              </div>

              {/* Hackathon Demo Action Buttons */}
              <div className="flex items-center gap-2">
                {!isTamperedState ? (
                  <button
                    onClick={triggerTamperDemo}
                    className="px-3.5 py-2 rounded-xl bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20 text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Simulate Fraudulent Alteration</span>
                  </button>
                ) : (
                  <button
                    onClick={restoreOriginalClaim}
                    className="px-3.5 py-2 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span>Restore Authentic Claim</span>
                  </button>
                )}
              </div>
            </div>

            {/* Offline Form Inputs */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <label className="text-xs font-bold text-muted-foreground block mb-1">
                  Canonical Credential Claim JSON:
                </label>
                <textarea
                  rows={10}
                  value={offlineClaimJson}
                  onChange={(e) => setOfflineClaimJson(e.target.value)}
                  placeholder={`{\n  "apaar_id_masked": "XXXX-XXXX-0015",\n  "student_name": "Aarav Sharma",\n  "program": "B.Tech in Computer Science",\n  "institution_name": "Delhi College of Engineering",\n  "aicte_approved": true\n}`}
                  className={`w-full font-mono text-xs p-3 rounded-xl border bg-background outline-none resize-none leading-relaxed transition-colors ${
                    isTamperedState
                      ? "border-destructive/60 bg-destructive/5 text-destructive"
                      : "border-border"
                  }`}
                />
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-xs font-bold text-muted-foreground block mb-1">
                    Ed25519 Digital Signature (Base64):
                  </label>
                  <textarea
                    rows={4}
                    value={offlineSignature}
                    onChange={(e) => setOfflineSignature(e.target.value)}
                    placeholder="Wp0f16r8xVb3..."
                    className="w-full font-mono text-xs p-3 rounded-xl border border-border bg-background outline-none resize-none break-all"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-muted-foreground block mb-1">
                    AICTE Public Root Key (Base64):
                  </label>
                  <input
                    type="text"
                    value={offlinePublicKey}
                    onChange={(e) => setOfflinePublicKey(e.target.value)}
                    placeholder="AICTE Master Key..."
                    className="w-full font-mono text-xs p-3 rounded-xl border border-border bg-background outline-none"
                  />
                </div>

                <button
                  onClick={handleOfflineVerify}
                  disabled={isOfflineVerifying || !offlineClaimJson || !offlineSignature}
                  className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs shadow-md hover:opacity-90 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  {isOfflineVerifying ? (
                    <RefreshCw className="w-4 h-4 animate-spin" />
                  ) : (
                    <KeyRound className="w-4 h-4" />
                  )}
                  <span>Verify Signature Offline (Pure Math / No DB)</span>
                </button>
              </div>
            </div>

            {/* Offline Result Status Banner */}
            {offlineResult && (
              <div
                className={`mt-6 p-6 rounded-2xl border flex items-start gap-4 transition-all ${
                  offlineResult.is_valid
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
                    : "bg-destructive/10 border-destructive/30 text-destructive"
                }`}
              >
                {offlineResult.is_valid ? (
                  <CheckCircle2 className="w-8 h-8 flex-shrink-0 mt-0.5 text-emerald-500" />
                ) : (
                  <XCircle className="w-8 h-8 flex-shrink-0 mt-0.5 text-destructive" />
                )}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-extrabold text-base">
                      {offlineResult.is_valid
                        ? "CRYPTOGRAPHIC SIGNATURE VALID (OFFLINE ATTESTATION)"
                        : "TAMPER DETECTED / INVALID SIGNATURE"}
                    </h3>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-background/50 border border-current">
                      {offlineResult.algorithm}
                    </span>
                  </div>
                  <p className="text-xs mt-1 leading-relaxed">{offlineResult.message}</p>
                  <div className="flex items-center gap-4 mt-3 text-[11px] opacity-80 font-mono">
                    <span>Issuer: {offlineResult.issuer}</span>
                    <span>Verified: {new Date(offlineResult.verified_at).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
