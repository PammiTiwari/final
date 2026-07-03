<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Book a Facility" :unread-count="unread" @notifications="showNotif = true" />
      <div class="content-area">
        <div class="page-header">
          <p>Browse and book community halls, sports grounds, parks and more.</p>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else>
          <div class="facilities-grid">
            <div v-for="f in facilities" :key="f.id" class="facility-card card">
              <ImageGallery v-if="f.image_urls?.length" :images="f.image_urls" alt="Facility photo" class="facility-gallery" />
              <div class="facility-header">
                <div class="facility-type-icon">{{ typeIcon(f.facility_type) }}</div>
                <span class="facility-type-badge">{{ f.facility_type }}</span>
              </div>
              <h3 class="facility-name">{{ f.name }}</h3>
              <p class="facility-desc">{{ f.description }}</p>
              <div class="facility-info">
                <div class="info-chip">👥 Capacity: {{ f.capacity }}</div>
                <div class="info-chip">📍 {{ f.ward || 'City' }}</div>
                <div class="info-chip">{{ f.fee_per_hour > 0 ? `💰 ₹${f.fee_per_hour}/hr` : '🆓 Free' }}</div>
              </div>
              <div v-if="f.amenities" class="amenities">
                <span v-for="a in f.amenities.split(',')" :key="a" class="amenity-chip">{{ a.trim() }}</span>
              </div>
              <div class="facility-address">📍 {{ f.address }}</div>
              <button class="btn btn-primary w-full mt-4" @click="openBooking(f)">
                📅 Book Now
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Booking modal -->
    <div v-if="bookingModal.show" class="modal-overlay" @click.self="bookingModal.show = false">
      <div class="modal modal-w-lg">
        <div class="modal-header">
          <h2>Book {{ bookingModal.facility?.name }}</h2>
          <button class="modal-close" @click="bookingModal.show = false">✕</button>
        </div>

        <ImageGallery v-if="bookingModal.facility?.image_urls?.length" :images="bookingModal.facility.image_urls" alt="Facility photo" class="mb-4" />
        <div class="facility-booking-info">
          <span>👥 Capacity: {{ bookingModal.facility?.capacity }}</span>
          <span>{{ bookingModal.facility?.fee_per_hour > 0 ? `💰 ₹${bookingModal.facility?.fee_per_hour}/hr` : '🆓 Free' }}</span>
          <span>📍 {{ bookingModal.facility?.ward }}</span>
        </div>

        <div v-if="bookingModal.error" class="alert alert-error mb-4">{{ bookingModal.error }}</div>

        <form @submit.prevent="submitBooking" class="flex-col gap-4">
          <div class="form-group">
            <label>Booking Date *</label>
            <input v-model="bookingForm.booking_date" type="date" class="form-control"
                   :min="today" required @change="loadAvailability" />
          </div>

          <!-- Already booked slots for selected date -->
          <div v-if="slotsLoading" class="text-sm text-muted">Checking availability...</div>
          <div v-else-if="bookedSlots.length > 0" class="booked-slots-info">
            <div class="booked-slots-title">⚠️ Already booked on this date:</div>
            <div v-for="slot in bookedSlots" :key="slot.start" class="booked-slot">
              {{ slot.start }} – {{ slot.end }}
              <span :class="`badge badge-${slot.status}`" class="ml-2">{{ slot.status }}</span>
            </div>
          </div>
          <div v-else-if="bookingForm.booking_date" class="alert alert-success m-0 slot-available-alert">
            ✅ No existing bookings on this date — all slots available
          </div>

          <div class="grid-2">
            <div class="form-group">
              <label>Start Time *</label>
              <input v-model="bookingForm.start_time" type="time" class="form-control"
                     min="06:00" max="21:00" required />
            </div>
            <div class="form-group">
              <label>End Time *</label>
              <input v-model="bookingForm.end_time" type="time" class="form-control"
                     min="07:00" max="22:00" required />
            </div>
          </div>
          <div v-if="estimatedFee > 0" class="fee-preview">
            Estimated fee: <strong>₹{{ estimatedFee }}</strong>
            <span class="text-xs text-muted"> (₹{{ bookingModal.facility?.fee_per_hour }}/hr × {{ hours }} hr)</span>
          </div>
          <div class="form-group">
            <label>Number of Attendees *</label>
            <input v-model.number="bookingForm.attendees" type="number" class="form-control"
                   min="1" :max="bookingModal.facility?.capacity" required />
          </div>
          <div class="form-group">
            <label>Purpose of Booking *</label>
            <input v-model="bookingForm.purpose" type="text" class="form-control"
                   placeholder="e.g., Community meeting, Birthday celebration, Sports event" required />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-outline" @click="bookingModal.show = false">Cancel</button>
            <button type="submit" class="btn btn-primary" :disabled="bookingModal.loading">
              {{ bookingModal.loading ? 'Booking…' : '✅ Confirm Booking' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Success modal -->
    <div v-if="successModal" class="modal-overlay">
      <div class="modal modal-w-sm text-center">
        <div class="success-icon">🎉</div>
        <h2 class="navy-text">Booking Requested!</h2>
        <p class="text-muted success-msg">
          Your booking is pending confirmation. You'll be notified once approved.
          {{ successModal.fee > 0 ? `Payment of ₹${successModal.fee} will be due after confirmation.` : '' }}
        </p>
        <div class="flex gap-3 justify-center mt-4">
          <router-link to="/bookings" class="btn btn-primary">View My Bookings</router-link>
          <button class="btn btn-outline" @click="successModal = null">Book Another</button>
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
import ImageGallery from "../../components/ImageGallery.vue"
import api from "../../api"

const loading = ref(true)
const facilities = ref([])
const showNotif = ref(false)
const unread = ref(0)
const successModal = ref(null)
const today = new Date().toISOString().split("T")[0]

const bookingModal = ref({ show: false, facility: null, loading: false, error: "" })
const bookingForm = ref({ booking_date: "", start_time: "", end_time: "", attendees: 1, purpose: "" })
const bookedSlots = ref([])
const slotsLoading = ref(false)

const hours = computed(() => {
  if (!bookingForm.value.start_time || !bookingForm.value.end_time) return 0
  const [sh, sm] = bookingForm.value.start_time.split(":").map(Number)
  const [eh, em] = bookingForm.value.end_time.split(":").map(Number)
  return Math.max(0, (eh * 60 + em - sh * 60 - sm) / 60)
})

const estimatedFee = computed(() => {
  if (!bookingModal.value.facility) return 0
  return Math.round(bookingModal.value.facility.fee_per_hour * hours.value * 100) / 100
})

onMounted(async () => {
  const [facRes, notifRes] = await Promise.all([api.get("/facilities"), api.get("/notifications")])
  facilities.value = facRes.data.filter(f => f.is_active)
  unread.value = notifRes.data.unread_count
  loading.value = false
})

function openBooking(facility) {
  bookingModal.value = { show: true, facility, loading: false, error: "" }
  bookingForm.value = { booking_date: "", start_time: "", end_time: "", attendees: 1, purpose: "" }
  bookedSlots.value = []
}

async function loadAvailability() {
  const date = bookingForm.value.booking_date
  const facilityId = bookingModal.value.facility?.id
  if (!date || !facilityId) return
  slotsLoading.value = true
  try {
    const res = await api.get(`/facilities/${facilityId}/availability`, { params: { date } })
    bookedSlots.value = res.data.booked_slots || []
  } catch {
    bookedSlots.value = []
  } finally {
    slotsLoading.value = false
  }
}

async function submitBooking() {
  bookingModal.value.loading = true
  bookingModal.value.error = ""
  try {
    const { data } = await api.post("/bookings", {
      ...bookingForm.value,
      facility_id: bookingModal.value.facility.id,
    })
    bookingModal.value.show = false
    successModal.value = { fee: data.fee }
  } catch (e) {
    bookingModal.value.error = e.response?.data?.message || "Booking failed."
  } finally {
    bookingModal.value.loading = false
  }
}

function typeIcon(t) {
  const map = {
    "Community Hall": "🏛️", "Sports Ground": "⚽", "Conference Room": "🏢",
    "Park": "🌳", "Auditorium": "🎭", "Library": "📚",
  }
  return map[t] || "🏗️"
}
</script>

<style scoped>
.facilities-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}
.facility-card { display: flex; flex-direction: column; }
.facility-gallery.count-1 :deep(img) { max-height: 170px; }
.facility-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.75rem; }
.facility-type-icon { font-size: 2rem; }
.facility-type-badge {
  background: var(--bg); color: var(--text-muted);
  font-size: 0.75rem; font-weight: 700;
  padding: 0.2rem 0.7rem; border-radius: 100px;
  text-transform: uppercase; letter-spacing: 0.05em;
}
.facility-name { font-size: 1.05rem; font-weight: 800; color: var(--navy); margin-bottom: 0.4rem; }
.facility-desc { font-size: 0.85rem; color: var(--text-muted); line-height: 1.5; margin-bottom: 0.85rem; flex: 1; }
.facility-info { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.75rem; }
.info-chip {
  background: rgba(255,180,0,0.08); color: var(--text);
  border: 1px solid rgba(255,180,0,0.2);
  padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600;
}
.amenities { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-bottom: 0.75rem; }
.amenity-chip {
  background: var(--bg); color: var(--text-muted);
  padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem;
}
.facility-address { font-size: 0.82rem; color: var(--text-muted); }
.facility-booking-info {
  display: flex; gap: 1rem; flex-wrap: wrap;
  background: var(--bg); padding: 0.75rem 1rem; border-radius: 8px;
  font-size: 0.85rem; color: var(--text-muted); font-weight: 600;
  margin-bottom: 1.25rem;
}
.fee-preview {
  background: #D7F5E5;
  color: #0E7A4F;
  padding: 0.6rem 0.85rem;
  border-radius: 8px;
  font-size: 0.9rem;
}
.booked-slots-info {
  background: #FFF0F6;
  border: 1px solid #FFB400;
  border-radius: 8px;
  padding: 0.65rem 0.85rem;
  font-size: 0.84rem;
}
.booked-slots-title { font-weight: 700; color: #A66E00; margin-bottom: 0.35rem; }
.booked-slot { color: #8a5800; padding: 0.15rem 0; }
.slot-available-alert { font-size: 0.82rem; padding: 0.5rem 0.85rem; }
.success-icon { font-size: 3rem; margin-bottom: 1rem; }
.navy-text { color: var(--navy); }
.success-msg { margin: 1rem 0; }
.justify-center { justify-content: center; }
</style>
