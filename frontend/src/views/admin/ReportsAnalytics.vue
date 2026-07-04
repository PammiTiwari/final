<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Reports & Analytics" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Insights on complaint management and department performance</p>
          </div>
        </div>

        <!-- Date Range -->
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
            <button class="btn btn-primary" @click="loadReports" :disabled="loading">
              {{ loading ? 'Loading...' : 'Generate Report' }}
            </button>
          </div>
        </div>

        <div v-if="loading" class="spinner"></div>
        <template v-else-if="data">
          <!-- Summary stats -->
          <div class="stats-grid mb-4">
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9776;</div>
              <div class="stat-num">{{ data.total }}</div>
              <div class="stat-label">Total Complaints</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-orange">&#9654;</div>
              <div class="stat-num">{{ data.by_status?.pending || 0 }}</div>
              <div class="stat-label">Pending</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-blue">&#9685;</div>
              <div class="stat-num">{{ data.by_status?.in_progress || 0 }}</div>
              <div class="stat-label">In Progress</div>
            </div>
            <div class="stat-card">
              <div class="stat-icon icon-green">&#10003;</div>
              <div class="stat-num">{{ data.by_status?.resolved || 0 }}</div>
              <div class="stat-label">Resolved</div>
            </div>
          </div>

          <div class="charts-row">
            <!-- Complaints over time line chart -->
            <div class="card">
              <div class="section-title mb-4">Complaints Over Time</div>
              <div class="line-chart">
                <svg :viewBox="`0 0 ${svgW} ${svgH}`" class="line-svg" preserveAspectRatio="none">
                  <!-- Grid lines -->
                  <line v-for="i in 4" :key="i"
                    :x1="padL" :y1="padT + (i-1) * ((svgH - padT - padB) / 3)"
                    :x2="svgW - padR" :y2="padT + (i-1) * ((svgH - padT - padB) / 3)"
                    stroke="#FFD1E6" stroke-width="1"
                  />
                  <!-- Area fill -->
                  <path :d="areaPath" fill="#FFF3DA" opacity="0.4" />
                  <!-- Line -->
                  <polyline :points="linePoints" fill="none" stroke="#FFB400" stroke-width="2.5" stroke-linejoin="round" />
                  <!-- Dots -->
                  <circle v-for="(pt, i) in chartPoints" :key="i"
                    :cx="pt.x" :cy="pt.y" r="3" fill="#FFB400"
                  />
                </svg>
                <!-- X labels -->
                <div class="line-labels">
                  <span v-for="(d, i) in labeledDays" :key="i">{{ d }}</span>
                </div>
              </div>
            </div>

            <!-- Department performance -->
            <div class="card">
              <div class="section-title mb-4">Department Performance</div>
              <div class="dept-perf-list">
                <div v-for="(dept, i) in data.department_performance" :key="i" class="dept-perf-item">
                  <div class="dept-perf-header">
                    <span class="dept-perf-name">{{ dept.name }}</span>
                    <span class="dept-perf-pct">{{ dept.pct }}%</span>
                  </div>
                  <div class="perf-track">
                    <div class="perf-fill" :style="{ width: dept.pct + '%', background: perfColors[i] }"></div>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import api from '../../api'

const loading = ref(false)
const data = ref(null)
const fromDate = ref('')
const toDate = ref('')
const perfColors = ['#FFB400', '#E0218A', '#A66E00', '#FF2D6F', '#9B2C6F']

// Chart constants
const svgW = 500, svgH = 160, padL = 20, padR = 20, padT = 15, padB = 25

const chartPoints = computed(() => {
  if (!data.value?.complaints_over_time) return []
  const days = data.value.complaints_over_time
  const maxVal = Math.max(...days.map(d => d.count), 1)
  const stepX = (svgW - padL - padR) / Math.max(days.length - 1, 1)
  const scaleY = (svgH - padT - padB) / maxVal
  return days.map((d, i) => ({
    x: padL + i * stepX,
    y: svgH - padB - d.count * scaleY,
  }))
})

const linePoints = computed(() =>
  chartPoints.value.map(p => `${p.x},${p.y}`).join(' ')
)

const areaPath = computed(() => {
  if (!chartPoints.value.length) return ''
  const pts = chartPoints.value
  const bottomLeft = `${pts[0].x},${svgH - padB}`
  const bottomRight = `${pts[pts.length-1].x},${svgH - padB}`
  return `M ${bottomLeft} L ${pts.map(p => `${p.x},${p.y}`).join(' L ')} L ${bottomRight} Z`
})

const labeledDays = computed(() => {
  if (!data.value?.complaints_over_time) return []
  const days = data.value.complaints_over_time
  return days.filter((_, i) => i % 2 === 0).map(d => d.date)
})

onMounted(() => {
  const now = new Date()
  toDate.value = now.toISOString().split('T')[0]
  const from = new Date(now)
  from.setDate(from.getDate() - 30)
  fromDate.value = from.toISOString().split('T')[0]
  loadReports()
})

async function loadReports() {
  loading.value = true
  try {
    const res = await api.get('/reports', { params: { from: fromDate.value, to: toDate.value } })
    data.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.date-range-bar { display: flex; gap: 1rem; align-items: flex-end; flex-wrap: wrap; }
.date-range-bar .form-group label { font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.25rem; }
.charts-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }

/* Line chart */
.line-chart { }
.line-svg { width: 100%; height: 140px; }
.line-labels { display: flex; justify-content: space-between; padding: 0.25rem 0.5rem 0; }
.line-labels span { font-size: 0.65rem; color: #D69AB8; }

/* Department performance bars */
.dept-perf-list { display: flex; flex-direction: column; gap: 1rem; }
.dept-perf-item { }
.dept-perf-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.dept-perf-name { font-size: 0.82rem; font-weight: 600; color: #5C1A41; }
.dept-perf-pct { font-size: 0.85rem; font-weight: 800; color: #5C1A41; }
.perf-track { background: #FFE9F2; border-radius: 100px; height: 8px; overflow: hidden; }
.perf-fill { height: 100%; border-radius: 100px; transition: width 0.5s; }
.dept-perf-footer { display: flex; justify-content: space-between; margin-top: 0.2rem; font-size: 0.72rem; color: #D69AB8; }

@media (max-width: 900px) {
  .charts-row { grid-template-columns: 1fr; }
}
</style>
