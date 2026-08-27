<template>
  <div class="kanban-board">
    <p v-if="showTouchHint" class="kanban-touch-hint">
      Long-press a card to drag, or use the status menu on each card.
    </p>
    <div class="kanban-columns">
      <section
        v-for="col in STATUS_GROUPS"
        :key="col.key"
        class="kanban-column"
        :data-status="col.key"
      >
        <header class="kanban-column__header">
          <span class="status-pill" :data-s="col.key">{{ col.label }}</span>
          <span class="count">{{ columnTasks[col.key].length }}</span>
        </header>

        <draggable
          v-model="columnTasks[col.key]"
          class="kanban-column__list"
          :class="{ 'kanban-column__list--empty': !columnTasks[col.key].length }"
          group="tasks"
          item-key="id"
          :disabled="dragDisabled"
          :delay="touchDelay"
          :delay-on-touch-only="true"
          :touch-start-threshold="8"
          :force-fallback="false"
          ghost-class="kanban-card--ghost"
          drag-class="kanban-card--drag"
          chosen-class="kanban-card--chosen"
          @start="onDragStart"
          @end="onDragEnd"
          @change="(evt) => onColumnChange(evt, col.key)"
        >
          <template #item="{ element: task }">
            <article
              class="kanban-card"
              :class="{ 'kanban-card--flash': flashId === task.id }"
            >
              <div class="kanban-card__top">
                <button
                  v-if="canEdit"
                  type="button"
                  class="kanban-card__title"
                  @click="$emit('edit', task)"
                >
                  {{ task.title }}
                </button>
                <span v-else class="kanban-card__title kanban-card__title--static">
                  {{ task.title }}
                </span>
                <span
                  v-if="projectLabel && projectLabel(task.project_id)"
                  class="project-tag kanban-card__project"
                >
                  {{ projectLabel(task.project_id) }}
                </span>
              </div>

              <div class="kanban-card__meta">
                <span
                  class="avatar kanban-card__avatar"
                  :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
                  :title="assigneeName(task)"
                >
                  {{ getInitials(assigneeName(task)) }}
                </span>
                <span class="kanban-card__due" :class="{ 'kanban-card__due--overdue': isOverdue(task) }">
                  <Calendar :size="12" :stroke-width="1.75" />
                  {{ task.due_date ? formatShortDate(task.due_date) : 'No due date' }}
                </span>
                <span v-if="task.priority" class="priority-pill" :data-p="task.priority">
                  {{ task.priority }}
                </span>
                <span v-if="task.description" class="kanban-card__indicator" title="Has notes">
                  <FileText :size="12" :stroke-width="1.75" />
                </span>
                <span v-if="task.links?.length" class="kanban-card__indicator" title="Has links">
                  <Link2 :size="12" :stroke-width="1.75" />
                  {{ task.links.length }}
                </span>
              </div>

              <div class="kanban-card__footer">
                <select
                  class="status-pill kanban-card__status-mobile"
                  :data-s="task.status"
                  :value="task.status"
                  :disabled="busyId === task.id || writeRestricted"
                  :title="writeDisabledTitle"
                  @change="onStatusSelect(task, $event)"
                >
                  <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
                    {{ opt.label }}
                  </option>
                </select>

                <div v-if="canManageActions" class="kanban-card__actions">
                  <button
                    type="button"
                    class="row-icon-btn"
                    title="Edit task"
                    aria-label="Edit task"
                    :disabled="busyId === task.id"
                    @click="$emit('edit', task)"
                  >
                    <Pencil :size="14" :stroke-width="1.75" />
                  </button>
                  <button
                    type="button"
                    class="row-icon-btn row-icon-btn--danger"
                    title="Delete task"
                    aria-label="Delete task"
                    :disabled="busyId === task.id"
                    @click="$emit('delete', task)"
                  >
                    <Trash2 :size="14" :stroke-width="1.75" />
                  </button>
                </div>
              </div>
            </article>
          </template>
        </draggable>
      </section>
    </div>
  </div>
</template>

