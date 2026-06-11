<template>
  <div class="game-detail-page">
    <div v-if="loading" class="gd-loading" v-loading="true" />

    <template v-else-if="game">
      <div ref="gdHeaderRef" class="gd-header">
        <div class="gd-header-left">
          <el-button text @click="goBack">
            <el-icon><ArrowLeft /></el-icon> 返回
          </el-button>
          <span class="gd-title">
            <span class="gd-white-name">{{ game.white_player_name || '白方' }}<span v-if="game.white_elo" class="gd-header-elo"> ({{ game.white_elo }})</span></span>
            <span class="gd-vs">vs</span>
            <span class="gd-black-name">{{ game.black_player_name || '黑方' }}<span v-if="game.black_elo" class="gd-header-elo"> ({{ game.black_elo }})</span></span>
            <el-tag :type="resultTagType(game.result)" size="small" class="gd-result-tag">{{ game.result || '*' }}</el-tag>
          </span>
          <span v-if="game.tournament_name" class="gd-event">{{ game.tournament_name }}</span>
        </div>
        <div class="gd-header-actions">
          <el-button size="small" @click="toggleFavorite">
            <el-icon><component :is="isFavorited ? StarFilled : Star" /></el-icon>
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
          <el-button size="small" @click="shareGame">分享</el-button>
          <el-button size="small" @click="downloadPgn">下载PGN</el-button>
          <el-button
            v-if="!analyzing && !game.has_analysis"
            size="small"
            type="primary"
            @click="analyzeGame"
          >分析</el-button>
          <el-button
            v-if="analyzing"
            size="small"
            type="warning"
            loading
          >分析中 {{ analysisProgress }}%</el-button>
          <el-button
            v-if="!analyzing && game.has_analysis"
            size="small"
            type="success"
          >已分析</el-button>
        </div>
      </div>

      <div class="gd-body">
        <div class="gd-left-panel">
          <div class="gd-info-section">
            <h3>对局信息</h3>
            <div class="gd-info-row gd-info-row-highlight">
              <span class="gd-info-label">棋谱编号</span>
              <span class="gd-info-value gd-game-id">#{{ String(game.game_number || game.id).padStart(3, '0') }}</span>
            </div>
            <div class="gd-info-row">
              <span class="gd-info-label">白方</span>
              <span class="gd-info-value">
                {{ game.white_player_name || '-' }}
                <span v-if="game.white_elo" class="gd-elo">({{ game.white_elo }})</span>
              </span>
            </div>
            <div class="gd-info-row">
              <span class="gd-info-label">黑方</span>
              <span class="gd-info-value">
                {{ game.black_player_name || '-' }}
                <span v-if="game.black_elo" class="gd-elo">({{ game.black_elo }})</span>
              </span>
            </div>
            <div class="gd-info-row">
              <span class="gd-info-label">ECO</span>
              <span class="gd-info-value">{{ game.eco_code || '-' }}</span>
            </div>
            <div class="gd-info-row">
              <span class="gd-info-label">开局</span>
              <span class="gd-info-value">{{ game.opening_name || '-' }}</span>
            </div>
            <div v-if="game.date" class="gd-info-row">
              <span class="gd-info-label">日期</span>
              <span class="gd-info-value">{{ game.date }}</span>
            </div>
            <div v-if="game.tournament_name" class="gd-info-row">
              <span class="gd-info-label">赛事</span>
              <span class="gd-info-value">{{ game.tournament_name }}</span>
            </div>
            <div v-if="game.round" class="gd-info-row">
              <span class="gd-info-label">轮次</span>
              <span class="gd-info-value">{{ game.round }}</span>
            </div>
            <div v-if="game.termination" class="gd-info-row">
              <span class="gd-info-label">终止方式</span>
              <span class="gd-info-value">
                <el-tag :type="terminationTagType(game.termination)" size="small">{{ terminationLabel(game.termination) }}</el-tag>
              </span>
            </div>
            <div v-if="game.time_control" class="gd-info-row">
              <span class="gd-info-label">用时</span>
              <span class="gd-info-value">{{ formatTimeControl(game.time_control) }}</span>
            </div>
          </div>

          <div class="gd-moves-section">
            <h3>着法列表</h3>
            <MoveList
              :moves="displayMoves"
              :current-move="currentHalfMove"
              :show-evaluation="true"
              @move-click="onMoveListClick"
            />
            <div class="gd-legend">
              <div class="gd-legend-title">
                着法标记说明
                <el-tooltip
                  class="gd-legend-help"
                  placement="top"
                  effect="light"
                >
                  <template #content>
                    <div class="gd-legend-popover">
                      <div><b>!!</b> 妙手：在极小差距（&lt;0.05兵）内找到唯一最佳着法，出人意料的精准。</div>
                      <div><b>!</b> 好着：与最佳差距约 0.05–0.20 兵，优于大多数常规着法。</div>
                      <div><b>!?</b> 有趣尝试：差距约 0.20–0.50 兵，可能走出需要对手精确应对的变化。</div>
                      <div><b>?!</b> 不精确：差距约 0.50–1.00 兵，错过更优着法但未造成实质损失。</div>
                      <div><b>?</b> 失误：差距约 1.00–2.00 兵，给对手带来明显优势。</div>
                      <div><b>??</b> 严重失误：差距 &gt;2.00 兵，往往丢子甚至直接输棋。</div>
                      <div><b>+ / #</b> 将杀/绝杀：# 后的数字表示距离将杀步数（mate-in N）。</div>
                      <div class="gd-legend-popover-tip">分数为走完本手后白方的局面评估（兵），正数白方优势。</div>
                    </div>
                  </template>
                  <el-icon class="gd-legend-help-icon"><QuestionFilled /></el-icon>
                </el-tooltip>
              </div>
              <ul class="gd-legend-list">
                <li><span class="gd-legend-symbol">!!</span><span class="gd-legend-name">妙手（Brilliant）</span></li>
                <li><span class="gd-legend-symbol good">!</span><span class="gd-legend-name">好着（Good）</span></li>
                <li><span class="gd-legend-symbol neutral">!?</span><span class="gd-legend-name">有趣尝试（Interesting）</span></li>
                <li><span class="gd-legend-symbol neutral">?!</span><span class="gd-legend-name">不精确（Inaccuracy）</span></li>
                <li><span class="gd-legend-symbol bad">?</span><span class="gd-legend-name">失误（Mistake）</span></li>
                <li><span class="gd-legend-symbol bad">??</span><span class="gd-legend-name">严重失误（Blunder）</span></li>
                <li><span class="gd-legend-symbol good">+</span><span class="gd-legend-name">将杀（Check / Mate）</span></li>
              </ul>
            </div>
          </div>
        </div>

        <div class="gd-center-panel">
          <div class="gd-result-card" :class="'result-' + game.result.replace('/', '-')">
            <div class="gd-result-title">对局结果</div>
            <div class="gd-result-main">
              <span class="gd-result-score">{{ game.result || '*' }}</span>
              <span v-if="game.termination || game.time_control" class="gd-result-detail">
                <template v-if="game.termination">{{ terminationLabel(game.termination) }}</template>
                <template v-if="game.termination && game.time_control"> · </template>
                <template v-if="game.time_control">{{ formatTimeControl(game.time_control) }}</template>
                <template v-if="game.total_moves"> · {{ game.total_moves }}步</template>
              </span>
            </div>
            <div class="gd-result-desc">{{ resultDescription(game) }}</div>
          </div>

          <ChessBoard
            ref="boardRef"
            :fen="currentFen"
            :last-move="currentLastMove"
            :orientation="boardOrientation"
            :interactive="false"
            :show-coordinates="true"
            :board-size="boardSize"
            :move-annotation="boardAnnotation"
          />
          <div class="gd-controller">
            <GameController
              :current-move="currentHalfMove"
              :total-moves="totalHalfMoves"
              :is-playing="isPlaying"
              :play-speed="playSpeed"
              :turn-info="currentTurn"
              :eval-score="currentEvalScore"
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
          <div class="gd-capture-bar">
            <span class="gd-capture-info">当前第 {{ currentHalfMove }} 步</span>
            <HelpTooltip content="将当前局面截取为残局并保存到残局库，可用于AI对弈练习" />
            <el-button type="primary" size="small" @click="captureAsPuzzle">
              <el-icon><ScissorIcon /></el-icon> 截取残局
            </el-button>
          </div>
        </div>

        <div class="gd-right-panel">
          <div class="gd-chart-section">
            <h3>胜率走势</h3>
            <WinRateChart
              :analysis-data="analysisData"
              :current-move="currentHalfMove"
              :height="200"
              @move-select="onChartMoveSelect"
            />
          </div>

          <div class="gd-eval-section">
            <h3>当前评价</h3>
            <MoveEvaluation :evaluation="currentMoveEval" />
          </div>

          <div v-if="currentBestMove" class="gd-suggestion-section">
            <h3>AI 建议</h3>
            <div class="gd-suggestion-item">
              <span class="gd-suggestion-label">最佳着法</span>
              <span class="gd-suggestion-value">{{ currentBestMove }}</span>
            </div>
            <div v-if="currentPv" class="gd-suggestion-item">
              <span class="gd-suggestion-label">预测续着</span>
              <span class="gd-suggestion-value">{{ currentPv }}</span>
            </div>
          </div>

          <div v-if="game.eco_code" class="gd-opening-section">
            <h3>开局信息</h3>
            <div class="gd-opening-item">
              <span class="gd-opening-label">ECO</span>
              <span class="gd-opening-value">{{ game.eco_code }}</span>
            </div>
            <div v-if="game.opening_name" class="gd-opening-item">
              <span class="gd-opening-label">名称</span>
              <span class="gd-opening-value">{{ game.opening_name }}</span>
            </div>
          </div>

          <div class="gd-puzzle-section">
            <h3>关联残局</h3>
            <div v-if="loadingPuzzles" class="gd-puzzle-loading">加载中...</div>
            <div v-else-if="relatedPuzzles.length === 0" class="gd-puzzle-empty">
              暂无关联残局，可点击上方「截取残局」从当前局面创建
            </div>
            <div v-else class="gd-puzzle-list">
              <div v-for="p in relatedPuzzles" :key="p.id" class="gd-puzzle-item" @click="router.push({ path: '/practice', query: { mode: 'puzzle', puzzle_id: p.id } })">
                <div class="gd-puzzle-item-info">
                  <span class="gd-puzzle-item-name">{{ p.name }}</span>
                  <span v-if="p.from_move" class="gd-puzzle-item-move">第{{ p.from_move }}步</span>
                </div>
                <div class="gd-puzzle-item-tags">
                  <el-tag :type="diffTagType(p.difficulty)" size="small">{{ diffLabel(p.difficulty) }}</el-tag>
                  <span class="gd-puzzle-item-count">练{{ p.practice_count || 0 }}</span>
                </div>
              </div>
            </div>
            <div class="gd-puzzle-actions">
              <router-link :to="{ path: '/puzzles', query: { source_game_id: game?.id } }" class="gd-puzzle-link">在残局库中查看</router-link>
            </div>
          </div>
        </div>
      </div>
    </template>

    <AnalysisOverlay
      v-if="game"
      :visible="analyzing && overlayVisible"
      :progress="analysisProgress"
      :top-offset="overlayTopOffset"
      @dismiss="dismissOverlay"
    />

    <el-dialog v-model="showPuzzleDialog" title="截取残局到残局库" width="480px" :close-on-click-modal="false">
      <el-form :model="puzzleForm" label-width="80px" size="small">
        <el-form-item label="名称" required>
          <el-input v-model="puzzleForm.name" placeholder="为残局起个名字" />
        </el-form-item>
        <el-form-item label="FEN">
          <el-input v-model="puzzleForm.fen" type="textarea" :rows="2" readonly />
        </el-form-item>
        <el-form-item label="分类">
          <el-select v-model="puzzleForm.category" style="width: 100%">
            <el-option label="残局" value="endgame" />
            <el-option label="将杀" value="mate" />
            <el-option label="战术" value="tactics" />
            <el-option label="开局" value="opening" />
            <el-option label="中局" value="middlegame" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="puzzleForm.difficulty" style="width: 100%">
            <el-option label="入门" value="beginner" />
            <el-option label="初级" value="easy" />
            <el-option label="中级" value="medium" />
            <el-option label="高级" value="hard" />
            <el-option label="专家" value="expert" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="puzzleForm.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="提示">
          <el-input v-model="puzzleForm.hint" placeholder="可选提示" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPuzzleDialog = false">取消</el-button>
        <el-button type="primary" @click="savePuzzleToLibrary">保存到残局库</el-button>
        <el-button @click="goPracticeWithFen">仅开始练习</el-button>
      </template>
    </el-dialog>

    <div v-if="!loading && !game" class="gd-error">
      <el-empty description="棋谱加载失败">
        <el-button type="primary" @click="goBack">返回列表</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Star, StarFilled, Scissor as ScissorIcon, QuestionFilled } from '@element-plus/icons-vue'
