<template>
  <div class="track-page">
    <!-- Public view or authenticated view -->
    <div v-if="!auth.isLoggedIn" class="public-track">
      <nav class="land-nav">
        <div class="land-brand">
          <div class="brand-icon">CP</div>
          <span class="brand-name">Cyber Panchayat</span>
        </div>
        <div>
          <router-link to="/login" class="btn-nav-login">Login</router-link>
          <router-link to="/register" class="btn-nav-register ml-3">Register</router-link>
        </div>
      </nav>
      <div class="track-content">
        <div class="track-card">
          <h2 class="track-title">Track Your Complaint</h2>
          <p class="track-sub">Enter your complaint ID to check the status</p>
          <SearchSection @found="setResult" />
        </div>
      </div>
    </div>

    <!-- Logged-in layout -->
    <div v-else class="app-layout">
      <AppSidebar />
      <div class="main-content">
        <AppTopbar title="Track Complaint" />
        <div class="content-area">
          <div class="page-header">
            <div class="page-header-left">
              <p>Enter your complaint ID to check the current status</p>
            </div>
          </div>
          <div class="card modal-w-xl">
            <SearchSection @found="setResult" />
          </div>
        </div>
      </div>
    </div>

    <!-- Result shown in modal-style -->
    <div v-if="result" class="modal-overlay" @click.self="result = null">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h2>{{ result.cmp_id }} — Complaint Details</h2>
          <button class="modal-close" @click="result = null">&#x2715;</button>
        </div>

        <div class="flex gap-2 mb-4">
          <span :class="['badge', `badge-${result.status}`]">{{ fmtStatus(result.status) }}</span>
          <span :class="['badge', `badge-${result.priority}`]">{{ result.priority }}</span>
        </div>

        <div v-if="result.status === 'on_hold_weather'" class="alert alert-info">
          &#9729; <strong>On hold — weather restrictions.</strong> {{ result.hold_reason }}
        </div>

        <div class="detail-row"><div class="detail-label">Category</div><div class="detail-value capitalize">{{ result.category }}</div></div>
        <div class="detail-row"><div class="detail-label">Location</div><div class="detail-value">{{ result.address }}</div></div>
        <div class="detail-row"><div class="detail-label">Department</div><div class="detail-value">{{ result.department }}</div></div>
        <div class="detail-row"><div class="detail-label">Description</div><div class="detail-value">{{ result.description }}</div></div>
        <div class="detail-row"><div class="detail-label">Submitted On</div><div class="detail-value">{{ fmtDate(result.created_at) }}</div></div>
        <div class="detail-row" v-if="result.assignment">
          <div class="detail-label">Assigned To</div>
          <div class="detail-value">{{ result.assignment.staff_name }} ({{ result.assignment.staff_department }})</div>
        </div>
        <div class="detail-row" v-if="result.resolved_at">
          <div class="detail-label">Resolved On</div>
          <div class="detail-value">{{ fmtDate(result.resolved_at) }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineComponent } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'
import { fmtStatus } from '../../utils/status'
import { h } from 'vue'

const auth = useAuthStore()
const result = ref(null)

function setResult(r) { result.value = r }
function fmtDate(d) {
  return new Date(d).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

// Inline search component
const SearchSection = defineComponent({
  emits: ['found'],
  setup(_, { emit }) {
    const cmpId = ref('')
    const loading = ref(false)
    const error = ref('')

    async function search() {
      error.value = ''
      if (!cmpId.value.trim()) { error.value = 'Please enter a complaint ID'; return }
      loading.value = true
      try {
        const res = await api.get(`/track?id=${cmpId.value.trim().toUpperCase()}`)
        emit('found', res.data)
      } catch (e) {
        error.value = e.response?.data?.message || 'Complaint not found'
      } finally {
        loading.value = false
      }
    }

    return () => h('div', [
      error.value ? h('div', { class: 'alert alert-error', style: 'margin-bottom:1rem' }, error.value) : null,
      h('div', { style: 'display:flex; gap:0.75rem; align-items:flex-end' }, [
        h('div', { class: 'form-group', style: 'flex:1; margin:0' }, [
          h('label', { style: 'display:block; font-size:0.82rem; font-weight:600; margin-bottom:0.3rem' }, 'Complaint ID'),
          h('input', {
            class: 'form-control',
            placeholder: 'Enter Complaint ID (e.g. CMP0001)',
            value: cmpId.value,
            onInput: e => { cmpId.value = e.target.value },
            onKeydown: e => { if (e.key === 'Enter') search() },
          }),
        ]),
        h('button', {
          class: 'btn btn-primary',
          onClick: search,
          disabled: loading.value,
          style: 'flex-shrink:0; padding:0.55rem 1.25rem',
        }, loading.value ? 'Searching...' : 'Search'),
      ]),
    ])
  },
})
</script>

<style scoped>
.public-track { min-height: 100vh; background: var(--bg); }
.land-nav {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.85rem 2rem; background: rgba(255,255,255,0.85); backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
}
.land-brand { display: flex; align-items: center; gap: 0.55rem; }
.brand-icon {
  width: 28px; height: 28px; background: var(--gradient-accent); color: #fff;
  border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.6rem; box-shadow: var(--shadow-accent);
}
.brand-name { font-family: var(--font-heading); font-weight: 400; font-size: 1rem; color: var(--text); }
.btn-nav-login { padding: 0.45rem 1.1rem; font-size: 0.875rem; font-weight: 600; border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text); transition: var(--transition); }
.btn-nav-login:hover { border-color: var(--primary); color: var(--primary); background: var(--accent); }
.btn-nav-register { padding: 0.45rem 1.1rem; font-size: 0.875rem; font-weight: 600; background: var(--gradient-accent); color: #fff; border-radius: var(--radius-sm); box-shadow: var(--shadow-accent); transition: var(--transition); }
.btn-nav-register:hover { filter: brightness(1.08); transform: translateY(-1px); }
.track-content { padding: 4rem 2rem; display: flex; justify-content: center; align-items: flex-start; }
.track-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 2rem; width: 100%; max-width: 540px; box-shadow: var(--shadow); }
.track-title { font-family: var(--font-heading); font-size: 1.5rem; font-weight: 400; color: var(--text); margin-bottom: 0.35rem; }
.track-sub { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1.5rem; }
</style>
