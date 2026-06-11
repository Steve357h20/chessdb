<template>
  <div class="win-rate-chart" :style="{ height: height + 'px' }">
    <v-chart
      ref="chartRef"
      :option="chartOption"
      :autoresize="true"
      @click="onChartClick"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useThemeStore } from '@/store/themeStore'

const themeStore = useThemeStore()

const props = defineProps({
  analysisData: { type: Array, default: () => [] },
  currentMove: { type: Number, default: 0 },
  height: { type: Number, default: 300 },
  playerColor: { type: String, default: 'w' },
})

const emit = defineEmits(['move-select'])

const chartRef = ref(null)

const moveNumbers = computed(() => props.analysisData.map((_, i) => i + 1))

const isPlayerBlack = computed(() => props.playerColor === 'b')

const winRateData = computed(() => {
  const raw = props.analysisData.map(d => {
    let rate = d.white_win_rate != null ? d.white_win_rate : null
    if (rate != null && isPlayerBlack.value) rate = 100 - rate
    return rate != null ? Math.round(rate * 100) / 100 : null
  })
  if (raw.length <= 3) return raw
  const smoothed = []
  for (let i = 0; i < raw.length; i++) {
    if (raw[i] == null) { smoothed.push(null); continue }
    const start = Math.max(0, i - 1)
    const end = Math.min(raw.length - 1, i + 1)
    let sum = 0, count = 0
    for (let j = start; j <= end; j++) {
      if (raw[j] != null) { sum += raw[j]; count++ }
    }
    smoothed.push(Math.round(sum / count * 100) / 100)
  }
  return smoothed
})

const scoreData = computed(() =>
  props.analysisData.map(d => {
    if (d.score == null) return null
    let s = Math.round(d.score * 100) / 100
    if (isPlayerBlack.value) s = -s
    if (s > 10) return 10
    if (s < -10) return -10
    return s
  })
)

const markLine50 = computed(() => {
  if (!props.analysisData.length) return {}
  return {
    silent: true,
    symbol: 'none',
    lineStyle: { color: '#999', type: 'dashed', width: 1 },
    data: [{ yAxis: 50, label: { show: false } }],
  }
})

const markLine0 = computed(() => {
  if (!props.analysisData.length) return {}
  return {
    silent: true,
    symbol: 'none',
    lineStyle: { color: '#999', type: 'dashed', width: 1 },
    data: [{ yAxis: 0, label: { show: false } }],
  }
})

const currentMoveMark = computed(() => {
  if (!props.currentMove || !props.analysisData.length) return {}
  const idx = props.currentMove - 1
  if (idx < 0 || idx >= props.analysisData.length) return {}
  return {
    data: [
      {
        xAxis: idx + 1,
        label: { show: false },
        lineStyle: { color: '#e6a700', width: 2, type: 'solid' },
      },
    ],
    symbol: 'none',
    silent: true,
    animation: false,
  }
})

