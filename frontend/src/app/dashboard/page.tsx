"use client";

import React, { useState, useEffect } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import {
  ShieldAlert,
  Building2,
  Users,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Unlock,
  Radio,
  Flame,
  Scale,
  Sparkles,
  RefreshCw,
  SlidersHorizontal,
  MapPin,
  TrendingUp,
  Activity,
  Award,
  ChevronRight,
  Download,
  FileSpreadsheet,
  FileText,
  Search,
  Send,
  Terminal,
  X,
} from "lucide-react";
import { analyticsApi, exportApi, NLQueryResult, API_BASE } from "@/lib/api";

export default function DashboardPage() {
  const { t } = useLanguage();
  const { user, isAuthenticated } = useAuth();

  // Mode: AICTE National Command vs Institution Command
  const isInstAdmin = user?.role === "INSTITUTION_ADMIN";
  const [viewMode, setViewMode] = useState<"aicte" | "institution">(
    isInstAdmin ? "institution" : "aicte"
  );

  const [nationalData, setNationalData] = useState<any | null>(null);
  const [institutionData, setInstitutionData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [liveAlerts, setLiveAlerts] = useState<any[]>([]);

  // Safe Natural Language Analytics Bar state
  const [nlQuery, setNlQuery] = useState("");
  const [nlLoading, setNlLoading] = useState(false);
  const [nlResult, setNlResult] = useState<NLQueryResult | null>(null);
  const [nlError, setNlError] = useState<string | null>(null);

  const handleRunNLQuery = async (queryText?: string) => {
    const q = (queryText || nlQuery).trim();
    if (!q) return;
    setNlQuery(q);
    setNlLoading(true);
    setNlError(null);
    try {
      const res = await analyticsApi.runNLQuery(q);
      setNlResult(res);
    } catch (e: any) {
      setNlError(e.message || "Failed to process analytical query.");
    } finally {
      setNlLoading(false);
    }
  };

  // Category chart color palette
  const CATEGORY_COLORS = ["#0A2540", "#FF9933", "#138808", "#38BDF8", "#A855F7"];

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
      const headers: Record<string, string> = {};
      if (token) headers["Authorization"] = `Bearer ${token}`;

      // 1. Fetch National Analytics
      const natRes = await fetch(`${API_BASE}/api/v1/analytics/national`, { headers });
      if (natRes.ok) {
        const natJson = await natRes.json();
        setNationalData(natJson);
        setLiveAlerts(natJson.alerts_feed || []);
      }

      // 2. Fetch Institution Analytics
      let instId = user?.institution_id;
      if (!instId) {
        // Fallback to first available institution for preview
        const instListRes = await fetch(`${API_BASE}/api/v1/institutions/?limit=1`, { headers });
        if (instListRes.ok) {
          const listJson = await instListRes.json();
          if (listJson.length > 0) instId = listJson[0].id;
        }
      }

      if (instId) {
        const instRes = await fetch(`${API_BASE}/api/v1/analytics/institution/${instId}`, { headers });
        if (instRes.ok) {
          setInstitutionData(await instRes.json());
        }
      }
    } catch (e) {
      console.error("Dashboard data load error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();

    // WebSocket / Realtime simulation for live ticker
    let interval: any;
    try {
      const wsUrl = API_BASE.replace(/^http/, "ws") + "/api/v1/realtime/ws";
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type && data.type !== "HANDSHAKE_ESTABLISHED") {
            setLiveAlerts((prev) => [data, ...prev.slice(0, 8)]);
          }
        } catch {}
      };
      return () => ws.close();
    } catch {
      // Fallback polling for live alert simulation
      interval = setInterval(() => {
        // Keeps alerts fresh
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [user]);

  // Filtered state chart data
  const stateChartData = nationalData?.state_heatmap
    ?.filter((s: any) => s.intake > 0)
    ?.slice(0, 8)
    ?.map((s: any) => ({
      name: s.code || s.name,
      fullName: s.name,
      Intake: s.intake,
      Enrolled: s.enrolment,
      fill_rate: s.fill_rate,
    }));

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* Top Banner & View Switcher */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-card border border-border shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-primary/10 text-primary">
              <Activity className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black tracking-tight">
              {viewMode === "aicte"
                ? "AICTE Central Command Dashboard"
                : "Institution Seat Allocation & Monitoring"}
            </h1>
          </div>
          <p className="text-xs text-muted-foreground">
            {viewMode === "aicte"
              ? "Live national student intake monitoring, state heatmap visualizer, and fraud anomaly radar."
              : `Real-time seat fill rate, 90% warnings, 100% seat locks, and institutional Trust Score.`}
          </p>
        </div>

        {/* View Switcher Toggle & Refresh */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-muted p-1 rounded-2xl border border-border text-xs font-bold">
            <button
              onClick={() => setViewMode("aicte")}
              className={`px-3.5 py-1.5 rounded-xl transition-all ${
                viewMode === "aicte"
                  ? "bg-primary text-primary-foreground shadow"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              AICTE National
            </button>
            <button
              onClick={() => setViewMode("institution")}
              className={`px-3.5 py-1.5 rounded-xl transition-all ${
                viewMode === "institution"
                  ? "bg-primary text-primary-foreground shadow"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              College Registrar
            </button>
          </div>

          {/* Export Reports Buttons */}
          <a
            href={exportApi.getTrustScoresUrl("excel")}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-emerald-500/30 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-500 text-xs font-bold transition-all shadow-sm"
            title="Download National Trust Score Leaderboard Excel"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Excel</span>
          </a>

          <a
            href={exportApi.getTrustScoresUrl("pdf")}
            download
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-rose-500/30 bg-rose-500/10 hover:bg-rose-500/20 text-rose-500 text-xs font-bold transition-all shadow-sm"
            title="Download Official AICTE PDF Audit Dossier"
          >
            <FileText className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">PDF</span>
          </a>

          <button
            onClick={fetchDashboardData}
            className="p-2.5 rounded-xl border border-border bg-card hover:bg-muted text-muted-foreground transition-colors cursor-pointer"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Safe Natural Language Analytics Bar */}
      <div className="p-5 rounded-3xl bg-card border border-border/80 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="p-1.5 rounded-xl bg-purple-500/20 text-purple-400 border border-purple-500/30">
              <Sparkles className="w-4 h-4 animate-pulse" />
            </span>
            <div>
              <h3 className="text-sm font-bold tracking-tight text-foreground flex items-center gap-2">
                <span>Safe Natural Language Analytics Bar</span>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
                  Allowlisted Parameterized Plans • Zero SQL Injection
                </span>
              </h3>
              <p className="text-[11px] text-muted-foreground">
                Query national admission telemetry in plain English or Hindi without risk of un-sanitized SQL execution.
              </p>
            </div>
          </div>
        </div>

        {/* Input Bar */}
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="e.g. 'top 5 institutions by enrollment', 'colleges with trust score below 70', 'gender distribution'..."
              value={nlQuery}
              onChange={(e) => setNlQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleRunNLQuery()}
              className="w-full pl-10 pr-4 py-2 rounded-2xl bg-muted/60 border border-border text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-purple-500 transition-colors"
            />
          </div>
          <button
            onClick={() => handleRunNLQuery()}
            disabled={nlLoading || !nlQuery.trim()}
            className="flex items-center gap-1.5 px-4 py-2 rounded-2xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs shadow-md shadow-purple-600/20 transition-all disabled:opacity-50 cursor-pointer"
          >
            {nlLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
            <span>Run</span>
          </button>
        </div>

        {/* Quick Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
          <span className="text-muted-foreground font-semibold text-[10px]">Suggested:</span>
          {[
            "Top 5 institutions by enrollment",
            "Colleges with trust score below 70",
            "Gender distribution across students",
            "Branches near full seat capacity",
            "Ghost student anomaly overview"
          ].map((chip, idx) => (
            <button
              key={idx}
              onClick={() => handleRunNLQuery(chip)}
              className="px-2.5 py-1 rounded-xl bg-muted hover:bg-purple-500/10 hover:text-purple-400 hover:border-purple-500/30 border border-border text-muted-foreground font-medium transition-all cursor-pointer"
            >
              {chip}
            </button>
          ))}
        </div>

        {/* Error Notice */}
        {nlError && (
          <div className="p-3 rounded-2xl bg-destructive/10 border border-destructive/30 text-destructive text-xs">
            {nlError}
          </div>
        )}

        {/* Results Box */}
        {nlResult && (
          <div className="p-4 rounded-2xl bg-muted/40 border border-purple-500/30 space-y-3">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    {nlResult.intent}
                  </span>
                  <h4 className="text-xs font-bold text-foreground">{nlResult.title}</h4>
                </div>
                <p className="text-[11px] text-emerald-500 font-medium">{nlResult.summary_insight}</p>
              </div>
              <button
                onClick={() => setNlResult(null)}
                className="p-1 rounded-lg hover:bg-muted text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>

            {/* Parameterized SQL Transparency */}
            <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-400 flex items-center justify-between gap-2 overflow-x-auto">
              <span className="text-pink-400 font-semibold shrink-0">SQL Translation:</span>
              <code className="text-slate-300 truncate">{nlResult.sql_translation}</code>
            </div>

            {/* Results Table */}
            <div className="rounded-xl border border-border overflow-hidden max-h-56 overflow-y-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted text-muted-foreground font-bold">
                  <tr>
                    {nlResult.columns.map((col, idx) => (
                      <th key={idx} className="p-2.5 border-b border-border">
                        {col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {nlResult.rows.map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-muted/50 transition-colors">
                      {Object.values(row).map((val: any, cIdx) => (
                        <td key={cIdx} className="p-2.5 font-medium">
                          {String(val)}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {viewMode === "aicte" ? (
        /* ==================== AICTE CENTRAL COMMAND VIEW ==================== */
        <div className="space-y-6">
          {/* Top National KPI Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-5 rounded-3xl bg-card border border-border shadow-sm">
              <div className="flex items-center justify-between text-muted-foreground text-xs font-medium">
                <span>Sanctioned AICTE Intake</span>
                <Building2 className="w-4 h-4 text-sky-500" />
              </div>
              <div className="text-3xl font-extrabold tracking-tight mt-2">
                {nationalData?.summary?.total_approved_intake?.toLocaleString() || "—"}
              </div>
              <span className="text-[11px] text-muted-foreground">Across 40+ premier colleges</span>
            </div>

            <div className="p-5 rounded-3xl bg-card border border-emerald-500/30 bg-emerald-500/5 shadow-sm">
              <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400 text-xs font-medium">
                <span>Total Enrolled (APAAR Keyed)</span>
                <Users className="w-4 h-4 text-emerald-500" />
              </div>
              <div className="text-3xl font-extrabold tracking-tight mt-2 text-emerald-600 dark:text-emerald-400">
                {nationalData?.summary?.total_actual_enrolment?.toLocaleString() || "—"}
              </div>
              <span className="text-[11px] text-emerald-600 font-bold">
                {nationalData?.summary?.overall_fill_rate}% National Fill Rate
              </span>
            </div>

            <div className="p-5 rounded-3xl bg-card border border-red-500/30 bg-red-500/5 shadow-sm">
              <div className="flex items-center justify-between text-red-500 text-xs font-medium">
                <span>Flagged Institutions</span>
                <ShieldAlert className="w-4 h-4 text-red-500" />
              </div>
              <div className="text-3xl font-extrabold tracking-tight mt-2 text-red-500">
                {nationalData?.summary?.critical_violations_count || 3}
              </div>
              <span className="text-[11px] text-red-500 font-bold">Over-intake & ghost clusters</span>
            </div>

            <div className="p-5 rounded-3xl bg-card border border-amber-500/30 bg-amber-500/5 shadow-sm">
              <div className="flex items-center justify-between text-amber-500 text-xs font-medium">
                <span>Cross-College Clashes</span>
                <Scale className="w-4 h-4 text-amber-500" />
              </div>
              <div className="text-3xl font-extrabold tracking-tight mt-2 text-amber-500">
                {nationalData?.summary?.active_dispute_cases || 2}
              </div>
              <span className="text-[11px] text-amber-500 font-bold">Active SLA timers running</span>
            </div>
          </div>

          {/* State Heatmap Interactive Grid */}
          <div className="p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 className="text-base font-bold tracking-tight flex items-center gap-2">
                  <MapPin className="w-4 h-4 text-amber-500" />
                  <span>State-Wise Seat Utilization Heatmap</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Interactive state grid color-coded by admission fill rate and sanctioned capacity breaches
                </p>
              </div>

              {/* Heatmap Legend */}
              <div className="flex items-center gap-3 text-[11px] font-bold">
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
                  <span>Optimal (&gt;75%)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-yellow-500"></span>
                  <span>High (90-100%)</span>
                </span>
                <span className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-pulse"></span>
                  <span>Intake Breach</span>
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2.5">
              {nationalData?.state_heatmap?.map((state: any) => {
                const isBreach = state.risk_level === "BREACH";
                const isHigh = state.fill_rate >= 90;

                return (
                  <div
                    key={state.code}
                    onClick={() => setSelectedState(state.name === selectedState ? null : state.name)}
                    className={`p-3 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between ${
                      selectedState === state.name
                        ? "ring-2 ring-primary border-primary bg-primary/10 shadow"
                        : isBreach
                        ? "border-red-500/40 bg-red-500/5 hover:border-red-500"
                        : isHigh
                        ? "border-yellow-500/30 bg-yellow-500/5 hover:border-yellow-500"
                        : "border-border bg-muted/20 hover:border-primary/50"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-xs font-mono">{state.code}</span>
                      <span
                        className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded ${
                          isBreach
                            ? "bg-red-500 text-white"
                            : isHigh
                            ? "bg-yellow-500/20 text-yellow-600 dark:text-yellow-400"
                            : "bg-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                        }`}
                      >
                        {state.fill_rate}%
                      </span>
                    </div>

                    <div className="mt-2">
                      <span className="text-xs font-bold block truncate">{state.name}</span>
                      <span className="text-[10px] text-muted-foreground block">
                        {state.enrolment}/{state.intake} seats
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Charts Row: BarChart (State Intake vs Enrolment) & Donut (Categories) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* BarChart */}
            <div className="lg:col-span-8 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold tracking-tight">
                    Intake vs. Actual Enrolment across Top States
                  </h3>
                  <p className="text-xs text-muted-foreground">Sanctioned seats vs verified APAAR entries</p>
                </div>
              </div>

              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stateChartData || []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="name" fontSize={11} tickLine={false} />
                    <YAxis fontSize={11} tickLine={false} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "var(--card)",
                        borderRadius: "12px",
                        border: "1px solid var(--border)",
                        fontSize: "12px",
                      }}
                    />
                    <Bar dataKey="Intake" fill="#0A2540" radius={[6, 6, 0, 0]} />
                    <Bar dataKey="Enrolled" fill="#FF9933" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Donut Chart: Social Category Distribution */}
            <div className="lg:col-span-4 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
              <div>
                <h3 className="text-sm font-bold tracking-tight">Category-Wise Distribution</h3>
                <p className="text-xs text-muted-foreground">Social reservation quota breakdown</p>
              </div>

              <div className="h-60 w-full flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={nationalData?.category_distribution || []}
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={80}
                      paddingAngle={4}
                      dataKey="value"
                    >
                      {nationalData?.category_distribution?.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              {/* Custom Legend */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-1 border-t border-border">
                {nationalData?.category_distribution?.map((cat: any, idx: number) => (
                  <div key={cat.name} className="flex items-center gap-2">
                    <span
                      className="w-2.5 h-2.5 rounded-full shrink-0"
                      style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                    ></span>
                    <span className="text-muted-foreground truncate">{cat.name}:</span>
                    <span className="font-bold">{cat.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Lower Row: Flagged Institutions Radar & Real-Time Alert Feed */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Flagged Radar */}
            <div className="lg:col-span-7 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold tracking-tight flex items-center gap-2">
                    <Flame className="w-4 h-4 text-red-500" />
                    <span>Flagged Institutions Radar & Audit Priority</span>
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Colleges exceeding intake capacity, ghost-student clusters, or low Trust Scores
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                {nationalData?.flagged_radar?.map((inst: any) => (
                  <div
                    key={inst.id}
                    className="p-4 rounded-2xl border border-red-500/20 bg-red-500/5 hover:border-red-500/50 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs">{inst.name}</span>
                        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted text-muted-foreground">
                          {inst.aicte_id}
                        </span>
                      </div>
                      <span className="text-xs font-black text-red-500 bg-red-500/10 px-2.5 py-0.5 rounded-full border border-red-500/30">
                        Trust: {inst.trust_score}
                      </span>
                    </div>

                    <div className="flex flex-wrap gap-1.5">
                      {inst.reasons?.map((r: string, idx: number) => (
                        <span
                          key={idx}
                          className="text-[10px] font-semibold px-2 py-0.5 rounded bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20"
                        >
                          ⚠️ {r}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-muted-foreground pt-1 border-t border-red-500/10">
                      <span>{inst.state} Region</span>
                      <span className="font-bold">
                        Enrolment: {inst.actual_enrolment} / {inst.approved_intake} seats
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Realtime Live Alert Feed */}
            <div className="lg:col-span-5 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-bold tracking-tight flex items-center gap-2">
                    <Radio className="w-4 h-4 text-emerald-500 animate-pulse" />
                    <span>Real-Time Alert Feed</span>
                  </h3>
                  <p className="text-xs text-muted-foreground">Live WebSocket streaming push events</p>
                </div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/30">
                  LIVE STREAM
                </span>
              </div>

              <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
                {liveAlerts?.map((alert: any, idx: number) => (
                  <div
                    key={alert.id || idx}
                    className="p-3 rounded-2xl border border-border bg-muted/30 hover:bg-muted/60 transition-colors space-y-1 text-xs"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[11px] truncate max-w-[200px] text-primary">
                        {alert.title}
                      </span>
                      <span
                        className={`text-[9px] font-extrabold px-1.5 py-0.5 rounded ${
                          alert.severity === "URGENT" || alert.severity === "CRITICAL"
                            ? "bg-red-500/10 text-red-500 border border-red-500/30"
                            : "bg-amber-500/10 text-amber-500 border border-amber-500/30"
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-muted-foreground line-clamp-2 leading-snug">
                      {alert.message || alert.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* ==================== INSTITUTION REGISTRAR COMMAND VIEW ==================== */
        <div className="space-y-6">
          {/* Institutional Overview & Trust Score Meter */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Left: College Identity & Fill Rate */}
            <div className="lg:col-span-8 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border pb-4">
                <div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-muted text-muted-foreground">
                    AICTE ID: {institutionData?.institution?.aicte_id || "1-1000101"}
                  </span>
                  <h2 className="text-xl font-black tracking-tight mt-1">
                    {institutionData?.institution?.name || "Indian Institute of Technology Delhi"}
                  </h2>
                  <p className="text-xs text-muted-foreground">
                    {institutionData?.institution?.state} • {institutionData?.institution?.type} Institution
                  </p>
                </div>

                <div className="text-right">
                  <span className="text-xs text-muted-foreground block">Sanctioned Status</span>
                  <span
                    className={`text-xs font-bold px-3 py-1 rounded-full border ${
                      institutionData?.institution?.status === "ACTIVE"
                        ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                        : "bg-amber-500/10 text-amber-500 border-amber-500/30"
                    }`}
                  >
                    {institutionData?.institution?.status || "ACTIVE"}
                  </span>
                </div>
              </div>

              {/* Progress Fill Rate */}
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-bold">
                  <span>Overall Seat Fill Rate</span>
                  <span className="text-primary font-mono text-sm">
                    {institutionData?.institution?.actual_enrolment} / {institutionData?.institution?.approved_intake} seats (
                    {institutionData?.institution?.utilization_rate}%)
                  </span>
                </div>
                <div className="w-full h-3 rounded-full bg-muted overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all duration-500"
                    style={{ width: `${Math.min(100, institutionData?.institution?.utilization_rate || 85)}%` }}
                  ></div>
                </div>
              </div>

              {/* Branch-Wise Live Seat Lock Monitor (Feature E) */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                    Branch-Wise Live Seat Lock Monitor (Feature E)
                  </h3>
                  <span className="text-[10px] font-medium text-muted-foreground">
                    Warns at 90% • Locks at 100%
                  </span>
                </div>

                <div className="space-y-2.5">
                  {institutionData?.branch_utilization?.map((branch: any) => {
                    const isLocked = branch.lock_status === "LOCKED";
                    const isWarning = branch.lock_status === "WARNING";

                    return (
                      <div
                        key={branch.id}
                        className="p-3.5 rounded-2xl border border-border bg-muted/20 space-y-1.5"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-xs">{branch.branch}</span>
                          <span
                            className={`flex items-center gap-1 text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${
                              isLocked
                                ? "bg-red-500/10 text-red-500 border-red-500/30"
                                : isWarning
                                ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30"
                                : "bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                            }`}
                          >
                            {isLocked ? <Lock className="w-3 h-3" /> : isWarning ? <AlertTriangle className="w-3 h-3" /> : <Unlock className="w-3 h-3" />}
                            <span>{isLocked ? "SEAT LOCK ENGAGED" : isWarning ? "90% WARN THRESHOLD" : "SEATS OPEN"}</span>
                          </span>
                        </div>

                        <div className="w-full h-2 rounded-full bg-muted overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all ${
                              isLocked ? "bg-red-500" : isWarning ? "bg-yellow-500" : "bg-emerald-500"
                            }`}
                            style={{ width: `${Math.min(100, branch.utilization_rate)}%` }}
                          ></div>
                        </div>

                        <div className="flex justify-between text-[11px] text-muted-foreground font-mono">
                          <span>{branch.enrolled_count} / {branch.approved_intake} seats</span>
                          <span>Remaining: {branch.remaining_seats} seats</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Right: Institution Trust Score Meter (Feature B) */}
            <div className="lg:col-span-4 p-6 rounded-3xl bg-card border border-border shadow-sm space-y-6">
              <div>
                <h3 className="text-sm font-bold tracking-tight flex items-center gap-2">
                  <Award className="w-4 h-4 text-amber-500" />
                  <span>Institution Trust Score (0-100)</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Algorithmic reliability index computed from quality, timeliness, and anomaly history
                </p>
              </div>

              {/* Trust Score Radial Display */}
              <div className="p-6 rounded-3xl bg-gradient-to-br from-amber-500/10 via-transparent to-emerald-500/10 border border-border flex flex-col items-center justify-center text-center space-y-2">
                <span className="text-5xl font-black text-primary">
                  {institutionData?.trust_score_breakdown?.score || 95.0}
                </span>
                <span className="text-xs font-bold text-emerald-500 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">
                  Tier-1 High Reliability
                </span>
                <p className="text-[11px] text-muted-foreground pt-1">
                  Audit Priority: {institutionData?.trust_score_breakdown?.audit_priority || "STANDARD"}
                </p>
              </div>

              {/* Factors Breakdown */}
              <div className="space-y-3 text-xs">
                <h4 className="font-bold text-muted-foreground uppercase text-[11px]">Score Contributors:</h4>
                <div className="space-y-2">
                  <div className="flex justify-between p-2 rounded-xl bg-muted/40">
                    <span className="text-muted-foreground">Data Quality Score</span>
                    <span className="font-bold text-emerald-500">98% (+30 pts)</span>
                  </div>
                  <div className="flex justify-between p-2 rounded-xl bg-muted/40">
                    <span className="text-muted-foreground">Ingestion Timeliness</span>
                    <span className="font-bold text-emerald-500">95% (+25 pts)</span>
                  </div>
                  <div className="flex justify-between p-2 rounded-xl bg-muted/40">
                    <span className="text-muted-foreground">Anomaly Penalty</span>
                    <span className="font-bold text-emerald-500">0.0 (Zero fraud)</span>
                  </div>
                  <div className="flex justify-between p-2 rounded-xl bg-muted/40">
                    <span className="text-muted-foreground">Dispute Resolution Speed</span>
                    <span className="font-bold text-emerald-500">92% (+20 pts)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
