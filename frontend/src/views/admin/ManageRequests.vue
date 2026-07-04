<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Complaints Management" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>View and manage all citizen complaints</p>
          </div>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by ID, category, citizen..." />
            <select v-model="statusFilter" class="form-control filter-select">
              <option value="">Filter: All</option>
              <option value="pending">Pending</option>
              <option value="assigned">Assigned</option>
              <option value="reassigned">Reassigned</option>
              <option value="in_progress">In Progress</option>
              <option value="on_hold_weather">On Hold - Weather Restrictions</option>
              <option value="resolved">Resolved</option>
              <option value="closed">Closed</option>
              <option value="rejected">Rejected</option>
            </select>
            <select v-model="categoryFilter" class="form-control filter-select">
              <option value="">Category: All</option>
              <option value="road">Road</option>
              <option value="water">Water</option>
              <option value="electricity">Electricity</option>
              <option value="sanitation">Sanitation</option>
              <option value="waste">Waste</option>
              <option value="parks">Parks</option>
              <option value="complaint">General</option>
              <option value="maintenance">Maintenance</option>
              <option value="other">Other</option>
            </select>
            <select v-model="wardFilter" class="form-control filter-select">
              <option value="">Ward: All</option>
              <option v-for="w in wardOptions" :key="w" :value="w">{{ w }}</option>
            </select>
            <select v-model="fundsFilter" class="form-control filter-select">
              <option value="">Budget Tag: All</option>
              <option value="yes">💰 Pending Funds</option>
            </select>
            <select v-model="sortBy" class="form-control filter-select">
              <option value="newest">Sort: Newest First</option>
              <option value="upvotes">Sort: Most Upvoted</option>
            </select>
          </div>

          <div v-if="loading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Category</th>
                  <th>Department</th>
                  <th>Ward</th>
                  <th>Citizen</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>👍</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!paged.length">
                  <td colspan="10"><div class="empty-state"><p>No complaints found</p></div></td>
                </tr>
                <tr v-for="r in paged" :key="r.id">
                  <td>
                    <code class="cmp-id">{{ r.cmp_id }}</code>
                    <span v-if="r.pending_funds" class="badge badge-funds ml-1" title="Tagged for budget allocation">💰</span>
                  </td>
                  <td class="capitalize text-sm">{{ r.category }}</td>
                  <td class="td-dept">{{ r.department }}</td>
                  <td class="text-sm">{{ r.ward || '—' }}</td>
                  <td class="text-sm">{{ r.citizen_name }}</td>
                  <td><span :class="['badge', `badge-${r.priority}`]">{{ r.priority }}</span></td>
                  <td><span :class="['badge', `badge-${r.status}`]">{{ fmtStatus(r.status) }}</span></td>
                  <td class="text-sm text-center">{{ r.upvotes_count || 0 }}</td>
                  <td class="td-date">{{ fmtDate(r.created_at) }}</td>
                  <td>
                    <button class="btn btn-xs btn-primary" @click="viewComplaint(r)">View</button>
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
        </div>
      </div>
    </div>

    <!-- View / Assign Modal -->
    <div v-if="selectedRequest" class="modal-overlay" @click.self="selectedRequest = null">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h2>{{ selectedRequest.cmp_id }} — Complaint Details</h2>
          <button class="modal-close" @click="selectedRequest = null">&#x2715;</button>
        </div>

        <div class="flex gap-2 mb-4">
          <span :class="['badge', `badge-${selectedRequest.status}`]">{{ fmtStatus(selectedRequest.status) }}</span>
          <span :class="['badge', `badge-${selectedRequest.priority}`]">{{ selectedRequest.priority }}</span>
          <span v-if="selectedRequest.pending_funds" class="badge badge-funds">💰 Pending Funds</span>
          <span class="badge badge-closed">👍 {{ selectedRequest.upvotes_count || 0 }} upvotes</span>
        </div>

        <div v-if="selectedRequest.status === 'on_hold_weather'" class="alert alert-info">
          &#9729; <strong>On hold — weather restrictions.</strong> {{ selectedRequest.hold_reason }}
        </div>

        <div class="detail-row"><div class="detail-label">Category</div><div class="detail-value capitalize">{{ selectedRequest.category }}</div></div>
        <div class="detail-row"><div class="detail-label">Department</div><div class="detail-value">{{ selectedRequest.department }}</div></div>
        <div class="detail-row" v-if="selectedRequest.ward"><div class="detail-label">Ward</div><div class="detail-value">{{ selectedRequest.ward }}</div></div>
        <div class="detail-row"><div class="detail-label">Location</div><div class="detail-value">{{ selectedRequest.address }}</div></div>
        <div class="detail-row"><div class="detail-label">Description</div><div class="detail-value">{{ selectedRequest.description }}</div></div>
        <div class="detail-row" v-if="selectedRequest.image_urls?.length">
          <div class="detail-label">Photos</div>
          <div class="detail-value"><ImageGallery :images="selectedRequest.image_urls" alt="Complaint photo" /></div>
        </div>
        <div class="detail-row" v-if="selectedRequest.evidence_urls?.length">
          <div class="detail-label">Resolution Evidence</div>
          <div class="detail-value"><ImageGallery :images="selectedRequest.evidence_urls" alt="Resolution evidence photo" /></div>
        </div>
        <div class="detail-row"><div class="detail-label">Citizen</div><div class="detail-value">{{ selectedRequest.citizen_name }} ({{ selectedRequest.citizen_email }})</div></div>
        <div class="detail-row"><div class="detail-label">Submitted On</div><div class="detail-value">{{ fmtDate(selectedRequest.created_at) }}</div></div>
        <div class="detail-row" v-if="selectedRequest.assignment">
          <div class="detail-label">Assigned To</div>
          <div class="detail-value">{{ selectedRequest.assignment.staff_name }}</div>
        </div>
        <div class="detail-row" v-if="selectedRequest.admin_notes">
          <div class="detail-label">Remarks</div>
          <div class="detail-value">{{ selectedRequest.admin_notes }}</div>
        </div>
        <div class="detail-row" v-if="selectedRequest.rating">
          <div class="detail-label">Citizen Rating</div>
          <div class="detail-value">
            <span class="rating-stars">
              <span v-for="n in 5" :key="n" :class="{ filled: n <= selectedRequest.rating }">&#9733;</span>
              <span class="rating-num">{{ selectedRequest.rating }}/5</span>
            </span>
            <p v-if="selectedRequest.feedback" class="rating-feedback">"{{ selectedRequest.feedback }}"</p>
          </div>
        </div>

        <!-- Assign / Reassign section -->
        <div v-if="['pending','assigned','reassigned','in_progress'].includes(selectedRequest.status)" class="assign-section">
          <div class="section-title mb-3">
            {{ selectedRequest.status === 'pending' ? 'Assign to Officer' : 'Reassign Officer' }}
          </div>

          <div v-if="selectedRequest.assignment" class="current-assignee">
            Currently assigned to <strong>{{ selectedRequest.assignment.staff_name }}</strong>
            <span v-if="selectedRequest.status === 'in_progress'"> &middot; work already in progress</span>
          </div>

          <div v-if="assignError" class="alert alert-error">{{ assignError }}</div>
          <div v-if="assignSuccess" class="alert alert-success">{{ assignSuccess }}</div>

          <div v-if="!officers.length" class="no-officer-note">
            No officers exist yet. Add one via Manage Officers.
          </div>
          <div v-else class="flex gap-3 items-end">
            <div class="form-group flex-1 m-0">
              <label class="assign-label">
                Select Officer <span class="text-xs text-muted">(any department — pick a different one if this was filed under the wrong department)</span>
              </label>
              <select v-model="assignStaffId" class="form-control">
                <option value="">-- Select Officer --</option>
                <optgroup v-for="dept in officersByDept" :key="dept.name" :label="dept.name">
                  <option v-for="o in dept.officers" :key="o.id" :value="o.id"
                          :disabled="o.id === selectedRequest.assignment?.staff_id">
                    {{ o.name }}{{ o.id === selectedRequest.assignment?.staff_id ? ' — current' : '' }}
                  </option>
                </optgroup>
              </select>
            </div>
            <button class="btn btn-primary" @click="assignComplaint" :disabled="assigning || !assignStaffId">
              {{ assigning ? 'Saving...' : (selectedRequest.status === 'pending' ? 'Assign' : 'Reassign') }}
            </button>
          </div>
        </div>

        <!-- Weather hold / resume section -->
        <div v-if="['pending','assigned','reassigned','in_progress'].includes(selectedRequest.status)" class="hold-section">
          <div class="section-title mb-3">Hold for Weather/Seasonal Delays</div>
          <p class="text-xs text-muted mb-2">Use this when physical work (e.g. road repair) must pause for the rainy season — residents see the reason instead of assuming the complaint was ignored.</p>
          <div v-if="holdError" class="alert alert-error">{{ holdError }}</div>
          <div class="flex gap-3 items-end">
            <div class="form-group flex-1 m-0">
              <label class="assign-label">Reason shown to citizen (optional)</label>
              <input v-model="holdReason" class="form-control" placeholder="e.g. Paused until monsoon ends" />
            </div>
            <button class="btn btn-secondary" @click="holdForWeather" :disabled="holding">
              {{ holding ? 'Saving...' : 'Hold for Weather' }}
            </button>
          </div>
        </div>
        <div v-else-if="selectedRequest.status === 'on_hold_weather'" class="hold-section">
          <div class="section-title mb-3">On Hold — Weather Restrictions</div>
          <div v-if="holdError" class="alert alert-error">{{ holdError }}</div>
          <button class="btn btn-secondary" @click="resumeFromHold" :disabled="holding">
            {{ holding ? 'Resuming...' : 'Resume Work' }}
          </button>
        </div>

        <!-- Budget allocation tag -->
        <div v-if="!['rejected'].includes(selectedRequest.status)" class="hold-section">
          <div class="section-title mb-3">Budget Allocation</div>
          <p class="text-xs text-muted mb-2">Tag verified complaints as "Pending Funds" to compile a list for the next budget allocation meeting.</p>
          <div v-if="fundsError" class="alert alert-error">{{ fundsError }}</div>
          <button class="btn" :class="selectedRequest.pending_funds ? 'btn-secondary' : 'btn-outline'"
                  @click="toggleBudgetTag" :disabled="taggingFunds">
            {{ taggingFunds ? 'Saving...' : (selectedRequest.pending_funds ? '✓ Tagged — Pending Funds (click to remove)' : 'Tag for Budget Allocation') }}
          </button>
        </div>

        <!-- Reject section — only for complaints not yet assigned -->
        <div v-if="selectedRequest.status === 'pending'" class="reject-section">
          <div class="section-title mb-3">Reject Complaint</div>
          <p class="text-xs text-muted mb-2">Use this for spam, duplicate, or invalid complaints instead of leaving them pending or deleting the record.</p>
          <div v-if="rejectError" class="alert alert-error">{{ rejectError }}</div>
          <div class="flex gap-3 items-end">
            <div class="form-group flex-1 m-0">
              <label class="assign-label">Reason (sent to citizen)</label>
              <input v-model="rejectReason" class="form-control" placeholder="e.g. Duplicate of CMP0012" />
            </div>
            <button class="btn btn-danger" @click="rejectComplaint" :disabled="rejecting || !rejectReason.trim()">
              {{ rejecting ? 'Rejecting...' : 'Reject' }}
            </button>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="selectedRequest = null">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import ImageGallery from '../../components/ImageGallery.vue'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const loading = ref(true)
