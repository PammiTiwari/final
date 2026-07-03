<template>
  <div class="multi-image-upload">
    <!-- Empty state: one large dropzone, not a tiny tile lost in the modal -->
    <div v-if="!photos.length" class="dropzone" :class="{ disabled: uploading }" @click="!uploading && fileInput.click()">
      <span v-if="uploading" class="add-spinner"></span>
      <template v-else>
        <span class="dz-icon">&#128247;</span>
        <p class="dz-title">Add photo</p>
        <p class="dz-hint">Click to select from your device</p>
      </template>
    </div>

    <!-- Once photos exist: compact thumbnail row + small add-more tile -->
    <div v-else class="thumbs">
      <div v-for="(url, i) in photos" :key="url" class="thumb">
        <img :src="url" alt="Uploaded photo" />
        <button type="button" class="thumb-remove" @click="removeAt(i)">&#x2715;</button>
      </div>
      <div v-if="photos.length < max" class="add-tile" :class="{ disabled: uploading }" @click="!uploading && fileInput.click()">
        <span v-if="uploading" class="add-spinner"></span>
        <template v-else>
          <span class="add-icon">+</span>
          <span class="add-label">Add more</span>
        </template>
      </div>
    </div>

    <input ref="fileInput" type="file" accept="image/*" multiple class="hidden" @change="handleFiles" />
    <p class="hint">{{ photos.length }}/{{ max }} photos &bull; JPG, PNG up to 5MB each</p>
    <p v-if="error" class="upload-err">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '../api'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  max: { type: Number, default: 3 },
})
const emit = defineEmits(['update:modelValue'])

const photos = computed(() => props.modelValue || [])

const MAX_SIZE = 5 * 1024 * 1024

const uploading = ref(false)
const error = ref('')
const fileInput = ref(null)

async function handleFiles(e) {
  if (uploading.value) return
  const files = Array.from(e.target.files || [])
  if (!files.length) return
  error.value = ''

  const oversized = files.filter(f => f.size > MAX_SIZE)
  const validFiles = files.filter(f => f.size <= MAX_SIZE)

  const remaining = props.max - photos.value.length
  const toUpload = validFiles.slice(0, remaining)

  const errors = []
  if (oversized.length) {
    errors.push(`${oversized.map(f => f.name).join(', ')} — over 5MB, please choose a smaller photo.`)
  }
  if (validFiles.length > remaining) {
    errors.push(`You can add up to ${props.max} photos only.`)
  }
  error.value = errors.join(' ')

  if (!toUpload.length) return

  uploading.value = true
  try {
    const urls = []
    for (const file of toUpload) {
      const fd = new FormData()
      fd.append('file', file)
      const res = await api.post('/upload', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      urls.push(res.data.url)
    }
    emit('update:modelValue', [...photos.value, ...urls])
  } catch (err) {
    error.value = err.response?.data?.message || 'Image upload failed. Try again.'
  } finally {
    uploading.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

function removeAt(i) {
  const next = [...photos.value]
  next.splice(i, 1)
  emit('update:modelValue', next)
}
</script>

<style scoped>
.dropzone {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 0.4rem; min-height: 220px; border: 2px dashed #FFD1E6; border-radius: 10px;
  background: #FFF0F6; cursor: pointer; text-align: center; transition: border-color 0.15s, background 0.15s;
}
.dropzone:hover { border-color: #D69AB8; background: #FFE0EE; }
.dropzone.disabled { cursor: default; }
.dz-icon { font-size: 2.4rem; margin-bottom: 0.3rem; }
.dz-title { font-size: 0.95rem; font-weight: 600; color: #5C1A41; }
.dz-hint { font-size: 0.8rem; color: #B0708F; margin-top: 0.2rem; }

.thumbs { display: flex; flex-wrap: wrap; gap: 0.6rem; }
.thumb, .add-tile {
  width: 84px; height: 84px; border-radius: 8px; position: relative;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
}
.thumb { overflow: hidden; border: 1px solid #FFD1E6; }
.thumb img { width: 100%; height: 100%; object-fit: cover; display: block; }
.thumb-remove {
  position: absolute; top: 4px; right: 4px; width: 20px; height: 20px; border-radius: 50%;
  border: none; background: rgba(0,0,0,0.6); color: #fff; font-size: 0.65rem; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
}
.add-tile {
  flex-direction: column; gap: 0.2rem; border: 2px dashed #FFD1E6; background: #FFF0F6;
  cursor: pointer; transition: 0.15s;
}
.add-tile:hover { border-color: #D69AB8; }
.add-tile.disabled { cursor: default; }
.add-icon { font-size: 1.4rem; color: #E0218A; line-height: 1; }
.add-label { font-size: 0.62rem; color: #B0708F; text-align: center; padding: 0 0.2rem; }
.add-spinner {
  width: 20px; height: 20px; border-radius: 50%; border: 2px solid #FFD1E6;
  border-top-color: #E0218A; animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.hint { font-size: 0.72rem; color: #D69AB8; margin-top: 0.5rem; }
.upload-err { font-size: 0.78rem; color: #FF2D6F; margin-top: 0.3rem; }
.hidden { display: none; }
</style>
