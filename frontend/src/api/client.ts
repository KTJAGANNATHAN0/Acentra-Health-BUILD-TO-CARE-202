import type {
  FraudFlagDetail,
  FraudStats,
  PaginatedFlags,
  RuleConfig,
  FraudFlag
} from '../types';

const API_BASE = '/api';

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
  if (!res.ok) throw new Error(`Failed to fetch flags: ${res.statusText}`);
  return res.json();
}

export async function fetchFlagDetail(flagId: number): Promise<FraudFlagDetail> {
  const res = await fetch(`${API_BASE}/flags/${flagId}`);
  if (!res.ok) throw new Error(`Failed to fetch flag detail: ${res.statusText}`);
  return res.json();
}

export async function updateFlagStatus(
  flagId: number,
  status: 'REVIEWED' | 'CLEARED' | 'PENDING',
  note?: string,
  reviewer?: string
): Promise<FraudFlag> {
  const res = await fetch(`${API_BASE}/flags/${flagId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ status, note, reviewer })
  });
  if (!res.ok) throw new Error(`Failed to update flag status: ${res.statusText}`);
  return res.json();
}

export async function fetchRules(): Promise<RuleConfig[]> {
  const res = await fetch(`${API_BASE}/rules`);
  if (!res.ok) throw new Error(`Failed to fetch rules: ${res.statusText}`);
  return res.json();
}

export async function updateRule(
  ruleName: string,
  payload: { enabled?: boolean; weight?: number; params?: Record<string, any> }
): Promise<RuleConfig> {
  const res = await fetch(`${API_BASE}/rules/${ruleName}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to update rule: ${res.statusText}`);
  return res.json();
}

export async function fetchStats(): Promise<FraudStats> {
  const res = await fetch(`${API_BASE}/stats`);
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.statusText}`);
  return res.json();
}

export async function reEvaluateTransaction(txnId: string) {
  const res = await fetch(`${API_BASE}/transactions/${txnId}/re-evaluate`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(`Failed to re-evaluate transaction: ${res.statusText}`);
  return res.json();
}

export async function triggerScenario(scenarioName: string) {
  const res = await fetch(`${API_BASE}/simulator/scenario/${scenarioName}`, {
    method: 'POST'
  });
  if (!res.ok) throw new Error(`Failed to run scenario: ${res.statusText}`);
  return res.json();
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
  const res = await fetch(`${API_BASE}/transactions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  if (!res.ok) throw new Error(`Failed to submit transaction: ${res.statusText}`);
  return res.json();
}

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}