import { Chess } from 'chess.js'
import { getGame, analyzeGame as analyzeGameApi } from '@/api/games'
import { startAnalysis, getAnalysisStatus } from '@/api/analysis'
import { checkCollection, addCollection, removeCollection } from '@/api/collections'
import { recordBrowsing } from '@/api/browsing'
import { createPuzzle, getPuzzles } from '@/api/practice'
import HelpTooltip from '@/components/HelpTooltip.vue'
import { classifyMove, nagToSymbol } from '@/utils/chessUtils'
import ChessBoard from '@/components/ChessBoard.vue'
import MoveList from '@/components/MoveList.vue'
import WinRateChart from '@/components/WinRateChart.vue'
import MoveEvaluation from '@/components/MoveEvaluation.vue'
import GameController from '@/components/GameController.vue'
import AnalysisOverlay from '@/components/AnalysisOverlay.vue'
import { useAnalysisOverlay } from '@/composables/useAnalysisOverlay'

const route = useRoute()
const router = useRouter()

const { overlayVisible, dismissOverlay, watchAnalyzing } = useAnalysisOverlay()

const loading = ref(true)
const game = ref(null)
const boardRef = ref(null)
const gdHeaderRef = ref(null)
const overlayTopOffset = ref(0)
const isFavorited = ref(false)
const collectionId = ref(null)
const boardOrientation = ref('white')
const boardSize = ref(480)

