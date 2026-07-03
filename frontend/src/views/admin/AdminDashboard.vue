<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Admin Dashboard" :unread-count="unread" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Overview of city complaints and services</p>
          </div>
          <router-link to="/admin/complaints" class="btn btn-primary">View All Complaints</router-link>
        </div>

        <div v-if="loading" class="spinner"></div>
        <template v-else>
          <!-- Stats (live snapshot) -->
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
              <div class="stat-num">{{ (stats.requests?.assigned || 0) + (stats.requests?.reassigned || 0) + (stats.requests?.in_progress || 0) + (stats.requests?.reopened || 0) }}</div>
              <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-orange">&#9729;</div>
              <div class="stat-num">{{ stats.requests?.on_hold_weather || 0 }}</div>
              <div class="stat-label">On Hold (Weather)</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-green">&#10003;</div>
              <div class="stat-num">{{ stats.requests?.resolved || 0 }}</div>
              <div class="stat-label">Resolved</div>
            </div>
          </div>

          <!-- Status donut chart -->
          <div class="card chart-card mb-4">
            <div class="section-title">Complaints by Status</div>
            <div class="donut-row">
              <div class="donut-container">
                <svg viewBox="0 0 100 100" class="donut-svg">
                  <circle v-for="(seg, i) in donutSegments" :key="i"
                    cx="50" cy="50" r="35"
                    :stroke="seg.color"
                    stroke-width="20"
                    fill="none"
                    :stroke-dasharray="`${seg.dash} ${seg.gap}`"
                    :stroke-dashoffset="seg.offset"
                    transform="rotate(-90 50 50)"
                  />
                </svg>
                <div class="donut-center">
                  <div class="donut-total">{{ stats.requests?.total || 0 }}</div>
                  <div class="donut-lbl">Total</div>
                </div>
              </div>
              <div class="donut-legend">
                <div v-for="(item, i) in statusItems" :key="i" class="legend-item">
                  <div class="legend-dot" :style="{ background: item.color }"></div>
                  <span>{{ item.label }}: {{ item.count }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Reports & Analytics (merged in, so admins don't need a separate page) -->
          <div class="section-label mb-3">
            <span class="dot"></span>Reports &amp; Analytics
          </div>
          <div class="card mb-4">
            <div class="date-range-bar">
              <div class="form-group m-0">
                <label>From Date</label>
                <input v-model="fromDate" type="date" class="form-control" />
              </div>
              <div class="form-group m-0">
                <label>To Date</label>
                <input v-model="toDate" type="date" class="form-control" />
              </div>
              <button class="btn btn-primary" @click="loadReports" :disabled="reportsLoading">
                {{ reportsLoading ? 'Loading...' : 'Generate Report' }}
              </button>
            </div>
          </div>

          <div v-if="reportsLoading" class="spinner"></div>
          <template v-else-if="reportData">
            <div class="charts-row">
              <!-- Complaints over time line chart -->
              <div class="card chart-card">
                <div class="section-title">Complaints Over Time</div>
                <div class="line-chart">
                  <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="line-svg" preserveAspectRatio="none">
                    <line v-for="i in 4" :key="i"
                      :x1="padL" :y1="padT + (i-1) * ((svgH - padT - padB) / 3)"
                      :x2="svgW - padR" :y2="padT + (i-1) * ((svgH - padT - padB) / 3)"
                      stroke="var(--border)" stroke-width="1"
                    />
                    <path :d="areaPath" fill="var(--accent)" opacity="0.6" />
                    <polyline :points="linePoints" fill="none" stroke="var(--primary)" stroke-width="2.5" stroke-linejoin="round" />
                    <circle v-for="(pt, i) in chartPoints" :key="i" :cx="pt.x" :cy="pt.y" r="3" fill="var(--primary)" />
                  </svg>
                  <div class="line-labels">
                    <span v-for="(d, i) in labeledDays" :key="i">{{ d }}</span>
                  </div>
                </div>
              </div>

              <!-- Department performance -->
              <div class="card chart-card">
                <div class="section-title">Department Performance</div>
                <div class="dept-perf-list">
                  <div v-for="(dept, i) in reportData.department_performance" :key="i" class="dept-perf-item">
                    <div class="dept-perf-header">
                      <span class="dept-perf-name">{{ dept.name }}</span>
                      <span class="dept-perf-pct">{{ dept.pct }}%</span>
                    </div>
                    <div class="perf-track">
                      <div class="perf-fill" :style="{ width: dept.pct + '%', background: perfColors[i % perfColors.length] }"></div>
                    </div>
                    <div class="dept-perf-footer">
                      <span>{{ dept.resolved }} resolved</span>
                      <span>{{ dept.total }} total</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>

          <!-- Quick links -->
          <div class="quick-links">
            <router-link to="/admin/departments" class="quick-card card">
              <div class="quick-icon icon-blue">&#9675;</div>
              <div class="quick-label">Departments</div>
              <div class="quick-num">{{ deptCount }}</div>
            </router-link>
            <router-link to="/admin/officers" class="quick-card card">
              <div class="quick-icon icon-purple">&#9673;</div>
              <div class="quick-label">Officers</div>
              <div class="quick-num">{{ stats.users?.staff || 0 }}</div>
            </router-link>
            <router-link to="/admin/users" class="quick-card card">
              <div class="quick-icon icon-orange">&#128100;</div>
              <div class="quick-label">Citizens</div>
              <div class="quick-num">{{ stats.users?.citizens || 0 }}</div>
            </router-link>
            <router-link to="/admin/complaints" class="quick-card card">
              <div class="quick-icon icon-green">&#9776;</div>
              <div class="quick-label">Complaints</div>
              <div class="quick-num">{{ stats.requests?.total || 0 }}</div>
            </router-link>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import api from '../../api'

const loading = ref(true)
const stats = ref({})
const unread = ref(0)
const deptCount = ref(0)

const reportsLoading = ref(false)
const reportData = ref(null)
const fromDate = ref('')
const toDate = ref('')
const perfColors = ['#0052FF', '#4D7CFF', '#15803D', '#B45309', '#9B59B6']

const statusItems = computed(() => [
  { label: 'Pending', count: stats.value.requests?.pending || 0, color: '#B45309' },
  { label: 'In Progress', count: (stats.value.requests?.assigned || 0) + (stats.value.requests?.reassigned || 0) + (stats.value.requests?.in_progress || 0) + (stats.value.requests?.reopened || 0), color: '#0052FF' },
  { label: 'On Hold (Weather)', count: stats.value.requests?.on_hold_weather || 0, color: '#4D7CFF' },
  { label: 'Resolved', count: stats.value.requests?.resolved || 0, color: '#15803D' },
  { label: 'Closed', count: stats.value.requests?.closed || 0, color: '#94A3B8' },
])

const donutSegments = computed(() => {
  const total = Math.max(statusItems.value.reduce((s, i) => s + i.count, 0), 1)
  const circumference = 2 * Math.PI * 35
  let offset = 0
  return statusItems.value.map(item => {
    const dash = (item.count / total) * circumference
    const seg = { color: item.color, dash, gap: circumference - dash, offset: -offset }
    offset += dash
    return seg
  })
})

// Line chart constants
const svgW = 500, svgH = 160, padL = 20, padR = 20, padT = 15, padB = 25

const chartPoints = computed(() => {
  if (!reportData.value?.complaints_over_time) return []
  const days = reportData.value.complaints_over_time
  const maxVal = Math.max(...days.map(d => d.count), 1)
  const stepX = (svgW - padL - padR) / Math.max(days.length - 1, 1)
  const scaleY = (svgH - padT - padB) / maxVal
  return days.map((d, i) => ({
    x: padL + i * stepX,
    y: svgH - padB - d.count * scaleY,
  }))
})

const linePoints = computed(() => chartPoints.value.map(p => `${p.x},${p.y}`).join(' '))

const areaPath = computed(() => {
  if (!chartPoints.value.length) return ''
  const pts = chartPoints.value
  const bottomLeft = `${pts[0].x},${svgH - padB}`
  const bottomRight = `${pts[pts.length - 1].x},${svgH - padB}`
  return `M ${bottomLeft} L ${pts.map(p => `${p.x},${p.y}`).join(' L ')} L ${bottomRight} Z`
})

const labeledDays = computed(() => {
  if (!reportData.value?.complaints_over_time) return []
  return reportData.value.complaints_over_time.filter((_, i) => i % 2 === 0).map(d => d.date)
})

async function loadReports() {
  reportsLoading.value = true
  try {
    const res = await api.get('/reports', { params: { from: fromDate.value, to: toDate.value } })
    reportData.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    reportsLoading.value = false
  }
}

onMounted(async () => {
  const now = new Date()
  toDate.value = now.toISOString().split('T')[0]
  const from = new Date(now)
  from.setDate(from.getDate() - 30)
  fromDate.value = from.toISOString().split('T')[0]

  try {
    const [dash, depts, notifs] = await Promise.all([
      api.get('/dashboard'),
      api.get('/departments'),
      api.get('/notifications'),
    ])
    stats.value = dash.data
    deptCount.value = depts.data.length
    unread.value = notifs.data.unread_count || 0
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
  loadReports()
})
</script>

<style scoped>
.chart-card { }
.donut-row { display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; }
.donut-container { position: relative; width: 140px; height: 140px; flex-shrink: 0; }
.donut-svg { width: 100%; height: 100%; }
.donut-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.donut-total { font-size: 1.5rem; font-weight: 800; color: var(--text); }
.donut-lbl { font-size: 0.7rem; color: var(--text-muted); }
.donut-legend { display: flex; flex-direction: column; gap: 0.5rem; }
.legend-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.82rem; color: var(--text); }
.legend-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }

.date-range-bar { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
.date-range-bar .form-group label { font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.25rem; }

.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.line-svg { width: 100%; height: 140px; }
.line-labels { display: flex; justify-content: space-between; padding: 0.25rem 0.5rem 0; }
.line-labels span { font-size: 0.65rem; color: var(--text-muted); }

.dept-perf-list { display: flex; flex-direction: column; gap: 1rem; }
.dept-perf-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.dept-perf-name { font-size: 0.82rem; font-weight: 600; color: var(--text); }
.dept-perf-pct { font-size: 0.85rem; font-weight: 800; color: var(--text); }
.perf-track { background: var(--stone); border-radius: 100px; height: 8px; overflow: hidden; }
.perf-fill { height: 100%; border-radius: 100px; transition: width 0.5s; }
.dept-perf-footer { display: flex; justify-content: space-between; margin-top: 0.2rem; font-size: 0.72rem; color: var(--text-muted); }

.quick-links { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.quick-card { display: flex; flex-direction: column; gap: 0.35rem; text-decoration: none; transition: var(--transition); }
.quick-card:hover { box-shadow: var(--shadow-hover); transform: translateY(-2px); }
.quick-icon { width: 36px; height: 36px; border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center; font-size: 1rem; margin-bottom: 0.3rem; }
.quick-label { font-size: 0.78rem; color: var(--text-muted); font-weight: 500; }
.quick-num { font-size: 1.4rem; font-weight: 800; color: var(--text); }

@media (max-width: 900px) {
  .charts-row { grid-template-columns: 1fr; }
  .quick-links { grid-template-columns: repeat(2, 1fr); }
}
</style>
