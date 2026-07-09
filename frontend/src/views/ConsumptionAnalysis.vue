<template>
  <div class="page">
    <h2 class="page-title">能源消费量及强度</h2>

    <!-- 日期区间选择 -->
    <div class="toolbar">
      <label class="date-label">起始日期:</label>
      <input type="date" v-model="startDate" :min="pastDays(30)" :max="todayStr()" class="date-input" />
      <label class="date-label">结束日期:</label>
      <input type="date" v-model="endDate" :min="pastDays(30)" :max="todayStr()" class="date-input" />
      <button @click="load" class="btn btn-primary">查询</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 统计卡片 -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">总电耗</div>
          <div class="kpi-val">{{ (intensity?.total_kwh || 0).toLocaleString() }} <small>kWh</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">综合能耗</div>
          <div class="kpi-val">{{ (intensity?.total_energy_tce || 0).toFixed(2) }} <small>吨标煤</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">单位产品能耗</div>
          <div class="kpi-val">{{ (intensity?.energy_per_product || 0).toFixed(2) }} <small>kWh/台</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">单位产值能耗</div>
          <div class="kpi-val">{{ (intensity?.energy_per_output_value || 0).toFixed(2) }} <small>kWh/万元</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">总产量</div>
          <div class="kpi-val">{{ (intensity?.total_output || 0).toLocaleString() }} <small>台</small></div>
        </div>
      </div>

      <!-- 日用电柱状图 -->
      <div class="section">
        <div class="section-header">
          <h3>日用电量趋势</h3>
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
const startDate = ref(pastDays(7))
const endDate = ref(todayStr())
const intensity = ref(null)
const dailyKwh = ref([])
const chartRef = ref(null)
let chartIns = null

async function load() {
  loading.value = true
  try {
    intensity.value = await store.fetchJSONRaw(
      `/api/analysis/energy_intensity?start_date=${startDate.value}&end_date=${endDate.value}`
    )

    const start = new Date(startDate.value)
    const end = new Date(endDate.value)
    const days = []
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      const ds = d.toISOString().slice(0, 10)
      try {
        const s = await store.fetchJSONRaw(`/api/dashboard/summary?date=${ds}`)
        days.push({ date: ds.slice(5), kwh: s?.today_kwh || 0 })
      } catch {
        days.push({ date: ds.slice(5), kwh: 0 })
      }
    }
    dailyKwh.value = days
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart()
}

function renderChart() {
  if (!chartRef.value || !dailyKwh.value.length) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)

  chartIns.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 50, right: 30, top: 20, bottom: 40 },
    xAxis: { type: 'category', data: dailyKwh.value.map(d => d.date) },
    yAxis: { type: 'value', name: 'kWh' },
    series: [{
      type: 'bar',
      data: dailyKwh.value.map((d, i) => ({
        value: d.kwh,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#8b5cf6' },
            { offset: 1, color: '#c4b5fd' }
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

.toolbar { display:flex; gap:10px; align-items:center; flex-wrap:wrap }
.date-label { font-size:13px; color:#666 }
.date-input { padding:6px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px }
.btn { padding:8px 18px; border:none; border-radius:6px; cursor:pointer; font-size:13px }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#8b5cf6; border-radius:3px 0 0 3px }
.kpi-label { font-size:12px; color:#999; margin-bottom:6px }
.kpi-val { font-size:26px; font-weight:700; color:#333 }
.kpi-val small { font-size:12px; font-weight:400; color:#999 }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }
</style>