const currentHalfMove = ref(0)
const isPlaying = ref(false)
const playSpeed = ref(1000)

const positions = ref([])
const analysisData = ref([])

let playTimer = null

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

const currentEvalScore = computed(() => {
  if (!analysisData.value.length || currentHalfMove.value <= 0) return null
  const aIdx = currentHalfMove.value - 1
  if (aIdx >= analysisData.value.length) return null
  return analysisData.value[aIdx]?.score ?? null
})

const currentMoveEval = computed(() => {
  if (!positions.value.length || currentHalfMove.value <= 0) return null
  const idx = Math.min(currentHalfMove.value, positions.value.length - 1)
  const pos = positions.value[idx]
  if (!pos) return null

  let evalInfo = null
  if (analysisData.value.length && idx <= analysisData.value.length) {
    const aIdx = Math.min(idx - 1, analysisData.value.length - 1)
    if (aIdx >= 0) {
      const a = analysisData.value[aIdx]
      evalInfo = {
        move: pos.san || a?.san || '',
        score: a?.score ?? null,
        win_rate: a?.white_win_rate ?? a?.win_rate ?? null,
        best_move: a?.best_moves?.[0]?.move || a?.best_move || null,
        best_score: a?.best_moves?.[0]?.score ?? a?.best_score ?? null,
        evaluation: a?.evaluation || null,
        nag: a?.nag ?? null,
        pv: a?.best_moves?.[0]?.pv || a?.pv || null,
        comment: a?.comment || null,
      }
    }
  }

  if (!evalInfo) {
    evalInfo = {
      move: pos.san || '',
      score: pos.score ?? null,
      win_rate: pos.win_rate ?? null,
      best_move: pos.best_move || null,
      best_score: pos.best_score ?? null,
      evaluation: pos.evaluation || null,
      nag: pos.nag ?? null,
      pv: pos.pv || null,
      comment: pos.comment || null,
    }
  }

  return evalInfo
})

const currentBestMove = computed(() => {
  return currentMoveEval.value?.best_move || null
})

const currentPv = computed(() => {
  const pv = currentMoveEval.value?.pv
  return pv && pv.length ? pv.join(' ') : null
})

const EVAL_ANNOTATIONS = {
  brilliant: { symbol: '!!', label: '妙着', class: 'eval-brilliant' },
  great: { symbol: '!', label: '好着', class: 'eval-great' },
  good: { symbol: '', label: '正常', class: '' },
  interesting: { symbol: '!?', label: '有趣', class: 'eval-interesting' },
  inaccuracy: { symbol: '?!', label: '不精确', class: 'eval-inaccuracy' },
  mistake: { symbol: '?', label: '失误', class: 'eval-mistake' },
  blunder: { symbol: '??', label: '严重失误', class: 'eval-blunder' },
}

