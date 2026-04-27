import { apiClient } from './itinerary'
import type { SendCodeRequest, LoginRequest, LoginResponse } from '@/types/auth'

export const sendCode = async (data: SendCodeRequest) => {
  const response = await apiClient.post('/auth/send-code', data)
  return response.data
}

export const login = async (data: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/auth/login', data)
  return response.data
}
