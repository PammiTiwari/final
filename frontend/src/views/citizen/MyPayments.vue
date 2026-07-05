<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Payments" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">

        <div class="page-header">
          <div class="page-header-left">
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
          <div class="payment-list">
            <div class="payment-row payment-head">
              <div class="pcol-facility">Facility</div>
              <div class="pcol-amount">Amount</div>
              <div class="pcol-status">Status</div>
              <div class="pcol-date">Date</div>
              <div class="pcol-action">Action</div>
            </div>
            <div v-for="p in payments" :key="p.id" class="payment-row">
              <div class="pcol-facility">
                <div class="payment-facility-main">{{ bookingMap[p.booking_id]?.facility_name || ('Booking #' + p.booking_id) }}</div>
                <div class="payment-facility-sub">{{ p.transaction_ref || ('TXN-' + p.id) }} · {{ methodLabel(p.method) }}</div>
              </div>
              <div class="pcol-amount">
                <div class="payment-amount-val">₹{{ p.amount }}</div>
              </div>
              <div class="pcol-status">
                <span :class="['badge', `badge-${p.status}`]">{{ p.status }}</span>
              </div>
              <div class="pcol-date">{{ p.paid_at ? fmtDate(p.paid_at) : fmtDate(p.created_at) }}</div>
              <div class="pcol-action">
                <button v-if="p.status === 'pending'" class="btn btn-xs btn-success" @click="openPay(p)">Pay Now</button>
              </div>
            </div>
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
  return new Date(iso).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
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

/* ── Row layout instead of a raw table — keeps the Action column a fixed
   width whether or not a "Pay Now" button is present in that row ────────── */
.payment-list { display: flex; flex-direction: column; }
.payment-row {
  display: grid;
  grid-template-columns: 1.6fr 100px 100px 120px 110px;
  align-items: center;
  gap: 1rem;
  padding: 0.9rem 0.25rem;
  border-bottom: 1px solid #FFE9F2;
}
.payment-row:last-child { border-bottom: none; }
.payment-row:not(.payment-head):hover { background: #FFF7FB; }
.payment-head {
  font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
  color: #B0708F; padding-bottom: 0.6rem; border-bottom: 1px solid #FFD1E6;
}
.payment-facility-main { font-size: 0.88rem; font-weight: 700; color: #5C1A41; }
.payment-facility-sub { font-family: monospace; font-size: 0.74rem; color: #B0708F; margin-top: 0.15rem; }
.pcol-amount { text-align: right; }
.payment-amount-val { font-size: 0.92rem; font-weight: 800; color: #5C1A41; }
.pcol-status { text-align: center; }
.pcol-date { font-size: 0.82rem; color: #B0708F; white-space: nowrap; }
.pcol-action { display: flex; justify-content: flex-end; }

@media (max-width: 760px) {
  .payment-row { grid-template-columns: 1fr auto; grid-template-areas: "facility amount" "status date" "action action"; row-gap: 0.5rem; }
  .payment-row.payment-head { display: none; }
  .pcol-facility { grid-area: facility; }
  .pcol-amount { grid-area: amount; }
  .pcol-status { grid-area: status; text-align: left; }
  .pcol-date { grid-area: date; text-align: right; }
  .pcol-action { grid-area: action; }
}

.btn-xs {
  padding: 0.22rem 0.65rem; font-size: 0.72rem;
  border-radius: 4px; font-weight: 600;
  border: none; cursor: pointer;
}
.btn-success { background: #E0218A; color: #fff; }
</style>