const boardAnnotation = computed(() => {
  if (currentHalfMove.value <= 0) return null
  const idx = Math.min(currentHalfMove.value, positions.value.length - 1)
  const pos = positions.value[idx]
  if (!pos) return null

  let classification = ''
  if (analysisData.value.length && idx - 1 < analysisData.value.length && idx - 1 >= 0) {
    const a = analysisData.value[idx - 1]
    if (a) {
      if (a.evaluation) {
        const evalMap = { '!!': 'brilliant', '!': 'great', '!?': 'interesting', '?!': 'inaccuracy', '?': 'mistake', '??': 'blunder' }
        classification = evalMap[a.evaluation] || ''
      } else if (a.nag) {
        const nagSym = nagToSymbol(a.nag)
        if (nagSym === '!!') classification = 'brilliant'
        else if (nagSym === '!') classification = 'great'
        else if (nagSym === '!?') classification = 'interesting'
        else if (nagSym === '?!') classification = 'inaccuracy'
        else if (nagSym === '?') classification = 'mistake'
        else if (nagSym === '??') classification = 'blunder'
      } else if (a.delta != null) {
        classification = classifyMove(Math.abs(a.delta) * 100)
      } else if (a.score_diff != null) {
        classification = classifyMove(a.score_diff * 100)
      }
    }
  }

  if (!classification || classification === 'good') return null
  return EVAL_ANNOTATIONS[classification] || null
})

const displayMoves = computed(() => {
  if (!positions.value.length) return []
  const moves = []
  for (let i = 1; i < positions.value.length; i++) {
    const pos = positions.value[i]
    const moveNum = Math.ceil(i / 2)

    let evalData = null
    if (analysisData.value.length && i - 1 < analysisData.value.length) {
      const a = analysisData.value[i - 1]
      if (a) {
        let classification = ''
        if (a.evaluation) {
          const evalMap = { '!!': 'brilliant', '!': 'great', '!?': 'interesting', '?!': 'inaccuracy', '?': 'mistake', '??': 'blunder' }
          classification = evalMap[a.evaluation] || ''
        } else if (a.nag) {
          const nagSym = nagToSymbol(a.nag)
          if (nagSym === '!!') classification = 'brilliant'
          else if (nagSym === '!') classification = 'great'
          else if (nagSym === '!?') classification = 'interesting'
          else if (nagSym === '?!') classification = 'inaccuracy'
          else if (nagSym === '?') classification = 'mistake'
          else if (nagSym === '??') classification = 'blunder'
        } else if (a.delta != null) {
          classification = classifyMove(Math.abs(a.delta) * 100)
        } else if (a.score_diff != null) {
          classification = classifyMove(a.score_diff * 100)
        }
        const delta = a.delta != null ? Math.abs(a.delta) * 100 : (a.score_diff != null ? a.score_diff * 100 : null)
        evalData = {
          classification,
          delta,
          score: a.score,
          win_rate: a.white_win_rate ?? a.win_rate,
          best_move: a.best_moves?.[0]?.move || a.best_move,
        }
      }
    }

    if (i % 2 === 1) {
      moves.push({
        move_number: moveNum,
        white: pos.san || '...',
        black: '',
        white_eval: evalData,
        black_eval: null,
        white_half_move: i,
        black_half_move: null,
      })
    } else {
      if (moves.length) {
        moves[moves.length - 1].black = pos.san || '...'
        moves[moves.length - 1].black_eval = evalData
        moves[moves.length - 1].black_half_move = i
      }
    }
  }
  return moves
})

function resultTagType(result) {
  if (result === '1-0') return 'success'
  if (result === '0-1') return 'danger'
  if (result === '1/2-1/2') return 'warning'
  return 'info'
}

function terminationLabel(term) {
  const map = {
    'Normal': '正常结束',
    'Time forfeit': '超时判负',
    'Abandoned': '弃权',
    'Rules infraction': '违规',
  }
  return map[term] || term
}

function resultDescription(g) {
  if (!g) return ''
  const winner = g.result === '1-0' ? g.white_player_name : g.result === '0-1' ? g.black_player_name : null
  const loser = g.result === '1-0' ? g.black_player_name : g.result === '0-1' ? g.white_player_name : null
  if (g.result === '1/2-1/2') return '双方和棋'
  if (!winner) return '对局未完成'
  const term = g.termination
  if (term === 'Time forfeit') return `${loser} 超时，${winner} 获胜`
  if (term === 'Abandoned') return `${loser} 弃权，${winner} 获胜`
  if (term === 'Normal') {
    const lastFen = g.final_fen || ''
    if (lastFen.includes('#') || g.pgn_content?.trimEnd().endsWith('#')) return `${winner} 将杀获胜`
    return `${winner} 获胜（${loser} 认输）`
  }
  return `${winner} 获胜`
}

function terminationTagType(term) {
  if (term === 'Normal') return 'success'
  if (term === 'Time forfeit') return 'warning'
  if (term === 'Abandoned') return 'danger'
  return 'info'
}

function formatTimeControl(tc) {
  if (!tc) return ''
  const parts = tc.split('+')
  const base = parseInt(parts[0])
  const increment = parts[1] ? parseInt(parts[1]) : 0
  if (base >= 60) {
    const mins = Math.floor(base / 60)
    return increment > 0 ? `${mins}+${increment}` : `${mins}分钟`
  }
  return increment > 0 ? `${base}+${increment}` : `${base}秒`
}

