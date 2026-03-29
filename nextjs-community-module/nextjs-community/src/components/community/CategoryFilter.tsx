'use client';

import type { PostCategory } from '@/lib/supabase/types';

const CATEGORIES: { value: PostCategory; label: string; emoji: string }[] = [
  { value: 'visa-journey', label: 'Visa Journey', emoji: '✈️' },
  { value: 'state-nomination', label: 'State Nomination', emoji: '🏛️' },
  { value: 'points-help', label: 'Points Help', emoji: '🧮' },
  { value: 'skills-assessment', label: 'Skills Assessment', emoji: '📋' },
  { value: 'eoi-updates', label: 'EOI Updates', emoji: '📬' },
  { value: 'agent-reviews', label: 'Agent Reviews', emoji: '⭐' },
  { value: 'job-market', label: 'Job Market', emoji: '💼' },
  { value: 'settlement', label: 'Settlement', emoji: '🏠' },
  { value: 'general', label: 'General', emoji: '💬' },
];

export function CategoryFilter({ selected, onChange }: { selected?: PostCategory; onChange: (cat?: PostCategory) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      <button onClick={() => onChange(undefined)} className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${!selected ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30' : 'bg-zinc-800/50 text-zinc-400 border border-zinc-700/50 hover:border-zinc-600'}`}>All</button>
      {CATEGORIES.map(cat => (
        <button key={cat.value} onClick={() => onChange(selected === cat.value ? undefined : cat.value)} className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${selected === cat.value ? 'bg-pink-500/20 text-pink-400 border border-pink-500/30' : 'bg-zinc-800/50 text-zinc-400 border border-zinc-700/50 hover:border-zinc-600'}`}>{cat.emoji} {cat.label}</button>
      ))}
    </div>
  );
}

export function CategoryBadge({ category }: { category: PostCategory }) {
  const cat = CATEGORIES.find(c => c.value === category);
  if (!cat) return null;
  return <span className="text-xs bg-zinc-800 text-zinc-400 px-2 py-0.5 rounded-full">{cat.emoji} {cat.label}</span>;
}

export { CATEGORIES };
