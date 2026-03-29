'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createPost } from '@/lib/community/queries';
import { CATEGORIES } from './CategoryFilter';
import type { PostCategory, VisaSubclass, AustralianState } from '@/lib/supabase/types';

const VISA_OPTIONS: { value: VisaSubclass; label: string }[] = [
  { value: '189', label: 'SC 189 — Skilled Independent' },
  { value: '190', label: 'SC 190 — Skilled Nominated' },
  { value: '491', label: 'SC 491 — Skilled Regional' },
  { value: '482', label: 'SC 482 — TSS Visa' },
  { value: 'sid', label: 'Skills in Demand' },
];

const STATE_OPTIONS: { value: AustralianState; label: string }[] = [
  { value: 'NSW', label: 'New South Wales' }, { value: 'VIC', label: 'Victoria' },
  { value: 'QLD', label: 'Queensland' }, { value: 'WA', label: 'Western Australia' },
  { value: 'SA', label: 'South Australia' }, { value: 'TAS', label: 'Tasmania' },
  { value: 'ACT', label: 'ACT' }, { value: 'NT', label: 'Northern Territory' },
];

export function CreatePostForm({ userId }: { userId: string }) {
  const router = useRouter();
  const [submitting, setSubmitting] = useState(false);
  const [form, setForm] = useState({
    title: '', body: '', category: 'general' as PostCategory, tags: '',
    visa_subclass: '', state: '', points_score: '', is_anonymous: false,
  });

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!form.title.trim() || !form.body.trim()) return;
    setSubmitting(true);
    try {
      const post = await createPost({
        author_id: userId, title: form.title.trim(), body: form.body.trim(),
        category: form.category,
        tags: form.tags ? form.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
        visa_subclass: form.visa_subclass as VisaSubclass || undefined,
        state: form.state as AustralianState || undefined,
        points_score: form.points_score ? parseInt(form.points_score) : undefined,
        is_anonymous: form.is_anonymous,
      });
      router.push(`/community/${post.id}`);
    } catch (err) { console.error(err); setSubmitting(false); }
  }

  const inputClass = 'w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-2.5 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-pink-500/40 focus:border-pink-500/40 transition-colors';
  const labelClass = 'block text-sm font-medium text-zinc-300 mb-1.5';

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div><label className={labelClass}>Title *</label>
        <input type="text" value={form.title} onChange={e => setForm(p => ({ ...p, title: e.target.value }))} placeholder="What's your question or update?" className={inputClass} required minLength={5} maxLength={300} /></div>

      <div><label className={labelClass}>Details *</label>
        <textarea value={form.body} onChange={e => setForm(p => ({ ...p, body: e.target.value }))} placeholder="Share your experience, question, or update..." className={`${inputClass} min-h-[160px] resize-y`} required minLength={10} /></div>

      <div><label className={labelClass}>Category *</label>
        <select value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value as PostCategory }))} className={inputClass}>
          {CATEGORIES.map(c => <option key={c.value} value={c.value}>{c.emoji} {c.label}</option>)}
        </select></div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div><label className={labelClass}>Visa Subclass</label>
          <select value={form.visa_subclass} onChange={e => setForm(p => ({ ...p, visa_subclass: e.target.value }))} className={inputClass}>
            <option value="">Select (optional)</option>
            {VISA_OPTIONS.map(v => <option key={v.value} value={v.value}>{v.label}</option>)}
          </select></div>
        <div><label className={labelClass}>State</label>
          <select value={form.state} onChange={e => setForm(p => ({ ...p, state: e.target.value }))} className={inputClass}>
            <option value="">Select (optional)</option>
            {STATE_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select></div>
        <div><label className={labelClass}>Points Score</label>
          <input type="number" value={form.points_score} onChange={e => setForm(p => ({ ...p, points_score: e.target.value }))} placeholder="e.g. 85" className={inputClass} min={0} max={200} /></div>
      </div>

      <div><label className={labelClass}>Tags (comma-separated)</label>
        <input type="text" value={form.tags} onChange={e => setForm(p => ({ ...p, tags: e.target.value }))} placeholder="e.g. software-engineer, 261313, offshore" className={inputClass} /></div>

      <label className="flex items-center gap-3 cursor-pointer">
        <input type="checkbox" checked={form.is_anonymous} onChange={e => setForm(p => ({ ...p, is_anonymous: e.target.checked }))} className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-pink-500 focus:ring-pink-500/40" />
        <span className="text-sm text-zinc-400">Post anonymously</span>
      </label>

      <button type="submit" disabled={submitting || !form.title.trim() || !form.body.trim()} className="w-full sm:w-auto px-6 py-2.5 bg-pink-600 hover:bg-pink-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white font-semibold rounded-lg transition-colors">
        {submitting ? 'Posting...' : 'Create Post'}
      </button>
    </form>
  );
}
