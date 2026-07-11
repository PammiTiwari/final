<template>
  <div class="progress-container">
    <div class="progress-bar">
      <div class="progress-fill" :style="{ width: progressPercentage + '%' }"></div>
    </div>

    <div class="progress-steps">
      <div
        v-for="(step, index) in steps"
        :key="index"
        :class="['step', { active: index === currentStep, completed: index < currentStep }]"
        @click="$emit('step-click', index)"
      >
        <div class="step-number">
          <span v-if="index < currentStep" class="check-icon">✓</span>
          <span v-else>{{ index + 1 }}</span>
        </div>
        <div class="step-label">{{ step }}</div>
      </div>
    </div>

    <div class="progress-info">
      <span class="step-counter">Step {{ currentStep + 1 }} of {{ steps.length }}</span>
      <span class="progress-percentage">{{ progressPercentage }}%</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  steps: {
    type: Array,
    required: true,
    default: () => ['Details', 'Category', 'Photos', 'Review', 'Submit']
  },
  currentStep: {
    type: Number,
    default: 0
  }
})

defineEmits(['step-click'])

const progressPercentage = computed(() => {
  return Math.round(((props.currentStep + 1) / props.steps.length) * 100)
})
</script>

<style scoped>
.progress-container {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 20px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
  box-shadow: 0 0 8px rgba(59, 130, 246, 0.4);
}

.progress-steps {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 16px;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
  cursor: pointer;
  transition: all 0.3s ease;
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #e5e7eb;
  color: #6b7280;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.3s ease;
}

.step.active .step-number {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  transform: scale(1.1);
}

.step.completed .step-number {
  background: #10b981;
  color: white;
}

.check-icon {
  font-weight: bold;
}

.step-label {
  font-size: 12px;
  font-weight: 500;
  color: #9ca3af;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.step.active .step-label {
  color: #3b82f6;
  font-weight: 600;
}

.step.completed .step-label {
  color: #10b981;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6b7280;
}

.step-counter {
  font-weight: 500;
}

.progress-percentage {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-weight: 600;
}

@media (max-width: 640px) {
  .progress-container {
    padding: 16px;
    margin-bottom: 16px;
  }

  .step-label {
    font-size: 10px;
  }

  .progress-steps {
    gap: 4px;
  }

  .step-number {
    width: 28px;
    height: 28px;
    font-size: 12px;
  }
}
</style>
