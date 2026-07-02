import { defineStore } from "pinia"
import { ref, computed } from "vue"
import api from "../api"

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("civic_token") || null)
  const user = ref(JSON.parse(localStorage.getItem("civic_user") || "null"))

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role || null)
  const isCitizen = computed(() => role.value === "citizen")
  const isStaff = computed(() => role.value === "staff")
  const isAdmin = computed(() => role.value === "admin")

  async function login(email, password) {
    const { data } = await api.post("/auth/login", { email, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem("civic_token", data.token)
    localStorage.setItem("civic_user", JSON.stringify(data.user))
    return data.user
  }

  async function register(payload) {
    const { data } = await api.post("/auth/register", payload)
    token.value = data.token
    user.value = data.user
    localStorage.setItem("civic_token", data.token)
    localStorage.setItem("civic_user", JSON.stringify(data.user))
    return data.user
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem("civic_token")
    localStorage.removeItem("civic_user")
  }

  async function refreshMe() {
    const { data } = await api.get("/auth/me")
    user.value = data
    localStorage.setItem("civic_user", JSON.stringify(data))
  }

  return { token, user, isLoggedIn, role, isCitizen, isStaff, isAdmin, login, register, logout, refreshMe }
})
