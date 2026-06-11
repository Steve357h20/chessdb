<template>
  <div class="move-evaluation" :class="{ 'eval-blunder-flash': isBlunder }">
    <div v-if="!evaluation" class="eval-empty">暂无评价</div>

    <template v-else>
      <div class="eval-header">
        <span
          class="eval-badge"
          :class="badgeClass"
          :style="badgeStyle"
        >{{ evalSymbol }}</span>
        <span class="eval-move">{{ evaluation.move || '' }}</span>
      </div>

      <div class="eval-stats">
        <div class="eval-stat-item">
          <span class="eval-stat-label">分数</span>
          <span class="eval-stat-value" :class="scoreColor">{{ formattedScore }}</span>
        </div>
        <div class="eval-stat-item">
          <span class="eval-stat-label">胜率</span>
          <span class="eval-stat-value">{{ formattedWinRate }}</span>
        </div>
        <div v-if="deltaFromBest != null" class="eval-stat-item">
          <span class="eval-stat-label">差距</span>
          <span class="eval-stat-value" :class="deltaClass">{{ formattedDelta }}</span>
        </div>
      </div>

      <div v-if="evaluation.best_move" class="eval-suggestion">
        <div class="eval-suggestion-label">AI 推荐</div>
        <div class="eval-suggestion-move">{{ evaluation.best_move }}</div>
        <div v-if="evaluation.best_score != null" class="eval-suggestion-score">
          ({{ formatScore(evaluation.best_score) }})
        </div>
      </div>

      <div v-if="evaluation.pv && evaluation.pv.length" class="eval-pv">
        <div class="eval-pv-label">预测续着</div>
        <div class="eval-pv-moves">{{ evaluation.pv.join(' ') }}</div>
      </div>

      <div v-if="evaluation.comment" class="eval-comment">
        <div
          class="eval-comment-toggle"
          @click="commentExpanded = !commentExpanded"
        >
          <span>{{ commentExpanded ? '收起评论' : '展开评论' }}</span>
          <span class="eval-comment-arrow" :class="{ expanded: commentExpanded }">&#9662;</span>
        </div>
        <div v-show="commentExpanded" class="eval-comment-body" v-html="renderedComment"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  evaluation: { type: Object, default: null },
})

const commentExpanded = ref(false)

const EVAL_MAP = {
  '!!': { label: '妙手', color: '#FFD700', class: 'brilliant' },
  '!': { label: '好着', color: '#32CD32', class: 'great' },
  '!?': { label: '有趣', color: '#4169E1', class: 'interesting' },
  '?!': { label: '疑问', color: '#FF8C00', class: 'inaccuracy' },
  '?': { label: '坏着', color: '#FF4500', class: 'mistake' },
  '??': { label: '大坏着', color: '#8B0000', class: 'blunder' },
}

const NAG_MAP = {
  1: '!',
  2: '?',
  3: '!!',
  4: '??',
  5: '!?',
  6: '?!',
}

const evalSymbol = computed(() => {
  if (!props.evaluation) return ''
  if (props.evaluation.evaluation) return props.evaluation.evaluation
  if (props.evaluation.nag != null && NAG_MAP[props.evaluation.nag]) {
    return NAG_MAP[props.evaluation.nag]
  }
  return ''
})

const evalInfo = computed(() => {
  const sym = evalSymbol.value
  return EVAL_MAP[sym] || null
})

const badgeClass = computed(() => {
  if (!evalInfo.value) return ''
  return `badge-${evalInfo.value.class}`
})

const badgeStyle = computed(() => {
  if (!evalInfo.value) return {}
  return {
    backgroundColor: evalInfo.value.color,
    color: ['brilliant', 'interesting'].includes(evalInfo.value.class) ? '#333' : '#fff',
  }
})

const isBlunder = computed(() => {
  const sym = evalSymbol.value
  return sym === '??' || sym === '?'
})

const formattedScore = computed(() => formatScore(props.evaluation?.score))

const formattedWinRate = computed(() => {
  if (props.evaluation?.win_rate == null) return '-'
  return `${Number(props.evaluation.win_rate).toFixed(1)}%`
})

const deltaFromBest = computed(() => {
  if (props.evaluation?.score == null || props.evaluation?.best_score == null) return null
  return props.evaluation.score - props.evaluation.best_score
})

