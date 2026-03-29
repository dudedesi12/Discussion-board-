'use client';

import { useState } from 'react';
import { useJourney } from '@/lib/community/hooks';
import { JourneyForm } from '@/components/community/JourneyForm';
import { ProcessingStatsView } from '@/components/community/ProcessingStats';

export function JourneyPageClient({ userId }: { userId: string }) {
  const { milestones, loading, save } = useJourney(userId);
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<'my-journey' | 'community-stats'>('my-journey');

  async function handleSave(data: any) { await save(data); setShowForm(false); setEditing(null); }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-2">Visa Journey Tracker</h1>
      <p className="text-sm text-zinc-500 mb-6">Log your milestones. Help others by contributing anonymous processing data.</p>

      <div className="flex gap-1 mb-6 border-b border-zinc-800">
        <button onClick={() => setActiveTab('my-journey')} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === 'my-journey' ? 'border-teal-500 text-teal-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>My Journey</button>
        <button onClick={() => setActiveTab('community-stats')} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${activeTab === 'community-stats' ? 'border-teal-500 text-teal-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>Community Processing Times</button>
      </div>

      {activeTab === 'my-journey' && (
        <div>
          {!showForm && !editing && (
            <button onClick={() => setShowForm(true)} className="mb-6 px-5 py-2.5 bg-teal-600 hover:bg-teal-500 text-white text-sm font-semibold rounded-lg transition-colors">+ Log New Journey</button>
          )}
          {(showForm || editing) && (
            <div className="mb-8">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">{editing ? 'Update Journey' : 'Log New Journey'}</h2>
                <button onClick={() => { setShowForm(false); setEditing(null); }} className="text-sm text-zinc-500 hover:text-zinc-300">Cancel</button>
              </div>
              <JourneyForm userId={userId} onSave={handleSave} initialData={editing} />
            </div>
          )}
          {loading ? (
            <div className="animate-pulse space-y-4">{[1,2].map(i => <div key={i} className="h-24 bg-zinc-800 rounded-xl" />)}</div>
          ) : milestones.length === 0 && !showForm ? (
            <div className="border border-dashed border-zinc-700 rounded-xl p-8 text-center">
              <p className="text-zinc-500 text-sm mb-3">You haven&apos;t logged any journeys yet.</p>
              <p className="text-xs text-zinc-600">Your milestones help build community processing data that helps everyone.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {milestones.map(m => (
                <div key={m.id} className="border border-zinc-800 rounded-xl p-5 bg-zinc-900/30">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-zinc-200">SC {m.visa_subclass} &mdash; {m.occupation_name || m.occupation_code}</span>
                      {m.state && <span className="text-xs bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">{m.state}</span>}
                      {m.points_score && <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full">{m.points_score} pts</span>}
                    </div>
                    <button onClick={() => setEditing(m)} className="text-xs text-zinc-500 hover:text-teal-400 transition-colors">Edit</button>
                  </div>
                  <div className="flex flex-wrap gap-3">
                    {[{ key: 'eoi_submitted_at', label: 'EOI' }, { key: 'invitation_received_at', label: 'Invite' },
                      { key: 'visa_lodged_at', label: 'Lodge' }, { key: 's56_received_at', label: 'S56' },
                      { key: 'medicals_completed_at', label: 'Medicals' }, { key: 'grant_received_at', label: 'Grant' }].map(step => {
                      const date = (m as any)[step.key];
                      return (
                        <div key={step.key} className={`text-center px-3 py-2 rounded-lg border text-xs ${date ? 'border-teal-500/30 bg-teal-500/10 text-teal-400' : 'border-zinc-800 bg-zinc-900 text-zinc-600'}`}>
                          <div className="font-medium">{step.label}</div>
                          {date && <div className="text-xs mt-0.5 opacity-70">{new Date(date).toLocaleDateString('en-AU', { day: 'numeric', month: 'short' })}</div>}
                        </div>
                      );
                    })}
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${m.status === 'granted' ? 'bg-emerald-500/10 text-emerald-400' : m.status === 'refused' ? 'bg-red-500/10 text-red-400' : 'bg-zinc-800 text-zinc-400'}`}>{m.status}</span>
                    <span className="text-xs text-zinc-600">{m.onshore ? 'Onshore' : 'Offshore'}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'community-stats' && (
        <div>
          <p className="text-sm text-zinc-500 mb-6">Aggregated processing times from anonymous community data.</p>
          <ProcessingStatsView />
        </div>
      )}
    </div>
  );
}
