<template>
  <div>
    <div class="dense-row dense-row--task dense-row--head" aria-hidden="true">
      <span />
      <span class="dense-head-label">Task</span>
      <span class="dense-head-label">Assigned to</span>
      <span class="dense-head-label">Due</span>
      <span />
      <span class="dense-head-label dense-head-label--end">Status</span>
    </div>
    <section v-for="group in statusGroups" :key="group.key" class="task-group">
      <div class="group-label">
        <span class="status-pill" :data-s="group.key">{{ group.label }}</span>
        <span class="count">{{ group.tasks.length }}</span>
      </div>
      <ul v-if="group.tasks.length" class="dense-list">
        <li
          v-for="task in group.tasks"
          :key="task.id"
          class="dense-row dense-row--task"
          :class="{ 'dense-row--flash': flashId === task.id }"
        >
          <span
            class="avatar"
            :class="`avatar-tone-${avatarTone(assigneeSeed(task))}`"
            :title="assigneeName(task)"
          >
            {{ getInitials(assigneeName(task)) }}
          </span>
          <div class="dense-row__meta">
            <button
              v-if="canEdit"
              type="button"
              class="dense-row__title"
              @click="$emit('edit', task)"
            >
              {{ task.title }}
            </button>
            <span v-else class="dense-row__title">{{ task.title }}</span>
            <span v-if="projectLabel && projectLabel(task.project_id)" class="project-tag">
              {{ projectLabel(task.project_id) }}
            </span>
            <p v-if="task.description" class="task-notes">{{ task.description }}</p>
            <LinksList :links="task.links" compact class="task-links" />
          </div>
          <div class="dense-row__assignee" :title="assigneeName(task)">
            <UserRound class="dense-row__assignee-icon" :size="13" :stroke-width="1.75" />
            <span class="dense-row__assignee-name">{{ assigneeName(task) }}</span>
          </div>
          <span class="dense-row__due">
            <Calendar class="dense-row__due-icon" :size="13" :stroke-width="1.75" />
            {{ task.due_date ? formatShortDate(task.due_date) : 'No due date' }}
          </span>
          <div class="dense-row__actions">
            <template v-if="canManageActions">
              <button
                type="button"
                class="row-icon-btn"
                title="Edit task"
                aria-label="Edit task"
                :disabled="busyId === task.id"
                @click="$emit('edit', task)"
              >
                <Pencil :size="15" :stroke-width="1.75" />
              </button>
              <button
                type="button"
                class="row-icon-btn row-icon-btn--danger"
                title="Delete task"
                aria-label="Delete task"
                :disabled="busyId === task.id"
                @click="$emit('delete', task)"
              >
                <Trash2 :size="15" :stroke-width="1.75" />
              </button>
            </template>
          </div>
          <select
            class="status-pill"
            :data-s="task.status"
            :value="task.status"
            :disabled="busyId === task.id || writeRestricted"
            :title="writeDisabledTitle"
            @change="onStatusChange(task, $event)"
          >
            <option v-for="opt in STATUS_OPTIONS" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </li>
      </ul>
      <p v-else class="muted-line empty-group">None</p>
    </section>
  </div>
</template>

<script setup>
import { Calendar, Pencil, Trash2, UserRound } from '@lucide/vue'

import LinksList from '@/components/LinksList.vue'
import { STATUS_OPTIONS, avatarTone, formatShortDate, getInitials } from '@/utils/ui'

defineProps({
  statusGroups: { type: Array, required: true },
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

const emit = defineEmits(['edit', 'delete', 'status-change'])

function onStatusChange(task, event) {
  const next = event.target.value
  if (next === task.status) return
  emit('status-change', { task, status: next })
}
</script>

<style scoped>
.empty-group {
  margin: 0.35rem 0 0;
  font-size: 0.85rem;
}
</style>
