<template>
  <div class="shell">
    <AppHeader />
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
</script>

<style scoped>
.shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(120% 80% at 10% 0%, rgba(196, 163, 90, 0.08), transparent 45%),
    var(--color-bg);
}

.main {
  flex: 1;
  width: 100%;
  max-width: 1120px;
  margin: 0 auto;
  padding: 1.5rem 1.25rem 3rem;
}
</style>
