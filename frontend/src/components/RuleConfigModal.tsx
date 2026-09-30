import React, { useState } from 'react';
import { X, Sliders, Save, Check, RefreshCw } from 'lucide-react';
import type { RuleConfig } from '../types';

interface RuleConfigModalProps {
  rules: RuleConfig[];
  onClose: () => void;
  onSaveRule: (ruleName: string, payload: { enabled?: boolean; weight?: number; params?: Record<string, any> }) => Promise<void>;
  isLoading?: boolean;
}

export const RuleConfigModal: React.FC<RuleConfigModalProps> = ({
  rules,
  onClose,
  onSaveRule
}) => {
  const [configState, setConfigState] = useState<Record<string, RuleConfig>>(() => {
    const map: Record<string, RuleConfig> = {};
    rules.forEach(r => { map[r.rule_name] = JSON.parse(JSON.stringify(r)); });
    return map;
  });

  const [savingRule, setSavingRule] = useState<string | null>(null);
  const [savedSuccess, setSavedSuccess] = useState<string | null>(null);

  const handleToggle = (ruleName: string) => {
    setConfigState(prev => ({
      ...prev,
      [ruleName]: {
        ...prev[ruleName],
        enabled: !prev[ruleName].enabled
      }
    }));
  };

  const handleWeightChange = (ruleName: string, weight: number) => {
    setConfigState(prev => ({
      ...prev,
      [ruleName]: {
        ...prev[ruleName],
        weight
      }
    }));
  };

  const handleParamChange = (ruleName: string, paramKey: string, val: any) => {
    setConfigState(prev => ({
      ...prev,
      [ruleName]: {
        ...prev[ruleName],
        params: {
          ...prev[ruleName].params,
          [paramKey]: val
        }
      }
    }));
  };

  const handleSave = async (ruleName: string) => {
    const rule = configState[ruleName];
    setSavingRule(ruleName);
    try {
      await onSaveRule(ruleName, {
        enabled: rule.enabled,
        weight: rule.weight,
        params: rule.params
      });
      setSavedSuccess(ruleName);
      setTimeout(() => setSavedSuccess(null), 2500);
    } finally {
      setSavingRule(null);
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
              color: 'var(--primary)'
            }}>
              <Sliders size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Rule Engine Configuration (FR-11)</h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                Tune detection thresholds, enable/disable rules, and calibrate risk weights
              </p>
            </div>
          </div>
          <button className="btn btn-secondary" style={{ padding: '6px' }} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        {/* Rules List */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {Object.values(configState).map(rule => {
            const isSaving = savingRule === rule.rule_name;
            const isSaved = savedSuccess === rule.rule_name;

            return (
              <div 
                key={rule.rule_name}
                style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '20px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '16px'
                }}
              >
                {/* Rule Title & State */}
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <span style={{ fontSize: '1.05rem', fontWeight: 700, textTransform: 'capitalize' }}>
                      {rule.rule_name.replace('_', ' ')}
                    </span>
                    <button
                      id={`toggle-${rule.rule_name}`}
                      className="btn"
                      style={{
                        padding: '4px 10px',
                        fontSize: '0.75rem',
                        background: rule.enabled ? 'rgba(16, 185, 129, 0.2)' : 'rgba(255, 255, 255, 0.05)',
                        color: rule.enabled ? '#6ee7b7' : 'var(--text-muted)',
                        border: `1px solid ${rule.enabled ? 'rgba(16, 185, 129, 0.4)' : 'var(--border-subtle)'}`
                      }}
                      onClick={() => handleToggle(rule.rule_name)}
                    >
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </button>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    {/* Weight slider */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem' }}>
                      <span>Weight:</span>
                      <input
                        type="range"
                        min="0.5"
                        max="2.0"
                        step="0.1"
                        value={rule.weight}
                        onChange={(e) => handleWeightChange(rule.rule_name, parseFloat(e.target.value))}
                        style={{ accentColor: 'var(--primary)', width: '70px' }}
                      />
                      <span style={{ fontFamily: 'var(--font-mono)', minWidth: '28px' }}>{rule.weight.toFixed(1)}x</span>
                    </div>

                    <button
                      id={`btn-save-rule-${rule.rule_name}`}
                      className="btn btn-primary"
                      style={{ padding: '6px 12px', fontSize: '0.8rem' }}
                      onClick={() => handleSave(rule.rule_name)}
                      disabled={isSaving}
                    >
                      {isSaving ? <RefreshCw size={14} className="spin-anim" /> : isSaved ? <Check size={14} /> : <Save size={14} />}
                      {isSaved ? 'Saved!' : 'Save'}
                    </button>
                  </div>
                </div>

                {/* Parameters Form */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '12px',
                  background: 'rgba(0, 0, 0, 0.25)',
                  padding: '14px',
                  borderRadius: '8px'
                }}>
                  {Object.entries(rule.params).map(([paramKey, paramVal]) => (
                    <div key={paramKey}>
                      <label style={{ display: 'block', fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '4px' }}>
                        {paramKey.replace('_', ' ')}
                      </label>
                      <input
                        type="number"
                        className="input-control"
                        style={{ width: '100%', padding: '6px 10px', fontSize: '0.85rem' }}
                        value={paramVal}
                        onChange={(e) => handleParamChange(rule.rule_name, paramKey, Number(e.target.value))}
                      />
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
