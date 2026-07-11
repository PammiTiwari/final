<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Manage Users" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header">
          <p>View and manage all citizens and staff members</p>
        </div>

        <div class="filters card mb-6 p-4">
          <div class="flex gap-3 flex-wrap">
            <select v-model="roleFilter" class="form-control w-auto">
              <option value="">All Roles</option>
              <option value="citizen">Citizens</option>
              <option value="staff">Staff</option>
              <option value="admin">Admins</option>
            </select>
            <input v-model="search" type="text" class="form-control flex-1" placeholder="🔍 Search by name or email…" />
          </div>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="card">
          <div class="table-wrapper">
            <table class="data-table">
              <thead>
                <tr>
                  <th>ID</th><th>Name</th><th>Email</th><th>Role</th>
                  <th>Department</th><th>Phone</th><th>Subscription</th><th>Status</th><th>Joined</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="u in filtered" :key="u.id">
                  <td class="text-xs text-muted">#{{ u.id }}</td>
                  <td>
                    <div class="flex items-center gap-2">
                      <div class="user-mini-avatar" :class="u.role">{{ initials(u.name) }}</div>
                      <span class="font-bold">{{ u.name }}</span>
                    </div>
                  </td>
                  <td class="text-sm text-muted">{{ u.email }}</td>
                  <td>
                    <span :class="`role-badge role-${u.role}`">{{ u.role }}</span>
                  </td>
                  <!-- Citizens have no department (only staff/admin do) -->
                  <td class="text-sm">{{ u.department || '—' }}</td>
                  <td class="text-sm">{{ u.phone || '—' }}</td>
                  <td>
                    <span v-if="subMap[u.id]" :class="`sub-badge sub-${subMap[u.id].status}`">
                      {{ subMap[u.id].status === 'active' ? '⭐ Premium' : 'Cancelled' }}
                    </span>
                    <span v-else class="text-xs text-faint">—</span>
                  </td>
                  <td>
                    <span :class="u.is_active ? 'badge-active' : 'badge-inactive'">
                      {{ u.is_active ? 'Active' : 'Disabled' }}
                    </span>
                  </td>
                  <td class="text-xs text-muted">{{ fmtDate(u.created_at) }}</td>
                  <td>
                    <div class="flex gap-2">
                      <button class="btn btn-outline btn-sm" @click="openEdit(u)">Edit</button>
                      <button :class="`btn btn-sm ${u.is_active ? 'btn-danger' : 'btn-success'}`"
                              @click="toggleActive(u)">
                        {{ u.is_active ? 'Disable' : 'Enable' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit modal -->
    <div v-if="editModal.show" class="modal-overlay" @click.self="editModal.show = false">
      <div class="modal modal-w-md">
        <div class="modal-header">
          <h2>Edit User</h2>
          <button class="modal-close" @click="editModal.show = false">✕</button>
        </div>
        <div v-if="editModal.error" class="alert alert-error mb-4">{{ editModal.error }}</div>
        <div class="flex-col gap-4">
          <div class="form-group">
            <label>Role</label>
            <select v-model="editModal.role" class="form-control">
              <option value="citizen">Citizen</option>
              <option value="staff" :disabled="editModal.user?.role !== 'staff'">Staff</option>
              <option value="admin">Admin</option>
            </select>
            <p v-if="editModal.user?.role !== 'staff'" class="text-xs text-faint mt-1">
              To make someone an officer, use Manage Officers instead (it requires picking a department).
            </p>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-outline" @click="editModal.show = false">Cancel</button>
          <button class="btn btn-primary" :disabled="editModal.loading" @click="confirmEdit">
            {{ editModal.loading ? 'Saving…' : 'Save Changes' }}
          </button>
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

const loading = ref(true)
const users = ref([])
const subscriptions = ref([])
const showNotif = ref(false)
const unread = ref(0)
const roleFilter = ref("")
const search = ref("")

const subMap = computed(() => {
  const m = {}
  subscriptions.value.forEach(s => { m[s.citizen_id] = s })
  return m
})

const filtered = computed(() => {
  return users.value.filter(u => {
    if (roleFilter.value && u.role !== roleFilter.value) return false
    if (search.value) {
      const q = search.value.toLowerCase()
      if (!u.name.toLowerCase().includes(q) && !u.email.toLowerCase().includes(q)) return false
    }
    return true
  })
})

const editModal = ref({ show: false, user: null, role: "", loading: false, error: "" })

onMounted(async () => {
  const [uRes, nRes, sRes] = await Promise.all([
    api.get("/admin/users"), api.get("/notifications"), api.get("/admin/subscriptions"),
  ])
  users.value = uRes.data
  unread.value = nRes.data.unread_count
  subscriptions.value = sRes.data.subscriptions
  loading.value = false
})

function openEdit(u) {
  editModal.value = { show: true, user: u, role: u.role, loading: false, error: "" }
}

async function confirmEdit() {
  editModal.value.loading = true
  editModal.value.error = ""
  try {
    const payload = { role: editModal.value.role }
    const { data } = await api.put(`/admin/users/${editModal.value.user.id}`, payload)
    const u = users.value.find(x => x.id === editModal.value.user.id)
    if (u) { u.role = data.role }
    editModal.value.show = false
  } catch (e) {
    editModal.value.error = e.response?.data?.message || "Update failed."
  } finally {
    editModal.value.loading = false
  }
}

async function toggleActive(u) {
  const action = u.is_active ? "disable" : "enable"
  if (!confirm(`${action.charAt(0).toUpperCase() + action.slice(1)} ${u.name}?`)) return
  await api.put(`/admin/users/${u.id}`, { is_active: !u.is_active })
  u.is_active = !u.is_active
}

function initials(name) {
  return (name || "U").split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2)
}

function fmtDate(iso) {
  return new Date(iso).toLocaleDateString("en-IN", { timeZone: "Asia/Kolkata", day: "2-digit", month: "short", year: "numeric" })
}
</script>

<style scoped>
.user-mini-avatar {
  width: 30px; height: 30px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.75rem;
  flex-shrink: 0;
  background: #FFF3DA; color: #A66E00;
}
.user-mini-avatar.admin { background: rgba(255,45,111,0.15); color: #FF2D6F; }
.user-mini-avatar.staff { background: rgba(255,180,0,0.18); color: #A66E00; }
.role-badge {
  display: inline-block; padding: 0.2rem 0.7rem;
  border-radius: 100px; font-size: 0.75rem; font-weight: 700;
  text-transform: uppercase; letter-spacing: 0.04em;
}
.role-citizen { background: #FFE9F2; color: #9B2C6F; }
.role-staff { background: #FFF3DA; color: #A66E00; }
.role-admin { background: rgba(255,45,111,0.15); color: #FF2D6F; }
.badge-active { color: var(--success); font-size: 0.83rem; font-weight: 700; }
.badge-inactive { color: var(--danger); font-size: 0.83rem; font-weight: 700; }
.sub-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 100px; font-size: 0.72rem; font-weight: 700; }
.sub-active { background: rgba(224,33,138,0.14); color: #E0218A; }
.sub-cancelled { background: rgba(148,163,184,0.2); color: #64748B; }
</style>
