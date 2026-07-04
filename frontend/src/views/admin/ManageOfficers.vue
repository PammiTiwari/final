<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Officers" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Manage department officers and staff</p>
          </div>
          <button class="btn btn-primary" @click="openAdd">+ Add Officer</button>
        </div>

        <div class="card">
          <div class="filter-bar">
            <input v-model="search" class="form-control" placeholder="Search by name or department..." />
          </div>
          <div v-if="loading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Name</th>
                  <th>Department</th>
                  <th>Contact</th>
                  <th>Rating</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!filteredOfficers.length">
                  <td colspan="7"><div class="empty-state"><p>No officers found</p></div></td>
                </tr>
                <tr v-for="o in filteredOfficers" :key="o.id">
                  <td><code class="off-id">{{ o.officer_id }}</code></td>
                  <td>
                    <div class="officer-name-cell">
                      <div class="avatar avatar-sm">{{ o.name?.charAt(0) }}</div>
                      <span>{{ o.name }}</span>
                    </div>
                  </td>
                  <td class="text-sm">{{ o.department || '—' }}</td>
                  <td class="td-phone">{{ o.phone || '—' }}</td>
                  <td>
                    <span v-if="officerRatings[o.id]" class="rating-cell" :title="`${officerRatings[o.id].count} rating(s) from citizens`">
                      <span class="rating-star">&#9733;</span> {{ officerRatings[o.id].avg }}
                    </span>
                    <span v-else class="text-xs text-muted">—</span>
                  </td>
                  <td>
                    <span :class="o.is_active ? 'badge-active' : 'badge-inactive'">
                      {{ o.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <div class="action-btns">
                      <button class="btn btn-xs btn-secondary" @click="openEdit(o)">&#9998; Edit</button>
                      <button class="btn btn-xs btn-danger" @click="deactivate(o)" v-if="o.is_active">Deactivate</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingOfficer ? 'Edit Officer' : 'Add Officer' }}</h2>
          <button class="modal-close" @click="showModal = false">&#x2715;</button>
        </div>
        <div v-if="modalError" class="alert alert-error">{{ modalError }}</div>
        <div class="form-grid-2">
          <div class="form-group">
            <label>Full Name</label>
            <input v-model="form.name" class="form-control" placeholder="Officer name" />
          </div>
          <div class="form-group">
            <label>Email</label>
            <input v-model="form.email" type="email" class="form-control" placeholder="Email address" :disabled="!!editingOfficer" />
          </div>
        </div>
        <div class="form-group">
          <label>Phone</label>
          <input v-model="form.phone" class="form-control" placeholder="Phone number" />
        </div>
        <div class="form-group">
          <label>Department</label>
          <select v-model="form.department" class="form-control">
            <option value="">Select Department</option>
            <option v-for="d in departments" :key="d.id" :value="d.name">{{ d.name }}</option>
            <option v-if="form.department && !departments.some(d => d.name === form.department)" :value="form.department">
              {{ form.department }} (legacy — not in Manage Departments)
            </option>
          </select>
          <p v-if="!departments.length" class="text-xs text-faint mt-1">
            No departments yet — add one via Manage Departments first.
          </p>
        </div>
        <div class="form-group" v-if="!editingOfficer">
          <label>Password</label>
          <input v-model="form.password" type="password" class="form-control" placeholder="Set password" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
          <button class="btn btn-primary" @click="saveOfficer" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
        </div>
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
const officers = ref([])
const departments = ref([])
const search = ref('')
const showModal = ref(false)
const editingOfficer = ref(null)
const saving = ref(false)
const modalError = ref('')

const form = ref({ name: '', email: '', phone: '', department: '', password: '' })

const requests = ref([])

