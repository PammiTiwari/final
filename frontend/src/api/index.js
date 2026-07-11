import axios from "axios"

const api = axios.create({ baseURL: "/api" })

// Attach the JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("civic_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On an expired/invalid session, clear it and return to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("civic_token")
      localStorage.removeItem("civic_user")
      window.location.href = "/login"
    }
    return Promise.reject(err)
  }
)

export default api