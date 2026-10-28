"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Layers,
  Link as LinkIcon,
  Unlink,
  Hash,
  Clock,
  User,
  Activity,
  FileCode,
  Bug,
  Sparkles,
  ArrowDown,
  Copy,
} from "lucide-react";
import {
  auditApi,
  AuditLogItem,
  AuditIntegrityResult,
} from "@/lib/api";

export default function AuditLedgerPage() {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [integrity, setIntegrity] = useState<AuditIntegrityResult | null>(null);
  const [isLoadingLogs, setIsLoadingLogs] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [isTampering, setIsTampering] = useState(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const fetchLogs = async () => {
    setIsLoadingLogs(true);
    try {
      const data = await auditApi.getLogs(60);
      setLogs(data);
    } catch (err) {
      console.error("Failed to load audit logs:", err);
    } finally {
      setIsLoadingLogs(false);
    }
  };

  const handleVerifyIntegrity = async () => {
    setIsVerifying(true);
    try {
      const result = await auditApi.verifyIntegrity();
      setIntegrity(result);
      await fetchLogs(); // Refresh logs to get latest hashes/details
    } catch (err) {
      console.error("Integrity verification failed:", err);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleInjectTamper = async () => {
    setIsTampering(true);
    try {
      await auditApi.injectTamper(3);
      // Run verify immediately to dramatically trigger the red alert for hackathon judges
      await handleVerifyIntegrity();
    } catch (err) {
      console.error("Tamper demo failed:", err);
    } finally {
      setIsTampering(false);
    }
  };

  const handleRestoreTamper = async () => {
    setIsRestoring(true);
    try {
      await auditApi.restoreTamper(3);
      await handleVerifyIntegrity();
    } catch (err) {
      console.error("Restore demo failed:", err);
    } finally {
      setIsRestoring(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    handleVerifyIntegrity();
  }, []);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  return (
    <div className="min-h-screen bg-background py-8 px-4 sm:px-8 max-w-7xl mx-auto space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20 flex items-center gap-1.5">
              <Layers className="w-3.5 h-3.5" />
              <span>Immutable SHA-256 Block Chaining</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Feature H: Tamper Detection</span>
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            Cryptographic Audit Ledger & Chain Inspector
          </h1>
          <p className="text-xs sm:text-sm text-muted-foreground mt-1">
            Every administrative, upload, validation, and verification event is linked sequentially into a SHA-256 hash chain with strict backward dependency.
          </p>
        </div>

        {/* Action Controls for Demo */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleVerifyIntegrity}
            disabled={isVerifying}
            className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-xs font-bold shadow-md hover:opacity-90 transition-all flex items-center gap-2 disabled:opacity-50"
          >
            {isVerifying ? <RefreshCw className="w-4 h-4 animate-spin" /> : <ShieldCheck className="w-4 h-4" />}
            <span>Verify Chain Integrity</span>
          </button>

          {integrity?.chain_valid ? (
            <button
              onClick={handleInjectTamper}
              disabled={isTampering}
              className="px-3.5 py-2 rounded-xl bg-destructive/10 text-destructive border border-destructive/20 hover:bg-destructive/20 text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
              title="Deliberately tamper with Block #3 in database to show tamper detection"
            >
              <Bug className="w-3.5 h-3.5" />
              <span>Inject Tamper Demo (Block #3)</span>
            </button>
          ) : (
            <button
              onClick={handleRestoreTamper}
              disabled={isRestoring}
              className="px-3.5 py-2 rounded-xl bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 hover:bg-emerald-500/20 text-xs font-bold transition-all flex items-center gap-1.5 shadow-sm"
              title="Restore Block #3 to original authentic hash"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Heal / Restore Block #3</span>
            </button>
          )}
        </div>
      </div>

      {/* Ledger Health Status Card */}
      {integrity && (
        <div
          className={`p-6 rounded-2xl border transition-all relative overflow-hidden shadow-md ${
            integrity.chain_valid
              ? "bg-gradient-to-r from-emerald-500/10 via-emerald-500/5 to-transparent border-emerald-500/30 text-emerald-600 dark:text-emerald-400"
              : "bg-gradient-to-r from-destructive/15 via-destructive/5 to-transparent border-destructive/40 text-destructive animate-pulse"
          }`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-start gap-4">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  integrity.chain_valid
                    ? "bg-emerald-500/20 text-emerald-500"
                    : "bg-destructive/20 text-destructive"
                }`}
              >
                {integrity.chain_valid ? (
                  <CheckCircle2 className="w-7 h-7" />
                ) : (
                  <Unlink className="w-7 h-7" />
                )}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-lg font-extrabold tracking-tight">
                    {integrity.chain_valid
                      ? "CRYPTOGRAPHIC LEDGER INTEGRITY VERIFIED (100% UNBROKEN)"
                      : `CRITICAL ALERT: LEDGER TAMPER DETECTED AT BLOCK #${integrity.broken_at_sequence}`}
                  </h2>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-background/60 border border-current">
                    SHA-256 CHAIN
                  </span>
                </div>
                <p className="text-xs mt-1 max-w-2xl text-foreground/80">
                  {integrity.message}
                </p>
                <div className="flex flex-wrap items-center gap-4 mt-3 text-[11px] font-mono text-muted-foreground">
                  <span>Total Blocks Verified: {integrity.total_records_checked}</span>
                  <span>Tip Hash: {integrity.latest_block_hash.slice(0, 16)}...</span>
                  <span>Checked: {new Date(integrity.checked_at).toLocaleTimeString()}</span>
                </div>
              </div>
            </div>

            {/* Quick Demo Guidance pill */}
            <div className="p-3 rounded-xl bg-background/50 border border-border text-foreground text-right sm:max-w-xs">
              <span className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground block">
                Hackathon Judge Showcase
              </span>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {integrity.chain_valid
                  ? "Click 'Inject Tamper Demo' above to simulate a rogue DBA altering historical logs."
                  : "Click 'Heal / Restore Block #3' to recover the unbroken mathematical chain."}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Visual Block-by-Block Chain */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold flex items-center gap-2">
              <LinkIcon className="w-4 h-4 text-primary" />
              <span>Immutable Chain Explorer</span>
            </h2>
            <p className="text-xs text-muted-foreground">
              Sequential backward-linked blocks. Changing a single character in Block #N invalidates all blocks N through Tip.
            </p>
          </div>
          <span className="text-xs font-mono text-muted-foreground">
            Displaying Latest {logs.length} Blocks
          </span>
        </div>

        {isLoadingLogs ? (
          <div className="h-48 flex items-center justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="space-y-3">
            {logs.map((block, idx) => {
              const isTampered =
                !integrity?.chain_valid &&
                integrity?.broken_at_sequence === block.sequence_number;

              return (
                <div key={block.id} className="relative">
                  {/* Visual Connection Arrow */}
                  {idx > 0 && (
                    <div className="flex justify-center -my-2 relative z-10">
                      <div className="w-5 h-5 rounded-full bg-muted border border-border flex items-center justify-center">
                        <ArrowDown className="w-3 h-3 text-muted-foreground" />
                      </div>
                    </div>
                  )}

                  <div
                    className={`p-4 sm:p-5 rounded-2xl border transition-all ${
                      isTampered
                        ? "border-destructive bg-destructive/10 shadow-lg shadow-destructive/10 ring-2 ring-destructive"
                        : "border-border bg-card/60 backdrop-blur hover:bg-card/90"
                    }`}
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 mb-3 border-b border-border/80">
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-9 h-9 rounded-xl flex items-center justify-center font-mono font-bold text-xs ${
                            isTampered
                              ? "bg-destructive text-destructive-foreground"
                              : block.sequence_number === 1
                              ? "bg-amber-500/20 text-amber-500 border border-amber-500/30"
                              : "bg-muted text-foreground"
                          }`}
                        >
                          #{block.sequence_number}
                        </div>

                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-extrabold">
                              {block.action.replace(/_/g, " ")}
                            </span>
                            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-muted border border-border">
                              {block.role}
                            </span>
                            {block.sequence_number === 1 && (
                              <span className="text-[10px] font-extrabold px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-600 dark:text-amber-400">
                                GENESIS BLOCK
                              </span>
                            )}
                            {isTampered && (
                              <span className="text-[10px] font-extrabold px-2 py-0.5 rounded bg-destructive text-destructive-foreground animate-pulse">
                                TAMPER DETECTED HERE
                              </span>
                            )}
                          </div>
                          <span className="text-[10px] text-muted-foreground">
                            Entity: {block.entity_type} {block.entity_id ? `• ${block.entity_id}` : ""} • Actor: {block.user_email || "System Engine"}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 text-[11px] font-mono text-muted-foreground">
                        <Clock className="w-3.5 h-3.5" />
                        <span>{new Date(block.timestamp).toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Hash Chain Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-2.5 rounded-xl bg-muted/40 border border-border/60">
                        <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-1 uppercase font-bold">
                          <span>Previous Block Hash (Parent):</span>
                          <button
                            onClick={() => copyToClipboard(block.previous_hash)}
                            className="hover:text-foreground"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                        <div className="truncate text-[11px] select-all">
                          {block.previous_hash}
                        </div>
                      </div>

                      <div
                        className={`p-2.5 rounded-xl border ${
                          isTampered
                            ? "bg-destructive/20 border-destructive text-destructive font-bold"
                            : "bg-muted/40 border-border/60"
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] text-muted-foreground mb-1 uppercase font-bold">
                          <span>Block SHA-256 Hash:</span>
                          <button
                            onClick={() => copyToClipboard(block.current_hash)}
                            className="hover:text-foreground"
                          >
                            <Copy className="w-3 h-3" />
                          </button>
                        </div>
                        <div className="truncate text-[11px] select-all">
                          {block.current_hash}
                        </div>
                      </div>
                    </div>

                    {/* Payload Details */}
                    {block.details && Object.keys(block.details).length > 0 && (
                      <div className="mt-3 p-2.5 rounded-xl bg-muted/20 border border-border/40 text-[11px] font-mono text-muted-foreground">
                        <span className="text-[10px] font-bold block mb-1 text-foreground/70 uppercase">
                          Block Data Payload:
                        </span>
                        <div className="break-all whitespace-pre-wrap">
                          {JSON.stringify(block.details)}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
