<template>
  <div class="home-page">
    <div class="hp-hero">
      <div class="hp-hero-content">
        <h1 class="hp-hero-title">♚ ChessDB</h1>
        <p class="hp-hero-desc">国际象棋数据管理系统 — 探索经典对局，研究开局变化</p>
        <div class="hp-hero-actions">
          <el-button type="primary" size="large" @click="router.push('/games')">浏览棋谱库</el-button>
          <el-button size="large" @click="router.push('/players')">棋手排行</el-button>
          <el-button size="large" @click="router.push('/openings')">开局库</el-button>
        </div>
      </div>
    </div>

    <div class="hp-stats">
      <el-row :gutter="16">
        <el-col :xs="12" :sm="6">
          <div class="hp-stat-card">
            <div class="hp-stat-value">{{ stats.games }}</div>
            <div class="hp-stat-label">对局数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="hp-stat-card">
            <div class="hp-stat-value">{{ stats.players }}</div>
            <div class="hp-stat-label">棋手数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="hp-stat-card">
            <div class="hp-stat-value">{{ stats.openings }}</div>
            <div class="hp-stat-label">开局数</div>
          </div>
        </el-col>
        <el-col :xs="12" :sm="6">
          <div class="hp-stat-card">
            <div class="hp-stat-value">{{ stats.tournaments }}</div>
            <div class="hp-stat-label">赛事数</div>
          </div>
        </el-col>
      </el-row>
    </div>

    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <el-card class="hp-section">
          <template #header>
            <div class="hp-section-header">
              <h2>最新对局</h2>
              <el-button text type="primary" @click="router.push('/games')">查看全部 →</el-button>
            </div>
          </template>
          <div v-loading="loadingGames">
            <div v-if="!loadingGames && recentGames.length === 0" class="hp-empty">
              <el-empty description="暂无对局数据" :image-size="80" />
            </div>
            <div v-else class="hp-game-list">
              <div
                v-for="game in recentGames"
                :key="game.id"
                class="hp-game-item"
                @click="router.push(`/games/${game.id}`)"
              >
                <div class="hp-game-players">
                  <span class="hp-game-player hp-game-white">
                    {{ game.white_player_name || '未知' }}
                    <span v-if="game.white_elo" class="hp-elo">({{ game.white_elo }})</span>
                  </span>
                  <span class="hp-game-vs">vs</span>
                  <span class="hp-game-player hp-game-black">
                    {{ game.black_player_name || '未知' }}
                    <span v-if="game.black_elo" class="hp-elo">({{ game.black_elo }})</span>
                  </span>
                </div>
                <div class="hp-game-meta">
                  <el-tag :type="resultTagType(game.result)" size="small">{{ game.result || '*' }}</el-tag>
                  <span v-if="game.eco_code" class="hp-game-eco">{{ game.eco_code }}</span>
                  <span v-if="game.opening_name" class="hp-game-opening">{{ game.opening_name }}</span>
                  <span class="hp-game-date">{{ game.date || '' }}</span>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="10">
        <el-card class="hp-section">
          <template #header>
            <div class="hp-section-header">
              <h2>棋手排行</h2>
              <el-button text type="primary" @click="router.push('/players')">查看全部 →</el-button>
            </div>
          </template>
          <div v-loading="loadingPlayers">
            <div v-if="!loadingPlayers && topPlayers.length === 0" class="hp-empty">
              <el-empty description="暂无棋手数据" :image-size="80" />
            </div>
            <div v-else class="hp-player-list">
              <div
                v-for="(player, index) in topPlayers"
                :key="player.id"
                class="hp-player-item"
                @click="router.push(`/players/${player.id}`)"
              >
                <div class="hp-player-rank">{{ index + 1 }}</div>
                <div class="hp-player-info">
                  <div class="hp-player-name">
                    <span v-if="player.title" class="hp-player-title">{{ player.title }}</span>
                    {{ player.name }}
                  </div>
                  <div class="hp-player-detail">
                    <span v-if="player.country">{{ player.country }}</span>
                    <span class="hp-player-elo">ELO: {{ player.elo_rating }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="hp-section" style="margin-top: 16px">
          <template #header>
            <div class="hp-section-header">
              <h2>热门开局</h2>
              <el-button text type="primary" @click="router.push('/openings')">查看全部 →</el-button>
            </div>
          </template>
          <div v-loading="loadingOpenings">
            <div v-if="!loadingOpenings && topOpenings.length === 0" class="hp-empty">
              <el-empty description="暂无开局数据" :image-size="80" />
            </div>
            <div v-else class="hp-opening-list">
              <div
                v-for="opening in topOpenings"
                :key="opening.id"
                class="hp-opening-item"
              >
                <el-tag size="small" type="info">{{ opening.eco_code }}</el-tag>
                <span class="hp-opening-name">{{ opening.name }}</span>
                <span v-if="opening.variation" class="hp-opening-variation">{{ opening.variation }}</span>
              </div>
            </div>
          </div>
        </el-card>

        <el-card class="hp-practice-card" style="margin-top: 16px" @click="router.push('/practice')">
          <div class="hp-practice-content">
            <div class="hp-practice-icon">♞</div>
            <div class="hp-practice-info">
              <div class="hp-practice-title">AI对弈练习</div>
              <div class="hp-practice-desc">与AI对弈，提升棋力</div>
            </div>
            <el-icon class="hp-practice-arrow"><ArrowRight /></el-icon>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight } from '@element-plus/icons-vue'
