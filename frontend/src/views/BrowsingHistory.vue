<template>
  <div class="browsing-page">
    <div class="br-header">
      <h1>最近浏览</h1>
      <div class="br-header-actions">
        <span class="br-total">共 {{ pagination.total }} 局</span>
        <el-button-group>
          <el-button :type="viewMode === 'card' ? 'primary' : ''" @click="viewMode = 'card'" size="small">
            <el-icon><Grid /></el-icon>
          </el-button>
          <el-button :type="viewMode === 'table' ? 'primary' : ''" @click="viewMode = 'table'" size="small">
            <el-icon><List /></el-icon>
          </el-button>
        </el-button-group>
        <el-button size="small" type="danger" @click="onClearAll" :disabled="games.length === 0">清空记录</el-button>
      </div>
    </div>

    <div v-if="!isLoggedIn" class="br-login-tip">
      <el-alert type="info" :closable="false" show-icon>
        <template #title>登录后浏览记录将同步至云端，可在不同设备间共享</template>
      </el-alert>
    </div>

    <div v-loading="loading" class="br-content">
      <div v-if="!loading && games.length === 0" class="br-empty">
        <el-empty description="暂无浏览记录">
          <el-button type="primary" @click="$router.push('/games')">浏览棋谱库</el-button>
        </el-empty>
      </div>

      <template v-else-if="viewMode === 'card'">
        <el-row :gutter="16">
          <el-col
            v-for="item in games"
            :key="item.id"
            :xs="24"
            :sm="12"
            :md="8"
            :lg="6"
          >
            <el-card class="br-card" shadow="hover" @click="goDetail(item.game_id)">
              <div class="br-card-info">
                <div class="br-card-players">
                  <span class="br-card-white">{{ item.white_player_name || '未知' }}</span>
                  <span class="br-card-vs">vs</span>
                  <span class="br-card-black">{{ item.black_player_name || '未知' }}</span>
                </div>
                <div class="br-card-meta">
                  <el-tag :type="resultTagType(item.result)" size="small">{{ item.result || '*' }}</el-tag>
                  <span v-if="item.eco_code" class="br-card-eco">{{ item.eco_code }}</span>
                </div>
                <div class="br-card-date">{{ formatDate(item.viewed_at) }}</div>
              </div>
              <div class="br-card-actions" @click.stop>
                <el-button type="danger" size="small" text @click="onRemove(item)">删除</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else>
        <el-table :data="games" stripe style="width: 100%" @row-click="(row) => goDetail(row.game_id)" class="br-table">
          <el-table-column label="白方" min-width="130">
            <template #default="{ row }">{{ row.white_player_name || '未知' }}</template>
          </el-table-column>
          <el-table-column label="黑方" min-width="130">
            <template #default="{ row }">{{ row.black_player_name || '未知' }}</template>
          </el-table-column>
          <el-table-column prop="result" label="结果" width="80">
            <template #default="{ row }">
              <el-tag :type="resultTagType(row.result)" size="small">{{ row.result || '*' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="eco_code" label="ECO" width="80">
            <template #default="{ row }">{{ row.eco_code || '-' }}</template>
          </el-table-column>
          <el-table-column label="浏览时间" width="120">
            <template #default="{ row }">{{ formatDate(row.viewed_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80" align="center">
            <template #default="{ row }">
              <el-button type="danger" text size="small" @click.stop="onRemove(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </div>

    <div v-if="games.length" class="br-pagination">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :page-sizes="[12, 24, 36]"
        :total="pagination.total"
        layout="total, sizes, prev, pager, next"
        @size-change="onPageSizeChange"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, List } from '@element-plus/icons-vue'
import { getBrowsingHistory, deleteBrowsing, clearBrowsing } from '@/api/browsing'

const router = useRouter()
const loading = ref(false)
const games = ref([])
const viewMode = ref('card')
const isLoggedIn = computed(() => !!localStorage.getItem('token'))

const pagination = reactive({
  page: 1,
  pageSize: 12,
  total: 0,
})

function resultTagType(result) {
  if (result === '1-0') return 'success'
  if (result === '0-1') return 'danger'
  if (result === '1/2-1/2') return 'warning'
  return 'info'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch {
    return dateStr
  }
}

async function fetchHistory() {
  loading.value = true
  try {
    if (isLoggedIn.value) {
      const res = await getBrowsingHistory({ page: pagination.page, per_page: pagination.pageSize })
      const data = res.data || res
      games.value = data.items || []
      pagination.total = data.total || 0
    } else {
      const stored = localStorage.getItem('recentGames')
      let all = []
      try { all = JSON.parse(stored || '[]') } catch { all = [] }
      const start = (pagination.page - 1) * pagination.pageSize
      const end = start + pagination.pageSize
      games.value = all.slice(start, end).map(g => ({
        id: g.id,
        game_id: g.id,
        white_player_name: g.white || '?',
        black_player_name: g.black || '?',
        result: '*',
        viewed_at: null,
      }))
      pagination.total = all.length
    }
  } catch (e) {
    ElMessage.error('加载浏览记录失败')
  } finally {
    loading.value = false
  }
}

async function onRemove(item) {
  try {
    if (isLoggedIn.value) {
      await deleteBrowsing(item.game_id)
    } else {
      const stored = localStorage.getItem('recentGames')
      let all = []
      try { all = JSON.parse(stored || '[]') } catch { all = [] }
      all = all.filter(g => g.id !== item.game_id)
      localStorage.setItem('recentGames', JSON.stringify(all))
    }
    ElMessage.success('已删除')
    fetchHistory()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function onClearAll() {
  try {
    await ElMessageBox.confirm('确定清空所有浏览记录？', '确认', { type: 'warning' })
    if (isLoggedIn.value) {
      await clearBrowsing()
    } else {
      localStorage.removeItem('recentGames')
    }
    ElMessage.success('已清空')
    games.value = []
    pagination.total = 0
  } catch { /* cancelled */ }
}

function goDetail(gameId) {
  router.push(`/games/${gameId}`)
}

function onPageChange() {
  fetchHistory()
}

function onPageSizeChange() {
  pagination.page = 1
  fetchHistory()
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.browsing-page {
  max-width: 1200px;
  margin: 0 auto;
}

.br-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.br-header h1 {
  font-size: 24px;
  color: var(--text-color);
  margin: 0;
}

.br-header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.br-total {
  font-size: 14px;
  color: var(--text-color-secondary);
}

.br-login-tip {
  margin-bottom: 16px;
}

.br-empty {
  padding: 60px 0;
}

.br-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.br-card:hover {
  transform: translateY(-2px);
}

.br-card-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.br-card-players {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.br-card-vs {
  margin: 0 4px;
  color: var(--text-color-secondary);
  font-size: 12px;
}

.br-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.br-card-eco {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.br-card-date {
  font-size: 12px;
  color: var(--text-color-placeholder);
}

.br-card-actions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color-lighter);
}

.br-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.br-table {
  cursor: pointer;
}
</style>
