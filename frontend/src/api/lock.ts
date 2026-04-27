import { apiClient } from './itinerary'

export interface LockResponse {
  success: boolean
  message: string
  is_locked: boolean
  final_plan_index: number | null
}

export const lockItinerary = async (
  itineraryId: number,
  action: 'lock' | 'unlock' = 'lock',
  planIndex?: number,
): Promise<LockResponse> => {
  const params = new URLSearchParams()
  params.append('itinerary_id', String(itineraryId))
  params.append('action', action)
  if (planIndex !== undefined) {
    params.append('plan_index', String(planIndex))
  }
  const response = await apiClient.post<LockResponse>(`/itinerary/lock?${params.toString()}`)
  return response.data
}
