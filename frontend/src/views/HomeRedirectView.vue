<template>
  <p class="muted">Loading…</p>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

import { loadSessionUser, user } from '@/composables/session'
import { getToken } from '@/services/auth'

const router = useRouter()

onMounted(async () => {
  if (!getToken()) {
    router.replace({ name: 'login' })
    return
  }
  await loadSessionUser()
  if (!user.value) {
    router.replace({ name: 'login' })
    return
  }
  router.replace(user.value.role === 'admin' ? { name: 'admin-dashboard' } : { name: 'employee-assignments' })
})
</script>

<style scoped>
.muted {
  color: var(--color-text-muted);
  margin: 2rem 0;
}
</style>
