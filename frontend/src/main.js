import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/theme-chalk/dark/css-vars.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import '@/styles/theme.css'
import '@/styles/global.scss'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, ScatterChart, HeatmapChart, CustomChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  VisualMapComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

import App from './App.vue'
import router from './router'
import pinia from './store'
import { useThemeStore } from './store'

use([
  CanvasRenderer,
  LineChart,
  BarChart,
  PieChart,
  ScatterChart,
  HeatmapChart,
  CustomChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
  DataZoomComponent,
  VisualMapComponent,
])

const app = createApp(App)

for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.component('v-chart', VChart)
app.use(ElementPlus, { locale: zhCn, size: 'default' })
app.use(pinia)
app.use(router)

const themeStore = useThemeStore()
themeStore.init()

app.mount('#app')
