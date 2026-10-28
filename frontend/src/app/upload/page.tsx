"use client";

import React, { useState, useEffect } from "react";
import { useLanguage } from "@/hooks/useLanguage";
import { useAuth } from "@/hooks/useAuth";
import { API_BASE } from "@/lib/api";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  Sparkles,
  Download,
  RefreshCw,
  SlidersHorizontal,
  FileText,
  UserPlus,
  ShieldAlert,
  Flame,
} from "lucide-react";

export default function UploadPortalPage() {
  const { t } = useLanguage();
  const { user, isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState<"bulk" | "single">("bulk");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [previewData, setPreviewData] = useState<any | null>(null);
  const [batchResult, setBatchResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>("ALL");

  // Single Entry Form state
  const [singleForm, setSingleForm] = useState({
    apaar_id: "",
    name: "",
    dob: "2004-05-14",
    gender: "Male",
    program: "UG",
    branch: "Computer Science & Engineering",
    year_of_study: 1,
    admission_date: "2025-07-15",
    quota_type: "Merit",
    category: "General",
    is_supernumerary: false,
    is_nri: false,
  });
  const [singleResult, setSingleResult] = useState<any | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setErrorMsg(null);
      setBatchResult(null);

      // Trigger Smart Upload Assistant Preview
      setIsAnalyzing(true);
      const formData = new FormData();
      formData.append("file", file);

      try {
        const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
        const headers: Record<string, string> = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }
        const res = await fetch(`${API_BASE}/api/v1/upload/preview`, {
          method: "POST",
          headers,
          body: formData,
        });

        if (!res.ok) {
          throw new Error("Failed to analyze upload file preview");
        }
        const data = await res.json();
        setPreviewData(data);
      } catch (err: any) {
        setErrorMsg(err.message || "Failed to inspect file preview");
      } finally {
        setIsAnalyzing(false);
      }
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    setIsSubmitting(true);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append("file", selectedFile);
    if (previewData?.mapping_analysis?.mapping) {
      formData.append(
        "column_mapping_json",
        JSON.stringify(previewData.mapping_analysis.mapping)
      );
    }

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
      const headers: Record<string, string> = {};
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API_BASE}/api/v1/upload/batch`, {
        method: "POST",
        headers,
        body: formData,
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || "Batch upload failed");
      }

      const result = await res.json();
      setBatchResult(result);
    } catch (err: any) {
      setErrorMsg(err.message || "Upload and validation failed");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSingleEntrySubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSingleResult(null);

    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
      const res = await fetch(`${API_BASE}/api/v1/upload/single-entry`, {
        method: "POST",
        headers,
        body: JSON.stringify(singleForm),
      });

      const data = await res.json();
      setSingleResult(data);
    } catch (err: any) {
      setSingleResult({ success: false, message: err.message });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadSample = () => {
    window.open(`${API_BASE}/api/v1/upload/sample-csv`, "_blank");
  };

  const filteredIssues = batchResult?.error_grid?.filter((issue: any) => {
    if (severityFilter === "ALL") return true;
    return issue.severity === severityFilter;
  });

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-6 rounded-3xl bg-card border border-border shadow-sm">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-primary/10 text-primary">
              <UploadCloud className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black tracking-tight">
              Student Ingestion & Validation Portal
            </h1>
          </div>
          <p className="text-xs text-muted-foreground">
            Upload institutional student batches with AI Smart Mapping, real-time 12-digit APAAR validation, and live seat lock monitoring.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadSample}
            className="flex items-center gap-2 px-3.5 py-2 rounded-xl border border-border bg-muted/60 hover:bg-muted text-xs font-bold transition-all"
            title="Download 500-row test dataset with deliberate planted clashes and errors"
          >
            <Download className="w-4 h-4 text-amber-500" />
            <span>Download 500-Row Demo CSV</span>
          </button>
        </div>
      </div>

      {/* Mode Tabs: Bulk CSV vs Single Form */}
      <div className="flex items-center gap-2 border-b border-border pb-2">
        <button
          onClick={() => setActiveTab("bulk")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "bulk"
              ? "bg-primary text-primary-foreground shadow"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Bulk Ingestion (CSV / Excel)</span>
        </button>
        <button
          onClick={() => setActiveTab("single")}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
            activeTab === "single"
              ? "bg-primary text-primary-foreground shadow"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <UserPlus className="w-4 h-4" />
          <span>Single Candidate Entry Form</span>
        </button>
      </div>

      {errorMsg && (
        <div className="p-4 rounded-2xl bg-destructive/10 border border-destructive/20 text-destructive text-xs font-medium flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {activeTab === "bulk" ? (
        <div className="space-y-6">
          {/* File Upload Zone */}
          <div className="p-8 rounded-3xl border-2 border-dashed border-border bg-muted/20 hover:border-primary/50 transition-colors flex flex-col items-center justify-center text-center space-y-4">
            <div className="p-4 rounded-2xl bg-primary/10 text-primary">
              <UploadCloud className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold">Select student enrolment data file</h3>
              <p className="text-xs text-muted-foreground max-w-md">
                Supports CSV or XLSX up to 50,000 rows. Includes auto-detection of messy column headers.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <label className="cursor-pointer px-4 py-2.5 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity">
                Browse Files
                <input
                  type="file"
                  accept=".csv,.xlsx"
                  className="hidden"
                  onChange={handleFileChange}
                />
              </label>
              {selectedFile && (
                <span className="text-xs font-mono font-medium text-muted-foreground">
                  {selectedFile.name} ({(selectedFile.size / 1024).toFixed(1)} KB)
                </span>
              )}
            </div>
          </div>

          {/* Smart Upload Assistant: Header Mapping Preview */}
          {isAnalyzing && (
            <div className="p-6 rounded-2xl bg-card border border-border flex items-center justify-center gap-3 text-xs font-medium">
              <RefreshCw className="w-4 h-4 animate-spin text-amber-500" />
              <span>Smart Assistant inspecting column headers & schema mapping...</span>
            </div>
          )}

          {previewData && !batchResult && (
            <div className="p-6 rounded-3xl bg-card border border-border shadow-sm space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="p-1.5 rounded-lg bg-amber-500/10 text-amber-500">
                    <Sparkles className="w-4 h-4" />
                  </span>
                  <div>
                    <h3 className="text-sm font-bold">Smart Upload Assistant: Header Mapping</h3>
                    <p className="text-xs text-muted-foreground">
                      Columns mapped to canonical AICTE schema with confidence indicators
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleUploadSubmit}
                  disabled={isSubmitting}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 text-white text-xs font-bold hover:bg-emerald-700 shadow-md transition-all disabled:opacity-50"
                >
                  {isSubmitting ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ArrowRight className="w-4 h-4" />}
                  <span>{isSubmitting ? "Running Validation Engine..." : "Submit Batch for Validation"}</span>
                </button>
              </div>

              {/* Mapping Badges Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
                {Object.entries(previewData.mapping_analysis.mapping).map(([rawCol, canonCol]: any) => (
                  <div
                    key={rawCol}
                    className="p-3 rounded-xl bg-muted/40 border border-border flex flex-col justify-between space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono text-muted-foreground truncate max-w-[120px]">
                        "{rawCol}"
                      </span>
                      <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                        {Math.round((previewData.mapping_analysis.confidence[rawCol] || 1) * 100)}%
                      </span>
                    </div>
                    <span className="text-xs font-bold text-primary truncate">
                      → {previewData.mapping_analysis.canonical_schema[canonCol] || canonCol}
                    </span>
                  </div>
                ))}
              </div>

              {/* Sample Rows Preview */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-muted-foreground">First 5 Rows Preview:</h4>
                <div className="overflow-x-auto rounded-xl border border-border">
                  <table className="w-full text-[11px] text-left">
                    <thead className="bg-muted text-muted-foreground">
                      <tr>
                        {previewData.detected_headers.map((h: string) => (
                          <th key={h} className="p-2.5 font-bold border-b border-border">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {previewData.sample_rows_preview.map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-border/60 hover:bg-muted/20 font-mono">
                          {previewData.detected_headers.map((h: string) => (
                            <td key={h} className="p-2.5 truncate max-w-[160px]">
                              {row[h]}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* Batch Validation Output: Execution Summary & Error Grid */}
          {batchResult && (
            <div className="space-y-6">
              {/* Metric Highlights */}
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
                <div className="p-5 rounded-2xl bg-card border border-border shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-medium text-muted-foreground">Total Ingested</span>
                  <span className="text-3xl font-extrabold">{batchResult.total_records}</span>
                  <span className="text-[11px] text-muted-foreground">Processed without blocking</span>
                </div>
                <div className="p-5 rounded-2xl bg-card border border-emerald-500/30 bg-emerald-500/5 shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-medium text-emerald-600 dark:text-emerald-400">Valid Records</span>
                  <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                    {batchResult.valid_records}
                  </span>
                  <span className="text-[11px] text-emerald-500 font-medium">Ready for Central Repo</span>
                </div>
                <div className="p-5 rounded-2xl bg-card border border-amber-500/30 bg-amber-500/5 shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-medium text-amber-600 dark:text-amber-400">Flagged Records</span>
                  <span className="text-3xl font-extrabold text-amber-600 dark:text-amber-400">
                    {batchResult.flagged_records}
                  </span>
                  <span className="text-[11px] text-amber-500 font-medium">Requires review/auto-fix</span>
                </div>
                <div className="p-5 rounded-2xl bg-card border border-destructive/30 bg-destructive/5 shadow-sm flex flex-col justify-between">
                  <span className="text-xs font-medium text-destructive">Total Issues Raised</span>
                  <span className="text-3xl font-extrabold text-destructive">
                    {batchResult.issues_count}
                  </span>
                  <span className="text-[11px] text-destructive font-medium">Violations & Warnings</span>
                </div>
              </div>

              {/* Interactive Row-by-Row Error Grid */}
              <div className="p-6 rounded-3xl bg-card border border-border shadow-sm space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <h3 className="text-base font-bold tracking-tight">Row-by-Row Error Grid</h3>
                    <p className="text-xs text-muted-foreground">
                      Inspect flagged anomalies with suggested one-click fixes
                    </p>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center gap-1.5 bg-muted p-1 rounded-xl text-xs font-bold">
                    {["ALL", "CRITICAL", "HIGH", "WARNING", "INFO"].map((sev) => (
                      <button
                        key={sev}
                        onClick={() => setSeverityFilter(sev)}
                        className={`px-3 py-1 rounded-lg transition-all ${
                          severityFilter === sev
                            ? "bg-card text-primary shadow-sm"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        {sev}
                      </button>
                    ))}
                  </div>
                </div>

                <div className="overflow-x-auto rounded-2xl border border-border">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-muted text-muted-foreground font-bold">
                      <tr>
                        <th className="p-3 w-16">Row</th>
                        <th className="p-3 w-32">Student APAAR</th>
                        <th className="p-3 w-40">Rule Code</th>
                        <th className="p-3 w-24">Severity</th>
                        <th className="p-3">Violation Reason</th>
                        <th className="p-3 w-64">Fix Suggestion</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {filteredIssues?.map((issue: any, idx: number) => (
                        <tr key={idx} className="hover:bg-muted/30 transition-colors">
                          <td className="p-3 font-mono font-bold text-muted-foreground">
                            #{issue.row_index || idx + 1}
                          </td>
                          <td className="p-3 font-mono font-bold">
                            {issue.student_apaar || "—"}
                          </td>
                          <td className="p-3">
                            <span className="px-2 py-0.5 rounded font-mono text-[10px] bg-muted border border-border font-bold">
                              {issue.rule_code}
                            </span>
                          </td>
                          <td className="p-3">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase border ${
                                issue.severity === "CRITICAL"
                                  ? "bg-red-500/10 text-red-500 border-red-500/30"
                                  : issue.severity === "HIGH"
                                  ? "bg-amber-500/10 text-amber-500 border-amber-500/30"
                                  : issue.severity === "WARNING"
                                  ? "bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border-yellow-500/30"
                                  : "bg-blue-500/10 text-blue-500 border-blue-500/30"
                              }`}
                            >
                              {issue.severity}
                            </span>
                          </td>
                          <td className="p-3 text-muted-foreground leading-snug">
                            {issue.message}
                          </td>
                          <td className="p-3 text-emerald-600 dark:text-emerald-400 font-medium">
                            {issue.fix_suggestion || "Manual review required."}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Single Candidate Entry Form */
        <div className="p-6 sm:p-8 rounded-3xl bg-card border border-border shadow-sm max-w-3xl mx-auto space-y-6">
          <div>
            <h2 className="text-lg font-bold">Candidate Admission Registration Form</h2>
            <p className="text-xs text-muted-foreground">
              Enrol a single student with instant live seat lock and Verhoeff checksum validation
            </p>
          </div>

          {singleResult && (
            <div
              className={`p-4 rounded-2xl border text-xs font-medium space-y-1 ${
                singleResult.success
                  ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
                  : "bg-destructive/10 border-destructive/20 text-destructive"
              }`}
            >
              <div className="font-bold flex items-center gap-2">
                {singleResult.success ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                <span>{singleResult.message}</span>
              </div>
              {singleResult.violations && (
                <ul className="list-disc pl-5 pt-1 space-y-1">
                  {singleResult.violations.map((v: any, i: number) => (
                    <li key={i}>{v.message} ({v.rule_code})</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <form onSubmit={handleSingleEntrySubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">12-Digit APAAR ID *</label>
                <input
                  type="text"
                  required
                  maxLength={12}
                  value={singleForm.apaar_id}
                  onChange={(e) => setSingleForm({ ...singleForm, apaar_id: e.target.value })}
                  placeholder="e.g. 992817263541"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm font-mono focus:ring-2 focus:ring-primary/40 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Candidate Full Name *</label>
                <input
                  type="text"
                  required
                  value={singleForm.name}
                  onChange={(e) => setSingleForm({ ...singleForm, name: e.target.value })}
                  placeholder="e.g. Priyanshu Saxena"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Date of Birth *</label>
                <input
                  type="date"
                  required
                  value={singleForm.dob}
                  onChange={(e) => setSingleForm({ ...singleForm, dob: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Gender</label>
                <select
                  value={singleForm.gender}
                  onChange={(e) => setSingleForm({ ...singleForm, gender: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                >
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Program & Branch *</label>
                <select
                  value={singleForm.branch}
                  onChange={(e) => setSingleForm({ ...singleForm, branch: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                >
                  <option value="Computer Science & Engineering">B.Tech - Computer Science & Engineering</option>
                  <option value="Electronics & Communication Engineering">B.Tech - Electronics & Communication</option>
                  <option value="Mechanical Engineering">B.Tech - Mechanical Engineering</option>
                  <option value="Artificial Intelligence & Data Science">B.Tech - AI & Data Science</option>
                  <option value="Master of Computer Applications">MCA - Computer Applications</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Admission Date *</label>
                <input
                  type="date"
                  required
                  value={singleForm.admission_date}
                  onChange={(e) => setSingleForm({ ...singleForm, admission_date: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Quota Type</label>
                <select
                  value={singleForm.quota_type}
                  onChange={(e) => setSingleForm({ ...singleForm, quota_type: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                >
                  <option value="Merit">Regular Merit</option>
                  <option value="Management">Management Quota</option>
                  <option value="NRI">NRI Quota</option>
                  <option value="Supernumerary">Supernumerary (TFW/PMSSS/EWS)</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-muted-foreground">Social Category</label>
                <select
                  value={singleForm.category}
                  onChange={(e) => setSingleForm({ ...singleForm, category: e.target.value })}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-input bg-background text-sm focus:ring-2 focus:ring-primary/40 focus:outline-none"
                >
                  <option value="General">General (Unreserved)</option>
                  <option value="OBC">OBC (Non-Creamy Layer)</option>
                  <option value="SC">SC (Scheduled Caste)</option>
                  <option value="ST">ST (Scheduled Tribe)</option>
                  <option value="EWS">EWS (Economically Weaker Section)</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-6 pt-2">
              <label className="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={singleForm.is_supernumerary}
                  onChange={(e) => setSingleForm({ ...singleForm, is_supernumerary: e.target.checked })}
                  className="rounded border-input text-primary"
                />
                <span>Supernumerary Seat</span>
              </label>

              <label className="flex items-center gap-2 text-xs font-semibold cursor-pointer">
                <input
                  type="checkbox"
                  checked={singleForm.is_nri}
                  onChange={(e) => setSingleForm({ ...singleForm, is_nri: e.target.checked })}
                  className="rounded border-input text-primary"
                />
                <span>Non-Resident Indian (NRI)</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl bg-primary text-primary-foreground text-xs font-bold hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow"
            >
              {isSubmitting && <RefreshCw className="w-4 h-4 animate-spin" />}
              <span>{isSubmitting ? "Validating & Enrolling..." : "Submit Student Admission"}</span>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
