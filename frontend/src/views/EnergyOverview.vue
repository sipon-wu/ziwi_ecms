<template>
  <div class="page">
    <h2 class="page-title">用能概况</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- KPI 卡片 -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">综合能耗</div>
          <div class="kpi-val">{{ (intensity?.total_energy_tce || 0).toFixed(2) }} <small>tce</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">单位产值能耗</div>
          <div class="kpi-val">{{ (intensity?.energy_per_output_value || 0).toFixed(2) }} <small>kWh/万元</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">单位产品能耗</div>
          <div class="kpi-val">{{ (intensity?.energy_per_product || 0).toFixed(2) }} <small>kWh/台</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">今日下线数</div>
          <div class="kpi-val">{{ (intensity?.today_offline || 0).toLocaleString() }} <small>台</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">总产量</div>
          <div class="kpi-val">{{ (intensity?.total_output || 0).toLocaleString() }} <small>台</small></div>
        </div>
      </div>

      <!-- 7日能耗柱状图 -->
      <div class="section">
        <div class="section-header">
          <h3>近7日每日能耗</h3>
        </div>
        <div ref="chartRef" style="width:100%;height:380px"></div>
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
const intensity = ref(null)
const chartRef = ref(null)
let chartIns = null

const dates = []
for (let i = 1; i <= 7; i++) {
  dates.push(`${pastDays(7-i)}`)
}

async function load() {
  loading.value = true
  const dailyData = []
  try {
    intensity.value = await store.fetchJSONRaw(`/api/analysis/energy_intensity?start_date=${pastDays(6)}&end_date=${todayStr()}`)

    for (const d of dates) {
      try {
        const s = await store.fetchJSONRaw(`/api/dashboard/summary?date=${d}`)
        dailyData.push(s?.today_kwh || 0)
      } catch {
        dailyData.push(0)
      }
    }
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart(dailyData)
}

function renderChart(dailyData) {
  if (!chartRef.value) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)
  chartIns.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)),
      axisLabel: { fontSize: 12 }
    },
    yAxis: { type: 'value', name: 'kWh' },
    series: [{
      type: 'bar',
      data: dailyData.map((v, i) => ({
        value: v,
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

onMounted(() => { load() })
onUnmounted(() => { chartIns?.dispose() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#0d7377; border-radius:3px 0 0 3px }
.kpi-label { font-size:12px; color:#999; margin-bottom:6px }
.kpi-val { font-size:26px; font-weight:700; color:#333 }
.kpi-val small { font-size:12px; font-weight:400; color:#999 }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }
</style>
