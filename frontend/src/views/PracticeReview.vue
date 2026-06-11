<template>
  <div class="practice-review-page">
    <div v-if="loading" class="pr-loading" v-loading="true" />

    <template v-else-if="record">
      <div ref="prHeaderRef" class="pr-header">
        <el-button text @click="$router.push('/practice/history')">
          <el-icon><ArrowLeft /></el-icon> 返回历史
        </el-button>
        <div class="pr-header-info">
          <el-tag :type="modeTagType(record.mode)" size="small">{{ modeLabel(record.mode) }}</el-tag>
          <el-tag size="small">{{ difficultyLabel(record.difficulty) }}</el-tag>
          <span class="pr-header-item">执棋：{{ record.user_color === 'w' ? '白方' : '黑方' }}</span>
          <span class="pr-header-item">结果：<strong :class="resultClass">{{ resultLabel }}</strong></span>
          <span class="pr-header-item">{{ record.total_moves }} 步</span>
          <span class="pr-header-item">提示 {{ record.hints_used }} 次</span>
          <span class="pr-header-item">悔棋 {{ record.undo_count }} 次</span>
        </div>
        <div class="pr-header-actions">
          <el-button
            v-if="!analyzing && !hasAnalysis"
            size="small"
            type="primary"
            @click="startAnalysis"
          >AI 分析</el-button>
          <el-button
            v-if="analyzing"
            size="small"
            type="warning"
            loading
          >分析中 {{ analysisProgress }}%</el-button>
          <el-button
            v-if="!analyzing && hasAnalysis"
            size="small"
            type="success"
          >已分析</el-button>
        </div>
      </div>

      <div class="pr-body">
        <div class="pr-left-panel">
          <div class="pr-info-section">
            <h3>对局信息</h3>
            <div class="pr-info-row">
              <span class="pr-info-label">模式</span>
              <span class="pr-info-value">{{ modeLabel(record.mode) }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">难度</span>
              <span class="pr-info-value">{{ difficultyLabel(record.difficulty) }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">执棋</span>
              <span class="pr-info-value">{{ record.user_color === 'w' ? '白方' : '黑方' }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">结果</span>
              <span class="pr-info-value" :class="resultClass">{{ resultLabel }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">总步数</span>
              <span class="pr-info-value">{{ record.total_moves }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">提示次数</span>
              <span class="pr-info-value">{{ record.hints_used }}</span>
            </div>
            <div class="pr-info-row">
              <span class="pr-info-label">悔棋次数</span>
              <span class="pr-info-value">{{ record.undo_count }}</span>
            </div>
            <div v-if="record.duration_seconds" class="pr-info-row">
              <span class="pr-info-label">用时</span>
              <span class="pr-info-value">{{ formatDuration(record.duration_seconds) }}</span>
            </div>
            <div v-if="record.created_at" class="pr-info-row">
              <span class="pr-info-label">日期</span>
              <span class="pr-info-value">{{ formatDate(record.created_at) }}</span>
            </div>
          </div>

          <div v-if="hasAnalysis" class="pr-eval-section">
            <h3>当前评价</h3>
            <MoveEvaluation :evaluation="currentMoveEval" :player-color="record.user_color" />
          </div>

          <div v-if="hasAnalysis && currentBestMove" class="pr-suggestion-section">
            <h3>AI 建议</h3>
            <div class="pr-suggestion-item">
              <span class="pr-suggestion-label">最佳着法</span>
              <span class="pr-suggestion-value">{{ currentBestMove }}</span>
            </div>
            <div v-if="currentPv" class="pr-suggestion-item">
              <span class="pr-suggestion-label">预测续着</span>
              <span class="pr-suggestion-value">{{ currentPv }}</span>
            </div>
          </div>
        </div>

        <div class="pr-center-panel">
          <ChessBoard
            :fen="currentFen"
            :last-move="currentLastMove"
            :orientation="boardOrientation"
            :interactive="false"
            :show-coordinates="true"
            :board-size="boardSize"
            :move-annotation="currentAnnotation"
          />
          <div class="pr-controller">
            <GameController
              :current-move="currentHalfMove"
              :total-moves="totalHalfMoves"
              :is-playing="isPlaying"
              :play-speed="playSpeed"
              :turn-info="currentTurn"
              :eval-score="currentEvalScore"
              :player-color="record.user_color"
              @play="isPlaying = true"
              @pause="isPlaying = false"
              @next="goNext"
              @prev="goPrev"
              @first="goFirst"
              @last="goLast"
              @jump-to="jumpTo"
              @speed-change="playSpeed = $event"
            />
          </div>
        </div>

        <div class="pr-right-panel">
          <div v-if="hasAnalysis" class="pr-chart-section">
            <h3>胜率走势</h3>
            <WinRateChart
              :analysis-data="analysisData"
              :current-move="currentHalfMove"
              :player-color="record.user_color"
              :height="180"
              @move-select="onChartMoveSelect"
            />
          </div>

          <div class="pr-moves-section">
            <h3>着法列表</h3>
            <MoveList
              :moves="displayMoves"
              :current-move="currentHalfMove"
              :show-evaluation="hasAnalysis"
              @move-click="onMoveListClick"
            />
          </div>
        </div>
      </div>
    </template>

    <AnalysisOverlay
      v-if="record"
      :visible="analyzing && overlayVisible"
      :progress="analysisProgress"
      :top-offset="overlayTopOffset"
      @dismiss="dismissOverlay"
    />

    <div v-else class="pr-empty">
      <el-empty description="未找到练习记录">
        <el-button type="primary" @click="$router.push('/practice')">返回练习</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ArrowLeft } from '@element-plus/icons-vue'
import { Chess } from 'chess.js'
import { getPracticeDetail, startPracticeAnalysis, getPracticeAnalysisStatus, getPracticeAnalysisResult } from '@/api/practice'
import ChessBoard from '@/components/ChessBoard.vue'
import GameController from '@/components/GameController.vue'
import MoveList from '@/components/MoveList.vue'
import WinRateChart from '@/components/WinRateChart.vue'
import MoveEvaluation from '@/components/MoveEvaluation.vue'
import AnalysisOverlay from '@/components/AnalysisOverlay.vue'
import { useAnalysisOverlay } from '@/composables/useAnalysisOverlay'

const route = useRoute()

const { overlayVisible, dismissOverlay, watchAnalyzing } = useAnalysisOverlay()

const loading = ref(true)
const record = ref(null)
const positions = ref([])
const currentHalfMove = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(1000)
const boardSize = ref(480)
const analysisData = ref([])
const analyzing = ref(false)
const analysisProgress = ref(0)
const prHeaderRef = ref(null)
const overlayTopOffset = ref(0)

watchAnalyzing(analyzing)

let playTimer = null
let analysisPollTimer = null

const hasAnalysis = computed(() => analysisData.value.length > 0)

const boardOrientation = computed(() => {
  if (!record.value) return 'white'
  return record.value.user_color === 'b' ? 'black' : 'white'
})

const totalHalfMoves = computed(() => Math.max(0, positions.value.length - 1))

const currentFen = computed(() => {
  if (!positions.value.length) return 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
  const idx = Math.min(currentHalfMove.value, positions.value.length - 1)
  return positions.value[idx]?.fen || positions.value[0]?.fen
})

const currentLastMove = computed(() => {
  if (!positions.value.length || currentHalfMove.value <= 0) return null
  const idx = Math.min(currentHalfMove.value, positions.value.length - 1)
  const pos = positions.value[idx]
  return pos?.from && pos?.to ? { from: pos.from, to: pos.to } : null
})

const currentTurn = computed(() => {
  const fen = currentFen.value
  if (!fen) return 'white'
  return fen.includes(' w ') ? 'white' : 'black'
})

const isPlayerBlack = computed(() => record.value?.user_color === 'b')

const currentEvalScore = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const aIdx = currentHalfMove.value - 1
  if (aIdx >= analysisData.value.length) return null
  const score = analysisData.value[aIdx]?.score ?? null
  if (score == null) return null
  return isPlayerBlack.value ? -score : score
})

const currentMoveEval = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const idx = currentHalfMove.value
  if (idx - 1 < 0 || idx - 1 >= analysisData.value.length) return null
  const a = analysisData.value[idx - 1]

  let evalInfo = null
  if (a) {
    const flip = isPlayerBlack.value
    const pScore = flip ? (a.score != null ? -a.score : null) : a.score
    const pWinRate = flip ? (a.white_win_rate != null ? 100 - a.white_win_rate : null) : (a.white_win_rate ?? a.win_rate)
    const pBestScore = flip ? (a.best_moves?.[0]?.score != null ? -a.best_moves[0].score : null) : (a.best_moves?.[0]?.score ?? null)

    evalInfo = {
      move: a.san,
      score: pScore,
      win_rate: pWinRate,
      evaluation: a.evaluation || null,
      best_move: a.best_moves?.[0]?.move || null,
      best_score: pBestScore,
      pv: a.best_moves?.[0]?.pv || null,
      score_diff: a.score_diff ?? null,
      delta: a.delta ?? null,
    }
  }

  if (!evalInfo) {
    const pos = positions.value[idx]
    evalInfo = {
      move: pos?.san || null,
      score: null,
      win_rate: pos?.win_rate ?? null,
      evaluation: null,
      best_move: null,
      best_score: null,
      pv: null,
      score_diff: null,
      delta: null,
    }
  }

  return evalInfo
})

