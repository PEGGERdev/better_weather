<template>
  <div class="webcam-stream">
    <video ref="videoEl" autoplay playsinline class="webcam-stream__video"></video>
    <canvas ref="canvasEl" class="webcam-stream__canvas"></canvas>

    <div class="webcam-stream__screenshot">
      <p class="webcam-stream__hint">Letzter Screenshot (alle 5 Sekunden)</p>
      <img
        v-if="screenshot"
        :src="screenshot"
        alt="Screenshot"
        class="webcam-stream__image"
      />
      <p v-else class="webcam-stream__hint">Noch kein Bild…</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'

const videoEl = ref<HTMLVideoElement | null>(null)
const canvasEl = ref<HTMLCanvasElement | null>(null)
const screenshot = ref<string>('')

let stream: MediaStream | null = null
let intervalId: number | null = null

onMounted(async () => {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    if (videoEl.value) {
      videoEl.value.srcObject = stream
    }

    intervalId = window.setInterval(() => {
      if (!videoEl.value || !canvasEl.value) return
      const canvas = canvasEl.value
      const video = videoEl.value

      const ctx = canvas.getContext('2d')
      if (!ctx) return

      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
      screenshot.value = canvas.toDataURL('image/png')
    }, 5000)
  } catch (err) {
    console.error('Webcam error:', err)
  }
})

onBeforeUnmount(() => {
  if (intervalId !== null) {
    window.clearInterval(intervalId)
  }
  if (stream) {
    stream.getTracks().forEach(t => t.stop())
  }
})
</script>

<style scoped>
.webcam-stream {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.webcam-stream__video {
  width: 100%;
  border-radius: 0.75rem;
  background: #020617;
}

.webcam-stream__canvas {
  display: none;
}

.webcam-stream__screenshot {
  font-size: 0.85rem;
}

.webcam-stream__hint {
  margin: 0 0 0.25rem;
  color: var(--text-muted);
}

.webcam-stream__image {
  max-width: 100%;
  border-radius: 0.5rem;
}
</style>
