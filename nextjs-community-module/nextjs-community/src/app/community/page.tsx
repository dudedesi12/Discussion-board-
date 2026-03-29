'use client';

import { useState } from 'react';
import { usePosts } from '@/lib/community/hooks';
import { PostCard } from '@/components/community/PostCard';
import { CategoryFilter } from '@/components/community/CategoryFilter';
import type { PostCategory } from '@/lib/supabase/types';
import Link from 'next/link';

export default function CommunityPage() {
  const [category, setCategory] = useState<PostCategory | undefined>();
  const [sort, setSort] = useState<'newest' | 'popular' | 'unanswered'>('newest');
  const { posts, total, page, setPage, loading } = usePosts({ category, sort });
  const totalPages = Math.ceil(total / 15);

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-bold">Community</h1>
            <p className="text-sm text-zinc-500 mt-1">Share your journey, ask questions, help others navigate Australian migration.</p>
          </div>
          <div className="flex gap-3">
            <Link href="/community/journey" className="px-4 py-2 border border-teal-500/30 text-teal-400 hover:bg-teal-500/10 text-sm font-medium rounded-lg transition-colors">My Journey</Link>
            <Link href="/community/create" className="px-4 py-2 bg-pink-600 hover:bg-pink-500 text-white text-sm font-semibold rounded-lg transition-colors">+ New Post</Link>
          </div>
        </div>

        <div className="mb-5"><CategoryFilter selected={category} onChange={setCategory} /></div>

        <div className="flex gap-1 mb-6 border-b border-zinc-800">
          {(['newest', 'popular', 'unanswered'] as const).map(s => (
            <button key={s} onClick={() => setSort(s)} className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${sort === s ? 'border-pink-500 text-pink-400' : 'border-transparent text-zinc-500 hover:text-zinc-300'}`}>
              {s === 'newest' ? 'Newest' : s === 'popular' ? 'Popular' : 'Unanswered'}
            </button>
          ))}
        </div>

        {loading ? (
          <div className="space-y-4">{[1,2,3,4].map(i => (
            <div key={i} className="animate-pulse border border-zinc-800 rounded-xl p-5"><div className="h-5 bg-zinc-800 rounded w-3/4 mb-3" /><div className="h-3 bg-zinc-800 rounded w-1/2" /></div>
          ))}</div>
        ) : posts.length === 0 ? (
          <div className="border border-dashed border-zinc-700 rounded-xl p-12 text-center">
            <p className="text-zinc-500 mb-4">No posts yet in this category.</p>
            <Link href="/community/create" className="text-pink-400 hover:text-pink-300 font-medium">Be the first to post</Link>
          </div>
        ) : (
          <div className="space-y-4">{posts.map(post => <PostCard key={post.id} post={post} />)}</div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="px-3 py-1.5 text-sm border border-zinc-700 rounded-lg disabled:opacity-30">Previous</button>
            <span className="text-sm text-zinc-500 px-3">Page {page} of {totalPages}</span>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="px-3 py-1.5 text-sm border border-zinc-700 rounded-lg disabled:opacity-30">Next</button>
          </div>
        )}
      </div>
    </div>
  );
}
