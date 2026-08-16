<template>
  <div v-if="open" class="modal-overlay" @click.self="emitClose">
    <div class="modal-panel">
      <button type="button" class="modal-close" aria-label="Close" @click="emitClose">×</button>
      <h2>{{ mode === 'create' ? 'New task' : 'Edit task' }}</h2>
      <form class="field-stack" @submit.prevent="onSubmit">
        <label>
          Title *
          <input v-model="form.title" type="text" required maxlength="200" :disabled="saving" />
        </label>
        <label>
          Assignee
          <select v-model="form.assignee_key" :disabled="saving">
            <option :value="null">Unassigned</option>
            <option v-for="opt in assigneeOptions" :key="opt.key" :value="opt.key">
              {{ assigneeOptionLabel(opt) }}
            </option>
          </select>
        </label>
        <label v-if="showProject">
          Project
          <select v-model="form.project_id" :disabled="saving">
            <option :value="null">No project</option>
            <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
          </select>
        </label>
        <label>
          Due date
          <DatePicker v-model="form.due_date" :disabled="saving" />
        </label>
        <label>
          Status
          <select v-model="form.status" :disabled="saving">
            <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </label>
        <p v-if="error" class="error-line">{{ error }}</p>
        <div class="modal-actions">
          <button type="button" class="btn-outline" :disabled="saving" @click="emitClose">Cancel</button>
          <button type="submit" class="btn-primary" :disabled="saving || !form.title.trim()">
            {{ saving ? 'Saving…' : mode === 'create' ? 'Create task' : 'Save changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

import DatePicker from '@/components/DatePicker.vue'
import { assigneeOptionLabel } from '@/utils/assignee'
import { STATUS_OPTIONS } from '@/utils/ui'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'edit' }, // 'edit' | 'create'
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
  assigneeOptions: { type: Array, default: () => [] },
  projects: { type: Array, default: () => [] },
  showProject: { type: Boolean, default: false },
  initial: {
    type: Object,
    default: () => ({
      title: '',
      assignee_key: null,
      due_date: '',
      status: 'pending',
      project_id: null,
    }),
  },
})

const emit = defineEmits(['close', 'save'])

const form = reactive({
  title: '',
  assignee_key: null,
  due_date: '',
  status: 'pending',
  project_id: null,
})

watch(
  () => [props.open, props.initial],
  () => {
    if (!props.open) return
    const init = props.initial || {}
    form.title = init.title || ''
    form.assignee_key = init.assignee_key ?? null
    form.due_date = init.due_date || ''
    form.status = init.status || 'pending'
    form.project_id = init.project_id ?? null
  },
  { immediate: true, deep: true },
)

function emitClose() {
  emit('close')
}

function onSubmit() {
  if (!form.title.trim()) return
  emit('save', {
    title: form.title.trim(),
    assignee_key: form.assignee_key,
    due_date: form.due_date || null,
    status: form.status || 'pending',
    project_id: form.project_id ?? null,
  })
}
</script>