onMounted(async () => {
  try {
    const [offRes, deptRes, reqRes] = await Promise.all([api.get('/officers'), api.get('/departments'), api.get('/requests')])
    officers.value = offRes.data
    departments.value = deptRes.data
    requests.value = reqRes.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

// Average citizen rating per officer, from the complaints they handled that
// were closed with a rating. Computed client-side from data already fetched —
// works identically in mock mode and against the real backend.
const officerRatings = computed(() => {
  const acc = {}
  for (const r of requests.value) {
    const staffId = r.assignment?.staff_id
    if (!staffId || !r.rating) continue
    if (!acc[staffId]) acc[staffId] = { sum: 0, count: 0 }
    acc[staffId].sum += r.rating
    acc[staffId].count += 1
  }
  const out = {}
  for (const [id, { sum, count }] of Object.entries(acc)) {
    out[id] = { avg: (sum / count).toFixed(1), count }
  }
  return out
})

const filteredOfficers = computed(() => {
  if (!search.value) return officers.value
  const q = search.value.toLowerCase()
  return officers.value.filter(o =>
    o.name?.toLowerCase().includes(q) ||
    o.department?.toLowerCase().includes(q) ||
    o.email?.toLowerCase().includes(q)
  )
})

function openAdd() {
  editingOfficer.value = null
  form.value = { name: '', email: '', phone: '', department: '', password: '' }
  modalError.value = ''
  showModal.value = true
}

function openEdit(officer) {
  editingOfficer.value = officer
  form.value = { name: officer.name, email: officer.email, phone: officer.phone || '', department: officer.department || '', password: '' }
  modalError.value = ''
  showModal.value = true
}

async function saveOfficer() {
  const name = form.value.name.trim()
  if (!/^[A-Za-z][A-Za-z\s.'-]{1,79}$/.test(name)) { modalError.value = 'Please enter a valid name — letters only, numbers are not a name'; return }
  const phone = form.value.phone.trim()
  if (phone && !/^[6-9]\d{9}$/.test(phone)) { modalError.value = 'Phone must be a valid 10-digit mobile number'; return }
  saving.value = true
  modalError.value = ''
  try {
    if (editingOfficer.value) {
      const res = await api.put(`/officers/${editingOfficer.value.id}`, {
        name,
        phone,
        department: form.value.department,
      })
      const idx = officers.value.findIndex(o => o.id === editingOfficer.value.id)
      if (idx >= 0) officers.value[idx] = res.data
    } else {
      if (!form.value.email.trim() || !form.value.password) { modalError.value = 'Email and password required'; saving.value = false; return }
      if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(form.value.email.trim())) { modalError.value = 'Please enter a valid email address'; saving.value = false; return }
      if (form.value.password.length < 6) { modalError.value = 'Password must be at least 6 characters'; saving.value = false; return }
      const res = await api.post('/officers', { ...form.value, name, phone, email: form.value.email.trim() })
      officers.value.push(res.data)
    }
    showModal.value = false
  } catch (e) {
    modalError.value = e.response?.data?.message || 'Failed to save'
  } finally {
    saving.value = false
  }
}

async function deactivate(officer) {
  if (!confirm(`Deactivate officer "${officer.name}"?`)) return
  try {
    const res = await api.delete(`/officers/${officer.id}`)
    const idx = officers.value.findIndex(o => o.id === officer.id)
    if (idx >= 0) officers.value[idx].is_active = false
    if (res.data.open_complaints) {
      alert(`Officer deactivated. They had ${res.data.open_complaints} open complaint(s) — go to Manage Complaints to reassign them.`)
    }
  } catch (e) {
    alert(e.response?.data?.message || 'Failed')
  }
}
</script>

<style scoped>
.off-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.4rem; border-radius: 4px; }
.rating-cell { font-size: 0.85rem; font-weight: 700; color: var(--text); white-space: nowrap; }
.rating-star { color: #FFC107; }
.officer-name-cell { display: flex; align-items: center; gap: 0.5rem; }
.action-btns { display: flex; gap: 0.35rem; }
.badge-active { font-size: 0.72rem; font-weight: 700; color: #0E7A4F; background: #D7F5E5; padding: 0.15rem 0.5rem; border-radius: 100px; }
.badge-inactive { font-size: 0.72rem; font-weight: 700; color: #9B2C6F; background: #FFE9F2; padding: 0.15rem 0.5rem; border-radius: 100px; }
.td-phone { font-size: 0.8rem; color: #9B2C6F; }
</style>
