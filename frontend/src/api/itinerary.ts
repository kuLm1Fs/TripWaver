import axios from 'axios'
import type { ItineraryRequest, ItineraryResponse } from '@/types/itinerary'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const planItinerary = async (data: ItineraryRequest): Promise<ItineraryResponse> => {
  const response = await apiClient.post<ItineraryResponse>('/itineraries/plan', data)
  return response.data
}
