<template>
  <div v-if="writeRestricted" class="plan-restriction-banner" role="status">
    <p class="plan-restriction-banner__text">
      {{ restrictionMessage }}
      <RouterLink
        v-if="overMemberLimit"
        to="/app/team"
        class="plan-restriction-banner__link"
      >
        Open Team →
      </RouterLink>
      <RouterLink
        v-else
        to="/app/account"
        class="plan-restriction-banner__link"
      >
        Upgrade in Account →
      </RouterLink>
    </p>
  </div>
</template>

<script setup>
import { useWriteAccess } from '@/composables/useWriteAccess'

const { writeRestricted, overMemberLimit, restrictionMessage } = useWriteAccess()
</script>

<style scoped>
.plan-restriction-banner {
  flex-shrink: 0;
  padding: 0.65rem 1.1rem;
  background: rgba(196, 163, 90, 0.14);
  border-bottom: 1px solid rgba(196, 163, 90, 0.35);
}

.plan-restriction-banner__text {
  margin: 0;
  font-size: 0.86rem;
  line-height: 1.45;
  color: var(--color-text);
}

.plan-restriction-banner__link {
  margin-left: 0.35rem;
  font-weight: 600;
  color: var(--color-accent);
  white-space: nowrap;
}
</style>
