<template>
  <div class="practice-page">
    <div class="pp-left-panel">
      <div class="pp-section">
        <h3 class="pp-section-title">
          模式选择
          <HelpTooltip content="选择AI对弈练习的模式：残局练习从残局库选择局面，从棋谱开始可截取棋谱中的局面，自定义FEN可输入任意局面" />
        </h3>
        <el-radio-group v-model="mode" :disabled="!!store.sessionId" size="small">
          <el-radio-button value="puzzle">残局练习</el-radio-button>
          <el-radio-button value="from_game">从棋谱开始</el-radio-button>
          <el-radio-button value="custom">自定义FEN</el-radio-button>
        </el-radio-group>
      </div>

      <div v-if="mode === 'puzzle'" class="pp-section">
        <h3 class="pp-section-title">选择残局</h3>
        <div v-if="store.puzzles.length === 0" class="pp-puzzle-empty">
          <p>暂无残局数据</p>
          <el-button type="primary" size="small" @click="$router.push('/puzzles')">前往残局库</el-button>
        </div>
        <div v-else class="pp-puzzle-list">
          <div
            v-for="p in store.puzzles"
            :key="p.id"
            class="pp-puzzle-card"
            :class="{ 'is-selected': selectedPuzzleId === p.id }"
            @click="selectPuzzle(p)"
          >
            <div class="pp-puzzle-card-header">
              <span class="pp-puzzle-card-name"><span class="pp-puzzle-num">#{{ String(p.puzzle_number || p.id).padStart(3, '0') }}</span> {{ p.name }}</span>
              <el-tag :type="diffTagType(p.difficulty)" size="small">{{ difficultyLabel(p.difficulty) }}</el-tag>
            </div>
            <div class="pp-puzzle-card-cat">{{ categoryLabel(p.category) }}</div>
          </div>
        </div>
        <div v-if="selectedPuzzle" class="pp-puzzle-preview">
          <div class="pp-puzzle-preview-title">{{ selectedPuzzle.name }}</div>
          <p>{{ selectedPuzzle.description }}</p>
          <div v-if="selectedPuzzle.hint" class="pp-puzzle-hint">
            <el-icon><QuestionFilled /></el-icon>
            {{ selectedPuzzle.hint }}
          </div>
        </div>
        <div class="pp-puzzle-more">
          <router-link to="/puzzles" class="pp-puzzle-more-link">浏览残局库 →</router-link>
        </div>
      </div>

      <div v-if="mode === 'from_game'" class="pp-section">
        <h3 class="pp-section-title">选择棋谱</h3>
        <p class="pp-mode-hint">从棋谱库中选择一个对局，播放到指定步数后截取局面，与AI继续对弈。</p>
        <div v-if="!selectedGameId" class="pp-game-pick">
          <el-button type="primary" size="small" @click="$router.push('/games')">
            前往棋谱库选择
          </el-button>
        </div>
        <div v-else class="pp-game-info">
          <div class="pp-game-info-row">
            <span>棋谱编号</span>
            <strong>#{{ selectedGameId }}</strong>
          </div>
          <el-button size="small" text type="primary" @click="selectedGameId = null; fromMoveInput = 0" style="margin-top: 4px">
            重新选择
          </el-button>
        </div>
        <div v-if="selectedGameId" class="pp-setting-row" style="margin-top: 8px">
          <span class="pp-setting-label">起始手数</span>
          <el-input-number v-model="fromMoveInput" :min="0" :max="200" size="small" :disabled="!!store.sessionId" />
        </div>
      </div>

      <div v-if="mode === 'custom'" class="pp-section">
        <h3 class="pp-section-title">自定义FEN</h3>
        <p class="pp-mode-hint">输入FEN字符串指定起始局面，与AI对弈练习。</p>
        <el-input
          v-model="customFenInput"
          placeholder="例如：rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
          :disabled="!!store.sessionId"
          type="textarea"
          :rows="3"
          size="small"
        />
      </div>

      <div class="pp-section">
        <h3 class="pp-section-title">
          对局设置
          <HelpTooltip content="设置执棋颜色和AI难度等级。入门/初级适合新手，中级适合有经验的棋手，高级/专家具有较强棋力" />
        </h3>
        <div class="pp-setting-row">
          <span class="pp-setting-label">执棋颜色</span>
          <el-radio-group v-model="userColor" :disabled="!!store.sessionId" size="small">
            <el-radio-button value="white">白方</el-radio-button>
            <el-radio-button value="black">黑方</el-radio-button>
          </el-radio-group>
        </div>
        <div class="pp-setting-row">
          <span class="pp-setting-label">AI难度</span>
          <el-select v-model="difficulty" :disabled="!!store.sessionId" size="small" style="width: 120px">
            <el-option label="入门" value="beginner" />
            <el-option label="初级" value="easy" />
            <el-option label="中级" value="medium" />
            <el-option label="高级" value="hard" />
            <el-option label="专家" value="expert" />
          </el-select>
        </div>
      </div>

      <el-button
        v-if="!store.sessionId"
        type="primary"
        :loading="store.loading"
        style="width: 100%"
        :disabled="!canStartGame"
        @click="startGame"
      >
        开始对局
      </el-button>
      <el-button
        v-else
        type="info"
        style="width: 100%"
        @click="newGame"
      >
        新对局
      </el-button>

      <div v-if="store.sessionId" class="pp-section">
        <h3 class="pp-section-title">对局信息</h3>
        <div class="pp-info-grid">
          <span class="pp-info-label">难度</span>
          <span class="pp-info-value">{{ difficultyLabel(store.difficulty) }}</span>
          <span class="pp-info-label">执棋</span>
          <span class="pp-info-value">{{ store.userColor === 'white' ? '白方' : '黑方' }}</span>
          <span class="pp-info-label">步数</span>
          <span class="pp-info-value">{{ store.moveHistory.length }}</span>
          <span class="pp-info-label">提示</span>
          <span class="pp-info-value">{{ store.hintsUsed }}</span>
          <span class="pp-info-label">悔棋</span>
          <span class="pp-info-value">{{ store.undoCount }}</span>
        </div>
      </div>

    </div>

    <div class="pp-center">
      <PracticeBoard
        :fen="store.currentFen"
        :user-color="store.userColor"
        :last-ai-move="aiLastMoveObj"
        :last-user-move="lastUserMoveObj"
        :last-move-from-to="store.lastMoveFromTo"
        :hint-move="currentHintSan"
        :is-user-turn="store.isUserTurn"
        :is-ai-thinking="store.aiThinking"
        :in-check="checkState.inCheck"
        :in-checkmate="checkState.inCheckmate"
        :board-size="560"
        @move-submit="onMoveSubmit"
      />

      <div class="pp-controls">
        <el-button :disabled="!canUndo" @click="onUndo">
          <el-icon><RefreshLeft /></el-icon> 悔棋
        </el-button>
        <HelpTooltip content="撤销最近一步你和AI的着法" />
        <el-button :disabled="!store.sessionId || store.isGameOver" @click="onHint">
          <el-icon><QuestionFilled /></el-icon> 提示
        </el-button>
        <HelpTooltip content="获取AI推荐的着法提示" />
        <el-button :disabled="!store.sessionId || store.isGameOver" type="danger" @click="onResign">
          <el-icon><CloseBold /></el-icon> 认输
        </el-button>
        <HelpTooltip content="放弃当前对局" />
        <el-button @click="newGame">
          <el-icon><Plus /></el-icon> 新对局
        </el-button>
      </div>

      <div v-if="store.sessionExpired" class="pp-error">
        <el-alert title="对局会话已过期" description="服务器会话已丢失（可能因服务器重启），请开始新的对局。" type="warning" show-icon :closable="false">
          <el-button type="primary" size="small" @click="newGame">开始新对局</el-button>
        </el-alert>
      </div>
      <div v-else-if="store.error" class="pp-error">
        <el-alert :title="store.error" type="error" show-icon :closable="false" />
      </div>
    </div>

    <div class="pp-right-panel">
      <div v-if="store.puzzleInfo" class="pp-section">
        <h3 class="pp-section-title">残局说明</h3>
        <div class="pp-puzzle-info">
          <div class="pp-puzzle-name">{{ store.puzzleInfo.name }}</div>
          <div class="pp-puzzle-desc">{{ store.puzzleInfo.description }}</div>
          <div v-if="store.puzzleInfo.hint" class="pp-puzzle-hint">
            <el-icon><QuestionFilled /></el-icon>
            {{ store.puzzleInfo.hint }}
          </div>
        </div>
      </div>

      <div v-if="store.showHint && store.hintData" class="pp-section">
        <h3 class="pp-section-title">提示</h3>
        <div class="pp-hint-card">
          <div v-if="store.hintData.best_move" class="pp-hint-item">
            <span class="pp-hint-label">推荐着法</span>
            <span class="pp-hint-value">{{ store.hintData.best_move }}</span>
          </div>
          <div v-if="store.hintData.hint_move" class="pp-hint-item">
            <span class="pp-hint-label">推荐着法</span>
            <span class="pp-hint-value">{{ store.hintData.hint_move }}</span>
          </div>
          <div v-if="store.hintData.pv" class="pp-hint-item">
            <span class="pp-hint-label">预测续着</span>
            <span class="pp-hint-value">{{ store.hintData.pv }}</span>
          </div>
          <div v-if="store.hintData.hint" class="pp-hint-item">
            <span class="pp-hint-value">{{ store.hintData.hint }}</span>
          </div>
        </div>
      </div>

      <div v-if="!store.sessionId && !store.puzzleInfo && selectedPuzzle" class="pp-section">
        <h3 class="pp-section-title">残局说明</h3>
        <div class="pp-puzzle-info">
          <div class="pp-puzzle-name">{{ selectedPuzzle.name }}</div>
          <div class="pp-puzzle-desc">{{ selectedPuzzle.description }}</div>
          <div class="pp-puzzle-hint">
            <el-icon><QuestionFilled /></el-icon>
            {{ selectedPuzzle.hint }}
          </div>
        </div>
      </div>

      <div v-if="store.isGameOver" class="pp-section">
        <h3 class="pp-section-title">对局结束</h3>
        <div class="pp-result-card">
          <div class="pp-result-text" :class="resultClass">{{ resultText }}</div>
          <div class="pp-result-stats">
            <div>总步数：{{ store.moveHistory.length }}</div>
            <div>使用提示：{{ store.hintsUsed }} 次</div>
            <div>悔棋次数：{{ store.undoCount }} 次</div>
          </div>
          <div class="pp-result-actions">
            <el-button type="primary" size="small" @click="newGame">再来一局</el-button>
            <el-button size="small" @click="$router.push('/practice/history')">练习历史</el-button>
          </div>
        </div>
      </div>

      <div v-if="store.sessionId" class="pp-section pp-move-list-section">
        <h3 class="pp-section-title">着法记录</h3>
        <MoveList
          :moves="practiceMoves"
          :current-move="practiceMoves.length"
          :show-evaluation="false"
          style="height: 200px"
        />
      </div>
    </div>

    <el-dialog v-model="showResignDialog" title="确认认输" width="360px" :close-on-click-modal="false">
      <p>确定要认输吗？此操作不可撤销。</p>
      <template #footer>
        <el-button @click="showResignDialog = false">取消</el-button>
        <el-button type="danger" @click="confirmResign">确认认输</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { Chess } from 'chess.js'
