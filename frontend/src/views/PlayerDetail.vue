<template>
  <div class="player-detail-page">
    <div v-loading="loading" class="pd-content">
      <div v-if="!loading && !player" class="pd-empty">
        <el-empty description="棋手不存在" />
      </div>

      <template v-if="player">
        <div class="pd-header">
          <div class="pd-info">
            <div class="pd-name">
              <span v-if="player.title" class="pd-title-badge">{{ player.title }}</span>
              <h1>{{ player.name }}</h1>
            </div>
            <div class="pd-meta">
              <span v-if="player.country">{{ player.country }}</span>
              <span class="pd-elo">等级分: <strong>{{ player.elo_rating }}</strong></span>
              <span v-if="player.birth_date">出生: {{ player.birth_date }}</span>
            </div>
          </div>
          <el-button @click="goBack">返回列表</el-button>
        </div>

        <el-row :gutter="20">
          <el-col :xs="24" :md="8">
            <el-card class="pd-stats-card">
              <template #header><h3>战绩统计</h3></template>
              <div v-if="stats" class="pd-stats">
                <div class="pd-stat-row">
                  <span>总对局</span>
                  <strong>{{ stats.total_games }}</strong>
                </div>
                <div class="pd-stat-row">
                  <span>胜</span>
                  <strong class="pd-stat-win">{{ stats.wins }}</strong>
                </div>
                <div class="pd-stat-row">
                  <span>负</span>
                  <strong class="pd-stat-loss">{{ stats.losses }}</strong>
                </div>
                <div class="pd-stat-row">
                  <span>和</span>
                  <strong class="pd-stat-draw">{{ stats.draws }}</strong>
                </div>
                <div class="pd-stat-row">
                  <span>胜率</span>
                  <strong>{{ stats.win_rate }}%</strong>
                </div>
                <el-divider />
                <div class="pd-stat-row">
                  <span>执白 胜/负/和</span>
                  <span>{{ stats.as_white?.wins || 0 }}/{{ stats.as_white?.losses || 0 }}/{{ stats.as_white?.draws || 0 }}</span>
                </div>
                <div class="pd-stat-row">
                  <span>执黑 胜/负/和</span>
                  <span>{{ stats.as_black?.wins || 0 }}/{{ stats.as_black?.losses || 0 }}/{{ stats.as_black?.draws || 0 }}</span>
                </div>
              </div>
              <div v-else class="pd-stats-empty">暂无战绩数据</div>
            </el-card>
          </el-col>

          <el-col :xs="24" :md="16">
            <el-card class="pd-games-card">
              <template #header>
                <div class="pd-games-header">
                  <h3>对局记录</h3>
                  <el-tag size="small">{{ gamesTotal }} 局</el-tag>
                </div>
              </template>
              <div v-if="games.length === 0" class="pd-games-empty">
                暂无对局记录
              </div>
              <div v-else class="pd-game-list">
                <div
                  v-for="game in games"
                  :key="game.id"
                  class="pd-game-item"
                  @click="router.push(`/games/${game.id}`)"
                >
                  <div class="pd-game-players">
                    <span :class="{ 'pd-game-highlight': game.white_player_name === player.name }">
                      {{ game.white_player_name || '未知' }}
                    </span>
                    <span class="pd-game-vs">vs</span>
                    <span :class="{ 'pd-game-highlight': game.black_player_name === player.name }">
                      {{ game.black_player_name || '未知' }}
                    </span>
                  </div>
                  <div class="pd-game-meta">
                    <el-tag :type="resultTagType(game.result)" size="small">{{ game.result || '*' }}</el-tag>
                    <span v-if="game.eco_code" class="pd-game-eco">{{ game.eco_code }}</span>
                    <span v-if="game.date" class="pd-game-date">{{ game.date }}</span>
                  </div>
                </div>
              </div>
              <div v-if="games.length < gamesTotal" class="pd-games-more">
                <el-button text type="primary" @click="loadMoreGames">加载更多</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getPlayer, getPlayerGames } from '@/api/players'
import request from '@/api/request'

const router = useRouter()
const route = useRoute()

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/players')
  }
}

const loading = ref(false)
const player = ref(null)
const stats = ref(null)
const games = ref([])
const gamesTotal = ref(0)
const gamesPage = ref(1)

function resultTagType(result) {
  if (result === '1-0') return 'success'
  if (result === '0-1') return 'danger'
  if (result === '1/2-1/2') return 'warning'
  return 'info'
}

async function fetchPlayer() {
  loading.value = true
  try {
    const id = route.params.id
    const res = await getPlayer(id)
    const data = res.data || res
    player.value = data

    try {
      const statsRes = await request.get(`/players/${id}/stats`)
      stats.value = statsRes.data || statsRes
    } catch {
      stats.value = null
    }

    await fetchGames()
  } catch (e) {
    ElMessage.error('加载棋手信息失败')
  } finally {
    loading.value = false
  }
}

async function fetchGames() {
  try {
    const id = route.params.id
    const res = await getPlayerGames(id, { page: gamesPage.value, per_page: 10 })
    const data = res.data || res
    if (gamesPage.value === 1) {
      games.value = data.items || []
    } else {
      games.value.push(...(data.items || []))
    }
    gamesTotal.value = data.total || 0
  } catch (e) {
    console.error('Failed to fetch player games:', e)
  }
}

function loadMoreGames() {
  gamesPage.value++
  fetchGames()
}

onMounted(() => {
  fetchPlayer()
})
</script>

<style scoped>
.player-detail-page {
  max-width: 1100px;
  margin: 0 auto;
}

.pd-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.pd-info {
  flex: 1;
}

.pd-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.pd-name h1 {
  font-size: 28px;
  margin: 0;
  color: var(--text-color);
}

.pd-title-badge {
  background: #e6a23c;
  color: #fff;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 3px;
  font-weight: 700;
}

.pd-meta {
  display: flex;
  gap: 16px;
  font-size: 14px;
  color: var(--text-color-secondary);
  margin-top: 8px;
}

.pd-elo {
  color: #409eff;
}

.pd-elo strong {
  font-size: 18px;
}

.pd-stats-card h3,
.pd-games-card h3 {
  font-size: 15px;
  margin: 0;
}

.pd-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pd-stat-row {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: var(--text-color-regular);
}

.pd-stat-row strong {
  color: var(--text-color);
}

.pd-stat-win {
  color: #67c23a;
}

.pd-stat-loss {
  color: #f56c6c;
}

.pd-stat-draw {
  color: #e6a23c;
}

.pd-stats-empty {
  text-align: center;
  color: var(--text-color-placeholder);
  padding: 20px;
}

.pd-games-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.pd-game-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.pd-game-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.pd-game-item:hover {
  background: var(--bg-color-secondary);
}

.pd-game-players {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.pd-game-vs {
  color: var(--text-color-placeholder);
  font-size: 12px;
  margin: 0 6px;
}

.pd-game-highlight {
  color: #409eff;
  font-weight: 600;
}

.pd-game-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.pd-game-eco {
  background: #f4f4f5;
  padding: 1px 6px;
  border-radius: 3px;
}

.pd-games-empty {
  text-align: center;
  color: var(--text-color-placeholder);
  padding: 40px 0;
}

.pd-games-more {
  text-align: center;
  padding: 12px 0;
}
</style>
