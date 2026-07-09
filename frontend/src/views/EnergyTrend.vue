<template>
  <div class="page">
    <h2 class="page-title">能耗趋势</h2>

    <!-- Tab 切换 -->
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'day' }]" @click="switchTab('day')">日趋势</button>
      <button :class="['tab-btn', { active: activeTab === 'week' }]" @click="switchTab('week')">周趋势</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <div class="section">
        <div class="section-header">
          <h3>{{ activeTab === 'day' ? '小时级趋势 (' + currentDate + ')' : '近7日每日能耗趋势' }}</h3>
        </div>
        <div ref="chartRef" style="width:100%;height:400px"></div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useEnergyStore } from '../store/energy'
import * as echarts from 'echarts'

function pad(n) { return String(n).padStart(2,'0') }
function todayStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function pastDays(n) { const d=new Date(); d.setDate(d.getDate()-n); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function thisMonthStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1) }

const store = useEnergyStore()
const loading = ref(true)
const activeTab = ref('day')
const currentDate = ref(todayStr())
const trendData = ref(null)
const weeklyData = ref([])
const chartRef = ref(null)
let chartIns = null

async function switchTab(tab) {
  activeTab.value = tab
  loading.value = true
  chartIns?.dispose()
  chartIns = null
  try {
    if (tab === 'day') {
      trendData.value = await store.fetchJSONRaw(`/api/dashboard/trend?date=${currentDate.value}`)
    } else {
      const data = []
      for (let i = 1; i <= 7; i++) {
        const d = `${pastDays(7-i)}`
        try {
          const s = await store.fetchJSONRaw(`/api/dashboard/summary?date=${d}`)
          data.push({ date: d.slice(5), kwh: s?.today_kwh || 0 })
        } catch {
          data.push({ date: d.slice(5), kwh: 0 })
        }
      }
      weeklyData.value = data
    }
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart()
}

function renderChart() {
  if (!chartRef.value) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)

  if (activeTab.value === 'day' && trendData.value) {
    const t = trendData.value
    const timestamps = t.current_timestamps || t.timestamps || []
    const power = t.current_power || t.power || []
    chartIns.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 30, top: 20, bottom: 50 },
      xAxis: {
        type: 'category',
        data: timestamps,
        axisLabel: { interval: Math.max(1, Math.floor(timestamps.length / 12)), fontSize: 11, rotate: 30 }
      },
      yAxis: { type: 'value', name: 'kW' },
      series: [{
        type: 'bar',
        data: power.map(v => ({
          value: v,
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#8b5cf6' },
              { offset: 1, color: '#c4b5fd' }
            ])
          }
        })),
        barWidth: 10
      }]
    }, true)
  } else if (activeTab.value === 'week' && weeklyData.value.length) {
    chartIns.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 50, right: 30, top: 20, bottom: 40 },
      xAxis: { type: 'category', data: weeklyData.value.map(d => d.date) },
      yAxis: { type: 'value', name: 'kWh' },
      series: [{
        type: 'bar',
        data: weeklyData.value.map((d, i) => ({
          value: d.kwh,
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#0d9488' },
              { offset: 1, color: '#0d7377' }
            ])
          }
        })),
        barWidth: 36,
        label: { show: true, position: 'top', fontSize: 11, formatter: p => p.value.toLocaleString() }
      }]
    }, true)
  }
}

async function load() {
  await switchTab('day')
}

onMounted(() => { load() })
onUnmounted(() => { chartIns?.dispose() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.tabs { display:flex; gap:8px }
.tab-btn { padding:8px 20px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:#666; cursor:pointer; font-size:13px; transition:all 0.2s }
.tab-btn.active { background:#0d7377; color:#fff; border-color:#0d7377 }
.tab-btn:hover:not(.active) { border-color:#0d7377; color:#0d7377 }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }
</style>
