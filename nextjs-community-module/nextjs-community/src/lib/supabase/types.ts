export type UserRole = 'member' | 'agent' | 'admin';
export type AvailabilityStatus = 'available' | 'busy' | 'offline';
export type VisaSubclass = '189' | '190' | '491' | '482' | 'sid';
export type AustralianState = 'WA' | 'NSW' | 'VIC' | 'QLD' | 'SA' | 'TAS' | 'ACT' | 'NT';

export type PostCategory =
  | 'visa-journey' | 'state-nomination' | 'points-help'
  | 'skills-assessment' | 'eoi-updates' | 'agent-reviews'
  | 'job-market' | 'settlement' | 'general';

export type JourneyStatus =
  | 'eoi-submitted' | 'invited' | 'lodged' | 'waiting'
  | 's56-received' | 'granted' | 'refused' | 'withdrawn';

export type VerificationStatus = 'pending' | 'approved' | 'rejected';
export type ConsultationStatus = 'pending' | 'accepted' | 'declined' | 'completed';

export interface CommunityProfile {
  id: string;
  username: string;
  email: string | null;
  full_name: string | null;
  bio: string | null;
  location: string | null;
  avatar_url: string | null;
  role: UserRole;
  visa_subclass: VisaSubclass | null;
  occupation_code: string | null;
  occupation_name: string | null;
  state: AustralianState | null;
  points_score: number | null;
  onshore: boolean;
  agent_verified: boolean;
  mara_number: string | null;
  specializations: string | null;
  availability_status: AvailabilityStatus;
  created_at: string;
  last_seen: string | null;
  is_active: boolean;
}

export interface CommunityPost {
  id: string;
  author_id: string;
  title: string;
  body: string;
  category: PostCategory;
  tags: string[];
  like_count: number;
  reply_count: number;
  view_count: number;
  visa_subclass: VisaSubclass | null;
  state: AustralianState | null;
  occupation_code: string | null;
  points_score: number | null;
  is_anonymous: boolean;
  is_resolved: boolean;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
  author?: CommunityProfile;
}

export interface CommunityReply {
  id: string;
  post_id: string;
  author_id: string;
  body: string;
  like_count: number;
  is_anonymous: boolean;
  is_accepted: boolean;
  created_at: string;
  author?: CommunityProfile;
}

export interface CommunityLike {
  id: string;
  user_id: string;
  post_id: string | null;
  reply_id: string | null;
  created_at: string;
}

export interface JourneyMilestone {
  id: string;
  user_id: string;
  visa_subclass: VisaSubclass;
  occupation_code: string;
  occupation_name: string | null;
  state: AustralianState | null;
  points_score: number | null;
  onshore: boolean;
  eoi_submitted_at: string | null;
  invitation_received_at: string | null;
  visa_lodged_at: string | null;
  s56_received_at: string | null;
  s56_responded_at: string | null;
  medicals_completed_at: string | null;
  grant_received_at: string | null;
  status: JourneyStatus;
  is_anonymous: boolean;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProcessingStats {
  visa_subclass: VisaSubclass;
  occupation_code: string;
  occupation_name: string | null;
  state: AustralianState | null;
  total_cases: number;
  total_grants: number;
  avg_days_lodge_to_grant: number | null;
  avg_days_eoi_to_invite: number | null;
  min_grant_points: number | null;
  avg_grant_points: number | null;
}

export interface AgentVerification {
  id: string;
  user_id: string;
  mara_number: string;
  issuing_authority: string;
  expiry_date: string;
  document_url: string | null;
  status: VerificationStatus;
  reviewed_by: string | null;
  reviewed_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export interface ConsultationRequest {
  id: string;
  student_id: string;
  agent_id: string;
  topic: string;
  preferred_time: string | null;
  message: string | null;
  status: ConsultationStatus;
  created_at: string;
  responded_at: string | null;
}

export type CreatePost = Pick<CommunityPost,
  'title' | 'body' | 'category' | 'is_anonymous'
> & {
  author_id: string;
  tags?: string[];
  visa_subclass?: VisaSubclass;
  state?: AustralianState;
  occupation_code?: string;
  points_score?: number;
};

export type CreateReply = {
  post_id: string;
  author_id: string;
  body: string;
  is_anonymous?: boolean;
};

export type CreateJourneyMilestone = Omit<JourneyMilestone,
  'id' | 'created_at' | 'updated_at'
>;
