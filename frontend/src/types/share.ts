export interface CreateShareRequest {
  itinerary_id: number
  expire_days?: number
}

export interface CreateShareResponse {
  share_id: string
  share_url: string
  expire_at: string | null
  created_at: string
}

export interface Member {
  user_id: number
  nickname: string
  avatar: string | null
  joined_at: string
}

export interface VoteStat {
  plan_index: number
  count: number
}

export interface ItineraryDetailResponse {
  itinerary_id: number
  destination: string
  days: number
  interests: string[]
  plan_results: any
  is_locked: boolean
  locked_at: string | null
  final_plan_index: number | null
  creator_id: number
  creator_nickname: string
  created_at: string
  updated_at: string
  members: Member[]
  vote_stats: VoteStat[]
  current_user_vote: number | null
  is_creator: boolean
}
