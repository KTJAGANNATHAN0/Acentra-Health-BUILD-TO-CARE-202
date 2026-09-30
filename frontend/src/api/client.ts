import type {
  FraudFlagDetail,
  FraudStats,
  PaginatedFlags,
  RuleConfig,
  FraudFlag
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

// Realistic in-browser fallback dataset for static GitHub Pages / offline deployments
let mockFlags: FraudFlag[] = [
  {
    id: 5,
    transaction_id: "c8f12a34-7b90-4c12-8e31-9a7412f518e1",
    score: 100,
    status: "PENDING",
    notified_at: new Date(Date.now() - 5 * 60000).toISOString(),
    created_at: new Date(Date.now() - 5 * 60000).toISOString(),
    updated_at: new Date(Date.now() - 5 * 60000).toISOString(),
    transaction: {
      id: "c8f12a34-7b90-4c12-8e31-9a7412f518e1",
      account_id: "acc_fraud_combo_01",
      amount: 9200.00,
      currency: "EUR",
      merchant: "Galeries Lafayette Paris",
      lat: 48.8566,
      lon: 2.3522,
      country: "FR",
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      risk_score: 100,
      created_at: new Date(Date.now() - 5 * 60000).toISOString(),
      rule_results: [
        {
          rule_name: "impossible_travel",
          triggered: true,
          score: 90,
          reason: "Impossible travel: 8,970 km traversed in 0.42h implies 21,357 km/h (exceeds 900 km/h commercial limit)",
          evidence: {
            distance_km: 8970.4,
            elapsed_hours: 0.42,
            elapsed_minutes: 25.0,
            implied_speed_kmh: 21357.1,
            speed_limit_kmh: 900.0,
            previous_location: {
              country: "US",
              merchant: "San Francisco Diner",
              lat: 37.7749,
              lon: -122.4194,
              timestamp: new Date(Date.now() - 30 * 60000).toISOString()
            },
            current_location: {
              country: "FR",
              merchant: "Galeries Lafayette Paris",
              lat: 48.8566,
              lon: 2.3522,
              timestamp: new Date(Date.now() - 5 * 60000).toISOString()
            }
          }
        },
        {
          rule_name: "unusual_amount",
          triggered: true,
          score: 95,
          reason: "Statistically anomalous amount: $9,200.00 has z-score of 4.85 (exceeds 3.0 std threshold; 30d mean: $35.00, std: $12.40)",
          evidence: {
            amount: 9200.00,
            mean: 35.00,
            std: 12.40,
            z_score: 4.85,
            k_threshold: 3.0,
            mode: "z_score"
          }
        },
        {
          rule_name: "velocity",
          triggered: false,
          score: 0,
          reason: "Velocity normal: 2 transactions in 10m (limit 5)",
          evidence: { total_count: 2, threshold_max_count: 5, window_minutes: 10 }
        }
      ]
    }
  },
  {
    id: 4,
    transaction_id: "d9a41b52-1c23-4e89-9a01-2b6381c940a2",
    score: 100,
    status: "REVIEWED",
    reviewed_by: "sarah.chen@fraud-ops.com",
    reviewed_at: new Date(Date.now() - 12 * 60000).toISOString(),
    review_note: "Confirmed compromised card token. Card blocked and customer notified.",
    notified_at: new Date(Date.now() - 15 * 60000).toISOString(),
    created_at: new Date(Date.now() - 15 * 60000).toISOString(),
    updated_at: new Date(Date.now() - 12 * 60000).toISOString(),
    transaction: {
      id: "d9a41b52-1c23-4e89-9a01-2b6381c940a2",
      account_id: "acc_fraud_travel_77",
      amount: 650.00,
      currency: "GBP",
      merchant: "Harrods Department Store London",
      lat: 51.5074,
      lon: -0.1278,
      country: "GB",
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      risk_score: 90,
      created_at: new Date(Date.now() - 15 * 60000).toISOString(),
      rule_results: [
        {
          rule_name: "impossible_travel",
          triggered: true,
          score: 90,
          reason: "Impossible travel: 5,570 km traversed in 0.30h implies 18,566 km/h (exceeds 900 km/h limit)",
          evidence: {
            distance_km: 5570.0,
            elapsed_hours: 0.30,
            elapsed_minutes: 18.0,
            implied_speed_kmh: 18566.7,
            speed_limit_kmh: 900.0,
            previous_location: {
              country: "US",
              merchant: "Manhattan Cafe",
              lat: 40.7128,
              lon: -74.0060,
              timestamp: new Date(Date.now() - 33 * 60000).toISOString()
            },
            current_location: {
              country: "GB",
              merchant: "Harrods London",
              lat: 51.5074,
              lon: -0.1278,
              timestamp: new Date(Date.now() - 15 * 60000).toISOString()
            }
          }
        }
      ]
    }
  },
  {
    id: 3,
    transaction_id: "e1f72b90-3a45-4c67-8b12-5c8914d720b3",
    score: 85,
    status: "PENDING",
    notified_at: new Date(Date.now() - 45 * 60000).toISOString(),
    created_at: new Date(Date.now() - 45 * 60000).toISOString(),
    updated_at: new Date(Date.now() - 45 * 60000).toISOString(),
    transaction: {
      id: "e1f72b90-3a45-4c67-8b12-5c8914d720b3",
      account_id: "acc_fraud_amount_99",
      amount: 4850.00,
      currency: "USD",
      merchant: "Rolex Geneva Online Store",
      lat: 34.0522,
      lon: -118.2437,
      country: "US",
      timestamp: new Date(Date.now() - 45 * 60000).toISOString(),
      risk_score: 85,
      created_at: new Date(Date.now() - 45 * 60000).toISOString(),
      rule_results: [
        {
          rule_name: "unusual_amount",
          triggered: true,
          score: 85,
          reason: "Statistically anomalous amount: $4,850.00 has z-score of 4.12 (exceeds 3.0 std threshold; 30d mean: $32.00, std: $8.50)",
          evidence: {
            amount: 4850.00,
            mean: 32.00,
            std: 8.50,
            z_score: 4.12,
            k_threshold: 3.0,
            mode: "z_score"
          }
        }
      ]
    }
  },
  {
    id: 2,
    transaction_id: "f2a83c01-4b56-4d78-9c23-6d9025e831c4",
    score: 70,
    status: "PENDING",
    created_at: new Date(Date.now() - 60 * 60000).toISOString(),
    updated_at: new Date(Date.now() - 60 * 60000).toISOString(),
    transaction: {
      id: "f2a83c01-4b56-4d78-9c23-6d9025e831c4",
      account_id: "acc_fraud_velocity_88",
      amount: 79.99,
      currency: "USD",
      merchant: "Digital Goods Store #7",
      lat: 37.7749,
      lon: -122.4194,
      country: "US",
      timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
      risk_score: 70,
      created_at: new Date(Date.now() - 60 * 60000).toISOString(),
      rule_results: [
        {
          rule_name: "velocity",
          triggered: true,
          score: 70,
          reason: "High velocity: account executed 7 transactions in 10 minutes (limit: 5)",
          evidence: {
            total_count: 7,
            threshold_max_count: 5,
            window_minutes: 10,
            overage: 2
          }
        }
      ]
    }
  }
];

let mockAuditLogs = [
  {
    id: 1,
    entity: "fraud_flag",
    entity_id: "4",
    action: "STATUS_CHANGE_REVIEWED",
    actor: "sarah.chen@fraud-ops.com",
    payload: { note: "Confirmed compromised card token. Card blocked and customer notified." },
    created_at: new Date(Date.now() - 12 * 60000).toISOString()
  },
  {
    id: 2,
    entity: "fraud_flag",
    entity_id: "5",
    action: "ALERT_DISPATCHED",
    actor: "notification_service",
    payload: { notifier: "SNS", score: 100 },
    created_at: new Date(Date.now() - 5 * 60000).toISOString()
  }
];

let mockRules: RuleConfig[] = [
  {
    rule_name: "velocity",
    enabled: true,
    weight: 1.0,
    params: { max_count: 5, window_minutes: 10 }
  },
  {
    rule_name: "unusual_amount",
    enabled: true,
    weight: 1.0,
    params: { k_std: 3.0, thin_multiplier: 3.0, thin_threshold: 5 }
  },
  {
    rule_name: "impossible_travel",
    enabled: true,
    weight: 1.0,
    params: { speed_limit_kmh: 900.0, min_distance_km: 50.0 }
  }
];

export async function fetchFlags(params: {
  status?: string;
  min_score?: number;
  max_score?: number;
  account_id?: string;
  sort_by?: string;
  sort_dir?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedFlags> {
  try {
    const query = new URLSearchParams();
    if (params.status && params.status !== 'ALL') query.set('status', params.status);
    if (params.min_score !== undefined) query.set('min_score', params.min_score.toString());
    if (params.max_score !== undefined) query.set('max_score', params.max_score.toString());
    if (params.account_id) query.set('account_id', params.account_id);
    if (params.sort_by) query.set('sort_by', params.sort_by);
    if (params.sort_dir) query.set('sort_dir', params.sort_dir);
    if (params.page) query.set('page', params.page.toString());
    if (params.page_size) query.set('page_size', params.page_size.toString());

    const res = await fetch(`${API_BASE}/flags?${query.toString()}`);
    if (res.ok) {
      return await res.json();
    }
  } catch {
    // Fall through to in-browser demo state if API endpoint is not reachable
  }

  // Filter in-memory flags
  let filtered = [...mockFlags];
  if (params.status && params.status !== 'ALL') {
    filtered = filtered.filter(f => f.status === params.status);
  }
  if (params.min_score !== undefined) {
    filtered = filtered.filter(f => f.score >= (params.min_score || 0));
  }
  if (params.account_id) {
    filtered = filtered.filter(f => f.transaction?.account_id.toLowerCase().includes((params.account_id || '').toLowerCase()));
  }

  return {
    items: filtered,
    total: filtered.length,
    page: params.page || 1,
    page_size: params.page_size || 15,
    total_pages: 1
  };
}

export async function fetchFlagDetail(flagId: number): Promise<FraudFlagDetail> {
  try {
    const res = await fetch(`${API_BASE}/flags/${flagId}`);
    if (res.ok) {
      return await res.json();
    }
  } catch {}

  const flag = mockFlags.find(f => f.id === flagId) || mockFlags[0];
  const logs = mockAuditLogs.filter(l => l.entity_id === String(flagId));

  return {
    flag,
    rule_results: flag.transaction?.rule_results || [],
    audit_logs: logs
  };
}

export async function updateFlagStatus(
  flagId: number,
  status: 'REVIEWED' | 'CLEARED' | 'PENDING',
  note?: string,
  reviewer?: string
): Promise<FraudFlag> {
  try {
    const res = await fetch(`${API_BASE}/flags/${flagId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note, reviewer })
    });
    if (res.ok) {
      return await res.json();
    }
  } catch {}

  const flag = mockFlags.find(f => f.id === flagId);
  if (flag) {
    flag.status = status;
    flag.reviewed_by = reviewer || "analyst";
    flag.reviewed_at = new Date().toISOString();
    flag.review_note = note || null;
    flag.updated_at = new Date().toISOString();
    mockAuditLogs.unshift({
      id: Date.now(),
      entity: "fraud_flag",
      entity_id: String(flagId),
      action: `STATUS_CHANGE_${status}`,
      actor: reviewer || "analyst",
      payload: { note: note || "" },
      created_at: new Date().toISOString()
    });
    return flag;
  }
  throw new Error("Flag not found");
}

export async function fetchRules(): Promise<RuleConfig[]> {
  try {
    const res = await fetch(`${API_BASE}/rules`);
    if (res.ok) return await res.json();
  } catch {}
  return mockRules;
}

export async function updateRule(
  ruleName: string,
  payload: { enabled?: boolean; weight?: number; params?: Record<string, any> }
): Promise<RuleConfig> {
  try {
    const res = await fetch(`${API_BASE}/rules/${ruleName}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch {}

  const rule = mockRules.find(r => r.rule_name === ruleName);
  if (rule) {
    if (payload.enabled !== undefined) rule.enabled = payload.enabled;
    if (payload.weight !== undefined) rule.weight = payload.weight;
    if (payload.params) rule.params = { ...rule.params, ...payload.params };
    return rule;
  }
  throw new Error("Rule not found");
}

export async function fetchStats(): Promise<FraudStats> {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    if (res.ok) return await res.json();
  } catch {}

  const totalFlagged = mockFlags.length;
  const pending = mockFlags.filter(f => f.status === 'PENDING').length;
  const reviewed = mockFlags.filter(f => f.status === 'REVIEWED').length;
  const cleared = mockFlags.filter(f => f.status === 'CLEARED').length;
  const highRisk = mockFlags.filter(f => (f.score || 0) >= 80).length;

  return {
    total_transactions: 58,
    total_flagged: totalFlagged,
    pending_flags: pending,
    reviewed_flags: reviewed,
    cleared_flags: cleared,
    high_risk_alerts_sent: highRisk,
    avg_risk_score: 8.5,
    rule_trigger_counts: {
      impossible_travel: 2,
      unusual_amount: 3,
      velocity: 2
    }
  };
}

export async function reEvaluateTransaction(txnId: string) {
  try {
    const res = await fetch(`${API_BASE}/transactions/${txnId}/re-evaluate`, {
      method: 'POST'
    });
    if (res.ok) return await res.json();
  } catch {}
  return { success: true };
}

export async function triggerScenario(scenarioName: string) {
  try {
    const res = await fetch(`${API_BASE}/simulator/scenario/${scenarioName}`, {
      method: 'POST'
    });
    if (res.ok) return await res.json();
  } catch {}

  // In-memory simulation fallback
  const newId = mockFlags.length + 1;
  const newFlag: FraudFlag = {
    id: newId,
    transaction_id: `sim-${Date.now()}`,
    score: scenarioName === 'impossible_travel' ? 90 : scenarioName === 'amount_spike' ? 85 : 70,
    status: 'PENDING',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    transaction: {
      id: `sim-${Date.now()}`,
      account_id: `sim_${scenarioName}_${Math.floor(Math.random() * 900 + 100)}`,
      amount: scenarioName === 'amount_spike' ? 5400.00 : 85.00,
      currency: "USD",
      merchant: scenarioName === 'impossible_travel' ? "Fifth Avenue NYC" : "Digital Store",
      lat: 40.7128,
      lon: -74.0060,
      country: "US",
      timestamp: new Date().toISOString(),
      risk_score: scenarioName === 'impossible_travel' ? 90 : 70,
      created_at: new Date().toISOString(),
      rule_results: [
        {
          rule_name: scenarioName === 'impossible_travel' ? 'impossible_travel' : scenarioName === 'amount_spike' ? 'unusual_amount' : 'velocity',
          triggered: true,
          score: scenarioName === 'impossible_travel' ? 90 : 70,
          reason: `Simulated attack scenario: ${scenarioName}`,
          evidence: { simulated: true }
        }
      ]
    }
  };
  mockFlags.unshift(newFlag);

  return {
    transaction: newFlag.transaction,
    risk_score: newFlag.score,
    decision: newFlag.score >= 80 ? "HIGH_RISK_ALERT" : "FLAGGED_FOR_REVIEW",
    high_risk: newFlag.score >= 80,
    flagged: true,
    rule_results: newFlag.transaction?.rule_results
  };
}

export async function submitTransaction(payload: {
  account_id: string;
  amount: number;
  merchant: string;
  currency?: string;
  lat?: number;
  lon?: number;
  country?: string;
}) {
  try {
    const res = await fetch(`${API_BASE}/transactions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (res.ok) return await res.json();
  } catch {}

  const score = payload.amount > 5000 ? 80 : 0;
  return {
    transaction: {
      id: `txn-${Date.now()}`,
      account_id: payload.account_id,
      amount: payload.amount,
      currency: payload.currency || "USD",
      merchant: payload.merchant,
      risk_score: score,
      created_at: new Date().toISOString(),
      timestamp: new Date().toISOString()
    },
    risk_score: score,
    flagged: score >= 50,
    high_risk: score >= 80,
    decision: score >= 80 ? "HIGH_RISK_ALERT" : score >= 50 ? "FLAGGED_FOR_REVIEW" : "ALLOW",
    rule_results: []
  };
}

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) return await res.json();
  } catch {}

  return {
    status: "healthy",
    service: "Accentra Fraud Rule Engine",
    rules_registered: ["unusual_amount", "impossible_travel", "velocity"],
    notifier: "log",
    flag_threshold: 50,
    high_risk_threshold: 80
  };
}
