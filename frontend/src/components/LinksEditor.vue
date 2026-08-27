<template>
  <div class="links-editor">
    <div class="links-editor__header">
      <label class="links-editor__label">
        <Link2 :size="14" :stroke-width="1.75" />
        {{ label }}
      </label>
      <button type="button" class="links-editor__add" :disabled="disabled" @click="addRow">
        <Plus :size="14" :stroke-width="2" />
        Add link
      </button>
    </div>

    <p v-if="!rows.length" class="links-editor__hint">Optional — add reference links for this item.</p>

    <ul v-else class="links-editor__list">
      <li v-for="(row, index) in rows" :key="index" class="links-editor__row">
        <input
          v-model="row.label"
          type="text"
          class="links-editor__input"
          placeholder="Label (e.g. Q3 Report)"
          maxlength="200"
          :disabled="disabled"
          @input="emitChange"
        />
        <input
          v-model="row.url"
          type="text"
          class="links-editor__input links-editor__input--url"
          placeholder="skao.com, www.example.com, or folder name"
          maxlength="2000"
          :disabled="disabled"
          @input="emitChange"
        />
        <button
          type="button"
          class="links-editor__remove"
          aria-label="Remove link"
          :disabled="disabled"
          @click="removeRow(index)"
        >
          <X :size="15" :stroke-width="1.75" />
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { Link2, Plus, X } from '@lucide/vue'
import { nextTick, ref, watch } from 'vue'

import { emptyLinkRow } from '@/utils/links'

const props = defineProps({
  modelValue: { type: Array, default: () => [] },
  label: { type: String, default: 'Links' },
  disabled: { type: Boolean, default: false },
})

const emit = defineEmits(['update:modelValue'])

const rows = ref([])
let syncing = false

function rowsFromValue(val) {
  if (!Array.isArray(val) || !val.length) return []
  return val.map((l) => ({ label: l.label || '', url: l.url || '' }))
}

watch(
  () => props.modelValue,
  (val) => {
    if (syncing) return
    rows.value = rowsFromValue(val)
  },
  { immediate: true, deep: true },
)

function emitChange() {
  syncing = true
  emit(
    'update:modelValue',
    rows.value.map((r) => ({ label: r.label, url: r.url })),
  )
  nextTick(() => {
    syncing = false
  })
}

function addRow() {
  rows.value = [...rows.value, emptyLinkRow()]
}

function removeRow(index) {
  rows.value = rows.value.filter((_, i) => i !== index)
  emitChange()
}
</script>

<style scoped>
.links-editor {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.links-editor__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.links-editor__label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.links-editor__add {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  font-family: var(--font-body);
  font-size: 0.76rem;
  font-weight: 600;
  padding: 0.3rem 0.55rem;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.links-editor__add:hover:not(:disabled) {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.links-editor__add:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.links-editor__hint {
  margin: 0;
  font-size: 0.8rem;
  color: var(--color-text-muted);
}

.links-editor__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.links-editor__row {
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.4fr) auto;
  gap: 0.4rem;
  align-items: center;
}

.links-editor__input {
  width: 100%;
  font-family: var(--font-body);
  font-size: 0.88rem;
  padding: 0.5rem 0.6rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
}

.links-editor__input:focus {
  outline: none;
  border-color: rgba(196, 163, 90, 0.55);
}

.links-editor__remove {
  width: 32px;
  height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.links-editor__remove:hover:not(:disabled) {
  border-color: var(--color-danger);
  color: var(--color-danger);
}

@media (max-width: 520px) {
  .links-editor__row {
    grid-template-columns: 1fr auto;
    grid-template-rows: auto auto;
  }

  .links-editor__input--url {
    grid-column: 1 / -1;
  }
}
</style>
