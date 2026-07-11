<template>
  <div class="auth-page">
    <router-link to="/" class="back-home">← Back to Home</router-link>
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon">CP</div>
        <span>Cyber Panchayat</span>
      </div>
      <h1 class="auth-title">Create Your Account</h1>
      <p class="auth-sub">Join us and help your colony</p>

      <div v-if="error" class="alert alert-error">{{ error }}</div>
      <div v-if="success" class="alert alert-success">{{ success }}</div>

      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label>Full Name</label>
          <input v-model="form.name" type="text" class="form-control" placeholder="Enter full name" required />
        </div>
        <div class="form-group">
          <label>Email Address</label>
          <input v-model="form.email" type="email" class="form-control" placeholder="Enter email" required />
        </div>
        <div class="form-group">
          <label>Phone Number</label>
          <input v-model="form.phone" type="tel" class="form-control" placeholder="Enter 10-digit phone number" required />
        </div>
        <div class="form-group">
          <label>Ward</label>
          <select v-model="form.ward" class="form-control" required>
            <option value="" disabled>Select your ward</option>
            <option v-for="w in wards" :key="w" :value="w">{{ w }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Password</label>
          <div class="input-group">
            <input
              v-model="form.password"
              :type="showPass ? 'text' : 'password'"
              class="form-control"
              placeholder="Create password (min 6 characters)"
              required
            />
            <button type="button" class="input-group-btn" @click="showPass = !showPass">
              {{ showPass ? '◡' : '◉' }}
            </button>
          </div>
        </div>

        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          {{ loading ? 'Registering...' : 'Register' }}
        </button>
      </form>

      <p class="auth-switch">
        Already have an account? <router-link to="/login">Login here</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ name: '', email: '', phone: '', ward: '', password: '' })
const showPass = ref(false)
const loading = ref(false)
const error = ref('')
const success = ref('')
const wards = ['Ward-1', 'Ward-2', 'Ward-3']

async function handleRegister() {
  error.value = ''
  const name = form.value.name.trim()
  // A real name: letters (with spaces/dots/hyphens), never digits or symbols
  if (!/^[A-Za-z][A-Za-z\s.'-]{1,79}$/.test(name)) {
    error.value = 'Please enter a valid name — letters only, numbers are not a name'
    return
  }
  // Validate phone: exactly 10 digits
  const phone = form.value.phone.trim()
  if (!/^[0-9]{10}$/.test(phone)) {
    error.value = 'Please enter a valid 10-digit phone number'
    return
  }
  if (!form.value.ward) {
    error.value = 'Please select your ward'
    return
  }
  if (form.value.password.length < 6) {
    error.value = 'Password must be at least 6 characters'
    return
  }
  loading.value = true
  try {
    await auth.register({
      name,
      email: form.value.email.trim(),
      phone,
      ward: form.value.ward,
      password: form.value.password,
    })
    router.push('/dashboard')
  } catch (e) {
    error.value = e.response?.data?.message || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
  position: relative;
}
.back-home {
  position: fixed;
  top: 1.25rem;
  left: 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text);
  text-decoration: none;
  background: #fff;
  border: 1.5px solid var(--border);
  border-radius: 999px;
  padding: 0.45rem 1rem;
  transition: all 0.15s;
  z-index: 10;
}
.back-home:hover {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}
.auth-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 2rem 2.25rem;
  width: 100%;
  max-width: 420px;
  box-shadow: var(--shadow);
}
.auth-logo {
  display: flex; align-items: center; gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.auth-logo .logo-icon {
  width: 28px; height: 28px; background: var(--primary); color: #fff;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.62rem;
}
.auth-logo span { font-weight: 700; font-size: 1rem; color: var(--primary); }
.auth-title { font-size: 1.4rem; font-weight: 600; color: var(--text); margin-bottom: 0.25rem; }
.auth-sub { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1.5rem; }

.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: var(--text); margin-bottom: 0.3rem; }

.btn-full { width: 100%; justify-content: center; padding: 0.65rem; font-size: 0.9rem; margin-top: 0.5rem; }

.auth-switch {
  text-align: center; margin-top: 1.25rem;
  font-size: 0.82rem; color: var(--text-muted);
}
.auth-switch a { color: var(--primary); font-weight: 700; text-decoration: underline; }

@media (max-width: 480px) {
  .auth-page { align-items: flex-start; padding-top: 4.5rem; }
}
</style>
