<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Manage Subscriptions" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header">
          <p>Cyber Panchayat Premium — recurring monthly memberships and revenue</p>
        </div>

        <div class="stats-row">
          <div class="stat-card stat-ok">
            <div class="stat-val">{{ stats.active || 0 }}</div>
            <div class="stat-lbl">Active Subscribers</div>
          </div>
          <div class="stat-card stat-muted">
            <div class="stat-val">{{ stats.cancelled || 0 }}</div>
            <div class="stat-lbl">Cancelled</div>
          </div>
          <div class="stat-card stat-ok">
            <div class="stat-val">₹{{ stats.monthly_recurring_revenue || 0 }}</div>
            <div class="stat-lbl">Monthly Recurring Revenue</div>
          </div>
          <div class="stat-card stat-ok">
            <div class="stat-val">₹{{ stats.total_collected || 0 }}</div>
            <div class="stat-lbl">Total Collected</div>
          </div>
          <div class="stat-card stat-warn">
            <div class="stat-val">{{ stats.pending_payments || 0 }}</div>
            <div class="stat-lbl">Pending Payments</div>
          </div>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by citizen name or email..." />
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">All Statuses</option>
              <option value="active">Active</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>

          <div v-if="loading" class="spinner"></div>
          <div v-else-if="!filtered.length" class="empty-state">
            <div class="empty-icon">⭐</div>
            <p>No subscriptions found</p>
          </div>
          <template v-else>
            <div class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Citizen</th><th>Status</th><th>Started</th>
                    <th>Next Billing</th><th>Last Invoice</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in filtered" :key="s.id">
                    <td>
                      <div class="font-bold">{{ s.citizen_name }}</div>
                      <div class="td-sub">{{ s.citizen_email }}</div>
                    </td>
                    <td><span :class="`badge ${s.status === 'active' ? 'badge-confirmed' : 'badge-cancelled'}`">{{ s.status }}</span></td>
                    <td class="text-sm">{{ fmtDate(s.started_at) }}</td>
                    <td class="text-sm">{{ s.status === 'active' ? fmtDateOnly(s.next_billing_date) : '—' }}</td>
                    <td>
                      <span v-if="s.latest_payment_status" :class="`badge badge-${s.latest_payment_status}`">{{ s.latest_payment_status }}</span>
                      <span v-else class="td-dash">—</span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </div>
      </div>
    </div>
    <NotificationsPanel v-if="showNotif" @close="showNotif = false" @read="unread = Math.max(0,unread-1)" />
  </div>
</template>

<script setup>
/**
 * Manage Subscriptions - Admin view of Premium subscription revenue and analytics
 * Tracks: active subscribers, monthly recurring revenue, payment status
 * Shows subscription lifecycle: active → cancelled
 * Key metric for business analytics and citizen engagement
 */
import { ref, computed, onMounted } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import api from "../../api"

const loading = ref(true)
const subscriptions = ref([]) // All citizen subscriptions
const stats = ref({}) // Subscription stats (active, cancelled, MRR, total collected)
const showNotif = ref(false)
const unread = ref(0)
const statusFilter = ref("") // Filter by active/cancelled
const search = ref("")

const filtered = computed(() => {
  let list = subscriptions.value
  if (statusFilter.value) list = list.filter(s => s.status === statusFilter.value)
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(s =>
      s.citizen_name?.toLowerCase().includes(q) ||
      s.citizen_email?.toLowerCase().includes(q)
    )
  }
  return list
})

onMounted(async () => {
  const [sRes, nRes] = await Promise.all([api.get("/admin/subscriptions"), api.get("/notifications")])
  subscriptions.value = sRes.data.subscriptions
  stats.value = sRes.data.stats
  unread.value = nRes.data.unread_count
  loading.value = false
})

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
}
function fmtDateOnly(d) {
  return new Date(d + "T00:00:00").toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
.stats-row { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.stat-card {
  flex: 1; min-width: 150px;
  background: #fff; border: 1px solid var(--border); border-radius: 8px;
  padding: 1rem 1.1rem;
}
.stat-val { font-size: 1.5rem; font-weight: 800; color: var(--text); line-height: 1; }
.stat-lbl { font-size: 0.7rem; color: var(--text-muted); margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-ok   .stat-val { color: var(--primary); }
.stat-warn .stat-val { color: var(--warning); }
.stat-muted .stat-val { color: var(--text-muted); }
.badge-confirmed { background: rgba(21,128,61,0.14); color: var(--success); }
.badge-cancelled { background: rgba(148,163,184,0.2); color: #64748B; }
.td-sub { font-size: 0.75rem; color: var(--text-muted); }
.td-dash { color: var(--text-muted); font-size: 0.82rem; }
.filter-bar { display: flex; gap: 0.75rem; padding: 1rem; }
.filter-select { max-width: 200px; }
</style>
