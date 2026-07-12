<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Premium Subscription" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header">
          <p>A recurring monthly membership that supports faster civic services</p>
        </div>

        <div v-if="loading" class="spinner"></div>

        <template v-else>
          <!-- Not subscribed -->
          <div v-if="!info.subscription" class="premium-showcase">
            <div class="hero-card">
              <div class="hero-glow"></div>
              <div class="hero-badge">✨ PREMIUM MEMBERSHIP</div>
              <h1 class="hero-title">Cyber Panchayat Premium</h1>
              <p class="hero-sub">Everything you need to get civic issues resolved faster</p>
              <div class="hero-price">₹{{ info.monthly_fee }}<span>/month</span></div>
              <button class="btn-hero" :disabled="acting" @click="openSubscribe">
                {{ acting ? 'Processing…' : 'Subscribe Now' }}
              </button>
              <p class="hero-note">Cancel anytime · No long-term lock-in</p>
            </div>

            <div class="benefits-grid">
              <div class="benefit-card">
                <div class="benefit-icon icon-pink">📝</div>
                <h3>File Complaints</h3>
                <p>Submit and track civic complaints in your area</p>
              </div>
              <div class="benefit-card">
                <div class="benefit-icon icon-gold">💬</div>
                <h3>Community Feed</h3>
                <p>Post, comment, and like on the community feed</p>
              </div>
              <div class="benefit-card">
                <div class="benefit-icon icon-purple">🛡️</div>
                <h3>Fair Billing</h3>
                <p>Cancel anytime and keep full access through the period you already paid for</p>
              </div>
              <div class="benefit-card">
                <div class="benefit-icon icon-teal">🔓</div>
                <h3>No Lock-In</h3>
                <p>No contracts — cancel with one click, whenever you like</p>
              </div>
            </div>
          </div>

          <!-- Subscribed (active or cancelled) -->
          <template v-else>
          <div class="subscribed-layout">
            <div class="card status-card" :class="{ 'is-cancelled': info.subscription.status === 'cancelled' }">
              <div class="plan-header">
                <div class="plan-header-left">
                  <div class="plan-icon">👑</div>
                  <div>
                    <div class="plan-title-row">
                      <span class="plan-name">Cyber Panchayat Premium</span>
                      <span v-if="info.subscription.status === 'cancelled'" class="badge badge-cancelled">Cancelled</span>
                      <span v-else-if="info.subscription.pending_cancellation" class="badge badge-ending">⏳ Ending Soon</span>
                      <span v-else class="badge badge-confirmed">⭐ Active</span>
                    </div>
                    <div class="plan-tenure">Member since {{ fmtDate(info.subscription.started_at) }}</div>
                  </div>
                </div>
                <div class="plan-price-block">
                  <div class="plan-price-val">₹{{ info.monthly_fee }}</div>
                  <div class="plan-price-unit">per month</div>
                </div>
              </div>

              <div class="divider"></div>

              <div class="billing-meta">
                <div class="meta-line">
                  <span class="meta-label" v-if="info.subscription.status === 'active' && !info.subscription.pending_cancellation">Next billing date</span>
                  <span class="meta-label" v-else-if="info.subscription.pending_cancellation">Access until</span>
                  <span class="meta-label" v-else>Cancelled on</span>
                  <strong v-if="info.subscription.status !== 'cancelled'">{{ fmtDateOnly(info.subscription.next_billing_date) }}</strong>
                  <strong v-else>{{ fmtDate(info.subscription.cancelled_at) }}</strong>
                </div>
                <div class="meta-line" v-if="lastPaidMethod">
                  <span class="meta-label">Payment method</span>
                  <strong>{{ lastPaidMethod }}</strong>
                </div>
              </div>

              <p v-if="info.subscription.pending_cancellation" class="status-note">
                🔓 Cancelled — you keep complaints &amp; community feed access until {{ fmtDateOnly(info.subscription.next_billing_date) }}
              </p>
              <p v-else-if="info.due_payment" class="status-note">
                ⚠️ Payment Due: ₹{{ info.due_payment.amount }} for {{ fmtDateOnly(info.due_payment.period_start) }} to {{ fmtDateOnly(info.due_payment.period_end) }}
                <button class="btn-pay-now" @click="openPay(info.due_payment)">Pay Now</button>
              </p>
              <p v-else-if="info.subscription.status === 'active'" class="status-note">
                ✅ All caught up — no pending dues
              </p>

              <div class="status-actions">
                <button v-if="info.subscription.status === 'active' && !info.subscription.pending_cancellation"
                        class="btn btn-outline btn-sm" :disabled="acting" @click="cancelSub">
                  {{ acting ? 'Processing…' : 'Cancel Subscription' }}
                </button>
                <button v-else-if="info.subscription.pending_cancellation" class="btn-hero-sm" :disabled="acting" @click="openSubscribe">
                  {{ acting ? 'Processing…' : '↻ Resume Subscription' }}
                </button>
                <button v-else-if="info.subscription.status === 'cancelled'" class="btn-hero-sm" :disabled="acting" @click="openSubscribe">
                  {{ acting ? 'Processing…' : '↻ Resubscribe' }}
                </button>
              </div>

              <div class="divider"></div>

              <div class="perks-section">
                <div class="perks-heading">Your Premium Benefits</div>
                <ul class="perks-list">
                  <li>File complaints</li>
                  <li>Community feed — post, comment &amp; like</li>
                  <li>Fair billing — keep access through what you've paid for</li>
                  <li>No lock-in — cancel anytime</li>
                </ul>
              </div>
            </div>

            <div class="card billing-card">
              <div class="section-title">Billing History</div>
              <div v-if="!payments.length" class="empty-state">
                <p>No invoices yet.</p>
              </div>
              <div v-else class="invoice-list">
                <div v-for="p in payments" :key="p.id" class="invoice-row">
                  <div class="invoice-col-period">
                    <div class="invoice-period-main">{{ fmtDateOnly(p.period_start) }} – {{ fmtDateOnly(p.period_end) }}</div>
                    <div class="invoice-period-sub">{{ methodLabel(p.method) }}</div>
                  </div>
                  <div class="invoice-col-amount">
                    <div class="invoice-amount-val">₹{{ p.amount }}</div>
                    <span :class="['badge', `badge-${p.status}`]">{{ p.status }}</span>
                  </div>
                  <div class="invoice-col-action">
                    <button v-if="p.status === 'pending'" class="btn btn-xs btn-success" @click="openPay(p)">Pay Now</button>
                    <button class="btn btn-xs btn-outline" @click="viewInvoice(p)">Invoice</button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          </template>
        </template>
      </div>
    </div>

    <!-- Pay modal -->
    <div v-if="payModal.show" class="modal-overlay" @click.self="payModal.show = false">
      <div class="modal modal-w-sm">
        <div class="modal-header">
          <h2>Pay ₹{{ payModal.payment?.amount }}</h2>
          <button class="modal-close" @click="payModal.show = false">✕</button>
        </div>
        <div v-if="payModal.error" class="alert alert-error mb-4">{{ payModal.error }}</div>
        <p class="text-sm text-muted mb-4">
          Cyber Panchayat Premium — {{ fmtDateOnly(payModal.payment?.period_start) }} to {{ fmtDateOnly(payModal.payment?.period_end) }}
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

    <NotificationsPanel v-if="showNotif" @close="showNotif = false" @read="unread = Math.max(0, unread - 1)" />
  </div>
