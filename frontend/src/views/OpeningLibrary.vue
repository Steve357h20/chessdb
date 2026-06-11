<template>
  <div class="opening-page">
    <div class="op-header">
      <h1>开局库</h1>
    </div>

    <div class="op-filters">
      <el-input
        v-model="filters.search"
        placeholder="搜索开局名称/ECO代码"
        clearable
        :prefix-icon="Search"
        style="width: 220px"
        @clear="onFilterChange"
        @keyup.enter="onFilterChange"
      />
      <el-select
        v-model="filters.category"
        placeholder="开局大类"
        clearable
        style="width: 160px"
        @change="onFilterChange"
      >
        <el-option label="A - 侧翼开局" value="A" />
        <el-option label="B - 半开放开局" value="B" />
        <el-option label="C - 开放开局" value="C" />
        <el-option label="D - 封闭/半封闭开局" value="D" />
        <el-option label="E - 印度防御" value="E" />
      </el-select>
      <el-select
        v-model="filters.sort"
        placeholder="排序方式"
        style="width: 150px"
        @change="onFilterChange"
      >
        <el-option label="ECO代码" value="eco_code" />
        <el-option label="名称" value="name" />
        <el-option label="白方胜率" value="white_win_rate" />
        <el-option label="黑方胜率" value="black_win_rate" />
        <el-option label="和棋率" value="draw_rate" />
        <el-option label="对局数量" value="popularity" />
      </el-select>
      <el-select
        v-model="filters.order"
        style="width: 100px"
        @change="onFilterChange"
      >
        <el-option label="升序" value="asc" />
        <el-option label="降序" value="desc" />
      </el-select>
      <el-button-group>
        <el-button :type="viewMode === 'card' ? 'primary' : ''" @click="viewMode = 'card'">
          <el-icon><Grid /></el-icon>
        </el-button>
        <el-button :type="viewMode === 'table' ? 'primary' : ''" @click="viewMode = 'table'">
          <el-icon><List /></el-icon>
        </el-button>
      </el-button-group>
      <el-button @click="clearFilters">清除筛选</el-button>
    </div>

    <div v-loading="loading" class="op-content">
      <div v-if="!loading && openings.length === 0" class="op-empty">
        <el-empty description="暂无开局数据" />
      </div>

      <template v-if="viewMode === 'card'">
        <el-row :gutter="16">
          <el-col
            v-for="opening in openings"
            :key="opening.eco_code"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <el-card class="op-card" shadow="hover" @click="showDetail(opening)">
              <div class="op-card-header">
                <el-tag type="info" size="small">{{ opening.eco_code }}</el-tag>
                <span class="op-card-category">{{ getCategoryName(opening.category) }}</span>
              </div>
              <div class="op-card-name">{{ opening.name }}</div>
              <div v-if="opening.variation" class="op-card-variation">{{ opening.variation }}</div>
              <div v-if="opening.moves && opening.moves.length" class="op-card-moves">
                <span class="op-moves-label">走法：</span>
                <span class="op-moves-text">{{ opening.moves.slice(0, 8).join(' ') }}{{ opening.moves.length > 8 ? '...' : '' }}</span>
              </div>
              <div class="op-card-stats">
                <div class="op-stat">
                  <span class="op-stat-label">白胜</span>
                  <el-progress :percentage="opening.white_win_rate" :stroke-width="6" :color="'#f56c6c'" :show-text="true" :format="(p) => p + '%'" />
                </div>
                <div class="op-stat">
                  <span class="op-stat-label">和棋</span>
                  <el-progress :percentage="opening.draw_rate" :stroke-width="6" :color="'#e6a23c'" :show-text="true" :format="(p) => p + '%'" />
                </div>
                <div class="op-stat">
                  <span class="op-stat-label">黑胜</span>
                  <el-progress :percentage="opening.black_win_rate" :stroke-width="6" :color="'#409eff'" :show-text="true" :format="(p) => p + '%'" />
                </div>
              </div>
              <div v-if="opening.popularity" class="op-card-popularity">
                对局数: {{ opening.popularity }}
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else>
        <el-table ref="openingTableRef" :data="openings" stripe style="width: 100%" @row-click="showDetail" class="op-table">
          <el-table-column prop="eco_code" label="ECO" width="80" sortable />
          <el-table-column prop="name" label="开局名称" min-width="180" />
          <el-table-column prop="variation" label="变例" min-width="140">
            <template #default="{ row }">{{ row.variation || '-' }}</template>
          </el-table-column>
          <el-table-column label="大类" width="120">
            <template #default="{ row }">{{ getCategoryName(row.category) }}</template>
          </el-table-column>
          <el-table-column prop="white_win_rate" label="白胜率" width="100" sortable>
            <template #default="{ row }">
              <span class="op-wr-white">{{ row.white_win_rate }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="draw_rate" label="和棋率" width="100" sortable>
            <template #default="{ row }">
              <span class="op-wr-draw">{{ row.draw_rate }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="black_win_rate" label="黑胜率" width="100" sortable>
            <template #default="{ row }">
              <span class="op-wr-black">{{ row.black_win_rate }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="popularity" label="对局数" width="90" sortable>
            <template #default="{ row }">{{ row.popularity || 0 }}</template>
          </el-table-column>
          <el-table-column label="走法" min-width="160">
            <template #default="{ row }">
              <span v-if="row.moves && row.moves.length" class="op-moves-text">{{ row.moves.slice(0, 6).join(' ') }}{{ row.moves.length > 6 ? '...' : '' }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </div>

    <div v-if="openings.length" class="op-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[12, 24, 48, 100]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="onPageSizeChange"
        @current-change="onPageChange"
      />
    </div>

    <el-dialog
      v-model="detailVisible"
      :title="detailData?.name || '开局详情'"
      width="680px"
      destroy-on-close
    >
      <div v-loading="detailLoading" class="op-detail">
        <template v-if="detailData">
          <div class="op-detail-header">
            <el-tag type="info">{{ detailData.eco_code }}</el-tag>
            <span v-if="detailData.category" class="op-detail-category">{{ getCategoryName(detailData.category) }}</span>
          </div>
          <div v-if="detailData.variation" class="op-detail-variation">{{ detailData.variation }}</div>
          <div v-if="detailData.moves && detailData.moves.length" class="op-detail-moves">
            <span class="op-moves-label">走法：</span>
            <span class="op-moves-text">{{ detailData.moves.join(' ') }}</span>
          </div>
          <div v-if="detailData.description" class="op-detail-desc">{{ detailData.description }}</div>

          <div class="op-detail-stats" v-if="detailData.white_win_rate != null">
            <div class="op-stat-row">
              <span class="op-stat-label">白方胜率</span>
              <el-progress :percentage="detailData.white_win_rate" :stroke-width="10" :color="'#f56c6c'" />
              <span class="op-stat-value">{{ detailData.white_win_rate }}%</span>
            </div>
            <div class="op-stat-row">
              <span class="op-stat-label">和棋率</span>
              <el-progress :percentage="detailData.draw_rate" :stroke-width="10" :color="'#e6a23c'" />
              <span class="op-stat-value">{{ detailData.draw_rate }}%</span>
            </div>
            <div class="op-stat-row">
              <span class="op-stat-label">黑方胜率</span>
              <el-progress :percentage="detailData.black_win_rate" :stroke-width="10" :color="'#409eff'" />
              <span class="op-stat-value">{{ detailData.black_win_rate }}%</span>
            </div>
            <div v-if="detailData.popularity" class="op-stat-row">
              <span class="op-stat-label">对局数</span>
              <span class="op-stat-value">{{ detailData.popularity }}</span>
            </div>
          </div>

          <el-divider v-if="detailData.example_games && detailData.example_games.length" content-position="left">
            样例棋谱
          </el-divider>

          <div v-if="detailData.example_games && detailData.example_games.length" class="op-example-games">
            <div
              v-for="g in detailData.example_games"
              :key="g.id"
              class="op-example-item"
              @click="goToGame(g.id)"
            >
              <div class="op-example-players">
                <span class="op-example-white">
                  {{ g.white_player_name }}
                  <span v-if="g.white_elo" class="op-example-elo">({{ g.white_elo }})</span>
                </span>
                <span class="op-example-vs">vs</span>
                <span class="op-example-black">
                  {{ g.black_player_name }}
                  <span v-if="g.black_elo" class="op-example-elo">({{ g.black_elo }})</span>
                </span>
              </div>
              <div class="op-example-meta">
                <el-tag :type="resultTagType(g.result)" size="small">{{ g.result }}</el-tag>
                <span v-if="g.date" class="op-example-date">{{ g.date }}</span>
              </div>
            </div>
          </div>

          <div v-if="detailData.example_games && !detailData.example_games.length" class="op-no-examples">
            暂无该开局的样例棋谱
          </div>
        </template>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Grid, List } from '@element-plus/icons-vue'
import { getOpenings, getOpening } from '@/api/openings'

const router = useRouter()
const loading = ref(false)
const openings = ref([])
const viewMode = ref('card')

const CATEGORY_MAP = {
  'A': 'A - 侧翼开局',
  'B': 'B - 半开放开局',
  'C': 'C - 开放开局',
  'D': 'D - 封闭/半封闭',
  'E': 'E - 印度防御',
}

function getCategoryName(cat) {
  return CATEGORY_MAP[cat] || cat
}

const openingTableRef = ref(null)

const filters = reactive({
  search: '',
  category: '',
  sort: 'eco_code',
  order: 'asc',
})

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
})

const detailVisible = ref(false)
const detailLoading = ref(false)
const detailData = ref(null)

async function fetchOpenings() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.pageSize,
      sort: filters.sort,
      order: filters.order,
    }
    if (filters.search) params.search = filters.search
    if (filters.category) params.category = filters.category

    const res = await getOpenings(params)
    const data = res.data || res
    openings.value = data.items || []
    pagination.total = data.total || 0
  } catch (e) {
    ElMessage.error('加载开局库失败：' + e.message)
  } finally {
    loading.value = false
  }
}

