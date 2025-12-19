<template>
  <div class="two-column-layout-root">
    <div class="two-column-layout">
      <div class="two-column-layout__column two-column-layout__column--left">
        <slot name="left" />
      </div>
      <div class="two-column-layout__column two-column-layout__column--right">
        <slot name="right" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts"></script>

<style scoped>
.two-column-layout-root {
  max-width: 1200px;
  margin: 0 auto;
}

.two-column-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 1rem;
  align-items: flex-start;
}

.two-column-layout__column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (max-width: 900px) {
  .two-column-layout {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
