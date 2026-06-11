<template>
  <div class="practice-board-wrapper">
    <div v-if="isAiThinking" class="pb-thinking-bar">
      <el-icon class="pb-thinking-icon is-loading"><Loading /></el-icon>
      <span>AI 思考中...</span>
    </div>

    <div
      class="practice-board"
      :style="{ width: boardSize + 'px', height: boardSize + 'px' }"
    >
      <div
        v-for="(row, rowIdx) in displayBoard"
        :key="rowIdx"
        class="pb-row"
      >
        <div
          v-for="(cell, colIdx) in row"
          :key="colIdx"
          class="pb-cell"
          :class="{
            'pb-light': cell.isLight,
            'pb-dark': !cell.isLight,
            'pb-selected': cell.square === selectedSquare,
            'pb-last-move': isLastMoveSquare(cell.square),
            'pb-last-move-ai': isLastMoveSquare(cell.square) && lastMoveIsAi,
            'pb-hint-target': isHintTargetSquare(cell.square),
            'pb-hint-from': isHintFromSquare(cell.square),
            'pb-king-check': isKingInCheck(cell.square),
            'pb-king-checkmate': props.inCheckmate && isKingInCheck(cell.square),
          }"
          :style="cellStyle"
          @click="onCellClick(cell)"
        >
          <div v-if="isLegalEmptySquare(cell.square)" class="pb-legal-dot" />
          <div v-if="isLegalCaptureSquare(cell.square)" class="pb-legal-ring" />

          <span
            v-if="cell.piece"
            class="pb-piece"
            :class="cell.piece === cell.piece.toUpperCase() ? 'pb-white-piece' : 'pb-black-piece'"
            :style="pieceStyle"
          >{{ pieceUnicode(cell.piece) }}</span>

          <span
            v-if="showCoordinates && colIdx === 0"
            class="pb-coord pb-coord-rank"
          >{{ cell.rank }}</span>
          <span
            v-if="showCoordinates && rowIdx === 7"
            class="pb-coord pb-coord-file"
          >{{ cell.file }}</span>
        </div>
      </div>

      <div v-if="promotionState.active" class="pb-promotion-overlay">
        <div class="pb-promotion-dialog" :style="promotionDialogStyle">
          <div
            v-for="p in promotionPieces"
            :key="p"
            class="pb-promotion-piece"
            :class="promotionState.color === 'w' ? 'pb-white-piece' : 'pb-black-piece'"
            @click="onPromotionSelect(p)"
          >
            {{ pieceUnicode(promotionState.color === 'w' ? p.toUpperCase() : p.toLowerCase()) }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, reactive } from 'vue'
import { Chess } from 'chess.js'
import { Loading } from '@element-plus/icons-vue'

const UNICODE_PIECES = {
  K: '\u2654', Q: '\u2655', R: '\u2656', B: '\u2657', N: '\u2658', P: '\u2659',
  k: '\u265A', q: '\u265B', r: '\u265C', b: '\u265D', n: '\u265E', p: '\u265F',
}

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
const RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']
const PROMOTION_PIECES = ['q', 'r', 'b', 'n']

