<template>
  <div class="fab-container">
    <div v-if="isOpen" class="fab-backdrop" @click="toggle"></div>

    <transition name="fab-menu">
      <div v-if="isOpen" class="fab-menu">
        <button
          v-for="(action, index) in actions"
          :key="index"
          :class="['fab-menu-item', `fab-menu-item-${index}`]"
          :title="action.label"
          @click="handleAction(action)"
        >
          <span class="fab-menu-icon">{{ action.icon }}</span>
          <span class="fab-menu-label">{{ action.label }}</span>
        </button>
      </div>
    </transition>

    <button
      :class="['fab-button', { 'fab-open': isOpen }]"
      @click="toggle"
      :title="mainButtonLabel"
    >
      <span class="fab-icon">{{ isOpen ? '✕' : '+' }}</span>
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  actions: {
    type: Array,
    default: () => [
      { icon: '📝', label: 'New Complaint' },
      { icon: '🏛️', label: 'Browse Facilities' }
    ]
  },
  mainButtonLabel: {
    type: String,
    default: 'Quick Actions'
  }
})

const emit = defineEmits(['action'])

const isOpen = ref(false)

const toggle = () => {
  isOpen.value = !isOpen.value
}

const handleAction = (action) => {
  emit('action', action)
  isOpen.value = false
}
</script>

<style scoped>
.fab-container {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}

.fab-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  animation: fadeIn 0.2s ease-out;
  z-index: 990;
}

.fab-menu {
  position: absolute;
  bottom: 70px;
  right: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: slideUp 0.3s ease-out;
}

.fab-menu-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
  transition: all 0.3s ease;
  white-space: nowrap;
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
}

.fab-menu-item:hover {
  transform: translateX(-4px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.16);
}

.fab-menu-icon {
  font-size: 18px;
}

.fab-menu-label {
  min-width: 120px;
  text-align: left;
}

.fab-button {
  position: relative;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
  transition: all 0.3s ease;
  z-index: 1000;
}

.fab-button:hover:not(.fab-open) {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.5);
}

.fab-button:active {
  transform: scale(0.95);
}

.fab-button.fab-open {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 6px 16px rgba(239, 68, 68, 0.4);
}

.fab-icon {
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.fab-menu-enter-active,
.fab-menu-leave-active {
  transition: all 0.3s ease;
}

.fab-menu-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fab-menu-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

@media (max-width: 640px) {
  .fab-container {
    bottom: 16px;
    right: 16px;
  }

  .fab-button {
    width: 48px;
    height: 48px;
    font-size: 24px;
  }

  .fab-menu-label {
    min-width: 100px;
  }

  .fab-menu-item {
    padding: 10px 14px;
    font-size: 13px;
  }
}
</style>
