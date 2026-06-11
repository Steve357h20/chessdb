<template>
  <div class="help-page">
    <div class="hp-header">
      <h2>帮助中心</h2>
      <p class="hp-subtitle">了解如何使用 ChessDB 的各项功能</p>
    </div>

    <el-tabs v-model="activeTab" class="hp-tabs">
      <el-tab-pane label="快速入门" name="tutorial">
        <div class="hp-progress-bar">
          <div class="hp-progress-track">
            <div class="hp-progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <span class="hp-progress-text">已完成 {{ completedSteps }}/{{ totalSteps }} 步</span>
        </div>

        <div class="hp-tutorials">
          <div v-for="(tutorial, tIdx) in tutorials" :key="tIdx" class="hp-tutorial" :class="{ 'is-completed': isTutorialCompleted(tIdx) }">
            <div class="hp-tutorial-header" @click="toggleTutorial(tIdx)">
              <div class="hp-tutorial-num" :class="{ 'is-done': isTutorialCompleted(tIdx) }">
                <el-icon v-if="isTutorialCompleted(tIdx)"><Check /></el-icon>
                <span v-else>{{ tIdx + 1 }}</span>
              </div>
              <div class="hp-tutorial-title">{{ tutorial.title }}</div>
              <el-icon class="hp-tutorial-arrow" :class="{ 'is-open': tutorial.open }"><ArrowRight /></el-icon>
            </div>
            <div v-show="tutorial.open" class="hp-tutorial-body">
              <div v-for="(step, sIdx) in tutorial.steps" :key="sIdx" class="hp-step" :class="{ 'is-done': isStepCompleted(tIdx, sIdx) }">
                <div class="hp-step-header">
                  <el-checkbox :model-value="isStepCompleted(tIdx, sIdx)" @change="toggleStepComplete(tIdx, sIdx)" size="small" />
                  <span class="hp-step-num">步骤 {{ sIdx + 1 }}</span>
                  <span class="hp-step-title">{{ step.title }}</span>
                </div>
                <p class="hp-step-desc">{{ step.desc }}</p>
                <div v-if="step.link" class="hp-step-action">
                  <router-link :to="step.link" class="hp-step-link" @click="markStepComplete(tIdx, sIdx)">
                    <el-button type="primary" size="small">前往体验 →</el-button>
                  </router-link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="常见问题" name="faq">
        <div class="hp-faqs">
          <el-collapse v-model="openFaqs">
            <el-collapse-item v-for="(faq, fIdx) in faqs" :key="fIdx" :name="fIdx" :title="faq.q">
              <div class="hp-faq-answer" v-html="faq.a"></div>
            </el-collapse-item>
          </el-collapse>
        </div>
      </el-tab-pane>

      <el-tab-pane label="功能说明" name="features">
        <div class="hp-features">
          <div v-for="feature in features" :key="feature.name" class="hp-feature">
            <div class="hp-feature-icon">{{ feature.icon }}</div>
            <div class="hp-feature-info">
              <div class="hp-feature-name">{{ feature.name }}</div>
              <div class="hp-feature-desc">{{ feature.desc }}</div>
              <router-link v-if="feature.link" :to="feature.link" class="hp-feature-link">了解更多 →</router-link>
            </div>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ArrowRight, Check } from '@element-plus/icons-vue'

const activeTab = ref('tutorial')
const openFaqs = ref([0])
const completedSet = ref(new Set())

onMounted(() => {
  try {
    const saved = localStorage.getItem('chessdb_tutorial_progress')
    if (saved) {
      completedSet.value = new Set(JSON.parse(saved))
    }
  } catch {}
})

function stepKey(tIdx, sIdx) {
  return `${tIdx}-${sIdx}`
}

function isStepCompleted(tIdx, sIdx) {
  return completedSet.value.has(stepKey(tIdx, sIdx))
}

function isTutorialCompleted(tIdx) {
  return tutorials.value[tIdx].steps.every((_, sIdx) => isStepCompleted(tIdx, sIdx))
}

function toggleStepComplete(tIdx, sIdx) {
  const key = stepKey(tIdx, sIdx)
  if (completedSet.value.has(key)) {
    completedSet.value.delete(key)
  } else {
    completedSet.value.add(key)
  }
  _saveProgress()
}

function markStepComplete(tIdx, sIdx) {
  completedSet.value.add(stepKey(tIdx, sIdx))
  _saveProgress()
}

function _saveProgress() {
  try {
    localStorage.setItem('chessdb_tutorial_progress', JSON.stringify([...completedSet.value]))
  } catch {}
}

const totalSteps = computed(() => tutorials.value.reduce((sum, t) => sum + t.steps.length, 0))
const completedSteps = computed(() => completedSet.value.size)
const progressPercent = computed(() => totalSteps.value > 0 ? Math.round(completedSteps.value / totalSteps.value * 100) : 0)

