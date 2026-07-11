<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="My Complaints" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Track all your submitted complaints</p>
          </div>
          <router-link to="/submit" class="btn btn-primary">+ Submit New</router-link>
        </div>

        <div class="card">
          <div class="filter-bar">
            <div class="search-wrapper">
              <input
                v-model="searchQuery"
                class="form-control"
                placeholder="🔍 Search by ID, title, or category..."
                @input="onSearchChange"
              />
              <span v-if="searchQuery" class="search-clear" @click="clearSearch">✕</span>
            </div>
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">Status: All</option>
              <option value="pending">Pending</option>
              <option value="assigned">Assigned</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold_weather">On Hold - Weather</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
            </select>
            <select v-model="categoryFilter" class="form-control filter-select">
              <option value="">Category: All</option>
              <option value="road">Road</option>
              <option value="water">Water</option>
              <option value="electricity">Electricity</option>
              <option value="sanitation">Sanitation</option>
              <option value="waste">Waste</option>
              <option value="parks">Parks & Public Spaces</option>
              <option value="maintenance">Maintenance</option>
              <option value="other">Other</option>
            </select>
            <button
              v-if="hasActiveFilters"
              class="btn btn-outline btn-sm clear-filters"
              @click="clearAllFilters"
            >
              Clear Filters
            </button>
          </div>

          <div v-if="hasActiveFilters || searchQuery" class="filter-info">
            <span class="result-count">📊 {{ filtered.length }} result{{ filtered.length !== 1 ? 's' : '' }} found</span>
          </div>

          <SkeletonLoader v-if="loading" type="table" :count="5" />
          <EmptyState
            v-else-if="!paged.length"
            type="complaints"
            title="No Complaints Found"
            description="You haven't submitted any complaints yet. Start helping your community!"
            buttonText="Submit Your First Complaint"
            @action="$router.push('/submit')"
          />
          <div v-else class="table-wrapper">
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
                    <div class="action-btns">
                      <router-link :to="`/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
                      <button v-if="r.status === 'pending'" class="btn btn-xs btn-danger" :disabled="deletingId === r.id" @click="deleteRequest(r)">
                        {{ deletingId === r.id ? 'Deleting...' : 'Delete' }}
                      </button>
                    </div>
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
/**
 * My Complaints - Citizen view for all their submitted complaints
 * Features: search, status filtering, pagination, and delete pending complaints
 * Only complaints in "pending" status can be deleted by the citizen
 */
import { ref, computed, onMounted, watch } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import SkeletonLoader from '../../components/SkeletonLoader.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useToast } from '../../composables/useToast'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const { success, error: toastError } = useToast()
const loading = ref(true)
const requests = ref([])
const searchQuery = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const page = ref(1)
const perPage = 10
const deletingId = ref(null)
let searchTimeout = null

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

/**
 * Filter complaints by search term (across ID, title, category, address)
 * and by status, category. Reset pagination when filters change.
 */
const filtered = computed(() => {
  let list = requests.value
  // Search across complaint ID, title, category, and address fields
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(r =>
      r.cmp_id?.toLowerCase().includes(q) ||
      r.title?.toLowerCase().includes(q) ||
      r.category?.toLowerCase().includes(q) ||
      r.address?.toLowerCase().includes(q)
    )
  }
  // Filter by status if selected
  if (statusFilter.value) list = list.filter(r => r.status === statusFilter.value)
  // Filter by category if selected
  if (categoryFilter.value) list = list.filter(r => r.category === categoryFilter.value)
  return list
})

const hasActiveFilters = computed(() => statusFilter.value || categoryFilter.value || searchQuery.value)

watch([searchQuery, statusFilter, categoryFilter], () => { page.value = 1 })

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const paged = computed(() => {
  const start = (page.value - 1) * perPage
  return filtered.value.slice(start, start + perPage)
})

/**
 * Delete a complaint - only allowed for complaints in "pending" status
 * UI button is hidden for non-pending complaints, server validates on DELETE
 * Shows confirmation dialog and provides user feedback during deletion
 */
async function deleteRequest(r) {
  if (deletingId.value) return // Prevent multiple simultaneous delete requests
  if (!confirm(`Delete complaint ${r.cmp_id}? This cannot be undone.`)) return
  deletingId.value = r.id
  try {
    await api.delete(`/requests/${r.id}`)
    requests.value = requests.value.filter(x => x.id !== r.id)
    success(`✓ Complaint ${r.cmp_id} deleted successfully`)
  } catch (e) {
    toastError(`Error: ${e.response?.data?.message || 'Failed to delete complaint'}`)
  } finally {
    deletingId.value = null
  }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' })
}

function onSearchChange() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    page.value = 1
  }, 300)
}

function clearSearch() {
  searchQuery.value = ''
  page.value = 1
}

function clearAllFilters() {
  searchQuery.value = ''
  statusFilter.value = ''
  categoryFilter.value = ''
  page.value = 1
}
</script>

<style scoped>
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  align-items: center;
}

.search-wrapper {
  flex: 1;
  position: relative;
  min-width: 200px;
}

.search-wrapper .form-control {
  padding-right: 32px;
}

.search-clear {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  cursor: pointer;
  color: #9ca3af;
  font-size: 18px;
  font-weight: bold;
  transition: color 0.2s;
}

.search-clear:hover {
  color: #6b7280;
}

.filter-select {
  min-width: 140px;
}

.clear-filters {
  white-space: nowrap;
}

.filter-info {
  background: #f0f9ff;
  border-left: 4px solid #3b82f6;
  padding: 8px 12px;
  margin-bottom: 16px;
  border-radius: 4px;
  font-size: 14px;
  color: #1e40af;
}

.result-count {
  font-weight: 500;
}

.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.cat-text { font-size: 0.8rem; font-weight: 600; color: #9B2C6F; text-transform: capitalize; }
.td-title { max-width: 220px; }
.title-with-thumb { display: flex; align-items: center; gap: 0.6rem; }
.title-with-thumb span { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 160px; }
.thumb { width: 40px; height: 40px; border-radius: 6px; object-fit: cover; flex-shrink: 0; border: 1px solid #FFD1E6; }
.action-btns { display: flex; gap: 0.35rem; }

@media (max-width: 640px) {
  .filter-bar {
    flex-direction: column;
  }

  .search-wrapper,
  .filter-select {
    width: 100%;
  }

  .filter-info {
    font-size: 12px;
  }
}
</style>
