<template>
  <div class="auth-page">
    <div class="auth-card">
      <div class="auth-logo">
        <div class="logo-icon">CP</div>
        <span>Cyber Panchayat</span>
      </div>
      <h1 class="auth-title">Reset Password</h1>
      <p class="auth-sub">Enter your email and we will send you an OTP to reset your password.</p>

      <div v-if="success" class="alert alert-success">{{ success }}</div>
      <div v-if="error" class="alert alert-error">{{ error }}</div>

      <div class="form-group">
        <label>Email Address</label>
        <input v-model="email" type="email" class="form-control" placeholder="Enter your email address" />
      </div>
      <button class="btn btn-primary btn-full" @click="sendOtp" :disabled="loading">
        {{ loading ? 'Sending...' : 'Send OTP' }}
      </button>

      <div class="or-divider"><span>OR</span></div>

      <div class="form-group">
        <label>New Password</label>
        <div class="input-group">
          <input
            v-model="newPassword"
            :type="showPass ? 'text' : 'password'"
            class="form-control"
            placeholder="Enter new password"
          />
          <button type="button" class="input-group-btn" @click="showPass = !showPass">{{ showPass ? '◡' : '◉' }}</button>
        </div>
      </div>
      <div class="form-group">
        <label>Confirm New Password</label>
        <div class="input-group">
          <input
            v-model="confirmPassword"
            :type="showConfirm ? 'text' : 'password'"
            class="form-control"
            placeholder="Confirm new password"
          />
          <button type="button" class="input-group-btn" @click="showConfirm = !showConfirm">{{ showConfirm ? '◡' : '◉' }}</button>
        </div>
      </div>
      <button class="btn btn-primary btn-full" @click="resetPassword">Reset Password</button>

      <p class="auth-switch">
        <router-link to="/login">← Back to Login</router-link>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const email = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const showPass = ref(false)
const showConfirm = ref(false)
const loading = ref(false)
const success = ref('')
const error = ref('')

function sendOtp() {
  if (!email.value) { error.value = 'Please enter your email'; return }
  loading.value = true
  setTimeout(() => {
    loading.value = false
    success.value = 'OTP sent to ' + email.value + '. (Demo: Use OTP 123456)'
  }, 1200)
}

function resetPassword() {
  error.value = ''
  if (!newPassword.value || !confirmPassword.value) { error.value = 'Please fill all fields'; return }
  if (newPassword.value !== confirmPassword.value) { error.value = 'Passwords do not match'; return }
  success.value = 'Password reset successfully! You can now login with your new password.'
  newPassword.value = ''
  confirmPassword.value = ''
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  background: #FFF0F6;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1rem;
}
.auth-card {
  background: #fff;
  border: 1px solid #FFD1E6;
  border-radius: 10px;
  padding: 2rem 2.25rem;
  width: 100%;
  max-width: 420px;
}
.auth-logo {
  display: flex; align-items: center; gap: 0.5rem;
  margin-bottom: 1.5rem;
}
.auth-logo .logo-icon {
  width: 28px; height: 28px; background: #5C1A41; color: #fff;
  border-radius: 6px; display: flex; align-items: center; justify-content: center;
  font-weight: 900; font-size: 0.62rem;
}
.auth-logo span { font-weight: 800; font-size: 1rem; color: #5C1A41; }
.auth-title { font-size: 1.4rem; font-weight: 800; color: #5C1A41; margin-bottom: 0.25rem; }
.auth-sub { font-size: 0.875rem; color: #B0708F; margin-bottom: 1.5rem; line-height: 1.6; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 0.82rem; font-weight: 600; color: #5C1A41; margin-bottom: 0.3rem; }
.btn-full { width: 100%; justify-content: center; padding: 0.65rem; font-size: 0.9rem; }
.or-divider {
  text-align: center; margin: 1.25rem 0; position: relative;
  color: #D69AB8; font-size: 0.8rem; font-weight: 600;
}
.or-divider::before, .or-divider::after {
  content: ''; position: absolute; top: 50%;
  width: 40%; height: 1px; background: #FFD1E6;
}
.or-divider::before { left: 0; }
.or-divider::after { right: 0; }
.or-divider span { background: #fff; padding: 0 0.6rem; }
.auth-switch { text-align: center; margin-top: 1.25rem; font-size: 0.82rem; }
.auth-switch a { color: #5C1A41; font-weight: 700; text-decoration: underline; }

@media (max-width: 480px) {
  .auth-page { align-items: flex-start; padding-top: 2.5rem; }
}
</style>
