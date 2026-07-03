<template>
  <div class="app-layout">
    <AppSidebar />
    <div class="main-content">
      <AppTopbar title="Community Management" />
      <div class="content-area">
        <div class="page-header">
          <div class="page-header-left">
            <p>Monitor and moderate community posts</p>
          </div>
        </div>

        <div class="tabs">
          <button class="tab-btn" :class="{ active: tab === 'all' }" @click="tab = 'all'">All Posts</button>
          <button class="tab-btn" :class="{ active: tab === 'mine' }" @click="tab = 'mine'">My Posts</button>
        </div>

        <div v-if="loading" class="spinner"></div>
        <div v-else class="posts-list">
          <div v-if="!displayPosts.length" class="empty-state">
            <div class="empty-icon">&#9998;</div>
            <p>No posts found</p>
          </div>
          <div v-for="post in displayPosts" :key="post.id" class="post-card card">
            <div class="post-header">
              <div class="post-author-info">
                <div class="avatar avatar-sm">{{ post.author_name?.charAt(0) }}</div>
                <div>
                  <div class="author-name">
                    {{ post.author_name }}
                    <span v-if="post.is_official" class="badge badge-official badge-inline">Official</span>
                    <span v-if="post.author_department" class="dept-tag">{{ post.author_department }}</span>
                  </div>
                  <div class="post-meta">{{ post.location }} &bull; {{ timeAgo(post.created_at) }}</div>
                </div>
              </div>
              <button class="btn btn-xs btn-danger" @click="deletePost(post)">&#128465; Delete</button>
            </div>
            <div v-if="post.title" class="post-title">{{ post.title }}</div>
            <div class="post-content">{{ post.content }}</div>
            <ImageGallery v-if="post.image_urls?.length" :images="post.image_urls" alt="Post image" />

            <div class="post-actions">
              <button class="action-btn" :class="{ liked: post.liked_by_me }" @click="toggleLike(post)">
                &#9829; {{ post.likes_count }}
              </button>
              <button class="action-btn" @click="toggleComments(post)">
                &#9997; {{ post.comments_count }} Comments
              </button>
            </div>

            <div v-if="expandedPost === post.id" class="comments-section">
              <div v-if="!commentData[post.id]" class="spinner p-4"></div>
              <template v-else>
                <div v-for="c in commentData[post.id]" :key="c.id" class="comment-item" :class="{ 'official-comment': c.is_official }">
                  <div class="comment-author">
                    {{ c.author_name }}
                    <span v-if="c.is_official" class="official-tag">{{ c.author_department || 'Admin' }}</span>
                    <button class="comment-delete-btn" title="Delete comment" @click="deleteComment(post, c)">&#x2715;</button>
                  </div>
                  <div class="comment-text">{{ c.content }}</div>
                  <div class="comment-time">{{ timeAgo(c.created_at) }}</div>
                </div>
              </template>
              <div class="comment-input">
                <input v-model="commentTexts[post.id]" class="form-control" placeholder="Reply as admin..." :disabled="postingComment[post.id]" @keydown.enter="addComment(post)" />
                <button class="btn btn-sm btn-primary" :disabled="postingComment[post.id]" @click="addComment(post)">Reply</button>
              </div>
            </div>
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

onMounted(async () => {
  try {
    const res = await api.get('/posts')
    posts.value = res.data
  } catch (e) { console.error(e) } finally { loading.value = false }
})

const displayPosts = computed(() => {
  if (tab.value === 'mine') return posts.value.filter(p => p.citizen_id === auth.user?.id)
  return posts.value
})

async function deletePost(post) {
  if (!confirm('Delete this post?')) return
  try {
    await api.delete(`/posts/${post.id}`)
    posts.value = posts.value.filter(p => p.id !== post.id)
  } catch (e) { alert(e.response?.data?.message || 'Failed to delete') }
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

async function deleteComment(post, comment) {
  if (!confirm('Delete this comment?')) return
  try {
    await api.delete(`/posts/${post.id}/comments/${comment.id}`)
    commentData.value[post.id] = commentData.value[post.id].filter(c => c.id !== comment.id)
    post.comments_count--
  } catch (e) {
    alert(e.response?.data?.message || 'Failed to delete comment')
  }
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
.posts-list { display: flex; flex-direction: column; gap: 1rem; max-width: 760px; }
.post-card { padding: 1.1rem 1.25rem; }
.post-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; }
.post-author-info { display: flex; align-items: flex-start; gap: 0.6rem; }
.author-name { font-size: 0.85rem; font-weight: 700; color: #5C1A41; display: flex; align-items: center; flex-wrap: wrap; gap: 0.25rem; }
.dept-tag { font-size: 0.7rem; color: #B0708F; background: #FFE9F2; padding: 0.1rem 0.35rem; border-radius: 100px; }
.post-meta { font-size: 0.75rem; color: #D69AB8; }
.post-title { font-size: 0.9rem; font-weight: 700; color: #5C1A41; margin-bottom: 0.4rem; }
.post-content { font-size: 0.875rem; color: #5C1A41; line-height: 1.6; margin-bottom: 0.75rem; }
.post-actions { display: flex; gap: 1rem; padding-top: 0.65rem; border-top: 1px solid #FFE9F2; }
.action-btn { background: none; border: none; font-size: 0.8rem; color: #B0708F; cursor: pointer; padding: 0.2rem 0.4rem; border-radius: 5px; }
.action-btn:hover { background: #FFE9F2; }
.action-btn.liked { color: #FF2D6F; }
.comments-section { margin-top: 0.85rem; padding-top: 0.85rem; border-top: 1px solid #FFD1E6; }
.comment-item { padding: 0.5rem 0; border-bottom: 1px solid #FFE9F2; }
.comment-item.official-comment { background: #DFF7EC; border-radius: 6px; padding: 0.5rem 0.75rem; margin-bottom: 0.35rem; }
.comment-author { font-size: 0.78rem; font-weight: 700; color: #5C1A41; display: flex; align-items: center; gap: 0.35rem; }
.official-tag { font-size: 0.65rem; background: #0E7A4F; color: #fff; padding: 0.1rem 0.35rem; border-radius: 100px; }
.comment-text { font-size: 0.82rem; color: #5C1A41; margin-top: 0.15rem; }
.comment-time { font-size: 0.7rem; color: #D69AB8; margin-top: 0.1rem; }
.comment-delete-btn { background: none; border: none; color: #D69AB8; font-size: 0.7rem; cursor: pointer; margin-left: 0.4rem; padding: 0 0.2rem; }
.comment-delete-btn:hover { color: #E0218A; }
.comment-input { display: flex; gap: 0.5rem; margin-top: 0.75rem; }
.badge-count { background: #FF2D6F; color: #fff; border-radius: 50%; padding: 0.05rem 0.3rem; font-size: 0.65rem; margin-left: 0.25rem; }
.btn-xs { padding: 0.22rem 0.6rem; font-size: 0.72rem; border-radius: 4px; font-weight: 600; border: none; cursor: pointer; }
.badge-inline { font-size: 0.6rem; margin-left: 0.35rem; }
</style>
