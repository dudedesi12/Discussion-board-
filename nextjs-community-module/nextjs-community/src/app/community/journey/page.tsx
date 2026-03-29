import { createServerSupabase } from '@/lib/supabase/server';
import { redirect } from 'next/navigation';
import { JourneyPageClient } from './JourneyPageClient';
import Link from 'next/link';

export const metadata = {
  title: 'My Visa Journey | Community | AussieImmigrant Tracker',
  description: 'Track your Australian visa milestones and compare processing times.',
};

export default async function JourneyPage() {
  const supabase = await createServerSupabase();
  const { data: { user } } = await supabase.auth.getUser();
  if (!user) redirect('/login?redirect=/community/journey');

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Link href="/community" className="text-sm text-zinc-500 hover:text-zinc-300 transition-colors mb-6 block">&larr; Back to Community</Link>
        <JourneyPageClient userId={user.id} />
      </div>
    </div>
  );
}
