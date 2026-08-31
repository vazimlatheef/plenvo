<template>
  <div ref="root" class="dp" :class="{ 'dp--open': open, 'dp--disabled': disabled }">
    <div class="dp-field">
      <input
        :id="inputId"
        v-model="typedValue"
        type="text"
        class="dp-input"
        :class="{ 'dp-input--placeholder': !typedValue }"
        :disabled="disabled"
        :placeholder="placeholder"
        inputmode="numeric"
        autocomplete="off"
        aria-label="Due date"
        @focus="onInputFocus"
        @blur="commitTyped"
        @keydown.enter.prevent="commitTyped"
      />
      <button
        type="button"
        class="dp-cal-btn"
        :disabled="disabled"
        :aria-expanded="open"
        aria-haspopup="dialog"
        aria-label="Open calendar"
        @click="toggle"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <rect x="3" y="5" width="18" height="16" rx="2" stroke="currentColor" stroke-width="1.75" />
          <path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
        </svg>
      </button>
    </div>

    <Teleport to="body">
      <div
        v-if="open"
        ref="panel"
        class="dp-panel"
        role="dialog"
        :style="panelStyle"
        @mousedown.stop
      >
        <div class="dp-nav">
          <button type="button" class="dp-nav-btn" aria-label="Previous month" @click="shiftMonth(-1)">‹</button>
          <div class="dp-selects">
            <select v-model.number="viewMonth" class="dp-select" aria-label="Month">
              <option v-for="(m, i) in MONTHS" :key="m" :value="i">{{ m }}</option>
            </select>
            <select v-model.number="viewYear" class="dp-select" aria-label="Year">
              <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
            </select>
          </div>
          <button type="button" class="dp-nav-btn" aria-label="Next month" @click="shiftMonth(1)">›</button>
        </div>

        <div class="dp-weekdays">
          <span v-for="d in WEEKDAYS" :key="d">{{ d }}</span>
        </div>

        <div class="dp-grid">
          <button
            v-for="(cell, idx) in dayCells"
            :key="idx"
            type="button"
            class="dp-day"
            :class="{
              'dp-day--muted': !cell.inMonth,
              'dp-day--selected': cell.iso && cell.iso === modelValue,
              'dp-day--today': cell.iso && cell.iso === todayIso,
            }"
            :disabled="!cell.inMonth"
            @click="pickDay(cell)"
          >
            {{ cell.day }}
          </button>
        </div>

        <div class="dp-footer">
          <button type="button" class="dp-footer-btn" @click="pickToday">Today</button>
          <button v-if="modelValue" type="button" class="dp-footer-btn" @click="clear">Clear</button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: 'dd/mm/yyyy' },
  inputId: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
]
const WEEKDAYS = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su']

const open = ref(false)
const root = ref(null)
const panel = ref(null)
const panelStyle = ref({})

const now = new Date()
const viewMonth = ref(now.getMonth())
const viewYear = ref(now.getFullYear())

const todayIso = toIso(now.getFullYear(), now.getMonth(), now.getDate())

const yearOptions = computed(() => {
  const center = viewYear.value || now.getFullYear()
  const start = center - 40
  const end = center + 20
  const years = []
  for (let y = start; y <= end; y += 1) years.push(y)
  return years
})

const typedValue = ref(isoToDisplay(props.modelValue))

watch(
  () => props.modelValue,
  (val) => {
    typedValue.value = isoToDisplay(val)
  },
)

const dayCells = computed(() => {
  const year = viewYear.value
  const month = viewMonth.value
  const first = new Date(year, month, 1)
  // Monday-first: Sun=0 → 6, Mon=1 → 0, …
  const startPad = (first.getDay() + 6) % 7
  const daysInMonth = new Date(year, month + 1, 0).getDate()
  const prevDays = new Date(year, month, 0).getDate()

  const cells = []
  for (let i = 0; i < startPad; i += 1) {
    const day = prevDays - startPad + i + 1
    cells.push({ day, inMonth: false, iso: null })
  }
  for (let day = 1; day <= daysInMonth; day += 1) {
    cells.push({ day, inMonth: true, iso: toIso(year, month, day) })
  }
  while (cells.length % 7 !== 0) {
    cells.push({ day: cells.length % 7 === 0 ? 1 : (cells[cells.length - 1].day + 1), inMonth: false, iso: null })
  }
  // Fix trailing muted days numbering
  let next = 1
  for (let i = startPad + daysInMonth; i < cells.length; i += 1) {
    cells[i] = { day: next, inMonth: false, iso: null }
    next += 1
  }
  return cells
})

