# Prompt: Rebuild the Next.js Community Module into the Immi Flask Project

## Context

You are working on **ImmPink** — a Flask-based community platform for international students and immigrants. The existing project lives at the repository root with Flask, SQLAlchemy, Jinja2 templates, and Bootstrap 5.

There is a **Next.js + Supabase community module** (in `nextjs-community-module/`) that contains enhanced features we want to port back into the Flask app. Your job is to rebuild all the new features from that module **directly into the existing Flask project**, keeping the same tech stack (Flask, SQLAlchemy, Jinja2, Bootstrap 5, vanilla JS).

---

## Existing Flask Project Structure

```
app/
├── __init__.py          # Flask app factory, blueprints, extensions
├── models.py            # SQLAlchemy models
├── forms.py             # WTForms
├── main/routes.py       # Homepage, health, user search API
├── auth/routes.py       # Register, login, logout
├── posts/routes.py      # Discussion CRUD, likes, replies, resolve
├── messages/routes.py   # Direct messaging with conversations
├── users/routes.py      # Profiles, follow, verify, consultations
├── static/css/main.css
├── static/js/main.js
└── templates/
    ├── base.html
    ├── main/index.html
    ├── auth/login.html, register.html
    ├── posts/index.html, create.html, show.html
    ├── messages/inbox.html, compose.html, conversation.html
    └── users/profile.html, edit.html
```

### What Already Exists in Flask (DO NOT rebuild these):
- User auth (register/login/logout) with Flask-Login
- Two roles: `customer` (student) and `agent` (immigration advisor)
- Discussion posts with 7 categories (Housing, Employment, Immigration, Healthcare, Legal, Academics, General)
- Replies on posts
- Post & reply likes (toggle)
- Post resolved/unresolved toggle
- Anonymous posting & replying
- Direct messaging with conversation threading
- User profiles with role-specific fields
- Follow/unfollow agents
- Agent verification workflow
- Consultation requests (student → agent)
- View counts, like counts, reply counts
- Category filtering & sorting (newest, most liked, unanswered)
- Pagination (15 per page)

---

## NEW Features to Build (from the Next.js module)

### Feature 1: Expanded Immigration-Specific Categories

**Replace** the current 7 generic categories with these **9 immigration-specific** ones:

| Slug | Display Name | Emoji |
|------|-------------|-------|
| `visa-journey` | Visa Journey | ✈️ |
| `state-nomination` | State Nomination | 🏛️ |
| `points-help` | Points Help | 🧮 |
| `skills-assessment` | Skills Assessment | 📋 |
| `eoi-updates` | EOI Updates | 📊 |
| `agent-reviews` | Agent Reviews | ⭐ |
| `job-market` | Job Market | 💼 |
| `settlement` | Settlement | 🏠 |
| `general` | General | 💬 |

**Implementation:**
- Update the `Post` model's category choices
- Update the post creation form dropdown
- Update the category filter buttons on the posts listing page
- Update any category badge rendering in templates

---

### Feature 2: Post Metadata Fields (Visa Context)

Add immigration-specific metadata to each post so users can provide context about their situation.

**New fields on the `Post` model:**
- `visa_subclass` — TEXT, nullable. Allowed values: `'189'`, `'190'`, `'491'`, `'482'`, `'sid'` (Skills in Demand)
- `state` — TEXT, nullable. Australian states: `'WA'`, `'NSW'`, `'VIC'`, `'QLD'`, `'SA'`, `'TAS'`, `'ACT'`, `'NT'`
- `occupation_code` — TEXT, nullable. Free text (e.g., `"261313"`)
- `points_score` — INTEGER, nullable. User's points claim (e.g., `85`)

**Implementation:**
- Add columns to `Post` model via migration
- Add optional fields to the post creation form:
  - Visa subclass dropdown (189, 190, 491, 482, SID)
  - State dropdown (WA, NSW, VIC, QLD, SA, TAS, ACT, NT)
  - Points score number input
- Display these as small badges/pills on `PostCard` and `PostDetail` views:
  - Visa badge: e.g., "Visa 190" in pink
  - State badge: e.g., "NSW" in blue
  - Points badge: e.g., "85 pts" in purple

---

### Feature 3: Pinned Posts

**New field on `Post` model:**
- `is_pinned` — BOOLEAN, default `False`

**Implementation:**
- Admin-only action to pin/unpin posts
- Pinned posts appear at the top of the posts listing, before all other posts
- Display a pin icon/badge on pinned posts

---

### Feature 4: Accepted Answers (StackOverflow-style)

**New field on `Reply` model:**
- `is_accepted` — BOOLEAN, default `False`

**Implementation:**
- The **post author** can mark ONE reply as the accepted answer
- Only one reply per post can be accepted (accepting a new one removes the previous)
- Accepted replies display with a green highlight/border and a checkmark badge
- Accepted replies sort to the top of the replies list (above other replies)
- Route: `POST /posts/<post_id>/replies/<reply_id>/accept` (author only)
- Logic: Set all replies for that post to `is_accepted = False`, then set the chosen one to `True`