import { RefreshLeft, QuestionFilled, CloseBold, Plus } from '@element-plus/icons-vue'
import HelpTooltip from '@/components/HelpTooltip.vue'
import { usePracticeStore } from '@/store'
import PracticeBoard from '@/components/PracticeBoard.vue'
import MoveList from '@/components/MoveList.vue'

const route = useRoute()
const store = usePracticeStore()

const mode = ref('puzzle')
const selectedPuzzleId = ref('')
const selectedGameId = ref(null)
const fromMoveInput = ref(0)
const customFenInput = ref('')
const userColor = ref('white')
const difficulty = ref('medium')
const showResignDialog = ref(false)

const selectedPuzzle = computed(() => {
  if (!selectedPuzzleId.value) return null
  return store.puzzles.find(p => p.id === selectedPuzzleId.value) || null
})

const canStartGame = computed(() => {
  if (mode.value === 'puzzle') return !!selectedPuzzleId.value
  if (mode.value === 'from_game') return !!selectedGameId.value
  return true
})

const canUndo = computed(() => store.sessionId && !store.isGameOver && !store.aiThinking && store.moveHistory.length >= 2)

const aiLastMoveObj = computed(() => {
  if (!store.lastAiMove) return null
  return { san: store.lastAiMove }
})

const lastUserMoveObj = computed(() => {
  const userMoves = store.moveHistory.filter(m => m.color === 'user')
  if (userMoves.length === 0) return null
  const lastSan = userMoves[userMoves.length - 1].san
  return { san: lastSan }
})

