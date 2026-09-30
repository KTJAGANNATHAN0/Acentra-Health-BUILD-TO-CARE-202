import React, { useState } from 'react';
import { X, Play, Zap, Globe, DollarSign, CheckCircle2, Send, Flame, AlertCircle } from 'lucide-react';

interface TransactionSimulatorModalProps {
  onClose: () => void;
  onTriggerScenario: (name: string) => Promise<any>;
  onSubmitCustom: (payload: any) => Promise<any>;
}

export const TransactionSimulatorModal: React.FC<TransactionSimulatorModalProps> = ({
  onClose,
  onTriggerScenario,
  onSubmitCustom
}) => {
  const [runningScenario, setRunningScenario] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<any | null>(null);

  // Custom Form State
  const [accountId, setAccountId] = useState('acc_test_custom');
  const [amount, setAmount] = useState('150.00');
  const [merchant, setMerchant] = useState('Apple Store Regent St');
  const [currency, setCurrency] = useState('USD');
  const [lat, setLat] = useState('51.5133');
  const [lon, setLon] = useState('-0.1419');
  const [country, setCountry] = useState('GB');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleScenario = async (name: string) => {
    setRunningScenario(name);
    setLastResult(null);
    try {
      const res = await onTriggerScenario(name);
      setLastResult(res);
    } finally {
      setRunningScenario(null);
    }
  };

  const handleCustomSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setLastResult(null);
    try {
      const res = await onSubmitCustom({
        account_id: accountId,
        amount: parseFloat(amount),
        merchant,
        currency,
        lat: lat ? parseFloat(lat) : null,
        lon: lon ? parseFloat(lon) : null,
        country
      });
      setLastResult(res);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 24px',
          borderBottom: '1px solid var(--border-subtle)',
          background: 'rgba(15, 23, 42, 0.4)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '8px',
              background: 'rgba(99, 102, 241, 0.2)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#818cf8'
            }}>
              <Play size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Transaction &amp; Fraud Simulator</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Inject real-time transactions or simulate attack vectors against the rule engine
              </p>
            </div>
          </div>
          <button className="btn btn-secondary" style={{ padding: '6px' }} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Preset Fraud Scenarios */}
          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)', marginBottom: '12px' }}>
              One-Click Fraud Attack Presets
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
              {/* Velocity Burst */}
              <button
                id="btn-sim-velocity"
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '14px',
                  background: 'rgba(245, 158, 11, 0.08)',
                  borderColor: 'rgba(245, 158, 11, 0.25)',
                  textAlign: 'left'
                }}
                onClick={() => handleScenario('velocity_burst')}
                disabled={!!runningScenario}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fbbf24', fontWeight: 700, marginBottom: '4px' }}>
                  <Zap size={16} />
                  Velocity Burst
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Generates 6 quick transactions within 4 minutes
                </span>
              </button>

              {/* Impossible Travel */}
              <button
                id="btn-sim-travel"
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '14px',
                  background: 'rgba(244, 63, 94, 0.08)',
                  borderColor: 'rgba(244, 63, 94, 0.25)',
                  textAlign: 'left'
                }}
                onClick={() => handleScenario('impossible_travel')}
                disabled={!!runningScenario}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fda4af', fontWeight: 700, marginBottom: '4px' }}>
                  <Globe size={16} />
                  Impossible Travel
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Tokyo &rarr; New York in 10 mins (64,000 km/h)
                </span>
              </button>

              {/* Amount Anomaly */}
              <button
                id="btn-sim-amount"
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '14px',
                  background: 'rgba(56, 189, 248, 0.08)',
                  borderColor: 'rgba(56, 189, 248, 0.25)',
                  textAlign: 'left'
                }}
                onClick={() => handleScenario('amount_spike')}
                disabled={!!runningScenario}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#7dd3fc', fontWeight: 700, marginBottom: '4px' }}>
                  <DollarSign size={16} />
                  Amount Anomaly
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  $5,400 diamond purchase on a $20 regular history
                </span>
              </button>

              {/* Normal Traffic */}
              <button
                id="btn-sim-normal"
                className="btn btn-secondary"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  padding: '14px',
                  background: 'rgba(16, 185, 129, 0.08)',
                  borderColor: 'rgba(16, 185, 129, 0.25)',
                  textAlign: 'left'
                }}
                onClick={() => handleScenario('normal')}
                disabled={!!runningScenario}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#6ee7b7', fontWeight: 700, marginBottom: '4px' }}>
                  <CheckCircle2 size={16} />
                  Normal Purchase
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Routine $35 grocery store transaction
                </span>
              </button>
            </div>
          </div>

          {/* Results Card if Available */}
          {lastResult && (
            <div style={{
              background: lastResult.high_risk 
                ? 'rgba(244, 63, 94, 0.12)' 
                : lastResult.flagged 
                ? 'rgba(245, 158, 11, 0.12)' 
                : 'rgba(16, 185, 129, 0.12)',
              border: `1px solid ${lastResult.high_risk ? '#f43f5e' : lastResult.flagged ? '#f59e0b' : '#10b981'}`,
              borderRadius: '10px',
              padding: '16px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 700, fontSize: '1rem' }}>
                  {lastResult.high_risk ? <Flame color="#f43f5e" size={20} /> : lastResult.flagged ? <AlertCircle color="#f59e0b" size={20} /> : <CheckCircle2 color="#10b981" size={20} />}
                  Decision: {lastResult.decision}
                </div>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, fontSize: '1.1rem' }}>
                  Risk Score: {lastResult.risk_score}/100
                </div>
              </div>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                Transaction ID: <code>{lastResult.transaction.id}</code> &bull; Account: <strong>{lastResult.transaction.account_id}</strong> &bull; Amount: ${lastResult.transaction.amount}
              </p>
              {lastResult.rule_results && (
                <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {lastResult.rule_results.map((r: any) => (
                    <span key={r.rule_name} className={r.triggered ? 'status-chip pending' : 'status-chip cleared'}>
                      {r.rule_name}: {r.triggered ? `Triggered (score ${r.score})` : 'Pass'}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Manual Transaction Injection Form */}
          <form onSubmit={handleCustomSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
              Or Ingest Custom Transaction (POST /api/transactions)
            </h3>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '12px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Account ID</label>
                <input
                  type="text"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={accountId}
                  onChange={(e) => setAccountId(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Amount</label>
                <input
                  type="number"
                  step="0.01"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Currency</label>
                <input
                  type="text"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  maxLength={3}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Merchant</label>
                <input
                  type="text"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={merchant}
                  onChange={(e) => setMerchant(e.target.value)}
                  required
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Latitude</label>
                <input
                  type="number"
                  step="0.0001"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Longitude</label>
                <input
                  type="number"
                  step="0.0001"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={lon}
                  onChange={(e) => setLon(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Country</label>
                <input
                  type="text"
                  className="input-control"
                  style={{ width: '100%' }}
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '6px' }}>
              <button
                id="btn-submit-custom-txn"
                type="submit"
                className="btn btn-primary"
                disabled={isSubmitting}
              >
                <Send size={16} />
                Evaluate Transaction
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