const requests = ref([])
const officers = ref([])
const search = ref('')
const statusFilter = ref('')
const categoryFilter = ref('')
const wardFilter = ref('')
const fundsFilter = ref('')
const sortBy = ref('newest')
const page = ref(1)
watch([search, statusFilter, categoryFilter, wardFilter, fundsFilter, sortBy], () => { page.value = 1 })
const perPage = 10
const selectedRequest = ref(null)
const assignStaffId = ref('')
const assigning = ref(false)
const assignError = ref('')
const assignSuccess = ref('')
const rejectReason = ref('')
const rejecting = ref(false)
const rejectError = ref('')
const holdReason = ref('')
const holding = ref(false)
const holdError = ref('')
const taggingFunds = ref(false)
const fundsError = ref('')

onMounted(async () => {
  try {
    const [reqs, offs] = await Promise.all([api.get('/requests'), api.get('/officers')])
    requests.value = reqs.data
    officers.value = offs.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const filtered = computed(() => {
  let list = requests.value
  if (search.value) {
    const q = search.value.toLowerCase()
    list = list.filter(r =>
      r.cmp_id?.toLowerCase().includes(q) ||
      r.citizen_name?.toLowerCase().includes(q) ||
      r.category?.toLowerCase().includes(q) ||
      r.address?.toLowerCase().includes(q)
    )
  }
  if (statusFilter.value) list = list.filter(r => r.status === statusFilter.value)
  if (categoryFilter.value) list = list.filter(r => r.category === categoryFilter.value)
  if (wardFilter.value) list = list.filter(r => r.ward === wardFilter.value)
  if (fundsFilter.value === 'yes') list = list.filter(r => r.pending_funds)
  if (sortBy.value === 'upvotes') list = [...list].sort((a, b) => (b.upvotes_count || 0) - (a.upvotes_count || 0))
  return list
})

const wardOptions = computed(() => [...new Set(requests.value.map(r => r.ward).filter(Boolean))].sort())

const totalPages = computed(() => Math.ceil(filtered.value.length / perPage))
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage, page.value * perPage))

const officersByDept = computed(() => {
  const groups = {}
  for (const o of officers.value) {
    if (!o.is_active) continue
    if (!groups[o.department]) groups[o.department] = []
    groups[o.department].push(o)
  }
  return Object.keys(groups).sort().map(name => ({ name, officers: groups[name] }))
})

function viewComplaint(r) {
  selectedRequest.value = r
  assignStaffId.value = r.assignment?.staff_id || ''
  assignError.value = ''
  assignSuccess.value = ''
  rejectReason.value = ''
  rejectError.value = ''
  holdReason.value = ''
  holdError.value = ''
  fundsError.value = ''
}

function updateRequestInPlace(updated) {
  const idx = requests.value.findIndex(r => r.id === updated.id)
  if (idx >= 0) requests.value[idx] = updated
  selectedRequest.value = updated
}

async function holdForWeather() {
  holding.value = true
  holdError.value = ''
  try {
    const res = await api.put(`/requests/${selectedRequest.value.id}/status`, {
      status: 'on_hold_weather',
      hold_reason: holdReason.value.trim() || undefined,
    })
    updateRequestInPlace(res.data)
    holdReason.value = ''
  } catch (e) {
    holdError.value = e.response?.data?.message || 'Failed to place on hold'
  } finally {
    holding.value = false
  }
}

async function resumeFromHold() {
  holding.value = true
  holdError.value = ''
  try {
    const resumeStatus = selectedRequest.value.assignment ? 'in_progress' : 'pending'
    const res = await api.put(`/requests/${selectedRequest.value.id}/status`, { status: resumeStatus })
    updateRequestInPlace(res.data)
  } catch (e) {
    holdError.value = e.response?.data?.message || 'Failed to resume'
  } finally {
    holding.value = false
  }
}

async function toggleBudgetTag() {
  taggingFunds.value = true
  fundsError.value = ''
  try {
    const res = await api.put(`/requests/${selectedRequest.value.id}/budget-tag`, {
      pending_funds: !selectedRequest.value.pending_funds,
    })
    updateRequestInPlace(res.data)
  } catch (e) {
    fundsError.value = e.response?.data?.message || 'Failed to update budget tag'
  } finally {
    taggingFunds.value = false
  }
}

async function rejectComplaint() {
  if (!rejectReason.value.trim()) return
  rejecting.value = true
  rejectError.value = ''
  try {
    const res = await api.put(`/requests/${selectedRequest.value.id}/status`, {
      status: 'rejected',
      admin_notes: rejectReason.value.trim(),
    })
    const idx = requests.value.findIndex(r => r.id === selectedRequest.value.id)
    if (idx >= 0) requests.value[idx] = res.data
    selectedRequest.value = res.data
  } catch (e) {
    rejectError.value = e.response?.data?.message || 'Failed to reject'
  } finally {
    rejecting.value = false
  }
}

async function assignComplaint() {
  if (!assignStaffId.value) return
  assigning.value = true
  assignError.value = ''
  assignSuccess.value = ''
  const wasReassign = selectedRequest.value.status !== 'pending'
  try {
    const res = await api.post('/assignments', { request_id: selectedRequest.value.id, staff_id: parseInt(assignStaffId.value) })
    const newStatus = wasReassign ? 'reassigned' : 'assigned'
    assignSuccess.value = wasReassign ? 'Complaint reassigned successfully!' : 'Complaint assigned successfully!'
    const idx = requests.value.findIndex(r => r.id === selectedRequest.value.id)
    if (idx >= 0) {
      requests.value[idx].status = newStatus
      requests.value[idx].assignment = res.data
      requests.value[idx].department = res.data.staff_department
      selectedRequest.value.status = newStatus
      selectedRequest.value.assignment = res.data
      selectedRequest.value.department = res.data.staff_department
    }
  } catch (e) {
    assignError.value = e.response?.data?.message || 'Failed to assign'
  } finally {
    assigning.value = false
  }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.cmp-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 4px; }
.td-dept { font-size: 0.78rem; color: #9B2C6F; max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.current-assignee { font-size: 0.82rem; color: #9B2C6F; margin-bottom: 0.65rem; }
.no-officer-note {
  font-size: 0.82rem; color: #A66E00; background: #FFF0F6;
  border: 1px solid #FFE0EE; border-radius: 7px; padding: 0.6rem 0.85rem;
}
.detail-value :deep(.image-gallery) { max-width: 380px; }
.td-date { font-size: 0.78rem; color: #B0708F; white-space: nowrap; }
.assign-section { margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid #FFD1E6; }
.reject-section { margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid #FFD1E6; }
.hold-section { margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid #FFD1E6; }
.assign-label { font-size: 0.78rem; font-weight: 600; display: block; margin-bottom: 0.25rem; }
.rating-stars { display: inline-flex; align-items: center; gap: 0.15rem; font-size: 1.2rem; color: var(--border); }
.rating-stars span.filled { color: #FFC107; }
.rating-num { font-size: 0.8rem; font-weight: 700; color: var(--text); margin-left: 0.4rem; }
.rating-feedback { font-size: 0.85rem; color: var(--text); font-style: italic; margin-top: 0.4rem; }
</style>
