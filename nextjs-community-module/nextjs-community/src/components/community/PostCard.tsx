'use client';

import Link from 'next/link';
import type { CommunityPost } from '@/lib/supabase/types';
import { LikeButton } from './LikeButton';
import { CategoryBadge } from './CategoryFilter';

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString('en-AU', { day: 'numeric', month: 'short' });
}

export function PostCard({ post, userId, isLiked }: { post: CommunityPost; userId?: string; isLiked?: boolean }) {
  const author = post.is_anonymous ? null : post.author;
  return (
    <div className="border border-zinc-800 rounded-xl p-5 hover:border-zinc-700 transition-colors bg-zinc-900/50">
      <div className="flex items-start justify-between gap-3 mb-3">
        <div className="flex items-center gap-2 text-sm text-zinc-400">
          {author ? (
            <>
              <div className="w-6 h-6 rounded-full bg-pink-600/20 flex items-center justify-center text-xs text-pink-400 font-bold">
                {author.username.charAt(0).toUpperCase()}
              </div>
              <span className="font-medium text-zinc-300">{author.username}</span>
              {author.agent_verified && (
                <span className="text-xs bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-full border border-emerald-500/20">✓ MARA</span>
              )}
            </>
          ) : (
            <span className="text-zinc-500">Anonymous</span>
          )}
          <span className="text-zinc-600">·</span>
          <span className="text-zinc-500">{timeAgo(post.created_at)}</span>
        </div>
        {post.is_resolved && (
          <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-1 rounded-full">✓ Resolved</span>
        )}
      </div>

      <Link href={`/community/${post.id}`} className="block">
        <h3 className="text-lg font-semibold text-zinc-100 hover:text-pink-400 transition-colors leading-snug mb-2">{post.title}</h3>
      </Link>
      <p className="text-sm text-zinc-400 line-clamp-2 mb-3 leading-relaxed">{post.body}</p>

      <div className="flex flex-wrap items-center gap-2 mb-3">
        <CategoryBadge category={post.category} />
        {post.visa_subclass && <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full">SC{post.visa_subclass}</span>}
        {post.state && <span className="text-xs bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">{post.state}</span>}
        {post.points_score && <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full">{post.points_score} pts</span>}
        {(post.tags || []).slice(0, 3).map(tag => (
          <span key={tag} className="text-xs bg-zinc-800 text-zinc-500 px-2 py-0.5 rounded-full">#{tag}</span>
        ))}
      </div>

      <div className="flex items-center gap-4 text-sm text-zinc-500">
        <LikeButton type="post" targetId={post.id} userId={userId} likeCount={post.like_count} initialLiked={isLiked} />
        <Link href={`/community/${post.id}`} className="flex items-center gap-1.5 hover:text-zinc-300 transition-colors">
          💬 {post.reply_count} {post.reply_count === 1 ? 'reply' : 'replies'}
        </Link>
        <span className="flex items-center gap-1.5">👁 {post.view_count}</span>
      </div>
    </div>
  );
}
