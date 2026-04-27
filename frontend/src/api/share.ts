import { apiClient } from './itinerary'
import type { CreateShareRequest, CreateShareResponse, ItineraryDetailResponse } from '@/types/share'

export const createShareLink = async (data: CreateShareRequest): Promise<CreateShareResponse> => {
  const response = await apiClient.post<CreateShareResponse>('/itinerary/share', data)
  return response.data
}

export const getSharedItinerary = async (shareId: string): Promise<ItineraryDetailResponse> => {
  const response = await apiClient.get<ItineraryDetailResponse>(`/itinerary/share/${shareId}`)
  return response.data
}
