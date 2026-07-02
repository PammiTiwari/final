<template>
  <div class="alert alert-warning similar-box">
    <div class="similar-title">⚠ Similar complaints already reported</div>
    <p class="similar-hint">Support an existing report with a "+1" instead of creating a duplicate — it helps the department prioritise.</p>

    <div class="similar-list">
      <div v-for="m in items" :key="m.id" class="similar-item">
        <div class="similar-info">
          <code class="cmp-id">{{ m.cmp_id }}</code>
          <span class="similar-text">{{ m.title }}</span>
          <span :class="['badge', `badge-${m.status}`]">{{ fmtStatus(m.status) }}</span>
        </div>
        <div class="similar-action">
          <span class="upvote-count">👍 {{ m.upvotes_count }}</span>
          <button class="btn btn-xs" :class="m.upvoted ? 'btn-success' : 'btn-outline'"
            :disabled="m.busy" @click="toggle(m)">
            {{ m.upvoted ? '✓ Supported' : '+1 Me too' }}
          </button>
        </div>
      </div>
    </div>

    <div class="similar-footer">
      <button class="btn btn-sm btn-primary" @click="$emit('proceed')">None of these — submit my complaint</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../api'
import { fmtStatus } from '../utils/status'

const props = defineProps({ matches: { type: Array, default: () => [] } })
const emit = defineEmits(['proceed', 'upvoted'])

// local copy so we can track per-item upvote/busy state
const items = ref([])
watch(() => props.matches, (m) => {
  items.value = m.map(x => ({ ...x, upvoted: false, busy: false }))
}, { immediate: true })

async function toggle(m) {
  m.busy = true
  try {
    const { data } = await api.post(`/requests/${m.id}/upvote`)
    m.upvoted = data.upvoted
    m.upvotes_count = data.upvotes_count
    if (data.upvoted) emit('upvoted', m)
  } finally {
    m.busy = false
  }
}
</script>

<style scoped>
.similar-box { text-align: left; }
.similar-title { font-weight: 800; margin-bottom: 0.2rem; }
.similar-hint { font-size: 0.8rem; font-weight: 500; margin-bottom: 0.75rem; opacity: 0.85; }
.similar-list { display: flex; flex-direction: column; gap: 0.5rem; }
.similar-item {
  display: flex; justify-content: space-between; align-items: center; gap: 0.75rem;
  background: #fff; border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 0.5rem 0.75rem;
}
.similar-info { display: flex; align-items: center; gap: 0.5rem; min-width: 0; }
.cmp-id { font-family: monospace; font-size: 0.75rem; background: var(--stone); padding: 0.1rem 0.35rem; border-radius: 4px; }
.similar-text { font-size: 0.83rem; font-weight: 600; color: var(--text); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.similar-action { display: flex; align-items: center; gap: 0.5rem; flex-shrink: 0; }
.upvote-count { font-size: 0.78rem; font-weight: 700; color: var(--text-muted); }
.similar-footer { margin-top: 0.85rem; }
</style>
