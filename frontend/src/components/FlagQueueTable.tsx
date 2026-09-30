import React from 'react';
import { 
  Search, 
  ArrowUpDown, 
  ChevronLeft, 
  ChevronRight, 
  AlertCircle,
  ExternalLink,
  Flame,
  Zap,
  Globe,
  DollarSign
} from 'lucide-react';
import type { FraudFlag, FlagStatus } from '../types';

interface FlagQueueTableProps {
  flags: FraudFlag[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
  statusFilter: string;
  minScoreFilter: number;
  accountFilter: string;
  sortBy: string;
  sortDir: string;
  isLoading: boolean;
  onSelectFlag: (flag: FraudFlag) => void;
  onStatusChange: (status: string) => void;
  onMinScoreChange: (score: number) => void;
  onAccountChange: (account: string) => void;
  onSortChange: (sortBy: string) => void;
  onPageChange: (newPage: number) => void;
}

export const FlagQueueTable: React.FC<FlagQueueTableProps> = ({
  flags,
  total,
  page,
  totalPages,
  statusFilter,
  minScoreFilter,
  accountFilter,
  sortBy,
  sortDir: _sortDir,
  isLoading,
  onSelectFlag,
  onStatusChange,
  onMinScoreChange,
  onAccountChange,
  onSortChange,
  onPageChange
}) => {

  const getScoreBadgeClass = (score: number) => {
    if (score >= 80) return 'score-badge high';
    if (score >= 50) return 'score-badge medium';
    return 'score-badge low';
  };

  const getStatusChipClass = (status: FlagStatus) => {
    switch (status) {
      case 'PENDING': return 'status-chip pending';
      case 'REVIEWED': return 'status-chip reviewed';
      case 'CLEARED': return 'status-chip cleared';
      default: return 'status-chip';
    }
  };

  const getRuleIcon = (ruleName: string) => {
    if (ruleName === 'velocity') return <Zap size={12} color="#fbbf24" />;
    if (ruleName === 'unusual_amount') return <DollarSign size={12} color="#34d399" />;
    if (ruleName === 'impossible_travel') return <Globe size={12} color="#f43f5e" />;
    return <AlertCircle size={12} />;
  };

  const formatCurrency = (amt: number, curr: string = 'USD') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: curr,
      maximumFractionDigits: 2
    }).format(amt);
  };

  const formatTimestamp = (isoStr: string) => {
    const d = new Date(isoStr);
    return d.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="glass-panel" style={{ padding: '20px' }}>
      {/* Filters and Controls Bar */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        marginBottom: '20px'
      }}>
        {/* Status Filter Tabs */}
        <div style={{ display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.3)', padding: '4px', borderRadius: '8px' }}>
          {['ALL', 'PENDING', 'REVIEWED', 'CLEARED'].map(st => (
            <button
              key={st}
              id={`tab-filter-${st.toLowerCase()}`}
              className="btn"
              style={{
                padding: '6px 14px',
                fontSize: '0.8rem',
                background: statusFilter === st ? 'var(--primary)' : 'transparent',
                color: statusFilter === st ? '#ffffff' : 'var(--text-secondary)',
                boxShadow: statusFilter === st ? '0 2px 6px rgba(99,102,241,0.4)' : 'none'
              }}
              onClick={() => onStatusChange(st)}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Score and Account Search */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Account Search */}
          <div style={{ position: 'relative', minWidth: '220px' }}>
            <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              id="input-search-account"
              type="text"
              placeholder="Search Account ID..."
              className="input-control"
              style={{ width: '100%', paddingLeft: '32px' }}
              value={accountFilter}
              onChange={(e) => onAccountChange(e.target.value)}
            />
          </div>

          {/* Min Score Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            <span>Min Score:</span>
            <input
              id="input-min-score"
              type="range"
              min="0"
              max="95"
              step="5"
              value={minScoreFilter}
              onChange={(e) => onMinScoreChange(Number(e.target.value))}
              style={{ accentColor: 'var(--primary)', width: '100px' }}
            />
            <span style={{ fontFamily: 'var(--font-mono)', minWidth: '24px', fontWeight: 600 }}>{minScoreFilter}</span>
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th className="sortable" onClick={() => onSortChange('score')} style={{ width: '100px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Risk Score
                  <ArrowUpDown size={12} color={sortBy === 'score' ? '#818cf8' : 'currentColor'} />
                </div>
              </th>
              <th>Account</th>
              <th>Amount</th>
              <th>Merchant &amp; Location</th>
              <th>Triggered Rules</th>
              <th className="sortable" onClick={() => onSortChange('created_at')}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Date / Time
                  <ArrowUpDown size={12} color={sortBy === 'created_at' ? '#818cf8' : 'currentColor'} />
                </div>
              </th>
              <th>Status</th>
              <th style={{ textAlign: 'right' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  Loading flagged transactions...
                </td>
              </tr>
            ) : flags.length === 0 ? (
              <tr>
                <td colSpan={8} style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)' }}>
                  <AlertCircle size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
                  <div>No flagged transactions found matching current filters.</div>
                </td>
              </tr>
            ) : (
              flags.map(flag => {
                const txn = flag.transaction;
                const isHighRisk = flag.score >= 80;
                const triggeredRules = txn?.rule_results?.filter(r => r.triggered) || [];

                return (
                  <tr 
                    key={flag.id} 
                    id={`flag-row-${flag.id}`}
                    className={`table-row ${flag.status === 'PENDING' ? 'row-pending' : ''}`}
                    onClick={() => onSelectFlag(flag)}
                  >
                    <td>
                      <div className={getScoreBadgeClass(flag.score)}>
                        {isHighRisk && <Flame size={12} style={{ marginRight: '4px' }} />}
                        {flag.score}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#e2e8f0' }}>
                        {txn?.account_id || 'N/A'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {txn ? formatCurrency(txn.amount, txn.currency) : 'N/A'}
                      </span>
                    </td>
                    <td>
                      <div>{txn?.merchant || 'Unknown Merchant'}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {txn?.country || 'Unknown location'} {txn?.lat ? `(${txn.lat.toFixed(2)}, ${txn.lon?.toFixed(2)})` : ''}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {triggeredRules.length > 0 ? (
                          triggeredRules.map(r => (
                            <span key={r.rule_name} className="rule-tag" title={r.reason}>
                              {getRuleIcon(r.rule_name)}
                              {r.rule_name}
                            </span>
                          ))
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>None</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {formatTimestamp(flag.created_at)}
                      </span>
                    </td>
                    <td>
                      <span className={getStatusChipClass(flag.status)}>
                        {flag.status}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        id={`btn-investigate-${flag.id}`}
                        className="btn btn-secondary" 
                        style={{ padding: '6px 12px', fontSize: '0.75rem' }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectFlag(flag);
                        }}
                      >
                        Investigate
                        <ExternalLink size={12} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid var(--border-subtle)',
        color: 'var(--text-muted)',
        fontSize: '0.85rem'
      }}>
        <div>
          Showing {flags.length} of {total} flagged items
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span>Page {page} of {Math.max(1, totalPages)}</span>
          <button 
            id="btn-page-prev"
            className="btn btn-secondary"
            style={{ padding: '4px 8px' }}
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
          >
            <ChevronLeft size={16} />
          </button>
          <button 
            id="btn-page-next"
            className="btn btn-secondary"
            style={{ padding: '4px 8px' }}
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>
    </div>
  );
};
