<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Dashboard" :unread-count="unread" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <h1>Hello, {{ auth.user?.name?.split(' ')[0] }} &#9728;</h1>
            <p>Here's what's happening with your complaints</p>
          </div>
          <router-link to="/submit" class="btn btn-primary">+ Submit Complaint</router-link>
        </div>

        <div v-if="loading" class="spinner"></div>
        <template v-else>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9776;</div>
              <div class="stat-num">{{ stats.requests?.total || 0 }}</div>
              <div class="stat-label">Total Complaints</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-orange">&#9654;</div>
              <div class="stat-num">{{ stats.requests?.pending || 0 }}</div>
              <div class="stat-label">Pending</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9685;</div>
              <div class="stat-num">{{ stats.requests?.in_progress || 0 }}</div>
              <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-green">&#10003;</div>
              <div class="stat-num">{{ stats.requests?.resolved || 0 }}</div>
              <div class="stat-label">Resolved</div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="section-title">Recent Complaints</div>
              <router-link to="/complaints" class="btn btn-sm btn-primary">View All</router-link>
            </div>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Complaint ID</th>
                    <th>Category</th>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!requests.length">
                    <td colspan="6" class="empty-state">No complaints yet. Submit your first complaint!</td>
                  </tr>
                  <tr v-for="r in requests.slice(0, 5)" :key="r.id">
                    <td><code class="cmp-id">{{ r.cmp_id }}</code></td>
                    <td><span class="cat-badge">{{ r.category }}</span></td>
                    <td class="td-title">{{ r.title }}</td>
                    <td>{{ fmtDate(r.created_at) }}</td>
                    <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                    <td>
                      <router-link :to="`/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const auth = useAuthStore()
const loading = ref(true)
const stats = ref({})
const requests = ref([])
const unread = ref(0)

onMounted(async () => {
  try {
    const [dash, reqs, notifs] = await Promise.all([
      api.get('/dashboard'),
      api.get('/requests'),
      api.get('/notifications'),
    ])
    stats.value = dash.data
    requests.value = reqs.data
    unread.value = notifs.data.unread_count || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}

</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.cat-badge { font-size: 0.75rem; font-weight: 600; color: #9B2C6F; text-transform: capitalize; }
.td-title { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem; }
</style>
