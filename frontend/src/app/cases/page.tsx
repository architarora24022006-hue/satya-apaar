"use client";

import React, { useState, useEffect } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import { API_BASE } from "@/lib/api";
import {
  Scale,
  AlertTriangle,
  Clock,
  CheckCircle2,
  Building2,
  User,
  ShieldAlert,
  ArrowRight,
  RefreshCw,
  FileText,
  Send,
} from "lucide-react";

export default function CasesPage() {
  const { t } = useLanguage();
  const { user, isAuthenticated } = useAuth();

  const [cases, setCases] = useState<any[]>([]);
  const [stats, setStats] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any | null>(null);
  const [resolutionNote, setResolutionNote] = useState("");
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  const fetchCasesData = async () => {
    setLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const [casesRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/cases/`, { headers }),
        fetch(`${API_BASE}/api/v1/cases/stats/summary`, { headers }),
      ]);

      if (casesRes.ok) {
        const casesJson = await casesRes.json();
        setCases(casesJson);
        if (casesJson.length > 0 && !selectedCase) {
          setSelectedCase(casesJson[0]);
        }
      }

      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } catch (e) {
      console.error("Failed to fetch cases:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCasesData();
  }, []);

  const handleResolveCase = async (caseId: string, statusVal: string = "RESOLVED") => {
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API_BASE}/api/v1/cases/${caseId}/resolve`, {
        method: "POST",
        headers,
        body: JSON.stringify({
          status: statusVal,
          resolution_notes: resolutionNote || "Approved resolution by AICTE Officer.",
        }),
      });

      if (res.ok) {
        setActionSuccess(`Case successfully marked as ${statusVal}!`);
        setResolutionNote("");
        fetchCasesData();
      }
    } catch (err: any) {
      alert("Failed to resolve case: " + err.message);
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-card border border-border shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-primary/10 text-primary">
              <Scale className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black tracking-tight">
              Dual-Enrolment & Intake Dispute Cases
            </h1>
          </div>
          <p className="text-xs text-muted-foreground">
            Real-time cross-college clashes, sanctioned intake breaches, and SLA resolution tracking under AICTE regulations.
          </p>
        </div>

        <button
          onClick={fetchCasesData}
          className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-border bg-muted/60 hover:bg-muted text-xs font-bold transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Feed</span>
        </button>
      </div>

      {/* KPI Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm">
          <span className="text-xs text-muted-foreground">Active Open Cases</span>
          <div className="text-2xl font-black text-primary">{stats?.active_cases_count || cases.length}</div>
        </div>
        <div className="p-4 rounded-2xl bg-card border border-red-500/30 bg-red-500/5 shadow-sm">
          <span className="text-xs text-red-500 font-bold">Urgent Clashes</span>
          <div className="text-2xl font-black text-red-500">{stats?.urgent_clashes_count || 2}</div>
        </div>
        <div className="p-4 rounded-2xl bg-card border border-emerald-500/30 bg-emerald-500/5 shadow-sm">
          <span className="text-xs text-emerald-500 font-bold">Resolved Cases</span>
          <div className="text-2xl font-black text-emerald-500">{stats?.resolved_cases_count || 0}</div>
        </div>
        <div className="p-4 rounded-2xl bg-card border border-border shadow-sm">
          <span className="text-xs text-muted-foreground">Average SLA Timer</span>
          <div className="text-2xl font-black text-amber-500">48h SLA</div>
        </div>
      </div>

      {actionSuccess && (
        <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionSuccess}</span>
        </div>
      )}

      {/* Main Split Grid: Case List vs Detail Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Side: Case Cards List */}
        <div className="lg:col-span-5 space-y-3">
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground px-1">
            Open Case Queue ({cases.length})
          </h3>

          <div className="space-y-3">
            {cases.map((c: any) => {
              const isSelected = selectedCase?.id === c.id;
              return (
                <div
                  key={c.id}
                  onClick={() => setSelectedCase(c)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-2 ${
                    isSelected
                      ? "border-primary bg-primary/5 shadow-md"
                      : "border-border bg-card hover:border-primary/40"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-muted-foreground">
                      {c.case_number}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border ${
                        c.priority === "URGENT"
                          ? "bg-red-500/10 text-red-500 border-red-500/30"
                          : "bg-amber-500/10 text-amber-500 border-amber-500/30"
                      }`}
                    >
                      {c.priority}
                    </span>
                  </div>

                  <h4 className="text-sm font-bold leading-snug tracking-tight">{c.title}</h4>

                  <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border/60">
                    <span className="flex items-center gap-1 font-mono text-[11px]">
                      <Clock className="w-3.5 h-3.5 text-amber-500" />
                      <span>SLA: 48h active</span>
                    </span>
                    <span className="font-bold text-[11px] px-2 py-0.5 rounded bg-muted">
                      {c.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right Side: Detailed Case Workspace */}
        <div className="lg:col-span-7">
          {selectedCase ? (
            <div className="p-6 rounded-3xl bg-card border border-border shadow-sm space-y-6">
              <div className="flex items-center justify-between border-b border-border pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-muted-foreground">
                      {selectedCase.case_number}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-red-500/10 text-red-500 border border-red-500/30">
                      {selectedCase.priority} PRIORITY
                    </span>
                  </div>
                  <h2 className="text-lg font-black tracking-tight mt-1">
                    {selectedCase.title}
                  </h2>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-muted-foreground block">Case Opened By</span>
                  <span className="text-xs font-bold px-2 py-0.5 rounded bg-purple-500/10 text-purple-500 border border-purple-500/20 font-mono">
                    {selectedCase.opened_by_type}
                  </span>
                </div>
              </div>

              {/* Institution Clash Overview */}
              <div className="grid grid-cols-2 gap-3 p-4 rounded-2xl bg-muted/40 border border-border text-xs">
                <div>
                  <span className="text-muted-foreground block text-[11px]">Reporting Institution</span>
                  <span className="font-bold text-primary block mt-0.5">
                    {selectedCase.institution_name || selectedCase.institution_id}
                  </span>
                </div>
                <div>
                  <span className="text-muted-foreground block text-[11px]">Conflicting Institution</span>
                  <span className="font-bold text-destructive block mt-0.5">
                    {selectedCase.clash_institution_name || "AKTU Lucknow (AKTU)"}
                  </span>
                </div>
              </div>

              {/* Description & Evidence */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-muted-foreground uppercase">Violation Summary</h4>
                <div className="p-4 rounded-xl bg-background border border-border text-xs leading-relaxed">
                  {selectedCase.description}
                </div>
              </div>

              {/* Drafted Sentinel Notice */}
              {selectedCase.action_draft && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-muted-foreground uppercase flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-amber-500" />
                    <span>Sentinel Drafted Formal Notice</span>
                  </h4>
                  <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs font-mono leading-relaxed text-amber-900 dark:text-amber-200">
                    {selectedCase.action_draft}
                  </div>
                </div>
              )}

              {/* Officer Resolution Workspace */}
              <div className="space-y-3 pt-2 border-t border-border">
                <h4 className="text-xs font-bold uppercase text-muted-foreground">Officer Decision & Action</h4>
                <textarea
                  rows={2}
                  value={resolutionNote}
                  onChange={(e) => setResolutionNote(e.target.value)}
                  placeholder="Enter resolution notes, verification outcome, or sanction details..."
                  className="w-full p-3 rounded-xl border border-input bg-background text-xs focus:ring-2 focus:ring-primary/40 focus:outline-none"
                />

                <div className="flex items-center justify-end gap-3">
                  <button
                    onClick={() => handleResolveCase(selectedCase.id, "ESCALATED")}
                    className="px-4 py-2 rounded-xl border border-amber-500/30 text-amber-600 dark:text-amber-400 text-xs font-bold hover:bg-amber-500/10 transition-colors"
                  >
                    Escalate to Regional Officer
                  </button>
                  <button
                    onClick={() => handleResolveCase(selectedCase.id, "RESOLVED")}
                    className="px-5 py-2 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 shadow transition-all flex items-center gap-2"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Approve Resolution & Close</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="p-12 rounded-3xl bg-card border border-border text-center text-xs text-muted-foreground">
              Select a case from the queue to view evidence and take action.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
