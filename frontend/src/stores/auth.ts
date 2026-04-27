import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as loginApi } from '@/api/auth'
import type { LoginResponse } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const userId = ref<number>(Number(localStorage.getItem('userId')) || 0)
  const nickname = ref<string>(localStorage.getItem('nickname') || '')
  const avatar = ref<string>(localStorage.getItem('avatar') || '')

  const isLoggedIn = computed(() => !!token.value)

  async function login(phone: string, code: string) {
    const res: LoginResponse = await loginApi({ phone, code })
    token.value = res.access_token
    userId.value = res.user_id
    nickname.value = res.nickname || ''
    avatar.value = res.avatar || ''
    localStorage.setItem('token', res.access_token)
    localStorage.setItem('userId', String(res.user_id))
    localStorage.setItem('nickname', res.nickname || '')
    localStorage.setItem('avatar', res.avatar || '')
  }

  function logout() {
    token.value = ''
    userId.value = 0
    nickname.value = ''
    avatar.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('userId')
    localStorage.removeItem('nickname')
    localStorage.removeItem('avatar')
  }

  return { token, userId, nickname, avatar, isLoggedIn, login, logout }
})
