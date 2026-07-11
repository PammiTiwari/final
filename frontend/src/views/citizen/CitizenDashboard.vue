<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Dashboard" :unread-count="unread" />
      <FloatingActionButton :actions="fabActions" @action="handleFabAction" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <h1>Hello, {{ auth.user?.name?.split(' ')[0] }} &#9728;</h1>
            <p>Here's what's happening with your complaints</p>
          </div>
          <router-link to="/submit" class="btn btn-primary">+ Submit Complaint</router-link>
        </div>

        <div v-if="loading" class="spinner"></div>
        <template v-else>
          <div v-if="subBanner" class="sub-banner">
            <div class="sub-banner-icon">⭐</div>
            <div class="sub-banner-text">
              <strong>{{ subBanner.title }}</strong>
              <p>{{ subBanner.desc }}</p>
            </div>
            <router-link to="/subscription" class="btn btn-primary btn-sm">{{ subBanner.cta }}</router-link>
          </div>

          <div class="stats-grid">
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9776;</div>
              <div class="stat-num">{{ stats.requests?.total || 0 }}</div>
              <div class="stat-label">Total Complaints</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-orange">&#9654;</div>
              <div class="stat-num">{{ stats.requests?.pending || 0 }}</div>
              <div class="stat-label">Pending</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9685;</div>
              <div class="stat-num">{{ stats.requests?.in_progress || 0 }}</div>
              <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-green">&#10003;</div>
              <div class="stat-num">{{ stats.requests?.resolved || 0 }}</div>
              <div class="stat-label">Resolved</div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="section-title">Recent Complaints</div>
              <router-link to="/complaints" class="btn btn-sm btn-primary">View All</router-link>
            </div>
            <div v-if="requests.length" class="table-wrapper">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Complaint ID</th>
                    <th>Category</th>
                    <th>Title</th>
                    <th>Date</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in requests.slice(0, 5)" :key="r.id">
                    <td><code class="cmp-id">{{ r.cmp_id }}</code></td>
                    <td><span class="cat-badge">{{ r.category }}</span></td>
                    <td class="td-title">{{ r.title }}</td>
                    <td>{{ fmtDate(r.created_at) }}</td>
                    <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                    <td>
                      <router-link :to="`/complaints/${r.id}`" class="btn btn-xs btn-primary">View</router-link>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <EmptyState
              v-else
              type="complaints"
              title="No Complaints Yet"
              description="You haven't submitted any complaints. Start helping your community by reporting an issue."
              buttonText="Submit Your First Complaint"
              @action="router.push('/submit')"
            />
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * Citizen Dashboard - Main landing page for citizens
 * Displays complaint statistics, recent complaints, and subscription status banner
 * Enforces Premium subscription requirement for filing complaints via banner messaging
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import FloatingActionButton from '../../components/FloatingActionButton.vue'
import EmptyState from '../../components/EmptyState.vue'
import { useAuthStore } from '../../stores/auth'
import { useToast } from '../../composables/useToast'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const auth = useAuthStore()
const router = useRouter()
const { success, error } = useToast()
const loading = ref(true)
const stats = ref({})
const requests = ref([])
const unread = ref(0)
const subInfo = ref(null)

const fabActions = [
  { icon: '📝', label: 'New Complaint' },
  { icon: '🏛️', label: 'Browse Facilities' }
]

const handleFabAction = (action) => {
  if (action.label === 'New Complaint') {
    router.push('/submit')
  } else if (action.label === 'Browse Facilities') {
    router.push('/facilities')
  }
}

/**
 * Subscription banner logic
 * Shows "Subscribe Now" if no subscription exists
 * Shows payment reminder if payment is overdue
 * Null if subscription is active and up-to-date
 * IMPORTANT: Filing complaints and posting to community feed require active Premium subscription
 */
const subBanner = computed(() => {
  if (!subInfo.value) return null
  if (!subInfo.value.subscription) {
    return {
      title: 'Unlock full access to Cyber Panchayat',
      desc: `Subscribe to Premium (₹${subInfo.value.monthly_fee}/month) to file complaints and join the community feed. Browsing and tracking stay free.`,
      cta: 'Subscribe Now',
    }
  }
  if (subInfo.value.due_payment) {
    return {
      title: 'Payment due on your Premium subscription',
      desc: `Pay ₹${subInfo.value.due_payment.amount} to keep filing complaints and posting on the community feed.`,
      cta: 'Pay Now',
    }
  }
  return null
})

/**
 * Fetch dashboard data on mount
 * Subscription info is fetched separately (fire-and-forget) to avoid blocking dashboard
 * Core dashboard data (stats, requests, notifications) is fetched in parallel
 */
onMounted(async () => {
  // Fetch subscription status separately — errors here should not block dashboard display
  api.get('/subscriptions/me').then(res => { subInfo.value = res.data }).catch(() => {})

  try {
    const [dash, reqs, notifs] = await Promise.all([
      api.get('/dashboard'),
      api.get('/requests'),
      api.get('/notifications'),
    ])
    stats.value = dash.data
    requests.value = reqs.data
    unread.value = notifs.data.unread_count || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' })
}

</script>

<style scoped>
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.cat-badge { font-size: 0.75rem; font-weight: 600; color: #9B2C6F; text-transform: capitalize; }

.sub-banner {
  display: flex; align-items: center; gap: 1rem;
  background: linear-gradient(135deg, #FFE9F2, #FFF3FA);
  border: 1px solid #FFD1E6; border-radius: 14px;
  padding: 1rem 1.25rem; margin-bottom: 1.5rem;
}
.sub-banner-icon {
  width: 40px; height: 40px; flex-shrink: 0; border-radius: 10px;
  background: #E0218A; color: #fff;
  display: flex; align-items: center; justify-content: center; font-size: 1.1rem;
}
.sub-banner-text { flex: 1; min-width: 0; }
.sub-banner-text strong { font-size: 0.9rem; color: #5C1A41; }
.sub-banner-text p { font-size: 0.8rem; color: #9B2C6F; margin-top: 0.2rem; }
.td-title { max-width: 220px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 0.85rem; }
</style>
