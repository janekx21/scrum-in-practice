<script setup lang="ts">
import { useWebSocket, useIntervalFn, useRafFn } from '@vueuse/core'
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import MultiModelScene from '@/components/MultiModelScene.vue'
import { fetchAllStrams, startStream } from '@/api/threeApi'

const { status, data, send, open, close, ws } = useWebSocket(
  `ws:/localhost:8765/ws`, {
    autoReconnect: true,
  }
)
const model_bytes = ref<{data: ArrayBuffer, time: number}[]>([])
const points = shallowRef<{data: [x: number, y: number, z: number], time: number}[]>([])
const selectedChannel = ref<string | null>(null)
const allStreams = ref<string[]>([])

const firstTime = ref(0)
const playheadTime = ref(0)
const playback = ref<"live" | "pause" | "play" | "ff" | "fb" | "ff" | "ff3x" |"fb3x">("live")

onMounted(() => open())

watch(status, () => {
  console.log(status)
})

watch(data, () => {
  const time = Date.now()
  if (firstTime.value == 0) {
    firstTime.value = time
    playheadTime.value = time
  }
  if (playback.value == "live") {
    playheadTime.value = time
  }

  if (data.value instanceof Blob) {
    data.value.arrayBuffer().then((b) => {

      model_bytes.value.push({
        data: b, time: time
      })
    })
  } else {
    const pose = JSON.parse(data.value) as {poses: number[][]}
    for(const p of pose.poses) {
      points.value.push({
        data: p as [number, number, number], time: time
      })
    }
  }
})

function connectToStream(channel: string) {
  selectedChannel.value = channel
  startStream(channel)
}

onMounted(() => {
   fetchAllStrams().then((s) => {
    allStreams.value  = s
  })
})

watch(selectedChannel, () => {
  if (selectedChannel.value == null) {
    model_bytes.value = []
    points.value = []
    close()
  }
})

onUnmounted(() => {
  close()
})

const cut_model_bytes = computed(() => {
  return model_bytes.value.filter(({time}) => time <= playheadTime.value).map(({data}) => data)
})

const cut_points = computed(() => {
  return points.value.filter(({time}) => time <= playheadTime.value).map(({data}) => data)
})

function pause() {
  playback.value = "pause"
}

function play() {
  playback.value = "play"
}
function fastForward() {
  playback.value = "ff"
}
function fastForward3x() {
  playback.value = "ff3x"
}
function fastBackward() {
  playback.value = "fb"
}
function fastBackward3x() {
  playback.value = "fb3x"
}


useRafFn(({delta}) => {
  if (playback.value == "play") {
    playheadTime.value += delta
    if (playheadTime.value >= Date.now()) {
      playheadTime.value = Date.now()
      playback.value = "live"
    }
  }

  if (playback.value == "ff") {
    playheadTime.value += delta * 2
    if (playheadTime.value >= Date.now()) {
      playheadTime.value = Date.now()
      playback.value = "live"
    }
  }

  if (playback.value == "ff3x") {
    playheadTime.value += delta * 3
    if (playheadTime.value >= Date.now()) {
      playheadTime.value = Date.now()
      playback.value = "live"
    }
  }

  if (playback.value == "fb") {
    playheadTime.value -= delta * 2
    if (playheadTime.value <= firstTime.value) {
      playheadTime.value = firstTime.value
      playback.value = "pause"
    }
  }

  if (playback.value == "fb3x") {
    playheadTime.value -= delta * 3
    if (playheadTime.value <= firstTime.value) {
      playheadTime.value = firstTime.value
      playback.value = "pause"
    }
  }
})



</script>

