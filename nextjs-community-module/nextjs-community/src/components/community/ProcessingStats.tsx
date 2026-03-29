'use client';

import { useProcessingStats } from '@/lib/community/hooks';

export function ProcessingStatsView({ filters }: { filters?: { visa_subclass?: string; state?: string } }) {
  const { stats, loading } = useProcessingStats(filters);

  if (loading) return (
    <div className="animate-pulse space-y-3">
      {[1, 2, 3].map(i => <div key={i} className="h-16 bg-zinc-800 rounded-lg" />)}
    </div>
  );

  if (stats.length === 0) return (
    <div className="border border-dashed border-zinc-700 rounded-xl p-8 text-center">
      <p className="text-zinc-500 text-sm">No processing data yet. Be the first to log your journey!</p>
    </div>
  );

  return (
    <div className="space-y-3">
      {stats.map((row, i) => (
        <div key={i} className="border border-zinc-800 rounded-xl p-4 bg-zinc-900/30">
          <div className="flex items-center justify-between mb-2">
            <div>
              <span className="text-sm font-semibold text-zinc-200">{row.occupation_name || row.occupation_code}</span>
              <div className="flex gap-2 mt-1">
                <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full">SC{row.visa_subclass}</span>
                {row.state && <span className="text-xs bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">{row.state}</span>}
              </div>
            </div>
            <div className="text-right">
              <span className="text-lg font-bold text-teal-400">{row.total_cases}</span>
              <span className="text-xs text-zinc-500 block">cases</span>
            </div>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-3 pt-3 border-t border-zinc-800">
            {row.avg_days_eoi_to_invite && <div className="text-center"><div className="text-base font-bold text-zinc-200">{row.avg_days_eoi_to_invite}d</div><div className="text-xs text-zinc-500">EOI→Invite</div></div>}
            {row.avg_days_lodge_to_grant && <div className="text-center"><div className="text-base font-bold text-zinc-200">{row.avg_days_lodge_to_grant}d</div><div className="text-xs text-zinc-500">Lodge→Grant</div></div>}
            {row.avg_grant_points && <div className="text-center"><div className="text-base font-bold text-zinc-200">{row.avg_grant_points}</div><div className="text-xs text-zinc-500">Avg Points</div></div>}
            {row.min_grant_points && <div className="text-center"><div className="text-base font-bold text-zinc-200">{row.min_grant_points}</div><div className="text-xs text-zinc-500">Min Points</div></div>}
          </div>
        </div>
      ))}
    </div>
  );
}
