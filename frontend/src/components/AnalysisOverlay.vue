<template>
  <Transition name="overlay-fade">
    <div
      v-if="visible"
      class="analysis-overlay"
      :style="{ '--overlay-top': topOffset + 'px' }"
      @click.self="onOverlayClick"
    >
      <canvas ref="canvasRef" class="analysis-overlay-canvas" />

      <div class="analysis-overlay-progress">
        <canvas ref="rooksCanvasRef" class="analysis-overlay-rooks" width="120" height="80" />
        <span class="analysis-overlay-text">正在分析...</span>
        <span class="analysis-overlay-percent">{{ progress }}%</span>
      </div>

      <div class="analysis-overlay-actions">
        <el-button type="primary" size="small" @click="$emit('dismiss')">
          后台分析
        </el-button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  progress: { type: Number, default: 0 },
  topOffset: { type: Number, default: 0 },
})

const emit = defineEmits(['dismiss'])

const canvasRef = ref(null)
const rooksCanvasRef = ref(null)

// ─── 棋子类型定义 ───
const PIECE_TYPES = [
  { type: 'K', white: '\u2654', black: '\u265A', weight: 1, wavelength: 120, amplitude: 1.0, whiteColor: [255, 215, 0], blackColor: [218, 165, 32] },
  { type: 'Q', white: '\u2655', black: '\u265B', weight: 1, wavelength: 100, amplitude: 0.9, whiteColor: [148, 0, 211], blackColor: [128, 0, 128] },
  { type: 'R', white: '\u2656', black: '\u265C', weight: 2, wavelength: 85, amplitude: 0.7, whiteColor: [30, 144, 255], blackColor: [0, 100, 200] },
  { type: 'B', white: '\u2657', black: '\u265D', weight: 2, wavelength: 75, amplitude: 0.65, whiteColor: [0, 206, 209], blackColor: [0, 139, 139] },
  { type: 'N', white: '\u2658', black: '\u265E', weight: 2, wavelength: 65, amplitude: 0.6, whiteColor: [50, 205, 50], blackColor: [34, 139, 34] },
  { type: 'P', white: '\u2659', black: '\u265F', weight: 8, wavelength: 50, amplitude: 0.4, whiteColor: [192, 192, 192], blackColor: [105, 105, 105] },
]

const totalWeight = PIECE_TYPES.reduce((s, p) => s + p.weight, 0)

// ─── 生命周期常量（ms） ───
const FADE_IN = 600
const DWELL = 3000
const FADE_OUT = 800
const PIECE_LIFETIME = FADE_IN + DWELL + FADE_OUT
const RIPPLE_DELAY = 300
const RIPPLE_FADEOUT = 800
const RIPPLE_LIFETIME = PIECE_LIFETIME + RIPPLE_DELAY + RIPPLE_FADEOUT
const WAVE_PERIOD = 1200
const MAX_PIECES = 5
const AUTO_INTERVAL = 2000
const MARGIN = 60

// ─── 状态 ───
let pieces = []
let animFrameId = null
let autoGenTimer = null
let resizeObserver = null

let mainCanvas = null
let mainCtx = null
let offCanvas = null
let offCtx = null
let canvasW = 0
let canvasH = 0
let dpr = 1
let downscale = 4

// ─── 两车追逐动画状态 ───
let rooksAnimId = null
let rooksState = {
  step: 0,
  stepTime: 0,
  stepInterval: 300, // 每步0.3s
  lastTime: 0,
  // 8步循环位置：
  // 0: 白(0,0) 黑(1,1) 初始
  // 1: 白(0,1) 黑(1,1) 白向下
  // 2: 白(0,1) 黑(1,0) 黑向上
  // 3: 白(1,1) 黑(1,0) 白向右
  // 4: 白(1,1) 黑(0,0) 黑向左
  // 5: 白(1,0) 黑(0,0) 白向上
  // 6: 白(1,0) 黑(0,1) 黑向下
  // 7: 白(0,0) 黑(0,1) 白向左
  // 8: 白(0,0) 黑(1,1) 黑向右，回到初始
  positions: [
    { white: { x: 0, y: 0 }, black: { x: 1, y: 1 } },
    { white: { x: 0, y: 1 }, black: { x: 1, y: 1 } },
    { white: { x: 0, y: 1 }, black: { x: 1, y: 0 } },
    { white: { x: 1, y: 1 }, black: { x: 1, y: 0 } },
    { white: { x: 1, y: 1 }, black: { x: 0, y: 0 } },
    { white: { x: 1, y: 0 }, black: { x: 0, y: 0 } },
    { white: { x: 1, y: 0 }, black: { x: 0, y: 1 } },
    { white: { x: 0, y: 0 }, black: { x: 0, y: 1 } },
  ],
}

