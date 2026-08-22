<template>
  <ul v-if="items.length" class="links-list" :class="{ 'links-list--compact': compact }">
    <li v-for="(link, index) in items" :key="`${link.label}-${index}`">
      <a
        :href="link.url"
        class="links-list__item"
        target="_blank"
        rel="noopener noreferrer"
        :title="link.url"
      >
        <ExternalLink :size="compact ? 12 : 13" :stroke-width="1.75" />
        <span>{{ link.label }}</span>
      </a>
    </li>
  </ul>
</template>

<script setup>
import { ExternalLink } from '@lucide/vue'
import { computed } from 'vue'

import { normalizeLinks } from '@/utils/links'

const props = defineProps({
  links: { type: Array, default: () => [] },
  compact: { type: Boolean, default: false },
})

const items = computed(() => normalizeLinks(props.links))
</script>

<style scoped>
.links-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.links-list--compact {
  gap: 0.25rem;
}

.links-list__item {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  max-width: 100%;
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--color-accent);
  text-decoration: none;
}

.links-list--compact .links-list__item {
  font-size: 0.76rem;
}

.links-list__item span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.links-list__item:hover {
  text-decoration: underline;
}
</style>
