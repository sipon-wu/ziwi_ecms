<template>
  <div class="page">
    <h2 class="page-title">用能结构</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 设备组能耗饼图 -->
      <div class="section">
        <div class="section-header">
          <h3>各设备组能耗占比</h3>
        </div>
        <div ref="pieChartRef" style="width:100%;height:380px"></div>
      </div>

      <!-- 峰平谷时段柱状图 -->
      <div class="section" v-if="peakValley">
        <div class="section-header">
          <h3>峰平谷时段用电分布</h3>
        </div>
        <div ref="barChartRef" style="width:100%;height:360px"></div>
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
const balance = ref(null)
const peakValley = ref(null)
const pieChartRef = ref(null)
const barChartRef = ref(null)
let pieIns = null, barIns = null

async function load() {
  loading.value = true
  try {
    balance.value = await store.fetchJSONRaw(`/api/analysis/balance?date=${todayStr()}`)
    peakValley.value = await store.fetchJSONRaw(`/api/system/peak_valley?date=${todayStr()}`)
  } finally {
    loading.value = false
  }
  await nextTick()
  renderPie()
  if (peakValley.value) renderBar()
}

function renderPie() {
  if (!pieChartRef.value || !balance.value) return
  if (!pieIns) pieIns = echarts.init(pieChartRef.value)

  const groups = balance.value.breakdown || []
  const data = groups.map(g => ({ name: g.name, value: g.kwh || 0 }))

  pieIns.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} kWh ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 12 } },
    series: [{
      type: 'pie',
      radius: ['45%', '72%'],
      center: ['50%', '48%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
      label: { formatter: '{b}\n{d}%', fontSize: 11 },
      data,
      emphasis: { label: { fontSize: 16, fontWeight: 'bold' } }
    }]
  }, true)
}

function renderBar() {
  if (!barChartRef.value || !peakValley.value) return
  if (!barIns) barIns = echarts.init(barChartRef.value)

  const pv = peakValley.value
  const hours = pv.hours || []
  const groupNames = hours.map(h => h.hour)
  const peakData = hours.map(h => h.avg_kw || 0)
  const flatData = hours.map(h => h.max_kw || 0)
  const valleyData = hours.map(h => h.min_kw || 0)

  barIns.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['峰时', '平时', '谷时'], top: 6 },
    grid: { left: 50, right: 30, top: 50, bottom: 40 },
    xAxis: { type: 'category', data: groupNames, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', name: 'kWh' },
    series: [
      { name: '峰时', type: 'bar', stack: 'total', data: peakData, itemStyle: { color: '#e74c3c' }, barWidth: 40 },
      { name: '平时', type: 'bar', stack: 'total', data: flatData, itemStyle: { color: '#f39c12' } },
      { name: '谷时', type: 'bar', stack: 'total', data: valleyData, itemStyle: { color: '#3498db' } }
    ]
  }, true)
}

onMounted(() => { load() })
onUnmounted(() => { pieIns?.dispose(); barIns?.dispose() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }
</style>
