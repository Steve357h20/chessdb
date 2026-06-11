<template>
  <div class="favorites-page">
    <div class="fav-header">
      <h1>我的收藏</h1>
      <span class="fav-total">共 {{ pagination.total }} 局</span>
      <div style="flex:1" />
      <el-button-group>
        <el-button :type="viewMode === 'card' ? 'primary' : ''" @click="viewMode = 'card'" size="small">
          <el-icon><Grid /></el-icon>
        </el-button>
        <el-button :type="viewMode === 'table' ? 'primary' : ''" @click="viewMode = 'table'" size="small">
          <el-icon><List /></el-icon>
        </el-button>
      </el-button-group>
    </div>

    <div v-loading="loading" class="fav-content">
      <div v-if="!loading && games.length === 0" class="fav-empty">
        <el-empty description="暂无收藏">
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
            <el-card class="fav-card" shadow="hover" @click="goDetail(item.game_id)">
              <div class="fav-card-info">
                <div class="fav-card-players">
                  <span class="fav-card-white">{{ item.white_player_name || '未知' }}</span>
                  <span class="fav-card-vs">vs</span>
                  <span class="fav-card-black">{{ item.black_player_name || '未知' }}</span>
                </div>
                <div class="fav-card-meta">
                  <el-tag :type="resultTagType(item.result)" size="small">{{ item.result || '*' }}</el-tag>
                  <span v-if="item.eco_code" class="fav-card-eco">{{ item.eco_code }}</span>
                </div>
                <div v-if="item.note" class="fav-card-note">{{ item.note }}</div>
                <div class="fav-card-date">收藏于 {{ formatDate(item.created_at) }}</div>
              </div>
              <div class="fav-card-actions" @click.stop>
                <el-button type="danger" size="small" text @click="onRemove(item)">取消收藏</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>

      <template v-else>
        <el-table :data="games" stripe style="width: 100%" @row-click="(row) => goDetail(row.game_id)" class="fav-table">
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
          <el-table-column prop="note" label="备注" min-width="150">
            <template #default="{ row }">{{ row.note || '-' }}</template>
          </el-table-column>
          <el-table-column label="收藏时间" width="120">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" align="center">
            <template #default="{ row }">
              <el-button type="danger" text size="small" @click.stop="onRemove(row)">取消</el-button>
            </template>
          </el-table-column>
        </el-table>
      </template>
    </div>

    <div v-if="games.length" class="fav-pagination">
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
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Grid, List } from '@element-plus/icons-vue'
import { getCollections, removeCollection } from '@/api/collections'

const router = useRouter()
const loading = ref(false)
const games = ref([])
const viewMode = ref('card')

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
    return d.toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

async function fetchCollections() {
  loading.value = true
  try {
    const res = await getCollections({ page: pagination.page, per_page: pagination.pageSize })
    const data = res.data || res
    games.value = data.items || []
    pagination.total = data.total || 0
  } catch (e) {
    ElMessage.error('加载收藏失败')
  } finally {
    loading.value = false
  }
}

async function onRemove(item) {
  try {
    await ElMessageBox.confirm('确定取消收藏？', '确认', { type: 'warning' })
    await removeCollection(item.id)
    ElMessage.success('已取消收藏')
    fetchCollections()
  } catch { /* cancelled */ }
}

function goDetail(gameId) {
  router.push(`/games/${gameId}`)
}

function onPageChange() {
  fetchCollections()
}

function onPageSizeChange() {
  pagination.page = 1
  fetchCollections()
}

onMounted(() => {
  fetchCollections()
})
</script>

<style scoped>
.favorites-page {
  max-width: 1200px;
  margin: 0 auto;
}

.fav-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.fav-header h1 {
  font-size: 24px;
  color: var(--text-color);
  margin: 0;
}

.fav-total {
  font-size: 14px;
  color: var(--text-color-secondary);
}

.fav-empty {
  padding: 60px 0;
}

.fav-card {
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s;
}

.fav-card:hover {
  transform: translateY(-2px);
}

.fav-card-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fav-card-players {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.fav-card-vs {
  margin: 0 4px;
  color: var(--text-color-secondary);
  font-size: 12px;
}

.fav-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.fav-card-eco {
  font-size: 12px;
  color: var(--text-color-secondary);
}

.fav-card-note {
  font-size: 12px;
  color: var(--text-color-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fav-card-date {
  font-size: 12px;
  color: var(--text-color-placeholder);
}

.fav-card-actions {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid var(--border-color-lighter);
}

.fav-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.fav-table {
  cursor: pointer;
}
</style>
