<template>
  <div class="analysis-queue-page">
    <div class="aq-header">
      <h2>分析队列</h2>
      <p class="aq-desc">查看和管理你的对局分析任务，分析在后台运行，离开页面不会中断</p>
    </div>

    <el-card class="aq-engine-card">
      <div class="aq-engine-info">
        <div class="aq-engine-item">
          <span class="aq-engine-label">引擎</span>
          <span class="aq-engine-value">{{ engineInfo.name || '未知' }}</span>
          <el-tag v-if="engineInfo.is_mock" type="warning" size="small">模拟模式</el-tag>
          <el-tag v-else type="success" size="small">Stockfish</el-tag>
        </div>
        <div class="aq-engine-item">
          <span class="aq-engine-label">分析深度</span>
          <span class="aq-engine-value">{{ engineInfo.depth || 20 }}</span>
        </div>
        <div class="aq-engine-item">
          <span class="aq-engine-label">线程数</span>
          <span class="aq-engine-value">{{ engineInfo.threads || 1 }}</span>
        </div>
        <div class="aq-engine-item">
          <span class="aq-engine-label">哈希表</span>
          <span class="aq-engine-value">{{ engineInfo.hash_size || 256 }}MB</span>
        </div>
      </div>
    </el-card>

    <el-card class="aq-tasks-card">
      <template #header>
        <div class="aq-tasks-header">
          <span>分析任务</span>
          <div class="aq-tasks-actions">
            <el-tag v-if="runningCount > 0" type="warning" size="small">{{ runningCount }} 个进行中</el-tag>
            <el-button size="small" @click="refreshTasks">
              刷新
            </el-button>
          </div>
        </div>
      </template>

      <div v-if="tasks.length === 0" class="aq-empty">
        <el-empty description="暂无分析任务">
          <el-button type="primary" @click="$router.push('/games')">浏览棋谱</el-button>
        </el-empty>
      </div>

      <div v-else class="aq-task-list">
        <div v-for="task in tasks" :key="task.task_id" class="aq-task-item">
          <div class="aq-task-info">
            <div class="aq-task-id">
              <el-tag :type="taskStatusType(task.status)" size="small">
                {{ taskStatusLabel(task.status) }}
              </el-tag>
              <span class="aq-task-game">对局 #{{ task.game_id }}</span>
              <router-link :to="`/games/${task.game_id}`" class="aq-task-link">查看</router-link>
            </div>
            <div v-if="task.status === 'running' || task.status === 'pending'" class="aq-task-progress">
              <el-progress :percentage="Math.round(task.progress * 100)" :stroke-width="8" />
            </div>
            <div v-if="task.status === 'completed' && task.result" class="aq-task-result">
              <span>分析完成：{{ task.result.total_moves }} 步，{{ task.result.key_moves_count }} 个关键手</span>
              <el-button size="small" type="primary" text @click="viewAnalysis(task.game_id)">查看分析</el-button>
            </div>
            <div v-if="task.status === 'failed' || task.status === 'cancelled'" class="aq-task-error">
              <span class="aq-error-text">{{ task.error || (task.status === 'cancelled' ? '已取消' : '分析失败') }}</span>
            </div>
          </div>
          <div class="aq-task-actions">
            <el-button
              v-if="task.status === 'running' || task.status === 'pending'"
              size="small"
              type="danger"
              text
              @click="cancelTask(task.task_id)"
            >取消</el-button>
          </div>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getEngineInfo, listAnalysisTasks, cancelAnalysisTask } from '@/api/analysis'

const router = useRouter()

const engineInfo = ref({})
const tasks = ref([])
let pollTimer = null

const runningCount = computed(() => tasks.value.filter(t => t.status === 'running' || t.status === 'pending').length)

function taskStatusType(status) {
  const map = { pending: 'info', running: 'warning', completed: 'success', failed: 'danger', cancelled: 'info' }
  return map[status] || 'info'
}

function taskStatusLabel(status) {
  const map = { pending: '等待中', running: '分析中', completed: '已完成', failed: '失败', cancelled: '已取消' }
  return map[status] || status
}

function viewAnalysis(gameId) {
  router.push(`/games/${gameId}`)
}

async function cancelTask(taskId) {
  try {
    await ElMessageBox.confirm('确定要取消此分析任务吗？', '取消确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await cancelAnalysisTask(taskId)
    ElMessage.success('任务已取消')
    refreshTasks()
  } catch {
    // 用户取消操作
  }
}

async function loadEngineInfo() {
  try {
    const res = await getEngineInfo()
    const data = res.data || res
    engineInfo.value = data.engine || data || {}
  } catch {
    engineInfo.value = { name: '不可用', is_mock: true }
  }
}

async function loadTasks() {
  try {
    const res = await listAnalysisTasks()
    const data = res.data || res
    tasks.value = data.tasks || []
  } catch {
    tasks.value = []
  }
}

function refreshTasks() {
  loadTasks()
  loadEngineInfo()
}

onMounted(() => {
  loadEngineInfo()
  loadTasks()
  // 每5秒轮询任务状态
  pollTimer = setInterval(() => {
    loadTasks()
  }, 5000)
})

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
})
</script>

<style scoped>
.analysis-queue-page {
  max-width: 800px;
  margin: 0 auto;
}

.aq-header {
  margin-bottom: 20px;
}

.aq-header h2 {
  margin: 0 0 4px;
  color: var(--text-color);
}

.aq-desc {
  margin: 0;
  font-size: 14px;
  color: var(--text-color-secondary);
}

.aq-engine-card {
  margin-bottom: 16px;
}

.aq-engine-info {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
}

.aq-engine-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.aq-engine-label {
  font-size: 13px;
  color: var(--text-color-secondary);
}

.aq-engine-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.aq-tasks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.aq-tasks-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.aq-empty {
  padding: 40px 0;
}

.aq-task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.aq-task-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px;
  background: var(--bg-color-secondary);
  border-radius: 6px;
}

.aq-task-info {
  flex: 1;
}

.aq-task-id {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.aq-task-game {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
}

.aq-task-link {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
}

.aq-task-link:hover {
  text-decoration: underline;
}

.aq-task-progress {
  margin-top: 4px;
}

.aq-task-result {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #67c23a;
}

.aq-task-error {
  margin-top: 4px;
}

.aq-error-text {
  font-size: 13px;
  color: #f56c6c;
}
</style>