const currentBestMove = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const aIdx = currentHalfMove.value - 1
  if (aIdx >= analysisData.value.length) return null
  return analysisData.value[aIdx]?.best_moves?.[0]?.move || null
})

const currentPv = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const aIdx = currentHalfMove.value - 1
  if (aIdx >= analysisData.value.length) return null
  const pv = analysisData.value[aIdx]?.best_moves?.[0]?.pv
  return pv && pv.length > 1 ? pv.slice(1).join(' ') : null
})

const EVAL_MAP = {
  '!!': { symbol: '!!', label: '妙着', class: 'eval-brilliant' },
  '!': { symbol: '!', label: '好着', class: 'eval-great' },
  '!?': { symbol: '!?', label: '有趣', class: 'eval-interesting' },
  '?!': { symbol: '?!', label: '不精确', class: 'eval-inaccuracy' },
  '?': { symbol: '?', label: '失误', class: 'eval-mistake' },
  '??': { symbol: '??', label: '严重失误', class: 'eval-blunder' },
}

const currentAnnotation = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const aIdx = currentHalfMove.value - 1
  if (aIdx >= analysisData.value.length) return null
  const evaluation = analysisData.value[aIdx]?.evaluation
  if (!evaluation) return null
  return EVAL_MAP[evaluation] || null
})

