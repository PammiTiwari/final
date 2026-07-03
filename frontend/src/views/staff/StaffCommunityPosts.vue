<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Community Posts" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Monitor and respond to citizen posts in your department</p>
          </div>
          <button class="btn btn-primary" @click="openCreate">+ Create Post</button>
        </div>

        <div class="tabs">
          <button class="tab-btn" :class="{ active: tab === 'all' }" @click="tab = 'all'">All Posts</button>
          <button class="tab-btn" :class="{ active: tab === 'mine' }" @click="tab = 'mine'">My Posts</button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="posts-list">
          <div v-if="!filteredPosts.length" class="empty-state">
            <div class="empty-icon">&#9998;</div>
            <p>No posts found</p>
          </div>
          <div v-for="post in filteredPosts" :key="post.id" class="post-card card">
            <div class="post-header">
              <div class="post-author">
                <div class="avatar avatar-sm">{{ post.author_name?.charAt(0) }}</div>
                <div>
                  <div class="author-name">
                    {{ post.author_name }}
                    <span v-if="post.is_official" class="badge badge-official badge-inline">Official</span>
                    <span v-if="post.author_department" class="dept-tag">{{ post.author_department }}</span>
                  </div>
                  <div class="post-meta">
                    <span v-if="post.location">{{ post.location }}</span>
                    <span> &bull; {{ timeAgo(post.created_at) }}</span>
                  </div>
                </div>
              </div>
              <button v-if="post.citizen_id === auth.user?.id" class="post-delete-btn" title="Delete post" @click="deletePost(post)">&#128465;</button>
            </div>
            <div v-if="post.title" class="post-title">{{ post.title }}</div>
            <div class="post-content">{{ post.content }}</div>
            <ImageGallery v-if="post.image_urls?.length" :images="post.image_urls" alt="Post image" />
            <div class="post-actions">
              <button class="action-btn" :class="{ liked: post.liked_by_me }" @click="toggleLike(post)">&#9829; {{ post.likes_count }}</button>
              <button class="action-btn" @click="toggleComments(post)">&#9997; {{ post.comments_count }} Comments</button>
            </div>

            <div v-if="expandedPost === post.id" class="comments-section">
              <div v-if="!commentData[post.id]" class="spinner p-4"></div>
              <template v-else>
                <div v-for="c in commentData[post.id]" :key="c.id" class="comment-item" :class="{ 'official-comment': c.is_official }">
                  <div class="comment-author">
                    {{ c.author_name }}
                    <span v-if="c.is_official" class="official-tag">{{ c.author_department || 'Official' }}</span>
                  </div>
                  <div class="comment-text">{{ c.content }}</div>
                  <div class="comment-time">{{ timeAgo(c.created_at) }}</div>
                </div>
              </template>
              <div class="comment-input">
                <input v-model="commentTexts[post.id]" class="form-control"
                       placeholder="Add official department response..."
                       :disabled="postingComment[post.id]"
                       @keydown.enter="addComment(post)" />
                <button class="btn btn-sm btn-primary" :disabled="postingComment[post.id]" @click="addComment(post)">Respond</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Post Modal -->
    <div v-if="showCreatePost" class="modal-overlay" @click.self="closeCreate">
      <div class="modal create-modal">
        <div class="create-header">
          <button class="create-nav" @click="closeCreate" aria-label="Close">&#x2715;</button>
          <h2>Create new post</h2>
          <button class="create-action" :disabled="!newPost.content.trim() || postLoading" @click="createPost">
            {{ postLoading ? 'Sharing…' : 'Share' }}
          </button>
        </div>

        <div class="create-body">
          <div class="form-group">
            <label>Caption</label>
            <textarea v-model="newPost.content" class="form-control" rows="4" placeholder="Share an update with your community…"></textarea>
          </div>
          <div class="form-group">
            <label>Location</label>
            <input v-model="newPost.location" class="form-control" placeholder="e.g. Ward-3, Preetam Nagar" />
          </div>
          <div class="form-group">
            <label>Pin location on map <span class="optional-label">(optional)</span></label>
            <LocationPicker @located="onPostLocated" />
          </div>
          <div class="form-group">
            <label>Photos <span class="optional-label">(optional)</span></label>
            <MultiImageUpload v-model="newPost.image_urls" :max="3" />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppSidebar from '../../components/AppSidebar.vue'