</template>

<script setup>
/**
 * My Subscription - Citizen Premium subscription management
 * Features: subscribe, cancel, resume, pay due invoices, view billing history and invoices
 * Premium unlocks: file complaints, community feed posting
 * Payment workflow: subscribe → pending → paid → active (or pending_cancellation → cancelled)
 */
import { ref, computed, onMounted } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import api from "../../api"
import { downloadInvoicePdf } from "../../utils/invoicePdf"

const loading = ref(true)
const acting = ref(false) // Prevents duplicate subscribe/cancel/resume requests
const showNotif = ref(false)
const unread = ref(0)
const info = ref({ subscribed: false, subscription: null, due_payment: null, monthly_fee: 100 })
const payments = ref([]) // Billing history (monthly invoices)
const payModal = ref({ show: false, payment: null, method: "upi", loading: false, error: "" })
const invoice = ref(null)

const lastPaidMethod = computed(() => {
  const paid = payments.value.find(p => p.status === "paid" && p.method)
  return paid ? methodLabel(paid.method) : null
})

async function loadAll() {
  const [subRes, notifRes] = await Promise.all([api.get("/subscriptions/me"), api.get("/notifications")])
  info.value = subRes.data
  unread.value = notifRes.data.unread_count
  if (info.value.subscription) {
    const payRes = await api.get("/subscriptions/payments")
    payments.value = payRes.data
  }
}