function parsePgnWithChessJs(pgn) {
  const initialFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
  const positions = [{ fen: initialFen }]

  try {
    const chess = new Chess()
    const movesSection = pgn.replace(/\[.*?\]/g, '').replace(/\{.*?\}/g, '').trim()
    const moveRegex = /\d+\.+\s*([a-h1-8KQRBNOo][\w\-+=#!?]+)\s*([a-h1-8KQRBNOo][\w\-+=#!?]*)?/g
    let match

    while ((match = moveRegex.exec(movesSection)) !== null) {
      const whiteSan = match[1]
      if (whiteSan && whiteSan !== '1-0' && whiteSan !== '0-1' && whiteSan !== '1/2-1/2' && whiteSan !== '*') {
        try {
          const m = chess.move(whiteSan)
          positions.push({
            fen: chess.fen(),
            san: m.san,
            from: m.from,
            to: m.to,
            halfMove: positions.length,
          })
        } catch {
          break
        }
      }
      const blackSan = match[2]
      if (blackSan && blackSan !== '1-0' && blackSan !== '0-1' && blackSan !== '1/2-1/2' && blackSan !== '*') {
        try {
          const m = chess.move(blackSan)
          positions.push({
            fen: chess.fen(),
            san: m.san,
            from: m.from,
            to: m.to,
            halfMove: positions.length,
          })
        } catch {
          break
        }
      }
    }
  } catch (e) {
    console.error('PGN parse error:', e)
  }

  return positions
}

async function loadGame() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await getGame(id)
    const data = res.data || res
    game.value = data

    const initialFen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    if (data.moves && Array.isArray(data.moves) && data.moves.length > 0) {
      positions.value = [{ fen: initialFen }]
      for (const move of data.moves) {
        positions.value.push({
          fen: move.fen_after || move.fen_before || '',
          san: move.san || '',
          from: move.uci ? move.uci.substring(0, 2) : '',
          to: move.uci ? move.uci.substring(2, 4) : '',
          halfMove: positions.value.length,
          eval_data: null,
        })
      }
    } else if (data.pgn_content || data.pgn) {
      positions.value = parsePgnWithChessJs(data.pgn_content || data.pgn)
    } else {
      positions.value = [{ fen: initialFen }]
    }

    if (data.analysis && typeof data.analysis === 'object') {
      const analysisMoves = data.analysis.analysis_data?.moves || data.analysis.moves
      if (analysisMoves && Array.isArray(analysisMoves)) {
        analysisData.value = analysisMoves
      } else if (Array.isArray(data.analysis)) {
        analysisData.value = data.analysis
      } else {
        analysisData.value = generateMockAnalysis()
      }
    } else if (data.analysis && Array.isArray(data.analysis)) {
      analysisData.value = data.analysis
    } else {
      analysisData.value = generateMockAnalysis()
    }

    currentHalfMove.value = 0
    checkFavStatus()
    loadRelatedPuzzles()

    nextTick(() => {
      updateOverlayTop()
    })
  } catch (e) {
    ElMessage.error('加载棋谱失败：' + e.message)
    game.value = null
  } finally {
    loading.value = false
  }
}

function generateMockAnalysis() {
  if (!positions.value.length) return []
  const data = []
  let winRate = 50
  let score = 0
  const bestMoves = ['e4', 'd4', 'Nf3', 'c4', 'Be2', 'O-O', 'Re1', 'Bc4', 'Nc3', 'Qd2']
  
  for (let i = 1; i < positions.value.length; i++) {
    const prevScore = score
    
    //winRate += (Math.random() - 0.5) * 8
    //winRate = Math.max(5, Math.min(95, winRate))
    
    const r = Math.random()
    if (r < 0.05) {
      score += (Math.random() - 0.5) * 3
    } else if (r < 0.20) {
      score += (Math.random() - 0.5) * 1.1
    } else {
      score += (Math.random() - 0.5) * 0.3
    }
    score = Math.max(-5, Math.min(5, score))
    
    const delta = Math.abs(score - prevScore)
    
    // ========== 修复：根据delta生成评价 ==========
    let classification = ''
    let evaluation = ''
    let nag = null
    
    if (delta < 0.10) {
      // 几乎没变化 → 好着 (!)
      classification = 'great'
      evaluation = '!'
      nag = 1
    } else if (delta < 0.25) {
      // 小变化 → 好着或正常
      classification = 'great'
      evaluation = '!'
      nag = 1
    } else if (delta < 0.50) {
      // 中等变化 → 正常
      classification = 'good'
      evaluation = ''
      nag = null
    } else if (delta < 1.00) {
      // 较大变化 → 有趣 (!?)
      classification = 'interesting'
      evaluation = '!?'
      nag = 5
    } else if (delta < 2.00) {
      // 大变化 → 不精确 (?!)
      classification = 'inaccuracy'
      evaluation = '?!'
      nag = 6
    } else {
      // 极大变化 → 失误 (?)
      classification = 'mistake'
      evaluation = '?'
      nag = 2
    }

    const pos = positions.value[i]
    
    // 生成best_move（应该比实际着法分数略好）
    const bestMoveScore = score + (Math.random() * 0.3)
    
    data.push({
      move_number: Math.ceil(i / 2),
      san: pos?.san || '',
      white_win_rate: Math.round(winRate * 100) / 100,
      score: Math.round(score * 100) / 100,
      delta: Math.round(delta),
      classification: classifyMove(delta),
      evaluation: evaluation,
      nag: nag,
      best_move: bestMoves[i % bestMoves.length],
      best_score: Math.round(bestMoveScore * 100) / 100,
      best_moves: [{
        move: bestMoves[i % bestMoves.length],
        score: Math.round(score * 100) / 100,
        win_rate: Math.round(winRate * 100) / 100,
        pv: [bestMoves[i % bestMoves.length]],
      }],
    })
  }
  return data
}

