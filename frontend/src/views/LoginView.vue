<template>
  <div class="auth-page">
    <router-link to="/" class="back-home">← Back to Home</router-link>
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon">CP</div>
        <span>Cyber Panchayat</span>
      </div>
      <h1 class="auth-title">Welcome Back!</h1>
      <p class="auth-sub">Login to your account</p>

      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label>Email Address</label>
          <input v-model="form.email" type="email" class="form-control" placeholder="Enter your email" required />
        </div>
        <div class="form-group">
          <label>Password</label>
          <div class="input-group">
            <input
              v-model="form.password"
              :type="showPassword ? 'text' : 'password'"
              class="form-control"
              placeholder="Enter your password"
              required
            />
            <button type="button" class="input-group-btn" @click="showPassword = !showPassword">
              {{ showPassword ? '◡' : '◉' }}
            </button>
          </div>
        </div>

        <div class="auth-row">
          <label class="remember-label">
            <input type="checkbox" v-model="rememberMe" />
            <span>Remember Me</span>
          </label>
        </div>

        <button type="submit" class="btn btn-primary btn-full" :disabled="loading">
          {{ loading ? 'Logging in...' : 'Login' }}
        </button>
      </form>

      <p class="auth-switch">
        Don't have an account? <router-link to="/register">Register here</router-link>
      </p>

      <!-- Demo credentials -->
      <div class="demo-box">
        <p class="demo-title">Demo Credentials (click to fill)</p>
        <div v-for="cred in demoCredentials" :key="cred.email" class="demo-row" @click="fillDemo(cred)">
          <span class="demo-role">{{ cred.role }}</span>
          <span class="demo-email">{{ cred.email }}</span>
          <span class="demo-pass">{{ cred.password }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

const form = ref({ email: '', password: '' })
const showPassword = ref(false)
const rememberMe = ref(false)
const loading = ref(false)
const error = ref('')

const demoCredentials = [
  { role: 'Admin', email: 'admin@civic.gov', password: 'Admin@123' },
  { role: 'Officer', email: 'rajesh@civic.gov', password: 'Staff@123' },
  { role: 'Citizen', email: 'amit@gmail.com', password: 'Citizen@123' },
]

function fillDemo(cred) {
  form.value.email = cred.email
  form.value.password = cred.password
}

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form.value.email, form.value.password)
    if (auth.isCitizen) router.push('/dashboard')
    else if (auth.isStaff) router.push('/staff/dashboard')
    else if (auth.isAdmin) router.push('/admin/dashboard')
  } catch (e) {
    error.value = e.response?.data?.message || 'Login failed. Please check your credentials.'
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

.auth-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.25rem;
}
.remember-label {
  display: flex; align-items: center; gap: 0.4rem;
  font-size: 0.8rem; color: var(--text-muted); cursor: pointer;
}
.btn-full { width: 100%; justify-content: center; padding: 0.65rem; font-size: 0.9rem; }

.auth-switch {
  text-align: center; margin-top: 1.25rem;
  font-size: 0.82rem; color: var(--text-muted);
}
.auth-switch a { color: var(--primary); font-weight: 700; text-decoration: underline; }

.demo-box {
  margin-top: 1.25rem;
  background: var(--stone);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.85rem;
}
.demo-title { font-size: 0.72rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
.demo-row {
  display: flex; gap: 0.6rem; align-items: center;
  padding: 0.4rem 0.5rem; border-radius: var(--radius-sm);
  cursor: pointer; transition: 0.12s;
  font-size: 0.78rem;
}
.demo-row:hover { background: var(--accent); }
.demo-role { font-weight: 700; color: var(--primary); min-width: 50px; }
.demo-email { color: var(--text); flex: 1; }
.demo-pass { color: var(--text-muted); }

@media (max-width: 480px) {
  /* Vertically centering a tall card on a short phone screen pushes its top
     above y=0, where it gets clipped by the browser/notch chrome — start
     from the top instead on small screens. */
  .auth-page { align-items: flex-start; padding-top: 4.5rem; }
}
</style>
