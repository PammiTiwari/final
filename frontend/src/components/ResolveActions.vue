<template>
  <div class="card resolve-card mt-4">
    <!-- Resolved → citizen confirms or reopens -->
    <template v-if="complaint.status === 'resolved'">
      <div class="section-title">Was this resolved to your satisfaction?</div>
      <p class="resolve-hint">Confirm and rate the work, or reopen it if the issue isn't actually fixed.</p>
      <div class="resolve-actions">
        <button class="btn btn-success" @click="openClose">&#10003; Confirm &amp; Close</button>
        <button class="btn btn-outline" @click="openReopen" :disabled="complaint.reopen_count >= 2">
          &#8635; Reopen
        </button>
      </div>
      <p v-if="complaint.reopen_count >= 2" class="resolve-note">
        Reopened twice already — please contact the department for further help.
      </p>
    </template>

    <!-- Closed with a rating → show what was given -->
    <template v-else-if="complaint.status === 'closed' && complaint.rating">
      <div class="section-title">Your Feedback</div>
      <div class="stars-static">
        <span v-for="n in 5" :key="n" :class="{ filled: n <= complaint.rating }">&#9733;</span>
        <span class="rating-num">{{ complaint.rating }}/5</span>
      </div>
      <p v-if="complaint.feedback" class="resolve-feedback">"{{ complaint.feedback }}"</p>
    </template>

    <!-- Reopened earlier → small status note -->
    <template v-else-if="complaint.reopen_count > 0">
      <div class="resolve-note">
        This complaint was reopened {{ complaint.reopen_count }} time{{ complaint.reopen_count > 1 ? 's' : '' }}.
      </div>
    </template>

    <div v-if="error" class="alert alert-error mt-3">{{ error }}</div>

    <!-- Rating modal -->
    <div v-if="showClose" class="modal-overlay" @click.self="showClose = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Rate the resolution</h2>
          <button class="modal-close" @click="showClose = false">&times;</button>
        </div>
        <div class="form-group">
          <label>How satisfied are you?</label>
          <div class="stars-input">
            <span v-for="n in 5" :key="n"
              :class="{ filled: n <= rating }"
              @click="rating = n">&#9733;</span>
          </div>
        </div>
        <div class="form-group">
          <label>Comment (optional)</label>
          <textarea v-model="feedback" class="form-control" placeholder="Tell us about the work done..."></textarea>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showClose = false">Cancel</button>
          <button class="btn btn-success" :disabled="!rating || submitting" @click="submitClose">
            {{ submitting ? 'Saving...' : 'Confirm & Close' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Reopen modal -->
    <div v-if="showReopen" class="modal-overlay" @click.self="showReopen = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Reopen complaint</h2>
          <button class="modal-close" @click="showReopen = false">&times;</button>
        </div>
        <p class="resolve-hint">This will mark the complaint as reopened and notify the department to review it again.</p>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showReopen = false">Cancel</button>
          <button class="btn btn-warning" :disabled="submitting" @click="submitReopen">
            {{ submitting ? 'Reopening...' : 'Reopen' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '../api'

const props = defineProps({ complaint: { type: Object, required: true } })
const emit = defineEmits(['updated'])

const showClose = ref(false)
const showReopen = ref(false)
const rating = ref(0)
const feedback = ref('')
const submitting = ref(false)
const error = ref('')

function openClose() { rating.value = 0; feedback.value = ''; error.value = ''; showClose.value = true }
function openReopen() { error.value = ''; showReopen.value = true }

async function submitClose() {
  submitting.value = true
  error.value = ''
  try {
    const { data } = await api.put(`/requests/${props.complaint.id}/status`, {
      status: 'closed', rating: rating.value, feedback: feedback.value,
    })
    showClose.value = false
    emit('updated', data)
  } catch (e) {
    error.value = e.response?.data?.message || 'Could not close the complaint.'
  } finally {
    submitting.value = false
  }
}

async function submitReopen() {
  submitting.value = true
  error.value = ''
  try {
    const { data } = await api.put(`/requests/${props.complaint.id}/status`, { status: 'reopened' })
    showReopen.value = false
    emit('updated', data)
  } catch (e) {
    error.value = e.response?.data?.message || 'Could not reopen the complaint.'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.resolve-hint { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.85rem; }
.resolve-actions { display: flex; gap: 0.75rem; }
.resolve-note { font-size: 0.82rem; color: #D69AB8; margin-top: 0.6rem; }
.resolve-feedback { font-size: 0.875rem; color: var(--text); font-style: italic; margin-top: 0.4rem; }
.stars-static, .stars-input { display: flex; align-items: center; gap: 0.15rem; font-size: 1.5rem; color: var(--border); }
.stars-static span.filled, .stars-input span.filled { color: var(--secondary); }
.stars-input span { cursor: pointer; transition: color 0.1s; }
.stars-input span:hover { color: #FFC933; }
.rating-num { font-size: 0.85rem; font-weight: 700; color: var(--text); margin-left: 0.5rem; }
</style>
