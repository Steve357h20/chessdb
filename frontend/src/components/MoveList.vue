<template>
  <div
    ref="listRef"
    class="move-list"
    tabindex="0"
    @keydown="onKeyDown"
  >
    <div v-if="!moves.length" class="move-list-empty">暂无着法</div>
    <div v-else class="move-list-body">
      <div
        v-for="row in displayMoves"
        :key="row.move_number"
        :ref="el => setRowRef(row.move_number, el)"
        class="move-row"
        :class="{
          'move-row-even': row.move_number % 2 === 0,
          'move-row-active': isRowActive(row.move_number),
        }"
      >
        <span class="move-number">{{ row.move_number }}.</span>
        <span
          class="move-cell"
          :class="{
            'move-cell-active': currentMove === row.white_half_move,
          }"
          @click="onMoveClick(row.move_number, 'white')"
        >
          <span class="move-text">{{ row.white || '...' }}</span>
          <span
            v-if="showEvaluation && row.white_eval && evalSymbol(row.white_eval)"
            class="move-eval"
            :class="evalClass(row.white_eval)"
            :title="evalTooltip(row.white_eval)"
          >{{ evalSymbol(row.white_eval) }}</span>
        </span>
        <span
          class="move-cell"
          :class="{
            'move-cell-active': row.black && currentMove === row.black_half_move,
          }"
          @click="onMoveClick(row.move_number, 'black')"
        >
          <span class="move-text">{{ row.black || '...' }}</span>
          <span
            v-if="showEvaluation && row.black_eval && evalSymbol(row.black_eval)"
            class="move-eval"
            :class="evalClass(row.black_eval)"
            :title="evalTooltip(row.black_eval)"
          >{{ evalSymbol(row.black_eval) }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { classifyMove } from '@/utils/chessUtils'

const props = defineProps({
  moves: { type: Array, default: () => [] },
  currentMove: { type: Number, default: 0 },
  showEvaluation: { type: Boolean, default: true },
})

const emit = defineEmits(['move-click'])

const listRef = ref(null)
const rowRefs = {}

function setRowRef(moveNumber, el) {
  if (el) rowRefs[moveNumber] = el
}

const displayMoves = computed(() => props.moves)

function isRowActive(moveNumber) {
  const half = props.currentMove
  return half === moveNumber * 2 - 1 || half === moveNumber * 2
}

function onMoveClick(moveNumber, color) {
  const halfMove = color === 'white' ? moveNumber * 2 - 1 : moveNumber * 2
  emit('move-click', halfMove)
}

const EVAL_SYMBOLS = {
  brilliant: '!!',
  great: '!',
  good: '',
  interesting: '!?',
  inaccuracy: '?!',
  mistake: '?',
  blunder: '??',
}

const EVAL_LABELS = {
  brilliant: '妙着',
  great: '好着',
  good: '正常',
  interesting: '有趣',
  inaccuracy: '不精确',
  mistake: '失误',
  blunder: '严重失误',
}

function getEvalClassification(evalData) {
  if (!evalData) return ''
  if (evalData.classification) return evalData.classification
  if (evalData.delta != null) return classifyMove(evalData.delta)
  return ''
}

function evalSymbol(evalData) {
  const cls = getEvalClassification(evalData)
  return EVAL_SYMBOLS[cls] || ''
}

function evalClass(evalData) {
  const cls = getEvalClassification(evalData)
  return cls ? `eval-${cls}` : ''
}

function evalTooltip(evalData) {
  const cls = getEvalClassification(evalData)
  let tip = EVAL_LABELS[cls] || ''
  if (evalData.delta != null) {
    const sign = evalData.delta > 0 ? '+' : ''
    tip += ` (${sign}${(evalData.delta / 100).toFixed(2)})`
  }
  return tip
}

function onKeyDown(e) {
  if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
    e.preventDefault()
    const prev = Math.max(0, props.currentMove - 1)
    if (prev !== props.currentMove) emit('move-click', prev)
  } else if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
    e.preventDefault()
    const next = Math.min(props.moves.length, props.currentMove + 1)
    if (next !== props.currentMove) emit('move-click', next)
  } else if (e.key === 'Home') {
    e.preventDefault()
    emit('move-click', 0)
  } else if (e.key === 'End') {
    e.preventDefault()
    if (props.moves.length) {
      const lastRow = props.moves[props.moves.length - 1]
      const lastHalf = lastRow.black ? lastRow.move_number * 2 : lastRow.move_number * 2 - 1
      emit('move-click', lastHalf)
    }
  }
}

function scrollToCurrentMove() {
  nextTick(() => {
    const targetMoveNum = Math.ceil(props.currentMove / 2) || 1
    const el = rowRefs[targetMoveNum]
    if (el) {
      el.scrollIntoView({ block: 'nearest', behavior: 'smooth' })
    }
  })
}

watch(() => props.currentMove, scrollToCurrentMove)

onMounted(() => {
  scrollToCurrentMove()
})
</script>

<style scoped>
.move-list {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 4px;
  overflow-y: auto;
  outline: none;
  height: 100%;
}

.move-list:focus {
  border-color: #409eff;
}

.move-list-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--text-color-secondary);
  font-size: 13px;
}

.move-list-body {
  padding: 4px 0;
}

.move-row {
  display: flex;
  align-items: center;
  padding: 3px 8px;
  min-height: 28px;
  transition: background-color 0.15s;
}

.move-row-even {
  background-color: #fafafa;
}

.move-row-active {
  background-color: #ecf5ff;
}

.move-number {
  width: 36px;
  flex-shrink: 0;
  color: var(--text-color-secondary);
  font-size: 12px;
  text-align: right;
  padding-right: 8px;
  user-select: none;
}

.move-cell {
  flex: 1;
  display: inline-flex;
  align-items: center;
  padding: 2px 6px;
  border-radius: 3px;
  cursor: pointer;
  min-width: 0;
  position: relative;
  transition: background-color 0.15s;
}

.move-cell:hover {
  background-color: #f0f0f0;
}

.move-cell-active {
  background-color: #409eff;
  color: #fff;
}

.move-cell-active:hover {
  background-color: #66b1ff;
}

.move-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.move-cell-active .move-text {
  color: #fff;
}

.move-eval {
  position: absolute;
  top: -2px;
  right: 1px;
  font-size: 10px;
  font-weight: 800;
  flex-shrink: 0;
  line-height: 1;
  pointer-events: none;
}

.move-cell-active .move-eval {
  color: #fff;
}

.eval-brilliant {
  color: #26c6da;
  text-shadow: 0 0 3px rgba(38, 198, 218, 0.4);
}

.eval-great {
  color: #66bb6a;
  text-shadow: 0 0 3px rgba(102, 187, 106, 0.4);
}

.eval-good {
  color: var(--text-color-secondary);
}

.eval-interesting {
  color: #4169E1;
  text-shadow: 0 0 3px rgba(65, 105, 225, 0.4);
}

.eval-inaccuracy {
  color: #fdd835;
  text-shadow: 0 0 3px rgba(253, 216, 53, 0.4);
}

.eval-mistake {
  color: #ff9800;
  text-shadow: 0 0 3px rgba(255, 152, 0, 0.4);
}

.eval-blunder {
  color: #ef5350;
  text-shadow: 0 0 3px rgba(239, 83, 80, 0.4);
}
</style>