// ─── 工具函数 ───
function randomPieceType() {
  let r = Math.random() * totalWeight
  for (const pt of PIECE_TYPES) {
    r -= pt.weight
    if (r <= 0) return pt
  }
  return PIECE_TYPES[PIECE_TYPES.length - 1]
}

function getPieceOpacity(age) {
  if (age < FADE_IN) return age / FADE_IN
  if (age < FADE_IN + DWELL) return 1
  if (age < PIECE_LIFETIME) return 1 - (age - FADE_IN - DWELL) / FADE_OUT
  return 0
}

function getEnvelope(age) {
  if (age < FADE_IN) return age / FADE_IN
  if (age < PIECE_LIFETIME) return 1
  if (age < PIECE_LIFETIME + RIPPLE_DELAY) return 1
  if (age < RIPPLE_LIFETIME) return 1 - (age - PIECE_LIFETIME - RIPPLE_DELAY) / RIPPLE_FADEOUT
  return 0
}

function isPieceAlive(age) {
  return age < PIECE_LIFETIME
}

function isRippleAlive(age) {
  return age < RIPPLE_LIFETIME
}

function getAliveCount() {
  const now = performance.now()
  return pieces.filter(p => isPieceAlive(now - p.createdAt)).length
}

function createPiece(x, y, forceReplace = false) {
  const aliveCount = getAliveCount()
  if (aliveCount >= MAX_PIECES) {
    if (!forceReplace) return
    // 对最早的存活棋子启动淡出（而非直接删除），保证视觉上的柔和过渡
    const now = performance.now()
    let oldestIdx = -1
    let oldestAge = -1
    for (let i = 0; i < pieces.length; i++) {
      const age = now - pieces[i].createdAt
      if (isPieceAlive(age) && age > oldestAge) {
        oldestAge = age
        oldestIdx = i
      }
    }
    if (oldestIdx >= 0) {
      // 将 createdAt 调整到「现在开始进入淡出阶段」的位置：
      // age = PIECE_LIFETIME - FADE_OUT  → 剩余 0..FADE_OUT ms 完成淡出
      pieces[oldestIdx].createdAt = now - (PIECE_LIFETIME - FADE_OUT)
    }
  }

  const pt = randomPieceType()
  const isWhite = Math.random() < 0.5
  pieces.push({
    x,
    y,
    char: isWhite ? pt.white : pt.black,
    isWhite,
    wavelength: pt.wavelength,
    amplitude: pt.amplitude,
    color: isWhite ? pt.whiteColor : pt.blackColor,
    createdAt: performance.now(),
  })
}

function generateRandomPiece() {
  if (getAliveCount() >= MAX_PIECES) return
  const margin = MARGIN
  const x = margin + Math.random() * (canvasW / dpr - 2 * margin)
  const y = margin + Math.random() * (canvasH / dpr - 2 * margin)
  createPiece(x, y)
}

function onOverlayClick(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const x = e.clientX - rect.left
  const y = e.clientY - rect.top
  createPiece(x, y, true)
}

// ─── Canvas 尺寸管理 ───
function resizeCanvas() {
  const el = canvasRef.value
  if (!el) return
  const parent = el.parentElement
  if (!parent) return

  dpr = window.devicePixelRatio || 1
  const w = parent.clientWidth
  const h = parent.clientHeight

  el.width = w * dpr
  el.height = h * dpr
  el.style.width = w + 'px'
  el.style.height = h + 'px'

  mainCanvas = el
  mainCtx = el.getContext('2d')
  canvasW = el.width
  canvasH = el.height

  downscale = w < 768 ? 6 : 4
  const offW = Math.ceil(canvasW / downscale)
  const offH = Math.ceil(canvasH / downscale)

  offCanvas = document.createElement('canvas')
  offCanvas.width = offW
  offCanvas.height = offH
  offCtx = offCanvas.getContext('2d')
}

