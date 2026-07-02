<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Staff Dashboard" :unread-count="unread" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <h1>Hello, {{ auth.user?.name?.split(' ')[0] }} &#128188;</h1>
            <p>{{ auth.user?.department }} — Here's your department overview</p>
          </div>
        </div>

        <div v-if="loading" class="spinner"></div>
        <template v-else>
          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9776;</div>
              <div class="stat-num">{{ stats.assignments?.total || 0 }}</div>
              <div class="stat-label">Total Assigned</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-orange">&#9654;</div>
              <div class="stat-num">{{ stats.assignments?.pending || 0 }}</div>
              <div class="stat-label">Pending</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9685;</div>
              <div class="stat-num">{{ stats.assignments?.in_progress || 0 }}</div>
              <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-green">&#10003;</div>
              <div class="stat-num">{{ stats.assignments?.resolved || 0 }}</div>
              <div class="stat-label">Resolved</div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="section-title">Recent Assigned Complaints</div>
              <router-link to="/staff/complaints" class="btn btn-sm btn-primary">View All</router-link>
            </div>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Category</th>
                    <th>Location</th>
                    <th>Priority</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="!recentRequests.length">
                    <td colspan="6" class="empty-state">No assigned complaints</td>
                  </tr>
                  <tr v-for="r in recentRequests" :key="r.id">
                    <td><code class="cmp-id">{{ r.cmp_id }}</code></td>
                    <td class="capitalize">{{ r.category }}</td>
                    <td class="td-ellipsis">{{ r.address }}</td>
                    <td><span :class="['badge', `badge-${r.priority}`]">{{ r.priority }}</span></td>
                    <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                    <td>
                      <router-link :to="`/staff/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
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
const recentRequests = ref([])
const unread = ref(0)

onMounted(async () => {
  try {
    const [dash, notifs] = await Promise.all([
      api.get('/dashboard'),
      api.get('/notifications'),
    ])
    stats.value = dash.data
    recentRequests.value = dash.data.recent || []
    unread.value = notifs.data.unread_count || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.td-ellipsis { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.82rem; color: #9B2C6F; }
</style>
