# immi-pink Community Module

> Flask Discussion Board → Next.js + Supabase rebuild

## Quick Start

1. **Run SQL migration** → Copy `supabase/migrations/001_community_schema.sql` into Supabase SQL Editor and execute
2. **Install dep** → `npm install @supabase/ssr`
3. **Merge into immi-pink** → Copy `src/` contents into your existing project
4. **Add nav link** → Point "Community" to `/community`
5. **Deploy** → `git push` to Vercel

## 20 Files

- 1 SQL migration (7 tables, triggers, views, RLS)
- 3 Supabase lib files (client, server, types)
- 2 Community lib files (queries, hooks)
- 8 React components
- 5 Next.js page routes
- 1 README

## Features

| Feature | Route |
|---|---|
| Post listing with filters | `/community` |
| Post detail with replies | `/community/[postId]` |
| Create post | `/community/create` |
| Journey milestone tracker | `/community/journey` |
| Community processing stats | `/community/journey` (tab) |

## What's New vs Flask

- 9 immigration-specific categories
- Visa/state/points metadata per post
- Journey milestones → crowdsourced processing data
- Processing stats aggregation view
- Accepted answers (StackOverflow-style)
- Supabase triggers auto-update counters
- RLS policies baked in
- Optimistic UI for likes
