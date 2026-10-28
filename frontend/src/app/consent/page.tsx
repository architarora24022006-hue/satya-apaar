"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  Lock,
  Unlock,
  KeyRound,
  Eye,
  Clock,
  History,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Building,
  User,
  Save,
  RefreshCw,
  Send,
  Sliders,
  FileCheck2,
} from "lucide-react";
import {
  consentApi,
  ConsentWalletData,
  ConsentPolicy,
  AccessLogItem,
} from "@/lib/api";

const AVAILABLE_FIELDS = [
  { key: "apaar_id_masked", label: "Masked APAAR ID", sensitive: false, alwaysAllowed: true },
  { key: "student_name", label: "Full Name", sensitive: false, alwaysAllowed: true },
  { key: "institution_name", label: "Institution & AICTE ID", sensitive: false, alwaysAllowed: true },
  { key: "program", label: "Program & Branch", sensitive: false, alwaysAllowed: true },
  { key: "year_of_study", label: "Current Year of Study", sensitive: false, alwaysAllowed: true },
  { key: "aicte_approved", label: "AICTE Approval Status", sensitive: false, alwaysAllowed: true },
  { key: "dob", label: "Date of Birth (DOB)", sensitive: true, alwaysAllowed: false },
  { key: "category", label: "Social Category / Caste", sensitive: true, alwaysAllowed: false },
  { key: "gender", label: "Gender", sensitive: true, alwaysAllowed: false },
  { key: "admission_date", label: "Exact Admission Date", sensitive: true, alwaysAllowed: false },
  { key: "quota_type", label: "Admission Quota Type", sensitive: true, alwaysAllowed: false },
];

