<template>
  <header class="topbar">
    <div class="topbar-left">
      <span class="live-dot" aria-hidden="true"></span>
      <h2 class="page-title">{{ title }}</h2>
    </div>
  </header>
</template>

<script setup>
// unreadCount is accepted (not used here) only so existing call sites that
// still pass it don't need to change now that notifications live in the
// global top navbar (AppSidebar.vue) instead of this per-page bar.
defineProps({ title: String, unreadCount: { type: Number, default: 0 } })
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  padding: 1.5rem 1.75rem 0;
  flex-shrink: 0;
}
.topbar-left { display: flex; align-items: center; gap: 0.6rem; }
.live-dot {
  width: 7px; height: 7px; border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 0 3px rgba(0,82,255,0.15);
  animation: pulse-dot 2s infinite;
  flex-shrink: 0;
}
.page-title { font-family: var(--font-heading); font-size: 1.15rem; font-weight: 400; color: var(--text); }

@media (max-width: 640px) {
  /* Every page already repeats this title as a bigger <h1> right below —
     on a small screen that duplication costs too much scroll space. */
  .topbar { display: none; }
}
</style>