// ─── 渲染循环 ───
function render() {
  if (!mainCtx || !offCtx) return

  const now = performance.now()

  // 清理过期棋子
  pieces = pieces.filter(p => isRippleAlive(now - p.createdAt))

  // 清空
  mainCtx.clearRect(0, 0, canvasW, canvasH)
  offCtx.clearRect(0, 0, offCanvas.width, offCanvas.height)

  // ─── 计算波纹干涉场 ───
  const offW = offCanvas.width
  const offH = offCanvas.height
  const imageData = offCtx.createImageData(offW, offH)
  const data = imageData.data

  const omega = (2 * Math.PI) / WAVE_PERIOD
  const brightnessFactor = 0.7

  for (let py = 0; py < offH; py++) {
    for (let px = 0; px < offW; px++) {
      let totalAmp = 0
      let weightedR = 0
      let weightedG = 0
      let weightedB = 0
      let totalWeight_ = 0

      for (const piece of pieces) {
        const age = now - piece.createdAt
        const envelope = getEnvelope(age)
        if (envelope <= 0) continue

        const sx = (piece.x * dpr) / downscale
        const sy = (piece.y * dpr) / downscale
        const dx = px - sx
        const dy = py - sy
        const rPixels = Math.sqrt(dx * dx + dy * dy)
        const rReal = rPixels * downscale / dpr

        const maxR = piece.wavelength * 6
        if (rReal > maxR) continue

        const k = (2 * Math.PI) / piece.wavelength
        const amp = piece.amplitude / Math.sqrt(rReal + 1) * Math.sin(k * rReal - omega * now) * envelope

        totalAmp += amp
        const absAmp = Math.abs(amp)
        weightedR += absAmp * piece.color[0]
        weightedG += absAmp * piece.color[1]
        weightedB += absAmp * piece.color[2]
        totalWeight_ += absAmp
      }

      if (totalWeight_ > 0) {
        weightedR /= totalWeight_
        weightedG /= totalWeight_
        weightedB /= totalWeight_
      }

      const idx = (py * offW + px) * 4
      if (totalAmp > 0) {
        const intensity = Math.min(1, totalAmp * brightnessFactor)
        data[idx] = weightedR
        data[idx + 1] = weightedG
        data[idx + 2] = weightedB
        data[idx + 3] = Math.round(intensity * 255)
      } else if (totalAmp < 0) {
        const intensity = Math.min(1, Math.abs(totalAmp) * brightnessFactor * 0.6)
        data[idx] = 0
        data[idx + 1] = 0
        data[idx + 2] = 0
        data[idx + 3] = Math.round(intensity * 200)
      }
    }
  }

  offCtx.putImageData(imageData, 0, 0)

  // 绘制波纹到主 Canvas
  mainCtx.imageSmoothingEnabled = true
  mainCtx.imageSmoothingQuality = 'high'
  mainCtx.drawImage(offCanvas, 0, 0, canvasW, canvasH)

  // ─── 绘制棋子 ───
  const fontSize = (canvasW / dpr < 768 ? 40 : 56) * dpr
  mainCtx.font = `${fontSize}px 'Segoe UI Symbol', 'Apple Color Emoji', sans-serif`
  mainCtx.textAlign = 'center'
  mainCtx.textBaseline = 'middle'

  for (const piece of pieces) {
    const age = now - piece.createdAt
    if (!isPieceAlive(age)) continue
    const opacity = getPieceOpacity(age)
    if (opacity <= 0) continue

    const cx = piece.x * dpr
    const cy = piece.y * dpr

    mainCtx.save()
    mainCtx.globalAlpha = opacity

    if (piece.isWhite) {
      mainCtx.fillStyle = '#FFFFFF'
      mainCtx.strokeStyle = '#333333'
      mainCtx.lineWidth = 2 * dpr
      mainCtx.strokeText(piece.char, cx, cy)
      mainCtx.fillText(piece.char, cx, cy)
    } else {
      mainCtx.fillStyle = '#1a1a1a'
      mainCtx.fillText(piece.char, cx, cy)
    }

    mainCtx.restore()
  }

  animFrameId = requestAnimationFrame(render)
}

