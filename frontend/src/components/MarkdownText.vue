<template>
  <div class="markdown-text" v-html="html" />
</template>

<script setup>
import { computed } from 'vue'

import { renderMarkdownLite } from '@/utils/markdown'

const props = defineProps({
  text: { type: String, default: '' },
})

const html = computed(() => renderMarkdownLite(props.text))
</script>

<style scoped>
.markdown-text :deep(p) {
  margin: 0 0 0.65rem;
}

.markdown-text :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-text :deep(ul) {
  margin: 0 0 0.65rem;
  padding-left: 1.2rem;
}

.markdown-text :deep(li) {
  margin: 0.2rem 0;
}

.markdown-text :deep(strong) {
  font-weight: 600;
  color: var(--color-text);
}

.markdown-text :deep(em) {
  font-style: italic;
}
</style>
