<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Announcements" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <h1>Announcements</h1>
            <p>Official notices and updates from city administration</p>
          </div>
          <button v-if="auth.isAdmin" class="btn btn-primary" @click="showCreateAnn = true">+ Post Announcement</button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="announcements-list">
          <div v-if="!posts.length" class="empty-state">
            <div class="empty-icon">&#9993;</div>
            <p>No announcements at this time</p>
          </div>
          <div v-for="post in posts" :key="post.id" class="announcement-card card">
            <div class="ann-icon">&#9993;</div>
            <div class="ann-body">
              <div class="ann-header">
                <h3 class="ann-title">{{ post.title || 'Official Announcement' }}</h3>
                <span class="badge badge-official">Official</span>
                <button v-if="auth.isAdmin" class="ann-delete-btn" title="Delete announcement" @click="deleteAnnouncement(post)">&#128465;</button>
              </div>
              <p class="ann-content">{{ post.content }}</p>
              <ImageGallery v-if="post.image_urls?.length" :images="post.image_urls" alt="Announcement image" />
              <div class="ann-footer">
                <span class="ann-location" v-if="post.location">&#9679; {{ post.location }}</span>
                <span class="ann-date">{{ fmtDate(post.created_at) }}</span>
                <span class="ann-by">By Preetam Nagar Admin</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Announcement Modal (admin only) -->
    <div v-if="showCreateAnn" class="modal-overlay" @click.self="showCreateAnn = false">
      <div class="modal">
        <div class="modal-header">
          <h2>Post Official Announcement</h2>
          <button class="modal-close" @click="showCreateAnn = false">&#x2715;</button>
        </div>
        <div v-if="annError" class="alert alert-error">{{ annError }}</div>
        <div class="form-group">
          <label>Title</label>
          <input v-model="annForm.title" class="form-control" placeholder="Announcement title" />
        </div>
        <div class="form-group">
          <label>Content</label>
          <textarea v-model="annForm.content" class="form-control" rows="4" placeholder="Write announcement content..."></textarea>
        </div>
        <div class="form-group">
          <label>Location / Area</label>
          <input v-model="annForm.location" class="form-control" placeholder="e.g. All Wards, Ward-1, etc." />
        </div>
        <div class="form-group">
          <label>Photos <span class="optional-label">(optional)</span></label>
          <MultiImageUpload v-model="annForm.image_urls" :max="3" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showCreateAnn = false">Cancel</button>
          <button class="btn btn-primary" @click="createAnnouncement" :disabled="annPosting">
            {{ annPosting ? 'Posting...' : 'Post Announcement' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppSidebar from '../components/AppSidebar.vue'
import AppTopbar from '../components/AppTopbar.vue'
import ImageGallery from '../components/ImageGallery.vue'
import MultiImageUpload from '../components/MultiImageUpload.vue'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const loading = ref(true)
const posts = ref([])
const showCreateAnn = ref(false)
const annForm = ref({ title: '', content: '', location: '', image_urls: [] })
const annPosting = ref(false)
const annError = ref('')

onMounted(async () => {
  await loadAnnouncements()
})

async function loadAnnouncements() {
  loading.value = true
  try {
    const res = await api.get('/posts?category=announcement')
    posts.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function createAnnouncement() {
  if (annPosting.value) return
  if (!annForm.value.content.trim()) { annError.value = 'Content required'; return }
  annPosting.value = true
  annError.value = ''
  try {
    const res = await api.post('/posts', {
      title: annForm.value.title,
      content: annForm.value.content,
      location: annForm.value.location,
      image_urls: annForm.value.image_urls,
      category: 'announcement',
    })
    posts.value.unshift(res.data)
    showCreateAnn.value = false
    annForm.value = { title: '', content: '', location: '', image_urls: [] }
  } catch (e) {
    annError.value = e.response?.data?.message || 'Failed to post'
  } finally {
    annPosting.value = false
  }
}

async function deleteAnnouncement(post) {
  if (!confirm('Delete this announcement?')) return
  try {
    await api.delete(`/posts/${post.id}`)
    posts.value = posts.value.filter(p => p.id !== post.id)
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to delete')
  }
}

function fmtDate(d) {
  return new Date(d).toLocaleDateString('en-IN', { day: '2-digit', month: 'long', year: 'numeric' })
}
</script>

<style scoped>
.announcements-list { display: flex; flex-direction: column; gap: 1rem; max-width: 760px; }
.announcement-card { display: flex; gap: 1rem; align-items: flex-start; padding: 1.25rem 1.5rem; }
.ann-icon {
  width: 40px; height: 40px; background: #D7F5E5; color: #0E7A4F;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-size: 1.1rem; flex-shrink: 0;
}
.ann-body { flex: 1; }
.ann-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem; }
.ann-title { font-size: 0.95rem; font-weight: 700; color: #5C1A41; }
.ann-delete-btn { margin-left: auto; background: none; border: none; font-size: 0.85rem; color: #D69AB8; cursor: pointer; padding: 0.2rem 0.4rem; border-radius: 5px; flex-shrink: 0; }
.ann-delete-btn:hover { background: #FFE9F2; color: #FF2D6F; }
.ann-content { font-size: 0.875rem; color: #9B2C6F; line-height: 1.65; margin-bottom: 0.75rem; }
.ann-footer { display: flex; gap: 1rem; align-items: center; flex-wrap: wrap; }
.ann-location { font-size: 0.78rem; color: #B0708F; }
.ann-date { font-size: 0.75rem; color: #D69AB8; }
.ann-by { font-size: 0.75rem; font-weight: 600; color: #9B2C6F; background: #FFE9F2; padding: 0.1rem 0.5rem; border-radius: 100px; }
.optional-label { font-weight: 400; color: #D69AB8; }
</style>