// ─── 两车追逐动画 ───
function animateRooks() {
  const canvas = rooksCanvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')
  const w = 120
  const h = 80
  const cellW = w / 2
  const cellH = h / 2
  const now = performance.now()

  const rs = rooksState
  const dt = now - rs.lastTime
  rs.lastTime = now

  // 更新步进计时
  rs.stepTime += dt
  if (rs.stepTime >= rs.stepInterval) {
    rs.stepTime = 0
    rs.step = (rs.step + 1) % 8
  }

  // 当前步和下一步的位置（用于平滑插值）
  const curPos = rs.positions[rs.step]
  const nextPos = rs.positions[(rs.step + 1) % 8]
  const t = Math.min(rs.stepTime / rs.stepInterval, 1)

  // 平滑插值位置
  const whiteX = curPos.white.x + (nextPos.white.x - curPos.white.x) * t
  const whiteY = curPos.white.y + (nextPos.white.y - curPos.white.y) * t
  const blackX = curPos.black.x + (nextPos.black.x - curPos.black.x) * t
  const blackY = curPos.black.y + (nextPos.black.y - curPos.black.y) * t

  // 绘制
  ctx.clearRect(0, 0, w, h)

  // 绘制白车
  ctx.font = '32px "Segoe UI Symbol", "Apple Color Emoji", sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillStyle = '#FFFFFF'
  ctx.strokeStyle = '#333333'
  ctx.lineWidth = 1.5
  const wcx = whiteX * cellW + cellW / 2
  const wcy = whiteY * cellH + cellH / 2
  ctx.strokeText('\u2656', wcx, wcy)
  ctx.fillText('\u2656', wcx, wcy)

  // 绘制黑车
  ctx.fillStyle = '#1a1a1a'
  const bcx = blackX * cellW + cellW / 2
  const bcy = blackY * cellH + cellH / 2
  ctx.fillText('\u265C', bcx, bcy)

  rooksAnimId = requestAnimationFrame(animateRooks)
}

// ─── 生命周期 ───
function startAnimation() {
  if (animFrameId) return
  resizeCanvas()
  animFrameId = requestAnimationFrame(render)

  autoGenTimer = setInterval(() => {
    generateRandomPiece()
  }, AUTO_INTERVAL)

  nextTick(() => {
    generateRandomPiece()
  })

  // 启动两车追逐动画
  rooksState.lastTime = performance.now()
  rooksAnimId = requestAnimationFrame(animateRooks)
}

function stopAnimation() {
  if (animFrameId) {
    cancelAnimationFrame(animFrameId)
    animFrameId = null
  }
  if (autoGenTimer) {
    clearInterval(autoGenTimer)
    autoGenTimer = null
  }
  if (rooksAnimId) {
    cancelAnimationFrame(rooksAnimId)
    rooksAnimId = null
  }
  pieces = []
  if (mainCtx) {
    mainCtx.clearRect(0, 0, canvasW, canvasH)
  }
}

watch(() => props.visible, (val) => {
  if (val) {
    nextTick(() => startAnimation())
  } else {
    stopAnimation()
  }
})

onMounted(() => {
  if (props.visible) {
    nextTick(() => startAnimation())
  }

  const el = canvasRef.value
  if (el && el.parentElement) {
    resizeObserver = new ResizeObserver(() => {
      resizeCanvas()
    })
    resizeObserver.observe(el.parentElement)
  }
})

onUnmounted(() => {
  stopAnimation()
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
})
</script>

<style scoped lang="scss">
.analysis-overlay {
  position: absolute;
  top: var(--overlay-top, 0);
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 50;
  backdrop-filter: blur(12px) saturate(1.2);
  -webkit-backdrop-filter: blur(12px) saturate(1.2);
  background: rgba(255, 255, 255, 0.35);
  cursor: pointer;
  overflow: hidden;

  @supports not (backdrop-filter: blur(12px)) {
    background: rgba(245, 247, 250, 0.92);
  }
}

html.dark .analysis-overlay {
  background: rgba(20, 20, 20, 0.45);

  @supports not (backdrop-filter: blur(12px)) {
    background: rgba(30, 30, 30, 0.92);
  }
}

.analysis-overlay-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.analysis-overlay-progress {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  pointer-events: none;
  z-index: 2;
}

.analysis-overlay-rooks {
  width: 120px;
  height: 80px;
}

.analysis-overlay-text {
  font-size: 18px;
  font-weight: 500;
  color: var(--text-color, #333);
  letter-spacing: 2px;

  html.dark & {
    color: var(--text-color, #e0e0e0);
  }
}

.analysis-overlay-percent {
  font-size: 28px;
  font-weight: 700;
  color: var(--el-color-primary, #409eff);
  font-variant-numeric: tabular-nums;
}

.analysis-overlay-actions {
  position: absolute;
  top: 16px;
  right: 16px;
  z-index: 3;
}

/* 淡入淡出过渡 */
.overlay-fade-enter-active,
.overlay-fade-leave-active {
  transition: opacity 0.4s ease;
}

.overlay-fade-enter-from,
.overlay-fade-leave-to {
  opacity: 0;
}
</style>