async function showDetail(opening) {
  detailVisible.value = true
  detailLoading.value = true
  detailData.value = null
  try {
    const eco = opening.eco_code
    const res = await getOpening(eco)
    detailData.value = res.data || res
  } catch (e) {
    detailData.value = opening
  } finally {
    detailLoading.value = false
  }
}

function goToGame(gameId) {
  detailVisible.value = false
  router.push(`/games/${gameId}`)
}

function resultTagType(result) {
  if (result === '1-0') return 'success'
  if (result === '0-1') return 'danger'
  if (result === '1/2-1/2') return 'warning'
  return 'info'
}

function onFilterChange() {
  pagination.page = 1
  openingTableRef.value?.clearSort()
  fetchOpenings()
}

function clearFilters() {
  filters.search = ''
  filters.category = ''
  filters.sort = 'eco_code'
  filters.order = 'asc'
  onFilterChange()
}

function onPageChange() {
  fetchOpenings()
}

function onPageSizeChange() {
  pagination.page = 1
  fetchOpenings()
}

onMounted(() => {
  fetchOpenings()
})
</script>

<style scoped>
.opening-page {
  max-width: 1200px;
  margin: 0 auto;
}

.op-header {
  margin-bottom: 20px;
}

.op-header h1 {
  font-size: 24px;
  color: var(--text-color);
  margin: 0;
}

