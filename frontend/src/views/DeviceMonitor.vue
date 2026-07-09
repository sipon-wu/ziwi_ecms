<template>
  <div class="page">
    <h2 class="page-title">设备监控</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-else>
      <!-- 仪表盘组 -->
      <div class="gauge-row">
        <div class="section gauge-card" v-for="(d, idx) in devices" :key="idx">
          <div class="gauge-title">{{ d.group_name || d.device_name || d.name }}</div>
          <div ref="gaugeRefs" :data-idx="idx" style="width:100%;height:220px"></div>
          <div class="gauge-info">
            <span>当前: {{ (d.avg_power_kw || d.current_power || 0).toFixed(1) }} kW</span>
            <span>额定: {{ (d.rated_power_kw || 0).toFixed(1) }} kW</span>
          </div>
        </div>
      </div>

      <!-- 设备组表格 -->
      <div class="section">
        <div class="section-header">
          <h3>设备组详情</h3>
        </div>
        <table>
          <thead>
            <tr>
              <th>设备组名称</th>
              <th>额定功率 (kW)</th>
              <th>当前平均功率 (kW)</th>
              <th>负载率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in devices" :key="d.group_name || d.name || d.device_name">
              <td>{{ d.group_name || d.device_name || d.name }}</td>
              <td>{{ (d.rated_power_kw || 0).toFixed(1) }}</td>
              <td>{{ (d.avg_power_kw || d.current_power || 0).toFixed(1) }}</td>
              <td>
                <span class="load-badge" :class="getLoadClass(d)">
                  {{ getLoadRate(d) }}%
                </span>
              </td>
            </tr>
          </tbody>
        </table>
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
const devices = ref([])
const gaugeRefs = ref(null)
const gaugeInstances = []

function getLoadRate(d) {
  const rated = d.rated_power_kw || d.rated_power || 1
  const current = d.avg_power_kw || d.current_power || 0
  return rated > 0 ? ((current / rated) * 100).toFixed(1) : 0
}

function getLoadClass(d) {
  const rate = parseFloat(getLoadRate(d))
  if (rate >= 80) return 'load-high'
  if (rate >= 50) return 'load-mid'
  return 'load-low'
}

async function load() {
  loading.value = true
  try {
    const data = await store.fetchJSONRaw(`/api/dashboard/ranking?date=${todayStr()}`)
    devices.value = data?.ranking || data || []
  } finally {
    loading.value = false
  }
  await nextTick()
  renderGauges()
}

function renderGauges() {
  if (!gaugeRefs.value) return
  const els = gaugeRefs.value
  if (!Array.isArray(els)) return
  els.forEach((el, idx) => {
    if (!el) return
    while (gaugeInstances.length <= idx) gaugeInstances.push(null)
    if (gaugeInstances[idx]) gaugeInstances[idx].dispose()
    const ins = echarts.init(el)
    gaugeInstances[idx] = ins

    const d = devices.value[idx] || {}
    const rate = parseFloat(getLoadRate(d))
    const rated = d.rated_power_kw || d.rated_power || 1
    const current = d.avg_power_kw || d.current_power || 0

    ins.setOption({
      series: [{
        type: 'gauge',
        startAngle: 210,
        endAngle: -30,
        center: ['50%', '58%'],
        radius: '88%',
        min: 0,
        max: rated,
        axisLine: {
          lineStyle: {
            width: 14,
            color: [
              [0.5, '#00d4aa'],
              [0.8, '#f39c12'],
              [1, '#e74c3c']
            ]
          }
        },
        pointer: { length: '60%', width: 6, itemStyle: { color: '#333' } },
        axisTick: { distance: -14, length: 6, lineStyle: { width: 1, color: '#999' } },
        splitLine: { distance: -18, length: 14, lineStyle: { width: 2, color: '#999' } },
        axisLabel: { distance: 20, fontSize: 10, color: '#666' },
        detail: {
          valueAnimation: true,
          formatter: '{value} kW',
          fontSize: 14,
          offsetCenter: [0, '72%']
        },
        data: [{ value: current, name: '负载率 ' + rate + '%' }]
      }]
    }, true)
  })
}

onMounted(() => { load() })
onUnmounted(() => { gaugeInstances.forEach(ins => ins?.dispose()) })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.gauge-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px }
.gauge-card { text-align:center }
.gauge-title { font-size:14px; font-weight:600; color:#333; margin-bottom:8px }
.gauge-info { display:flex; justify-content:space-around; font-size:11px; color:#999; margin-top:4px }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }

table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 14px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#fafafa; color:#666; font-weight:600 }
td { color:#333 }

.load-badge { display:inline-block; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600 }
.load-high { background:#fff1f0; color:#e74c3c }
.load-mid { background:#fff7e6; color:#f39c12 }
.load-low { background:#e6f7ec; color:#00a854 }
</style>
