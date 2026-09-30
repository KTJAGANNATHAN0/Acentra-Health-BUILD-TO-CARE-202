export interface RuleResult {
  rule_name: string;
  triggered: boolean;
  score: number;
  reason: string;
  evidence: Record<string, any>;
}

export interface Transaction {
  id: string;
  account_id: string;
  amount: number;
  currency: string;
  merchant: string;
  lat?: number | null;
  lon?: number | null;
  country?: string | null;
  timestamp: string;
  risk_score: number;
  created_at: string;
  rule_results?: RuleResult[];
}

export type FlagStatus = 'PENDING' | 'REVIEWED' | 'CLEARED';

export interface FraudFlag {
  id: number;
  transaction_id: string;
  score: number;
  status: FlagStatus;
  notified_at?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  review_note?: string | null;
  created_at: string;
  updated_at: string;
  transaction?: Transaction;
}

export interface AuditLog {
  id: number;
  entity: string;
  entity_id: string;
  action: string;
  actor: string;
  payload: Record<string, any>;
  created_at: string;
}

export interface FraudFlagDetail {
  flag: FraudFlag;
  rule_results: RuleResult[];
  audit_logs: AuditLog[];
}

export interface RuleConfig {
  rule_name: string;
  enabled: boolean;
  params: Record<string, any>;
  weight: number;
  updated_at?: string;
}

export interface FraudStats {
  total_transactions: number;
  total_flagged: number;
  pending_flags: number;
  reviewed_flags: number;
  cleared_flags: number;
  high_risk_alerts_sent: number;
  avg_risk_score: number;
  rule_trigger_counts: Record<string, number>;
}

export interface PaginatedFlags {
  items: FraudFlag[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