const formattedDelta = computed(() => {
  if (deltaFromBest.value == null) return '-'
  const val = deltaFromBest.value
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}`
})

const scoreColor = computed(() => {
  if (props.evaluation?.score == null) return ''
  if (props.evaluation.score > 0.3) return 'score-positive'
  if (props.evaluation.score < -0.3) return 'score-negative'
  return 'score-neutral'
})

const deltaClass = computed(() => {
  if (deltaFromBest.value == null) return ''
  if (deltaFromBest.value > -0.1) return 'delta-good'
  if (deltaFromBest.value > -0.5) return 'delta-moderate'
  return 'delta-bad'
})

const renderedComment = computed(() => {
  if (!props.evaluation?.comment) return ''
  let text = props.evaluation.comment
  text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  text = text.replace(/\*(.+?)\*/g, '<em>$1</em>')
  text = text.replace(/`(.+?)`/g, '<code>$1</code>')
  text = text.replace(/\n/g, '<br>')
  return text
})

function formatScore(score) {
  if (score == null) return '-'
  const val = Number(score)
  if (Math.abs(val) >= 100) {
    const mateDist = Math.round(Math.abs(val) - 100)
    if (mateDist <= 0) return val > 0 ? '+M1' : '-M1'
    return val > 0 ? `+M${mateDist}` : `-M${mateDist}`
  }
  const sign = val > 0 ? '+' : ''
  return `${sign}${val.toFixed(2)}`
}

watch(
  () => props.evaluation,
  () => {
    if (props.evaluation?.comment) {
      commentExpanded.value = false
    }
  }
)
</script>

<style scoped>
.move-evaluation {
  font-size: 13px;
  background: var(--card-bg);
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  padding: 12px;
  transition: opacity 0.3s ease;
}

.eval-empty {
  text-align: center;
  color: var(--text-color-secondary);
  padding: 16px 0;
}

.eval-blunder-flash {
  animation: blunder-flash 0.6s ease-in-out 2;
}

@keyframes blunder-flash {
  0%, 100% { background-color: #fff; }
  50% { background-color: #fef0f0; }
}

.eval-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.eval-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  padding: 0 6px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 700;
  line-height: 1;
  letter-spacing: 0.5px;
}

.eval-move {
  font-weight: 600;
  font-size: 15px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.eval-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 10px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.eval-stat-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.eval-stat-label {
  font-size: 11px;
  color: var(--text-color-secondary);
}

.eval-stat-value {
  font-weight: 600;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
}

.score-positive { color: #409eff; }
.score-negative { color: #f56c6c; }
.score-neutral { color: var(--text-color-secondary); }

.delta-good { color: #67c23a; }
.delta-moderate { color: #e6a23c; }
.delta-bad { color: #f56c6c; }

.eval-suggestion {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  padding: 6px 8px;
  background: #f0f9eb;
  border-radius: 4px;
}

.eval-suggestion-label {
  font-size: 11px;
  color: #67c23a;
  font-weight: 600;
  flex-shrink: 0;
}

.eval-suggestion-move {
  font-weight: 700;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  color: var(--text-color);
}

.eval-suggestion-score {
  font-size: 12px;
  color: #67c23a;
  font-family: 'Consolas', 'Monaco', monospace;
}

.eval-pv {
  margin-bottom: 8px;
}

.eval-pv-label {
  font-size: 11px;
  color: var(--text-color-secondary);
  margin-bottom: 3px;
}

.eval-pv-moves {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: var(--text-color-regular);
  line-height: 1.5;
  word-break: break-all;
}

.eval-comment {
  margin-top: 8px;
}

.eval-comment-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  color: #409eff;
  user-select: none;
}

.eval-comment-toggle:hover {
  color: #66b1ff;
}

.eval-comment-arrow {
  font-size: 10px;
  transition: transform 0.2s;
}

.eval-comment-arrow.expanded {
  transform: rotate(180deg);
}

.eval-comment-body {
  margin-top: 6px;
  padding: 8px;
  background: var(--bg-color-secondary);
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  color: var(--text-color);
  animation: fade-in 0.2s ease;
}

.eval-comment-body :deep(code) {
  background: #e4e7ed;
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
