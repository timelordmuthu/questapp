// frontend/src/api/client.ts
// Base axios instance with credentials (HttpOnly cookie) for all requests.

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true, // send HttpOnly session cookie
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor: redirect to /login on 401
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)