---

### Feature 5: Visa Journey Milestone Tracker (THE MAJOR NEW FEATURE)

This is a completely new feature. Users log their personal visa application milestones to track progress and (optionally) contribute anonymous data to community processing time statistics.

#### 5a. New Model: `JourneyMilestone`

```
Fields:
- id: Integer, primary key
- user_id: Foreign key → User, NOT NULL
- visa_subclass: TEXT, NOT NULL. Values: '189', '190', '491', '482', 'sid'
- occupation_code: TEXT, NOT NULL (e.g., "261313")
- occupation_name: TEXT, nullable (e.g., "Software Engineer")
- state: TEXT, nullable. Values: 'WA', 'NSW', 'VIC', 'QLD', 'SA', 'TAS', 'ACT', 'NT'
- points_score: INTEGER, nullable
- onshore: BOOLEAN, default True

Timeline dates (all nullable DATE fields):
- eoi_submitted_at: Date EOI was submitted
- invitation_received_at: Date invitation was received
- visa_lodged_at: Date visa application was lodged
- s56_received_at: Date Section 56 request was received
- s56_responded_at: Date Section 56 response was sent
- medicals_completed_at: Date medicals were completed
- grant_received_at: Date visa was granted

- status: TEXT, default 'eoi-submitted'
  Values: 'eoi-submitted', 'invited', 'lodged', 'waiting', 's56-received', 'granted', 'refused', 'withdrawn'
- is_anonymous: BOOLEAN, default True (if True, data is included in community stats)
- notes: TEXT, nullable (private notes)
- created_at: DateTime, default now
- updated_at: DateTime, default now, onupdate now
```

#### 5b. New Blueprint: `journey` (url_prefix: `/community/journey`)

**Routes:**

1. `GET /community/journey` — Journey dashboard page (login required)
   - **Tab 1: "My Journey"**
     - Lists all of the current user's milestones
     - Each milestone card shows:
       - Visa subclass badge + occupation code/name
       - State badge, points badge, onshore/offshore flag
       - Timeline pills: colored dots/badges for each date milestone that exists (EOI → Invitation → Lodged → S56 → S56 Response → Medicals → Grant)
       - Completed steps in green, pending in gray
       - Current status badge (color-coded: granted=green, refused=red, withdrawn=gray, etc.)
     - "+ Log New Journey" button to show the form
     - "Edit" button on each existing milestone

   - **Tab 2: "Community Processing Times"**
     - Shows aggregated anonymous processing statistics (see Feature 6)

2. `GET/POST /community/journey/create` — Create new milestone (login required)
   - Form with 3 sections:
     - **Visa Context**: visa_subclass (required dropdown), occupation_code (required text), occupation_name (optional), state (dropdown), points_score (number), onshore (radio: Onshore/Offshore)
     - **Timeline Milestones**: 7 date fields (all optional) — EOI Submitted, Invitation Received, Visa Lodged, S56 Received, S56 Responded, Medicals Completed, Grant Received
     - **Status & Privacy**: status (required dropdown), notes (optional textarea), is_anonymous (checkbox, default checked, label: "Include my anonymous data in community processing statistics")
   - On submit: create JourneyMilestone, redirect to journey dashboard

3. `GET/POST /community/journey/<int:id>/edit` — Edit milestone (login required, owner only)
   - Same form as create, pre-filled with existing data
   - On submit: update milestone, redirect to journey dashboard

4. `POST /community/journey/<int:id>/delete` — Delete milestone (login required, owner only)

#### 5c. New Form: `JourneyMilestoneForm`

```
Fields:
- visa_subclass: SelectField, required. Choices: [('189','Subclass 189'), ('190','Subclass 190'), ('491','Subclass 491'), ('482','Subclass 482'), ('sid','Skills in Demand')]
- occupation_code: StringField, required, max 10 chars
- occupation_name: StringField, optional, max 100 chars
- state: SelectField, optional. Choices: [('','-- Select --'), ('WA','WA'), ('NSW','NSW'), ('VIC','VIC'), ('QLD','QLD'), ('SA','SA'), ('TAS','TAS'), ('ACT','ACT'), ('NT','NT')]
- points_score: IntegerField, optional
- onshore: RadioField, choices: [('true','Onshore'), ('false','Offshore')], default 'true'
- eoi_submitted_at: DateField, optional
- invitation_received_at: DateField, optional
- visa_lodged_at: DateField, optional
- s56_received_at: DateField, optional
- s56_responded_at: DateField, optional
- medicals_completed_at: DateField, optional
- grant_received_at: DateField, optional
- status: SelectField, required. Choices: [('eoi-submitted','EOI Submitted'), ('invited','Invited'), ('lodged','Lodged'), ('waiting','Waiting'), ('s56-received','S56 Received'), ('granted','Granted'), ('refused','Refused'), ('withdrawn','Withdrawn')]
- is_anonymous: BooleanField, default True
- notes: TextAreaField, optional
```