function goNext() {
  if (currentHalfMove.value < totalHalfMoves.value) {
    currentHalfMove.value++
  }
}

function goPrev() {
  if (currentHalfMove.value > 0) {
    currentHalfMove.value--
  }
}

function goFirst() {
  currentHalfMove.value = 0
}

function goLast() {
  currentHalfMove.value = totalHalfMoves.value
}

function jumpTo(move) {
  currentHalfMove.value = Math.max(0, Math.min(totalHalfMoves.value, move))
}

function onMoveListClick(halfMove) {
  currentHalfMove.value = Math.max(0, Math.min(totalHalfMoves.value, halfMove))
}

function onChartMoveSelect(halfMove) {
  jumpTo(halfMove)
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push({ name: 'GameList' })
  }
}

async function toggleFavorite() {
  if (!game.value?.id) return
  const token = localStorage.getItem('token')
  if (!token) {
    ElMessage.warning('请先登录后再收藏')
    return
  }

  if (isFavorited.value && collectionId.value) {
    try {
      await removeCollection(collectionId.value)
      isFavorited.value = false
      collectionId.value = null
      ElMessage.success('已取消收藏')
    } catch (e) {
      ElMessage.error('取消收藏失败')
    }
  } else {
    try {
      const res = await addCollection(game.value.id)
      const data = res.data || res
      isFavorited.value = true
      collectionId.value = data.id
      ElMessage.success('已收藏')
    } catch (e) {
      if (e?.response?.status === 409) {
        isFavorited.value = true
        ElMessage.info('已在收藏中')
      } else {
        ElMessage.error('收藏失败')
      }
    }
  }
}

async function checkFavStatus() {
  const token = localStorage.getItem('token')
  if (!token || !game.value?.id) return
  try {
    const res = await checkCollection(game.value.id)
    const data = res.data || res
    isFavorited.value = data.is_collected
    collectionId.value = data.collection?.id || null
  } catch {
    isFavorited.value = false
  }
}

function shareGame() {
  const url = window.location.href
  navigator.clipboard.writeText(url).then(() => {
    ElMessage.success('链接已复制到剪贴板')
  }).catch(() => {
    ElMessage.info('分享链接：' + url)
  })
}

