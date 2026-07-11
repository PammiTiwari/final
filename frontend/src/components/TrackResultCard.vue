<template>
  <div class="track-result">
    <button class="btn btn-outline btn-sm mb-3" @click="$emit('close')">← Search Another Complaint</button>

    <div class="card">
      <div class="detail-header">
        <div>
          <div class="cmp-id-big">{{ result.cmp_id }}</div>
          <div class="mt-1">
            <span :class="['badge', `badge-${result.status}`]">{{ fmtStatus(result.status) }}</span>
            <span :class="['badge', `badge-${result.priority}`]" class="ml-2">{{ result.priority }}</span>
          </div>
        </div>
        <div class="detail-dept">{{ result.department }}</div>
      </div>

      <div v-if="result.status === 'on_hold_weather'" class="alert alert-info">
        &#9729; <strong>On hold — weather restrictions.</strong> {{ result.hold_reason }}
      </div>

      <div class="detail-section">
        <div class="detail-row">
          <div class="detail-label">Category</div>
          <div class="detail-value capitalize">{{ result.category }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">Location</div>
          <div class="detail-value">{{ result.address }}</div>
        </div>
        <div class="detail-row" v-if="result.ward">
          <div class="detail-label">Ward</div>
          <div class="detail-value">{{ result.ward }}</div>
        </div>
        <div class="detail-row">
          <div class="detail-label">Description</div>
          <div class="detail-value">{{ result.description }}</div>
        </div>
        <div v-if="result.image_urls?.length" class="detail-row">
          <div class="detail-label">Photos</div>
          <div class="detail-value">
            <ImageGallery :images="result.image_urls" alt="Complaint photo" />
          </div>
        </div>
        <div class="detail-row">
          <div class="detail-label">Submitted On</div>
          <div class="detail-value">{{ fmtDate(result.created_at) }}</div>
        </div>
        <div class="detail-row" v-if="result.assignment">
          <div class="detail-label">Assigned To</div>
          <div class="detail-value">
            {{ result.assignment.staff_name }}
            <span v-if="result.assignment.staff_department" class="text-muted"> ({{ result.assignment.staff_department }})</span>
          </div>
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
            <span>{{ fmtDate(result.created_at) }}</span>
          </div>
        </li>
        <li class="timeline-item">
          <div :class="['timeline-dot', result.assignment ? 'done' : 'pending']">
            {{ result.assignment ? '✓' : '' }}
          </div>
          <div class="timeline-content">
            <p>Assigned to Department</p>
            <span v-if="result.assignment">{{ fmtDate(result.assignment.assigned_at) }} — {{ result.assignment.staff_department }}</span>
            <span v-else class="text-faint">Pending assignment</span>
          </div>
        </li>
        <li class="timeline-item">
          <div :class="['timeline-dot', ['in_progress','resolved','closed'].includes(result.status) ? 'done' : 'pending']">
            {{ ['in_progress','resolved','closed'].includes(result.status) ? '✓' : '' }}
          </div>
          <div class="timeline-content">
            <p>Work In Progress</p>
            <span v-if="['in_progress','resolved','closed'].includes(result.status)">Status updated to in progress</span>
            <span v-else class="text-faint">Yet to start</span>
          </div>
        </li>
        <li class="timeline-item">
          <div :class="['timeline-dot', ['resolved','closed'].includes(result.status) ? 'done' : 'pending']">
            {{ ['resolved','closed'].includes(result.status) ? '✓' : '' }}
          </div>
          <div class="timeline-content">
            <p>Resolved</p>
            <span v-if="result.resolved_at">{{ fmtDate(result.resolved_at) }}</span>
            <span v-else class="text-faint">Yet to be resolved</span>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import ImageGallery from './ImageGallery.vue'
import { fmtStatus } from '../utils/status'

defineProps({ result: { type: Object, required: true } })
defineEmits(['close'])

function fmtDate(d) {
  if (!d) return ''
  return new Date(d).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.track-result { max-width: 640px; }
.detail-header { display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 1rem; margin-bottom: 1rem; border-bottom: 1px solid var(--border); }
.cmp-id-big { font-family: monospace; font-size: 1.1rem; font-weight: 800; color: var(--text); }
.detail-dept { font-size: 0.8rem; font-weight: 600; color: var(--text-muted); background: var(--accent); padding: 0.3rem 0.75rem; border-radius: 100px; }
.detail-section { margin-top: 0.5rem; }
.detail-value :deep(.image-gallery) { max-width: 480px; }
</style>