const EVAL_SYMBOLS = {
  brilliant: '!!',
  great: '!',
  interesting: '!?',
  inaccuracy: '?!',
  mistake: '?',
  blunder: '??',
}

const displayMoves = computed(() => {
  const result = []
  for (let i = 1; i < positions.value.length; i++) {
    const pos = positions.value[i]
    const moveNum = Math.ceil(i / 2)

    let classification = ''
    let evalData = null
    if (analysisData.value.length && i - 1 < analysisData.value.length) {
      const a = analysisData.value[i - 1]
      if (a) {
        if (a.evaluation) {
          const evalMap = { '!!': 'brilliant', '!': 'great', '!?': 'interesting', '?!': 'inaccuracy', '?': 'mistake', '??': 'blunder' }
          classification = evalMap[a.evaluation] || ''
        }
        evalData = {
          classification,
          symbol: EVAL_SYMBOLS[classification] || '',
          score: isPlayerBlack.value ? (a.score != null ? -a.score : null) : a.score,
          win_rate: isPlayerBlack.value ? (a.white_win_rate != null ? 100 - a.white_win_rate : null) : (a.white_win_rate ?? a.win_rate),
          evaluation: a.evaluation,
        }
      }
    }

    if (i % 2 === 1) {
      result.push({
        move_number: moveNum,
        white: pos.san || '...',
        black: '',
        white_half_move: i,
        black_half_move: i + 1,
        white_eval: evalData,
        black_eval: null,
      })
    } else {
      if (result.length) {
        result[result.length - 1].black = pos.san || '...'
        result[result.length - 1].black_eval = evalData
      }
    }
  }
  return result
})

