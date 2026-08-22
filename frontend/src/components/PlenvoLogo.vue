<template>
  <component :is="tag" class="plenvo-logo" :class="[`plenvo-logo--${variant}`, { 'plenvo-logo--compact': compact }]">
    <span class="plenvo-logo__mark" aria-hidden="true">
      <svg viewBox="0 0 128 128" fill="none" xmlns="http://www.w3.org/2000/svg">
        <rect
          class="plenvo-logo__squircle"
          width="128"
          height="128"
          rx="28"
          stroke-width="1.5"
        />
        <path
          class="plenvo-logo__glyph"
          d="M42 98V30h30c16.5 0 30 13.5 30 30S88.5 90 72 90H56"
          stroke-width="15"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </span>
    <span v-if="showWordmark" class="plenvo-logo__wordmark">Plenvo</span>
  </component>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  variant: {
    type: String,
    default: 'lockup', // 'lockup' | 'icon'
  },
  compact: { type: Boolean, default: false },
  tag: { type: String, default: 'span' },
})

const showWordmark = computed(() => props.variant === 'lockup')
</script>

<style scoped>
.plenvo-logo {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  text-decoration: none;
  color: inherit;
}

.plenvo-logo__mark {
  display: inline-flex;
  flex-shrink: 0;
  line-height: 0;
}

.plenvo-logo__mark svg {
  display: block;
  width: 2rem;
  height: 2rem;
}

.plenvo-logo--compact .plenvo-logo__mark svg {
  width: 1.65rem;
  height: 1.65rem;
}

.plenvo-logo__squircle {
  fill: var(--color-bg-elevated);
  stroke: var(--color-border);
}

.plenvo-logo__glyph {
  stroke: var(--color-accent);
}

.plenvo-logo__wordmark {
  font-family: var(--font-display);
  font-size: 1.55rem;
  font-style: italic;
  font-weight: 400;
  letter-spacing: 0.01em;
  color: var(--color-text);
  line-height: 1;
}

.plenvo-logo--compact .plenvo-logo__wordmark {
  font-size: 1.35rem;
}
</style>
