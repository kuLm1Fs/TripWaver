import axios from 'axios'
import type {
  ItineraryRequest,
  ItineraryResponse,
  CandidatesResponse,
  CustomPlanRequest,
} from '@/types/itinerary'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 120000, // 真实模式生成行程较慢，超时设为2分钟
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器：自动带 token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截器：401 自动跳转登录
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export { apiClient }

export const planItinerary = async (data: ItineraryRequest): Promise<ItineraryResponse> => {
  const response = await apiClient.post<ItineraryResponse>('/itineraries/plan', data)
  return response.data
}

export const deleteItinerary = async (id: number): Promise<void> => {
  await apiClient.delete(`/itineraries/${id}`)
}

export const getCandidates = async (params: ItineraryRequest): Promise<CandidatesResponse> => {
  const response = await apiClient.get<CandidatesResponse>('/itineraries/candidates', { params })
  return response.data
}

export const planCustomItinerary = async (data: CustomPlanRequest): Promise<ItineraryResponse> => {
  const response = await apiClient.post<ItineraryResponse>('/itineraries/custom', data)
  return response.data
}
