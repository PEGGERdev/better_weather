<template>
  <BaseCard data-testid="widget-webcam">
    <BaseSectionTitle title="Webcam" subtitle="Live-Bild mit periodischem Screenshot" />
    <WebcamStream />
  </BaseCard>
</template>

<script setup lang="ts">
import BaseCard from '../base/BaseCard.vue'
import BaseSectionTitle from '../base/BaseSectionTitle.vue'
import WebcamStream from './WebcamStream.vue'
</script>