const checkState = computed(() => {
  try {
    const chess = new Chess(store.currentFen)
    const inCheck = chess.inCheck()
    const inCheckmate = chess.isCheckmate()
    return { inCheck, inCheckmate }
  } catch {
    return { inCheck: false, inCheckmate: false }
  }
})

const currentHintSan = computed(() => {
  if (!store.showHint || !store.hintData) return ''
  return store.hintData.best_move || store.hintData.hint_move || store.hintData.hint || ''
})

const practiceMoves = computed(() => {
  const result = []
  for (let i = 0; i < store.moveHistory.length; i += 2) {
    const moveNum = Math.floor(i / 2) + 1
    result.push({
      move_number: moveNum,
      white: store.moveHistory[i]?.san || '...',
      black: store.moveHistory[i + 1]?.san || '',
      white_half_move: i + 1,
      black_half_move: i + 2,
      white_eval: null,
      black_eval: null,
    })
  }
  return result
})

const resultText = computed(() => {
  if (!store.result) return ''
  if (store.result === '1/2-1/2') return '和棋'
  const isWin = (store.result === '1-0' && store.userColor === 'white') ||
                (store.result === '0-1' && store.userColor === 'black')
  return isWin ? '你赢了！' : '你输了'
})

const resultClass = computed(() => {
  if (store.result === '1/2-1/2') return 'pp-result-draw'
  const isWin = (store.result === '1-0' && store.userColor === 'white') ||
                (store.result === '0-1' && store.userColor === 'black')
  return isWin ? 'pp-result-win' : 'pp-result-lose'
})