const resultLabel = computed(() => {
  if (!record.value) return ''
  const r = record.value.result
  if (r === '1/2-1/2') return '和棋'
  if (r === '1-0' && record.value.user_color === 'w') return '胜'
  if (r === '0-1' && record.value.user_color === 'b') return '胜'
  return '负'
})

const resultClass = computed(() => {
  if (!record.value) return ''
  const r = record.value.result
  if (r === '1/2-1/2') return 'pr-result-draw'
  if (r === '1-0' && record.value.user_color === 'w') return 'pr-result-win'
  if (r === '0-1' && record.value.user_color === 'b') return 'pr-result-win'
  return 'pr-result-lose'
})

function difficultyLabel(diff) {
  const map = { beginner: '入门', easy: '初级', medium: '中级', hard: '高级', expert: '专家' }
  return map[diff] || diff
}

function modeLabel(mode) {
  const map = { puzzle: '残局练习', from_game: '从棋谱开始', custom: '自定义FEN' }
  return map[mode] || mode
}

function modeTagType(mode) {
  const map = { puzzle: 'primary', from_game: 'success', custom: 'warning' }
  return map[mode] || 'info'
}

function formatDate(isoStr) {
  if (!isoStr) return '-'
  try {
    return new Date(isoStr).toLocaleString('zh-CN')
  } catch {
    return isoStr
  }
}