const props = defineProps({
  fen: { type: String, default: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1' },
  userColor: { type: String, default: 'white' },
  lastAiMove: { type: Object, default: null },
  lastUserMove: { type: Object, default: null },
  lastMoveFromTo: { type: Object, default: null },
  hintMove: { type: String, default: '' },
  isUserTurn: { type: Boolean, default: true },
  isAiThinking: { type: Boolean, default: false },
  boardSize: { type: Number, default: 560 },
  showCoordinates: { type: Boolean, default: true },
  inCheck: { type: Boolean, default: false },
  inCheckmate: { type: Boolean, default: false },
})

const emit = defineEmits(['move-submit'])

const chess = ref(new Chess(props.fen))
const selectedSquare = ref(null)
const legalMoves = ref([])
const hintTargetSquares = ref([])
const hintFromSquare = ref(null)
const lastMoveSquares = ref([])
const lastMoveIsAi = ref(false)

const promotionState = reactive({
  active: false,
  color: 'w',
  from: null,
  to: null,
})

const promotionPieces = PROMOTION_PIECES

const promotionDialogStyle = computed(() => ({
  flexDirection: promotionState.color === 'w' ? 'column' : 'column-reverse',
}))

const squareSize = computed(() => props.boardSize / 8)
const cellStyle = computed(() => ({ width: squareSize.value + 'px', height: squareSize.value + 'px' }))
const pieceStyle = computed(() => ({ fontSize: squareSize.value * 0.75 + 'px', lineHeight: squareSize.value + 'px' }))

const orientation = computed(() => props.userColor === 'white' ? 'white' : 'black')

const displayBoard = computed(() => {
  const board = []
  const fenRows = chess.value.fen().split(' ')[0].split('/')
  const pieceGrid = []

  for (const row of fenRows) {
    const gridRow = []
    for (const ch of row) {
      if (ch >= '1' && ch <= '8') {
        for (let i = 0; i < parseInt(ch); i++) gridRow.push(null)
      } else {
        gridRow.push(ch)
      }
    }
    pieceGrid.push(gridRow)
  }

  const ranks = orientation.value === 'white' ? RANKS : [...RANKS].reverse()
  const files = orientation.value === 'white' ? FILES : [...FILES].reverse()

  for (let r = 0; r < 8; r++) {
    const row = []
    for (let c = 0; c < 8; c++) {
      const actualRow = orientation.value === 'white' ? r : 7 - r
      const actualCol = orientation.value === 'white' ? c : 7 - c
      const piece = pieceGrid[actualRow][actualCol]
      const file = files[c]
      const rank = ranks[r]
      const isLight = (actualRow + actualCol) % 2 === 0

      row.push({ piece, square: file + rank, file, rank, isLight, row: actualRow, col: actualCol })
    }
    board.push(row)
  }
  return board
})

watch(() => props.fen, (newFen) => {
  try {
    chess.value = new Chess(newFen)
    selectedSquare.value = null
    legalMoves.value = []
  } catch (e) {
    console.error('Invalid FEN:', e)
  }
})

watch(() => props.lastMoveFromTo, (newVal) => {
  if (newVal && newVal.from && newVal.to) {
    lastMoveSquares.value = [newVal.from, newVal.to]
    lastMoveIsAi.value = !!newVal.isAi
  } else {
    lastMoveSquares.value = []
    lastMoveIsAi.value = false
  }
}, { immediate: true })

watch(() => props.hintMove, (newHint) => {
  hintTargetSquares.value = []
  hintFromSquare.value = null
  if (!newHint) return
  try {
    const tempChess = new Chess(props.fen)
    const move = tempChess.move(newHint)
    if (move) {
      hintTargetSquares.value = [move.to]
      hintFromSquare.value = move.from
    }
  } catch {
    try {
      const moves = chess.value.moves({ verbose: true })
      const found = moves.find(m => m.san === newHint)
      if (found) {
        hintTargetSquares.value = [found.to]
        hintFromSquare.value = found.from
      }
    } catch { /* ignore */ }
  }
})

function pieceUnicode(piece) {
  return UNICODE_PIECES[piece] || ''
}

function isOwnPiece(piece) {
  const turn = chess.value.turn()
  return (turn === 'w' && piece.color === 'w') || (turn === 'b' && piece.color === 'b')
}

function isLastMoveSquare(square) {
  return lastMoveSquares.value.includes(square)
}

function isKingInCheck(square) {
  if (!props.inCheck && !props.inCheckmate) return false
  const piece = chess.value.get(square)
  if (!piece || piece.type !== 'k') return false
  const turn = chess.value.turn()
  return piece.color === turn
}

function isHintTargetSquare(square) {
  return hintTargetSquares.value.includes(square)
}

function isHintFromSquare(square) {
  return hintFromSquare.value === square
}

function isLegalEmptySquare(square) {
  if (!selectedSquare.value || !legalMoves.value.length) return false
  return legalMoves.value.some(m => m.to === square && !chess.value.get(m.to) && m.flags !== 'e')
}

function isLegalCaptureSquare(square) {
  if (!selectedSquare.value || !legalMoves.value.length) return false
  return legalMoves.value.some(m => m.to === square && (chess.value.get(m.to) || m.flags === 'e'))
}

function onCellClick(cell) {
  if (!props.isUserTurn || props.isAiThinking) return
  if (promotionState.active) return

  const square = cell.square
  const piece = chess.value.get(square)

  if (selectedSquare.value) {
    const move = legalMoves.value.find(m => m.to === square)
    if (move) {
      if (move.promotion) {
        promotionState.active = true
        promotionState.color = chess.value.turn()
        promotionState.from = selectedSquare.value
        promotionState.to = square
        selectedSquare.value = null
        legalMoves.value = []
        return
      }
      lastMoveIsAi.value = false
      emit('move-submit', move.san)
      selectedSquare.value = null
      legalMoves.value = []
      return
    }

    if (piece && isOwnPiece(piece)) {
      selectSquare(square)
      return
    }

    selectedSquare.value = null
    legalMoves.value = []
    return
  }

  if (piece && isOwnPiece(piece)) {
    selectSquare(square)
  }
}

function onPromotionSelect(piece) {
  promotionState.active = false
  if (promotionState.from && promotionState.to) {
    const tempChess = new Chess(props.fen)
    try {
      const moveObj = tempChess.move({ from: promotionState.from, to: promotionState.to, promotion: piece })
      if (moveObj) {
        lastMoveIsAi.value = false
        emit('move-submit', moveObj.san)
      }
    } catch (e) {
      console.error('Invalid promotion:', e)
    }
  }
}

function selectSquare(square) {
  selectedSquare.value = square
  legalMoves.value = chess.value.moves({ square, verbose: true })
}
</script>

<style scoped>
.practice-board-wrapper {
  display: inline-block;
  user-select: none;
  -webkit-user-select: none;
}

.pb-thinking-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 0;
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
}