watch(
  () => props.modelValue,
  (val) => {
    const parsed = parseIso(val)
    if (parsed) {
      viewMonth.value = parsed.getMonth()
      viewYear.value = parsed.getFullYear()
    }
  },
  { immediate: true },
)

function toIso(year, monthIndex, day) {
  const m = String(monthIndex + 1).padStart(2, '0')
  const d = String(day).padStart(2, '0')
  return `${year}-${m}-${d}`
}

function parseIso(value) {
  if (!value || typeof value !== 'string') return null
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value.trim())
  if (!m) return null
  const date = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  if (Number.isNaN(date.getTime())) return null
  return date
}

function isoToDisplay(value) {
  const date = parseIso(value)
  if (!date) return ''
  const d = String(date.getDate()).padStart(2, '0')
  const m = String(date.getMonth() + 1).padStart(2, '0')
  return `${d}/${m}/${date.getFullYear()}`
}

function parseTypedDate(raw) {
  const s = String(raw || '').trim()
  if (!s) return ''
  const iso = parseIso(s)
  if (iso) return toIso(iso.getFullYear(), iso.getMonth(), iso.getDate())
  const m = /^(\d{1,2})[/\-. ](\d{1,2})[/\-. ](\d{4})$/.exec(s)
  if (!m) return null
  const day = Number(m[1])
  const month = Number(m[2])
  const year = Number(m[3])
  const date = new Date(year, month - 1, day)
  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null
  }
  return toIso(year, month - 1, day)
}

function commitTyped() {
  const parsed = parseTypedDate(typedValue.value)
  if (parsed === '') {
    emit('update:modelValue', '')
    typedValue.value = ''
    return
  }
  if (!parsed) {
    typedValue.value = isoToDisplay(props.modelValue)
    return
  }
  emit('update:modelValue', parsed)
  typedValue.value = isoToDisplay(parsed)
}

function onInputFocus() {
  if (open.value) close()
}

function shiftMonth(delta) {
  let m = viewMonth.value + delta
  let y = viewYear.value
  if (m < 0) {
    m = 11
    y -= 1
  } else if (m > 11) {
    m = 0
    y += 1
  }
  viewMonth.value = m
  viewYear.value = y
}

async function toggle() {
  if (props.disabled) return
  if (open.value) {
    close()
    return
  }
  open.value = true
  await nextTick()
  positionPanel()
  requestAnimationFrame(() => positionPanel())
}

function close() {
  open.value = false
}

function pickDay(cell) {
  if (!cell.inMonth || !cell.iso) return
  emit('update:modelValue', cell.iso)
  close()
}

function pickToday() {
  emit('update:modelValue', todayIso)
  viewMonth.value = now.getMonth()
  viewYear.value = now.getFullYear()
  close()
}

function clear() {
  emit('update:modelValue', '')
  close()
}

function positionPanel() {
  const el = root.value
  const pop = panel.value
  if (!el || !pop) return
  const rect = el.getBoundingClientRect()
  const margin = 8
  const gap = 6
  const maxH = Math.max(180, window.innerHeight - margin * 2)
  const naturalH = pop.scrollHeight || pop.offsetHeight || 320
  const popH = Math.min(naturalH, maxH)
  const popW = Math.min(Math.max(rect.width, 280), window.innerWidth - margin * 2)
  const spaceBelow = window.innerHeight - rect.bottom - margin
  const spaceAbove = rect.top - margin
  const openUp = spaceBelow < popH + gap && spaceAbove > spaceBelow
  let top = openUp ? rect.top - popH - gap : rect.bottom + gap
  top = Math.min(Math.max(margin, top), window.innerHeight - popH - margin)
  let left = rect.left
  if (left + popW > window.innerWidth - margin) {
    left = window.innerWidth - popW - margin
  }
  left = Math.max(margin, left)
  panelStyle.value = {
    position: 'fixed',
    top: `${top}px`,
    left: `${left}px`,
    width: `${popW}px`,
    maxHeight: `${popH}px`,
    overflowY: naturalH > popH ? 'auto' : 'visible',
    zIndex: 1200,
  }
}

