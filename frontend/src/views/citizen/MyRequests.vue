<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="My Complaints" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <h1>My Complaints</h1>
            <p>Track all your submitted complaints</p>
          </div>
          <router-link to="/submit" class="btn btn-primary">+ Submit New</router-link>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by ID or keyword..." />
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">Filter: All</option>
              <option value="pending">Pending</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold_weather">On Hold - Weather Restrictions</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          <div v-if="loading" class="spinner"></div>
          <div class="table-wrapper" v-else>
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Category</th>
                  <th>Title</th>
                  <th>Date</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!paged.length">
                  <td colspan="6">
                    <div class="empty-state">
                      <div class="empty-icon">&#9776;</div>
                      <p>No complaints found</p>
                    </div>
                  </td>
                </tr>
                <tr v-for="r in paged" :key="r.id">
                  <td><code class="cmp-id">{{ r.cmp_id }}</code></td>
                  <td><span class="cat-text">{{ r.category }}</span></td>
                  <td class="td-title">
                    <div class="title-with-thumb">
                      <img v-if="r.image_urls?.length" :src="r.image_urls[0]" class="thumb" alt="" />
                      <span>{{ r.title }}</span>
                    </div>
                  </td>
                  <td>{{ fmtDate(r.created_at) }}</td>
                  <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                  <td>
                    <router-link :to="`/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="pagination" v-if="totalPages > 1">
            <button class="page-btn" :disabled="page === 1" @click="page--">&lt;</button>
            <button
              v-for="p in totalPages" :key="p"
              class="page-btn" :class="{ active: page === p }"
              @click="page = p"
            >{{ p }}</button>
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
      r.category?.toLowerCase().includes(q) ||
      r.address?.toLowerCase().includes(q)
    )
  }
  if (statusFilter.value) list = list.filter(r => r.status === statusFilter.value)
  return list
})

watch([search, statusFilter], () => { page.value = 1 })

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const paged = computed(() => {
  const start = (page.value - 1) * perPage
  return filtered.value.slice(start, start + perPage)
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.cat-text { font-size: 0.8rem; font-weight: 600; color: #9B2C6F; text-transform: capitalize; }
.td-title { max-width: 220px; }
.title-with-thumb { display: flex; align-items: center; gap: 0.6rem; }
.title-with-thumb span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
.thumb { width: 40px; height: 40px; border-radius: 6px; object-fit: cover; flex-shrink: 0; border: 1px solid #FFD1E6; }
</style>
