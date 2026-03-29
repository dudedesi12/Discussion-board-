import { createServerSupabase } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import { CreatePostForm } from '@/components/community/CreatePostForm';
import Link from 'next/link';

export const metadata = {
  title: 'Create Post | Community | AussieImmigrant Tracker',
  description: 'Share your visa journey, ask questions, or help others navigate Australian skilled migration.',
};

export default async function CreatePostPage() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect('/login?redirect=/community/create');

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <Link href="/community" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-6 block">&larr; Back to Community</Link>
        <h1 className="text-2xl font-bold mb-2">Create a Post</h1>
        <p className="text-sm text-zinc-500 mb-8">Share your experience, ask a question, or update the community.</p>
        <CreatePostForm userId={user.id} />
      </div>
    </div>
  );
}
