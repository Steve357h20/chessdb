<template>
  <div class="component-test">
    <h1>组件测试页面</h1>

    <section class="test-section">
      <h2>ChessBoard 棋盘组件</h2>
      <div class="test-controls">
        <el-button @click="flipBoard">翻转棋盘</el-button>
        <el-button @click="resetBoard">重置局面</el-button>
        <span>交互模式：</span>
        <el-switch v-model="interactive" />
        <span>显示坐标：</span>
        <el-switch v-model="showCoords" />
      </div>
      <div class="board-area">
        <ChessBoard
          ref="boardRef"
          :fen="fen"
          :last-move="lastMove"
          :orientation="orientation"
          :interactive="interactive"
          :show-coordinates="showCoords"
          :highlight-squares="highlightSquares"
          :board-size="480"
          @move-made="onMoveMade"
          @square-click="onSquareClick"
          @piece-click="onPieceClick"
        />
      </div>
      <div class="event-log">
        <p><strong>事件日志：</strong></p>
        <div v-for="(log, i) in eventLogs" :key="i" class="log-item">{{ log }}</div>
      </div>
    </section>

    <section class="test-section">
      <h2>WinRateChart 胜率走势图组件</h2>
      <div class="test-controls">
        <el-button @click="generateChartData">生成随机数据</el-button>
        <el-button @click="clearChartData">清除数据</el-button>
        <span>当前回合：</span>
        <el-slider v-model="chartCurrentMove" :min="0" :max="chartMaxMove" :step="1" style="width: 200px; display: inline-flex" />
      </div>
      <WinRateChart
        :analysis-data="chartAnalysisData"
        :current-move="chartCurrentMove"
        :height="300"
        @move-select="onChartMoveSelect"
      />
      <div class="event-log">
        <p><strong>选中回合：</strong>{{ chartSelectedMove ?? '-' }}</p>
      </div>
    </section>

    <section class="test-section">
      <h2>MoveList 着法列表组件</h2>
      <div class="test-controls">
        <el-button @click="generateMoveListData">生成着法数据</el-button>
        <el-button @click="clearMoveListData">清除</el-button>
        <span>当前着法：</span>
        <el-slider v-model="moveListCurrent" :min="0" :max="moveListMax" :step="1" style="width: 200px; display: inline-flex" />
        <span>显示评价：</span>
        <el-switch v-model="moveListShowEval" />
      </div>
      <div class="move-list-container">
        <MoveList
          :moves="moveListData"
          :current-move="moveListCurrent"
          :show-evaluation="moveListShowEval"
          @move-click="onMoveListClick"
        />
      </div>
    </section>

    <section class="test-section">
      <h2>MoveEvaluation 评价标记组件</h2>
      <div class="test-controls">
        <el-button @click="cycleEvalType">切换评价类型</el-button>
        <span>当前类型：{{ currentEvalLabel }}</span>
      </div>
      <div class="eval-demo-area">
        <MoveEvaluation :evaluation="currentEvalData" />
      </div>
    </section>

    <section class="test-section">
      <h2>GameController 打谱控制器组件</h2>
      <div class="test-controls">
        <span>总步数：</span>
        <el-input-number v-model="gcTotalMoves" :min="1" :max="200" size="small" />
      </div>
      <GameController
        :current-move="gcCurrentMove"
        :total-moves="gcTotalMoves"
        :is-playing="gcIsPlaying"
        :play-speed="gcPlaySpeed"
        :turn-info="gcTurnInfo"
        :eval-score="gcEvalScore"
        @play="gcIsPlaying = true"
        @pause="gcIsPlaying = false"
        @next="gcCurrentMove = Math.min(gcTotalMoves, gcCurrentMove + 1)"
        @prev="gcCurrentMove = Math.max(0, gcCurrentMove - 1)"
        @first="gcCurrentMove = 0"
        @last="gcCurrentMove = gcTotalMoves"
        @jump-to="gcCurrentMove = $event"
        @speed-change="gcPlaySpeed = $event"
      />
    </section>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ChessBoard from '@/components/ChessBoard.vue'
