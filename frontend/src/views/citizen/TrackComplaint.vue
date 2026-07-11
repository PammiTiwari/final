<template>
  <div class="track-page">
    <!-- Which layout to show depends on which route got us here — not on
         whether a login session happens to exist — so the landing page's
         Track Complaint link is always the plain public page, even if an
         old session token is still sitting in localStorage. -->
    <div v-if="route.name === 'track-public'" class="public-track">
      <router-link to="/" class="back-home">← Back to Home</router-link>
      <div class="track-content">
        <div v-if="!result" class="track-card">
          <h2 class="track-title">Track Your Complaint</h2>
          <p class="track-sub">Enter your complaint ID to check the status</p>
          <SearchSection @found="setResult" />
        </div>
        <TrackResultCard v-else :result="result" @close="result = null" />
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
          <div v-if="!result" class="card modal-w-xl">
            <SearchSection @found="setResult" />
          </div>
          <TrackResultCard v-else :result="result" @close="result = null" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineComponent } from 'vue'
import { useRoute } from 'vue-router'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import TrackResultCard from '../../components/TrackResultCard.vue'
import api from '../../api'
import { h } from 'vue'

const route = useRoute()
const result = ref(null)

function setResult(r) { result.value = r }

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
.public-track { min-height: 100vh; background: var(--bg); position: relative; }
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
.track-content { padding: 6rem 2rem 4rem; display: flex; justify-content: center; align-items: flex-start; }
.track-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg); padding: 2rem; width: 100%; max-width: 540px; box-shadow: var(--shadow); }
.track-title { font-family: var(--font-heading); font-size: 1.5rem; font-weight: 400; color: var(--text); margin-bottom: 0.35rem; }
.track-sub { font-size: 0.875rem; color: var(--text-muted); margin-bottom: 1.5rem; }
</style>
