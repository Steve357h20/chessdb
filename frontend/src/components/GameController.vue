<template>
  <div class="game-controller" @keydown="onKeyDown" tabindex="0">
    <div class="gc-main-row">
      <el-button-group class="gc-transport">
        <el-button :icon="DArrowLeft" @click="emit('first')" :disabled="currentMove <= 0" size="small" title="跳到开头 (Home)" />
        <el-button :icon="ArrowLeft" @click="emit('prev')" :disabled="currentMove <= 0" size="small" title="后退一步 (←)" />
        <el-button @click="togglePlay" size="small" :type="isPlaying ? 'warning' : 'primary'" :title="isPlaying ? '暂停 (空格)' : '播放 (空格)'">
          <el-icon><component :is="isPlaying ? VideoPause : VideoPlay" /></el-icon>
        </el-button>
        <el-button :icon="ArrowRight" @click="emit('next')" :disabled="currentMove >= totalMoves" size="small" title="前进一步 (→)" />
        <el-button :icon="DArrowRight" @click="emit('last')" :disabled="currentMove >= totalMoves" size="small" title="跳到结尾 (End)" />
      </el-button-group>

      <div class="gc-speed">
        <span class="gc-speed-label">速度</span>
        <el-select v-model="selectedSpeed" size="small" style="width: 80px" @change="onSpeedChange">
          <el-option v-for="s in speedOptions" :key="s.value" :label="s.label" :value="s.value" />
        </el-select>
      </div>
    </div>

    <div class="gc-progress-row">
      <span class="gc-move-counter">{{ currentMove }} / {{ totalMoves }}</span>
      <el-slider
        v-model="sliderValue"
        :min="0"
        :max="totalMoves"
        :step="1"
        :show-tooltip="false"
        size="small"
        class="gc-slider"
        @change="onSliderChange"
      />
    </div>

    <div class="gc-jump-row">
      <el-button size="small" @click="emit('first')" :disabled="currentMove <= 0">跳到开头</el-button>
      <el-button size="small" @click="jumpBackward5" :disabled="currentMove <= 0">后退5步</el-button>
      <el-button size="small" @click="jumpForward5" :disabled="currentMove >= totalMoves">前进5步</el-button>
      <el-button size="small" @click="emit('last')" :disabled="currentMove >= totalMoves">跳到结尾</el-button>
    </div>

    <div v-if="turnInfo" class="gc-status-row">
      <span class="gc-turn-indicator" :class="turnInfo === 'white' ? 'turn-white' : 'turn-black'" />
      <span class="gc-turn-text">{{ turnInfo === 'white' ? '白方走棋' : '黑方走棋' }}</span>
      <span v-if="evalDisplay" class="gc-eval-display" :class="evalClass">{{ evalDisplay }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ArrowLeft, ArrowRight, DArrowLeft, DArrowRight, VideoPlay, VideoPause } from '@element-plus/icons-vue'

const props = defineProps({
  currentMove: { type: Number, default: 0 },
  totalMoves: { type: Number, default: 0 },
  isPlaying: { type: Boolean, default: false },
  playSpeed: { type: Number, default: 1000 },
  turnInfo: { type: String, default: null },
  evalScore: { type: Number, default: null },
  playerColor: { type: String, default: 'w' },
})

const emit = defineEmits(['play', 'pause', 'next', 'prev', 'first', 'last', 'jump-to', 'speed-change'])

const speedOptions = [
  { label: '0.5x', value: 2000 },
  { label: '1x', value: 1000 },
  { label: '2x', value: 500 },
  { label: '5x', value: 200 },
]

const selectedSpeed = ref(props.playSpeed)
const sliderValue = ref(props.currentMove)

let playTimer = null

watch(() => props.currentMove, (val) => {
  sliderValue.value = val
})

watch(() => props.playSpeed, (val) => {
  selectedSpeed.value = val
  if (props.isPlaying) {
    stopAutoPlay()
    startAutoPlay()
  }
})

watch(() => props.isPlaying, (val) => {
  if (val) {
    startAutoPlay()
  } else {
    stopAutoPlay()
  }
})

const evalDisplay = computed(() => {
  if (props.evalScore == null) return null
  const val = props.evalScore
  if (Math.abs(val) >= 100) {
    const mateDist = Math.round(Math.abs(val) - 100)
    if (mateDist <= 0) return val > 0 ? '+M1' : '-M1'
    return val > 0 ? `+M${mateDist}` : `-M${mateDist}`
  }
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(1)}`
})

const evalClass = computed(() => {
  if (props.evalScore == null) return ''
  if (props.evalScore > 0.5) return 'eval-positive'
  if (props.evalScore < -0.5) return 'eval-negative'
  return 'eval-neutral'
})

function togglePlay() {
  if (props.isPlaying) {
    emit('pause')
  } else {
    if (props.currentMove >= props.totalMoves) {
      emit('first')
    }
    emit('play')
  }
}

function startAutoPlay() {
  stopAutoPlay()
  playTimer = setInterval(() => {
    if (props.currentMove < props.totalMoves) {
      emit('next')
    } else {
      emit('pause')
    }
  }, props.playSpeed)
}

function stopAutoPlay() {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

function onSpeedChange(val) {
  emit('speed-change', val)
}

function onSliderChange(val) {
  emit('jump-to', val)
}

function jumpBackward5() {
  const target = Math.max(0, props.currentMove - 5)
  emit('jump-to', target)
}

function jumpForward5() {
  const target = Math.min(props.totalMoves, props.currentMove + 5)
  emit('jump-to', target)
}

function onKeyDown(e) {
  if (e.key === ' ' || e.code === 'Space') {
    e.preventDefault()
    togglePlay()
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault()
    emit('prev')
  } else if (e.key === 'ArrowRight') {
    e.preventDefault()
    emit('next')
  } else if (e.key === 'Home') {
    e.preventDefault()
    emit('first')
  } else if (e.key === 'End') {
    e.preventDefault()
    emit('last')
  }
}

onMounted(() => {
  if (props.isPlaying) {
    startAutoPlay()
  }
})

onUnmounted(() => {
  stopAutoPlay()
})
</script>

<style scoped>
.game-controller {
  background: var(--card-bg);
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px 16px;
  outline: none;
  user-select: none;
}

.game-controller:focus {
  border-color: #409eff;
}

.gc-main-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.gc-transport {
  flex-shrink: 0;
}

.gc-speed {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.gc-speed-label {
  font-size: 13px;
  color: var(--text-color-regular);
}

.gc-progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.gc-move-counter {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color);
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: nowrap;
  min-width: 60px;
  text-align: right;
}

.gc-slider {
  flex: 1;
}

.gc-jump-row {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.gc-jump-row .el-button {
  flex: 1;
}

.gc-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.gc-turn-indicator {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  border: 2px solid #999;
  flex-shrink: 0;
}

.turn-white {
  background-color: #fff;
  border-color: #ccc;
}

.turn-black {
  background-color: #333;
  border-color: #333;
}

.gc-turn-text {
  font-size: 13px;
  color: var(--text-color-regular);
}

.gc-eval-display {
  margin-left: auto;
  font-size: 13px;
  font-weight: 700;
  font-family: 'Consolas', 'Monaco', monospace;
}

.eval-positive { color: #409eff; }
.eval-negative { color: #f56c6c; }
.eval-neutral { color: var(--text-color-secondary); }
</style>