const chartOption = computed(() => {
  const isDark = themeStore.isDark
  const textColor = isDark ? '#e5eaf3' : '#303133'
  const axisLineColor = isDark ? '#4c4d4f' : '#e8e8e8'
  const splitLineColor = isDark ? '#363637' : '#e8e8e8'
  const secondaryColor = isDark ? '#a3a6ad' : '#909399'

  if (!props.analysisData.length) {
    return {
      title: {
        text: '暂无分析数据',
        left: 'center',
        top: 'center',
        textStyle: { color: secondaryColor, fontSize: 14, fontWeight: 'normal' },
      },
    }
  }

  return {
    animation: true,
    animationDuration: 300,
    backgroundColor: 'transparent',
    textStyle: { color: textColor },
    grid: {
      left: 55,
      right: 55,
      top: 25,
      bottom: 50,
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross', crossStyle: { color: secondaryColor } },
      formatter: formatTooltip,
      backgroundColor: isDark ? '#1d1d1d' : '#fff',
      borderColor: isDark ? '#4c4d4f' : '#e4e7ed',
      textStyle: { color: textColor },
    },
    xAxis: {
      type: 'category',
      data: moveNumbers.value,
      name: '步数',
      nameLocation: 'center',
      nameGap: 30,
      nameTextStyle: { color: textColor },
      axisLabel: {
        interval: Math.max(1, Math.floor(props.analysisData.length / 20)),
        fontSize: 11,
        color: textColor,
        formatter: (val) => {
          const n = parseInt(val)
          const moveNum = Math.ceil(n / 2)
          return n % 2 === 1 ? `${moveNum}.` : ''
        },
      },
      axisTick: { alignWithLabel: true },
      axisLine: { lineStyle: { color: axisLineColor } },
    },
    yAxis: [
      {
        type: 'value',
        name: '胜率',
        nameTextStyle: { color: textColor },
        min: 0,
        max: 100,
        interval: 10,
        axisLabel: { formatter: '{value}%', fontSize: 11, color: textColor },
        axisLine: { lineStyle: { color: axisLineColor } },
        splitLine: { lineStyle: { type: 'dashed', color: splitLineColor } },
      },
      {
        type: 'value',
        name: '分数',
        nameTextStyle: { color: textColor },
        min: -10,
        max: 10,
        interval: 2,
        axisLabel: { formatter: '{value}', fontSize: 11, color: textColor },
        axisLine: { lineStyle: { color: axisLineColor } },
        splitLine: { show: false },
      },
    ],
    dataZoom: [
      {
        type: 'inside',
        xAxisIndex: 0,
        filterMode: 'none',
      },
      {
        type: 'slider',
        xAxisIndex: 0,
        filterMode: 'none',
        bottom: 5,
        height: 18,
        borderColor: isDark ? '#4c4d4f' : '#ddd',
        fillerColor: 'rgba(64,158,255,0.15)',
        handleStyle: { color: '#409eff' },
        textStyle: { color: textColor },
      },
    ],
    series: [
      {
        name: isPlayerBlack.value ? '玩家胜率' : '白方胜率',
        type: 'line',
        yAxisIndex: 0,
        data: winRateData.value,
        smooth: 0.3,
        symbol: 'circle',
        symbolSize: 4,
        showSymbol: props.analysisData.length <= 60,
        lineStyle: { width: 2, color: '#409eff' },
        itemStyle: { color: '#409eff' },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64,158,255,0.35)' },
              { offset: 0.5, color: 'rgba(64,158,255,0.05)' },
              { offset: 0.5, color: 'rgba(245,108,108,0.05)' },
              { offset: 1, color: 'rgba(245,108,108,0.35)' },
            ],
          },
        },
        markLine: { ...markLine50.value, ...currentMoveMark.value },
        emphasis: {
          itemStyle: { borderWidth: 2, borderColor: '#409eff' },
        },
      },
      {
        name: '分数',
        type: 'line',
        yAxisIndex: 1,
        data: scoreData.value,
        smooth: 0.3,
        symbol: 'diamond',
        symbolSize: 3,
        showSymbol: props.analysisData.length <= 60,
        lineStyle: { width: 1.5, color: secondaryColor, type: 'dashed' },
        itemStyle: { color: secondaryColor },
        markLine: markLine0.value,
        emphasis: {
          itemStyle: { borderWidth: 2, borderColor: secondaryColor },
        },
      },
    ],
  }
})

function formatTooltip(params) {
  if (!params || !params.length) return ''
  const halfMove = params[0].axisValue
  const moveNum = Math.ceil(halfMove / 2)
  const color = halfMove % 2 === 1 ? '白' : '黑'
  let html = `<div style="font-weight:600;margin-bottom:4px">第${moveNum}回合 (${color}方)</div>`

  for (const p of params) {
    const colorDot = `<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${p.color};margin-right:4px"></span>`
    let value = ''
    if (p.seriesName === '白方胜率' || p.seriesName === '玩家胜率') {
      value = p.value != null ? `${p.value}%` : '-'
    } else if (p.seriesName === '分数') {
      value = p.value != null ? `${p.value > 0 ? '+' : ''}${p.value}` : '-'
    }
    html += `<div style="display:flex;align-items:center">${colorDot}${p.seriesName}：${value}</div>`
  }

  const dataItem = props.analysisData[halfMove - 1]
  if (dataItem) {
    if (dataItem.san) html += `<div style="margin-top:4px">着法：${dataItem.san}</div>`
    if (dataItem.best_moves?.[0]?.move) html += `<div style="color:#e6a700">最佳着法：${dataItem.best_moves[0].move}</div>`
  }

  return html
}

function onChartClick(params) {
  if (params.componentType === 'series') {
    emit('move-select', params.dataIndex + 1)
  }
}

watch(
  () => props.currentMove,
  (val) => {
    if (!chartRef.value || !props.analysisData.length) return
    const instance = chartRef.value.chart
    if (!instance) return
    const idx = val - 1
    if (idx < 0 || idx >= props.analysisData.length) return
    instance.dispatchAction({
      type: 'showTip',
      seriesIndex: 0,
      dataIndex: idx,
    })
  }
)
</script>

<style scoped>
.win-rate-chart {
  width: 100%;
}

.win-rate-chart :deep(.echarts) {
  width: 100% !important;
  height: 100% !important;
}
</style>
