<template>
  <div class="player-list-page">
    <div class="pl-header">
      <h1>棋手列表</h1>
    </div>

    <div class="pl-filters">
      <el-input
        v-model="filters.search"
        placeholder="搜索棋手姓名"
        clearable
        :prefix-icon="Search"
        style="width: 200px"
        @clear="onFilterChange"
        @keyup.enter="onFilterChange"
      />
      <el-select
        v-model="filters.title"
        placeholder="头衔"
        clearable
        style="width: 120px"
        @change="onFilterChange"
      >
        <el-option
          v-for="t in titleOptions"
          :key="t"
          :label="t"
          :value="t"
        />
      </el-select>
      <el-select
        v-model="filters.country"
        placeholder="国家/地区"
        clearable
        filterable
        style="width: 150px"
        @change="onFilterChange"
      >
        <el-option
          v-for="c in countryOptions"
          :key="c"
          :label="c"
          :value="c"
        />
      </el-select>
      <div class="pl-elo-range">
        <el-input-number
          v-model="filters.minElo"
          placeholder="最低等级分"
          :min="0"
          :max="4000"
          :step="100"
          controls-position="right"
          style="width: 120px"
          @change="onFilterChange"
        />
        <span class="pl-elo-sep">-</span>
        <el-input-number
          v-model="filters.maxElo"
          placeholder="最高等级分"
          :min="0"
          :max="4000"
          :step="100"
          controls-position="right"
          style="width: 120px"
          @change="onFilterChange"
        />
      </div>
      <el-select
        v-model="filters.sort"
        placeholder="排序"
        style="width: 140px"
        @change="onFilterChange"
      >
        <el-option label="等级分 ↓" value="elo_rating" />
        <el-option label="等级分 ↑" value="elo_rating_asc" />
        <el-option label="姓名 A-Z" value="name" />
        <el-option label="最近添加" value="created_at" />
      </el-select>
      <el-button @click="clearFilters">清除筛选</el-button>
    </div>

    <div v-loading="loading" class="pl-content">
      <div v-if="!loading && players.length === 0" class="pl-empty">
        <el-empty description="暂无棋手数据" />
      </div>

      <el-table
        v-else
        :data="players"
        stripe
        class="pl-table"
        @row-click="goDetail"
      >
        <el-table-column label="排名" width="70" align="center">
          <template #default="{ $index }">
            <span class="pl-rank">{{ (pagination.page - 1) * pagination.pageSize + $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="棋手" min-width="200">
          <template #default="{ row }">
            <div class="pl-player-cell">
              <span v-if="row.title" class="pl-title-badge">{{ row.title }}</span>
              <span class="pl-player-name">{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="国家" prop="country" width="120" />
        <el-table-column label="等级分" width="100" align="center">
          <template #default="{ row }">
            <span class="pl-elo">{{ row.elo_rating }}</span>
          </template>
        </el-table-column>
        <el-table-column label="出生日期" prop="birth_date" width="120" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button type="primary" text size="small" @click.stop="goDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-if="players.length" class="pl-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[10, 20, 50]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="onPageSizeChange"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { getPlayers, getPlayerFilters } from '@/api/players'

const router = useRouter()

const loading = ref(false)
const players = ref([])
const titleOptions = ref([])
const countryOptions = ref([])

const filters = reactive({
  search: '',
  title: '',
  country: '',
  minElo: undefined,
  maxElo: undefined,
  sort: 'elo_rating',
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0,
})

async function fetchFilterOptions() {
  try {
    const res = await getPlayerFilters()
    const data = res.data || res
    titleOptions.value = data.titles || []
    countryOptions.value = data.countries || []
  } catch { /* ignore */ }
}

async function fetchPlayers() {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      per_page: pagination.pageSize,
    }
    if (filters.search) params.search = filters.search
    if (filters.title) params.title = filters.title
    if (filters.country) params.country = filters.country
    if (filters.minElo) params.min_elo = filters.minElo
    if (filters.maxElo) params.max_elo = filters.maxElo

    if (filters.sort === 'elo_rating') {
      params.sort = 'elo_rating'
      params.order = 'desc'
    } else if (filters.sort === 'elo_rating_asc') {
      params.sort = 'elo_rating'
      params.order = 'asc'
    } else if (filters.sort === 'name') {
      params.sort = 'name'
      params.order = 'asc'
    } else if (filters.sort === 'created_at') {
      params.sort = 'created_at'
      params.order = 'desc'
    }

    const res = await getPlayers(params)
    const data = res.data || res
    players.value = data.items || []
    pagination.total = data.total || 0
  } catch (e) {
    ElMessage.error('加载棋手列表失败：' + e.message)
  } finally {
    loading.value = false
  }
}

function onFilterChange() {
  pagination.page = 1
  fetchPlayers()
}

function clearFilters() {
  filters.search = ''
  filters.title = ''
  filters.country = ''
  filters.minElo = undefined
  filters.maxElo = undefined
  filters.sort = 'elo_rating'
  onFilterChange()
}

function onPageChange() {
  fetchPlayers()
}

function onPageSizeChange() {
  pagination.page = 1
  fetchPlayers()
}

function goDetail(row) {
  router.push(`/players/${row.id}`)
}

onMounted(() => {
  fetchFilterOptions()
  const saved = sessionStorage.getItem('playerListState')
  if (saved) {
    try {
      const state = JSON.parse(saved)
      if (state.page) pagination.page = state.page
      if (state.pageSize) pagination.pageSize = state.pageSize
      if (state.filters) Object.assign(filters, state.filters)
    } catch { /* ignore */ }
  }
  fetchPlayers()
})

onBeforeUnmount(() => {
  sessionStorage.setItem('playerListState', JSON.stringify({
    page: pagination.page,
    pageSize: pagination.pageSize,
    filters: { search: filters.search, title: filters.title, country: filters.country, sort: filters.sort },
  }))
})
</script>

<style scoped>
.player-list-page {
  max-width: 1000px;
  margin: 0 auto;
}

.pl-header {
  margin-bottom: 20px;
}

.pl-header h1 {
  font-size: 24px;
  color: var(--text-color);
  margin: 0;
}

.pl-filters {
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

.pl-elo-range {
  display: flex;
  align-items: center;
  gap: 4px;
}

.pl-elo-sep {
  color: var(--text-color-secondary);
}

.pl-content {
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.pl-table {
  width: 100%;
  cursor: pointer;
}

.pl-rank {
  font-weight: 600;
  color: var(--text-color-secondary);
}

.pl-player-cell {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pl-title-badge {
  background: #e6a23c;
  color: #fff;
  font-size: 10px;
  padding: 1px 5px;
  border-radius: 2px;
  font-weight: 700;
}

.pl-player-name {
  font-weight: 500;
  color: var(--text-color);
}

.pl-elo {
  font-weight: 700;
  color: #409eff;
}

.pl-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px 0;
}
</style>