.op-filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
  padding: 16px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.op-card {
  margin-bottom: 16px;
  transition: transform 0.2s;
  cursor: pointer;
}

.op-card:hover {
  transform: translateY(-2px);
}

.op-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.op-card-category {
  font-size: 12px;
  color: var(--text-color-secondary);
  background: #f4f4f5;
  padding: 1px 6px;
  border-radius: 3px;
}

.op-card-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 4px;
}

.op-card-variation {
  font-size: 13px;
  color: var(--text-color-regular);
  margin-bottom: 6px;
}

.op-card-moves {
  font-size: 12px;
  margin-bottom: 6px;
}

.op-moves-label {
  color: var(--text-color-secondary);
}

.op-moves-text {
  color: #409eff;
  font-family: monospace;
}

.op-card-stats {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.op-stat {
  display: flex;
  align-items: center;
  gap: 6px;
}

.op-stat-label {
  font-size: 11px;
  color: var(--text-color-secondary);
  min-width: 30px;
}

.op-stat .el-progress {
  flex: 1;
}

.op-card-popularity {
  margin-top: 6px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.op-card-desc {
  font-size: 12px;
  color: var(--text-color-secondary);
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.op-table {
  cursor: pointer;
}

.op-wr-white { color: #f56c6c; font-weight: 600; }
.op-wr-draw { color: #e6a23c; font-weight: 600; }
.op-wr-black { color: #409eff; font-weight: 600; }

.op-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px 0;
}

.op-detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.op-detail-category {
  font-size: 13px;
  color: var(--text-color-secondary);
  background: #f4f4f5;
  padding: 2px 8px;
  border-radius: 3px;
}

.op-detail-variation {
  font-size: 14px;
  color: var(--text-color-regular);
  margin-bottom: 8px;
}

.op-detail-moves {
  font-size: 13px;
  margin-bottom: 8px;
}

.op-detail-desc {
  font-size: 13px;
  color: var(--text-color-regular);
  line-height: 1.6;
}

.op-detail-stats {
  margin-top: 12px;
  padding: 12px;
  background: #f9f9fb;
  border-radius: 8px;
}

.op-stat-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.op-stat-row:last-child {
  margin-bottom: 0;
}

.op-stat-row .op-stat-label {
  min-width: 70px;
  font-size: 13px;
}

.op-stat-row .el-progress {
  flex: 1;
}

.op-stat-value {
  min-width: 50px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
}

.op-example-games {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.op-example-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f9f9fb;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.op-example-item:hover {
  background: var(--hover-bg);
}

.op-example-players {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.op-example-white {
  font-weight: 600;
  color: var(--text-color);
}

.op-example-black {
  font-weight: 600;
  color: var(--text-color);
}

.op-example-vs {
  color: var(--text-color-placeholder);
  font-size: 12px;
}

.op-example-elo {
  color: var(--text-color-secondary);
  font-weight: 400;
  font-size: 12px;
}

.op-example-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.op-example-date {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.op-no-examples {
  text-align: center;
  color: var(--text-color-secondary);
  font-size: 13px;
  padding: 20px 0;
}
</style>
