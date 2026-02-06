import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../api/client'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))
  
  const isAuthenticated = computed(() => !!accessToken.value)
  
  async function login(email, password) {
    const response = await api.post('/auth/login', { email, password })
    setTokens(response.data.access_token, response.data.refresh_token)
    await fetchUser()
  }
  
  async function register(email, password) {
    await api.post('/auth/register', { email, password })
    await login(email, password)
  }
  
  async function fetchUser() {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      logout()
    }
  }
  
  async function refreshAccessToken() {
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: refreshToken.value
      })
      setTokens(response.data.access_token, response.data.refresh_token)
      return true
    } catch (error) {
      logout()
      return false
    }
  }
  
  function setTokens(access, refresh) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }
  
  async function logout() {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      // Ignore logout errors
    }
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }
  
  // Initialize user on page load
  if (accessToken.value) {
    fetchUser()
  }
  
  return {
    user,
    accessToken,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
    refreshAccessToken
  }
})