function formatDuration(seconds) {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}分${s}秒` : `${s}秒`
}

function buildPositions(startFen, moves) {
  const result = [{ fen: startFen }]
  try {
    const chess = new Chess(startFen)
    for (const move of moves) {
      const moveObj = chess.move(move.san || move)
      result.push({
        fen: chess.fen(),
        san: moveObj.san,
        from: moveObj.from,
        to: moveObj.to,
      })
    }
  } catch (e) {
    console.error('Error replaying moves:', e)
  }
  return result
}

function goNext() {
  if (currentHalfMove.value < totalHalfMoves.value) currentHalfMove.value++
}
function goPrev() {
  if (currentHalfMove.value > 0) currentHalfMove.value--
}
function goFirst() { currentHalfMove.value = 0 }
function goLast() { currentHalfMove.value = totalHalfMoves.value }
function jumpTo(n) { currentHalfMove.value = Math.max(0, Math.min(totalHalfMoves.value, n)) }

function onMoveListClick(halfMove) {
  currentHalfMove.value = halfMove
}

function onChartMoveSelect(halfMove) {
  currentHalfMove.value = halfMove
}

async function startAnalysis() {
  const id = route.params.id
  analyzing.value = true
  analysisProgress.value = 0

  try {
    await startPracticeAnalysis(id)

    if (analysisPollTimer) {
      clearInterval(analysisPollTimer)
      analysisPollTimer = null
    }

    analysisPollTimer = setInterval(async () => {
      try {
        const statusRes = await getPracticeAnalysisStatus(id)
        const statusData = statusRes.data || statusRes

        if (statusData.status === 'completed') {
          clearInterval(analysisPollTimer)
          analysisPollTimer = null
          analysisProgress.value = 100
          await loadAnalysisResult()
          analyzing.value = false
        } else if (statusData.status === 'failed') {
          clearInterval(analysisPollTimer)
          analysisPollTimer = null
          analyzing.value = false
        } else if (statusData.status === 'running' || statusData.status === 'pending') {
          analysisProgress.value = Math.round((statusData.progress || 0) * 100)
        }
      } catch {
        clearInterval(analysisPollTimer)
        analysisPollTimer = null
        analyzing.value = false
      }
    }, 2000)
  } catch {
    analyzing.value = false
  }
}

async function loadAnalysisResult() {
  const id = route.params.id
  try {
    const res = await getPracticeAnalysisResult(id)
    const data = res.data || res
    if (data.analysis) {
      const analysisMoves = data.analysis.moves || []
      analysisData.value = analysisMoves
    }
  } catch {
    analysisData.value = []
  }
}

async function loadRecord() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await getPracticeDetail(id)
    const data = res.data || res
    record.value = data

    const startFen = data.start_fen || 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
    const moves = data.moves || []
    positions.value = buildPositions(startFen, moves)
    currentHalfMove.value = 0

    if (data.has_analysis) {
      await loadAnalysisResult()
    }
  } catch {
    record.value = null
  } finally {
    loading.value = false
    nextTick(() => updateOverlayTop())
  }
}

watch(isPlaying, (playing) => {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
  if (playing) {
    playTimer = setInterval(() => {
      if (currentHalfMove.value < totalHalfMoves.value) {
        currentHalfMove.value++
      } else {
        isPlaying.value = false
      }
    }, playSpeed.value)
  }
})

watch(playSpeed, () => {
  if (isPlaying.value) {
    isPlaying.value = false
    setTimeout(() => { isPlaying.value = true }, 50)
  }
})

function updateOverlayTop() {
  if (prHeaderRef.value) {
    const headerEl = prHeaderRef.value
    overlayTopOffset.value = headerEl.offsetTop + headerEl.offsetHeight + 16
  }
}

onMounted(() => {
  loadRecord()
  window.addEventListener('resize', updateOverlayTop)
})

onUnmounted(() => {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
  if (analysisPollTimer) {
    clearInterval(analysisPollTimer)
    analysisPollTimer = null
  }
})
</script>

<style scoped>
.practice-review-page {
  position: relative;
  max-width: 1200px;
  margin: 0 auto;
}

.pr-loading {
  min-height: 400px;
}

.pr-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.pr-header-info {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--text-color-regular);
  flex-wrap: wrap;
}

.pr-header-item {
  white-space: nowrap;
}

.pr-header-actions {
  margin-left: auto;
}

.pr-body {
  position: relative;
  display: flex;
  gap: 20px;
}

.pr-left-panel {
  width: 220px;
  flex-shrink: 0;
}

.pr-center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.pr-right-panel {
  width: 280px;
  flex-shrink: 0;
}

.pr-info-section,
.pr-eval-section,
.pr-suggestion-section,
.pr-chart-section,
.pr-moves-section {
  background: var(--card-bg);
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.pr-info-section h3,
.pr-eval-section h3,
.pr-suggestion-section h3,
.pr-chart-section h3,
.pr-moves-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #f0f0f0;
}

.pr-info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.pr-info-label {
  color: var(--text-color-secondary);
}

.pr-info-value {
  color: var(--text-color);
  font-weight: 500;
}

.pr-suggestion-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.pr-suggestion-label {
  color: var(--text-color-secondary);
}

.pr-suggestion-value {
  color: var(--text-color);
  font-weight: 600;
  font-family: monospace;
}

.pr-moves-section {
  height: 520px;
  display: flex;
  flex-direction: column;
}

.pr-moves-section h3 {
  flex-shrink: 0;
}

.pr-controller {
  width: 480px;
}

.pr-result-win { color: #67c23a; }
.pr-result-lose { color: #f56c6c; }
.pr-result-draw { color: #e6a23c; }

.pr-empty {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1000px) {
  .pr-body {
    flex-wrap: wrap;
  }
  .pr-left-panel,
  .pr-right-panel {
    width: 100%;
  }
  .pr-center-panel {
    width: 100%;
  }
}
</style>
