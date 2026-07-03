<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Departments" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Manage city departments and officer assignments</p>
          </div>
          <button class="btn btn-primary" @click="openAdd">+ Add Department</button>
        </div>

        <div class="card">
          <div v-if="loading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Department Name</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="!departments.length">
                  <td colspan="3"><div class="empty-state"><p>No departments yet</p></div></td>
                </tr>
                <tr v-for="d in departments" :key="d.id">
                  <td><code class="dept-id">{{ d.dept_id }}</code></td>
                  <td><div class="dept-name">{{ d.name }}</div></td>
                  <td>
                    <div class="action-btns">
                      <button class="btn btn-xs btn-outline" @click="openView(d)">&#128065; View</button>
                      <button class="btn btn-xs btn-secondary" @click="openEdit(d)">&#9998; Edit</button>
                      <button class="btn btn-xs btn-danger" @click="deleteDept(d)">&#128465; Delete</button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- View Modal -->
    <div v-if="viewDept" class="modal-overlay" @click.self="viewDept = null">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ viewDept.name }}</h2>
          <button class="modal-close" @click="viewDept = null">&#x2715;</button>
        </div>
        <p class="view-desc">{{ viewDept.description || 'No description provided.' }}</p>

        <div class="section-title mt-4 mb-2">Officers in this Department</div>
        <div v-if="!deptOfficers.length" class="no-officers">
          No officers assigned to this department yet. Add one via Manage Officers.
        </div>
        <div v-else class="officer-list">
          <div v-for="o in deptOfficers" :key="o.id" class="officer-row">
            <div class="avatar avatar-sm">{{ o.name?.charAt(0) }}</div>
            <div class="officer-info">
              <div class="officer-name">{{ o.name }}</div>
              <div class="officer-phone">{{ o.phone || '—' }} &bull; {{ o.ward || '—' }}</div>
            </div>
            <span :class="o.is_active ? 'badge-active' : 'badge-inactive'">
              {{ o.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="viewDept = null">Close</button>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <h2>{{ editingDept ? 'Edit Department' : 'Add Department' }}</h2>
          <button class="modal-close" @click="showModal = false">&#x2715;</button>
        </div>
        <div v-if="modalError" class="alert alert-error">{{ modalError }}</div>
        <div class="form-group">
          <label>Department Name</label>
          <input v-model="form.name" class="form-control" placeholder="Department name" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="form.description" class="form-control" rows="2" placeholder="Department description"></textarea>
        </div>
        <p class="text-xs text-faint mb-2">
          Officers are linked by department name, not picked here — add or reassign them via Manage Officers.
        </p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showModal = false">Cancel</button>
          <button class="btn btn-primary" @click="saveDept" :disabled="saving">{{ saving ? 'Saving...' : 'Save' }}</button>
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
const departments = ref([])
const officers = ref([])
const showModal = ref(false)
const editingDept = ref(null)
const viewDept = ref(null)
const form = ref({ name: '', description: '' })
const saving = ref(false)
const modalError = ref('')

onMounted(async () => {
  try {
    const [depts, offs] = await Promise.all([api.get('/departments'), api.get('/officers')])
    departments.value = depts.data
    officers.value = offs.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const deptOfficers = computed(() => {
  if (!viewDept.value) return []
  return officers.value.filter(o => o.department === viewDept.value.name)
})

function openView(dept) {
  viewDept.value = dept
}

function openAdd() {
  editingDept.value = null
  form.value = { name: '', description: '' }
  modalError.value = ''
  showModal.value = true
}

function openEdit(dept) {
  editingDept.value = dept
  form.value = { name: dept.name, description: dept.description || '' }
  modalError.value = ''
  showModal.value = true
}

async function saveDept() {
  if (!form.value.name.trim()) { modalError.value = 'Department name is required'; return }
  saving.value = true
  modalError.value = ''
  try {
    if (editingDept.value) {
      const res = await api.put(`/departments/${editingDept.value.id}`, form.value)
      const idx = departments.value.findIndex(d => d.id === editingDept.value.id)
      if (idx >= 0) departments.value[idx] = res.data
    } else {
      const res = await api.post('/departments', form.value)
      departments.value.push(res.data)
    }
    showModal.value = false
  } catch (e) {
    modalError.value = e.response?.data?.message || 'Failed to save'
  } finally {
    saving.value = false
  }
}

async function deleteDept(dept) {
  if (!confirm(`Delete "${dept.name}"? This cannot be undone.`)) return
  try {
    await api.delete(`/departments/${dept.id}`)
    departments.value = departments.value.filter(d => d.id !== dept.id)
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to delete')
  }
}
</script>

<style scoped>
.dept-id { font-family: monospace; font-size: 0.8rem; background: #FFE9F2; padding: 0.1rem 0.4rem; border-radius: 4px; }
.dept-name { font-weight: 600; font-size: 0.875rem; }
.action-btns { display: flex; gap: 0.35rem; }
.view-desc { font-size: 0.85rem; color: #B0708F; line-height: 1.5; }
.no-officers {
  font-size: 0.82rem; color: #A66E00; background: #FFF0F6;
  border: 1px solid #FFE0EE; border-radius: 7px; padding: 0.6rem 0.85rem;
}
.officer-list { display: flex; flex-direction: column; gap: 0.6rem; max-height: 320px; overflow-y: auto; }
.officer-row {
  display: flex; align-items: center; gap: 0.65rem;
  padding: 0.6rem 0.7rem; border: 1px solid #FFD1E6; border-radius: var(--radius-sm);
}
.officer-info { flex: 1; }
.officer-name { font-size: 0.85rem; font-weight: 600; }
.officer-phone { font-size: 0.75rem; color: #B0708F; }
.badge-active { font-size: 0.7rem; font-weight: 700; color: #0E7A4F; background: #D7F5E5; padding: 0.15rem 0.5rem; border-radius: 100px; }
.badge-inactive { font-size: 0.7rem; font-weight: 700; color: #9B2C6F; background: #FFE9F2; padding: 0.15rem 0.5rem; border-radius: 100px; }
</style>
