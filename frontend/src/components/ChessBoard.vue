<template>
  <div class="chess-board-wrapper" :style="{ width: boardSize + 'px', height: boardSize + 'px' }">
    <div
      ref="boardRef"
      class="chess-board"
      :class="{ interactive }"
      @mousedown="onMouseDown"
      @mousemove="onMouseMove"
      @mouseup="onMouseUp"
      @touchstart.prevent="onTouchStart"
      @touchmove.prevent="onTouchMove"
      @touchend.prevent="onTouchEnd"
    >
      <div
        v-for="(row, rowIdx) in displayBoard"
        :key="rowIdx"
        class="board-row"
      >
        <div
          v-for="(cell, colIdx) in row"
          :key="colIdx"
          class="board-cell"
          :class="{
            'light-square': cell.isLight,
            'dark-square': !cell.isLight,
            'highlight-last-move': isLastMoveSquare(cell.square),
            'highlight-selected': isSelectedSquare(cell.square),
            'highlight-custom': isCustomHighlight(cell.square),
          }"
          :style="cellStyle"
          @click="onCellClick(cell)"
        >
          <div v-if="isLegalMoveSquare(cell.square)" class="legal-move-dot" />
          <div v-if="isLegalCaptureSquare(cell.square)" class="legal-capture-ring" />

          <span
            v-if="cell.piece && !isDraggingPiece(cell.square)"
            class="piece"
            :class="getPieceColor(cell.piece)"
            :style="pieceStyle"
          >{{ pieceUnicode(cell.piece) }}</span>

          <span
            v-if="moveAnnotation && moveAnnotation.symbol && isAnnotationSquare(cell.square)"
            class="move-annotation"
            :class="moveAnnotation.class"
            :title="moveAnnotation.label"
          >{{ moveAnnotation.symbol }}</span>

          <span
            v-if="showCoordinates && colIdx === 0"
            class="coord coord-rank"
          >{{ cell.rank }}</span>
          <span
            v-if="showCoordinates && rowIdx === 7"
            class="coord coord-file"
          >{{ cell.file }}</span>
        </div>
      </div>

      <div
        v-if="dragState.active"
        class="drag-piece"
        :class="getPieceColor(dragState.piece)"
        :style="{
          left: dragState.x - squareSize / 2 + 'px',
          top: dragState.y - squareSize / 2 + 'px',
          fontSize: squareSize * 0.75 + 'px',
        }"
      >{{ pieceUnicode(dragState.piece) }}</div>

      <div v-if="promotionState.active" class="promotion-overlay">
        <div class="promotion-dialog" :style="promotionDialogStyle">
          <div
            v-for="p in promotionPieces"
            :key="p"
            class="promotion-piece"
            :class="getPieceColor(promotionState.color === 'w' ? p.toUpperCase() : p.toLowerCase())"
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
import { ref, computed, watch, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { Chess } from 'chess.js'

const INITIAL_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

const UNICODE_PIECES = {
  K: '\u2654', Q: '\u2655', R: '\u2656', B: '\u2657', N: '\u2658', P: '\u2659',
  k: '\u265A', q: '\u265B', r: '\u265C', b: '\u265D', n: '\u265E', p: '\u265F',
}

const FILES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
const RANKS = ['8', '7', '6', '5', '4', '3', '2', '1']

const props = defineProps({
  fen: { type: String, default: INITIAL_FEN },
  lastMove: { type: Object, default: null },
  orientation: { type: String, default: 'white', validator: v => ['white', 'black'].includes(v) },
  interactive: { type: Boolean, default: false },
  showCoordinates: { type: Boolean, default: true },
  highlightSquares: { type: Array, default: () => [] },
  boardSize: { type: Number, default: 480 },
  moveAnnotation: { type: Object, default: null },
})

const emit = defineEmits(['move-made', 'square-click', 'piece-click'])

const boardRef = ref(null)
const chess = ref(new Chess(props.fen))
const selectedSquare = ref(null)
const legalMoves = ref([])
const internalOrientation = ref(props.orientation)

const dragState = reactive({
  active: false,
  piece: null,
  fromSquare: null,
  x: 0,
  y: 0,
})

const promotionState = reactive({
  active: false,
  color: 'w',
  from: null,
  to: null,
})

const squareSize = computed(() => props.boardSize / 8)

const cellStyle = computed(() => ({
  width: squareSize.value + 'px',
  height: squareSize.value + 'px',
}))

const pieceStyle = computed(() => ({
  fontSize: squareSize.value * 0.75 + 'px',
  lineHeight: squareSize.value + 'px',
}))

const promotionPieces = ['q', 'r', 'b', 'n']

const promotionDialogStyle = computed(() => {
  const isWhite = promotionState.color === 'w'
  return {
    flexDirection: isWhite ? 'column' : 'column-reverse',
  }
})

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

  const ranks = internalOrientation.value === 'white' ? RANKS : [...RANKS].reverse()
  const files = internalOrientation.value === 'white' ? FILES : [...FILES].reverse()

  for (let r = 0; r < 8; r++) {
    const row = []
    for (let c = 0; c < 8; c++) {
      const actualRow = internalOrientation.value === 'white' ? r : 7 - r
      const actualCol = internalOrientation.value === 'white' ? c : 7 - c
      const piece = pieceGrid[actualRow][actualCol]
      const file = files[c]
      const rank = ranks[r]
      const isLight = (actualRow + actualCol) % 2 === 0

      row.push({
        piece,
        square: file + rank,
        file,
        rank,
        isLight,
        row: actualRow,
        col: actualCol,
      })
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

watch(() => props.orientation, (val) => {
  internalOrientation.value = val
})

function pieceUnicode(piece) {
  return UNICODE_PIECES[piece] || ''
}

function getPieceColor(piece) {
  if (!piece) return ''
  return piece === piece.toUpperCase() ? 'white-piece' : 'black-piece'
}

function isLastMoveSquare(square) {
  if (!props.lastMove) return false
  return square === props.lastMove.from || square === props.lastMove.to
}

function isAnnotationSquare(square) {
  if (!props.lastMove) return false
  return square === props.lastMove.to
}

function isSelectedSquare(square) {
  return selectedSquare.value === square
}

function isCustomHighlight(square) {
  return props.highlightSquares.includes(square)
}

function isLegalMoveSquare(square) {
  if (!selectedSquare.value || !legalMoves.value.length) return false
  return legalMoves.value.some(m => m.to === square && !isCaptureMove(m))
}

function isLegalCaptureSquare(square) {
  if (!selectedSquare.value || !legalMoves.value.length) return false
  return legalMoves.value.some(m => m.to === square && isCaptureMove(m))
}

function isCaptureMove(move) {
  return chess.value.get(move.to) !== null || move.flags === 'e'
}

function isDraggingPiece(square) {
  return dragState.active && dragState.fromSquare === square
}

function getSquareFromEvent(e) {
  if (!boardRef.value) return null
  const rect = boardRef.value.getBoundingClientRect()
  let clientX, clientY
  if (e.touches) {
    clientX = e.touches[0].clientX
    clientY = e.touches[0].clientY
  } else {
    clientX = e.clientX
    clientY = e.clientY
  }
  const x = clientX - rect.left
  const y = clientY - rect.top
  const col = Math.floor(x / squareSize.value)
  const row = Math.floor(y / squareSize.value)
  if (col < 0 || col > 7 || row < 0 || row > 7) return null

  const ranks = internalOrientation.value === 'white' ? RANKS : [...RANKS].reverse()
  const files = internalOrientation.value === 'white' ? FILES : [...FILES].reverse()
  return files[col] + ranks[row]
}

function onCellClick(cell) {
  if (dragState.active) return
  const square = cell.square
  emit('square-click', square)

  if (!props.interactive) return

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
      executeMove(selectedSquare.value, square)
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
    emit('piece-click', { square, piece: piece.type })
  }
}

function isOwnPiece(piece) {
  const turn = chess.value.turn()
  return (turn === 'w' && piece.color === 'w') || (turn === 'b' && piece.color === 'b')
}

function selectSquare(square) {
  selectedSquare.value = square
  const moves = chess.value.moves({ square, verbose: true })
  legalMoves.value = moves
}

function executeMove(from, to, promotion = undefined) {
  try {
    const moveObj = chess.value.move({ from, to, promotion })
    if (moveObj) {
      selectedSquare.value = null
      legalMoves.value = []
      emit('move-made', {
        from: moveObj.from,
        to: moveObj.to,
        promotion: moveObj.promotion || null,
      })
    }
  } catch (e) {
    console.error('Invalid move:', e)
    selectedSquare.value = null
    legalMoves.value = []
  }
}

function onPromotionSelect(piece) {
  promotionState.active = false
  if (promotionState.from && promotionState.to) {
    executeMove(promotionState.from, promotionState.to, piece)
  }
}

function onMouseDown(e) {
  if (!props.interactive) return
  const square = getSquareFromEvent(e)
  if (!square) return

  const piece = chess.value.get(square)
  if (piece && isOwnPiece(piece)) {
    selectSquare(square)
    dragState.active = true
    dragState.piece = piece.color === 'w' ? piece.type.toUpperCase() : piece.type.toLowerCase()
    dragState.fromSquare = square
    const rect = boardRef.value.getBoundingClientRect()
    dragState.x = e.clientX - rect.left
    dragState.y = e.clientY - rect.top
  }
}

function onMouseMove(e) {
  if (!dragState.active) return
  const rect = boardRef.value?.getBoundingClientRect()
  if (!rect) return
  dragState.x = e.clientX - rect.left
  dragState.y = e.clientY - rect.top
}

function onMouseUp(e) {
  if (!dragState.active) return
  const square = getSquareFromEvent(e)
  if (square && square !== dragState.fromSquare) {
    const move = legalMoves.value.find(m => m.to === square)
    if (move) {
      if (move.promotion) {
        promotionState.active = true
        promotionState.color = chess.value.turn()
        promotionState.from = dragState.fromSquare
        promotionState.to = square
      } else {
        executeMove(dragState.fromSquare, square)
      }
    }
  }
  dragState.active = false
  dragState.piece = null
  dragState.fromSquare = null
}

function onTouchStart(e) {
  onMouseDown(e.touches[0])
}

function onTouchMove(e) {
  onMouseMove(e.touches[0])
}

function onTouchEnd(e) {
  if (!dragState.active) return
  const touch = e.changedTouches[0]
  const square = getSquareFromEvent({ clientX: touch.clientX, clientY: touch.clientY })
  if (square && square !== dragState.fromSquare) {
    const move = legalMoves.value.find(m => m.to === square)
    if (move) {
      if (move.promotion) {
        promotionState.active = true
        promotionState.color = chess.value.turn()
        promotionState.from = dragState.fromSquare
        promotionState.to = square
      } else {
        executeMove(dragState.fromSquare, square)
      }
    }
  }
  dragState.active = false
  dragState.piece = null
  dragState.fromSquare = null
}

function move(from, to, animation = true, promotion = undefined) {
  try {
    const moveObj = chess.value.move({ from, to, promotion })
    if (moveObj) {
      selectedSquare.value = null
      legalMoves.value = []
      return moveObj
    }
  } catch (e) {
    console.error('Invalid move:', e)
  }
  return null
}

function setPosition(fen) {
  try {
    chess.value = new Chess(fen)
    selectedSquare.value = null
    legalMoves.value = []
  } catch (e) {
    console.error('Invalid FEN:', e)
  }
}

function flip() {
  internalOrientation.value = internalOrientation.value === 'white' ? 'black' : 'white'
}

function highlight(squares) {
  // highlightSquares is a prop, so we emit for parent to update
  // but we also provide a local method via expose
}

defineExpose({
  move,
  setPosition,
  flip,
  highlight,
  getFen: () => chess.value.fen(),
  getChess: () => chess.value,
})
</script>

<style scoped>
.chess-board-wrapper {
  position: relative;
  user-select: none;
  -webkit-user-select: none;
}

.chess-board {
  position: relative;
  display: flex;
  flex-direction: column;
  border: 2px solid #333;
  border-radius: 2px;
  overflow: hidden;
}

.chess-board.interactive {
  cursor: pointer;
}

.board-row {
  display: flex;
}

.board-cell {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.light-square {
  background-color: #F0D9B5;
}

.dark-square {
  background-color: #B58863;
}

.highlight-last-move.light-square {
  background-color: #F6F669;
}

.highlight-last-move.dark-square {
  background-color: #BACA2B;
}

.highlight-selected.light-square {
  background-color: rgba(20, 85, 30, 0.5);
}

.highlight-selected.dark-square {
  background-color: rgba(20, 85, 30, 0.6);
}

.highlight-custom::after {
  content: '';
  position: absolute;
  inset: 0;
  background-color: rgba(255, 255, 0, 0.4);
  pointer-events: none;
}

.piece {
  position: absolute;
  z-index: 2;
  pointer-events: none;
  text-align: center;
  transition: none;
  filter: drop-shadow(1px 1px 1px rgba(0, 0, 0, 0.3));
}

.white-piece {
  color: #fff;
  -webkit-text-stroke: 0.5px #333;
  text-shadow:
    0 0 2px rgba(0, 0, 0, 0.5),
    0 0 4px rgba(0, 0, 0, 0.2);
}

.black-piece {
  color: #333;
  text-shadow:
    0 0 2px rgba(0, 0, 0, 0.3);
}

.legal-move-dot {
  position: absolute;
  width: 28%;
  height: 28%;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.2);
  z-index: 3;
  pointer-events: none;
}

.legal-capture-ring {
  position: absolute;
  width: 90%;
  height: 90%;
  border-radius: 50%;
  border: 5px solid rgba(0, 0, 0, 0.2);
  z-index: 3;
  pointer-events: none;
  box-sizing: border-box;
}

.coord {
  position: absolute;
  font-size: 10px;
  font-weight: 700;
  pointer-events: none;
  z-index: 4;
  line-height: 1;
}

.coord-rank {
  top: 2px;
  left: 3px;
}

.coord-file {
  bottom: 2px;
  right: 3px;
}

.light-square .coord {
  color: #B58863;
}

.dark-square .coord {
  color: #F0D9B5;
}

.drag-piece {
  position: absolute;
  z-index: 100;
  pointer-events: none;
  text-align: center;
  line-height: 1;
  filter: drop-shadow(2px 2px 3px rgba(0, 0, 0, 0.4));
  transform: translate(-50%, -50%);
}

.promotion-overlay {
  position: absolute;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
}

.promotion-dialog {
  background-color: #fff;
  border-radius: 6px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3);
  display: flex;
  overflow: hidden;
}

.promotion-piece {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42px;
  cursor: pointer;
  transition: background-color 0.15s;
}

.promotion-piece:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

.promotion-piece.white-piece {
  color: #fff;
  -webkit-text-stroke: 0.5px #333;
  text-shadow: 0 0 2px rgba(0, 0, 0, 0.5);
}

.promotion-piece.black-piece {
  color: #333;
}

.move-annotation {
  position: absolute;
  top: 1px;
  right: 2px;
  font-size: 12px;
  font-weight: 800;
  font-family: 'Arial', 'Helvetica', sans-serif;
  z-index: 5;
  pointer-events: none;
  line-height: 1;
  text-shadow: 0 0 3px rgba(255, 255, 255, 0.8), 0 0 3px rgba(255, 255, 255, 0.8);
}

.move-annotation.eval-brilliant {
  color: #00bcd4;
}

.move-annotation.eval-great {
  color: #4caf50;
}

.move-annotation.eval-inaccuracy {
  color: #fdd835;
}

.move-annotation.eval-mistake {
  color: #ff9800;
}

.move-annotation.eval-blunder {
  color: #f44336;
}
</style>
