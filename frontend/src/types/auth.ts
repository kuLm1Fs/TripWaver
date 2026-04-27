export interface SendCodeRequest {
  phone: string
}

export interface LoginRequest {
  phone: string
  code: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: number
  nickname: string | null
  avatar: string | null
}