function difficultyLabel(diff) {
  const map = { beginner: '入门', easy: '初级', medium: '中级', hard: '高级', expert: '专家' }
  return map[diff] || diff
}

function diffTagType(diff) {
  const map = { beginner: 'success', easy: '', medium: 'warning', hard: 'danger', expert: 'info' }
  return map[diff] || 'info'
}

function categoryLabel(cat) {
  const map = {
    endgame: '残局',
    mate: '将杀',
    tactics: '战术',
    opening: '开局',
    middlegame: '中局',
  }
  return map[cat] || cat
}

function selectPuzzle(p) {
  selectedPuzzleId.value = p.id
  difficulty.value = p.difficulty
}

async function startGame() {
  if (mode.value === 'puzzle') {
    if (!selectedPuzzleId.value) return
    await store.startFromPuzzle(selectedPuzzleId.value, userColor.value, difficulty.value)
  } else if (mode.value === 'from_game') {
    if (!selectedGameId.value) return
    await store.startFromGame(selectedGameId.value, fromMoveInput.value, userColor.value, difficulty.value)
  } else {
    await store.startCustom(customFenInput.value, userColor.value, difficulty.value)
  }
}

function onMoveSubmit(san) {
  store.submitMove(san)
}

function onUndo() {
  store.undo()
}

function onHint() {
  store.requestHint()
}

function onResign() {
  showResignDialog.value = true
}

function confirmResign() {
  showResignDialog.value = false
  store.resign()
}

function newGame() {
  store.reset()
}

onMounted(async () => {
  store.loadPuzzles()
  let shouldAutoStart = false
  if (route.query.mode === 'custom' && route.query.fen) {
    mode.value = 'custom'
    customFenInput.value = route.query.fen
    shouldAutoStart = true
  }
  if (route.query.mode === 'from_game' && route.query.game_id) {
    mode.value = 'from_game'
    selectedGameId.value = parseInt(route.query.game_id)
    if (route.query.from_move) {
      fromMoveInput.value = parseInt(route.query.from_move)
    }
    shouldAutoStart = true
  }
  if (route.query.mode === 'puzzle' && route.query.puzzle_id) {
    mode.value = 'puzzle'
    selectedPuzzleId.value = parseInt(route.query.puzzle_id)
    shouldAutoStart = true
  }
  if (shouldAutoStart) {
    await startGame()
  }
})
</script>

<style scoped>
.practice-page {
  display: flex;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
  min-height: calc(100vh - 160px);
}

