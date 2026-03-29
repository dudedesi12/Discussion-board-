'use client';

import { useState, useEffect, useCallback, useTransition } from 'react';
import * as queries from './queries';
import type { CommunityPost, CommunityReply, PostCategory, JourneyMilestone, ProcessingStats } from '@/lib/supabase/types';

export function usePosts(options?: { category?: PostCategory; sort?: 'newest' | 'popular' | 'unanswered'; tag?: string }) {
  const [posts, setPosts] = useState<CommunityPost[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchPosts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await queries.getPosts({ ...options, page });
      setPosts(result.posts);
      setTotal(result.total);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [options?.category, options?.sort, options?.tag, page]);

  useEffect(() => { fetchPosts(); }, [fetchPosts]);
  return { posts, total, page, setPage, loading, error, refresh: fetchPosts };
}

export function usePostDetail(postId: string) {
  const [post, setPost] = useState<CommunityPost | null>(null);
  const [replies, setReplies] = useState<CommunityReply[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [p, r] = await Promise.all([queries.getPost(postId), queries.getReplies(postId)]);
        setPost(p);
        setReplies(r);
      } catch (err) { console.error(err); }
      finally { setLoading(false); }
    }
    load();
  }, [postId]);

  const addReply = useCallback(async (reply: { post_id: string; author_id: string; body: string; is_anonymous?: boolean }) => {
    const newReply = await queries.createReply(reply);
    setReplies(prev => [...prev, newReply]);
    setPost(prev => prev ? { ...prev, reply_count: prev.reply_count + 1 } : prev);
    return newReply;
  }, []);

  return { post, replies, loading, addReply, setPost, setReplies };
}

export function useLike() {
  const [isPending, startTransition] = useTransition();
  const togglePostLike = useCallback(async (postId: string, userId: string, onToggle: (liked: boolean) => void) => {
    startTransition(async () => {
      const liked = await queries.togglePostLike(postId, userId);
      onToggle(liked);
    });
  }, []);
  const toggleReplyLike = useCallback(async (replyId: string, userId: string, onToggle: (liked: boolean) => void) => {
    startTransition(async () => {
      const liked = await queries.toggleReplyLike(replyId, userId);
      onToggle(liked);
    });
  }, []);
  return { togglePostLike, toggleReplyLike, isPending };
}

export function useJourney(userId: string | null) {
  const [milestones, setMilestones] = useState<JourneyMilestone[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!userId) { setLoading(false); return; }
    queries.getMyJourney(userId).then(data => { setMilestones(data); setLoading(false); });
  }, [userId]);

  const save = useCallback(async (milestone: any) => {
    const saved = await queries.upsertMilestone(milestone);
    setMilestones(prev => {
      const idx = prev.findIndex(m => m.id === saved.id);
      if (idx >= 0) { const next = [...prev]; next[idx] = saved; return next; }
      return [saved, ...prev];
    });
    return saved;
  }, []);

  return { milestones, loading, save };
}

export function useProcessingStats(filters?: { visa_subclass?: string; occupation_code?: string; state?: string }) {
  const [stats, setStats] = useState<ProcessingStats[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    queries.getProcessingStats(filters).then(data => { setStats(data); setLoading(false); });
  }, [filters?.visa_subclass, filters?.occupation_code, filters?.state]);
  return { stats, loading };
}
