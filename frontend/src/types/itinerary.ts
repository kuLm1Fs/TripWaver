export interface CandidatePlace {
  name: string
  category: string
  reason: string
}

export interface ItineraryItem {
  day: number
  title: string
  summary: string
  places: CandidatePlace[]
}

export interface ItineraryRequest {
  destination: string
  days: number
  interests: string[]
}

export interface ItineraryResponse {
  destination: string
  overview: string
  items: ItineraryItem[]
}
