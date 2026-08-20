<template>
  <router-view v-slot="{ Component, route }">
    <component :is="Component" :key="pageKey(route)" />
  </router-view>
</template>

<script setup>
function pageKey(route) {
  if (route.path.startsWith('/app')) return 'app-shell'
  return route.name || route.path
}
</script>
