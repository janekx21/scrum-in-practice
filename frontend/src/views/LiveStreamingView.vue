<script setup lang="ts">
import { useWebSocket, useIntervalFn } from '@vueuse/core'
import { computed, onMounted, onUnmounted, ref, shallowRef, watch } from 'vue'
import MultiModelScene from '@/components/MultiModelScene.vue'
import { fetchAllStrams, startStream } from '@/api/threeApi'


const toggleStream = () => {
  alert("Attempting to connect to EVOK hardware...")
}

const { status, data, send, open, close, ws } = useWebSocket(
  `ws:/localhost:8765/ws`, {
    autoReconnect: true,
  }
)
onMounted(() => open())
watch(status, () => {
  console.log(status)
})
watch(data, () => {
  if (data.value instanceof Blob) {
    data.value.arrayBuffer().then((b) => {
      model_bytes.value.push(b)
      if (playback.value == "live") {
        frame.value += 1
      }
    })
  } else {
    const pose = JSON.parse(data.value) as {poses: number[][]}
    points.value = [...points.value, ...pose.poses]
    console.log(points.value)
  }
})

const model_bytes = ref<ArrayBuffer[]>([])
const points = shallowRef<number[][]>([[0,0,0], [0,0,1]])
const selectedChannel = ref<string | null>(null)
const allStreams = ref<string[]>([])

const frame = ref(0)
const playback = ref<"live" | "pause" | "play" | "ff" | "fb" | "ff" | "ff3x" |"fb3x">("live")

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
    close()
  }
})

onUnmounted(() => {
  close()
})

const cut_model_bytes = computed(() => {
  return model_bytes.value.slice(0, frame.value)
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


useIntervalFn(() => {
  if (playback.value == "play") {
    frame.value += 1
    if (frame.value >= model_bytes.value.length) {
      frame.value = model_bytes.value.length
      playback.value = "live"
    }
  }
}, 50);

useIntervalFn(() => {
  if (playback.value == "fb") {
    frame.value -= 2
    if (frame.value <= 0) {
      frame.value = 0
      playback.value = "pause"
    }
  }
}, 10);
useIntervalFn(() => {
  if (playback.value == "fb3x") {
    frame.value -= 3
    if (frame.value <= 0) {
      frame.value = 0
      playback.value = "pause"
    }
  }
}, 10);

useIntervalFn(() => {
  if (playback.value == "ff") {
    frame.value += 2
    if (frame.value >= model_bytes.value.length) {
      frame.value = model_bytes.value.length
      playback.value = "live"
    }
  }
}, 10);

useIntervalFn(() => {
  if (playback.value == "ff3x") {
    frame.value += 3
    if (frame.value >= model_bytes.value.length) {
      frame.value = model_bytes.value.length
      playback.value = "live"
    }
  }
}, 10);

</script>
<template>

<div class="livestream-container bg-black position-relative" style="height: calc(100vh - 56px);">

    <!-- UI Overlay Controls -->
    <div class="position-absolute top-0 start-0 m-3 z-3" style="width: 250px;">
      <div class="card bg-dark text-white border-secondary shadow">
        <div class="card-body">
          <h5 v-if="playback == 'live'" class="text-danger fw-bold mb-3">● EVOK LIVE</h5>
          <h5 v-else class="text-secondary fw-bold mb-3">EVOK PLAYBACK</h5>

          <div v-if="!selectedChannel">
            <div class="list-group">
              <button
                v-for="ch in allStreams"
                :key="ch"
                @click="connectToStream(ch)"
                class="list-group-item list-group-item-action list-group-item-dark small"
              >
                Connect to {{ ch }}
              </button>
            </div>
          </div>

          <div v-else>
            <p class="small text-success mb-1">Active: {{ selectedChannel }}</p>
            <p class="extra-small text-muted mb-3">Frame ID: {{ frame }}</p>
            <RouterLink to="/" class="btn btn-outline-light btn-sm w-100"r>
              Disconnect
            </RouterLink>
          </div>
        </div>
      </div>
      <div class="card bg-dark text-white border-secondary shadow mt-4">
        <div class="card-body d-flex">
            <button @click="fastBackward3x()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'fb3x'}">⏪</button>
            <button @click="fastBackward()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'fb'}" >⏪</button>
            <button v-if="playback != 'pause'" @click="pause()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'play'}">⏸️</button>
            <button v-else @click="play()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'pause'}">▶️</button>
            <button @click="fastForward()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'ff'}">⏩</button>
            <button @click="fastForward3x()" class="btn btn-outline p-1" :class="{'btn-primary': playback == 'ff3x'}">⏩</button>
            <div class="border rounded border-secondary p-1 ml-2"> {{ frame }} </div>
        </div>
      </div>
    </div>


    <!-- 3D Viewport -->
    <div v-if="selectedChannel" class="w-100 h-100">
      <MultiModelScene :path_points="points"  :model_bytes="cut_model_bytes" :model_paths="[]"/>
    </div>

    <div v-else class="w-100 h-100 d-flex align-items-center justify-content-center text-secondary">
      <p>Select an EVOK channel to start livestreaming</p>
    </div>
  </div>
</template>

<style scoped>
.z-3 { z-index: 1050; }
.extra-small { font-size: 0.75rem; }
</style>
