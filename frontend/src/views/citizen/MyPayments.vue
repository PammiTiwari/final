<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Payments" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">

        <div class="page-header">
          <div class="page-header-left">
            <h1>My Payments</h1>
            <p>History of all payment transactions for facility bookings</p>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats-row">
          <div class="stat-card stat-ok">
            <div class="stat-val">₹{{ totalPaid }}</div>
            <div class="stat-lbl">Total Paid</div>
          </div>
          <div class="stat-card stat-warn">
            <div class="stat-val">{{ pendingCount }}</div>
            <div class="stat-lbl">Pending Payments</div>
          </div>
          <div class="stat-card stat-muted">
            <div class="stat-val">{{ refundedCount }}</div>
            <div class="stat-lbl">Refunds</div>
          </div>
        </div>

        <div v-if="loading" class="spinner"></div>

        <div v-else-if="payments.length === 0" class="empty-state card">
          <div class="empty-icon">💳</div>
          <p>No payment history found.</p>
        </div>

        <div v-else class="card">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Txn Reference</th>
                  <th>Facility</th>
                  <th class="text-right">Amount</th>
                  <th>Method</th>
                  <th class="text-center">Status</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in payments" :key="p.id">
                  <td class="td-txn">{{ p.transaction_ref || ('TXN-' + p.id) }}</td>
                  <td class="td-facility">
                    {{ bookingMap[p.booking_id]?.facility_name || ('Booking #' + p.booking_id) }}
                  </td>
                  <td class="text-right font-bold">₹{{ p.amount }}</td>
                  <td class="td-method">{{ methodLabel(p.method) }}</td>
                  <td class="text-center">
                    <span :class="['badge', `badge-${p.status}`]">{{ p.status }}</span>
                  </td>
                  <td class="td-date">
                    {{ p.paid_at ? fmtDate(p.paid_at) : fmtDate(p.created_at) }}
                  </td>
                  <td>
                    <button v-if="p.status === 'pending'" class="btn btn-xs btn-success"
                            @click="openPay(p)">Pay Now</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

    <!-- Pay Modal -->
    <div v-if="payModal.show" class="modal-overlay" @click.self="payModal.show = false">
      <div class="modal modal-w-sm">
        <div class="modal-header">
          <h2>Pay ₹{{ payModal.payment?.amount }}</h2>
          <button class="modal-close" @click="payModal.show = false">✕</button>
        </div>
        <div v-if="payModal.error" class="alert alert-error mb-4">{{ payModal.error }}</div>
        <p class="text-sm text-muted mb-4">
          {{ bookingMap[payModal.payment?.booking_id]?.facility_name }}
        </p>
        <div class="form-group">
          <label>Payment Method</label>
          <select v-model="payModal.method" class="form-control">
            <option value="upi">UPI</option>
            <option value="card">Credit / Debit Card</option>
            <option value="netbanking">Net Banking</option>
            <option value="online">Online Transfer</option>
          </select>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="payModal.show = false">Cancel</button>
          <button class="btn btn-success" :disabled="payModal.loading" @click="confirmPay">
            {{ payModal.loading ? 'Processing…' : `Pay ₹${payModal.payment?.amount}` }}
          </button>
        </div>
      </div>
    </div>

    <NotificationsPanel v-if="showNotif" @close="showNotif = false"
                        @read="unread = Math.max(0, unread - 1)" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import api from "../../api"

const loading = ref(true)
const payments = ref([])
const bookings = ref([])
const showNotif = ref(false)
const unread = ref(0)
const payModal = ref({ show: false, payment: null, method: "upi", loading: false, error: "" })

const bookingMap = computed(() => {
  const m = {}
  bookings.value.forEach(b => { m[b.id] = b })
  return m
})

const totalPaid = computed(() =>
  payments.value.filter(p => p.status === "paid").reduce((s, p) => s + p.amount, 0)
)
const pendingCount = computed(() => payments.value.filter(p => p.status === "pending").length)
const refundedCount = computed(() => payments.value.filter(p => p.status === "refunded").length)

onMounted(async () => {
  const [pRes, bRes, nRes] = await Promise.all([
    api.get("/payments"), api.get("/bookings"), api.get("/notifications")
  ])
  payments.value = pRes.data
  bookings.value = bRes.data
  unread.value = nRes.data.unread_count
  loading.value = false
})

function openPay(p) {
  payModal.value = { show: true, payment: p, method: "upi", loading: false, error: "" }
}

async function confirmPay() {
  payModal.value.loading = true
  payModal.value.error = ""
  try {
    const { data } = await api.post(`/payments/${payModal.value.payment.id}/pay`,
      { method: payModal.value.method })
    const p = payments.value.find(x => x.id === payModal.value.payment.id)
    if (p) Object.assign(p, data)
    payModal.value.show = false
  } catch (e) {
    payModal.value.error = e.response?.data?.message || "Payment failed."
  } finally {
    payModal.value.loading = false
  }
}

function methodLabel(m) {
  return { upi: 'UPI', card: 'Card', netbanking: 'Net Banking', online: 'Online' }[m] || (m || '—')
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
.stats-row { display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
.stat-card {
  flex: 1; min-width: 120px;
  background: #fff; border: 1px solid #FFD1E6; border-radius: 8px;
  padding: 1rem 1.25rem;
}
.stat-val { font-size: 1.6rem; font-weight: 800; color: #5C1A41; line-height: 1; }
.stat-lbl { font-size: 0.72rem; color: #888; margin-top: 0.3rem; text-transform: uppercase; letter-spacing: 0.04em; }
.stat-ok   .stat-val { color: #E0218A; }
.stat-warn .stat-val { color: #A66E00; }
.stat-muted .stat-val { color: #9B2C6F; }

.td-txn    { font-family: monospace; font-size: 0.8rem; color: #9B2C6F; }
.td-facility { font-size: 0.85rem; font-weight: 500; }
.td-method { font-size: 0.84rem; color: #9B2C6F; }
.td-date   { font-size: 0.82rem; color: #B0708F; white-space: nowrap; }

.btn-xs {
  padding: 0.22rem 0.65rem; font-size: 0.72rem;
  border-radius: 4px; font-weight: 600;
  border: none; cursor: pointer;
}
.btn-success { background: #E0218A; color: #fff; }
</style>
