<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Assigned Complaints" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Complaints assigned to you for action</p>
          </div>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by ID or keyword..." />
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">Filter: All</option>
              <option value="assigned">Assigned</option>
              <option value="reassigned">Reassigned</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold_weather">On Hold - Weather Restrictions</option>
              <option value="resolved">Resolved</option>
            </select>
          </div>

          <div v-if="loading" class="spinner"></div>
          <div class="table-wrapper" v-else>
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Category</th>
                  <th>Location</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!paged.length">
                  <td colspan="7">
                    <div class="empty-state">
                      <div class="empty-icon">&#9776;</div>
                      <p>No assigned complaints</p>
                    </div>
                  </td>
                </tr>
                <tr v-for="r in paged" :key="r.id">
                  <td><code class="cmp-id">{{ r.cmp_id }}</code></td>
                  <td class="capitalize text-sm">{{ r.category }}</td>
                  <td class="td-ellipsis">{{ r.address }}</td>
                  <td><span :class="['badge', `badge-${r.priority}`]">{{ r.priority }}</span></td>
                  <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                  <td class="td-date">{{ fmtDate(r.created_at) }}</td>
                  <td>
                    <router-link :to="`/staff/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="pagination" v-if="totalPages > 1">
            <button class="page-btn" :disabled="page === 1" @click="page--">&lt;</button>
            <button v-for="p in totalPages" :key="p" class="page-btn" :class="{ active: page === p }" @click="page = p">{{ p }}</button>
            <button class="page-btn" :disabled="page === totalPages" @click="page++">&gt;</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const loading = ref(true)
const requests = ref([])
const search = ref('')
const statusFilter = ref('')
const page = ref(1)
watch([search, statusFilter], () => { page.value = 1 })
const perPage = 10

onMounted(async () => {
  try {
    const res = await api.get('/requests')
    requests.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  let list = requests.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.cmp_id?.toLowerCase().includes(q) ||
      r.title?.toLowerCase().includes(q) ||
      r.address?.toLowerCase().includes(q)
    )
  }
  if (statusFilter.value) list = list.filter(r => r.status === statusFilter.value)
  return list
})

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage, page.value * perPage))

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.td-ellipsis { max-width: 180px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.82rem; color: #9B2C6F; }
.td-date { font-size: 0.8rem; color: #B0708F; }
</style>
