'use client';

import { useState } from 'react';
import type { VisaSubclass, AustralianState, JourneyStatus } from '@/lib/supabase/types';

const VISA_OPTIONS: VisaSubclass[] = ['189', '190', '491', '482', 'sid'];
const STATE_OPTIONS: AustralianState[] = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT'];
const STATUS_OPTIONS: { value: JourneyStatus; label: string }[] = [
  { value: 'eoi-submitted', label: 'EOI Submitted' }, { value: 'invited', label: 'Invited to Apply' },
  { value: 'lodged', label: 'Visa Lodged' }, { value: 'waiting', label: 'Waiting' },
  { value: 's56-received', label: 'S56 Received' }, { value: 'granted', label: 'Granted!' },
  { value: 'refused', label: 'Refused' }, { value: 'withdrawn', label: 'Withdrawn' },
];

export function JourneyForm({ userId, onSave, initialData }: {
  userId: string; onSave: (data: any) => Promise<void>; initialData?: any;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    visa_subclass: initialData?.visa_subclass || '190',
    occupation_code: initialData?.occupation_code || '',
    occupation_name: initialData?.occupation_name || '',
    state: initialData?.state || '',
    points_score: initialData?.points_score?.toString() || '',
    onshore: initialData?.onshore ?? true,
    status: initialData?.status || 'eoi-submitted',
    eoi_submitted_at: initialData?.eoi_submitted_at || '',
    invitation_received_at: initialData?.invitation_received_at || '',
    visa_lodged_at: initialData?.visa_lodged_at || '',
    s56_received_at: initialData?.s56_received_at || '',
    s56_responded_at: initialData?.s56_responded_at || '',
    medicals_completed_at: initialData?.medicals_completed_at || '',
    grant_received_at: initialData?.grant_received_at || '',
    is_anonymous: initialData?.is_anonymous ?? true,
    notes: initialData?.notes || '',
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault(); setSubmitting(true);
    try {
      await onSave({
        ...(initialData?.id ? { id: initialData.id } : {}),
        user_id: userId, visa_subclass: form.visa_subclass, occupation_code: form.occupation_code,
        occupation_name: form.occupation_name || null, state: form.state || null,
        points_score: form.points_score ? parseInt(form.points_score) : null,
        onshore: form.onshore, status: form.status,
        eoi_submitted_at: form.eoi_submitted_at || null, invitation_received_at: form.invitation_received_at || null,
        visa_lodged_at: form.visa_lodged_at || null, s56_received_at: form.s56_received_at || null,
        s56_responded_at: form.s56_responded_at || null, medicals_completed_at: form.medicals_completed_at || null,
        grant_received_at: form.grant_received_at || null, is_anonymous: form.is_anonymous, notes: form.notes || null,
      });
    } finally { setSubmitting(false); }
  }

  const inputClass = 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-teal-500/40 transition-colors text-sm';
  const labelClass = 'block text-xs font-medium text-zinc-400 mb-1';

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="border border-zinc-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-teal-400 uppercase tracking-wider">Your Visa Context</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div><label className={labelClass}>Visa Subclass *</label>
            <select value={form.visa_subclass} onChange={e => setForm(p => ({ ...p, visa_subclass: e.target.value }))} className={inputClass} required>
              {VISA_OPTIONS.map(v => <option key={v} value={v}>SC {v}</option>)}
            </select></div>
          <div><label className={labelClass}>ANZSCO Code *</label>
            <input value={form.occupation_code} onChange={e => setForm(p => ({ ...p, occupation_code: e.target.value }))} placeholder="e.g. 261313" className={inputClass} required /></div>
          <div><label className={labelClass}>Occupation Name</label>
            <input value={form.occupation_name} onChange={e => setForm(p => ({ ...p, occupation_name: e.target.value }))} placeholder="e.g. Software Engineer" className={inputClass} /></div>
          <div><label className={labelClass}>State</label>
            <select value={form.state} onChange={e => setForm(p => ({ ...p, state: e.target.value }))} className={inputClass}>
              <option value="">N/A (189)</option>
              {STATE_OPTIONS.map(s => <option key={s} value={s}>{s}</option>)}
            </select></div>
          <div><label className={labelClass}>Points Score</label>
            <input type="number" value={form.points_score} onChange={e => setForm(p => ({ ...p, points_score: e.target.value }))} placeholder="85" className={inputClass} /></div>
          <div><label className={labelClass}>Location</label>
            <div className="flex gap-3 mt-1">
              <label className="flex items-center gap-2 cursor-pointer"><input type="radio" checked={form.onshore} onChange={() => setForm(p => ({ ...p, onshore: true }))} className="text-teal-500" /><span className="text-sm text-zinc-300">Onshore</span></label>
              <label className="flex items-center gap-2 cursor-pointer"><input type="radio" checked={!form.onshore} onChange={() => setForm(p => ({ ...p, onshore: false }))} className="text-teal-500" /><span className="text-sm text-zinc-300">Offshore</span></label>
            </div></div>
        </div>
      </div>

      <div className="border border-zinc-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-semibold text-teal-400 uppercase tracking-wider">Timeline Milestones</h3>
        <p className="text-xs text-zinc-500">Fill dates as your journey progresses. Leave blank for milestones not yet reached.</p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[{ key: 'eoi_submitted_at', label: 'EOI Submitted' }, { key: 'invitation_received_at', label: 'Invitation Received' },
            { key: 'visa_lodged_at', label: 'Visa Lodged' }, { key: 's56_received_at', label: 'S56 Received' },
            { key: 's56_responded_at', label: 'S56 Responded' }, { key: 'medicals_completed_at', label: 'Medicals Completed' },
            { key: 'grant_received_at', label: 'Grant Received' }].map(m => (
            <div key={m.key}><label className={labelClass}>{m.label}</label>
              <input type="date" value={(form as any)[m.key]} onChange={e => setForm(p => ({ ...p, [m.key]: e.target.value }))} className={inputClass} /></div>
          ))}
        </div>
      </div>

      <div className="border border-zinc-800 rounded-xl p-5 space-y-4">
        <div><label className={labelClass}>Current Status</label>
          <select value={form.status} onChange={e => setForm(p => ({ ...p, status: e.target.value }))} className={inputClass}>
            {STATUS_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select></div>
        <div><label className={labelClass}>Notes (optional)</label>
          <textarea value={form.notes} onChange={e => setForm(p => ({ ...p, notes: e.target.value }))} placeholder="Any tips or details..." className={`${inputClass} min-h-[80px] resize-y`} /></div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" checked={form.is_anonymous} onChange={e => setForm(p => ({ ...p, is_anonymous: e.target.checked }))} className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-teal-500" />
          <span className="text-sm text-zinc-400">Share anonymously (data appears in aggregate stats, name hidden)</span>
        </label>
      </div>

      <button type="submit" disabled={submitting || !form.occupation_code} className="w-full sm:w-auto px-6 py-2.5 bg-teal-600 hover:bg-teal-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white font-semibold rounded-lg transition-colors">
        {submitting ? 'Saving...' : initialData?.id ? 'Update Journey' : 'Log My Journey'}
      </button>
    </form>
  );
}