const tutorials = ref([
  {
    title: '浏览和搜索棋谱',
    open: false,
    steps: [
      { title: '进入棋谱库', desc: '点击顶部导航栏的"棋谱库"进入棋谱列表页面，这里汇集了所有已录入的对局记录。', link: '/games' },
      { title: '搜索棋谱', desc: '在棋谱库页面使用搜索框，输入棋手名称或开局名称来筛选对局。也可以按ECO编码、年份等条件筛选。' },
      { title: '查看对局详情', desc: '点击任意对局卡片进入详情页，可以逐步回放对局、查看胜率走势图和AI分析结果。', link: '/games' },
    ],
  },
  {
    title: '上传棋谱',
    open: false,
    steps: [
      { title: '进入上传页面', desc: '点击顶部导航栏的"上传"按钮进入上传页面。需要登录后才能上传。', link: '/upload' },
      { title: '选择PGN文件', desc: '点击上传区域选择一个或多个PGN格式的棋谱文件，系统会自动解析并录入。' },
      { title: '确认上传', desc: '上传后系统会显示解析结果，确认无误后提交即可。棋谱将自动关联棋手和开局信息。' },
    ],
  },
  {
    title: 'AI对弈练习',
    open: false,
    steps: [
      { title: '选择练习模式', desc: '进入AI对弈练习页面，选择"残局练习"、"从棋谱开始"或"自定义FEN"三种模式之一。', link: '/practice' },
      { title: '残局练习', desc: '从残局库中选择一个预设或用户创建的残局，与AI对弈来练习残局技巧。可以获取提示和悔棋。' },
      { title: '从棋谱开始', desc: '前往棋谱库选择一个对局，在对局详情页播放到某个局面后，点击"截取残局"按钮将局面保存到残局库，然后跳转到AI对弈练习继续对弈。', link: '/games' },
      { title: '自定义FEN', desc: '直接输入FEN字符串来指定任意起始局面，适合练习特定局面。' },
      { title: '对局操作', desc: '对局中可以点击棋盘走棋，使用"提示"按钮获取AI推荐着法，使用"悔棋"撤销上一步，或"认输"结束对局。' },
    ],
  },
  {
    title: '残局库管理',
    open: false,
    steps: [
      { title: '浏览残局库', desc: '在残局库页面可以浏览所有预设和用户创建的残局，按分类、难度筛选。', link: '/puzzles' },
      { title: '创建残局', desc: '点击"创建残局"按钮，输入FEN和相关信息即可创建自定义残局。也可以从棋谱详情页截取残局自动保存。' },
      { title: '练习残局', desc: '在残局库中选择一个残局，点击"开始练习"即可跳转到AI对弈页面进行练习。' },
    ],
  },
  {
    title: '棋谱分析',
    open: false,
    steps: [
      { title: '启动分析', desc: '在对局详情页点击"分析"按钮，系统将使用Stockfish引擎对整局进行深度分析。' },
      { title: '查看分析结果', desc: '分析完成后，胜率走势图和每步着法的评价将自动显示。着法会被标注为妙着、好着、不精确、失误等。' },
      { title: 'AI建议', desc: '在右侧面板查看每步的AI建议着法和预测续着，帮助理解更好的走法选择。' },
    ],
  },
])

const faqs = [
  { q: '什么是FEN？', a: 'FEN（Forsyth-Edwards Notation）是一种用文本字符串描述国际象棋局面的标准格式。例如：<code>rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1</code> 表示初始局面。FEN包含棋子位置、行棋方、王车易位权利、吃过路兵目标和回合数等信息。' },
  { q: 'AI对弈练习的会话会过期吗？', a: '是的，AI对弈练习的会话存储在服务器内存中，服务器重启后会话将丢失。如果遇到"会话已过期"的提示，请重新开始一局新的对局。已完成的对局记录会保存在数据库中，不会丢失。' },
  { q: '如何截取棋谱中的某个局面进行练习？', a: '在对局详情页，使用播放控制器将棋局推进到你想要截取的局面，然后点击"截取残局"按钮。在弹出的对话框中填写残局信息后，点击"保存到残局库"即可。你也可以选择"仅开始练习"直接跳转到AI对弈页面。' },
  { q: 'AI难度等级有什么区别？', a: '入门（ELO约800）：适合初学者，AI会故意走出一些次优着法。初级（ELO约1200）：基本棋力，偶尔犯错。中级（ELO约1600）：有经验的棋手水平。高级（ELO约2000）：强棋手水平。专家（ELO约2400+）：接近大师水平，极少犯错。' },
  { q: '如何上传棋谱？', a: '点击顶部导航栏的"上传"按钮，选择PGN格式的棋谱文件上传。系统会自动解析PGN文件中的对局信息，包括棋手、开局、着法等。上传前请确保PGN文件格式正确。' },
  { q: '残局库中的预设残局可以删除吗？', a: '预设残局是系统内置的，不可删除。用户自己创建的残局可以在残局库中删除。' },
  { q: '为什么有时AI分析需要较长时间？', a: 'AI分析使用Stockfish引擎对每一步着法进行深度计算，分析时间取决于对局长度和服务器负载。通常一局标准对局（40步左右）需要1-3分钟完成分析。' },
  { q: '如何收藏棋谱？', a: '在对局详情页点击"收藏"按钮即可收藏该棋谱。收藏的棋谱可以在侧边栏的"我的收藏"中快速访问。需要登录后才能使用收藏功能。' },
]

