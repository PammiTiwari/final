<template>
  <div v-if="images.length" class="image-gallery" :class="`count-${Math.min(images.length, 3)}`">
    <img v-for="url in images.slice(0, 3)" :key="url" :src="url" :alt="alt" />
  </div>
</template>

<script setup>
defineProps({
  images: { type: Array, default: () => [] },
  alt: { type: String, default: 'Photo' },
})
</script>

<style scoped>
.image-gallery {
  display: grid;
  gap: 6px;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 0.85rem;
  border: 1px solid #FFD1E6;
}
.image-gallery img {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
}

/* Single photo: natural landscape frame, capped so it never dominates the card. */
.image-gallery.count-1 { grid-template-columns: 1fr; }
.image-gallery.count-1 img { aspect-ratio: 4 / 3; max-height: 320px; }

/* Two photos: equal side-by-side squares — simplest layout, nothing to misalign. */
.image-gallery.count-2 { grid-template-columns: 1fr 1fr; }
.image-gallery.count-2 img { aspect-ratio: 1 / 1; }

/* Three photos: equal row of squares (like a standard photo-grid), not a
   stacked/spanning layout — avoids any row-span sizing edge cases. */
.image-gallery.count-3 { grid-template-columns: repeat(3, 1fr); }
.image-gallery.count-3 img { aspect-ratio: 1 / 1; }
</style>
