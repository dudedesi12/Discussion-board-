import { createClient } from '@/lib/supabase/client';
import type {
  CommunityPost, CommunityReply, CreatePost, CreateReply,
  JourneyMilestone, CreateJourneyMilestone, ProcessingStats, PostCategory,
} from '@/lib/supabase/types';

const supabase = createClient();

// ==================== POSTS ====================

export async function getPosts(options?: {
  category?: PostCategory;
  sort?: 'newest' | 'popular' | 'unanswered';
  tag?: string;
  page?: number;
  limit?: number;
}) {
  const { category, sort = 'newest', tag, page = 1, limit = 15 } = options || {};
  const from = (page - 1) * limit;
  const to = from + limit - 1;

  let query = supabase
    .from('community_posts')
    .select('*, author:community_profiles!author_id(id, username, avatar_url, role, agent_verified)', { count: 'exact' });

  if (category) query = query.eq('category', category);
  if (tag) query = query.contains('tags', [tag]);

  if (sort === 'popular') {
    query = query.order('like_count', { ascending: false });
  } else if (sort === 'unanswered') {
    query = query.eq('reply_count', 0).order('created_at', { ascending: false });
  } else {
    query = query.order('is_pinned', { ascending: false }).order('created_at', { ascending: false });
  }

  const { data, error, count } = await query.range(from, to);
  if (error) throw error;
  return { posts: data as CommunityPost[], total: count || 0 };
}

export async function getPost(postId: string) {
  const { data, error } = await supabase
    .from('community_posts')
    .select('*, author:community_profiles!author_id(id, username, avatar_url, role, agent_verified, occupation_name, state)')
    .eq('id', postId)
    .single();
  if (error) throw error;
  supabase.rpc('increment_view_count', { post_uuid: postId }).then();
  return data as CommunityPost;
}

export async function createPost(post: CreatePost) {
  const { data, error } = await supabase
    .from('community_posts').insert(post).select().single();
  if (error) throw error;
  return data as CommunityPost;
}

export async function deletePost(postId: string) {
  const { error } = await supabase.from('community_posts').delete().eq('id', postId);
  if (error) throw error;
}

export async function toggleResolve(postId: string, current: boolean) {
  const { error } = await supabase
    .from('community_posts').update({ is_resolved: !current }).eq('id', postId);
  if (error) throw error;
}

// ==================== REPLIES ====================

export async function getReplies(postId: string) {
  const { data, error } = await supabase
    .from('community_replies')
    .select('*, author:community_profiles!author_id(id, username, avatar_url, role, agent_verified)')
    .eq('post_id', postId)
    .order('is_accepted', { ascending: false })
    .order('created_at', { ascending: true });
  if (error) throw error;
  return data as CommunityReply[];
}

export async function createReply(reply: CreateReply) {
  const { data, error } = await supabase
    .from('community_replies').insert(reply)
    .select('*, author:community_profiles!author_id(id, username, avatar_url, role, agent_verified)')
    .single();
  if (error) throw error;
  return data as CommunityReply;
}

export async function acceptReply(replyId: string, postId: string) {
  await supabase.from('community_replies').update({ is_accepted: false }).eq('post_id', postId);
  const { error } = await supabase.from('community_replies').update({ is_accepted: true }).eq('id', replyId);
  if (error) throw error;
}

// ==================== LIKES ====================

export async function togglePostLike(postId: string, userId: string) {
  const { data: existing } = await supabase
    .from('community_likes').select('id').eq('user_id', userId).eq('post_id', postId).maybeSingle();
  if (existing) {
    await supabase.from('community_likes').delete().eq('id', existing.id);
    return false;
  } else {
    await supabase.from('community_likes').insert({ user_id: userId, post_id: postId });
    return true;
  }
}

export async function toggleReplyLike(replyId: string, userId: string) {
  const { data: existing } = await supabase
    .from('community_likes').select('id').eq('user_id', userId).eq('reply_id', replyId).maybeSingle();
  if (existing) {
    await supabase.from('community_likes').delete().eq('id', existing.id);
    return false;
  } else {
    await supabase.from('community_likes').insert({ user_id: userId, reply_id: replyId });
    return true;
  }
}

export async function getUserPostLikes(userId: string, postIds: string[]) {
  const { data } = await supabase
    .from('community_likes').select('post_id').eq('user_id', userId).in('post_id', postIds);
  return new Set((data || []).map(l => l.post_id));
}

// ==================== JOURNEY MILESTONES ====================

export async function getMyJourney(userId: string) {
  const { data, error } = await supabase
    .from('journey_milestones').select('*').eq('user_id', userId).order('created_at', { ascending: false });
  if (error) throw error;
  return data as JourneyMilestone[];
}

export async function upsertMilestone(milestone: CreateJourneyMilestone) {
  const { data, error } = await supabase
    .from('journey_milestones').upsert(milestone, { onConflict: 'id' }).select().single();
  if (error) throw error;
  return data as JourneyMilestone;
}

export async function getProcessingStats(filters?: {
  visa_subclass?: string;
  occupation_code?: string;
  state?: string;
}) {
  let query = supabase.from('processing_stats').select('*');
  if (filters?.visa_subclass) query = query.eq('visa_subclass', filters.visa_subclass);
  if (filters?.occupation_code) query = query.eq('occupation_code', filters.occupation_code);
  if (filters?.state) query = query.eq('state', filters.state);
  const { data, error } = await query.order('total_cases', { ascending: false });
  if (error) throw error;
  return data as ProcessingStats[];
}
