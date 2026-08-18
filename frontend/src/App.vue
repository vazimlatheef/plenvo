<template>
  <router-view v-slot="{ Component, route }">
    <transition name="page" mode="out-in">
      <component :is="Component" :key="pageKey(route)" />
    </transition>
  </router-view>
</template>

<script setup>
function pageKey(route) {
  if (route.path.startsWith('/app')) return 'app-shell'
  return route.name || route.path
}
</script>