export default function StudentConsentWalletPage() {
  const [apaarId, setApaarId] = useState("100000000015");
  const [wallet, setWallet] = useState<ConsentWalletData | null>(null);
  const [accessLogs, setAccessLogs] = useState<AccessLogItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [generatedOtp, setGeneratedOtp] = useState<string | null>(null);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);

  const fetchWalletData = async (targetApaar = apaarId) => {
    setIsLoading(true);
    setSaveSuccess(false);
    try {
      const clean = targetApaar.replace(/\D/g, "");
      const [walletData, logsData] = await Promise.all([
        consentApi.getWallet(clean),
        consentApi.getAccessLogs(clean),
      ]);
      setWallet(walletData);
      setAccessLogs(logsData);
    } catch (err) {
      console.error("Failed to load consent wallet:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWalletData();
  }, []);

  const handleToggleField = (verifierType: string, fieldKey: string) => {
    if (!wallet) return;
    const updatedPolicies = wallet.policies.map((policy) => {
      if (policy.verifier_type === verifierType) {
        const hasField = policy.allowed_fields.includes(fieldKey);
        const newFields = hasField
          ? policy.allowed_fields.filter((f) => f !== fieldKey)
          : [...policy.allowed_fields, fieldKey];
        return { ...policy, allowed_fields: newFields };
      }
      return policy;
    });

    setWallet({ ...wallet, policies: updatedPolicies });
  };

  const handleToggleActive = (verifierType: string) => {
    if (!wallet) return;
    const updatedPolicies = wallet.policies.map((policy) => {
      if (policy.verifier_type === verifierType) {
        return { ...policy, is_active: !policy.is_active };
      }
      return policy;
    });
    setWallet({ ...wallet, policies: updatedPolicies });
  };

  const handleSavePolicies = async () => {
    if (!wallet) return;
    setIsSaving(true);
    setSaveSuccess(false);
    try {
      await consentApi.updateWallet(wallet.student_apaar_id, wallet.policies);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error("Failed to save consent policies:", err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRequestOtp = async () => {
    try {
      const res = await consentApi.requestOtp(apaarId.replace(/\D/g, ""));
      setGeneratedOtp(res.otp);
      setOtpMessage(res.message);
    } catch (err) {
      console.error("Failed to request OTP:", err);
    }
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4 sm:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>DPDP Act 2023 Sovereign Data Rights</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center gap-1.5">
              <Eye className="w-3.5 h-3.5" />
              <span>Full Access Transparency</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Student Consent Wallet & Privacy Shield
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Students retain full sovereign control over who views their academic credentials, which fields are disclosed, and can audit every access event.
          </p>
        </div>

        {/* Student Selector */}
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={apaarId}
            onChange={(e) => setApaarId(e.target.value)}
            placeholder="100000000015"
            className="w-40 font-mono text-xs px-3 py-2 rounded-xl border border-border bg-background outline-none"
          />
          <button
            onClick={() => fetchWalletData(apaarId)}
            disabled={isLoading}
            className="px-3 py-2 rounded-xl border border-border bg-muted hover:bg-background text-xs font-bold transition-colors flex items-center gap-1.5"
          >
            {isLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
            <span>Load</span>
          </button>
        </div>
      </div>

      {wallet && (
        <div className="p-4 rounded-2xl bg-gradient-to-r from-indigo-500/10 via-sky-500/5 to-emerald-500/10 border border-indigo-500/20 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/20 text-indigo-500 flex items-center justify-center font-bold text-lg">
              {wallet.student_name ? wallet.student_name[0] : "S"}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-base">{wallet.student_name}</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted border border-border font-bold">
                  {wallet.student_apaar_id}
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">
                Active Sovereign Consent Matrix • Governed under Section 6 of DPDP Act 2023
              </p>
            </div>
          </div>

          {/* Quick OTP Generator Trigger */}
          <div className="flex items-center gap-2">
            <button
              onClick={handleRequestOtp}
              className="px-3.5 py-2 rounded-xl bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 hover:bg-amber-500/20 text-xs font-bold transition-all flex items-center gap-2 shadow-sm"
            >
              <KeyRound className="w-4 h-4" />
              <span>Simulate Elevated OTP Dispatch</span>
            </button>
          </div>
        </div>
      )}

      {/* Simulated OTP Notification Banner */}
      {generatedOtp && (
        <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300 flex items-start gap-3 animate-in fade-in">
          <Send className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-xs uppercase tracking-wider">
                Simulated DigiLocker SMS Notification
              </span>
              <span className="font-mono font-bold text-sm bg-amber-500/20 px-2.5 py-0.5 rounded-lg border border-amber-500/30">
                {generatedOtp}
              </span>
            </div>
            <p className="text-xs mt-1">{otpMessage}</p>
          </div>
        </div>
      )}

      {/* Consent Policies Matrix */}
      {wallet && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Sliders className="w-4 h-4 text-primary" />
                <span>Field-Level Granular Consent Matrix</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Authorize or redact specific data attributes based on who is asking.
              </p>
            </div>

            <button
              onClick={handleSavePolicies}
              disabled={isSaving}
              className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-md hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-50"
            >
              {isSaving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>{saveSuccess ? "Preferences Saved!" : "Save Consent Policies"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {wallet.policies.map((policy) => {
              const roleTitle =
                policy.verifier_type === "EMPLOYER"
                  ? "Corporate Employers & Recruiters"
                  : policy.verifier_type === "UNIVERSITY"
                  ? "Universities & Academic Boards"
                  : "Public & Third-Party Verifiers";

              return (
                <div
                  key={policy.verifier_type}
                  className={`p-5 rounded-2xl border transition-all ${
                    policy.is_active
                      ? "bg-card/70 border-border shadow-sm"
                      : "bg-muted/30 border-dashed border-border/80 opacity-70"
                  }`}
                >
                  <div className="flex items-center justify-between pb-3 mb-4 border-b border-border">
                    <div>
                      <span className="text-[10px] font-extrabold tracking-wider text-muted-foreground uppercase">
                        {policy.verifier_type}
                      </span>
                      <h3 className="text-xs font-bold">{roleTitle}</h3>
                    </div>

                    <button
                      onClick={() => handleToggleActive(policy.verifier_type)}
                      className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-colors ${
                        policy.is_active
                          ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                          : "bg-muted text-muted-foreground border-border"
                      }`}
                    >
                      {policy.is_active ? "ACTIVE" : "PAUSED"}
                    </button>
                  </div>

                  <div className="space-y-2">
                    <span className="text-[11px] font-bold text-muted-foreground block mb-2">
                      Granted Attributes:
                    </span>
                    {AVAILABLE_FIELDS.map((field) => {
                      const isAllowed = policy.allowed_fields.includes(field.key);

                      return (
                        <div
                          key={field.key}
                          onClick={() => {
                            if (!field.alwaysAllowed) {
                              handleToggleField(policy.verifier_type, field.key);
                            }
                          }}
                          className={`flex items-center justify-between p-2 rounded-xl text-xs transition-colors cursor-pointer ${
                            field.alwaysAllowed
                              ? "bg-muted/40 cursor-not-allowed"
                              : isAllowed
                              ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20"
                              : "bg-muted/20 hover:bg-muted/60 text-muted-foreground border border-transparent"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            {field.alwaysAllowed ? (
                              <CheckCircle2 className="w-3.5 h-3.5 text-sky-500 flex-shrink-0" />
                            ) : isAllowed ? (
                              <Unlock className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />
                            ) : (
                              <Lock className="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
                            )}
                            <span className="font-medium text-[11px]">{field.label}</span>
                          </div>

                          <span className="text-[10px] font-mono font-bold">
                            {field.alwaysAllowed
                              ? "PUBLIC"
                              : isAllowed
                              ? "GRANTED"
                              : "REDACTED"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* DPDP Access History Transparency Audit Log */}
      <div className="p-6 rounded-2xl border border-border bg-card/60 backdrop-blur shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold flex items-center gap-2">
              <History className="w-4 h-4 text-primary" />
              <span>Access Transparency Audit Log (Right to be Informed)</span>
            </h2>
            <p className="text-xs text-muted-foreground">
              Under Section 11 of DPDP Act 2023, every query to your student record is permanently recorded.
            </p>
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            Total Accesses Logged: {accessLogs.length}
          </span>
        </div>

        {accessLogs.length === 0 ? (
          <div className="p-8 text-center text-xs text-muted-foreground border border-dashed border-border rounded-xl">
            No external entity has queried this student record yet.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/60 text-muted-foreground uppercase text-[10px] font-extrabold border-b border-border">
                <tr>
                  <th className="py-2.5 px-3">Timestamp</th>
                  <th className="py-2.5 px-3">Verifier Name</th>
                  <th className="py-2.5 px-3">Organization</th>
                  <th className="py-2.5 px-3">Role</th>
                  <th className="py-2.5 px-3">Purpose</th>
                  <th className="py-2.5 px-3">Disclosed Attributes</th>
                  <th className="py-2.5 px-3">Client IP</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {accessLogs.map((log) => (
                  <tr key={log.id} className="hover:bg-muted/30 transition-colors">
                    <td className="py-2.5 px-3 font-mono text-[11px] text-muted-foreground whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-2.5 px-3 font-semibold">{log.verifier_name}</td>
                    <td className="py-2.5 px-3 text-muted-foreground">{log.verifier_org}</td>
                    <td className="py-2.5 px-3">
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted border border-border">
                        {log.verifier_role}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-muted-foreground">{log.purpose}</td>
                    <td className="py-2.5 px-3">
                      <div className="flex flex-wrap gap-1 max-w-xs">
                        {log.accessed_fields.slice(0, 4).map((f) => (
                          <span
                            key={f}
                            className="px-1.5 py-0.5 rounded text-[9px] bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-mono"
                          >
                            {f}
                          </span>
                        ))}
                        {log.accessed_fields.length > 4 && (
                          <span className="text-[9px] text-muted-foreground">
                            +{log.accessed_fields.length - 4} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-mono text-[10px] text-muted-foreground">
                      {log.ip_address}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