---

### Feature 6: Community Processing Statistics (Aggregated View)

Display crowdsourced, anonymized visa processing time data from journey milestones where `is_anonymous = True`.

#### 6a. Statistics to Calculate

Group by `(visa_subclass, occupation_code, occupation_name, state)` and compute:

| Metric | Calculation |
|--------|------------|
| `total_cases` | COUNT of all milestones in group |
| `total_grants` | COUNT where `grant_received_at IS NOT NULL` |
| `avg_days_lodge_to_grant` | AVG days between `visa_lodged_at` and `grant_received_at` (only where both exist) |
| `avg_days_eoi_to_invite` | AVG days between `eoi_submitted_at` and `invitation_received_at` (only where both exist) |
| `min_grant_points` | MIN `points_score` where `grant_received_at IS NOT NULL` |
| `avg_grant_points` | AVG `points_score` where `grant_received_at IS NOT NULL` (rounded to int) |

#### 6b. Display

On the "Community Processing Times" tab of the journey page, show a table/card list with:
- Occupation name + code
- Visa subclass badge
- State badge
- Total cases count
- Avg days EOI → Invite
- Avg days Lodge → Grant
- Avg/Min grant points

#### 6c. Optional Filters

Allow filtering the stats by:
- Visa subclass dropdown
- Occupation code text search
- State dropdown

#### 6d. Implementation

- Query the `JourneyMilestone` model where `is_anonymous = True`
- Group and aggregate using SQLAlchemy (or raw SQL)
- Route: `GET /community/journey` (tab 2) or a separate `GET /community/journey/stats` endpoint
- Empty state: "No anonymous data available yet. Be the first to share your journey!"

---

### Feature 7: Enhanced User Profile Fields

**New fields on the `User` model:**

- `visa_subclass` — TEXT, nullable (replaces the generic `visa_type`)
- `occupation_code` — TEXT, nullable
- `occupation_name` — TEXT, nullable
- `state` — TEXT, nullable (Australian state)
- `points_score` — INTEGER, nullable
- `onshore` — BOOLEAN, default True
- `mara_number` — TEXT, nullable (for agents — MARA registration number)

**Implementation:**
- Add to User model via migration
- Add to profile edit form
- Display on user profile page with appropriate badges
- MARA number shown for verified agents

---

## Summary of All Changes

### Models to Modify:
1. **Post** — Add: `visa_subclass`, `state`, `occupation_code`, `points_score`, `is_pinned`. Update category choices.
2. **Reply** — Add: `is_accepted`
3. **User** — Add: `visa_subclass`, `occupation_code`, `occupation_name`, `state`, `points_score`, `onshore`, `mara_number`

### New Model:
4. **JourneyMilestone** — Full new model (see Feature 5a)

### New Blueprint:
5. **journey** — 4 routes: dashboard, create, edit, delete

### Forms to Modify:
6. **PostForm** — Add optional: visa_subclass, state, points_score dropdowns
7. **ProfileEditForm** — Add: visa_subclass, occupation_code, occupation_name, state, points_score, onshore, mara_number

### New Form:
8. **JourneyMilestoneForm** — Full new form (see Feature 5c)

### Templates to Modify:
9. **posts/index.html** — Updated categories, metadata badges on cards, pinned posts section
10. **posts/create.html** — New optional metadata fields
11. **posts/show.html** — Metadata badges, accepted answer UI, accept button for post author
12. **users/profile.html** — New profile fields display
13. **users/edit.html** — New profile form fields
14. **base.html** — Add "Journey Tracker" nav link

### New Templates:
15. **journey/dashboard.html** — Two-tab layout: My Journey + Community Stats
16. **journey/form.html** — Create/edit milestone form (3 sections)

### Routes to Modify:
17. **posts/routes.py** — Add `POST /posts/<id>/replies/<reply_id>/accept` route

### New Routes:
18. **journey/routes.py** — 4 new routes (see Feature 5b)

---

## Design Notes

- **Dark theme**: The existing app uses Bootstrap 5 light theme. The Next.js module uses a dark theme (zinc-950 background, pink accents). Choose one and be consistent. The current Flask app uses Bootstrap default (light), so keep it consistent unless you want to redesign.
- **Color scheme**: Pink (#ec4899) for primary actions, teal (#14b8a6) for journey features, green for accepted/granted, red for refused/rejected.
- **Timeline visualization**: For journey milestones, use a horizontal progress-bar style with colored dots for each step. Completed = green, current = yellow/amber, future = gray.
- **Responsive**: All new templates must work on mobile (Bootstrap grid).
- **CSRF**: All new forms must include `{{ form.hidden_tag() }}` for CSRF protection.
- **Flash messages**: Use Flask flash() for success/error feedback.
- **Auth guards**: All create/edit/delete routes require `@login_required`.
- **Owner guards**: Journey edit/delete must check `milestone.user_id == current_user.id`.
