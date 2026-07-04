<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar :title="`Complaint ${complaint?.cmp_id || ''}`" />
      <div class="content-area">
        <div class="detail-topbar">
          <router-link to="/complaints" class="back-link">&larr; Back to Complaints</router-link>
          <button v-if="complaint?.status === 'pending'" class="btn btn-sm btn-danger" :disabled="deleting" @click="deleteComplaint">
            {{ deleting ? 'Deleting...' : '🗑 Delete Complaint' }}
          </button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else-if="!complaint" class="empty-state">
          <p>Complaint not found.</p>
        </div>
        <template v-else>
          <div class="card mt-4">
            <div class="detail-header">
              <div>
                <div class="cmp-id-big">{{ complaint.cmp_id }}</div>
                <div class="mt-1">
                  <span :class="['badge', `badge-${complaint.status}`]">{{ fmtStatus(complaint.status) }}</span>
                  <span :class="['badge', `badge-${complaint.priority}`]" class="ml-2">{{ complaint.priority }}</span>
                </div>
              </div>
              <div class="detail-dept">{{ complaint.department }}</div>
            </div>

            <div v-if="complaint.status === 'on_hold_weather'" class="alert alert-info">
              &#9729; <strong>On hold — weather restrictions.</strong> {{ complaint.hold_reason }}
            </div>

            <div class="detail-section">
              <div class="detail-row">
                <div class="detail-label">Category</div>
                <div class="detail-value capitalize">{{ complaint.category }}</div>
              </div>
              <div class="detail-row">
                <div class="detail-label">Location</div>
                <div class="detail-value">{{ complaint.address }}</div>
              </div>
              <div class="detail-row" v-if="complaint.ward">
                <div class="detail-label">Ward</div>
                <div class="detail-value">{{ complaint.ward }}</div>
              </div>
              <div class="detail-row">
                <div class="detail-label">Description</div>
                <div class="detail-value">{{ complaint.description }}</div>
              </div>
              <div v-if="complaint.image_urls?.length" class="detail-row">
                <div class="detail-label">Photos</div>
                <div class="detail-value">
                  <ImageGallery :images="complaint.image_urls" alt="Complaint photo" />
                </div>
              </div>
              <div v-if="complaint.evidence_urls?.length" class="detail-row">
                <div class="detail-label">Resolution Evidence</div>
                <div class="detail-value">
                  <ImageGallery :images="complaint.evidence_urls" alt="Resolution evidence photo" />
                </div>
              </div>
              <div class="detail-row">
                <div class="detail-label">Submitted By</div>
                <div class="detail-value">{{ complaint.citizen_name }}</div>
              </div>
              <div class="detail-row">
                <div class="detail-label">Submitted On</div>
                <div class="detail-value">{{ fmtDateFull(complaint.created_at) }}</div>
              </div>
              <div class="detail-row" v-if="complaint.assignment">
                <div class="detail-label">Assigned To</div>
                <div class="detail-value">
                  {{ complaint.assignment.staff_name }}
                  <span v-if="complaint.assignment.staff_department" class="text-muted"> ({{ complaint.assignment.staff_department }})</span>
                </div>
              </div>
              <div class="detail-row" v-if="complaint.admin_notes">
                <div class="detail-label">Remarks</div>
                <div class="detail-value">{{ complaint.admin_notes }}</div>
              </div>
            </div>
          </div>

          <!-- Timeline -->
          <div class="card mt-4">
            <div class="section-title">Timeline</div>
            <ul class="timeline">
              <li class="timeline-item">
                <div class="timeline-dot done">&#10003;</div>
                <div class="timeline-content">
                  <p>Complaint Submitted</p>
                  <span>{{ fmtDateFull(complaint.created_at) }}</span>
                </div>
              </li>
              <li class="timeline-item">
                <div :class="['timeline-dot', complaint.assignment ? 'done' : 'pending']">
                  {{ complaint.assignment ? '✓' : '' }}
                </div>
                <div class="timeline-content">
                  <p>Assigned to Department</p>
                  <span v-if="complaint.assignment">{{ fmtDateFull(complaint.assignment.assigned_at) }} — {{ complaint.assignment.staff_department }}</span>
                  <span v-else class="text-faint">Pending assignment</span>
                </div>
              </li>
              <li class="timeline-item">
                <div :class="['timeline-dot', ['in_progress','resolved','closed'].includes(complaint.status) ? 'done' : 'pending']">
                  {{ ['in_progress','resolved','closed'].includes(complaint.status) ? '✓' : '' }}
                </div>
                <div class="timeline-content">
                  <p>Work In Progress</p>
                  <span v-if="['in_progress','resolved','closed'].includes(complaint.status)">Status updated to in progress</span>
                  <span v-else class="text-faint">Yet to start</span>
                </div>
              </li>
              <li class="timeline-item">
                <div :class="['timeline-dot', ['resolved','closed'].includes(complaint.status) ? 'done' : 'pending']">
                  {{ ['resolved','closed'].includes(complaint.status) ? '✓' : '' }}
                </div>
                <div class="timeline-content">
                  <p>Resolved</p>
                  <span v-if="complaint.resolved_at">{{ fmtDateFull(complaint.resolved_at) }}</span>
                  <span v-else class="text-faint">Yet to be resolved</span>
                </div>
              </li>
            </ul>
          </div>

          <ResolveActions
            v-if="['resolved','closed'].includes(complaint.status) || complaint.reopen_count > 0"
            :complaint="complaint" @updated="onUpdated" />
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import ResolveActions from '../../components/ResolveActions.vue'
import ImageGallery from '../../components/ImageGallery.vue'
import api from '../../api'
import { fmtStatus } from '../../utils/status'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const complaint = ref(null)
const deleting = ref(false)

onMounted(async () => {
  try {
    const res = await api.get(`/requests/${route.params.id}`)
    complaint.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

function onUpdated(data) {
  complaint.value = data
}

async function deleteComplaint() {
  if (deleting.value) return
  if (!confirm(`Delete complaint ${complaint.value.cmp_id}? This cannot be undone.`)) return
  deleting.value = true
  try {
    await api.delete(`/requests/${complaint.value.id}`)
    router.push('/complaints')
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to delete complaint')
    deleting.value = false
  }
}

function fmtDateFull(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.detail-topbar { display: flex; justify-content: space-between; align-items: center; }
.back-link { font-size: 0.85rem; font-weight: 600; color: #9B2C6F; display: inline-flex; align-items: center; gap: 0.3rem; }
.back-link:hover { color: #5C1A41; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid #FFD1E6; }
.cmp-id-big { font-family: monospace; font-size: 1.1rem; font-weight: 800; color: #5C1A41; }
.detail-dept { font-size: 0.8rem; font-weight: 600; color: #B0708F; background: #FFE9F2; padding: 0.3rem 0.75rem; border-radius: 100px; }
.detail-section { margin-top: 0.5rem; }
.detail-value :deep(.image-gallery) { max-width: 480px; }
</style>
