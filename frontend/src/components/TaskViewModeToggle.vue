<template>
  <div class="view-mode-toggle" role="group" aria-label="Task view mode">
    <button
      type="button"
      class="view-mode-btn"
      :class="{ 'view-mode-btn--active': modelValue === 'kanban' }"
      :aria-pressed="modelValue === 'kanban'"
      @click="$emit('update:modelValue', 'kanban')"
    >
      <Columns3 :size="15" :stroke-width="1.75" />
      Board
    </button>
    <button
      type="button"
      class="view-mode-btn"
      :class="{ 'view-mode-btn--active': modelValue === 'list' }"
      :aria-pressed="modelValue === 'list'"
      @click="$emit('update:modelValue', 'list')"
    >
      <List :size="15" :stroke-width="1.75" />
      List
    </button>
  </div>
</template>

<script setup>
import { Columns3, List } from '@lucide/vue'

defineProps({
  modelValue: { type: String, required: true },
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.view-mode-toggle {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  background: rgba(0, 0, 0, 0.15);
}

.view-mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.7rem;
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--color-text-muted);
  background: transparent;
  border: none;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
}

.view-mode-btn:hover {
  color: var(--color-text);
  background: rgba(196, 163, 90, 0.08);
}

.view-mode-btn--active {
  color: var(--color-text);
  background: rgba(196, 163, 90, 0.14);
}
</style>
