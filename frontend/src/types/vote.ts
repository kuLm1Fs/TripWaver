export interface VoteRequest {
  itinerary_id: number
  plan_index: number
}

export interface VoteResponse {
  success: boolean
  message: string
  itinerary_id: number
  plan_index: number
  vote_stats: { plan_index: number; count: number }[]
}
