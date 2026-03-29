'use client';

import { useState } from 'react';

export function ReplyForm({ postId, userId, onSubmit }: {
  postId: string; userId?: string;
  onSubmit: (reply: { post_id: string; author_id: string; body: string; is_anonymous?: boolean }) => Promise<void>;
}) {
  const [body, setBody] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  if (!userId) {
    return (
      <div className="border border-zinc-800 rounded-xl p-5 text-center">
        <p className="text-sm text-zinc-500"><a href="/login" className="text-pink-400 hover:text-pink-300 font-medium">Sign in</a> to reply</p>
      </div>
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!body.trim() || !userId) return;
    setSubmitting(true);
    try {
      await onSubmit({ post_id: postId, author_id: userId, body: body.trim(), is_anonymous: isAnonymous });
      setBody('');
      setIsAnonymous(false);
    } catch (err) { console.error(err); }
    finally { setSubmitting(false); }
  }

  return (
    <form onSubmit={handleSubmit} className="border border-zinc-800 rounded-xl p-5 space-y-3">
      <textarea value={body} onChange={e => setBody(e.target.value)}
        placeholder="Share your thoughts, experience, or advice..."
        className="w-full bg-zinc-900 border border-zinc-700 rounded-lg px-4 py-3 text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-pink-500/40 min-h-[100px] resize-y" required />
      <div className="flex items-center justify-between">
        <label className="flex items-center gap-2 cursor-pointer">
          <input type="checkbox" checked={isAnonymous} onChange={e => setIsAnonymous(e.target.checked)}
            className="w-4 h-4 rounded border-zinc-600 bg-zinc-900 text-pink-500" />
          <span className="text-sm text-zinc-400">Reply anonymously</span>
        </label>
        <button type="submit" disabled={submitting || !body.trim()}
          className="px-5 py-2 bg-pink-600 hover:bg-pink-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white text-sm font-semibold rounded-lg transition-colors">
          {submitting ? 'Posting...' : 'Reply'}
        </button>
      </div>
    </form>
  );
}