import { getGames } from '@/api/games'
import { getPlayers } from '@/api/players'
import { getOpenings } from '@/api/openings'

const router = useRouter()

const loadingGames = ref(false)
const loadingPlayers = ref(false)
const loadingOpenings = ref(false)

const recentGames = ref([])
const topPlayers = ref([])
const topOpenings = ref([])

const stats = reactive({
  games: 0,
  players: 0,
  openings: 0,
  tournaments: 0,
})

function resultTagType(result) {
  if (result === '1-0') return 'success'
  if (result === '0-1') return 'danger'
  if (result === '1/2-1/2') return 'warning'
  return 'info'
}

async function fetchGames() {
  loadingGames.value = true
  try {
    const res = await getGames({ page: 1, per_page: 6 })
    const data = res.data || res
    recentGames.value = data.items || []
    stats.games = data.total || 0
  } catch (e) {
    console.error('Failed to fetch games:', e)
  } finally {
    loadingGames.value = false
  }
}

async function fetchPlayers() {
  loadingPlayers.value = true
  try {
    const res = await getPlayers({ page: 1, per_page: 10, sort: 'elo_rating', order: 'desc' })
    const data = res.data || res
    topPlayers.value = data.items || []
    stats.players = data.total || 0
  } catch (e) {
    console.error('Failed to fetch players:', e)
  } finally {
    loadingPlayers.value = false
  }
}

async function fetchOpenings() {
  loadingOpenings.value = true
  try {
    const res = await getOpenings({ page: 1, per_page: 8 })
    const data = res.data || res
    topOpenings.value = data.items || []
    stats.openings = data.total || 0
  } catch (e) {
    console.error('Failed to fetch openings:', e)
  } finally {
    loadingOpenings.value = false
  }
}

onMounted(() => {
  fetchGames()
  fetchPlayers()
  fetchOpenings()
})
</script>

<style scoped>
.home-page {
  max-width: 1200px;
  margin: 0 auto;
}

.hp-hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  border-radius: 12px;
  padding: 48px 32px;
  margin-bottom: 24px;
  text-align: center;
}

.hp-hero-title {
  font-size: 42px;
  color: #fff;
  margin: 0 0 12px;
  letter-spacing: 2px;
}

.hp-hero-desc {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.75);
  margin: 0 0 24px;
}

.hp-hero-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  flex-wrap: wrap;
}

.hp-stats {
  margin-bottom: 24px;
}

.hp-stat-card {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s;
}

.hp-stat-card:hover {
  transform: translateY(-2px);
}

.hp-stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #409eff;
}

.hp-stat-label {
  font-size: 14px;
  color: var(--text-color-secondary);
  margin-top: 4px;
}

.hp-section {
  margin-bottom: 0;
}

.hp-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.hp-section-header h2 {
  font-size: 16px;
  margin: 0;
  color: var(--text-color);
}

.hp-empty {
  padding: 20px 0;
}

.hp-game-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hp-game-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.hp-game-item:hover {
  background: var(--bg-color-secondary);
}

.hp-game-players {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.hp-game-player {
  color: var(--text-color);
}

.hp-elo {
  font-size: 12px;
  color: var(--text-color-secondary);
  font-weight: 400;
}

.hp-game-vs {
  color: var(--text-color-placeholder);
  font-size: 12px;
}

.hp-game-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.hp-game-eco {
  background: #f4f4f5;
  padding: 1px 6px;
  border-radius: 3px;
}

.hp-game-opening {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hp-game-date {
  margin-left: auto;
}

.hp-player-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.hp-player-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.hp-player-item:hover {
  background: var(--bg-color-secondary);
}

.hp-player-rank {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--hover-bg);
  color: #409eff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}

.hp-player-item:nth-child(1) .hp-player-rank {
  background: #fef0d5;
  color: #e6a23c;
}

.hp-player-item:nth-child(2) .hp-player-rank {
  background: #f0f0f0;
  color: var(--text-color-secondary);
}

.hp-player-item:nth-child(3) .hp-player-rank {
  background: #fde8e8;
  color: #cd7f32;
}

.hp-player-info {
  flex: 1;
  min-width: 0;
}

.hp-player-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.hp-player-title {
  background: #e6a23c;
  color: #fff;
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 2px;
  margin-right: 4px;
  font-weight: 700;
}

.hp-player-detail {
  font-size: 12px;
  color: var(--text-color-secondary);
  display: flex;
  gap: 8px;
}

.hp-player-elo {
  color: #409eff;
  font-weight: 600;
}

.hp-opening-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.hp-opening-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  padding: 4px 0;
}

.hp-opening-name {
  color: var(--text-color);
  font-weight: 500;
}

.hp-opening-variation {
  color: var(--text-color-secondary);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hp-practice-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.hp-practice-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.15);
}

.hp-practice-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.hp-practice-icon {
  font-size: 40px;
  color: #409eff;
  line-height: 1;
  flex-shrink: 0;
}

.hp-practice-info {
  flex: 1;
}

.hp-practice-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.hp-practice-desc {
  font-size: 13px;
  color: var(--text-color-secondary);
  margin-top: 2px;
}

.hp-practice-arrow {
  font-size: 18px;
  color: var(--text-color-placeholder);
  flex-shrink: 0;
}
</style>