<template>
  <div class="livestream-container bg-black position-relative" style="height: calc(100vh - 56px);">

    <!-- TACTICAL COMMAND PANEL -->
    <div class="position-absolute top-0 start-0 m-3 z-3" style="width: 300px;">
      <div class="card bg-dark text-white border-0 shadow-lg tactical-card">
        <div class="card-body p-3">

          <!-- Status Header -->
          <div class="d-flex align-items-center justify-content-between mb-3">
            <div class="d-flex align-items-center">
              <span :class="['status-dot me-2', playback === 'live' ? 'live-red' : 'playback-blue']"></span>
              <h6 class="text-uppercase fw-900 m-0 tracking-tighter">
                {{ playback === 'live' ? 'EVOK Live Stream' : 'EVOK Playback' }}
              </h6>
            </div>
            <div class="frame-counter">{{ frame }}</div>
          </div>

          <!-- Channel Selection State -->
          <div v-if="!selectedChannel">
            <div class="list-group list-group-flush border-top border-secondary mt-2">
              <button
                v-for="ch in allStreams"
                :key="ch"
                @click="connectToStream(ch)"
                class="list-group-item list-group-item-action bg-transparent text-white border-secondary small py-3"
              >
                📡 Initialize: {{ ch }}
              </button>
            </div>
          </div>

          <!-- Active Controls State -->
          <div v-else>
            <div class="info-strip mb-3">
              <div class="d-flex justify-content-between mb-1">
                <span class="text-muted extra-small">IDENTIFIER</span>
                <span class="text-success extra-small fw-bold">{{ selectedChannel }}</span>
              </div>
              <div class="d-flex justify-content-between">
                <span class="text-muted extra-small">LATENCY</span>
                <span class="text-white extra-small">OPTIMAL</span>
              </div>
            </div>

            <!-- TACTICAL PLAYBACK BAR -->
            <div class="playback-bar d-flex align-items-center justify-content-between mb-3">
              <button @click="fastBackward3x()" class="pb-btn" :class="{active: playback == 'fb3x'}" title="Backward 3x">
                <span class="speed-label">3x</span><span class="icon">⏪</span>
              </button>

              <button @click="fastBackward()" class="pb-btn" :class="{active: playback == 'fb'}" title="Backward 1x">
                <span class="icon">⏪</span>
              </button>

              <button v-if="playback != 'pause'" @click="pause()" class="pb-btn main-action" title="Pause">
                <span class="icon">⏸</span>
              </button>
              <button v-else @click="play()" class="pb-btn main-action" title="Play">
                <span class="icon">▶</span>
              </button>

              <button @click="fastForward()" class="pb-btn" :class="{active: playback == 'ff'}" title="Forward 1x">
                <span class="icon">⏩</span>
              </button>

              <button @click="fastForward3x()" class="pb-btn" :class="{active: playback == 'ff3x'}" title="Forward 3x">
                <span class="icon">⏩</span><span class="speed-label">3x</span>
              </button>
            </div>

            <RouterLink to="/" class="btn btn-disconnect w-100 text-uppercase fw-bold pt-2 pb-2">
              Terminate Connection
            </RouterLink>
          </div>
        </div>
      </div>
    </div>

    <!-- 3D Viewport -->
    <div v-if="selectedChannel" class="w-100 h-100">
      <MultiModelScene :path_points="cut_points"  :model_bytes="cut_model_bytes" :model_paths="[]"/>
    </div>

    <div v-else class="w-100 h-100 d-flex align-items-center justify-content-center text-secondary">
      <div class="text-center opacity-50">
        <div class="spinner-grow text-secondary mb-3" role="status"></div>
        <p class="small tracking-widest text-uppercase">Awaiting Secure Link</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.z-3 { z-index: 1050; }
.fw-900 { font-weight: 900; }
.extra-small { font-size: 0.6rem; letter-spacing: 0.05rem; }
.tracking-tighter { letter-spacing: -0.02rem; }

.tactical-card {
  background: rgba(15, 23, 42, 0.9) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.live-red {
  background-color: #ef4444;
  box-shadow: 0 0 10px #ef4444;
  animation: pulse-red 2s infinite;
}

.playback-blue {
  background-color: #3b82f6;
  box-shadow: 0 0 10px #3b82f6;
}

.frame-counter {
  font-family: 'Courier New', Courier, monospace;
  background: rgba(0,0,0,0.5);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #fbbf24;
  border: 1px solid rgba(255,255,255,0.1);
}

.info-strip {
  background: rgba(0,0,0,0.3);
  padding: 8px 12px;
  border-radius: 6px;
  border-left: 3px solid #10b981;
}

/* SLEEK PLAYBACK BAR */
.playback-bar {
  background: rgba(255, 255, 255, 0.05);
  padding: 5px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.pb-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex: 1;
  border-radius: 6px;
  height: 40px;
}

.pb-btn .icon { font-size: 1rem; }
.pb-btn .speed-label { font-size: 0.5rem; font-weight: 800; margin-bottom: -4px; }

.pb-btn:hover { color: #fff; background: rgba(255,255,255,0.1); }
.pb-btn.active { color: #fbbf24; background: rgba(251, 191, 36, 0.1); }

.pb-btn.main-action {
  background: #facc15;
  color: #000;
  border-radius: 8px;
  transform: scale(1.05);
}

.pb-btn.main-action:hover {
  background: #eab308;
  transform: scale(1.1);
}

.btn-disconnect {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.15);
  color: rgba(255,255,255,0.6);
  font-size: 0.7rem;
  transition: all 0.3s;
}

.btn-disconnect:hover {
  background: #ef4444;
  border-color: #ef4444;
  color: white;
}

@keyframes pulse-red {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.2); opacity: 0.5; }
  100% { transform: scale(1); opacity: 1; }
}
</style>
