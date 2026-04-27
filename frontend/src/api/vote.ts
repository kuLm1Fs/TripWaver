import { apiClient } from './itinerary'
import type { VoteRequest, VoteResponse } from '@/types/vote'

export const votePlan = async (data: VoteRequest): Promise<VoteResponse> => {
  const response = await apiClient.post<VoteResponse>('/itinerary/vote', data)
  return response.data
}
