<template>
  <Teleport to="body">
    <Transition name="drawer">
      <div v-if="open" class="task-drawer-overlay" @click.self="emitClose">
        <aside class="task-drawer" role="dialog" aria-modal="true" :aria-label="panelTitle">
          <div class="task-drawer__accent" :data-s="form.status" />

          <header class="task-drawer__header">
            <div class="task-drawer__header-text">
              <p class="task-drawer__eyebrow">{{ mode === 'create' ? 'New task' : 'Task details' }}</p>
              <h2 class="task-drawer__title">{{ panelTitle }}</h2>
            </div>
            <button type="button" class="task-drawer__close" aria-label="Close" @click="emitClose">
              <X :size="18" :stroke-width="1.75" />
            </button>
          </header>

          <form class="task-drawer__form" @submit.prevent="onSubmit">
            <div class="task-drawer__field task-drawer__field--title">
              <label for="task-title">Title</label>
              <input
                id="task-title"
                v-model="form.title"
                type="text"
                required
                maxlength="200"
                :disabled="saving"
                placeholder="What needs to get done?"
                class="task-drawer__title-input"
              />
            </div>

            <div class="task-drawer__field">
              <label for="task-description">
                <AlignLeft :size="14" :stroke-width="1.75" />
                Notes
              </label>
              <textarea
                id="task-description"
                v-model="form.description"
                rows="4"
                maxlength="500"
                :disabled="saving"
                placeholder="Add context or details (optional)"
                class="task-drawer__textarea"
              />
            </div>

            <LinksEditor v-model="form.links" :disabled="saving" />

            <div class="task-drawer__grid">
              <div class="task-drawer__field">
                <label for="task-status">
                  <CircleDot :size="14" :stroke-width="1.75" />
                  Status
                </label>
                <select id="task-status" v-model="form.status" :disabled="saving" class="task-drawer__select">
                  <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>
              </div>

              <div class="task-drawer__field">
                <label for="task-due">
                  <Calendar :size="14" :stroke-width="1.75" />
                  Due date
                </label>
                <DatePicker id="task-due" v-model="form.due_date" :disabled="saving" />
              </div>
            </div>

            <div class="task-drawer__field">
              <label for="task-assignee">
                <UserRound :size="14" :stroke-width="1.75" />
                Assignee
              </label>
              <select id="task-assignee" v-model="form.assignee_key" :disabled="saving" class="task-drawer__select">
                <option :value="null">Unassigned</option>
                <option v-for="opt in assigneeOptions" :key="opt.key" :value="opt.key">
                  {{ assigneeOptionLabel(opt) }}
                </option>
              </select>
            </div>

            <div v-if="showProject" class="task-drawer__field">
              <label for="task-project">
                <FolderKanban :size="14" :stroke-width="1.75" />
                Project
              </label>
              <select id="task-project" v-model="form.project_id" :disabled="saving" class="task-drawer__select">
                <option :value="null">No project</option>
                <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.title }}</option>
              </select>
            </div>

            <p v-if="error" class="task-drawer__error">{{ error }}</p>

            <footer class="task-drawer__footer">
              <button type="button" class="btn-outline" :disabled="saving" @click="emitClose">Cancel</button>
              <button type="submit" class="btn-primary" :disabled="saving || !form.title.trim()">
                {{ saving ? 'Saving…' : mode === 'create' ? 'Create task' : 'Save changes' }}
              </button>
            </footer>
          </form>
        </aside>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { AlignLeft, Calendar, CircleDot, FolderKanban, UserRound, X } from '@lucide/vue'
import { computed, reactive, watch, onUnmounted } from 'vue'

