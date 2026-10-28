const rawBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const API_BASE = rawBase.startsWith("http") ? rawBase : `https://${rawBase}`;

export async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("satya_access_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE}${endpoint}`;

  const res = await fetch(url, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errorDetail = "API Request failed";
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail || errorDetail;
    } catch {
      errorDetail = `${res.status} ${res.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return res.json() as Promise<T>;
}

// Phase 4: Verification, Consent & Audit Endpoints
export interface VerificationRequestPayload {
  apaar_id: string;
  verifier_name: string;
  verifier_org: string;
  verifier_role: string;
  purpose: string;
  otp_code?: string;
}

export interface VerificationResponseData {
  apaar_id: string;
  apaar_id_masked: string;
  student_name: string;
  verification_status: string;
  institution_name: string;
  institution_aicte_id: string;
  program: string;
  branch: string;
  year_of_study: number;
  aicte_approved: boolean;
  disclosed_data: Record<string, any>;
  restricted_fields: string[];
  consent_status: string;
  canonical_claim: Record<string, any>;
  signature_ed25519: string;
  public_key_b64: string;
  qr_payload: string;
  verified_at: string;
  access_log_id: string;
}

export interface OfflineVerifyPayload {
  claim: Record<string, any>;
  signature_ed25519: string;
  public_key_b64?: string;
}

export interface OfflineVerifyResult {
  is_valid: boolean;
  algorithm: string;
  issuer: string;
  verified_at: string;
  message: string;
  claim?: Record<string, any>;
}

export interface ConsentPolicy {
  verifier_type: string;
  allowed_fields: string[];
  is_active: boolean;
  expires_at?: string;
}

export interface ConsentWalletData {
  student_apaar_id: string;
  student_name: string;
  policies: ConsentPolicy[];
  active_otp?: string;
}

export interface AccessLogItem {
  id: string;
  student_apaar_id: string;
  verifier_name: string;
  verifier_org: string;
  verifier_role: string;
  purpose: string;
  accessed_fields: string[];
  ip_address: string;
  timestamp: string;
}

export interface AuditLogItem {
  id: string;
  sequence_number: number;
  timestamp: string;
  user_id?: string;
  user_email?: string;
  role: string;
  ip_address: string;
  action: string;
  entity_type: string;
  entity_id?: string;
  payload_hash: string;
  previous_hash: string;
  current_hash: string;
  details: Record<string, any>;
}

export interface AuditIntegrityResult {
  total_records_checked: number;
  chain_valid: boolean;
  broken_at_sequence?: number | null;
  message: string;
  latest_block_hash: string;
  checked_at: string;
}

export const verificationApi = {
  verifyStudent: (payload: VerificationRequestPayload) =>
    apiRequest<VerificationResponseData>("/api/v1/verification/verify", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  verifyOffline: (payload: OfflineVerifyPayload) =>
    apiRequest<OfflineVerifyResult>("/api/v1/verification/verify-offline", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  getPublicKey: () =>
    apiRequest<{ public_key_b64: string; algorithm: string; authority: string }>(
      "/api/v1/verification/public-key"
    ),
};

export const consentApi = {
  getWallet: (apaarId: string) =>
    apiRequest<ConsentWalletData>(`/api/v1/consent/wallet/${apaarId}`),

  updateWallet: (studentApaarId: string, policies: ConsentPolicy[]) =>
    apiRequest<{ success: boolean; message: string }>("/api/v1/consent/wallet/update", {
      method: "POST",
      body: JSON.stringify({ student_apaar_id: studentApaarId, policies }),
    }),

  requestOtp: (apaarId: string) =>
    apiRequest<{ success: boolean; otp: string; message: string }>(
      `/api/v1/consent/request-otp/${apaarId}`,
      { method: "POST" }
    ),

  getAccessLogs: (apaarId: string) =>
    apiRequest<AccessLogItem[]>(`/api/v1/consent/access-logs/${apaarId}`),
};

export const auditApi = {
  getLogs: (limit = 100) =>
    apiRequest<AuditLogItem[]>(`/api/v1/audit/logs?limit=${limit}`),

  verifyIntegrity: () =>
    apiRequest<AuditIntegrityResult>("/api/v1/audit/verify-integrity"),

  injectTamper: (sequenceNumber = 3) =>
    apiRequest<{ tampered: boolean; sequence_number: number; message: string }>(
      `/api/v1/audit/tamper-demo?sequence_number=${sequenceNumber}`,
      { method: "POST" }
    ),

  restoreTamper: (sequenceNumber = 3) =>
    apiRequest<{ restored: boolean; sequence_number: number; message: string }>(
      `/api/v1/audit/restore-demo?sequence_number=${sequenceNumber}`,
      { method: "POST" }
    ),
};

// Phase 5: Machine Learning & Intelligence Endpoints
export interface AnomalyItem {
  institution_id: string;
  aicte_id: string;
  name: string;
  state: string;
  city: string;
  total_students: number;
  total_intake: number;
  intake_saturation: number;
  surge_ratio: number;
  last_day_clustering: number;
  category_entropy: number;
  sequentiality_ratio: number;
  anomaly_score: number;
  risk_tier: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  explanation: string;
  analyzed_at: string;
}

export interface TrustScoreItem {
  institution_id: string;
  aicte_id: string;
  name: string;
  state: string;
  city: string;
  trust_score: number;
  previous_score: number;
  is_flagged_for_audit: boolean;
  breakdown: {
    data_quality_pts: number;
    data_quality_max: number;
    timeliness_pts: number;
    timeliness_max: number;
    anomaly_pts: number;
    anomaly_max: number;
    resolution_pts: number;
    resolution_max: number;
    total_score: number;
    is_flagged_for_audit: boolean;
    formula_explanation: string;
  };
}

export interface FuzzyDuplicateItem {
  candidate_id: string;
  composite_score: number;
  name_similarity: number;
  tier: string;
  explanation: string;
  record_a: {
    id: string;
    apaar_id: string;
    name: string;
    dob: string;
    gender: string;
    institution_id: string;
    institution_name: string;
    program: string;
    branch: string;
    verification_status: string;
  };
  record_b: {
    id: string;
    apaar_id: string;
    name: string;
    dob: string;
    gender: string;
    institution_id: string;
    institution_name: string;
    program: string;
    branch: string;
    verification_status: string;
  };
  detected_at: string;
}

export interface SeatForecastItem {
  branch_id: string;
  institution_id: string;
  institution_name: string;
  institution_aicte_id: string;
  program_name: string;
  branch_name: string;
  approved_intake: number;
  current_enrolled: number;
  current_capacity_pct: number;
  daily_velocity: number;
  projected_final_enrolment: number;
  projected_capacity_pct: number;
  days_to_breach: number | null;
  risk_status: "BREACHED" | "HIGH_RISK_PROJECTED_BREACH" | "NEAR_CAPACITY_WARNING" | "STABLE";
  is_locked: boolean;
  recommendation: string;
  analyzed_at: string;
}

export const mlApi = {
  getAnomalies: () =>
    apiRequest<AnomalyItem[]>("/api/v1/ml/anomalies"),

  getInstitutionAnomaly: (institutionId: string) =>
    apiRequest<AnomalyItem>(`/api/v1/ml/anomalies/${institutionId}`),

  getTrustScores: () =>
    apiRequest<TrustScoreItem[]>("/api/v1/ml/trust-scores"),

  recalculateTrustScores: () =>
    apiRequest<{ success: boolean; total_institutions_updated: number; leaderboard: TrustScoreItem[] }>(
      "/api/v1/ml/trust-scores/recalculate",
      { method: "POST" }
    ),

  getFuzzyDuplicates: (similarityThreshold = 75.0, limit = 50) =>
    apiRequest<FuzzyDuplicateItem[]>(
      `/api/v1/ml/fuzzy-duplicates?similarity_threshold=${similarityThreshold}&limit=${limit}`
    ),

  openCaseForFuzzy: (payload: {
    candidate_id: string;
    record_a_id: string;
    record_b_id: string;
    reason: string;
  }) =>
    apiRequest<{ success: boolean; case_id: string; case_number: string; message: string }>(
      "/api/v1/ml/fuzzy-duplicates/open-case",
      {
        method: "POST",
        body: JSON.stringify(payload),
      }
    ),

  getSeatForecast: (daysRemaining = 14) =>
    apiRequest<SeatForecastItem[]>(`/api/v1/ml/seat-forecast?days_remaining=${daysRemaining}`),

  toggleSeatLock: (branchId: string, lockState: boolean) =>
    apiRequest<{
      branch_id: string;
      branch_name: string;
      institution_name: string;
      is_locked: boolean;
      message: string;
    }>("/api/v1/ml/seat-lock/toggle", {
      method: "POST",
      body: JSON.stringify({ branch_id: branchId, lock_state: lockState }),
    }),
};

export interface SentinelThought {
  timestamp: string;
  phase: string;
  message: string;
}

export interface SentinelToolExecution {
  tool_name: string;
  input: Record<string, any>;
  output: Record<string, any>;
}

export interface SentinelTriageResult {
  success: boolean;
  batch_id: string;
  institution_name: string;
  status: string;
  executive_summary: string;
  thought_log: SentinelThought[];
  tool_executions: SentinelToolExecution[];
  proposed_approval?: any;
}

export interface SentinelChatMessage {
  query: string;
  answer: string;
  tools_called: string[];
  related_links: Array<{ label: string; href: string }>;
  timestamp: string;
}

export interface SentinelBatchItem {
  id: string;
  filename: string;
  institution_id: string;
  institution_name: string;
  state: string;
  total_records: number;
  valid_records: number;
  flagged_records: number;
  status: string;
  created_at: string;
}

export interface PendingApprovalItem {
  case_id: string;
  case_number: string;
  title: string;
  institution_id: string;
  priority: string;
  status: string;
  description: string;
  proposed_action: string;
  evidence_pack?: Record<string, any>;
  created_at: string;
  sla_deadline?: string;
}

export const sentinelApi = {
  getBatches: (limit = 15) =>
    apiRequest<SentinelBatchItem[]>(`/api/v1/sentinel/batches?limit=${limit}`),

  triageBatch: (batchId?: string) =>
    apiRequest<SentinelTriageResult>("/api/v1/sentinel/triage-batch", {
      method: "POST",
      body: JSON.stringify({ batch_id: batchId }),
    }),

  chat: (message: string, history?: any[]) =>
    apiRequest<SentinelChatMessage>("/api/v1/sentinel/chat", {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),

  getPendingApprovals: () =>
    apiRequest<PendingApprovalItem[]>("/api/v1/sentinel/pending-approvals"),

  decideApproval: (caseId: string, decision: "APPROVE" | "REJECT", officerNotes?: string) =>
    apiRequest<{ success: boolean; decision: string; case_number: string; message: string }>(
      "/api/v1/sentinel/decide-approval",
      {
        method: "POST",
        body: JSON.stringify({
          case_id: caseId,
          decision,
          officer_notes: officerNotes,
        }),
      }
    ),
};

export interface NLQueryResult {
  intent: string;
  title: string;
  sql_translation: string;
  columns: string[];
  rows: Array<Record<string, any>>;
  chart_type: "BAR" | "PIE" | "METRIC" | "TABLE";
  chart_key_x?: string;
  chart_key_y?: string;
  summary_insight: string;
}

export type NationalDashboardData = Record<string, any>;
export type InstitutionDashboardData = Record<string, any>;

export const analyticsApi = {
  getNational: () =>
    apiRequest<NationalDashboardData>("/api/v1/analytics/national"),

  getInstitution: (institutionId?: string) =>
    apiRequest<InstitutionDashboardData>(
      institutionId
        ? `/api/v1/analytics/institution?institution_id=${institutionId}`
        : "/api/v1/analytics/institution"
    ),

  runNLQuery: (query: string) =>
    apiRequest<NLQueryResult>("/api/v1/analytics/nl-query", {
      method: "POST",
      body: JSON.stringify({ query }),
    }),
};

export const exportApi = {
  getTrustScoresUrl: (format: "excel" | "pdf" = "excel") =>
    `${API_BASE}/api/v1/export/trust-scores?format=${format}`,

  getAnomaliesUrl: (format: "excel" | "pdf" = "excel") =>
    `${API_BASE}/api/v1/export/anomalies?format=${format}`,

  getStudentsUrl: (institutionId?: string, maskApaar: boolean = true) =>
    `${API_BASE}/api/v1/export/students?${institutionId ? `institution_id=${institutionId}&` : ""}mask_apaar=${maskApaar}&format=csv`,
};