const features = [
  { name: '棋谱库', desc: '浏览、搜索和查看国际象棋对局记录，支持PGN上传和自动解析。', icon: '📖', link: '/games' },
  { name: '棋手数据库', desc: '查看棋手信息、对局统计和历史战绩。', icon: '👤', link: '/players' },
  { name: '开局库', desc: '按ECO编码浏览开局变化，查看开局统计和常见续着。', icon: '♟', link: '/openings' },
  { name: '残局库', desc: '浏览和创建残局题目，支持从棋谱截取残局，追踪练习记录。', icon: '♛', link: '/puzzles' },
  { name: 'AI对弈练习', desc: '与Stockfish AI对弈，支持多种难度和练习模式。', icon: '🤖', link: '/practice' },
  { name: '棋谱分析', desc: '使用Stockfish引擎深度分析对局，查看胜率走势和着法评价。', icon: '📊', link: '/games' },
  { name: '数据分析', desc: '查看个人对局统计、开局偏好和胜率趋势。', icon: '📈', link: '/stats' },
]

function toggleTutorial(idx) {
  tutorials.value[idx].open = !tutorials.value[idx].open
}
</script>

<style scoped>
.help-page {
  max-width: 900px;
  margin: 0 auto;
}

.hp-header {
  margin-bottom: 24px;
}

.hp-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--text-color);
}

.hp-subtitle {
  color: var(--text-color-secondary);
  font-size: 14px;
  margin: 0;
}

.hp-tabs {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 16px 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.hp-progress-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.hp-progress-track {
  flex: 1;
  height: 8px;
  background: #ebeef5;
  border-radius: 4px;
  overflow: hidden;
}

.hp-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 4px;
  transition: width 0.3s;
}

.hp-progress-text {
  font-size: 12px;
  color: var(--text-color-secondary);
  white-space: nowrap;
}

.hp-tutorial.is-completed {
  border-color: #67c23a;
}

.hp-tutorial.is-completed .hp-tutorial-header {
  background: #f0f9eb;
}

.hp-tutorial-num.is-done {
  background: #67c23a;
}

.hp-step.is-done .hp-step-title {
  color: #67c23a;
  text-decoration: line-through;
}

.hp-tutorials {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hp-tutorial {
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.hp-tutorial-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.hp-tutorial-header:hover {
  background: var(--bg-color-secondary);
}

.hp-tutorial-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.hp-tutorial-title {
  flex: 1;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-color);
}

.hp-tutorial-arrow {
  color: var(--text-color-secondary);
  transition: transform 0.2s;
}

.hp-tutorial-arrow.is-open {
  transform: rotate(90deg);
}

.hp-tutorial-body {
  padding: 0 16px 16px 56px;
}

.hp-step {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #ebeef5;
}

.hp-step:last-child {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.hp-step-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.hp-step-num {
  font-size: 12px;
  color: #409eff;
  font-weight: 600;
}

.hp-step-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.hp-step-desc {
  font-size: 13px;
  color: var(--text-color-regular);
  line-height: 1.6;
  margin: 0 0 8px 0;
}

.hp-step-action {
  margin-top: 4px;
}

.hp-step-link {
  text-decoration: none;
}

.hp-faqs {
  max-width: 800px;
}

.hp-faq-answer {
  font-size: 13px;
  color: var(--text-color-regular);
  line-height: 1.8;
}

.hp-faq-answer :deep(code) {
  background: var(--bg-color-secondary);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
  color: #e6a23c;
}

.hp-features {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.hp-feature {
  display: flex;
  gap: 12px;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.2s;
}

.hp-feature:hover {
  border-color: #409eff;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
}

.hp-feature-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.hp-feature-info {
  flex: 1;
}

.hp-feature-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 4px;
}

.hp-feature-desc {
  font-size: 12px;
  color: var(--text-color-secondary);
  line-height: 1.5;
  margin-bottom: 6px;
}

.hp-feature-link {
  font-size: 12px;
  color: #409eff;
  text-decoration: none;
}

.hp-feature-link:hover {
  text-decoration: underline;
}
</style>
