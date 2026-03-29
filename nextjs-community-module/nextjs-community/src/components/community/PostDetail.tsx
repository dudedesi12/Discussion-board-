'use client';

import { usePostDetail } from '@/lib/community/hooks';
import { LikeButton } from './LikeButton';
import { ReplyForm } from './ReplyForm';
import { CategoryBadge } from './CategoryFilter';
import Link from 'next/link';

function timeAgo(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
  return new Date(dateStr).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function PostDetail({ postId, userId }: { postId: string; userId?: string }) {
  const { post, replies, loading, addReply } = usePostDetail(postId);

  if (loading) return (
    <div className="animate-pulse space-y-4">
      <div className="h-8 bg-zinc-800 rounded-lg w-3/4" />
      <div className="h-4 bg-zinc-800 rounded w-1/2" />
      <div className="h-32 bg-zinc-800 rounded-lg" />
    </div>
  );

  if (!post) return <p className="text-zinc-500">Post not found.</p>;
  const author = post.is_anonymous ? null : post.author;

  return (
    <div className="space-y-6">
      <Link href="/community" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors">&larr; Back to Community</Link>

      <article className="border border-zinc-800 rounded-xl p-6 bg-zinc-900/50">
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <CategoryBadge category={post.category} />
          {post.visa_subclass && <span className="text-xs bg-blue-500/10 text-blue-400 px-2 py-0.5 rounded-full">SC{post.visa_subclass}</span>}
          {post.state && <span className="text-xs bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded-full">{post.state}</span>}
          {post.points_score && <span className="text-xs bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full">{post.points_score} pts</span>}
          {post.is_resolved && <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full">&check; Resolved</span>}
        </div>
        <h1 className="text-2xl font-bold text-zinc-100 mb-3 leading-tight">{post.title}</h1>
        <div className="flex items-center gap-2 text-sm text-zinc-400 mb-5">
          {author ? (
            <><span className="font-medium text-zinc-300">{author.username}</span>
            {author.agent_verified && <span className="text-xs bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-full border border-emerald-500/20">&check; MARA</span>}</>
          ) : <span className="text-zinc-500">Anonymous</span>}
          <span className="text-zinc-600">&middot;</span><span>{timeAgo(post.created_at)}</span>
          <span className="text-zinc-600">&middot;</span><span>{post.view_count} views</span>
        </div>
        <div className="prose prose-invert prose-sm max-w-none text-zinc-300 leading-relaxed whitespace-pre-wrap">{post.body}</div>
        <div className="flex items-center gap-4 mt-5 pt-4 border-t border-zinc-800">
          <LikeButton type="post" targetId={post.id} userId={userId} likeCount={post.like_count} />
          <span className="text-sm text-zinc-500">{post.reply_count} {post.reply_count === 1 ? 'reply' : 'replies'}</span>
        </div>
      </article>

      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-zinc-200">{replies.length} {replies.length === 1 ? 'Reply' : 'Replies'}</h2>
        {replies.map(reply => {
          const rAuthor = reply.is_anonymous ? null : reply.author;
          return (
            <div key={reply.id} className={`border rounded-xl p-5 ${reply.is_accepted ? 'border-emerald-500/30 bg-emerald-500/5' : 'border-zinc-800 bg-zinc-900/30'}`}>
              {reply.is_accepted && <div className="text-xs text-emerald-400 font-semibold mb-2">&check; Accepted Answer</div>}
              <div className="flex items-center gap-2 text-sm text-zinc-400 mb-3">
                {rAuthor ? (
                  <><span className="font-medium text-zinc-300">{rAuthor.username}</span>
                  {rAuthor.agent_verified && <span className="text-xs bg-emerald-500/10 text-emerald-400 px-1.5 py-0.5 rounded-full border border-emerald-500/20">&check; MARA</span>}</>
                ) : <span className="text-zinc-500">Anonymous</span>}
                <span className="text-zinc-600">&middot;</span><span>{timeAgo(reply.created_at)}</span>
              </div>
              <p className="text-sm text-zinc-300 whitespace-pre-wrap leading-relaxed">{reply.body}</p>
              <div className="mt-3"><LikeButton type="reply" targetId={reply.id} userId={userId} likeCount={reply.like_count} /></div>
            </div>
          );
        })}
      </div>

      <ReplyForm postId={postId} userId={userId} onSubmit={addReply} />
    </div>
  );
}
