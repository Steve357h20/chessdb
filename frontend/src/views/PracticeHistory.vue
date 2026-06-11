<template>
  <div class="practice-history-page">
    <div class="ph-header">
      <el-button text @click="$router.push('/practice')">
        <el-icon><ArrowLeft /></el-icon> 返回练习
      </el-button>
      <h2 class="ph-title">AI对弈练习历史</h2>
    </div>

    <el-row :gutter="16" class="ph-stats-row">
      <el-col :span="6">
        <el-card shadow="hover" class="ph-stat-card">
          <div class="ph-stat-value">{{ stats.totalGames }}</div>
          <div class="ph-stat-label">总对局数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="ph-stat-card">
          <div class="ph-stat-value ph-stat-win">{{ stats.winRate }}%</div>
          <div class="ph-stat-label">胜率</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="ph-stat-card">
          <div class="ph-stat-value">{{ stats.avgMoves }}</div>
          <div class="ph-stat-label">平均步数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover" class="ph-stat-card">
          <div class="ph-stat-value">{{ stats.topDifficulty }}</div>
          <div class="ph-stat-label">最常用难度</div>
        </el-card>
      </el-col>
    </el-row>

    <div class="ph-filters">
      <el-select v-model="filterDifficulty" placeholder="难度" clearable size="small" style="width: 120px" @change="onFilterChange">
        <el-option label="入门" value="beginner" />
        <el-option label="初级" value="easy" />
        <el-option label="中级" value="medium" />
        <el-option label="高级" value="hard" />
        <el-option label="专家" value="expert" />
      </el-select>
      <el-select v-model="filterMode" placeholder="模式" clearable size="small" style="width: 120px" @change="onFilterChange">
        <el-option label="残局练习" value="puzzle" />
        <el-option label="从棋谱开始" value="from_game" />
        <el-option label="自定义FEN" value="custom" />
      </el-select>
      <el-select v-model="filterResult" placeholder="结果" clearable size="small" style="width: 120px" @change="onFilterChange">
        <el-option label="胜" value="win" />
        <el-option label="负" value="lose" />
        <el-option label="和" value="draw" />
      </el-select>
    </div>

    <el-table :data="history" stripe style="width: 100%" v-loading="loading">
      <el-table-column label="日期" prop="created_at" width="170">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="模式" width="110">
        <template #default="{ row }">
          <el-tag size="small" :type="modeTagType(row.mode)">{{ modeLabel(row.mode) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="难度" width="90">
        <template #default="{ row }">
          {{ difficultyLabel(row.difficulty) }}
        </template>
      </el-table-column>
      <el-table-column label="执棋" width="80">
        <template #default="{ row }">
          {{ row.user_color === 'w' ? '白方' : '黑方' }}
        </template>
      </el-table-column>
      <el-table-column label="结果" width="80">
        <template #default="{ row }">
          <span :class="resultClass(row)">{{ resultLabel(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="步数" prop="total_moves" width="80" />
      <el-table-column label="提示" prop="hints_used" width="70" />
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button size="small" type="primary" text @click="$router.push(`/practice/review/${row.id}`)">
            复盘
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="ph-pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="perPage"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="loadHistory"
        @size-change="loadHistory"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowLeft } from '@element-plus/icons-vue'
import { getPracticeHistory } from '@/api/practice'

const loading = ref(false)
const history = ref([])
const total = ref(0)
const page = ref(1)
const perPage = ref(20)

const filterDifficulty = ref('')
const filterMode = ref('')
const filterResult = ref('')

const stats = computed(() => {
  const all = history.value
  const totalGames = all.length
  if (totalGames === 0) {
    return { totalGames: 0, winRate: 0, avgMoves: 0, topDifficulty: '-' }
  }

  const wins = all.filter(h => getResultType(h) === 'win').length
  const winRate = Math.round((wins / totalGames) * 100)
  const avgMoves = Math.round(all.reduce((s, h) => s + (h.total_moves || 0), 0) / totalGames)

  const diffCount = {}
  all.forEach(h => {
    const d = h.difficulty || 'medium'
    diffCount[d] = (diffCount[d] || 0) + 1
  })
  const topDifficulty = Object.entries(diffCount).sort((a, b) => b[1] - a[1])[0]?.[0] || 'medium'

  return { totalGames, winRate, avgMoves, topDifficulty: difficultyLabel(topDifficulty) }
})

function getResultType(row) {
  if (row.result === '1/2-1/2') return 'draw'
  if (row.result === '1-0' && row.user_color === 'w') return 'win'
  if (row.result === '0-1' && row.user_color === 'b') return 'win'
  return 'lose'
}

function difficultyLabel(diff) {
  const map = { beginner: '入门', easy: '初级', medium: '中级', hard: '高级', expert: '专家' }
  return map[diff] || diff
}

function modeLabel(mode) {
  const map = { puzzle: '残局', from_game: '棋谱', custom: '自定义' }
  return map[mode] || mode
}

function modeTagType(mode) {
  const map = { puzzle: 'primary', from_game: 'success', custom: 'warning' }
  return map[mode] || 'info'
}

function resultLabel(row) {
  const type = getResultType(row)
  const map = { win: '胜', lose: '负', draw: '和' }
  return map[type] || row.result
}

function resultClass(row) {
  const type = getResultType(row)
  const map = { win: 'ph-result-win', lose: 'ph-result-lose', draw: 'ph-result-draw' }
  return map[type] || ''
}

function formatDate(isoStr) {
  if (!isoStr) return '-'
  try {
    const d = new Date(isoStr)
    return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  } catch {
    return isoStr
  }
}

function onFilterChange() {
  page.value = 1
  loadHistory()
}

async function loadHistory() {
  loading.value = true
  try {
    const params = {
      page: page.value,
      per_page: perPage.value,
    }
    if (filterDifficulty.value) params.difficulty = filterDifficulty.value
    if (filterMode.value) params.mode = filterMode.value
    if (filterResult.value) params.result = filterResult.value

    const res = await getPracticeHistory(params)
    const data = res.data || res
    history.value = data.history || data.items || []
    total.value = data.total || history.value.length
  } catch {
    history.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.practice-history-page {
  max-width: 1000px;
  margin: 0 auto;
}

.ph-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.ph-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.ph-stats-row {
  margin-bottom: 20px;
}

.ph-stat-card {
  text-align: center;
}

.ph-stat-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-color);
  font-family: 'Consolas', 'Monaco', monospace;
}

.ph-stat-win {
  color: #67c23a;
}

.ph-stat-label {
  font-size: 13px;
  color: var(--text-color-secondary);
  margin-top: 4px;
}

.ph-filters {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.ph-result-win { color: #67c23a; font-weight: 600; }
.ph-result-lose { color: #f56c6c; font-weight: 600; }
.ph-result-draw { color: #e6a23c; font-weight: 600; }

.ph-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>
