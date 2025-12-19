<template>
  <section class="base-card">
    <slot />
  </section>
</template>

<script setup lang="ts"></script>

<style scoped>
.base-card {
  background-color: var(--bg-elevated);
  border-radius: 0.75rem;
  border: 1px solid var(--border-subtle);
  padding: 1rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
}
</style>