import DatePicker from '@/components/DatePicker.vue'
import LinksEditor from '@/components/LinksEditor.vue'
import { assigneeOptionLabel } from '@/utils/assignee'
import { linksForApi } from '@/utils/links'
import { STATUS_OPTIONS } from '@/utils/ui'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'edit' },
  saving: { type: Boolean, default: false },
  error: { type: String, default: '' },
  assigneeOptions: { type: Array, default: () => [] },
  projects: { type: Array, default: () => [] },
  showProject: { type: Boolean, default: false },
  initial: {
    type: Object,
    default: () => ({
      title: '',
      description: '',
      links: [],
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
  description: '',
  links: [],
  assignee_key: null,
  due_date: '',
  status: 'pending',
  project_id: null,
})

const panelTitle = computed(() => {
  if (props.mode === 'create') return 'Create a task'
  return form.title.trim() || 'Edit task'
})

watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

onUnmounted(() => {
  document.body.style.overflow = ''
})

watch(
  () => [props.open, props.initial],
  () => {
    if (!props.open) return
    const init = props.initial || {}
    form.title = init.title || ''
    form.description = init.description || ''
    form.links = Array.isArray(init.links) ? init.links.map((l) => ({ ...l })) : []
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
    description: form.description.trim() || null,
    links: linksForApi(form.links),
    assignee_key: form.assignee_key,
    due_date: form.due_date || null,
    status: form.status || 'pending',
    project_id: form.project_id ?? null,
  })
}
</script>

<style scoped>
.task-drawer-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  display: flex;
  justify-content: flex-end;
  background: rgba(8, 10, 9, 0.55);
  backdrop-filter: blur(4px);
}

.task-drawer {
  width: min(100%, 460px);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-elevated);
  border-left: 1px solid var(--color-border);
  box-shadow: -24px 0 48px rgba(0, 0, 0, 0.35);
  overflow: hidden;
}

.task-drawer__accent {
  height: 3px;
  flex-shrink: 0;
  background: var(--status-todo);
}

.task-drawer__accent[data-s='in_progress'] {
  background: linear-gradient(90deg, var(--color-accent), #a6853a);
}

.task-drawer__accent[data-s='completed'] {
  background: var(--status-done);
}

.task-drawer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.35rem 1.35rem 1rem;
  border-bottom: 1px solid var(--color-border);
}

.task-drawer__eyebrow {
  margin: 0 0 0.25rem;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--color-accent);
}

.task-drawer__title {
  margin: 0;
  font-family: var(--font-display);
  font-size: 1.45rem;
  font-weight: 400;
  line-height: 1.25;
  color: var(--color-text);
  word-break: break-word;
}

.task-drawer__close {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s;
}

.task-drawer__close:hover {
  border-color: var(--color-accent);
  color: var(--color-text);
  background: rgba(196, 163, 90, 0.08);
}

.task-drawer__form {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.35rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.task-drawer__field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.task-drawer__field label {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}

.task-drawer__field--title label {
  text-transform: none;
  letter-spacing: 0;
  font-size: 0.82rem;
  font-weight: 500;
}

.task-drawer__title-input {
  font-family: var(--font-display);
  font-size: 1.15rem;
  padding: 0.65rem 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.task-drawer__title-input:focus {
  outline: none;
  border-color: rgba(196, 163, 90, 0.55);
  box-shadow: 0 0 0 3px rgba(196, 163, 90, 0.12);
}

.task-drawer__select,
.task-drawer__textarea,
.task-drawer__field :deep(input) {
  font-family: var(--font-body);
  font-size: 0.95rem;
  padding: 0.6rem 0.7rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  transition: border-color 0.2s;
}

.task-drawer__textarea {
  resize: vertical;
  min-height: 5.5rem;
  line-height: 1.5;
}

.task-drawer__select:focus,
.task-drawer__textarea:focus,
.task-drawer__field :deep(input:focus) {
  outline: none;
  border-color: rgba(196, 163, 90, 0.55);
}

.task-drawer__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem;
}

.task-drawer__error {
  margin: 0;
  font-size: 0.88rem;
  color: var(--color-danger);
}

.task-drawer__footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
  margin-top: auto;
  padding-top: 0.5rem;
}

.drawer-enter-active,
.drawer-leave-active {
  transition: opacity 0.32s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-enter-active .task-drawer,
.drawer-leave-active .task-drawer {
  transition: transform 0.36s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-enter-from,
.drawer-leave-to {
  opacity: 0;
}

.drawer-enter-from .task-drawer,
.drawer-leave-to .task-drawer {
  transform: translateX(100%);
}

@media (max-width: 520px) {
  .task-drawer__grid {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .drawer-enter-active,
  .drawer-leave-active,
  .drawer-enter-active .task-drawer,
  .drawer-leave-active .task-drawer {
    transition: none;
  }
}
</style>
