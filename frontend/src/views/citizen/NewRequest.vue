<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Submit Complaint" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Report a civic issue in your area</p>
          </div>
        </div>

        <div class="form-container card">
          <div v-if="success" class="alert alert-success">
            Complaint submitted successfully! ID: <strong>{{ submittedId }}</strong>
            <router-link to="/complaints" class="ml-3 underline">View all complaints</router-link>
          </div>
          <div v-if="error" class="alert alert-error">{{ error }}</div>
          <div v-if="upvotedMsg" class="alert alert-success">
            {{ upvotedMsg }}
            <router-link to="/complaints" class="ml-3 underline">View all complaints</router-link>
          </div>

          <SimilarComplaints v-if="similar.length && !success && !upvotedMsg"
            :matches="similar" @proceed="doSubmit" @upvoted="onUpvoted" />

          <form @submit.prevent="handleSubmit" v-if="!success && !upvotedMsg">

            <!-- Scan a paper complaint with AI -->
            <div class="scan-box">
              <div class="scan-box-text">
                <strong>📄 Got a written complaint on paper?</strong>
                <p>Take a photo of it and we'll fill the form for you.</p>
              </div>
              <button type="button" class="btn btn-outline btn-sm" @click="$refs.scanInput.click()" :disabled="scanLoading">
                {{ scanLoading ? 'Reading...' : '✦ Scan Paper' }}
              </button>
              <input ref="scanInput" type="file" accept="image/*" class="hidden" @change="handleScanPaper" />
            </div>
            <p v-if="scanMessage" class="ai-hint scan-msg" :class="{ 'scan-msg-error': scanError }">{{ scanMessage }}</p>

            <!-- Category + AI Suggest -->
            <div class="form-group">
              <label>Category <span class="req">*</span></label>
              <div class="category-row">
                <select v-model="form.category" class="form-control" required>
                  <option value="">Select Category</option>
                  <option value="road">Road</option>
                  <option value="water">Water</option>
                  <option value="electricity">Electricity</option>
                  <option value="sanitation">Sanitation</option>
                  <option value="waste">Waste</option>
                  <option value="parks">Parks & Public Spaces</option>
                  <option value="complaint">General Complaint</option>
                  <option value="maintenance">Maintenance</option>
                  <option value="other">Other</option>
                </select>
                <button type="button" class="btn btn-outline btn-sm" @click="suggestCategory" :disabled="aiLoading || !form.description">
                  {{ aiLoading ? 'Thinking...' : '✦ AI Suggest' }}
                </button>
              </div>
              <p v-if="aiMessage" class="ai-hint">{{ aiMessage }}</p>
            </div>

            <div class="form-group">
              <label>Title <span class="req">*</span></label>
              <input v-model="form.title" type="text" class="form-control" placeholder="Short summary" required />
            </div>

            <div class="form-group">
              <label>Location / Area <span class="req">*</span></label>
              <input v-model="form.address" type="text" class="form-control" placeholder="Enter location / area" required />
            </div>

            <div class="form-group">
              <label>Pin location on map (optional)</label>
              <LocationPicker @located="onLocated" />
            </div>

            <div class="form-group">
              <label>Ward</label>
              <select v-model="form.ward" class="form-control">
                <option value="">Select Ward (Optional)</option>
                <option v-for="w in wards" :key="w" :value="w">{{ w }}</option>
              </select>
            </div>

            <div class="form-group">
              <label>Description <span class="req">*</span></label>
              <textarea v-model="form.description" class="form-control" rows="4"
                placeholder="Describe your issue in detail... (then click AI Suggest for auto category)" required></textarea>
            </div>

            <div class="form-group">
              <label>Priority</label>
              <select v-model="form.priority" class="form-control">
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>

            <!-- Image Upload -->
            <div class="form-group">
              <label>Upload Photos (Optional)</label>
              <MultiImageUpload v-model="form.image_urls" :max="3" />
            </div>

            <div class="form-actions">
              <router-link to="/complaints" class="btn btn-secondary">Cancel</router-link>
              <button type="submit" class="btn btn-primary" :disabled="loading">
                {{ loading ? 'Submitting...' : 'Submit Complaint' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import LocationPicker from '../../components/LocationPicker.vue'
import SimilarComplaints from '../../components/SimilarComplaints.vue'
import MultiImageUpload from '../../components/MultiImageUpload.vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'

const auth = useAuthStore()

const form = ref({
  category: '',
  title: '',
  address: '',
  ward: auth.user?.ward || '',
  description: '',
  priority: 'medium',
  image_urls: [],
  latitude: null,
  longitude: null,
})
const loading = ref(false)
const error = ref('')
const success = ref(false)
const submittedId = ref('')
const aiLoading = ref(false)
const aiMessage = ref('')
const similar = ref([])
const upvotedMsg = ref('')
const scanLoading = ref(false)
const scanMessage = ref('')
const scanError = ref(false)

const wards = ['Ward-1', 'Ward-2', 'Ward-3', 'Central']

async function handleScanPaper(e) {
  const file = e.target.files[0]
  if (!file) return
  scanLoading.value = true
  scanError.value = false
  scanMessage.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const res = await api.post('/ai/extract-from-image', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    form.value.category = res.data.category
    if (res.data.title) form.value.title = res.data.title
    form.value.description = res.data.description
    if (res.data.address) form.value.address = res.data.address
    form.value.priority = res.data.priority
    if (res.data.image_url && !form.value.image_urls.includes(res.data.image_url) && form.value.image_urls.length < 3) {
      form.value.image_urls.push(res.data.image_url)
    }
    scanMessage.value = 'Read the paper and filled the form below — please check it over before submitting. Add a photo of the actual problem separately if you have one.'
  } catch (err) {
    scanError.value = true
    scanMessage.value = err.response?.data?.message || 'Could not read that photo. Please fill the form manually.'
  } finally {
    scanLoading.value = false
    if (e.target) e.target.value = ''
  }
}

function onLocated({ lat, lng, address }) {
  form.value.latitude = lat
  form.value.longitude = lng
  if (address && !form.value.address) form.value.address = address
}

async function suggestCategory() {
  if (!form.value.description.trim()) return
  aiLoading.value = true
  aiMessage.value = ''
  try {
    const res = await api.post('/ai/suggest', { description: form.value.description })
    form.value.category = res.data.category
    aiMessage.value = `✦ AI suggested: "${res.data.category}" (${res.data.confidence})`
  } catch {
    aiMessage.value = 'Could not get AI suggestion. Please select manually.'
  } finally {
    aiLoading.value = false
  }
}

async function handleSubmit() {
  if (loading.value) return
  error.value = ''
  if (!form.value.category || !form.value.title.trim() || !form.value.address.trim() || !form.value.description.trim()) {
    error.value = 'Please fill all required fields'
    return
  }
  // Check for likely duplicates first; show the panel if any, otherwise create
  loading.value = true
  try {
    const { data } = await api.post('/requests/similar', {
      category: form.value.category, ward: form.value.ward, description: form.value.description,
      latitude: form.value.latitude, longitude: form.value.longitude,
    })
    if (data.length) {
      similar.value = data
      return
    }
  } catch { /* non-blocking: fall through to submit */ }
  finally { loading.value = false }
  doSubmit()
}

async function doSubmit() {
  if (loading.value) return
  similar.value = []
  error.value = ''
  loading.value = true
  try {
    const res = await api.post('/requests', form.value)
    submittedId.value = res.data.cmp_id
    success.value = true
  } catch (e) {
    error.value = e.response?.data?.message || 'Failed to submit complaint'
  } finally {
    loading.value = false
  }
}

function onUpvoted(item) {
  upvotedMsg.value = `Thanks! We added your support to ${item.cmp_id} instead of creating a duplicate.`
}
</script>

<style scoped>
.form-container { max-width: 640px; }
.req { color: var(--danger); }
.form-actions { display: flex; gap: 0.75rem; justify-content: flex-end; margin-top: 0.5rem; }
.category-row { display: flex; gap: 0.5rem; align-items: center; }
.category-row .form-control { flex: 1; }
.ai-hint { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.25rem; }

.scan-box {
  display: flex; align-items: center; justify-content: space-between; gap: 1rem;
  background: var(--accent); border: 1px dashed var(--primary); border-radius: var(--radius);
  padding: 0.9rem 1.1rem; margin-bottom: 1.1rem;
}
.scan-box-text strong { font-size: 0.85rem; color: var(--text); }
.scan-box-text p { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.1rem; }
.scan-msg { margin-top: -0.6rem; margin-bottom: 1.1rem; }
.scan-msg-error { color: var(--danger); }
</style>