import AppTopbar from '../../components/AppTopbar.vue'
import ImageGallery from '../../components/ImageGallery.vue'
import MultiImageUpload from '../../components/MultiImageUpload.vue'
import LocationPicker from '../../components/LocationPicker.vue'
import { useAuthStore } from '../../stores/auth'
import api from '../../api'

const auth = useAuthStore()
const loading = ref(true)
const posts = ref([])
const tab = ref('all')
const expandedPost = ref(null)
const commentData = ref({})
const commentTexts = ref({})
const postingComment = ref({})
const showCreatePost = ref(false)
const newPost = ref({ content: '', location: '', image_urls: [] })
const postLoading = ref(false)

onMounted(async () => {
  try {
    const res = await api.get('/posts')
    posts.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})

const filteredPosts = computed(() => {
  if (tab.value === 'mine') return posts.value.filter(p => p.citizen_id === auth.user?.id)
  return posts.value
})

function openCreate() {
  resetCreate()
  showCreatePost.value = true
}

function closeCreate() {
  showCreatePost.value = false
  resetCreate()
}

function resetCreate() {
  newPost.value = { content: '', location: '', image_urls: [] }
}

function onPostLocated({ address, lat, lng }) {
  // Fill the location box from the map pin, unless the user already typed one.
  if (!newPost.value.location) newPost.value.location = address || `${lat}, ${lng}`
}

async function deletePost(post) {
  if (!confirm('Delete this post?')) return
  try {
    await api.delete(`/posts/${post.id}`)
    posts.value = posts.value.filter(p => p.id !== post.id)
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to delete post')
  }
}

async function toggleLike(post) {
  try {
    const res = await api.post(`/posts/${post.id}/like`)
    post.liked_by_me = res.data.liked
    post.likes_count += res.data.liked ? 1 : -1
  } catch (e) { console.error(e) }
}

async function toggleComments(post) {
  if (expandedPost.value === post.id) { expandedPost.value = null; return }
  expandedPost.value = post.id
  if (!commentData.value[post.id]) {
    try {
      const res = await api.get(`/posts/${post.id}/comments`)
      commentData.value[post.id] = res.data
    } catch (e) { commentData.value[post.id] = [] }
  }
}

async function addComment(post) {
  if (postingComment.value[post.id]) return
  const text = commentTexts.value[post.id]?.trim()
  if (!text) return
  postingComment.value[post.id] = true
  commentTexts.value[post.id] = ''
  try {
    const res = await api.post(`/posts/${post.id}/comments`, { content: text })
    if (!commentData.value[post.id]) commentData.value[post.id] = []
    commentData.value[post.id].push(res.data)
    post.comments_count++
  } catch (e) {
    console.error(e)
    commentTexts.value[post.id] = text
  } finally {
    postingComment.value[post.id] = false
  }
}

async function createPost() {
  if (!newPost.value.content.trim() || postLoading.value) return
  postLoading.value = true
  try {
    const res = await api.post('/posts', {
      content: newPost.value.content,
      location: newPost.value.location,
      image_urls: newPost.value.image_urls,
      category: 'general',
    })
    posts.value.unshift(res.data)
    closeCreate()
  } catch (e) { console.error(e) } finally { postLoading.value = false }
}

function timeAgo(d) {
  const diff = (Date.now() - new Date(d)) / 1000
  if (diff < 60) return 'just now'
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}
</script>

<style scoped>
.posts-list { display: flex; flex-direction: column; gap: 1rem; max-width: 700px; }
.post-card { padding: 1.1rem 1.25rem; }
.post-header { display: flex; justify-content: space-between; gap: 0.75rem; align-items: flex-start; margin-bottom: 0.75rem; }
.post-delete-btn { background: none; border: none; font-size: 0.85rem; color: #D69AB8; cursor: pointer; padding: 0.2rem 0.4rem; border-radius: 5px; flex-shrink: 0; }
.post-delete-btn:hover { background: #FFE9F2; color: #FF2D6F; }
.post-author { display: flex; align-items: flex-start; gap: 0.6rem; }
.author-name { font-size: 0.85rem; font-weight: 700; color: #5C1A41; display: flex; align-items: center; flex-wrap: wrap; gap: 0.25rem; }
.dept-tag { font-size: 0.7rem; color: #B0708F; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 100px; }
.post-meta { font-size: 0.75rem; color: #D69AB8; margin-top: 0.1rem; }
.post-title { font-size: 0.9rem; font-weight: 700; color: #5C1A41; margin-bottom: 0.4rem; }
.post-content { font-size: 0.875rem; color: #5C1A41; line-height: 1.65; margin-bottom: 0.85rem; }
.post-img { width: 100%; max-height: 280px; object-fit: cover; border-radius: 8px; margin-bottom: 0.85rem; border: 1px solid #FFD1E6; display: block; }
.post-actions { display: flex; gap: 1rem; padding-top: 0.65rem; border-top: 1px solid #FFE9F2; }
.action-btn { background: none; border: none; font-size: 0.8rem; color: #B0708F; cursor: pointer; padding: 0.2rem 0.4rem; border-radius: 5px; }
.action-btn:hover { background: #FFE9F2; }
.action-btn.liked { color: #FF2D6F; }
.comments-section { margin-top: 0.85rem; padding-top: 0.85rem; border-top: 1px solid #FFD1E6; }
.comment-item { padding: 0.5rem 0; border-bottom: 1px solid #FFE9F2; }
.comment-item.official-comment { background: #DFF7EC; border-radius: 6px; padding: 0.5rem 0.75rem; margin-bottom: 0.35rem; }
.comment-author { font-size: 0.78rem; font-weight: 700; color: #5C1A41; display: flex; align-items: center; gap: 0.35rem; }
.official-tag { font-size: 0.65rem; background: #5C1A41; color: #fff; padding: 0.1rem 0.35rem; border-radius: 100px; }
.comment-text { font-size: 0.82rem; color: #5C1A41; margin-top: 0.15rem; }
.comment-time { font-size: 0.7rem; color: #D69AB8; margin-top: 0.1rem; }
.comment-input { display: flex; gap: 0.5rem; margin-top: 0.75rem; }

.badge-inline { margin-left: 0.4rem; font-size: 0.6rem; }

/* Instagram-style create-post modal — same pattern as the citizen feed */
.create-modal { width: 460px; max-width: 92vw; padding: 0; overflow: hidden; display: flex; flex-direction: column; }
.create-header { display: flex; align-items: center; justify-content: space-between; padding: 0.6rem 0.85rem; border-bottom: 1px solid #FFD1E6; }
.create-header h2 { font-size: 0.95rem; font-weight: 700; margin: 0; color: #5C1A41; }
.create-nav { background: none; border: none; font-size: 1.1rem; color: #5C1A41; cursor: pointer; padding: 0.15rem 0.35rem; line-height: 1; }
.create-action { background: none; border: none; color: #E0218A; font-size: 0.85rem; font-weight: 700; cursor: pointer; padding: 0.15rem 0.35rem; }
.create-action:disabled { color: #FFD1E6; cursor: default; }
.create-body { padding: 1rem; overflow-y: auto; }
.optional-label { font-weight: 400; color: #D69AB8; }
</style>