function onDocPointer(e) {
  if (!open.value) return
  const t = e.target
  if (root.value?.contains(t) || panel.value?.contains(t)) return
  close()
}

function onKey(e) {
  if (e.key === 'Escape' && open.value) close()
}

function onScrollOrResize() {
  if (open.value) positionPanel()
}

onMounted(() => {
  document.addEventListener('mousedown', onDocPointer)
  document.addEventListener('keydown', onKey)
  window.addEventListener('resize', onScrollOrResize)
  window.addEventListener('scroll', onScrollOrResize, true)
})

onBeforeUnmount(() => {
  document.removeEventListener('mousedown', onDocPointer)
  document.removeEventListener('keydown', onKey)
  window.removeEventListener('resize', onScrollOrResize)
  window.removeEventListener('scroll', onScrollOrResize, true)
})
</script>

<style scoped>
.dp {
  position: relative;
  width: 100%;
}

.dp-field {
  width: 100%;
  min-height: var(--control-height);
  display: flex;
  align-items: center;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  box-sizing: border-box;
}

.dp-field:hover {
  border-color: rgba(196, 163, 90, 0.45);
}

.dp--open .dp-field,
.dp-field:focus-within {
  border-color: var(--color-accent);
  box-shadow: 0 0 0 2px var(--color-accent-soft);
}

.dp--disabled .dp-field {
  opacity: 0.55;
}

.dp-input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.95rem;
  padding: 0.65rem 0.5rem 0.65rem 0.9rem;
  outline: none;
}

.dp-input--placeholder::placeholder {
  color: var(--color-text-muted);
}

.dp-cal-btn {
  flex-shrink: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.4rem;
  height: 100%;
  min-height: var(--control-height);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
}

.dp-cal-btn:disabled {
  cursor: not-allowed;
}
</style>

<style>
/* Unscoped: panel is teleported to body */
.dp-panel {
  font-family: var(--font-body);
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  padding: 0.75rem;
  color: var(--color-text);
}

.dp-nav {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-bottom: 0.65rem;
}

.dp-nav-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
}

.dp-nav-btn:hover {
  border-color: var(--color-accent);
  color: var(--color-accent);
}

.dp-selects {
  flex: 1;
  display: flex;
  gap: 0.35rem;
  min-width: 0;
}

.dp-select {
  flex: 1;
  min-width: 0;
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.35rem 0.4rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border);
  background: var(--color-bg);
  color: var(--color-text);
}

.dp-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.15rem;
  margin-bottom: 0.25rem;
}

.dp-weekdays span {
  text-align: center;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--color-text-muted);
  padding: 0.2rem 0;
}

.dp-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 0.15rem;
}

.dp-day {
  aspect-ratio: 1;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text);
  font-family: var(--font-body);
  font-size: 0.82rem;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;
}

.dp-day:hover:not(:disabled) {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}

.dp-day--muted {
  color: var(--color-text-muted);
  opacity: 0.35;
  cursor: default;
}

.dp-day--today:not(.dp-day--selected) {
  box-shadow: inset 0 0 0 1px rgba(196, 163, 90, 0.55);
}

.dp-day--selected {
  background: linear-gradient(135deg, var(--color-accent), #a6853a);
  color: #0f1210;
  font-weight: 600;
}

.dp-footer {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  margin-top: 0.65rem;
  padding-top: 0.55rem;
  border-top: 1px solid var(--color-border);
}

.dp-footer-btn {
  font-family: var(--font-body);
  font-size: 0.75rem;
  font-weight: 600;
  background: none;
  border: none;
  color: var(--color-accent);
  cursor: pointer;
  padding: 0.2rem 0.1rem;
}

.dp-footer-btn:hover {
  text-decoration: underline;
}
</style>
