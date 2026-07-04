<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Notifications" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Stay updated on your complaints and activities</p>
          </div>
          <button class="btn btn-secondary" @click="markAllRead" v-if="unreadCount > 0">
            Mark All Read
          </button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="notif-list">
          <div v-if="!notifications.length" class="empty-state">
            <div class="empty-icon">&#9993;</div>
            <p>No notifications yet</p>
          </div>
          <div
            v-for="n in notifications"
            :key="n.id"
            class="notif-card card"
            :class="{ unread: !n.is_read }"
            @click="markRead(n)"
          >
            <div class="notif-dot-wrap">
              <div class="notif-type-icon" :class="n.notif_type">
                {{ typeIcon(n.notif_type) }}
              </div>
              <div v-if="!n.is_read" class="unread-dot"></div>
            </div>
            <div class="notif-body">
              <div class="notif-title">{{ n.title }}</div>
              <div class="notif-msg">{{ n.message }}</div>
              <div class="notif-time">{{ fmtDate(n.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'
import api from '../api'

const loading = ref(true)
const notifications = ref([])
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

onMounted(async () => {
  try {
    const res = await api.get('/notifications')
    notifications.value = res.data.notifications || []
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

async function markRead(n) {
  if (n.is_read) return
  try {
    await api.put(`/notifications/${n.id}/read`)
    n.is_read = true
  } catch (e) { console.error(e) }
}

async function markAllRead() {
  try {
    await api.put('/notifications/0/read')
    notifications.value.forEach(n => n.is_read = true)
  } catch (e) { console.error(e) }
}

function typeIcon(type) {
  const icons = { info: 'i', success: '✓', warning: '!', error: '✕', assignment: '→', status: '⊙', request: '+' }
  return icons[type] || 'i'
}

function fmtDate(d) {
  return new Date(d).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.notif-list { display: flex; flex-direction: column; gap: 0.6rem; max-width: 680px; }
.notif-card { display: flex; gap: 0.85rem; align-items: flex-start; cursor: pointer; transition: 0.12s; padding: 1rem 1.25rem; }
.notif-card.unread { background: #FFF0F6; border-left: 3px solid #FFB400; }
.notif-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
.notif-dot-wrap { position: relative; flex-shrink: 0; }
.notif-type-icon {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.75rem; font-weight: 800;
}
.notif-type-icon.info { background: #FFF3DA; color: #A66E00; }
.notif-type-icon.success { background: #D7F5E5; color: #0E7A4F; }
.notif-type-icon.warning { background: #FFE0EE; color: #A66E00; }
.notif-type-icon.assignment { background: #FFE3ED; color: #b0123f; }
.notif-type-icon.status { background: #DFF7EC; color: #0E7A4F; }
.notif-type-icon.request { background: #FFF3DA; color: #A66E00; }
.unread-dot { width: 8px; height: 8px; background: #FFB400; border-radius: 50%; position: absolute; top: -2px; right: -2px; border: 1.5px solid #fff; }
.notif-body { flex: 1; }
.notif-title { font-size: 0.875rem; font-weight: 700; color: #5C1A41; margin-bottom: 0.2rem; }
.notif-msg { font-size: 0.82rem; color: #9B2C6F; line-height: 1.5; }
.notif-time { font-size: 0.72rem; color: #D69AB8; margin-top: 0.3rem; }
</style>
