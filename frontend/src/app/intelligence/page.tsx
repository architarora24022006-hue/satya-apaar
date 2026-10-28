"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  AlertTriangle,
  ShieldCheck,
  Search,
  Lock,
  Unlock,
  Building2,
  Users,
  CheckCircle2,
  XCircle,
  HelpCircle,
  TrendingUp,
  Zap,
  Activity,
  ArrowRight,
  RefreshCw,
  GitCompare,
  Sliders,
  Scale,
  Sparkles,
  Info,
} from "lucide-react";
import {
  mlApi,
  AnomalyItem,
  TrustScoreItem,
  FuzzyDuplicateItem,
  SeatForecastItem,
} from "@/lib/api";

export default function IntelligenceCenterPage() {
  const [activeTab, setActiveTab] = useState<"ghost" | "trust" | "fuzzy" | "seats">("ghost");

  // State for all 4 features
  const [anomalies, setAnomalies] = useState<AnomalyItem[]>([]);
  const [trustScores, setTrustScores] = useState<TrustScoreItem[]>([]);
  const [fuzzyMatches, setFuzzyMatches] = useState<FuzzyDuplicateItem[]>([]);
  const [seatForecasts, setSeatForecasts] = useState<SeatForecastItem[]>([]);

  // Loading & Filter states
  const [isLoading, setIsLoading] = useState(false);
  const [isRecalculatingTrust, setIsRecalculatingTrust] = useState(false);
  const [similarityThreshold, setSimilarityThreshold] = useState(70.0);
  const [daysRemaining, setDaysRemaining] = useState(14);
  const [searchFilter, setSearchFilter] = useState("");
  const [riskFilter, setRiskFilter] = useState<string>("ALL");
  const [showFormulaModal, setShowFormulaModal] = useState(false);
  const [caseSuccessMessage, setCaseSuccessMessage] = useState<string | null>(null);

  const fetchAnomalies = async () => {
    try {
      const data = await mlApi.getAnomalies();
      setAnomalies(data);
    } catch (err) {
      console.error("Failed to load anomalies:", err);
    }
  };

  const fetchTrustScores = async () => {
    try {
      const data = await mlApi.getTrustScores();
      setTrustScores(data);
    } catch (err) {
      console.error("Failed to load trust scores:", err);
    }
  };

  const fetchFuzzyMatches = async (thresh = similarityThreshold) => {
    try {
      const data = await mlApi.getFuzzyDuplicates(thresh);
      setFuzzyMatches(data);
    } catch (err) {
      console.error("Failed to load fuzzy duplicates:", err);
    }
  };

  const fetchSeatForecasts = async (days = daysRemaining) => {
    try {
      const data = await mlApi.getSeatForecast(days);
      setSeatForecasts(data);
    } catch (err) {
      console.error("Failed to load seat forecasts:", err);
    }
  };

  useEffect(() => {
    setIsLoading(true);
    Promise.all([
      fetchAnomalies(),
      fetchTrustScores(),
      fetchFuzzyMatches(),
      fetchSeatForecasts(),
    ]).finally(() => setIsLoading(false));
  }, []);

  const handleRecalculateTrust = async () => {
    setIsRecalculatingTrust(true);
    try {
      await mlApi.recalculateTrustScores();
      await fetchTrustScores();
    } catch (err) {
      console.error("Failed to recalculate:", err);
    } finally {
      setIsRecalculatingTrust(false);
    }
  };

  const handleToggleSeatLock = async (branchId: string, currentState: boolean) => {
    try {
      const res = await mlApi.toggleSeatLock(branchId, !currentState);
      setSeatForecasts((prev) =>
        prev.map((b) => (b.branch_id === branchId ? { ...b, is_locked: res.is_locked } : b))
      );
    } catch (err) {
      console.error("Failed to toggle seat lock:", err);
    }
  };

  const handleOpenFuzzyCase = async (match: FuzzyDuplicateItem) => {
    try {
      const res = await mlApi.openCaseForFuzzy({
        candidate_id: match.candidate_id,
        record_a_id: match.record_a.id,
        record_b_id: match.record_b.id,
        reason: match.explanation,
      });
      setCaseSuccessMessage(`Dispute Case ${res.case_number} successfully registered!`);
      setTimeout(() => setCaseSuccessMessage(null), 4000);
    } catch (err: any) {
      console.error("Failed to open case:", err);
    }
  };

  // Filtered Anomalies
  const filteredAnomalies = anomalies.filter((item) => {
    const matchesSearch =
      item.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      item.aicte_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
      item.state.toLowerCase().includes(searchFilter.toLowerCase());
    const matchesRisk = riskFilter === "ALL" || item.risk_tier === riskFilter;
    return matchesSearch && matchesRisk;
  });

  // Filtered Trust Scores
  const filteredTrustScores = trustScores.filter((item) =>
    item.name.toLowerCase().includes(searchFilter.toLowerCase()) ||
    item.aicte_id.toLowerCase().includes(searchFilter.toLowerCase()) ||
    item.state.toLowerCase().includes(searchFilter.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-background py-8 px-4 sm:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-purple-500/10 text-purple-500 border border-purple-500/20 flex items-center gap-1.5">
              <Brain className="w-3.5 h-3.5" />
              <span>Phase 5: AI & Machine Learning Suite</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" />
              <span>Real-Time Anomaly Radar</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            AICTE Predictive Intelligence & Risk Center
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Scikit-learn Isolation Forest anomaly detector, Rapidfuzz cross-college duplicate matching, dynamic trust score calculations, and seat allocation forecaster.
          </p>
        </div>

        {/* Global Tab Navigation */}
        <div className="flex items-center bg-muted p-1 rounded-xl border border-border">
          <button
            onClick={() => setActiveTab("ghost")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "ghost"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5 text-rose-500" />
            <span>Ghost-Student Radar</span>
          </button>
          <button
            onClick={() => setActiveTab("trust")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "trust"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
            <span>Trust Score Engine</span>
          </button>
          <button
            onClick={() => setActiveTab("fuzzy")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "fuzzy"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <GitCompare className="w-3.5 h-3.5 text-cyan-500" />
            <span>Fuzzy Matcher</span>
          </button>
          <button
            onClick={() => setActiveTab("seats")}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeTab === "seats"
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            <Lock className="w-3.5 h-3.5 text-amber-500" />
            <span>Seat Forecaster</span>
          </button>
        </div>
      </div>

      {caseSuccessMessage && (
        <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center gap-2 text-xs font-bold">
          <CheckCircle2 className="w-4 h-4" />
          <span>{caseSuccessMessage}</span>
        </div>
      )}

      {/* TAB 1: GHOST-STUDENT ANOMALY DETECTOR */}
      {activeTab === "ghost" && (
        <div className="space-y-6">
          {/* Quick Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl border border-border bg-card/60 backdrop-blur">
              <span className="text-[11px] font-bold text-muted-foreground block uppercase">
                Institutions Scanned
              </span>
              <span className="text-2xl font-extrabold block mt-1">{anomalies.length}</span>
              <span className="text-[10px] text-muted-foreground">Scikit-learn Isolation Forest</span>
            </div>
            <div className="p-4 rounded-2xl border border-rose-500/20 bg-rose-500/5">
              <span className="text-[11px] font-bold text-rose-600 dark:text-rose-400 block uppercase">
                Critical Risk Clusters
              </span>
              <span className="text-2xl font-extrabold text-rose-600 dark:text-rose-400 block mt-1">
                {anomalies.filter((a) => a.risk_tier === "CRITICAL").length}
              </span>
              <span className="text-[10px] text-muted-foreground">Score &gt; 80 / Severe Anomaly</span>
            </div>
            <div className="p-4 rounded-2xl border border-amber-500/20 bg-amber-500/5">
              <span className="text-[11px] font-bold text-amber-600 dark:text-amber-400 block uppercase">
                High Risk Watchlist
              </span>
              <span className="text-2xl font-extrabold text-amber-600 dark:text-amber-400 block mt-1">
                {anomalies.filter((a) => a.risk_tier === "HIGH").length}
              </span>
              <span className="text-[10px] text-muted-foreground">Velocity surges &gt; 2.5x</span>
            </div>
            <div className="p-4 rounded-2xl border border-emerald-500/20 bg-emerald-500/5">
              <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 block uppercase">
                Clean Normal Trajectory
              </span>
              <span className="text-2xl font-extrabold text-emerald-600 dark:text-emerald-400 block mt-1">
                {anomalies.filter((a) => a.risk_tier === "LOW").length}
              </span>
              <span className="text-[10px] text-muted-foreground">Within statistical baseline</span>
            </div>
          </div>

          {/* Filters Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 rounded-2xl bg-card/60 border border-border">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-muted-foreground" />
              <input
                type="text"
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                placeholder="Search college, AICTE ID, or state..."
                className="w-full text-xs pl-9 pr-3 py-2 rounded-xl border border-border bg-background outline-none"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground">Risk Tier:</span>
              {["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"].map((tier) => (
                <button
                  key={tier}
                  onClick={() => setRiskFilter(tier)}
                  className={`px-3 py-1 rounded-lg text-xs font-bold border transition-colors ${
                    riskFilter === tier
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:bg-muted"
                  }`}
                >
                  {tier}
                </button>
              ))}
            </div>
          </div>

          {/* Anomaly Cards Grid */}
          <div className="grid grid-cols-1 gap-4">
            {filteredAnomalies.map((item) => {
              const isCritical = item.risk_tier === "CRITICAL";
              const isHigh = item.risk_tier === "HIGH";

              return (
                <div
                  key={item.institution_id}
                  className={`p-5 rounded-2xl border transition-all ${
                    isCritical
                      ? "border-rose-500/40 bg-rose-500/5 shadow-md shadow-rose-500/5"
                      : isHigh
                      ? "border-amber-500/30 bg-amber-500/5"
                      : "border-border bg-card/60"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 mb-3 border-b border-border/80">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            isCritical
                              ? "bg-rose-500 text-white"
                              : isHigh
                              ? "bg-amber-500 text-slate-950 font-bold"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {item.risk_tier} RISK
                        </span>
                        <span className="text-xs font-mono font-bold text-muted-foreground">
                          {item.aicte_id}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          • {item.city}, {item.state}
                        </span>
                      </div>
                      <h3 className="text-base font-extrabold tracking-tight">{item.name}</h3>
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <span className="text-[10px] uppercase font-bold text-muted-foreground block">
                          Anomaly Score
                        </span>
                        <span
                          className={`text-2xl font-black font-mono ${
                            isCritical ? "text-rose-500" : isHigh ? "text-amber-500" : "text-emerald-500"
                          }`}
                        >
                          {item.anomaly_score}
                          <span className="text-xs text-muted-foreground font-normal">/100</span>
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* 5-Feature Telemetry Breakdown */}
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-4">
                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                        48h Surge Velocity
                      </span>
                      <span className="text-xs font-extrabold font-mono mt-0.5 block">
                        {item.surge_ratio}x baseline
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                        Final 72h Clustering
                      </span>
                      <span className="text-xs font-extrabold font-mono mt-0.5 block">
                        {item.last_day_clustering}%
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                        Demographic Entropy
                      </span>
                      <span className="text-xs font-extrabold font-mono mt-0.5 block">
                        {item.category_entropy}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                        Consecutive APAARs
                      </span>
                      <span className="text-xs font-extrabold font-mono mt-0.5 block">
                        {item.sequentiality_ratio}%
                      </span>
                    </div>

                    <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                      <span className="text-[10px] text-muted-foreground uppercase font-bold block">
                        Intake Saturation
                      </span>
                      <span className="text-xs font-extrabold font-mono mt-0.5 block">
                        {Math.round(item.intake_saturation * 100)}% ({item.total_students}/{item.total_intake})
                      </span>
                    </div>
                  </div>

                  {/* Natural Language AI Explanation */}
                  <div className="p-3 rounded-xl bg-background/60 border border-border flex items-start gap-2.5">
                    <Sparkles className="w-4 h-4 text-purple-500 flex-shrink-0 mt-0.5" />
                    <p className="text-xs leading-relaxed text-foreground/90 font-medium">
                      {item.explanation}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: INSTITUTION TRUST SCORE ENGINE */}
      {activeTab === "trust" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <span>Dynamic Trust Score Leaderboard</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Institutions scoring under 60 are automatically escalated for mandatory AICTE Regional Officer manual inspections.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowFormulaModal(true)}
                className="px-3.5 py-2 rounded-xl border border-border bg-muted/60 hover:bg-muted text-xs font-bold transition-colors flex items-center gap-1.5"
              >
                <HelpCircle className="w-4 h-4 text-sky-500" />
                <span>How is this calculated?</span>
              </button>

              <button
                onClick={handleRecalculateTrust}
                disabled={isRecalculatingTrust}
                className="px-3.5 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-md hover:opacity-90 transition-all flex items-center gap-1.5 disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isRecalculatingTrust ? "animate-spin" : ""}`} />
                <span>Recalculate All Scores</span>
              </button>
            </div>
          </div>

          {/* Trust Score Table */}
          <div className="overflow-x-auto rounded-2xl border border-border bg-card/60 backdrop-blur">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/60 text-muted-foreground uppercase text-[10px] font-extrabold border-b border-border">
                <tr>
                  <th className="py-3 px-4">Rank & College</th>
                  <th className="py-3 px-3">State</th>
                  <th className="py-3 px-3 text-center">Data Quality (/30)</th>
                  <th className="py-3 px-3 text-center">Timeliness (/20)</th>
                  <th className="py-3 px-3 text-center">Anomaly (/40)</th>
                  <th className="py-3 px-3 text-center">Dispute Speed (/10)</th>
                  <th className="py-3 px-4 text-right">Trust Score</th>
                  <th className="py-3 px-3 text-center">Audit Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {filteredTrustScores.map((item, idx) => {
                  const score = item.trust_score;
                  const isAudit = item.is_flagged_for_audit;

                  return (
                    <tr key={item.institution_id} className="hover:bg-muted/30 transition-colors">
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-3">
                          <span className="font-mono text-xs font-bold text-muted-foreground w-6">
                            #{idx + 1}
                          </span>
                          <div>
                            <span className="font-bold block truncate max-w-xs">{item.name}</span>
                            <span className="text-[10px] font-mono text-muted-foreground">{item.aicte_id}</span>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-3 text-muted-foreground">{item.state}</td>
                      <td className="py-3 px-3 text-center font-mono font-semibold">
                        {item.breakdown.data_quality_pts}
                      </td>
                      <td className="py-3 px-3 text-center font-mono font-semibold">
                        {item.breakdown.timeliness_pts}
                      </td>
                      <td className="py-3 px-3 text-center font-mono font-semibold">
                        {item.breakdown.anomaly_pts}
                      </td>
                      <td className="py-3 px-3 text-center font-mono font-semibold">
                        {item.breakdown.resolution_pts}
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-extrabold text-sm">
                        <span
                          className={
                            score >= 80 ? "text-emerald-500" : score >= 60 ? "text-amber-500" : "text-rose-500"
                          }
                        >
                          {score}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isAudit
                              ? "bg-rose-500/10 text-rose-500 border border-rose-500/20"
                              : "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20"
                          }`}
                        >
                          {isAudit ? "AUDIT REQUIRED" : "CLEAN"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: CROSS-INSTITUTION FUZZY MATCH RESOLVER */}
      {activeTab === "fuzzy" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <GitCompare className="w-5 h-5 text-cyan-500" />
                <span>Rapidfuzz Cross-Institution Identity Duplicate Matcher</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Flags potential dual registrations where names have middle initials, spelling variations, or different APAARs across institutions.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs font-semibold text-muted-foreground">Threshold:</span>
              <input
                type="range"
                min={50}
                max={95}
                value={similarityThreshold}
                onChange={(e) => {
                  const val = parseFloat(e.target.value);
                  setSimilarityThreshold(val);
                  fetchFuzzyMatches(val);
                }}
                className="w-28 cursor-pointer"
              />
              <span className="text-xs font-mono font-bold w-12">{similarityThreshold}%</span>
            </div>
          </div>

          {fuzzyMatches.length === 0 ? (
            <div className="p-12 text-center text-xs text-muted-foreground border border-dashed border-border rounded-2xl">
              No cross-institution duplicate identities detected at {similarityThreshold}% similarity threshold.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6">
              {fuzzyMatches.map((match) => (
                <div
                  key={match.candidate_id}
                  className="p-6 rounded-2xl border border-border bg-card/60 backdrop-blur shadow-sm space-y-4"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-border">
                    <div className="flex items-center gap-2">
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-extrabold bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20">
                        {match.tier.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs font-mono font-bold">
                        Similarity Score: {match.composite_score}% (Name Match: {match.name_similarity}%)
                      </span>
                    </div>

                    <button
                      onClick={() => handleOpenFuzzyCase(match)}
                      className="px-3 py-1.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-sm hover:opacity-90 transition-all flex items-center gap-1.5"
                    >
                      <Scale className="w-3.5 h-3.5" />
                      <span>1-Click Escalate to Dispute Case (48h SLA)</span>
                    </button>
                  </div>

                  {/* Side by Side Record Cards */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {/* Record A */}
                    <div className="p-4 rounded-xl bg-muted/40 border border-border">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                        Institution A Record
                      </span>
                      <h4 className="text-sm font-bold">{match.record_a.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{match.record_a.institution_name}</p>
                      <div className="mt-2 space-y-1 font-mono text-[11px] text-muted-foreground">
                        <div>APAAR: <span className="text-foreground font-semibold">{match.record_a.apaar_id}</span></div>
                        <div>DOB: <span className="text-foreground">{match.record_a.dob}</span> • Gender: {match.record_a.gender}</div>
                        <div>Program: {match.record_a.branch}</div>
                      </div>
                    </div>

                    {/* Record B */}
                    <div className="p-4 rounded-xl bg-muted/40 border border-border">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block mb-1">
                        Institution B Record
                      </span>
                      <h4 className="text-sm font-bold">{match.record_b.name}</h4>
                      <p className="text-xs text-muted-foreground mt-0.5">{match.record_b.institution_name}</p>
                      <div className="mt-2 space-y-1 font-mono text-[11px] text-muted-foreground">
                        <div>APAAR: <span className="text-foreground font-semibold">{match.record_b.apaar_id}</span></div>
                        <div>DOB: <span className="text-foreground">{match.record_b.dob}</span> • Gender: {match.record_b.gender}</div>
                        <div>Program: {match.record_b.branch}</div>
                      </div>
                    </div>
                  </div>

                  {/* Diff Explanation */}
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-700 dark:text-amber-300 font-medium">
                    Analysis: {match.explanation}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* TAB 4: PREDICTIVE SEAT FORECASTER & AUTOMATED LOCK */}
      {activeTab === "seats" && (
        <div className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold flex items-center gap-2">
                <Lock className="w-5 h-5 text-amber-500" />
                <span>Predictive Seat Allocation Forecaster & Lock Engine</span>
              </h2>
              <p className="text-xs text-muted-foreground">
                Projects quota exhaustion before admission deadlines and enables real-time AICTE seat locking.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-muted-foreground">Projection Horizon:</span>
              {[7, 14, 30].map((d) => (
                <button
                  key={d}
                  onClick={() => {
                    setDaysRemaining(d);
                    fetchSeatForecasts(d);
                  }}
                  className={`px-3 py-1 rounded-lg text-xs font-bold border transition-colors ${
                    daysRemaining === d
                      ? "bg-primary text-primary-foreground border-primary"
                      : "bg-background text-muted-foreground border-border hover:bg-muted"
                  }`}
                >
                  {d} Days
                </button>
              ))}
            </div>
          </div>

          {/* Seat Forecast Table */}
          <div className="overflow-x-auto rounded-2xl border border-border bg-card/60 backdrop-blur">
            <table className="w-full text-left text-xs">
              <thead className="bg-muted/60 text-muted-foreground uppercase text-[10px] font-extrabold border-b border-border">
                <tr>
                  <th className="py-3 px-4">College & Program Branch</th>
                  <th className="py-3 px-3 text-center">Approved Intake</th>
                  <th className="py-3 px-3 text-center">Current Enrolled</th>
                  <th className="py-3 px-3 text-center">Daily Velocity</th>
                  <th className="py-3 px-3 text-center">Projected ({daysRemaining}d)</th>
                  <th className="py-3 px-3 text-center">Risk Status</th>
                  <th className="py-3 px-4 text-center">Real-Time Seat Lock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {seatForecasts.map((b) => {
                  const isBreached = b.risk_status === "BREACHED";
                  const isHighRisk = b.risk_status === "HIGH_RISK_PROJECTED_BREACH";

                  return (
                    <tr
                      key={b.branch_id}
                      className={`hover:bg-muted/30 transition-colors ${
                        isBreached ? "bg-rose-500/5" : isHighRisk ? "bg-amber-500/5" : ""
                      }`}
                    >
                      <td className="py-3 px-4">
                        <span className="font-bold block truncate max-w-sm">{b.branch_name}</span>
                        <span className="text-[10px] text-muted-foreground">
                          {b.institution_name} • {b.institution_aicte_id}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center font-mono font-bold">{b.approved_intake}</td>
                      <td className="py-3 px-3 text-center font-mono font-bold">
                        <span className={isBreached ? "text-rose-500" : ""}>{b.current_enrolled}</span>
                        <span className="text-[10px] text-muted-foreground block">
                          ({b.current_capacity_pct}%)
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center font-mono text-muted-foreground">
                        +{b.daily_velocity}/day
                      </td>
                      <td className="py-3 px-3 text-center font-mono font-extrabold">
                        <span className={isBreached || isHighRisk ? "text-rose-500" : "text-emerald-500"}>
                          {b.projected_final_enrolment}
                        </span>
                        <span className="text-[10px] text-muted-foreground block">
                          ({b.projected_capacity_pct}%)
                        </span>
                      </td>
                      <td className="py-3 px-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isBreached
                              ? "bg-rose-500 text-white"
                              : isHighRisk
                              ? "bg-amber-500/10 text-amber-500 border border-amber-500/30"
                              : "bg-muted text-muted-foreground"
                          }`}
                        >
                          {b.risk_status.replace(/_/g, " ")}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleToggleSeatLock(b.branch_id, b.is_locked)}
                          className={`px-3 py-1 rounded-lg text-xs font-bold border flex items-center gap-1.5 mx-auto transition-colors ${
                            b.is_locked
                              ? "bg-rose-500/10 text-rose-500 border-rose-500/30 hover:bg-rose-500/20"
                              : "bg-emerald-500/10 text-emerald-500 border-emerald-500/30 hover:bg-emerald-500/20"
                          }`}
                        >
                          {b.is_locked ? <Lock className="w-3.5 h-3.5" /> : <Unlock className="w-3.5 h-3.5" />}
                          <span>{b.is_locked ? "LOCKED" : "OPEN"}</span>
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Formula Modal Popover */}
      {showFormulaModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-card border border-border p-6 rounded-2xl max-w-lg w-full space-y-4 shadow-xl">
            <div className="flex items-center justify-between pb-3 border-b border-border">
              <h3 className="font-extrabold text-base flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-sky-500" />
                <span>AICTE Trust Score Engine Formula</span>
              </h3>
              <button
                onClick={() => setShowFormulaModal(false)}
                className="p-1 hover:bg-muted rounded-lg text-muted-foreground"
              >
                <XCircle className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3 text-xs leading-relaxed">
              <p className="text-muted-foreground">
                The Trust Score is an automated 0–100 index evaluated dynamically for every AICTE-approved institution based on 4 pillars:
              </p>
              <div className="space-y-2 p-3 bg-muted/40 rounded-xl border border-border font-mono text-[11px]">
                <div className="flex justify-between">
                  <span className="font-bold text-foreground">1. Data Quality Factor (Max 30 pts):</span>
                  <span>Validated / Total uploads</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-bold text-foreground">2. Timeliness Factor (Max 20 pts):</span>
                  <span>Spread vs final 72h rush</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-bold text-foreground">3. Anomaly Clearance (Max 40 pts):</span>
                  <span>Isolation Forest & clash penalties</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-bold text-foreground">4. Dispute Resolution (Max 10 pts):</span>
                  <span>Cases resolved within SLA</span>
                </div>
              </div>
              <div className="p-3 bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 rounded-xl text-[11px] font-semibold">
                Audit Rule: Institutions with a score &lt; 60 are automatically scheduled for AICTE Regional Officer mandatory manual on-site inspection.
              </div>
            </div>

            <button
              onClick={() => setShowFormulaModal(false)}
              className="w-full py-2.5 rounded-xl bg-primary text-primary-foreground font-bold text-xs shadow-md"
            >
              Understood
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
