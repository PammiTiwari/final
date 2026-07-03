<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Manage Facilities" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header flex-between">
          <div>
            <p>Add, edit and manage civic facilities available for booking</p>
          </div>
          <button class="btn btn-primary" @click="openAdd">+ Add Facility</button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="facilities-grid">
          <div v-for="f in facilities" :key="f.id" class="facility-card card">
            <ImageGallery v-if="f.image_urls?.length" :images="f.image_urls" alt="Facility photo" class="fac-gallery" />
            <div class="fac-top">
              <div>
                <span class="fac-type">{{ f.facility_type }}</span>
                <span :class="f.is_active ? 'status-active' : 'status-inactive'" class="ml-3">
                  {{ f.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="text-sm text-muted">#{{ f.id }}</div>
            </div>
            <h3 class="fac-name">{{ f.name }}</h3>
            <div class="fac-details">
              <span>👥 {{ f.capacity }}</span>
              <span>📍 {{ f.ward }}</span>
              <span>{{ f.fee_per_hour > 0 ? `₹${f.fee_per_hour}/hr` : 'Free' }}</span>
            </div>
            <p class="fac-desc">{{ f.description }}</p>
            <div class="fac-actions">
              <button class="btn btn-outline btn-sm" @click="openEdit(f)">✏️ Edit</button>
              <button :class="`btn btn-sm ${f.is_active ? 'btn-warning' : 'btn-success'}`"
                      @click="toggleActive(f)">
                {{ f.is_active ? 'Deactivate' : 'Activate' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Add / Edit modal -->
    <div v-if="modal.show" class="modal-overlay" @click.self="modal.show = false">
      <div class="modal modal-w-lg">
        <div class="modal-header">
          <h2>{{ modal.isEdit ? 'Edit Facility' : 'Add New Facility' }}</h2>
          <button class="modal-close" @click="modal.show = false">✕</button>
        </div>
        <div v-if="modal.error" class="alert alert-error mb-4">{{ modal.error }}</div>
        <form @submit.prevent="submitFacility" class="flex-col gap-4">
          <div class="grid-2">
            <div class="form-group col-span-full">
              <label>Facility Name *</label>
              <input v-model="form.name" type="text" class="form-control" required placeholder="e.g., City Community Hall" />
            </div>
            <div class="form-group">
              <label>Type *</label>
              <select v-model="form.facility_type" class="form-control" required>
                <option value="">Select type</option>
                <option v-for="t in facilityTypes" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Ward</label>
              <select v-model="form.ward" class="form-control">
                <option value="">Select Ward</option>
                <option v-for="w in wards" :key="w" :value="w">{{ w }}</option>
              </select>
            </div>
            <div class="form-group col-span-full">
              <label>Address *</label>
              <input v-model="form.address" type="text" class="form-control" required />
            </div>
            <div class="form-group">
              <label>Capacity *</label>
              <input v-model.number="form.capacity" type="number" class="form-control" required min="1" />
            </div>
            <div class="form-group">
              <label>Fee per Hour (₹)</label>
              <input v-model.number="form.fee_per_hour" type="number" class="form-control" min="0" step="50" />
            </div>
            <div class="form-group col-span-full">
              <label>Description</label>
              <textarea v-model="form.description" class="form-control" rows="2"></textarea>
            </div>
            <div class="form-group col-span-full">
              <label>Amenities <span class="text-xs text-muted">(comma-separated)</span></label>
              <input v-model="form.amenities" type="text" class="form-control" placeholder="AC, Parking, WiFi, Projector" />
            </div>
            <div class="form-group col-span-full">
              <label>Photos</label>
              <MultiImageUpload v-model="form.image_urls" :max="3" />
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline" @click="modal.show = false">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="modal.loading">
              {{ modal.loading ? 'Saving…' : (modal.isEdit ? 'Save Changes' : 'Add Facility') }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <NotificationsPanel v-if="showNotif" @close="showNotif = false" @read="unread = Math.max(0,unread-1)" />
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue"
import AppSidebar from "../../components/AppSidebar.vue"
import AppTopbar from "../../components/AppTopbar.vue"
import NotificationsPanel from "../../components/NotificationsPanel.vue"
import ImageGallery from "../../components/ImageGallery.vue"
import MultiImageUpload from "../../components/MultiImageUpload.vue"
import api from "../../api"

const loading = ref(true)
const facilities = ref([])
const showNotif = ref(false)
const unread = ref(0)
const facilityTypes = ["Community Hall","Sports Ground","Conference Room","Park","Auditorium","Library Hall","Swimming Pool","Other"]
const wards = ["Ward-1","Ward-2","Ward-3","Ward-4","Ward-5","Central"]

const modal = ref({ show: false, isEdit: false, facilityId: null, loading: false, error: "" })
const form = ref({ name: "", facility_type: "", address: "", ward: "", capacity: 50, fee_per_hour: 0, description: "", amenities: "", image_urls: [] })

onMounted(async () => {
  const [fRes, nRes] = await Promise.all([api.get("/facilities?active=false"), api.get("/notifications")])
  facilities.value = fRes.data
  unread.value = nRes.data.unread_count
  loading.value = false
})

function openAdd() {
  form.value = { name: "", facility_type: "", address: "", ward: "", capacity: 50, fee_per_hour: 0, description: "", amenities: "", image_urls: [] }
  modal.value = { show: true, isEdit: false, facilityId: null, loading: false, error: "" }
}

function openEdit(f) {
  form.value = { name: f.name, facility_type: f.facility_type, address: f.address, ward: f.ward || "",
                 capacity: f.capacity, fee_per_hour: f.fee_per_hour, description: f.description || "",
                 amenities: f.amenities || "", image_urls: f.image_urls || [] }
  modal.value = { show: true, isEdit: true, facilityId: f.id, loading: false, error: "" }
}

async function submitFacility() {
  if (modal.value.loading) return
  modal.value.loading = true
  modal.value.error = ""
  try {
    if (modal.value.isEdit) {
      const { data } = await api.put(`/facilities/${modal.value.facilityId}`, form.value)
      const idx = facilities.value.findIndex(f => f.id === modal.value.facilityId)
      if (idx !== -1) facilities.value[idx] = data
    } else {
      const { data } = await api.post("/facilities", form.value)
      facilities.value.unshift(data)
    }
    modal.value.show = false
  } catch (e) {
    modal.value.error = e.response?.data?.message || "Operation failed."
  } finally {
    modal.value.loading = false
  }
}

async function toggleActive(f) {
  try {
    await api.put(`/facilities/${f.id}`, { is_active: !f.is_active })
    f.is_active = !f.is_active
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to update facility')
  }
}
</script>

<style scoped>
.facilities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.25rem;
}
.facility-card { padding: 1.25rem; }
.fac-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.fac-type {
  font-size: 0.75rem; font-weight: 700; text-transform: uppercase;
  background: var(--bg); color: var(--text-muted);
  padding: 0.2rem 0.6rem; border-radius: 100px; letter-spacing: 0.04em;
}
.status-active { color: var(--success); font-size: 0.78rem; font-weight: 700; }
.status-inactive { color: var(--danger); font-size: 0.78rem; font-weight: 700; }
.fac-name { font-size: 1rem; font-weight: 800; color: var(--navy); margin-bottom: 0.4rem; }
.fac-details { display: flex; gap: 0.85rem; font-size: 0.82rem; color: var(--text-muted); font-weight: 500; margin-bottom: 0.5rem; }
.fac-desc { font-size: 0.85rem; color: var(--text-muted); line-height: 1.4; margin-bottom: 1rem; }
.fac-actions { display: flex; gap: 0.5rem; }
textarea.form-control { resize: vertical; }
.fac-gallery.count-1 :deep(img) { max-height: 160px; }
</style>
