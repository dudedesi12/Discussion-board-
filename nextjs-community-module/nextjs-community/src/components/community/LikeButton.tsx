'use client';

import { useState, useCallback } from 'react';
import { useLike } from '@/lib/community/hooks';

export function LikeButton({ type, targetId, userId, likeCount: initialCount, initialLiked = false }: {
  type: 'post' | 'reply'; targetId: string; userId?: string; likeCount: number; initialLiked?: boolean;
}) {
  const [liked, setLiked] = useState(initialLiked);
  const [count, setCount] = useState(initialCount);
  const { togglePostLike, toggleReplyLike, isPending } = useLike();

  const handleClick = useCallback(async () => {
    if (!userId) return;
    setLiked(!liked);
    setCount(prev => liked ? prev - 1 : prev + 1);
    const toggle = type === 'post' ? togglePostLike : toggleReplyLike;
    await toggle(targetId, userId, (serverLiked) => setLiked(serverLiked));
  }, [liked, userId, targetId, type, togglePostLike, toggleReplyLike]);

  return (
    <button onClick={handleClick} disabled={!userId || isPending}
      className={`flex items-center gap-1.5 transition-colors ${liked ? 'text-pink-400 hover:text-pink-300' : 'text-zinc-500 hover:text-zinc-300'} ${!userId ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}>
      <svg className="w-4 h-4" fill={liked ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z" />
      </svg>
      <span className="text-sm font-medium">{count}</span>
    </button>
  );
}
