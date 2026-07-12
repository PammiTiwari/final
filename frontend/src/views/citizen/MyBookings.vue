<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="My Bookings" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header flex-between">
          <div>
            <p>Track all your facility booking requests and their status</p>
          </div>
          <router-link to="/facilities" class="btn btn-primary">+ New Booking</router-link>
        </div>

        <div class="filter-bar card mb-6">
          <select v-model="filter" class="form-control w-auto">
            <option value="">All Statuses</option>
            <option value="pending">Pending</option>
            <option value="confirmed">Confirmed</option>
            <option value="cancelled">Cancelled</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else-if="filtered.length === 0" class="empty-state card">
          <div class="empty-icon">📅</div>
          <p>No bookings found.</p>
          <router-link to="/facilities" class="btn btn-primary mt-4">Browse Facilities</router-link>
        </div>

        <div v-else class="bookings-list">
          <div v-for="b in filtered" :key="b.id" class="booking-card card">
            <div class="booking-top">
              <div>
                <span :class="`badge badge-${b.status}`">{{ b.status }}</span>
                <span class="facility-type ml-3">{{ b.facility_type }}</span>
              </div>
              <div class="text-xs text-muted">Booking #{{ b.id }}</div>
            </div>
            <h3 class="booking-facility">{{ b.facility_name }}</h3>
            <div class="booking-details">
              <div class="detail">📅 {{ fmtDate(b.booking_date) }}</div>
              <div class="detail">⏰ {{ b.start_time }} – {{ b.end_time }}</div>
              <div class="detail">👥 {{ b.attendees }} attendees</div>
              <div class="detail" v-if="b.fee > 0">💰 ₹{{ b.fee }}</div>
              <div class="detail" v-else>🆓 Free</div>
            </div>
            <div class="booking-purpose">Purpose: {{ b.purpose }}</div>

            <!-- Payment section -->
            <div v-if="b.payment && b.payment.status === 'pending' && b.status === 'confirmed'" class="payment-alert">
              <div>
                <strong>Payment Due:</strong> ₹{{ b.payment.amount }}
                <span class="text-xs text-muted"> — Please pay to confirm your slot</span>
              </div>
              <button class="btn btn-success btn-sm" @click="payNow(b)">
                💳 Pay Now
              </button>
            </div>

            <div v-if="b.payment && b.payment.status === 'paid'" class="payment-done">
              ✅ Paid ₹{{ b.payment.amount }}
              <span class="text-xs">via {{ b.payment.method }} · {{ b.payment.transaction_ref }}</span>
            </div>

            <div v-if="b.admin_notes" class="admin-note mt-3">
              <strong>Note:</strong> {{ b.admin_notes }}
            </div>

            <div class="booking-actions">
              <button class="btn btn-outline btn-sm" @click="viewInvoice(b)">🧾 Invoice</button>
              <button v-if="b.status === 'pending'" class="btn btn-danger btn-sm" @click="cancelBooking(b)">✕ Cancel</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Payment modal -->
    <div v-if="payModal.show" class="modal-overlay" @click.self="payModal.show = false">
      <div class="modal modal-w-md text-center">
        <div class="modal-header">
          <h2>Complete Payment</h2>
          <button class="modal-close" @click="payModal.show = false">✕</button>
        </div>
        <div class="pay-icon">💳</div>
        <p class="text-muted mb-4">
          Pay ₹{{ payModal.booking?.payment?.amount }} for {{ payModal.booking?.facility_name }}
        </p>
        <div class="form-group text-left mb-5">
          <label>Payment Method</label>
          <select v-model="payModal.method" class="form-control">
            <option value="upi">UPI</option>
            <option value="card">Credit/Debit Card</option>
            <option value="netbanking">Net Banking</option>
            <option value="online">Online Transfer</option>
          </select>
        </div>
        <div v-if="payModal.error" class="alert alert-error text-left mb-4">{{ payModal.error }}</div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="payModal.show = false">Cancel</button>
          <button class="btn btn-success" :disabled="payModal.loading" @click="confirmPayment">
            {{ payModal.loading ? 'Processing…' : '✅ Pay ₹' + payModal.booking?.payment?.amount }}
          </button>
        </div>
      </div>
    </div>

    <!-- Invoice Modal -->
    <div v-if="invoice" class="modal-overlay" @click.self="invoice = null">
      <div class="modal invoice-modal">
        <div class="modal-header">
          <h2>Booking Invoice</h2>
          <button class="modal-close" @click="invoice = null">✕</button>
        </div>
        <div class="invoice-body">
          <div class="inv-row"><span>Invoice No</span><strong>{{ invoice.invoice_number }}</strong></div>
          <div class="inv-row"><span>Date Issued</span><span>{{ invoice.issued_at }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row"><span>Citizen</span><span>{{ invoice.citizen_name }}</span></div>
          <div class="inv-row"><span>Phone</span><span>{{ invoice.citizen_phone || '—' }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row"><span>Facility</span><strong>{{ invoice.facility_name }}</strong></div>
          <div class="inv-row"><span>Address</span><span>{{ invoice.facility_address }}</span></div>
          <div class="inv-row"><span>Date</span><span>{{ invoice.booking_date }}</span></div>
          <div class="inv-row"><span>Time</span><span>{{ invoice.start_time }} – {{ invoice.end_time }} ({{ invoice.hours }}h)</span></div>
          <div class="inv-row"><span>Purpose</span><span>{{ invoice.purpose }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row"><span>Rate</span><span>₹{{ invoice.fee_per_hour }}/hr × {{ invoice.hours }}h</span></div>
          <div class="inv-row"><span>Subtotal</span><span>₹{{ invoice.subtotal }}</span></div>
          <div class="inv-row"><span>GST (18%)</span><span>₹{{ invoice.gst_18_percent }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row inv-total"><span>Total</span><strong>₹{{ invoice.total }}</strong></div>
          <div class="inv-row mt-2">
            <span>Payment</span>
            <span :class="['inv-payment-status', invoice.payment_status === 'paid' ? 'is-paid' : 'is-due']">
              {{ invoice.payment_status === 'free' ? 'Free' : invoice.payment_status.toUpperCase() }}
            </span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="downloadInvoice(invoice)">⬇ Download</button>
          <button class="btn btn-secondary" @click="invoice = null">Close</button>
        </div>
      </div>
    </div>

    <NotificationsPanel v-if="showNotif" @close="showNotif = false" @read="unread = Math.max(0,unread-1)" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import api from "../../api"
import { downloadInvoicePdf } from "../../utils/invoicePdf"

const loading = ref(true)
const bookings = ref([])
const showNotif = ref(false)
const unread = ref(0)
const filter = ref("")
const payModal = ref({ show: false, booking: null, method: "upi", loading: false, error: "" })
const invoice = ref(null)

async function viewInvoice(b) {
  try {
    const { data } = await api.get(`/bookings/${b.id}/invoice`)
    invoice.value = data
  } catch {
    alert("Could not load invoice")
  }
}

function downloadInvoice(inv) {
  const paymentLabel = inv.payment_status === "free" ? "Free" : inv.payment_status.toUpperCase()
  downloadInvoicePdf({
    title: "Cyber Panchayat — Booking Invoice",
    invoiceNumber: inv.invoice_number,
    issuedAt: inv.issued_at,
    filename: `${inv.invoice_number}.pdf`,
    rows: [
      ["Citizen", inv.citizen_name, { bold: true }],
      ["Phone", inv.citizen_phone || "—"],
      ["Facility", inv.facility_name, { divider: true, bold: true }],
      ["Address", inv.facility_address],
      ["Date", inv.booking_date],
      ["Time", `${inv.start_time} – ${inv.end_time} (${inv.hours}h)`],
      ["Purpose", inv.purpose],
      ["Rate", `₹${inv.fee_per_hour}/hr × ${inv.hours}h`, { divider: true }],
      ["Subtotal", `₹${inv.subtotal}`],
      ["GST (18%)", `₹${inv.gst_18_percent}`],
      ["Total", `₹${inv.total}`, { divider: true, bold: true }],
      ["Payment", paymentLabel],
    ],
  })
}

const filtered = computed(() => {
  if (!filter.value) return bookings.value
  return bookings.value.filter(b => b.status === filter.value)
})

onMounted(async () => {
  const [bRes, nRes] = await Promise.all([api.get("/bookings"), api.get("/notifications")])
  bookings.value = bRes.data
  unread.value = nRes.data.unread_count
  loading.value = false
})

async function cancelBooking(b) {
  if (!confirm("Cancel this booking?")) return
  await api.delete(`/bookings/${b.id}`)
  b.status = "cancelled"
}

function payNow(b) {
  payModal.value = { show: true, booking: b, method: "upi", loading: false, error: "" }
}

async function confirmPayment() {
  payModal.value.loading = true
  payModal.value.error = ""
  try {
    const paymentId = payModal.value.booking?.payment?.id
    if (!paymentId) { payModal.value.error = "Payment record not found."; return }
    const { data } = await api.post(`/payments/${paymentId}/pay`,
      { method: payModal.value.method })
    const b = bookings.value.find(x => x.id === payModal.value.booking.id)
    if (b && b.payment) {
      b.payment.status = "paid"
      b.payment.transaction_ref = data.transaction_ref
      b.payment.method = data.method
      b.status = "confirmed"
    }
    payModal.value.show = false
  } catch (e) {
    payModal.value.error = e.response?.data?.message || "Payment failed."
  } finally {
    payModal.value.loading = false
  }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", weekday: "short", day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
.bookings-list { display: flex; flex-direction: column; gap: 1rem; }
.booking-card { padding: 1.5rem; }
.booking-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.facility-type { font-size: 0.78rem; color: var(--text-muted); font-weight: 600; }
.booking-facility { font-size: 1.05rem; font-weight: 800; color: var(--navy); margin-bottom: 0.75rem; }
.booking-details { display: flex; gap: 1.25rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.detail { font-size: 0.85rem; color: var(--text-muted); font-weight: 500; }
.booking-purpose { font-size: 0.85rem; color: var(--text); margin-top: 0.25rem; }
.payment-alert {
  display: flex; justify-content: space-between; align-items: center;
  background: #FBF6EE; border-left: 4px solid var(--warning);
  padding: 0.75rem 1rem; border-radius: 8px; margin-top: 0.75rem;
  font-size: 0.88rem;
}
.payment-done {
  background: #E3EADE; color: #0E7A4F;
  padding: 0.5rem 0.85rem; border-radius: 8px;
  font-size: 0.85rem; margin-top: 0.75rem;
  display: flex; align-items: center; gap: 0.5rem;
}
.admin-note {
  padding: 0.6rem 0.85rem; background: #FFE9F2; border-radius: 6px;
  font-size: 0.83rem; color: var(--text-muted);
}
.booking-actions { margin-top: 0.85rem; display: flex; gap: 0.5rem; }
.invoice-modal { max-width: 420px; }
.invoice-body { padding: 0 0.25rem; }
.inv-row { display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.3rem 0; color: #9B2C6F; }
.inv-row span:first-child { color: #B0708F; }
.inv-divider { border-top: 1px solid #FFD1E6; margin: 0.5rem 0; }
.inv-total { font-size: 1rem; font-weight: 800; padding-top: 0.4rem; }
.inv-payment-status { font-weight: 700; }
.inv-payment-status.is-paid { color: #0E7A4F; }
.inv-payment-status.is-due { color: #A66E00; }
.filter-bar { padding: 1rem; display: flex; gap: 0.75rem; }
.pay-icon { font-size: 2.5rem; margin: 1rem 0; }
</style>