.pp-left-panel {
  width: 240px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pp-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.pp-right-panel {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.pp-section {
  background: var(--card-bg);
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
}

.pp-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0 0 10px 0;
  padding-bottom: 6px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  gap: 4px;
}

.pp-help-icon {
  font-size: 14px;
  color: var(--text-color-secondary);
  cursor: help;
  vertical-align: middle;
}

.pp-help-icon:hover {
  color: #409eff;
}

.pp-mode-hint {
  font-size: 12px;
  color: var(--text-color-secondary);
  margin: 0 0 8px 0;
  line-height: 1.5;
}

.pp-game-pick {
  text-align: center;
  padding: 12px 0;
}

.pp-puzzle-empty {
  text-align: center;
  padding: 16px 0;
  color: var(--text-color-secondary);
  font-size: 13px;
}

.pp-puzzle-more {
  text-align: center;
  margin-top: 8px;
}

.pp-puzzle-more-link {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
}

.pp-puzzle-more-link:hover {
  text-decoration: underline;
}

.pp-puzzle-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.pp-puzzle-card {
  padding: 8px 10px;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.pp-puzzle-card:hover {
  border-color: #409eff;
  background: var(--hover-bg);
}

.pp-puzzle-card.is-selected {
  border-color: #409eff;
  background: var(--hover-bg);
  box-shadow: 0 0 0 1px #409eff;
}

.pp-puzzle-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.pp-puzzle-card-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pp-puzzle-num {
  color: #409eff;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 11px;
  margin-right: 2px;
}

.pp-puzzle-card-cat {
  font-size: 11px;
  color: var(--text-color-secondary);
  margin-top: 2px;
}

.pp-puzzle-preview {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #f0f0f0;
  font-size: 12px;
  color: var(--text-color-regular);
  line-height: 1.6;
}

.pp-puzzle-preview-title {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 4px;
}

.pp-puzzle-desc {
  color: var(--text-color-regular);
  line-height: 1.6;
  margin-bottom: 8px;
}

.pp-puzzle-hint {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  color: #e6a23c;
  font-size: 12px;
  line-height: 1.5;
}

.pp-game-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.pp-game-option-id {
  color: #409eff;
  font-weight: 600;
  font-size: 12px;
  flex-shrink: 0;
}

.pp-game-info {
  background: var(--bg-color-secondary);
  border-radius: 4px;
  padding: 8px;
  font-size: 12px;
}

.pp-game-info-row {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
  color: var(--text-color-regular);
}

.pp-setting-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.pp-setting-label {
  font-size: 13px;
  color: var(--text-color-regular);
}

.pp-info-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 4px 12px;
  font-size: 12px;
}

.pp-info-label {
  color: var(--text-color-secondary);
}

.pp-info-value {
  color: var(--text-color);
  font-weight: 500;
}

.pp-move-list-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.pp-move-list-section .pp-section-title {
  flex-shrink: 0;
}

.pp-move-list-section :deep(.move-list) {
  overflow-y: auto;
}

.pp-controls {
  display: flex;
  gap: 8px;
}

.pp-error {
  width: 100%;
  max-width: 560px;
}

.pp-puzzle-info {
  font-size: 13px;
}

.pp-puzzle-name {
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 6px;
}

.pp-hint-card {
  font-size: 13px;
}

.pp-hint-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.pp-hint-label {
  color: var(--text-color-secondary);
  flex-shrink: 0;
}

.pp-hint-value {
  color: var(--text-color);
  font-weight: 500;
  font-family: 'Consolas', 'Monaco', monospace;
}

.pp-result-card {
  text-align: center;
}

.pp-result-text {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

.pp-result-win { color: #67c23a; }
.pp-result-lose { color: #f56c6c; }
.pp-result-draw { color: #e6a23c; }

.pp-result-stats {
  font-size: 12px;
  color: var(--text-color-secondary);
  line-height: 1.8;
  margin-bottom: 12px;
}

.pp-result-actions {
  display: flex;
  gap: 8px;
  justify-content: center;
}

@media (max-width: 1100px) {
  .practice-page {
    flex-wrap: wrap;
  }
  .pp-left-panel {
    width: 100%;
    order: 2;
  }
  .pp-center {
    order: 1;
    width: 100%;
  }
  .pp-right-panel {
    width: 100%;
    order: 3;
  }
}
</style>