import WinRateChart from '@/components/WinRateChart.vue'
import MoveList from '@/components/MoveList.vue'
import MoveEvaluation from '@/components/MoveEvaluation.vue'
import GameController from '@/components/GameController.vue'

const boardRef = ref(null)
const fen = ref('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
const lastMove = ref(null)
const orientation = ref('white')
const interactive = ref(true)
const showCoords = ref(true)
const highlightSquares = ref([])
const eventLogs = ref([])

function flipBoard() {
  orientation.value = orientation.value === 'white' ? 'black' : 'white'
  addLog('翻转视角 → ' + orientation.value)
}

function resetBoard() {
  fen.value = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
  lastMove.value = null
  addLog('重置局面')
}

function onMoveMade(move) {
  lastMove.value = { from: move.from, to: move.to }
  if (boardRef.value) {
    fen.value = boardRef.value.getFen()
  }
  addLog(`走子：${move.from} → ${move.to}${move.promotion ? ' 升变=' + move.promotion : ''}`)
}

function onSquareClick(square) {
  addLog(`点击格子：${square}`)
}

function onPieceClick({ square, piece }) {
  addLog(`点击棋子：${piece} @ ${square}`)
}

function addLog(msg) {
  eventLogs.value.unshift(`[${new Date().toLocaleTimeString()}] ${msg}`)
  if (eventLogs.value.length > 20) eventLogs.value.pop()
}

const chartAnalysisData = ref([])
const chartCurrentMove = ref(0)
const chartSelectedMove = ref(null)

const chartMaxMove = computed(() => {
  if (!chartAnalysisData.value.length) return 0
  return chartAnalysisData.value[chartAnalysisData.value.length - 1].move_number
})

function generateChartData() {
  const data = []
  let winRate = 50
  let score = 0
  for (let i = 1; i <= 40; i++) {
    winRate += (Math.random() - 0.5) * 12
    winRate = Math.max(5, Math.min(95, winRate))
    score += (Math.random() - 0.5) * 1.5
    score = Math.max(-8, Math.min(8, score))
    data.push({
      move_number: i,
      white_win_rate: Math.round(winRate * 100) / 100,
      score: Math.round(score * 100) / 100,
      best_move: ['e4', 'd4', 'Nf3', 'c4', 'Be2'][i % 5],
    })
  }
  chartAnalysisData.value = data
  chartCurrentMove.value = 1
  addLog('生成随机分析数据（40回合）')
}

function clearChartData() {
  chartAnalysisData.value = []
  chartCurrentMove.value = 0
  chartSelectedMove.value = null
  addLog('清除分析数据')
}

function onChartMoveSelect(moveNum) {
  chartSelectedMove.value = moveNum
  chartCurrentMove.value = moveNum
  addLog(`图表选中回合：${moveNum}`)
}

generateChartData()

const moveListData = ref([])
const moveListCurrent = ref(0)
const moveListShowEval = ref(true)

const moveListMax = computed(() => {
  if (!moveListData.value.length) return 0
  return moveListData.value[moveListData.value.length - 1].move_number
})

function generateMoveListData() {
  const whiteMoves = ['e4', 'Nf3', 'Bb5', 'd3', 'O-O', 'Re1', 'c3', 'h3']
  const blackMoves = ['e5', 'Nc6', 'a6', 'd6', 'Be7', 'b5', 'd5', 'Nf6']
  const evalTypes = ['brilliant', 'great', 'good', 'inaccuracy', 'mistake', 'blunder']
  const evalSymbols = { brilliant: '!!', great: '!', good: '', inaccuracy: '?!', mistake: '?!', blunder: '??' }

  const data = []
  for (let i = 0; i < 8; i++) {
    const wEval = Math.random() > 0.4 ? { classification: evalTypes[Math.floor(Math.random() * evalTypes.length)], delta: Math.floor(Math.random() * 300) - 50 } : null
    const bEval = Math.random() > 0.4 ? { classification: evalTypes[Math.floor(Math.random() * evalTypes.length)], delta: Math.floor(Math.random() * 300) - 50 } : null
    data.push({
      move_number: i + 1,
      white: whiteMoves[i],
      black: blackMoves[i],
      white_eval: wEval,
      black_eval: bEval,
    })
  }
  moveListData.value = data
  moveListCurrent.value = 1
  addLog('生成着法列表数据（8回合）')
}

function clearMoveListData() {
  moveListData.value = []
  moveListCurrent.value = 0
}

function onMoveListClick(moveNumber) {
  moveListCurrent.value = moveNumber
  addLog(`着法列表点击：第 ${moveNumber} 回合`)
}

generateMoveListData()

const EVAL_PRESETS = [
  { label: '妙手 !!', data: { move: 'Nf3', score: 1.5, win_rate: 65.3, best_move: 'Nf3', best_score: 1.5, evaluation: '!!', pv: ['Nf3', 'd5', 'exd5', 'Nf6'], comment: '**精彩的马跳！** 这步棋控制了中心，同时威胁对方王翼。' } },
  { label: '好着 !', data: { move: 'e4', score: 0.8, win_rate: 55.2, best_move: 'd4', best_score: 1.2, evaluation: '!', comment: '稳健的中心控制着法。' } },
  { label: '有趣 !?', data: { move: 'g4', score: 0.3, win_rate: 52.1, best_move: 'd4', best_score: 0.9, evaluation: '!?', pv: ['g4', 'd5', 'Bg2', 'Bf5'], comment: '*非标准着法*，但有其战略意图。' } },
  { label: '疑问 ?!', data: { move: 'f3', score: -0.2, win_rate: 47.5, best_move: 'd4', best_score: 0.9, evaluation: '?!', comment: '削弱了王翼防御。' } },
  { label: '坏着 ?', data: { move: 'Qh5', score: -1.8, win_rate: 32.0, best_move: 'Nf3', best_score: 0.5, evaluation: '?', pv: ['Qh5', 'g6', 'Qf3', 'Nd5'], comment: '**过早出后**，容易被对方驱赶浪费时间。' } },
  { label: '大坏着 ??', data: { move: 'Ke2', score: -4.5, win_rate: 8.0, best_move: 'O-O', best_score: 0.3, evaluation: '??', pv: ['Ke2', 'Qh4', 'Kf1', 'Bc5'], comment: '**致命错误！** 王暴露在中心，立刻遭到攻击。使用 `O-O` 更好。' } },
  { label: '无评价', data: { move: 'd4', score: 0.15, win_rate: 51.0, best_move: 'e4', best_score: 0.3 } },
]

const evalTypeIndex = ref(0)

const currentEvalLabel = computed(() => EVAL_PRESETS[evalTypeIndex.value].label)
const currentEvalData = computed(() => EVAL_PRESETS[evalTypeIndex.value].data)

function cycleEvalType() {
  evalTypeIndex.value = (evalTypeIndex.value + 1) % EVAL_PRESETS.length
  addLog(`切换评价类型：${currentEvalLabel.value}`)
}

const gcCurrentMove = ref(0)
const gcTotalMoves = ref(45)
const gcIsPlaying = ref(false)
const gcPlaySpeed = ref(1000)

const gcTurnInfo = computed(() => {
  return gcCurrentMove.value % 2 === 0 ? 'white' : 'black'
})

const gcEvalScore = computed(() => {
  const seed = gcCurrentMove.value * 7 + 3
  const val = Math.sin(seed) * 2.5
  return Math.round(val * 100) / 100
})
</script>

<style scoped>
.component-test {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  color: var(--text-color);
}

h2 {
  color: #409eff;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.test-section {
  margin-bottom: 40px;
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

.test-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 16px;
  font-size: 14px;
  color: var(--text-color-regular);
}

.board-area {
  display: flex;
  justify-content: center;
  margin: 16px 0;
}

.move-list-container {
  height: 280px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
}

.eval-demo-area {
  max-width: 320px;
}

.event-log {
  background: var(--bg-color-secondary);
  border-radius: 4px;
  padding: 10px 14px;
  margin-top: 12px;
  max-height: 150px;
  overflow-y: auto;
  font-size: 13px;
}

.log-item {
  padding: 2px 0;
  color: var(--text-color-regular);
  border-bottom: 1px solid var(--border-color-lighter);
}

.log-item:last-child {
  border-bottom: none;
}
</style>
