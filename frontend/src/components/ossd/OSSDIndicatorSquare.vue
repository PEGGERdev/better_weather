<template>
  <div class="osss-square" :class="{ 'osss-square--active': active }">
    <span class="osss-square__label">
      {{ label }}
    </span>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  label: string
  active: boolean
}>()
</script>

<style scoped>
.osss-square {
  flex: 1;
  height: 56px;
  border-radius: 0.75rem;
  background-color: #064e3b;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 0.9rem;
  color: #bbf7d0;
  transition: background-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
  border: 1px solid rgba(34, 197, 94, 0.5);
}

.osss-square--active {
  background-color: #b91c1c;
  color: #fee2e2;
  border-color: rgba(248, 113, 113, 0.7);
  box-shadow: 0 0 18px rgba(248, 113, 113, 0.6);
}
</style>