<script setup>
import { Calendar, FileText, Link2, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import draggable from 'vuedraggable'

import {
  STATUS_GROUPS,
  STATUS_OPTIONS,
  avatarTone,
  formatShortDate,
  getInitials,
} from '@/utils/ui'

const props = defineProps({
  tasks: { type: Array, required: true },
  busyId: { type: [Number, String, null], default: null },
  flashId: { type: [Number, String, null], default: null },
  writeRestricted: { type: Boolean, default: false },
  writeDisabledTitle: { type: String, default: '' },
  canEdit: { type: Boolean, default: true },
  canManageActions: { type: Boolean, default: true },
  assigneeName: { type: Function, required: true },
  assigneeSeed: { type: Function, required: true },
  projectLabel: { type: Function, default: null },
})

const emit = defineEmits(['status-change', 'edit', 'delete'])

const columnTasks = ref({
  pending: [],
  in_progress: [],
  completed: [],
})

const isDragging = ref(false)
const isCoarsePointer = ref(false)
const isNarrowViewport = ref(false)

const dragDisabled = computed(() => props.writeRestricted)
const touchDelay = computed(() => (isCoarsePointer.value ? 280 : 0))
const showTouchHint = computed(() => isCoarsePointer.value || isNarrowViewport.value)

let mediaNarrow = null
let mediaCoarse = null

function syncColumns(taskList) {
  columnTasks.value = {
    pending: taskList.filter((t) => t.status === 'pending'),
    in_progress: taskList.filter((t) => t.status === 'in_progress'),
    completed: taskList.filter((t) => t.status === 'completed'),
  }
}

watch(
  () => props.tasks,
  (taskList) => {
    if (!isDragging.value) syncColumns(taskList)
  },
  { deep: true, immediate: true },
)

function onDragStart() {
  isDragging.value = true
}

function onDragEnd() {
  isDragging.value = false
}

function onColumnChange(evt, targetStatus) {
  if (!evt.added) return
  const task = evt.added.element
  if (task.status === targetStatus) return
  emit('status-change', { task, status: targetStatus })
}

function onStatusSelect(task, event) {
  const next = event.target.value
  if (next === task.status) return
  emit('status-change', { task, status: next })
}

function isOverdue(task) {
  if (!task.due_date || task.status === 'completed') return false
  const due = new Date(task.due_date)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  due.setHours(0, 0, 0, 0)
  return due < today
}

function updateMediaFlags() {
  isNarrowViewport.value = mediaNarrow?.matches ?? false
  isCoarsePointer.value = mediaCoarse?.matches ?? false
}

onMounted(() => {
  if (typeof window !== 'undefined' && window.matchMedia) {
    mediaNarrow = window.matchMedia('(max-width: 640px)')
    mediaCoarse = window.matchMedia('(pointer: coarse)')
    updateMediaFlags()
    mediaNarrow.addEventListener('change', updateMediaFlags)
    mediaCoarse.addEventListener('change', updateMediaFlags)
  }
})

onUnmounted(() => {
  mediaNarrow?.removeEventListener('change', updateMediaFlags)
  mediaCoarse?.removeEventListener('change', updateMediaFlags)
})
</script>

<style scoped>
.kanban-board {
  margin-top: 0.25rem;
}

.kanban-touch-hint {
  margin: 0 0 0.75rem;
  font-size: 0.78rem;
  color: var(--color-text-muted);
}

.kanban-columns {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
  align-items: start;
}

.kanban-column {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: rgba(0, 0, 0, 0.12);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.65rem;
}

.kanban-column__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.55rem;
  padding: 0 0.1rem;
}

.kanban-column__header .count {
  font-size: 0.75rem;
  color: var(--color-text-muted);
}

.kanban-column__list {
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
  min-height: 3.5rem;
}

.kanban-column__list--empty {
  min-height: 4.5rem;
  border: 1px dashed rgba(232, 228, 216, 0.12);
  border-radius: var(--radius-sm);
}

.kanban-card {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  padding: 0.65rem 0.7rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  cursor: grab;
  touch-action: manipulation;
  transition:
    background-color 0.35s ease,
    box-shadow 0.35s ease,
    transform 0.2s cubic-bezier(0.22, 1, 0.36, 1);
}

.kanban-card:active {
  cursor: grabbing;
}

.kanban-card--ghost {
  opacity: 0.45;
}

.kanban-card--drag {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
  transform: rotate(1.5deg);
}

.kanban-card--chosen {
  box-shadow: 0 0 0 1px rgba(196, 163, 90, 0.45);
}

.kanban-card--flash {
  animation: kanban-flash 0.7s ease;
}

@keyframes kanban-flash {
  0%,
  100% {
    background: var(--color-surface);
  }
  40% {
    background: rgba(196, 163, 90, 0.18);
  }
}

.kanban-card__top {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  align-items: flex-start;
}

.kanban-card__title {
  font-family: var(--font-body);
  font-size: 0.88rem;
  font-weight: 600;
  line-height: 1.35;
  color: var(--color-text);
  text-align: left;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
}

.kanban-card__title:hover {
  color: var(--color-accent);
}

.kanban-card__title--static {
  cursor: default;
}

.kanban-card__project {
  max-width: 100%;
}

.kanban-card__meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.4rem 0.55rem;
}

.kanban-card__avatar {
  width: 22px;
  height: 22px;
  font-size: 0.58rem;
}

.kanban-card__due {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.72rem;
  color: var(--color-text-muted);
}

.kanban-card__due--overdue {
  color: #e8a0a0;
}

.priority-pill {
  font-size: 0.65rem;
  font-weight: 600;
  text-transform: capitalize;
  padding: 0.12rem 0.4rem;
  border-radius: 999px;
  border: 1px solid transparent;
}

.priority-pill[data-p='high'] {
  color: #e8a0a0;
  background: rgba(232, 160, 160, 0.12);
  border-color: rgba(232, 160, 160, 0.28);
}

.priority-pill[data-p='medium'] {
  color: var(--color-accent);
  background: var(--color-accent-soft);
  border-color: rgba(196, 163, 90, 0.28);
}

.priority-pill[data-p='low'] {
  color: var(--color-text-muted);
  background: rgba(232, 228, 216, 0.06);
  border-color: rgba(232, 228, 216, 0.14);
}

.kanban-card__indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.15rem;
  font-size: 0.68rem;
  color: var(--color-text-muted);
}

.kanban-card__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  margin-top: 0.1rem;
}

.kanban-card__status-mobile {
  display: none;
  font-size: 0.68rem;
  padding: 0.22rem 0.45rem;
  max-width: 100%;
}

.kanban-card__actions {
  display: flex;
  gap: 0.15rem;
  margin-left: auto;
}

@media (max-width: 900px) {
  .kanban-columns {
    grid-template-columns: 1fr;
  }

  .kanban-column__list {
    min-height: 2.5rem;
  }
}

@media (max-width: 640px), (pointer: coarse) {
  .kanban-card {
    cursor: default;
  }

  .kanban-card__status-mobile {
    display: inline-flex;
  }
}
</style>
