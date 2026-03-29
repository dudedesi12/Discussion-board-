'use client';

import { use } from 'react';
import { PostDetail } from '@/components/community/PostDetail';

export default function PostPage({ params }: { params: Promise<{ postId: string }> }) {
  const { postId } = use(params);
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <PostDetail postId={postId} />
      </div>
    </div>
  );
}
