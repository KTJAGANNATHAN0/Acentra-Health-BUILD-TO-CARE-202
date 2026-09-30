import React from 'react';
import { Clock, CheckCircle2, BellRing, Activity, Gauge } from 'lucide-react';
import type { FraudStats } from '../types';

interface StatsOverviewProps {
  stats?: FraudStats;
  onFilterStatus?: (status: string) => void;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats, onFilterStatus }) => {
  if (!stats) return null;

  return (
    <div className="stats-grid">
      {/* Pending Flags - Urgent callout */}
      <div 
        id="card-stat-pending"
        className="glass-panel stat-card" 
        style={{ '--card-accent': '#f59e0b', cursor: 'pointer' } as React.CSSProperties}
        onClick={() => onFilterStatus && onFilterStatus('PENDING')}
        title="Click to view pending flags"
      >
        <div className="stat-header">
          <span className="stat-title">Pending Flags</span>
          <Clock size={18} className="stat-icon" color="#f59e0b" />
        </div>
        <div className="stat-value" style={{ color: '#fbbf24' }}>
          {stats.pending_flags}
        </div>
        <div className="stat-subtext">Awaiting analyst investigation</div>
      </div>

      {/* High-Risk Alerts Sent */}
      <div 
        id="card-stat-alerts"
        className="glass-panel stat-card" 
        style={{ '--card-accent': '#f43f5e' } as React.CSSProperties}
      >
        <div className="stat-header">
          <span className="stat-title">High-Risk Alerts</span>
          <BellRing size={18} className="stat-icon" color="#f43f5e" />
        </div>
        <div className="stat-value" style={{ color: '#fda4af' }}>
          {stats.high_risk_alerts_sent}
        </div>
        <div className="stat-subtext">Dispatched to SNS/SES (score &ge; 80)</div>
      </div>

      {/* Total Flagged vs Reviewed */}
      <div 
        id="card-stat-resolved"
        className="glass-panel stat-card" 
        style={{ '--card-accent': '#38bdf8' } as React.CSSProperties}
      >
        <div className="stat-header">
          <span className="stat-title">Resolved / Cleared</span>
          <CheckCircle2 size={18} className="stat-icon" color="#38bdf8" />
        </div>
        <div className="stat-value" style={{ color: '#7dd3fc' }}>
          {stats.reviewed_flags + stats.cleared_flags}
          <span style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
            / {stats.total_flagged}
          </span>
        </div>
        <div className="stat-subtext">
          {stats.reviewed_flags} reviewed &bull; {stats.cleared_flags} cleared
        </div>
      </div>

      {/* Total Ingested Transactions */}
      <div 
        id="card-stat-ingested"
        className="glass-panel stat-card" 
        style={{ '--card-accent': '#6366f1' } as React.CSSProperties}
      >
        <div className="stat-header">
          <span className="stat-title">Total Ingested</span>
          <Activity size={18} className="stat-icon" color="#6366f1" />
        </div>
        <div className="stat-value" style={{ color: '#a5b4fc' }}>
          {stats.total_transactions}
        </div>
        <div className="stat-subtext">Evaluated against active rules</div>
      </div>

      {/* Average Risk Score */}
      <div 
        id="card-stat-avg-score"
        className="glass-panel stat-card" 
        style={{ '--card-accent': '#10b981' } as React.CSSProperties}
      >
        <div className="stat-header">
          <span className="stat-title">Mean Risk Score</span>
          <Gauge size={18} className="stat-icon" color="#10b981" />
        </div>
        <div className="stat-value" style={{ color: '#6ee7b7' }}>
          {stats.avg_risk_score}
          <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}> / 100</span>
        </div>
        <div className="stat-subtext">Across all ingested transactions</div>
      </div>
    </div>
  );
};
