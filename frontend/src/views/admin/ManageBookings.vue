<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Manage Bookings" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header">
          <h1>Facility Bookings</h1>
          <p>Review and manage all facility booking requests</p>
        </div>

        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-val">{{ bookings.length }}</div>
            <div class="stat-lbl">Total</div>
          </div>
          <div class="stat-card stat-warn">
            <div class="stat-val">{{ countByStatus('pending') }}</div>
            <div class="stat-lbl">Pending</div>
          </div>
          <div class="stat-card stat-ok">
            <div class="stat-val">{{ countByStatus('confirmed') }}</div>
            <div class="stat-lbl">Confirmed</div>
          </div>
          <div class="stat-card stat-muted">
            <div class="stat-val">{{ countByStatus('completed') }}</div>
            <div class="stat-lbl">Completed</div>
          </div>
          <div class="stat-card stat-danger">
            <div class="stat-val">{{ countByStatus('cancelled') }}</div>
            <div class="stat-lbl">Cancelled</div>
          </div>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by citizen or facility..." />
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="cancelled">Cancelled</option>
              <option value="completed">Completed</option>
            </select>
          </div>

          <div v-if="loading" class="spinner"></div>
          <div v-else-if="!paged.length" class="empty-state">
            <div class="empty-icon">📅</div>
            <p>No bookings found</p>
          </div>
          <template v-else>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>ID</th><th>Facility</th><th>Citizen</th>
                    <th>Date & Time</th><th>Attendees</th><th>Fee</th>
                    <th>Payment</th><th>Status</th><th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="b in paged" :key="b.id">
                    <td class="td-id">#{{ b.id }}</td>
                    <td>
                      <div class="font-bold">{{ b.facility_name }}</div>
                      <div class="td-sub">{{ b.facility_type }}</div>
                    </td>
                    <td class="text-sm">{{ b.citizen_name }}</td>
                    <td>
                      <div class="td-date-main">{{ fmtDate(b.booking_date) }}</div>
                      <div class="td-sub">{{ b.start_time }} – {{ b.end_time }}</div>
                    </td>
                    <td class="text-sm">{{ b.attendees }}</td>
                    <td class="font-bold">{{ b.fee > 0 ? `₹${b.fee}` : 'Free' }}</td>
                    <td>
                      <span v-if="b.payment" :class="`badge badge-${b.payment.status}`">{{ b.payment.status }}</span>
                      <span v-else class="td-dash">—</span>
                    </td>
                    <td><span :class="`badge badge-${b.status}`">{{ b.status }}</span></td>
                    <td>
                      <div class="action-btns">
                        <button v-if="b.status === 'pending'" class="btn btn-xs btn-success"
                                @click="updateStatus(b, 'confirmed')">Confirm</button>
                        <button v-if="['pending','confirmed'].includes(b.status)" class="btn btn-xs btn-danger"
                                @click="updateStatus(b, 'cancelled')">Cancel</button>
                        <button v-if="b.status === 'confirmed'" class="btn btn-xs btn-secondary"
                                @click="updateStatus(b, 'completed')">Complete</button>
                      </div>
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
          </template>
        </div>
      </div>
    </div>
    <NotificationsPanel v-if="showNotif" @close="showNotif = false" @read="unread = Math.max(0,unread-1)" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import api from "../../api"

const loading = ref(true)
const bookings = ref([])
const showNotif = ref(false)
const unread = ref(0)
const statusFilter = ref("")
const search = ref("")
const page = ref(1)
watch([search, statusFilter], () => { page.value = 1 })
const perPage = 10

function countByStatus(s) {
  return bookings.value.filter(b => b.status === s).length
}

const filtered = computed(() => {
  let list = bookings.value
  if (statusFilter.value) list = list.filter(b => b.status === statusFilter.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(b =>
      b.citizen_name?.toLowerCase().includes(q) ||
      b.facility_name?.toLowerCase().includes(q)
    )
  }
  return list
})

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage, page.value * perPage))

onMounted(async () => {
  const [bRes, nRes] = await Promise.all([api.get("/bookings"), api.get("/notifications")])
  bookings.value = bRes.data
  unread.value = nRes.data.unread_count
  loading.value = false
})

async function updateStatus(b, status) {
  const action = status === "confirmed" ? "confirm" : status === "cancelled" ? "cancel" : "complete"
  if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} this booking?`)) return
  const { data } = await api.put(`/bookings/${b.id}/status`, { status })
  const idx = bookings.value.findIndex(x => x.id === b.id)
  if (idx !== -1) bookings.value[idx] = data
}

function fmtDate(d) {
  return new Date(d + "T00:00:00").toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
.stats-row { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.stat-card {
  flex: 1; min-width: 110px;
  background: #fff; border: 1px solid #FFD1E6; border-radius: 8px;
  padding: 1rem 1.1rem;
}
.stat-val { font-size: 1.5rem; font-weight: 800; color: #5C1A41; line-height: 1; }
.stat-lbl { font-size: 0.7rem; color: #888; margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-ok   .stat-val { color: #E0218A; }
.stat-warn .stat-val { color: #A66E00; }
.stat-muted .stat-val { color: #9B2C6F; }
.stat-danger .stat-val { color: #FF2D6F; }
.action-btns { display: flex; gap: 0.35rem; flex-wrap: wrap; }
.btn-xs {
  padding: 0.22rem 0.6rem; font-size: 0.72rem;
  border-radius: 4px; font-weight: 600; border: none; cursor: pointer;
}
.btn-success { background: #E0218A; color: #fff; }
.btn-danger { background: #FF2D6F; color: #fff; }
.btn-secondary { background: #FFE9F2; color: #9B2C6F; }
.td-id { color: #B0708F; font-size: 0.82rem; }
.td-sub { font-size: 0.75rem; color: #D69AB8; }
.td-date-main { font-weight: 600; font-size: 0.88rem; }
.td-dash { color: #D69AB8; font-size: 0.82rem; }
</style>
