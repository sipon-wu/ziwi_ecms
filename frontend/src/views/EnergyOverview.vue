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

      <!-- 年度每月产量与能耗（可下钻各设备） -->
      <div class="section">
        <div class="section-header">
          <h3>年度每月产量与能耗（点击月份查看各设备能耗）</h3>
        </div>
        <div ref="chartRefCombined" style="width:100%;height:420px"></div>
        <div v-if="selectedMonth" class="drill">
          <div class="drill-header">
            <span>{{ selectedMonth }}月 · 各设备能耗</span>
            <button class="drill-close" @click="closeDrill">收起</button>
          </div>
          <div ref="chartRefDrill" style="width:100%;height:380px"></div>
        </div>
        <div v-else class="drill-hint">点击上方任意月份，查看该月各设备能耗明细</div>
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

const store = useEnergyStore()
const loading = ref(true)
const intensity = ref(null)
const chartRef = ref(null)
const chartRefCombined = ref(null)
const chartRefDrill = ref(null)
let chartIns = null
let chartInsCombined = null
let chartInsDrill = null

const selectedMonth = ref(null)
const drillLoading = ref(false)

const dates = []
for (let i = 1; i <= 7; i++) {
  dates.push(`${pastDays(7-i)}`)
}

async function load() {
  loading.value = true
  const dailyData = []
  let prod = null
  let monthly = null
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

    prod = await store.fetchJSONRaw('/api/analysis/monthly_production?year=2026')
    monthly = await store.fetchJSONRaw('/api/analysis/monthly_energy?year=2026')
  } finally {
    loading.value = false
  }
  await nextTick()
  renderChart(dailyData)
  renderCombined(prod?.units || [], monthly?.kwh || [])
}

function baseGrid() {
  return { left: '8%', right: '6%', top: '15%', bottom: '12%', containLabel: true }
}

function renderChart(dailyData) {
  if (!chartRef.value) return
  if (!chartIns) chartIns = echarts.init(chartRef.value)
  chartIns.setOption({
    tooltip: { trigger: 'axis' },
    grid: baseGrid(),
    xAxis: {
      type: 'category',
      data: dates.map(d => d.slice(5)),
      axisLabel: { fontSize: 12 }
    },
    yAxis: { type: 'value', name: 'kWh', axisLabel: { formatter: v => v.toLocaleString() } },
    series: [{
      type: 'bar',
      data: dailyData.map(v => ({
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

function renderCombined(units, kwh) {
  if (!chartRefCombined.value) return
  if (!chartInsCombined) chartInsCombined = echarts.init(chartRefCombined.value)
  const months = Array.from({ length: 12 }, (_, i) => `${i + 1}月`)
  chartInsCombined.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: p => {
        let s = `${p[0].name}<br/>`
        p.forEach(it => { s += `${it.marker} ${it.seriesName}: ${it.value.toLocaleString()}<br/>` })
        return s
      } },
    legend: { data: ['月能耗(kWh)', '月产量(台)'], top: 0 },
    grid: { left: '8%', right: '8%', top: '18%', bottom: '12%', containLabel: true },
    xAxis: { type: 'category', data: months, axisLabel: { fontSize: 12 } },
    yAxis: [
      { type: 'value', name: 'kWh', axisLabel: { formatter: v => v.toLocaleString() } },
      { type: 'value', name: '台', axisLabel: { formatter: v => v.toLocaleString() } }
    ],
    series: [
      { name: '月能耗(kWh)', type: 'bar', yAxisIndex: 0, barWidth: '45%',
        data: kwh.map(v => ({ value: v, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#0d9488' }, { offset: 1, color: '#0d7377' }]) } })),
        label: { show: true, position: 'top', fontSize: 10, formatter: p => p.value ? p.value.toLocaleString() : '' } },
      { name: '月产量(台)', type: 'line', yAxisIndex: 1, smooth: true, symbol: 'circle', symbolSize: 7,
        data: units, lineStyle: { width: 3, color: '#3b82f6' }, itemStyle: { color: '#3b82f6' },
        label: { show: true, position: 'top', fontSize: 10, formatter: p => p.value ? p.value.toLocaleString() : '' } }
    ]
  }, true)
  chartInsCombined.off('click')
  chartInsCombined.on('click', params => {
    if (params.componentType === 'series') fetchDrill(params.dataIndex + 1)
  })
}

async function fetchDrill(month) {
  selectedMonth.value = month
  drillLoading.value = true
  try {
    const r = await store.fetchJSONRaw(`/api/analysis/monthly_device_energy?year=2026&month=${month}`)
    await nextTick()
    renderDrill(r?.devices || [])
  } finally {
    drillLoading.value = false
  }
}

function renderDrill(devices) {
  if (!chartRefDrill.value) return
  if (!chartInsDrill) chartInsDrill = echarts.init(chartRefDrill.value)
  const names = devices.map(d => (d.device_name || '设备') + (d.device_code ? `(${d.device_code})` : ''))
  const vals = devices.map(d => d.energy_kwh)
  chartInsDrill.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: p => `${p[0].name}<br/>${p[0].marker} ${p[0].value.toLocaleString()} kWh` },
    grid: { left: '3%', right: '6%', top: '8%', bottom: '20%', containLabel: true },
    xAxis: { type: 'category', data: names, axisLabel: { fontSize: 10, rotate: 30, interval: 0 } },
    yAxis: { type: 'value', name: 'kWh', axisLabel: { formatter: v => v.toLocaleString() } },
    series: [{
      type: 'bar', barWidth: '55%',
      data: vals.map(v => ({ value: v, itemStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: '#3b82f6' }, { offset: 1, color: '#1d4ed8' }]), borderRadius: [4, 4, 0, 0] } })),
      label: { show: true, position: 'top', fontSize: 10, formatter: p => p.value ? p.value.toLocaleString() : '' }
    }]
  }, true)
}

function closeDrill() {
  selectedMonth.value = null
  chartInsDrill?.clear()
}

function onResize() {
  chartIns?.resize()
  chartInsCombined?.resize()
  chartInsDrill?.resize()
}

onMounted(() => {
  load()
  window.addEventListener('resize', onResize)
})
onUnmounted(() => {
  window.removeEventListener('resize', onResize)
  chartIns?.dispose()
  chartInsCombined?.dispose()
  chartInsDrill?.dispose()
})
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

.drill { margin-top:14px; border-top:1px dashed #e3e6ea; padding-top:14px }
.drill-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px }
.drill-header span { font-size:13px; color:#0d7377; font-weight:600 }
.drill-close { border:1px solid #d6d9de; background:#fff; color:#666; border-radius:6px; padding:4px 12px; font-size:12px; cursor:pointer }
.drill-close:hover { background:#f5f6f8 }
.drill-hint { margin-top:14px; text-align:center; color:#bbb; font-size:13px }

</style>
