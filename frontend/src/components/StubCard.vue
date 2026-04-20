<template>
  <section class="card">
    <h2 v-if="title">{{ title }}</h2>
    <p class="muted">{{ message }}</p>
    <slot />
  </section>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  message: { type: String, default: 'Placeholder — API wiring comes next.' },
})
</script>

<style scoped>
.card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 1.25rem 1.35rem;
  box-shadow: var(--shadow);
}

.card h2 {
  margin-bottom: 0.35rem;
}

.muted {
  margin: 0;
  font-size: 0.9rem;
}
</style>