function downloadPgn() {
  if (!game.value?.pgn_content && !game.value?.pgn) {
    ElMessage.warning('暂无PGN数据')
    return
  }
  const pgnData = game.value.pgn_content || game.value.pgn
  const blob = new Blob([pgnData], { type: 'application/x-chess-pgn' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${game.value.white_player_name || 'white'}_vs_${game.value.black_player_name || 'black'}.pgn`
  a.click()
  URL.revokeObjectURL(url)
}

const analyzing = ref(false)
const analysisProgress = ref(0)
let analysisPollTimer = null

watchAnalyzing(analyzing)

const relatedPuzzles = ref([])
const loadingPuzzles = ref(false)

async function loadRelatedPuzzles() {
  if (!game.value?.id) return
  loadingPuzzles.value = true
  try {
    const res = await getPuzzles({ source_game_id: game.value.id, per_page: 50 })
    const data = res.data || res
    relatedPuzzles.value = data.puzzles || []
  } catch {
    relatedPuzzles.value = []
  } finally {
    loadingPuzzles.value = false
  }
}

const showPuzzleDialog = ref(false)
const puzzleForm = ref({
  name: '',
  category: 'endgame',
  difficulty: 'medium',
  description: '',
  hint: '',
})

function captureAsPuzzle() {
  if (!positions.value.length) return
  const idx = Math.min(currentHalfMove.value, positions.value.length - 1)
  const fen = positions.value[idx]?.fen
  if (!fen) {
    ElMessage.warning('无法获取当前局面')
    return
  }
  const moveNum = currentHalfMove.value
  const whiteName = game.value?.white_player_name || '白方'
  const blackName = game.value?.black_player_name || '黑方'
  puzzleForm.value = {
    name: `${whiteName} vs ${blackName} - 第${moveNum}步`,
    category: 'endgame',
    difficulty: 'medium',
    description: `来自对局 ${whiteName} vs ${blackName}，第${moveNum}步的局面`,
    hint: '',
    fen: fen,
    source_game_id: game.value?.id,
    from_move: moveNum,
  }
  showPuzzleDialog.value = true
}

async function savePuzzleToLibrary() {
  if (!puzzleForm.value.name || !puzzleForm.value.fen) return
  try {
    await createPuzzle(puzzleForm.value)
    ElMessage.success('残局已保存到残局库')
    showPuzzleDialog.value = false
    loadRelatedPuzzles()
  } catch (e) {
    ElMessage.error(e?.response?.data?.error || '保存残局失败')
  }
}

function goPracticeWithFen() {
  showPuzzleDialog.value = false
  router.push({
    path: '/practice',
    query: {
      mode: 'from_game',
      game_id: game.value.id,
      from_move: currentHalfMove.value,
    },
  })
}

function diffTagType(diff) {
  const map = { beginner: 'success', easy: '', medium: 'warning', hard: 'danger', expert: 'info' }
  return map[diff] || 'info'
}

function diffLabel(diff) {
  const map = { beginner: '入门', easy: '初级', medium: '中级', hard: '高级', expert: '专家' }
  return map[diff] || diff
}

function analyzeGame() {
  if (analyzing.value) return
  if (!game.value?.id) return

  if (game.value.has_analysis) {
    ElMessage.info('该对局已有分析结果')
    return
  }

  analyzing.value = true
  analysisProgress.value = 0

  startAnalysis(game.value.id)
    .then((res) => {
      const data = res.data || res
      if (data.cached) {
        analyzing.value = false
        ElMessage.success('分析结果已存在，正在加载...')
        loadGame()
        return
      }
      ElMessage.info('开始分析，请稍候...')
      pollAnalysisStatus(game.value.id)
    })
    .catch((e) => {
      analyzing.value = false
      const msg = e?.response?.data?.error || e?.message || '启动分析失败'
      ElMessage.error(msg)
    })
}

function pollAnalysisStatus(gameId) {
  if (analysisPollTimer) {
    clearInterval(analysisPollTimer)
    analysisPollTimer = null
  }

  analysisPollTimer = setInterval(async () => {
    try {
      const res = await getAnalysisStatus(gameId)
      const data = res.data || res

      if (data.progress) {
        analysisProgress.value = Math.round(data.progress * 100)
      }

      if (data.status === 'completed') {
        clearInterval(analysisPollTimer)
        analysisPollTimer = null
        analyzing.value = false
        analysisProgress.value = 100
        ElMessage.success('分析完成！')
        loadGame()
      } else if (data.status === 'failed') {
        clearInterval(analysisPollTimer)
        analysisPollTimer = null
        analyzing.value = false
        ElMessage.error('分析失败：' + (data.error || '未知错误'))
      }
    } catch {
      clearInterval(analysisPollTimer)
      analysisPollTimer = null
      analyzing.value = false
      ElMessage.error('获取分析状态失败')
    }
  }, 2000)
}

watch(isPlaying, (val) => {
  if (val) {
    startAutoPlay()
  } else {
    stopAutoPlay()
  }
})

function startAutoPlay() {
  stopAutoPlay()
  playTimer = setInterval(() => {
    if (currentHalfMove.value < totalHalfMoves.value) {
      currentHalfMove.value++
    } else {
      isPlaying.value = false
    }
  }, playSpeed.value)
}

function stopAutoPlay() {
  if (playTimer) {
    clearInterval(playTimer)
    playTimer = null
  }
}

watch(playSpeed, () => {
  if (isPlaying.value) {
    stopAutoPlay()
    startAutoPlay()
  }
})

function updateBoardSize() {
  const w = window.innerWidth
  if (w < 768) {
    boardSize.value = Math.min(w - 40, 400)
  } else if (w < 1200) {
    boardSize.value = 400
  } else {
    boardSize.value = 480
  }
}

function updateOverlayTop() {
  if (gdHeaderRef.value) {
    const headerEl = gdHeaderRef.value
    overlayTopOffset.value = headerEl.offsetTop + headerEl.offsetHeight + 16
  }
}

function recordBrowsingHistory() {
  const gameId = route.params.id
  if (!gameId) return
  const token = localStorage.getItem('token')
  if (token) {
    recordBrowsing(parseInt(gameId)).catch(() => {})
  } else {
    const stored = localStorage.getItem('recentGames')
    let recent = []
    try { recent = JSON.parse(stored || '[]') } catch { recent = [] }
    recent = recent.filter(g => g.id !== parseInt(gameId))
    if (game.value) {
      recent.unshift({
        id: parseInt(gameId),
        white: game.value.white_player_name || '?',
        black: game.value.black_player_name || '?',
      })
    }
    recent = recent.slice(0, 20)
    localStorage.setItem('recentGames', JSON.stringify(recent))
  }
}

onMounted(() => {
  loadGame()
  loadRelatedPuzzles()
  updateBoardSize()
  window.addEventListener('resize', () => {
    updateBoardSize()
    updateOverlayTop()
  })
  recordBrowsingHistory()
})

onUnmounted(() => {
  stopAutoPlay()
  if (analysisPollTimer) {
    clearInterval(analysisPollTimer)
    analysisPollTimer = null
  }
  window.removeEventListener('resize', updateBoardSize)
})
</script>

<style scoped>
.game-detail-page {
  position: relative;
  max-width: 1400px;
  margin: 0 auto;
  padding: 16px;
}

.gd-loading {
  min-height: 400px;
}

.gd-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.gd-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.gd-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.gd-white-name {
  color: var(--text-color);
}

.gd-vs {
  color: var(--text-color-secondary);
  margin: 0 4px;
  font-weight: 400;
}

.gd-black-name {
  color: var(--text-color);
}

.gd-result-tag {
  margin-left: 8px;
}

.gd-event {
  font-size: 13px;
  color: var(--text-color-secondary);
}

.gd-header-actions {
  display: flex;
  gap: 8px;
}

.gd-body {
  position: relative;
  display: grid;
  grid-template-columns: 220px 1fr 300px;
  gap: 16px;
}

.gd-left-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.gd-center-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.gd-result-card {
  width: 100%;
  padding: 10px 16px;
  border-radius: 8px;
  background: var(--bg-color-secondary);
  border-left: 4px solid #909399;
  box-sizing: border-box;
}
.gd-result-card.result-1-0 {
  border-left-color: #67c23a;
  background: #f0f9eb;
}
.gd-result-card.result-0-1 {
  border-left-color: #f56c6c;
  background: #fef0f0;
}
.gd-result-card.result-1-2-1-2 {
  border-left-color: #e6a23c;
  background: #fdf6ec;
}
.gd-result-title {
  font-size: 11px;
  color: var(--text-color-secondary);
  margin-bottom: 4px;
  letter-spacing: 1px;
  text-transform: uppercase;
}
.gd-result-main {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.gd-result-score {
  font-size: 22px;
  font-weight: 800;
  font-family: 'Arial', sans-serif;
}
.result-1-0 .gd-result-score { color: #67c23a; }
.result-0-1 .gd-result-score { color: #f56c6c; }
.result-1-2-1-2 .gd-result-score { color: #e6a23c; }
.gd-result-detail {
  font-size: 13px;
  color: var(--text-color-regular);
}
.gd-result-desc {
  font-size: 13px;
  color: var(--text-color);
  margin-top: 4px;
  font-weight: 500;
}

.gd-right-panel {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.gd-info-section,
.gd-moves-section,
.gd-chart-section,
.gd-eval-section,
.gd-suggestion-section,
.gd-opening-section {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.gd-info-section h3,
.gd-moves-section h3,
.gd-chart-section h3,
.gd-eval-section h3,
.gd-suggestion-section h3,
.gd-opening-section h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #409eff;
  border-bottom: 1px solid var(--border-color-lighter);
  padding-bottom: 6px;
}

.gd-info-row-highlight {
  background: var(--hover-bg);
  border-radius: 4px;
  padding: 6px 8px !important;
  margin-bottom: 4px;
}

.gd-game-id {
  color: #409eff !important;
  font-size: 15px;
  font-weight: 700 !important;
  font-family: 'Consolas', 'Monaco', monospace;
}

.gd-capture-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
  padding: 6px 0;
}

.gd-capture-info {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.gd-puzzle-section {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 14px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.gd-puzzle-section h3 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #409eff;
  border-bottom: 1px solid var(--border-color-lighter);
  padding-bottom: 6px;
}

.gd-puzzle-loading,
.gd-puzzle-empty {
  font-size: 12px;
  color: var(--text-color-secondary);
  text-align: center;
  padding: 8px 0;
}

.gd-puzzle-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gd-puzzle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 8px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 12px;
}

.gd-puzzle-item:hover {
  border-color: #409eff;
  background: var(--hover-bg);
}

.gd-puzzle-item-info {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.gd-puzzle-item-name {
  color: var(--text-color);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.gd-puzzle-item-move {
  color: var(--text-color-secondary);
  font-size: 11px;
  flex-shrink: 0;
}

.gd-puzzle-item-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}

.gd-puzzle-item-count {
  color: var(--text-color-secondary);
  font-size: 11px;
}

.gd-puzzle-actions {
  margin-top: 8px;
  text-align: center;
}

.gd-puzzle-link {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
}

.gd-puzzle-link:hover {
  text-decoration: underline;
}

.gd-info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.gd-info-label {
  color: var(--text-color-secondary);
}

.gd-info-value {
  color: var(--text-color);
  font-weight: 500;
}

.gd-elo {
  color: var(--text-color-secondary);
  font-weight: 400;
}

.gd-header-elo {
  color: var(--text-color-secondary);
  font-weight: 400;
  font-size: 13px;
}

.gd-moves-section {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.gd-moves-section :deep(.move-list) {
  height: 300px;
  flex-shrink: 0;
}

.gd-legend {
  margin-top: 16px;
  padding: 14px 16px;
  background: var(--surface-color, #f5f7fa);
  border-radius: 8px;
  border: 1px solid var(--border-color, #ebeef5);
  font-size: 12px;
  line-height: 1.55;
  color: var(--text-color-regular, #4c4d4f);
}

.gd-legend-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-color-primary, #303133);
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.gd-legend-help {
  cursor: help;
  color: var(--text-color-secondary, #909399);
  display: inline-flex;
  align-items: center;
}

.gd-legend-help-icon {
  font-size: 14px;
  transition: color 0.15s;
}

.gd-legend-help:hover .gd-legend-help-icon {
  color: var(--el-color-primary, #409eff);
}

.gd-legend-popover {
  max-width: 320px;
  font-size: 12px;
  line-height: 1.6;
  color: #303133;
}

.gd-legend-popover > div {
  margin-bottom: 4px;
}

.gd-legend-popover-tip {
  margin-top: 8px !important;
  padding-top: 6px;
  border-top: 1px dashed #dcdfe6;
  color: #909399;
  font-size: 11.5px;
}

.gd-legend-symbol {
  flex-shrink: 0;
  width: 26px;
  height: 22px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  background: rgba(64, 158, 255, 0.12);
  color: #409eff;
  font-family: "Segoe UI Symbol", "Apple Color Emoji", "Microsoft YaHei", sans-serif;
}

.gd-legend-symbol.good {
  background: rgba(103, 194, 58, 0.15);
  color: #67c23a;
}

.gd-legend-symbol.neutral {
  background: rgba(230, 162, 60, 0.15);
  color: #e6a23c;
}

.gd-legend-symbol.bad {
  background: rgba(245, 108, 108, 0.15);
  color: #f56c6c;
}

.gd-legend-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.gd-legend-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.gd-legend-name {
  color: var(--text-color-regular, #4c4d4f);
  font-size: 12.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.gd-controller {
  width: 100%;
  max-width: 480px;
}

.gd-suggestion-item,
.gd-opening-item {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.gd-suggestion-label,
.gd-opening-label {
  color: var(--text-color-secondary);
}

.gd-suggestion-value,
.gd-opening-value {
  color: var(--text-color);
  font-weight: 500;
  font-family: 'Consolas', 'Monaco', monospace;
}

.gd-error {
  padding: 100px 0;
}

@media (max-width: 1200px) {
  .gd-body {
    grid-template-columns: 200px 1fr 260px;
  }
}

@media (max-width: 992px) {
  .gd-body {
    grid-template-columns: 1fr 1fr;
  }
  .gd-left-panel {
    grid-column: 1;
  }
  .gd-center-panel {
    grid-column: 2;
  }
  .gd-right-panel {
    grid-column: 1 / -1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
}

@media (max-width: 768px) {
  .gd-body {
    grid-template-columns: 1fr;
  }
  .gd-right-panel {
    grid-template-columns: 1fr;
  }
  .gd-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
