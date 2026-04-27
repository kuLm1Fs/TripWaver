export interface CandidatePlace {
  name: string
  category: string
  reason: string
  address?: string
  longitude?: number
  latitude?: number
  price?: string
  business_hours?: string
  tags?: string[]
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
  latitude?: number
  longitude?: number
  address?: string
  range_mode: 'walking' | 'transit'
  range_minutes: number
  custom_tags: string[]
}

export interface PlanOption {
  title: string
  description: string
  items: ItineraryItem[]
}

export interface ItineraryResponse {
  itinerary_id?: number
  destination: string
  days?: number
  overview: string
  items: ItineraryItem[]
  plan_options?: PlanOption[]
}

export interface ItinerarySummary {
  id: number
  destination: string
  days: number
  interests: string[]
  is_locked: boolean
  created_at: string
}

export interface RoutePoint {
  lng: number
  lat: number
}

export interface RouteSegment {
  from: number
  to: number
  points: RoutePoint[]
  distance: number
  duration: number
  from_name?: string
  to_name?: string
}

export interface RouteResponse {
  segments: RouteSegment[]
  total_distance: number
  total_duration: number
}
