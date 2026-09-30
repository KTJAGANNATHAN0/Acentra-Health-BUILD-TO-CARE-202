import React, { useState } from 'react';
import { 
  X, 
  RotateCw, 
  Flame, 
  AlertTriangle, 
  MapPin, 
  Navigation, 
  ShieldCheck, 
  History,
  FileText
} from 'lucide-react';
import type { FraudFlagDetail, FlagStatus } from '../types';

interface FlagDetailModalProps {
  detail: FraudFlagDetail;
  onClose: () => void;
  onUpdateStatus: (flagId: number, status: FlagStatus, note: string) => Promise<void>;
  onReEvaluate: (txnId: string) => Promise<void>;
  isUpdating: boolean;
}

export const FlagDetailModal: React.FC<FlagDetailModalProps> = ({
  detail,
  onClose,
  onUpdateStatus,
  onReEvaluate,
  isUpdating
}) => {
  const { flag, rule_results, audit_logs } = detail;
  const txn = flag.transaction;

  const [note, setNote] = useState('');
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const [activeTab, setActiveTab] = useState<'evidence' | 'audit'>('evidence');

  const isHighRisk = flag.score >= 80;

  const handleAction = async (newStatus: FlagStatus) => {
    if (newStatus === 'CLEARED' && !showClearConfirm) {
      setShowClearConfirm(true);
      return;
    }
    await onUpdateStatus(flag.id, newStatus, note);
    setShowClearConfirm(false);
  };

  const geoRule = rule_results.find(r => r.rule_name === 'impossible_travel');
  const geoEvidence = geoRule?.evidence;

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
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <div className={`score-badge ${flag.score >= 80 ? 'high' : flag.score >= 50 ? 'medium' : 'low'}`} style={{ fontSize: '1.1rem', padding: '6px 14px' }}>
              {isHighRisk && <Flame size={16} style={{ marginRight: '6px' }} />}
              Score {flag.score}
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                Flag #{flag.id} &bull; Account: {txn?.account_id}
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Transaction ID: {txn?.id}
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <button 
              id="btn-modal-reevaluate"
              className="btn btn-secondary"
              style={{ fontSize: '0.8rem', padding: '6px 12px' }}
              onClick={() => txn && onReEvaluate(txn.id)}
              disabled={isUpdating}
              title="FR-12: Re-run engine against this transaction with current rules"
            >
              <RotateCw size={14} className={isUpdating ? 'spin-anim' : ''} />
              Re-evaluate
            </button>
            <button 
              id="btn-close-modal"
              className="btn btn-secondary" 
              style={{ padding: '6px' }} 
              onClick={onClose}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Transaction Metadata Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            background: 'rgba(0,0,0,0.25)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '10px',
            padding: '16px'
          }}>
            <div>
              <span className="location-label">Amount</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                ${txn?.amount?.toFixed(2)} {txn?.currency}
              </div>
            </div>
            <div>
              <span className="location-label">Merchant</span>
              <div style={{ fontWeight: 600 }}>{txn?.merchant}</div>
            </div>
            <div>
              <span className="location-label">Location</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.9rem' }}>
                <MapPin size={14} color="#f43f5e" />
                {txn?.country || 'Unknown'} {txn?.lat ? `(${txn.lat.toFixed(2)}, ${txn.lon?.toFixed(2)})` : ''}
              </div>
            </div>
            <div>
              <span className="location-label">Timestamp</span>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                {txn ? new Date(txn.timestamp).toLocaleString() : 'N/A'}
              </div>
            </div>
            <div>
              <span className="location-label">Status</span>
              <div>
                <span className={`status-chip ${flag.status.toLowerCase()}`}>
                  {flag.status}
                </span>
              </div>
            </div>
          </div>

          {/* Navigation Tabs between Evidence & Audit History */}
          <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--border-subtle)' }}>
            <button
              id="tab-evidence"
              className="btn"
              style={{
                borderRadius: '8px 8px 0 0',
                borderBottom: activeTab === 'evidence' ? '2px solid var(--primary)' : 'none',
                color: activeTab === 'evidence' ? 'var(--text-primary)' : 'var(--text-muted)',
                background: 'transparent'
              }}
              onClick={() => setActiveTab('evidence')}
            >
              <FileText size={16} />
              Triggered Rule Evidence ({rule_results.filter(r => r.triggered).length})
            </button>
            <button
              id="tab-audit"
              className="btn"
              style={{
                borderRadius: '8px 8px 0 0',
                borderBottom: activeTab === 'audit' ? '2px solid var(--primary)' : 'none',
                color: activeTab === 'audit' ? 'var(--text-primary)' : 'var(--text-muted)',
                background: 'transparent'
              }}
              onClick={() => setActiveTab('audit')}
            >
              <History size={16} />
              Audit Log Trail ({audit_logs.length})
            </button>
          </div>

          {/* TAB 1: Evidence */}
          {activeTab === 'evidence' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* Impossible Travel Mini Route Map Card (if triggered) */}
              {geoEvidence && geoEvidence.previous_location && (
                <div className="geo-visualizer">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#fda4af', fontWeight: 600 }}>
                    <Navigation size={18} color="#f43f5e" />
                    Impossible Travel Kinematics Analysis
                  </div>

                  <div className="route-container">
                    <div className="location-node">
                      <span className="location-label">Prior Transaction</span>
                      <span className="location-title">
                        {geoEvidence.previous_location.country || 'Origin'} &bull; {geoEvidence.previous_location.merchant}
                      </span>
                      <span className="location-coords">
                        Lat: {geoEvidence.previous_location.lat?.toFixed(3)}, Lon: {geoEvidence.previous_location.lon?.toFixed(3)}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {new Date(geoEvidence.previous_location.timestamp).toLocaleTimeString()}
                      </span>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '0 16px' }}>
                      <span style={{ fontSize: '0.75rem', color: '#f43f5e', fontWeight: 700 }}>
                        &mdash;&mdash; {geoEvidence.distance_km} km &rarr;
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        in {geoEvidence.elapsed_minutes || (geoEvidence.elapsed_hours * 60).toFixed(0)} mins
                      </span>
                    </div>

                    <div className="location-node" style={{ textAlign: 'right' }}>
                      <span className="location-label">Current Flagged Transaction</span>
                      <span className="location-title">
                        {geoEvidence.current_location.country || 'Destination'} &bull; {geoEvidence.current_location.merchant}
                      </span>
                      <span className="location-coords">
                        Lat: {geoEvidence.current_location.lat?.toFixed(3)}, Lon: {geoEvidence.current_location.lon?.toFixed(3)}
                      </span>
                      <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                        {new Date(geoEvidence.current_location.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>

                  <div className="speed-metric-banner">
                    <div>
                      <span className="location-label">Implied Speed</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f43f5e', fontFamily: 'var(--font-mono)' }}>
                        {geoEvidence.implied_speed_kmh?.toLocaleString()} km/h
                      </div>
                    </div>
                    <div>
                      <span className="location-label">Commercial Flight Limit</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {geoEvidence.speed_limit_kmh} km/h
                      </div>
                    </div>
                    <div>
                      <span className="location-label">Velocity Ratio</span>
                      <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f43f5e', fontFamily: 'var(--font-mono)' }}>
                        {(geoEvidence.implied_speed_kmh / geoEvidence.speed_limit_kmh).toFixed(1)}x Limit
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Per-Rule Results */}
              {rule_results.map(rule => (
                <div 
                  key={rule.rule_name}
                  style={{
                    background: rule.triggered ? 'rgba(244, 63, 94, 0.05)' : 'rgba(255, 255, 255, 0.02)',
                    border: `1px solid ${rule.triggered ? 'rgba(244, 63, 94, 0.25)' : 'var(--border-subtle)'}`,
                    borderRadius: '10px',
                    padding: '16px'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontWeight: 700, textTransform: 'capitalize', color: rule.triggered ? '#fda4af' : 'var(--text-primary)' }}>
                        {rule.rule_name.replace('_', ' ')} Rule
                      </span>
                      <span className={rule.triggered ? 'status-chip pending' : 'status-chip cleared'}>
                        {rule.triggered ? 'Triggered' : 'Passed'}
                      </span>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: rule.triggered ? '#fda4af' : 'var(--text-muted)' }}>
                      Score: {rule.score}
                    </div>
                  </div>

                  <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '10px' }}>
                    {rule.reason}
                  </p>

                  {/* Evidence JSON inspector */}
                  {rule.evidence && Object.keys(rule.evidence).length > 0 && (
                    <details style={{ fontSize: '0.75rem', background: 'rgba(0,0,0,0.3)', borderRadius: '6px', padding: '8px' }}>
                      <summary style={{ cursor: 'pointer', color: 'var(--text-muted)' }}>
                        View Raw Evidence Signals
                      </summary>
                      <pre style={{ marginTop: '8px', overflowX: 'auto', color: '#93c5fd' }}>
                        {JSON.stringify(rule.evidence, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* TAB 2: Audit Log History */}
          {activeTab === 'audit' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {audit_logs.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)' }}>
                  No audit log entries recorded yet.
                </div>
              ) : (
                audit_logs.map(log => (
                  <div 
                    key={log.id} 
                    style={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      border: '1px solid var(--border-subtle)',
                      borderRadius: '8px',
                      padding: '12px 16px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '4px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, color: '#38bdf8', fontSize: '0.85rem' }}>
                        {log.action}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Actor: <strong style={{ color: 'var(--text-primary)' }}>{log.actor}</strong>
                    </div>
                    {log.payload && Object.keys(log.payload).length > 0 && (
                      <pre style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'rgba(0,0,0,0.2)', padding: '6px', borderRadius: '4px', marginTop: '4px' }}>
                        {JSON.stringify(log.payload)}
                      </pre>
                    )}
                  </div>
                ))
              )}
            </div>
          )}

          {/* Reviewer Action Resolution Panel (FR-10) */}
          <div style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px'
          }}>
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <ShieldCheck size={18} color="var(--primary)" />
              Resolution &amp; Review Action (FR-10)
            </h3>

            <div>
              <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '6px' }}>
                Reviewer Note / Justification (Audit Logged)
              </label>
              <textarea
                id="input-reviewer-note"
                className="input-control"
                style={{ width: '100%', minHeight: '64px', resize: 'vertical' }}
                placeholder="e.g. Cardholder confirmed legitimate travel to London; cleared flag."
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
            </div>

            {/* Confirmation Box for CLEAR */}
            {showClearConfirm && (
              <div style={{
                background: 'rgba(245, 158, 11, 0.15)',
                border: '1px solid rgba(245, 158, 11, 0.4)',
                borderRadius: '8px',
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#fcd34d', fontSize: '0.85rem' }}>
                  <AlertTriangle size={18} />
                  <span>Are you sure you want to <strong>CLEAR</strong> this fraud flag?</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <button 
                    id="btn-confirm-clear"
                    className="btn btn-danger" 
                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                    onClick={() => handleAction('CLEARED')}
                    disabled={isUpdating}
                  >
                    Yes, Clear
                  </button>
                  <button 
                    className="btn btn-secondary" 
                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                    onClick={() => setShowClearConfirm(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
              <button
                id="btn-action-reviewed"
                className="btn btn-primary"
                onClick={() => handleAction('REVIEWED')}
                disabled={isUpdating}
              >
                Mark Reviewed
              </button>

              <button
                id="btn-action-clear"
                className="btn btn-danger"
                onClick={() => handleAction('CLEARED')}
                disabled={isUpdating}
              >
                Clear Flag
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
