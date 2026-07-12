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
                      <div class="flex items-center gap-2">
                        <span v-if="s.latest_payment_status" :class="`badge badge-${s.latest_payment_status}`">{{ s.latest_payment_status }}</span>
                        <span v-else class="td-dash">—</span>
                        <button v-if="s.latest_payment_id" class="btn btn-xs btn-outline" @click="viewInvoice(s.latest_payment_id)">Invoice</button>
                      </div>
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

    <!-- Invoice modal -->
    <div v-if="invoice" class="modal-overlay" @click.self="invoice = null">
      <div class="modal invoice-modal">
        <div class="modal-header">
          <h2>Subscription Invoice</h2>
          <button class="modal-close" @click="invoice = null">✕</button>
        </div>
        <div class="invoice-body">
          <div class="inv-row"><span>Invoice No</span><strong>{{ invoice.invoice_number }}</strong></div>
          <div class="inv-row"><span>Date Issued</span><span>{{ invoice.issued_at }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row"><span>Citizen</span><span>{{ invoice.citizen_name }}</span></div>
          <div class="inv-row"><span>Email</span><span>{{ invoice.citizen_email || '—' }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row"><span>Plan</span><strong>{{ invoice.plan }}</strong></div>
          <div class="inv-row"><span>Billing Period</span><span>{{ invoice.period_start }} – {{ invoice.period_end }}</span></div>
          <div class="inv-divider"></div>
          <div class="inv-row inv-total"><span>Amount</span><strong>₹{{ invoice.amount }}</strong></div>
          <div class="inv-row mt-2">
            <span>Payment</span>
            <span :class="['inv-payment-status', invoice.status === 'paid' ? 'is-paid' : 'is-due']">
              {{ invoice.status.toUpperCase() }}
            </span>
          </div>
          <div v-if="invoice.transaction_ref" class="inv-row"><span>Txn Ref</span><span class="td-txn">{{ invoice.transaction_ref }}</span></div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="downloadInvoice(invoice)">⬇ Download</button>
          <button class="btn btn-secondary" @click="invoice = null">Close</button>
        </div>
      </div>
    </div>
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
import { downloadInvoicePdf } from "../../utils/invoicePdf"

const loading = ref(true)
const subscriptions = ref([]) // All citizen subscriptions
const stats = ref({}) // Subscription stats (active, cancelled, MRR, total collected)
const showNotif = ref(false)
const unread = ref(0)
const statusFilter = ref("") // Filter by active/cancelled
const invoice = ref(null)
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

async function viewInvoice(paymentId) {
  try {
    const { data } = await api.get(`/subscriptions/payments/${paymentId}/invoice`)
    invoice.value = data
  } catch {
    alert("Could not load invoice")
  }
}

function downloadInvoice(inv) {
  const rows = [
    ["Citizen", inv.citizen_name, { bold: true }],
    ["Email", inv.citizen_email || "—"],
    ["Plan", inv.plan, { divider: true, bold: true }],
    ["Billing Period", `${inv.period_start} – ${inv.period_end}`],
    ["Amount", `₹${inv.amount}`, { divider: true, bold: true }],
    ["Payment", inv.status.toUpperCase()],
  ]
  if (inv.transaction_ref) rows.push(["Txn Ref", inv.transaction_ref])
  downloadInvoicePdf({
    title: "Cyber Panchayat — Subscription Invoice",
    invoiceNumber: inv.invoice_number,
    issuedAt: inv.issued_at,
    filename: `${inv.invoice_number}.pdf`,
    rows,
  })
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

.td-txn { font-family: monospace; font-size: 0.8rem; color: var(--text-muted); }
.invoice-modal { max-width: 420px; }
.invoice-body { padding: 0 0.25rem; }
.inv-row { display: flex; justify-content: space-between; font-size: 0.85rem; padding: 0.3rem 0; color: var(--text); }
.inv-row span:first-child { color: var(--text-muted); }
.inv-divider { border-top: 1px solid var(--border); margin: 0.5rem 0; }
.inv-total { font-size: 1rem; font-weight: 800; padding-top: 0.4rem; }
.inv-payment-status { font-weight: 700; }
.inv-payment-status.is-paid { color: var(--success); }
.inv-payment-status.is-due { color: var(--warning); }
</style>