onMounted(async () => {
  try {
    await loadAll()
  } finally {
    loading.value = false
  }
})

/**
 * Subscribe to Premium or resume cancelled subscription
 * Creates initial pending payment for the subscription
 * Reloads subscription status and payment history after success
 */
async function openSubscribe() {
  acting.value = true
  try {
    await api.post("/subscriptions/subscribe")
    await loadAll() // Refresh UI with new subscription status
  } catch (e) {
    alert(e.response?.data?.message || "Could not subscribe")
  } finally {
    acting.value = false
  }
}

/**
 * Cancel subscription (marks pending_cancellation)
 * If payment is due and unpaid: access ends immediately, due amount is waived
 * If payment is up-to-date: access continues until next_billing_date, then ends
 * Citizens can resume cancelled subscriptions anytime before status becomes "cancelled"
 */
async function cancelSub() {
  const msg = info.value.due_payment
    ? "Cancel your Premium subscription? You haven't paid for the current cycle yet, so access ends immediately and that unpaid due will be waived."
    : `Cancel your Premium subscription? You'll keep full access until ${fmtDateOnly(info.value.subscription.next_billing_date)} (already paid for), then it won't renew.`
  if (!confirm(msg)) return
  acting.value = true
  try {
    await api.post("/subscriptions/cancel")
    await loadAll()
  } catch (e) {
    alert(e.response?.data?.message || "Could not cancel")
  } finally {
    acting.value = false
  }
}

function openPay(p) {
  payModal.value = { show: true, payment: p, method: "upi", loading: false, error: "" }
}

/**
 * Pay subscription invoice (monthly subscription fee or overdue amount)
 * Updates payment status to "paid" and refreshes subscription status
 * Payment methods: UPI, Card, Net Banking, Online Transfer
 */
async function confirmPay() {
  payModal.value.loading = true
  payModal.value.error = ""
  try {
    await api.post(`/subscriptions/payments/${payModal.value.payment.id}/pay`, { method: payModal.value.method })
    payModal.value.show = false
    await loadAll() // Refresh to remove "Payment Due" banner if this was the due payment
  } catch (e) {
    payModal.value.error = e.response?.data?.message || "Payment failed."
  } finally {
    payModal.value.loading = false
  }
}

