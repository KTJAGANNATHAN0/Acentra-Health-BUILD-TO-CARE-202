import React from 'react';
import { ShieldAlert, Sliders, PlayCircle, RefreshCw, Radio } from 'lucide-react';

interface NavbarProps {
  onOpenRules: () => void;
  onOpenSimulator: () => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  notifier: string;
}

export const Navbar: React.FC<NavbarProps> = ({
  onOpenRules,
  onOpenSimulator,
  onRefresh,
  isRefreshing,
  notifier
}) => {
  return (
    <header className="header-bar glass-panel">
      <div className="brand-wrapper">
        <div className="brand-icon-box">
          <ShieldAlert size={24} />
        </div>
        <div>
          <h1 className="brand-title">ACCENTRA FRAUD ENGINE</h1>
          <p className="brand-subtitle">Real-Time Risk Decisioning &amp; Review Console</p>
        </div>
      </div>

      <div className="nav-actions">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)',
          padding: '6px 12px',
          borderRadius: '8px',
          fontSize: '0.8rem',
          color: 'var(--text-secondary)'
        }}>
          <Radio size={14} color="#10b981" />
          <span>Alert Dispatcher: <strong style={{ color: '#6ee7b7', textTransform: 'uppercase' }}>{notifier || 'LOG'}</strong></span>
        </div>

        <button 
          id="btn-tune-rules"
          className="btn btn-secondary" 
          onClick={onOpenRules}
          title="Tune Rule Thresholds & Weights"
        >
          <Sliders size={16} />
          Rule Config
        </button>

        <button 
          id="btn-open-simulator"
          className="btn btn-secondary" 
          onClick={onOpenSimulator}
          title="Simulate Fraud & Test Ingestion"
        >
          <PlayCircle size={16} color="#818cf8" />
          Simulator
        </button>

        <button 
          id="btn-refresh"
          className="btn btn-secondary" 
          onClick={onRefresh}
          disabled={isRefreshing}
          title="Refresh Queue & Stats"
        >
          <RefreshCw size={16} className={isRefreshing ? 'spin-anim' : ''} />
          Refresh
        </button>
      </div>
    </header>
  );
};
