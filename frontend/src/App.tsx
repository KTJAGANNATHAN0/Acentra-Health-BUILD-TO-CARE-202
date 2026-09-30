import { useState } from 'react';
import { 
  QueryClient, 
  QueryClientProvider, 
  useQuery, 
  useMutation, 
  useQueryClient 
} from '@tanstack/react-query';
import { Navbar } from './components/Navbar';
import { StatsOverview } from './components/StatsOverview';
import { FlagQueueTable } from './components/FlagQueueTable';
import { FlagDetailModal } from './components/FlagDetailModal';
import { RuleConfigModal } from './components/RuleConfigModal';
import { TransactionSimulatorModal } from './components/TransactionSimulatorModal';
import { 
  fetchFlags, 
  fetchStats, 
  fetchRules, 
  fetchFlagDetail, 
  updateFlagStatus, 
  updateRule, 
  reEvaluateTransaction,
  triggerScenario,
  submitTransaction,
  fetchHealth
} from './api/client';
import type { FraudFlag, FlagStatus } from './types';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      staleTime: 5000,
    }
  }
});

function ConsoleDashboard() {
  const qc = useQueryClient();

  // Filters and Pagination State
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [minScoreFilter, setMinScoreFilter] = useState(0);
  const [accountFilter, setAccountFilter] = useState('');
  const [sortBy, setSortBy] = useState('score');
  const [sortDir, setSortDir] = useState('desc');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Modals State
  const [selectedFlagId, setSelectedFlagId] = useState<number | null>(null);
  const [isRulesModalOpen, setIsRulesModalOpen] = useState(false);
  const [isSimulatorModalOpen, setIsSimulatorModalOpen] = useState(false);

  // Queries
  const { data: stats, isLoading: isStatsLoading, refetch: refetchStats } = useQuery({
    queryKey: ['fraudStats'],
    queryFn: fetchStats,
    refetchInterval: 10000
  });

  const { data: health } = useQuery({
    queryKey: ['healthStatus'],
    queryFn: fetchHealth,
    staleTime: 30000
  });

  const { data: flagsData, isLoading: isFlagsLoading, refetch: refetchFlags } = useQuery({
    queryKey: ['fraudFlags', statusFilter, minScoreFilter, accountFilter, sortBy, sortDir, page],
    queryFn: () => fetchFlags({
      status: statusFilter,
      min_score: minScoreFilter > 0 ? minScoreFilter : undefined,
      account_id: accountFilter || undefined,
      sort_by: sortBy,
      sort_dir: sortDir,
      page,
      page_size: pageSize
    }),
    refetchInterval: 8000
  });

  const { data: rulesData, refetch: refetchRules } = useQuery({
    queryKey: ['fraudRules'],
    queryFn: fetchRules
  });

  const { data: flagDetail, isFetching: isDetailFetching } = useQuery({
    queryKey: ['flagDetail', selectedFlagId],
    queryFn: () => selectedFlagId ? fetchFlagDetail(selectedFlagId) : null,
    enabled: selectedFlagId !== null
  });

  // Mutations
  const updateStatusMutation = useMutation({
    mutationFn: ({ flagId, status, note }: { flagId: number; status: FlagStatus; note: string }) =>
      updateFlagStatus(flagId, status, note, 'fraud_reviewer'),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fraudFlags'] });
      qc.invalidateQueries({ queryKey: ['fraudStats'] });
      qc.invalidateQueries({ queryKey: ['flagDetail', selectedFlagId] });
    }
  });

  const reEvaluateMutation = useMutation({
    mutationFn: (txnId: string) => reEvaluateTransaction(txnId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fraudFlags'] });
      qc.invalidateQueries({ queryKey: ['fraudStats'] });
      if (selectedFlagId) {
        qc.invalidateQueries({ queryKey: ['flagDetail', selectedFlagId] });
      }
    }
  });

  const updateRuleMutation = useMutation({
    mutationFn: ({ ruleName, payload }: { ruleName: string; payload: any }) =>
      updateRule(ruleName, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['fraudRules'] });
    }
  });

  const handleRefresh = async () => {
    await Promise.all([refetchStats(), refetchFlags(), refetchRules()]);
  };

  const handleSortChange = (newSortBy: string) => {
    if (sortBy === newSortBy) {
      setSortDir(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(newSortBy);
      setSortDir('desc');
    }
  };

  return (
    <div className="app-container">
      {/* Top Navigation */}
      <Navbar 
        onOpenRules={() => setIsRulesModalOpen(true)}
        onOpenSimulator={() => setIsSimulatorModalOpen(true)}
        onRefresh={handleRefresh}
        isRefreshing={isFlagsLoading || isStatsLoading}
        notifier={health?.notifier || 'log'}
      />

      {/* Real-time Metric Cards Overview */}
      <StatsOverview 
        stats={stats} 
        onFilterStatus={(st) => { setStatusFilter(st); setPage(1); }} 
      />

      {/* Main Flag Queue Table */}
      <FlagQueueTable
        flags={flagsData?.items || []}
        total={flagsData?.total || 0}
        page={page}
        pageSize={pageSize}
        totalPages={flagsData?.total_pages || 1}
        statusFilter={statusFilter}
        minScoreFilter={minScoreFilter}
        accountFilter={accountFilter}
        sortBy={sortBy}
        sortDir={sortDir}
        isLoading={isFlagsLoading}
        onSelectFlag={(flag: FraudFlag) => setSelectedFlagId(flag.id)}
        onStatusChange={(st) => { setStatusFilter(st); setPage(1); }}
        onMinScoreChange={(score) => { setMinScoreFilter(score); setPage(1); }}
        onAccountChange={(acc) => { setAccountFilter(acc); setPage(1); }}
        onSortChange={handleSortChange}
        onPageChange={(p) => setPage(p)}
      />

      {/* Flag Detail & Investigation Modal (FR-9, FR-10, FR-12) */}
      {selectedFlagId && flagDetail && (
        <FlagDetailModal
          detail={flagDetail}
          onClose={() => setSelectedFlagId(null)}
          onUpdateStatus={async (flagId, status, note) => {
            await updateStatusMutation.mutateAsync({ flagId, status, note });
          }}
          onReEvaluate={async (txnId) => {
            await reEvaluateMutation.mutateAsync(txnId);
          }}
          isUpdating={updateStatusMutation.isPending || reEvaluateMutation.isPending || isDetailFetching}
        />
      )}

      {/* Rule Tuning & Configuration Modal (FR-11) */}
      {isRulesModalOpen && rulesData && (
        <RuleConfigModal
          rules={rulesData}
          onClose={() => setIsRulesModalOpen(false)}
          onSaveRule={async (ruleName, payload) => {
            await updateRuleMutation.mutateAsync({ ruleName, payload });
          }}
        />
      )}

      {/* Transaction & Fraud Simulator Modal */}
      {isSimulatorModalOpen && (
        <TransactionSimulatorModal
          onClose={() => setIsSimulatorModalOpen(false)}
          onTriggerScenario={async (scenarioName) => {
            const res = await triggerScenario(scenarioName);
            qc.invalidateQueries({ queryKey: ['fraudFlags'] });
            qc.invalidateQueries({ queryKey: ['fraudStats'] });
            return res;
          }}
          onSubmitCustom={async (payload) => {
            const res = await submitTransaction(payload);
            qc.invalidateQueries({ queryKey: ['fraudFlags'] });
            qc.invalidateQueries({ queryKey: ['fraudStats'] });
            return res;
          }}
        />
      )}
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConsoleDashboard />
    </QueryClientProvider>
  );
}