async function viewInvoice(p) {
  try {
    const { data } = await api.get(`/subscriptions/payments/${p.id}/invoice`)
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

function methodLabel(m) {
  return { upi: 'UPI', card: 'Card', netbanking: 'Net Banking', online: 'Online' }[m] || (m || '—')
}

function fmtDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
}
function fmtDateOnly(d) {
  if (!d) return '—'
  return new Date(d + "T00:00:00").toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
/* ── Not-subscribed showcase ─────────────────────────────────────────────── */
.premium-showcase { max-width: 780px; margin: 0 auto; }

.hero-card {
  position: relative;
  overflow: hidden;
  text-align: center;
  padding: 3rem 2rem 2.5rem;
  margin-bottom: 1.75rem;
  border-radius: 20px;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent-secondary) 55%, var(--navy) 100%);
  box-shadow: 0 12px 32px rgba(0,82,255,0.28);
}
.hero-glow {
  position: absolute; top: -60px; right: -60px;
  width: 220px; height: 220px; border-radius: 50%;
  background: rgba(255,255,255,0.18);
  filter: blur(10px);
}
.hero-badge {
  position: relative;
  display: inline-block; background: rgba(255,255,255,0.22); color: #fff;
  font-size: 0.72rem; font-weight: 800; letter-spacing: 0.08em;
  padding: 0.3rem 0.85rem; border-radius: 100px; margin-bottom: 1rem;
}
.hero-title { position: relative; font-size: 1.7rem; font-weight: 800; color: #fff; margin-bottom: 0.4rem; }
.hero-sub { position: relative; font-size: 0.92rem; color: rgba(255,255,255,0.88); margin-bottom: 1.5rem; }
.hero-price { position: relative; font-size: 2.6rem; font-weight: 800; color: #fff; margin-bottom: 1.5rem; }
.hero-price span { font-size: 1rem; font-weight: 500; color: rgba(255,255,255,0.75); }
.btn-hero {
  position: relative;
  background: #fff; color: var(--primary); border: none;
  font-size: 0.95rem; font-weight: 800; padding: 0.85rem 2.5rem;
  border-radius: 100px; cursor: pointer;
  box-shadow: 0 6px 18px rgba(0,0,0,0.18);
  transition: transform 0.15s, box-shadow 0.15s;
}
.btn-hero:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 22px rgba(0,0,0,0.22); }
.btn-hero:disabled { opacity: 0.7; cursor: default; }
.hero-note { position: relative; font-size: 0.78rem; color: rgba(255,255,255,0.75); margin-top: 0.85rem; }

.benefits-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; }
.benefit-card {
  background: #fff; border: 1px solid var(--border); border-radius: 14px;
  padding: 1.4rem 1.5rem; transition: transform 0.15s, box-shadow 0.15s;
}
.benefit-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-hover); }
.benefit-icon {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; margin-bottom: 0.75rem;
}
.icon-pink   { background: var(--accent); color: var(--primary); }
.icon-gold   { background: rgba(199,145,0,0.16);  color: #C79100; }
.icon-purple { background: rgba(155,89,182,0.15); color: #9B59B6; }
.icon-teal   { background: rgba(21,128,61,0.14);  color: var(--success); }
.benefit-card h3 { font-size: 0.98rem; font-weight: 800; color: var(--text); margin-bottom: 0.35rem; }
.benefit-card p { font-size: 0.83rem; color: var(--text-muted); line-height: 1.5; }

@media (max-width: 640px) {
  .benefits-grid { grid-template-columns: 1fr; }
}

/* ── Subscribed layout: status card + billing history side by side ───────── */
.subscribed-layout { display: grid; grid-template-columns: 1fr 1.05fr; gap: 1.25rem; align-items: start; }
@media (max-width: 900px) {
  .subscribed-layout { grid-template-columns: 1fr; }
}

/* ── Subscribed status card — matches the hero card's blue brand ─────────── */
.status-card {
  position: relative; overflow: hidden; color: #fff;
  background: linear-gradient(135deg, var(--primary) 0%, var(--accent-secondary) 55%, var(--navy) 100%);
  box-shadow: 0 12px 32px rgba(0,82,255,0.28);
}
.status-card.is-cancelled {
  background: linear-gradient(135deg, #94A3B8 0%, #64748B 55%, #475569 100%);
  box-shadow: 0 12px 32px rgba(71,85,105,0.22);
}

.plan-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 1.1rem; }
.plan-header-left { display: flex; align-items: flex-start; gap: 0.85rem; }
.plan-icon {
  width: 46px; height: 46px; border-radius: 12px; flex-shrink: 0;
  background: rgba(255,255,255,0.22); border: 1px solid rgba(255,255,255,0.3);
  display: flex; align-items: center; justify-content: center; font-size: 1.4rem;
}
.plan-title-row { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
.plan-name { font-size: 1.05rem; font-weight: 800; color: #fff; }
.plan-tenure { font-size: 0.78rem; color: rgba(255,255,255,0.75); margin-top: 0.2rem; }
.plan-price-block { text-align: right; flex-shrink: 0; }
.plan-price-val { font-size: 1.4rem; font-weight: 800; color: #fff; line-height: 1.1; }
.plan-price-unit { font-size: 0.72rem; color: rgba(255,255,255,0.75); }

.divider { border-top: 1px solid rgba(255,255,255,0.2); margin: 1.1rem 0; }

.billing-meta { display: flex; gap: 1.75rem; flex-wrap: wrap; margin-bottom: 1rem; }
.meta-line { font-size: 0.86rem; color: rgba(255,255,255,0.9); }
.meta-line strong { color: #fff; margin-left: 0.35rem; }
.meta-label { color: rgba(255,255,255,0.7); }

.badge-confirmed { background: rgba(255,255,255,0.9); color: #15803D; }
.badge-cancelled { background: rgba(255,255,255,0.2); color: #fff; }
.badge-ending { background: rgba(255,255,255,0.9); color: var(--warning); }

.perks-section { margin-top: -0.25rem; }
.perks-heading { font-size: 0.76rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: rgba(255,255,255,0.7); margin-bottom: 0.5rem; }
.perks-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.4rem; }
.perks-list li { font-size: 0.85rem; color: #fff; padding-left: 1.3rem; position: relative; }
.perks-list li::before { content: "✓"; position: absolute; left: 0; font-weight: 800; }

.status-note {
  font-size: 0.86rem; color: #fff; margin: 0 0 0.9rem;
  display: flex; align-items: center; flex-wrap: wrap; gap: 0.6rem;
}

.btn-pay-now {
  background: #fff; color: var(--primary); border: none; font-size: 0.82rem; font-weight: 800;
  padding: 0.55rem 1.2rem; border-radius: 100px; cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.18);
  transition: transform 0.15s, box-shadow 0.15s;
  flex-shrink: 0;
}
.btn-pay-now:hover { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.24); }

.btn-hero-sm {
  background: #fff; color: var(--primary); border: none; font-size: 0.82rem; font-weight: 800;
  padding: 0.5rem 1.3rem; border-radius: 100px; cursor: pointer;
  box-shadow: 0 4px 12px rgba(0,0,0,0.18);
  transition: transform 0.15s, box-shadow 0.15s;
}
.btn-hero-sm:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 16px rgba(0,0,0,0.24); }
.btn-hero-sm:disabled { opacity: 0.7; cursor: default; }

.status-actions { display: flex; gap: 0.5rem; }
.status-card :deep(.btn-outline) {
  background: #3F3F46; border: 1px solid #3F3F46; color: #fff;
}
.status-card :deep(.btn-outline:hover) { background: #27272A; border-color: #27272A; }

/* ── Billing history card — compact rows for the narrower side column ────── */
.billing-card { display: flex; flex-direction: column; max-height: 560px; }
.invoice-list {
  display: flex; flex-direction: column;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--accent) transparent;
}
.invoice-list::-webkit-scrollbar { width: 6px; }
.invoice-list::-webkit-scrollbar-thumb { background: var(--accent); border-radius: 100px; }
.invoice-list::-webkit-scrollbar-track { background: transparent; }
.invoice-row {
  display: flex; align-items: center; justify-content: space-between; gap: 0.75rem;
  padding: 0.85rem 0.15rem;
  border-bottom: 1px solid var(--border);
}
.invoice-row:last-child { border-bottom: none; }
.invoice-row:hover { background: var(--stone); }
.invoice-period-main { font-size: 0.86rem; font-weight: 700; color: var(--text); }
.invoice-period-sub { font-size: 0.74rem; color: var(--text-muted); margin-top: 0.15rem; }
.invoice-col-amount { text-align: right; flex-shrink: 0; }
.invoice-amount-val { font-size: 0.92rem; font-weight: 800; color: var(--text); }
.invoice-col-amount .badge { display: block; margin-top: 0.25rem; }
.invoice-col-action { display: flex; flex-direction: column; gap: 0.35rem; align-items: flex-end; flex-shrink: 0; }

.td-method { font-size: 0.84rem; color: var(--text-muted); }
.td-txn { font-family: monospace; font-size: 0.8rem; color: var(--text-muted); }
.btn-xs { padding: 0.22rem 0.65rem; font-size: 0.72rem; border-radius: 4px; font-weight: 600; cursor: pointer; }
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