.pb-thinking-icon {
  font-size: 18px;
  animation: rotating 1.5s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.practice-board {
  display: flex;
  flex-direction: column;
  border: 2px solid #333;
  border-radius: 2px;
  overflow: hidden;
  cursor: pointer;
}

.pb-row {
  display: flex;
}

.pb-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pb-light { background-color: #F0D9B5; }
.pb-dark { background-color: #B58863; }

.pb-selected.pb-light { background-color: rgba(20, 85, 30, 0.5); }
.pb-selected.pb-dark { background-color: rgba(20, 85, 30, 0.6); }

.pb-last-move.pb-light { background-color: #F6F669; }
.pb-last-move.pb-dark { background-color: #BACA2B; }

.pb-last-move-ai.pb-light { background-color: #FFB366; }
.pb-last-move-ai.pb-dark { background-color: #E68A00; }

.pb-king-check {
  background: radial-gradient(circle, #ff0000 0%, #ff000088 40%, transparent 70%) !important;
}

.pb-king-checkmate {
  background: #8b1a1a !important;
}

.pb-hint-target::after {
  content: '';
  position: absolute;
  width: 50%;
  height: 50%;
  border-radius: 50%;
  background-color: rgba(64, 158, 255, 0.6);
  pointer-events: none;
  z-index: 3;
}

.pb-hint-from::after {
  content: '';
  position: absolute;
  width: 90%;
  height: 90%;
  border-radius: 50%;
  border: 5px solid rgba(64, 158, 255, 0.6);
  pointer-events: none;
  z-index: 3;
  box-sizing: border-box;
}

.pb-piece {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  text-align: center;
  filter: drop-shadow(1px 1px 1px rgba(0, 0, 0, 0.3));
}

.pb-white-piece {
  color: #fff;
  -webkit-text-stroke: 0.5px #333;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5), 0 0 4px rgba(0, 0, 0, 0.2);
}

.pb-black-piece {
  color: #333;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.3);
}

.pb-legal-dot {
  position: absolute;
  width: 28%;
  height: 28%;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.2);
  z-index: 3;
  pointer-events: none;
}

.pb-legal-ring {
  position: absolute;
  width: 90%;
  height: 90%;
  border-radius: 50%;
  border: 5px solid rgba(0, 0, 0, 0.2);
  z-index: 3;
  pointer-events: none;
  box-sizing: border-box;
}

.pb-coord {
  position: absolute;
  font-size: 10px;
  font-weight: 700;
  pointer-events: none;
  z-index: 4;
  line-height: 1;
}

.pb-coord-rank { top: 2px; left: 3px; }
.pb-coord-file { bottom: 2px; right: 3px; }

.pb-light .pb-coord { color: #B58863; }
.pb-dark .pb-coord { color: #F0D9B5; }

.pb-promotion-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pb-promotion-dialog {
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  display: flex;
  overflow: hidden;
}

.pb-promotion-piece {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.pb-promotion-piece:hover {
  background-color: rgba(0, 0, 0, 0.1);
}
</style>
