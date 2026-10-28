"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Bot,
  Play,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Terminal,
  Wrench,
  ShieldCheck,
  Scale,
  MessageSquare,
  Send,
  RefreshCw,
  FileText,
  ChevronRight,
  Clock,
  ArrowRight,
  Lock,
  Unlock,
  Sparkles,
  Cpu,
  Layers,
  ExternalLink,
  UserCheck,
  ThumbsUp,
  ThumbsDown,
  Info,
  Check,
  AlertCircle,
} from "lucide-react";
import {
  sentinelApi,
  SentinelBatchItem,
  SentinelTriageResult,
  SentinelThought,
  SentinelToolExecution,
  PendingApprovalItem,
  SentinelChatMessage,
} from "@/lib/api";

type TabMode = "triage" | "approvals" | "chat" | "tools";

export default function SentinelPage() {
  const [activeTab, setActiveTab] = useState<TabMode>("triage");

  // Batches for Triage
  const [batches, setBatches] = useState<SentinelBatchItem[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<string>("");
  const [isTriaging, setIsTriaging] = useState(false);
  const [triageResult, setTriageResult] = useState<SentinelTriageResult | null>(null);
  const [triageError, setTriageError] = useState<string | null>(null);
  const [selectedToolExecution, setSelectedToolExecution] = useState<SentinelToolExecution | null>(null);

  // Human Approvals
  const [approvals, setApprovals] = useState<PendingApprovalItem[]>([]);
  const [loadingApprovals, setLoadingApprovals] = useState(false);
  const [decidingId, setDecidingId] = useState<string | null>(null);
  const [officerNotes, setOfficerNotes] = useState<Record<string, string>>({});
  const [approvalFeedback, setApprovalFeedback] = useState<string | null>(null);

  // Chat Copilot
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<
    Array<{ sender: "user" | "sentinel"; text: string; tools?: string[]; links?: Array<{ label: string; href: string }> }>
  >([
    {
      sender: "sentinel",
      text: "Namaste! I am **Sentinel**, the AICTE Autonomous Verification & Compliance Agent. I continuously verify APAAR ID cohorts, detect ghost student anomalies via Isolation Forest, catch cross-institution duplicate registrations with RapidFuzz, and project seat capacity limits.\n\nHow may I assist you today? You can choose a suggested query below or ask directly.",
      tools: [],
      links: [
        { label: "Run Batch Triage", href: "#triage" },
        { label: "View ML Radar", href: "/intelligence" },
      ],
    },
  ]);
  const [isSendingChat, setIsSendingChat] = useState(false);
  const chatScrollRef = useRef<HTMLDivElement>(null);

  // Load initial data
  useEffect(() => {
    loadBatches();
    loadApprovals();
  }, []);

  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight;
    }
  }, [chatMessages]);

  const loadBatches = async () => {
    try {
      const data = await sentinelApi.getBatches(20);
      setBatches(data);
      if (data.length > 0 && !selectedBatchId) {
        setSelectedBatchId(data[0].id);
      }
    } catch (e: any) {
      console.error("Failed to load batches:", e);
    }
  };

  const loadApprovals = async () => {
    setLoadingApprovals(true);
    try {
      const data = await sentinelApi.getPendingApprovals();
      setApprovals(data);
    } catch (e: any) {
      console.error("Failed to load approvals:", e);
    } finally {
      setLoadingApprovals(false);
    }
  };

  const handleRunTriage = async () => {
    if (!selectedBatchId) return;
    setIsTriaging(true);
    setTriageError(null);
    setTriageResult(null);
    setSelectedToolExecution(null);

    try {
      const result = await sentinelApi.triageBatch(selectedBatchId);
      setTriageResult(result);
      if (result.tool_executions && result.tool_executions.length > 0) {
        setSelectedToolExecution(result.tool_executions[0]);
      }
      // Reload approvals list in case a new human approval was staged
      loadApprovals();
    } catch (e: any) {
      setTriageError(e.message || "Failed to execute autonomous triage");
    } finally {
      setIsTriaging(false);
    }
  };

  const handleDecideApproval = async (caseId: string, decision: "APPROVE" | "REJECT") => {
    setDecidingId(caseId);
    setApprovalFeedback(null);
    try {
      const notes = officerNotes[caseId] || "";
      const res = await sentinelApi.decideApproval(caseId, decision, notes);
      setApprovalFeedback(
        `${decision === "APPROVE" ? "✅ Approved" : "❌ Rejected"}: ${res.case_number} — ${res.message}`
      );
      await loadApprovals();
    } catch (e: any) {
      setApprovalFeedback(`Error: ${e.message || "Could not record decision"}`);
    } finally {
      setDecidingId(null);
    }
  };

  const handleSendChat = async (promptToSend?: string) => {
    const text = promptToSend || chatInput;
    if (!text.trim() || isSendingChat) return;

    const userMsg = text.trim();
    setChatInput("");
    setChatMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setIsSendingChat(true);

    try {
      const resp: SentinelChatMessage = await sentinelApi.chat(userMsg);
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "sentinel",
          text: resp.answer,
          tools: resp.tools_called,
          links: resp.related_links,
        },
      ]);
    } catch (e: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: "sentinel",
          text: `⚠️ Error executing query: ${e.message || "Could not reach Sentinel Agent."}`,
        },
      ]);
    } finally {
      setIsSendingChat(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header Banner */}
        <div className="relative overflow-hidden rounded-2xl border border-pink-500/30 bg-gradient-to-r from-purple-950/70 via-slate-900/90 to-pink-950/70 p-6 sm:p-8 shadow-2xl">
          <div className="absolute -right-16 -top-16 w-64 h-64 bg-pink-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="relative flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-pink-500/20 border border-pink-500/40 text-pink-400">
                  <Bot className="w-8 h-8 animate-pulse" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-300 bg-clip-text text-transparent">
                      AICTE Sentinel AI Agent
                    </h1>
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-pink-500/20 text-pink-300 border border-pink-500/40">
                      Phase 6
                    </span>
                  </div>
                  <p className="text-xs sm:text-sm text-slate-400">
                    Claude-Compatible Autonomous Multi-Step Triage • Typed Tool Execution • Human-in-the-Loop Governance
                  </p>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                <span>Agent Loop Active</span>
              </div>
              <button
                onClick={() => {
                  loadBatches();
                  loadApprovals();
                }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-medium transition-colors"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh Desk</span>
              </button>
            </div>
          </div>

          {/* Navigation Mode Tabs */}
          <div className="mt-8 flex flex-wrap gap-2 border-t border-slate-800/80 pt-4">
            <button
              onClick={() => setActiveTab("triage")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "triage"
                  ? "bg-pink-600 text-white shadow-lg shadow-pink-600/30 border border-pink-400"
                  : "bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              <Terminal className="w-4 h-4" />
              <span>Autonomous Triage Workspace</span>
            </button>

            <button
              onClick={() => setActiveTab("approvals")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all relative cursor-pointer ${
                activeTab === "approvals"
                  ? "bg-pink-600 text-white shadow-lg shadow-pink-600/30 border border-pink-400"
                  : "bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              <Scale className="w-4 h-4" />
              <span>Human Approval Desk</span>
              {approvals.length > 0 && (
                <span className="px-1.5 py-0.2 rounded-full bg-amber-500 text-slate-950 text-[10px] font-black">
                  {approvals.length}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab("chat")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "chat"
                  ? "bg-pink-600 text-white shadow-lg shadow-pink-600/30 border border-pink-400"
                  : "bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              <MessageSquare className="w-4 h-4" />
              <span>Ask Sentinel (Copilot)</span>
            </button>

            <button
              onClick={() => setActiveTab("tools")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs sm:text-sm font-semibold transition-all cursor-pointer ${
                activeTab === "tools"
                  ? "bg-pink-600 text-white shadow-lg shadow-pink-600/30 border border-pink-400"
                  : "bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              <Wrench className="w-4 h-4" />
              <span>Typed Tool Registry (10 Tools)</span>
            </button>
          </div>
        </div>

        {/* TAB 1: AUTONOMOUS TRIAGE WORKSPACE */}
        {activeTab === "triage" && (
          <div className="space-y-6">
            {/* Control Bar */}
            <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="space-y-1">
                  <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    <Terminal className="w-5 h-5 text-pink-400" />
                    <span>Autonomous Triage Execution Engine</span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Sentinel autonomously runs: Ingest batch → Verify rules → Query ML detector → Match duplicates → Trigger SLA case or draft sanction.
                  </p>
                </div>

                <div className="flex flex-wrap items-center gap-3 w-full sm:w-auto">
                  <select
                    value={selectedBatchId}
                    onChange={(e) => setSelectedBatchId(e.target.value)}
                    className="flex-1 sm:w-72 px-3 py-2 rounded-xl bg-slate-950 border border-slate-700 text-xs font-medium text-slate-200 focus:outline-none focus:border-pink-500"
                  >
                    {batches.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.institution_name} ({b.total_records} records, {b.flagged_records} flags)
                      </option>
                    ))}
                  </select>

                  <button
                    onClick={handleRunTriage}
                    disabled={isTriaging || !selectedBatchId}
                    className="flex items-center gap-2 px-5 py-2 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white text-xs font-bold shadow-lg shadow-pink-600/30 disabled:opacity-50 transition-all cursor-pointer"
                  >
                    {isTriaging ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Sentinel Triaging...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4 fill-white" />
                        <span>Run Sentinel Triage</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {triageError && (
              <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-500/40 text-rose-300 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>{triageError}</span>
              </div>
            )}

            {/* Results Grid */}
            {triageResult && (
              <div className="space-y-6">
                {/* Executive Summary Card */}
                <div
                  className={`p-6 rounded-2xl border shadow-xl ${
                    triageResult.status === "ESCALATED_HUMAN_APPROVAL"
                      ? "bg-amber-950/30 border-amber-500/40"
                      : triageResult.status === "COMPLIANCE_NOTICE_SENT"
                      ? "bg-sky-950/30 border-sky-500/40"
                      : "bg-emerald-950/30 border-emerald-500/40"
                  }`}
                >
                  <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-xs uppercase font-extrabold tracking-wider text-slate-400">
                          Triage Verdict
                        </span>
                        <span
                          className={`text-xs px-2.5 py-0.5 rounded-full font-bold ${
                            triageResult.status === "ESCALATED_HUMAN_APPROVAL"
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                              : triageResult.status === "COMPLIANCE_NOTICE_SENT"
                              ? "bg-sky-500/20 text-sky-300 border border-sky-500/40"
                              : "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          }`}
                        >
                          {triageResult.status.replace(/_/g, " ")}
                        </span>
                      </div>
                      <h3 className="text-lg font-bold text-slate-100">{triageResult.institution_name}</h3>
                      <p className="text-sm text-slate-300 max-w-3xl leading-relaxed">
                        {triageResult.executive_summary}
                      </p>
                    </div>

                    {triageResult.status === "ESCALATED_HUMAN_APPROVAL" && (
                      <button
                        onClick={() => setActiveTab("approvals")}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs shadow-md transition-colors cursor-pointer"
                      >
                        <Scale className="w-4 h-4" />
                        <span>Review at Approvals Desk</span>
                      </button>
                    )}
                  </div>
                </div>

                {/* 2-Column Split: Reasoning Log + Tool Executions Drawer */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Step-by-Step Reasoning Timeline */}
                  <div className="lg:col-span-6 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
                    <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <Bot className="w-4 h-4 text-pink-400" />
                      <span>Autonomous Reasoning Timeline ({triageResult.thought_log.length} Steps)</span>
                    </h4>

                    <div className="space-y-3 max-h-[480px] overflow-y-auto pr-2">
                      {triageResult.thought_log.map((t, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-3 p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs"
                        >
                          <div
                            className={`mt-0.5 px-2 py-0.5 rounded font-black text-[10px] tracking-wider ${
                              t.phase === "PLAN"
                                ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                                : t.phase === "INVESTIGATE"
                                ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                                : t.phase === "ACTION"
                                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                                : t.phase === "COMPLETE"
                                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                                : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            }`}
                          >
                            {t.phase}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="text-[10px] text-slate-500 font-mono">{t.timestamp} UTC</div>
                            <p className="text-slate-300 leading-relaxed font-mono">{t.message}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tool Execution Drawer */}
                  <div className="lg:col-span-6 p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
                    <h4 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                      <Wrench className="w-4 h-4 text-purple-400" />
                      <span>Typed Tools Executed ({triageResult.tool_executions.length})</span>
                    </h4>

                    {/* Tool Badges */}
                    <div className="flex flex-wrap gap-2">
                      {triageResult.tool_executions.map((te, idx) => (
                        <button
                          key={idx}
                          onClick={() => setSelectedToolExecution(te)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono transition-all cursor-pointer ${
                            selectedToolExecution?.tool_name === te.tool_name
                              ? "bg-purple-600 text-white border border-purple-400 font-bold"
                              : "bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800"
                          }`}
                        >
                          <Cpu className="w-3.5 h-3.5 text-purple-400" />
                          <span>{te.tool_name}()</span>
                        </button>
                      ))}
                    </div>

                    {/* Selected Tool Details */}
                    {selectedToolExecution && (
                      <div className="space-y-3 pt-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-mono text-pink-400 font-bold">
                            Tool: {selectedToolExecution.tool_name}()
                          </span>
                          <span className="text-slate-500 text-[11px]">JSON-RPC Payload</span>
                        </div>

                        <div className="space-y-2">
                          <span className="text-[11px] font-semibold text-slate-400">Input Arguments:</span>
                          <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-32">
                            {JSON.stringify(selectedToolExecution.input, null, 2)}
                          </pre>
                        </div>

                        <div className="space-y-2">
                          <span className="text-[11px] font-semibold text-slate-400">Tool Output:</span>
                          <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-48">
                            {JSON.stringify(selectedToolExecution.output, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 2: HUMAN APPROVAL DESK */}
        {activeTab === "approvals" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-2 shadow-xl">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                    <Scale className="w-5 h-5 text-amber-400" />
                    <span>AICTE Regional Officer — Human-in-the-Loop Sanction Desk</span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    High-stakes sanctions (intake seat freeze, dual-college cancellation, legal notices) are drafted by Sentinel and paused here for mandatory human officer sign-off.
                  </p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                  {approvals.length} Pending Actions
                </span>
              </div>
            </div>

            {approvalFeedback && (
              <div className="p-4 rounded-xl bg-slate-900 border border-emerald-500/40 text-emerald-300 text-xs flex items-center gap-2 shadow-lg">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span>{approvalFeedback}</span>
              </div>
            )}

            {loadingApprovals ? (
              <div className="p-12 text-center text-slate-500 text-xs flex flex-col items-center gap-3">
                <RefreshCw className="w-6 h-6 animate-spin text-pink-500" />
                <span>Loading pending sanction cases...</span>
              </div>
            ) : approvals.length === 0 ? (
              <div className="p-12 rounded-2xl bg-slate-900/60 border border-slate-800 text-center space-y-3">
                <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto" />
                <h3 className="text-base font-bold text-slate-200">No Pending Sanctions</h3>
                <p className="text-xs text-slate-400 max-w-md mx-auto">
                  All drafted sanctions have been reviewed or resolved. You can run an autonomous triage in the Triage Workspace to analyze more batches.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-6">
                {approvals.map((appr) => (
                  <div
                    key={appr.case_id}
                    className="p-6 rounded-2xl bg-slate-900/90 border border-amber-500/40 space-y-4 shadow-xl"
                  >
                    <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="px-2.5 py-0.5 rounded font-mono font-bold text-[11px] bg-slate-800 text-amber-400 border border-slate-700">
                            {appr.case_number}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-wider bg-rose-500/20 text-rose-400 border border-rose-500/30">
                            {appr.priority}
                          </span>
                          <span className="text-[11px] text-slate-500 font-mono">
                            SLA Deadline: {appr.sla_deadline ? new Date(appr.sla_deadline).toLocaleString() : "24 Hours"}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-slate-100">{appr.title}</h3>
                      </div>

                      <div className="flex items-center gap-2 text-xs text-slate-400">
                        <Clock className="w-4 h-4 text-amber-400" />
                        <span>Created {new Date(appr.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>

                    {/* Proposed Action Draft */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                      <div className="text-[11px] font-extrabold uppercase tracking-wider text-pink-400 flex items-center gap-1.5">
                        <Bot className="w-3.5 h-3.5" />
                        <span>Sentinel Drafted Action:</span>
                      </div>
                      <p className="text-xs text-slate-200 leading-relaxed font-medium">{appr.proposed_action}</p>
                      <p className="text-xs text-slate-400 italic">Justification: {appr.description}</p>
                    </div>

                    {/* Officer Notes & Decision Buttons */}
                    <div className="flex flex-col sm:flex-row items-center gap-4 pt-2">
                      <input
                        type="text"
                        placeholder="Optional officer compliance note (recorded into SHA-256 ledger)..."
                        value={officerNotes[appr.case_id] || ""}
                        onChange={(e) =>
                          setOfficerNotes((prev) => ({
                            ...prev,
                            [appr.case_id]: e.target.value,
                          }))
                        }
                        className="flex-1 w-full px-3.5 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-pink-500"
                      />

                      <div className="flex items-center gap-2 w-full sm:w-auto">
                        <button
                          onClick={() => handleDecideApproval(appr.case_id, "APPROVE")}
                          disabled={decidingId === appr.case_id}
                          className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all cursor-pointer disabled:opacity-50"
                        >
                          <ThumbsUp className="w-3.5 h-3.5" />
                          <span>Approve & Execute</span>
                        </button>

                        <button
                          onClick={() => handleDecideApproval(appr.case_id, "REJECT")}
                          disabled={decidingId === appr.case_id}
                          className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-5 py-2 rounded-xl bg-slate-800 hover:bg-rose-950 hover:text-rose-300 text-slate-300 border border-slate-700 hover:border-rose-700/50 font-bold text-xs transition-all cursor-pointer disabled:opacity-50"
                        >
                          <ThumbsDown className="w-3.5 h-3.5" />
                          <span>Dismiss / Reject</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ASK SENTINEL (CONVERSATIONAL ASSISTANT) */}
        {activeTab === "chat" && (
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="space-y-1">
                <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                  <Bot className="w-5 h-5 text-pink-400" />
                  <span>Ask Sentinel — AICTE Natural Language Copilot</span>
                </h2>
                <p className="text-xs text-slate-400">
                  Ask conversational questions about ghost student detections, branch seat saturation, duplicate clashes, and trust score formulas.
                </p>
              </div>
            </div>

            {/* Quick Prompts Bar */}
            <div className="flex flex-wrap gap-2 pt-1">
              {[
                "Why was Balaji College flagged by the system?",
                "Which colleges are breaching approved seat capacity?",
                "Show me duplicate student cases across colleges",
                "Explain how the Institution Trust Score is calculated",
              ].map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendChat(qp)}
                  className="px-3 py-1.5 rounded-lg bg-slate-950 hover:bg-pink-950/40 border border-slate-800 hover:border-pink-500/40 text-slate-300 hover:text-pink-300 text-[11px] font-medium transition-all text-left cursor-pointer"
                >
                  💬 {qp}
                </button>
              ))}
            </div>

            {/* Chat Messages Log */}
            <div
              ref={chatScrollRef}
              className="p-4 rounded-xl bg-slate-950 border border-slate-800 min-h-[380px] max-h-[500px] overflow-y-auto space-y-4"
            >
              {chatMessages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${
                    msg.sender === "user" ? "justify-end" : "justify-start"
                  }`}
                >
                  {msg.sender === "sentinel" && (
                    <div className="w-8 h-8 rounded-lg bg-pink-500/20 border border-pink-500/40 flex items-center justify-center shrink-0 text-pink-400">
                      <Bot className="w-4 h-4" />
                    </div>
                  )}

                  <div
                    className={`max-w-2xl rounded-2xl p-4 text-xs leading-relaxed space-y-3 ${
                      msg.sender === "user"
                        ? "bg-purple-600 text-white rounded-tr-none font-medium"
                        : "bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none"
                    }`}
                  >
                    <div className="whitespace-pre-wrap font-sans">{msg.text}</div>

                    {/* Tool Badges */}
                    {msg.tools && msg.tools.length > 0 && (
                      <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-slate-800">
                        <span className="text-[10px] text-slate-500 font-mono">Tools invoked:</span>
                        {msg.tools.map((t, tidx) => (
                          <span
                            key={tidx}
                            className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-500/20 text-purple-300 border border-purple-500/30"
                          >
                            ⚙️ {t}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Related Action Links */}
                    {msg.links && msg.links.length > 0 && (
                      <div className="flex flex-wrap gap-2 pt-2">
                        {msg.links.map((l, lidx) => (
                          <Link
                            key={lidx}
                            href={l.href}
                            className="flex items-center gap-1 text-[11px] font-bold text-pink-400 hover:text-pink-300 underline"
                          >
                            <span>{l.label}</span>
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>

                  {msg.sender === "user" && (
                    <div className="w-8 h-8 rounded-lg bg-purple-600 flex items-center justify-center shrink-0 text-white font-bold text-xs">
                      YOU
                    </div>
                  )}
                </div>
              ))}

              {isSendingChat && (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-pink-500/20 border border-pink-500/40 flex items-center justify-center text-pink-400">
                    <Bot className="w-4 h-4 animate-spin" />
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-pink-400 animate-ping" />
                    <span>Sentinel is analyzing repository data...</span>
                  </div>
                </div>
              )}
            </div>

            {/* Input Bar */}
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Ask Sentinel any question about APAAR cohorts, anomalies, or compliance rules..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSendChat()}
                className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-pink-500"
              />
              <button
                onClick={() => handleSendChat()}
                disabled={isSendingChat || !chatInput.trim()}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white font-bold text-xs disabled:opacity-50 transition-all cursor-pointer shadow-lg shadow-pink-600/30"
              >
                <Send className="w-4 h-4" />
                <span>Send</span>
              </button>
            </div>
          </div>
        )}

        {/* TAB 4: TYPED TOOL REGISTRY */}
        {activeTab === "tools" && (
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-6 shadow-xl">
            <div className="space-y-1">
              <h2 className="text-lg font-bold text-slate-200 flex items-center gap-2">
                <Wrench className="w-5 h-5 text-purple-400" />
                <span>Claude-Compatible Typed Tool Specification (Anthropic JSON Schema)</span>
              </h2>
              <p className="text-xs text-slate-400">
                Sentinel uses standard Anthropic Tool Use schemas. Each tool executes strictly validated backend functions with cryptographic audit tracking.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[
                {
                  name: "fetch_upload_batch",
                  desc: "Fetches metadata, student count, and processing status of an uploaded student batch.",
                  args: "{ batch_id: string }",
                  output: "UploadBatch record with valid & flagged counts",
                  auth: "AICTE Officer / Institution Admin",
                },
                {
                  name: "run_validation",
                  desc: "Executes rule validation engine across format, duplicates, capacity, and clashes.",
                  args: "{ batch_id: string }",
                  output: "Rule summary with error grid entries",
                  auth: "Autonomous Engine",
                },
                {
                  name: "get_flags",
                  desc: "Retrieves granular validation flags with recommended auto-remediation actions.",
                  args: "{ batch_id?: string, severity?: string }",
                  output: "ValidationFlag array with suggested fixes",
                  auth: "Autonomous Engine",
                },
                {
                  name: "fuzzy_match_students",
                  desc: "Runs RapidFuzz Levenshtein token matching across institutions to detect duplicate identities.",
                  args: "{ similarity_threshold: number, limit: number }",
                  output: "Candidate duplicate pairs with confidence score",
                  auth: "AICTE Central Vigilance",
                },
                {
                  name: "check_cross_institution_status",
                  desc: "Determines if a student's APAAR ID is concurrently registered at multiple institutions.",
                  args: "{ apaar_id: string }",
                  output: "Multi-college enrolment history & clash flag",
                  auth: "Verification Engine",
                },
                {
                  name: "forecast_seats",
                  desc: "Projects seat capacity exhaustion using admission velocity forecasting.",
                  args: "{ institution_id: string, days_remaining: number }",
                  output: "Projected quota saturation & branch lock state",
                  auth: "Intake Controller",
                },
                {
                  name: "open_case",
                  desc: "Creates a formal AICTE compliance case with 48-hour resolution SLA.",
                  args: "{ title: string, institution_id: string, priority: string, description: string }",
                  output: "Registered Case with SHA-256 ledger block",
                  auth: "Sentinel Agent",
                },
                {
                  name: "notify_institution",
                  desc: "Dispatches simulated AICTE compliance notice to institution's official contact.",
                  args: "{ institution_id: string, subject: string, message: string }",
                  output: "Delivery receipt & audit anchor",
                  auth: "Sentinel Agent",
                },
                {
                  name: "request_human_approval",
                  desc: "Submits high-stakes sanction (seat freeze, enrolment cancellation) for Regional Officer sign-off.",
                  args: "{ action_type: string, institution_id: string, proposed_action: string, reason: string }",
                  output: "Pending Approval Case with 24h SLA",
                  auth: "Human-in-the-Loop Gateway",
                },
                {
                  name: "write_audit_entry",
                  desc: "Appends an immutable SHA-256 chained entry into the cryptographic audit trail.",
                  args: "{ action: string, entity_type: string, entity_id: string, details: object }",
                  output: "Block sequence number & current hash",
                  auth: "Cryptographic Ledger",
                },
              ].map((tool, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 hover:border-purple-500/40 transition-colors"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-pink-400">
                      ⚙️ {tool.name}()
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 font-mono">
                      {tool.auth}
                    </span>
                  </div>
                  <p className="text-xs text-slate-300">{tool.desc}</p>
                  <div className="space-y-1 pt-1 text-[11px] font-mono">
                    <div className="text-slate-500">Args: <span className="text-slate-300">{tool.args}</span></div>
                    <div className="text-slate-500">Returns: <span className="text-emerald-400">{tool.output}</span></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
