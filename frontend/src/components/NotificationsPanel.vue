<template>
  <div class="notif-overlay" @click.self="$emit('close')">
    <div class="notif-panel">
      <div class="notif-header">
        <h3>Notifications</h3>
        <div style="display:flex;gap:0.5rem;align-items:center">
          <button v-if="unread > 0" class="btn btn-sm btn-outline" @click="markAll">Mark all read</button>
          <button class="modal-close" @click="$emit('close')">✕</button>
        </div>
      </div>
      <div v-if="loading" class="spinner" style="padding:2rem"></div>
      <div v-else-if="notifications.length === 0" class="empty-state" style="padding:2rem">
        <div class="empty-icon">🔔</div>
        <p>No notifications yet</p>
      </div>
      <div v-else class="notif-list">
        <div
          v-for="n in notifications"
          :key="n.id"
          class="notif-item"
          :class="{ unread: !n.is_read }"
          @click="markRead(n)"
        >
          <div class="notif-dot" :class="n.notif_type"></div>
          <div class="notif-body">
            <div class="notif-title">{{ n.title }}</div>
            <div class="notif-msg">{{ n.message }}</div>
            <div class="notif-time">{{ timeAgo(n.created_at) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import api from "../api"

const emit = defineEmits(["close", "read"])
const notifications = ref([])
const loading = ref(true)
const unread = ref(0)

onMounted(async () => {
  try {
    const { data } = await api.get("/notifications")
    notifications.value = data.notifications
    unread.value = data.unread_count
  } finally {
    loading.value = false
  }
})

async function markRead(n) {
  if (n.is_read) return
  await api.put(`/notifications/${n.id}/read`)
  n.is_read = true
  unread.value = Math.max(0, unread.value - 1)
  emit("read")
}

async function markAll() {
  await api.put("/notifications/0/read")
  notifications.value.forEach(n => { n.is_read = true })
  unread.value = 0
  emit("read")
}

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}
</script>

<style scoped>
.notif-overlay {
  position: fixed; inset: 0;
  background: rgba(0,0,0,0.3);
  z-index: 1500;
  display: flex;
  justify-content: flex-end;
  align-items: flex-start;
}
.notif-panel {
  width: 380px;
  max-height: 100vh;
  background: #fff;
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.notif-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.notif-header h3 { font-size: 1.05rem; font-weight: 800; color: var(--navy); }
.notif-list { overflow-y: auto; flex: 1; }
.notif-item {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  cursor: pointer;
  border-bottom: 1px solid var(--border);
  transition: var(--transition);
}
.notif-item:hover { background: var(--bg); }
.notif-item.unread { background: rgba(224,33,138,0.06); }
.notif-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
  background: var(--text-muted);
}
.notif-dot.request { background: var(--primary); }
.notif-dot.assignment { background: var(--secondary); }
.notif-dot.booking { background: var(--danger); }
.notif-dot.payment { background: #0E7A4F; }
.notif-dot.status { background: #A66E00; }
.notif-dot.refund { background: var(--warning); }
.notif-title { font-size: 0.88rem; font-weight: 700; color: var(--text); }
.notif-msg { font-size: 0.83rem; color: var(--text-muted); margin-top: 0.2rem; line-height: 1.4; }
.notif-time { font-size: 0.75rem; color: #D69AB8; margin-top: 0.3rem; }
</style>
