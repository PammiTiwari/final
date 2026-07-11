<template>
  <div class="empty-state">
    <div class="empty-illustration">
      <svg v-if="type === 'complaints'" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="#f3f4f6"/>
        <path d="M 60 80 Q 100 120 140 80" stroke="#9ca3af" stroke-width="3" fill="none" stroke-linecap="round"/>
        <circle cx="75" cy="70" r="4" fill="#9ca3af"/>
        <circle cx="125" cy="70" r="4" fill="#9ca3af"/>
      </svg>

      <svg v-else-if="type === 'bookings'" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <rect x="50" y="40" width="100" height="120" rx="8" stroke="#9ca3af" stroke-width="2" fill="none"/>
        <line x1="50" y1="70" x2="150" y2="70" stroke="#9ca3af" stroke-width="2"/>
        <circle cx="65" cy="55" r="3" fill="#9ca3af"/>
        <circle cx="135" cy="55" r="3" fill="#9ca3af"/>
        <line x1="65" y1="90" x2="135" y2="90" stroke="#9ca3af" stroke-width="2" stroke-dasharray="4"/>
      </svg>

      <svg v-else-if="type === 'payments'" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <rect x="40" y="60" width="120" height="80" rx="8" stroke="#9ca3af" stroke-width="2" fill="none"/>
        <circle cx="100" cy="100" r="15" stroke="#9ca3af" stroke-width="2" fill="none"/>
        <line x1="100" y1="85" x2="100" y2="115" stroke="#9ca3af" stroke-width="2"/>
        <line x1="50" y1="75" x2="70" y2="75" stroke="#9ca3af" stroke-width="1.5"/>
      </svg>

      <svg v-else-if="type === 'search'" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="75" cy="75" r="35" stroke="#9ca3af" stroke-width="2" fill="none"/>
        <line x1="105" y1="105" x2="145" y2="145" stroke="#9ca3af" stroke-width="2" stroke-linecap="round"/>
        <line x1="60" y1="75" x2="90" y2="75" stroke="#9ca3af" stroke-width="1.5" stroke-dasharray="3"/>
      </svg>

      <svg v-else viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
        <circle cx="100" cy="100" r="80" fill="#f3f4f6"/>
        <text x="100" y="105" text-anchor="middle" font-size="60" fill="#9ca3af">?</text>
      </svg>
    </div>

    <h3 class="empty-title">{{ title }}</h3>
    <p class="empty-description">{{ description }}</p>

    <button v-if="buttonText" @click="$emit('action')" class="empty-button">
      {{ buttonText }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  type: {
    type: String,
    default: 'complaints',
    validator: (value) => ['complaints', 'bookings', 'payments', 'search', 'default'].includes(value)
  },
  title: {
    type: String,
    default: 'No data found'
  },
  description: {
    type: String,
    default: 'There is nothing here yet. Try again later.'
  },
  buttonText: {
    type: String,
    default: ''
  }
})

defineEmits(['action'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  min-height: 400px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  border-radius: 12px;
}

.empty-illustration {
  width: 120px;
  height: 120px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-illustration svg {
  width: 100%;
  height: 100%;
}

.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 12px 0;
}

.empty-description {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 24px 0;
  max-width: 300px;
  line-height: 1.5;
}

.empty-button {
  padding: 10px 24px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.empty-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.empty-button:active {
  transform: translateY(0);
}

@media (max-width: 640px) {
  .empty-state {
    padding: 40px 16px;
    min-height: 300px;
  }

  .empty-title {
    font-size: 18px;
  }

  .empty-description {
    font-size: 13px;
  }
}
</style>
