<template>
  <div class="page">
    <!-- 日期选择 -->
    <div class="page-toolbar">
      <input type="date" v-model="date" @change="load" :min="minDate" :max="maxDate" class="date-input" />
      <button @click="load" class="btn btn-primary">刷新</button>
    </div>

    <!-- KPI 卡片 -->
    <div class="kpi-row" v-if="store.summary">
      <div class="kpi-card">
        <div class="kpi-label">今日用电</div>
        <div class="kpi-val">{{ (store.summary.today_kwh||0).toLocaleString() }} <small>kWh</small></div>
        <div class="kpi-vs">较昨日 <span :class="store.summary.today_vs_yesterday_pct>=0?'up':'down'">{{ store.summary.today_vs_yesterday_pct>=0?'+':'' }}{{ store.summary.today_vs_yesterday_pct }}%</span></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">当月用电</div>
        <div class="kpi-val">{{ (store.summary.month_kwh||0).toLocaleString() }} <small>kWh</small></div>
        <div class="kpi-vs">较上月 <span :class="store.summary.month_vs_last_month_pct>=0?'up':'down'">{{ store.summary.month_vs_last_month_pct>=0?'+':'' }}{{ store.summary.month_vs_last_month_pct }}%</span></div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">当年用电</div>
        <div class="kpi-val">{{ (store.summary.year_kwh||0).toLocaleString() }} <small>kWh</small></div>
        <div class="kpi-vs">较去年 <span :class="store.summary.year_vs_last_year_pct>=0?'up':'down'">{{ store.summary.year_vs_last_year_pct>=0?'+':'' }}{{ store.summary.year_vs_last_year_pct }}%</span></div>
      </div>
      <div class="kpi-card carbon">
        <div class="kpi-label">当日碳排放 (范围二)</div>
        <div class="kpi-val">{{ (store.summary.carbon_emission_ton||0).toFixed(2) }} <small>tCO₂</small></div>
        <div class="kpi-vs">{{ (store.summary.carbon_emission_kg||0).toLocaleString() }} kg</div>
      </div>
    </div>

    <!-- 趋势图 -->
    <div class="section">
      <div class="section-header">
        <h3>能耗趋势对比 — 当日 vs 昨日总有功功率</h3>
        <span class="section-tip">峰值标注 ●</span>
      </div>
      <div ref="trendChart" style="width:100%;height:380px"></div>
    </div>

    <!-- 排名 + 实时 双栏 -->
    <div class="two-col">
      <div class="section">
        <h3>设备能耗排名</h3>
        <div ref="rankChart" style="width:100%;height:300px"></div>
      </div>
      <div class="section">
        <h3>实时设备参数</h3>
        <div class="realtime-table" v-if="store.realtime">
          <table>
            <thead><tr><th>设备</th><th>功率(kW)</th><th>电流(A)</th><th>电压(V)</th><th>功率因数</th></tr></thead>
            <tbody>
              <tr v-for="d in store.realtime.devices" :key="d.name">
                <td>{{ d.name }}</td>
                <td>{{ d.active_power_kw }}</td>
                <td>{{ d.current_a }}</td>
                <td>{{ d.voltage_v }}</td>
                <td>{{ d.power_factor }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="loading" v-else>加载实时数据...</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useEnergyStore } from '../store/energy'
import * as echarts from 'echarts'

const store = useEnergyStore()

function fmtDate(d) {
  return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0')
}
const today = new Date()
const minDate = fmtDate(new Date(today.getTime()-30*86400000))
const maxDate = fmtDate(today)
const date = ref(fmtDate(today))
const trendChart = ref(null)
const rankChart = ref(null)
let trendIns = null, rankIns = null

async function load() {
  await store.initDashboard(date.value)
  await store.fetchRealtime()
  nextTick(() => { renderTrend(); renderRank() })
}

function renderTrend() {
  if (!trendChart.value || !store.trend) return
  if (!trendIns) trendIns = echarts.init(trendChart.value)
  const d = store.trend
  const opt = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['今日', '昨日'], top: 6, right: 20 },
    grid: { left: 50, right: 30, top: 50, bottom: 40 },
    xAxis: { type: 'category', data: d.current_timestamps, axisLabel: { interval: 23 } },
    yAxis: { type: 'value', name: 'kW' },
    series: [
      { name: '今日', type: 'line', data: d.current_power, smooth: true, symbol: 'none',
        lineStyle: { color: '#8b5cf6', width: 2 },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(139,92,246,0.2)'},{offset:1,color:'rgba(139,92,246,0.02)'}]) },
        markPoint: { data: [{ name:'峰值', coord: [d.peak.index, d.peak.value], value: d.peak.value.toFixed(0)+'kW', symbol:'pin', symbolSize:40, itemStyle:{color:'#8b5cf6'}, label:{color:'#fff',fontSize:10,formatter:'{c}'} }] }
      },
      { name: '昨日', type: 'line', data: d.yesterday_power, smooth: true, symbol: 'none',
        lineStyle: { color: '#0d9488', width: 1.5, type: 'dashed' },
        areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(13,148,136,0.12)'},{offset:1,color:'rgba(13,148,136,0.01)'}]) }
      }
    ]
  }
  trendIns.setOption(opt, true)
}

function renderRank() {
  if (!rankChart.value || !store.ranking?.ranking) return
  if (!rankIns) rankIns = echarts.init(rankChart.value)
  const r = [...store.ranking.ranking].reverse()
  rankIns.setOption({
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: p => `<b>${p[0].name}</b><br/>耗电: ${p[0].value.toLocaleString()} kWh` },
    grid: { left: 120, right: 60, top: 10, bottom: 20 },
    xAxis: { type: 'value', name: 'kWh' },
    yAxis: { type: 'category', data: r.map(x => x.device_name.length>8?x.device_name.slice(0,8)+'...':x.device_name) },
    series: [{ type: 'bar', data: r.map((x,i) => ({ value: Math.round(x.consumption_kwh),
        itemStyle: { borderRadius: [0,4,4,0],
        color: new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#0d7377'},{offset:1,color:i===4?'#0d9488':'#4da6ff'}]) }
    })), barWidth: 16, label: { show: true, position: 'right', fontSize: 10, formatter: '{c} kWh' } }]
  }, true)
}

onMounted(() => { load() })
onUnmounted(() => { trendIns?.dispose(); rankIns?.dispose() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-toolbar { display:flex; gap:10px; align-items:center }
.date-input { padding:6px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px }
.btn { padding:6px 18px; border:none; border-radius:6px; cursor:pointer; font-size:13px }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#0d7377; border-radius:3px 0 0 3px }
.kpi-card.carbon::before { background:#8b5cf6 }
.kpi-label { font-size:12px; color:#999; margin-bottom:6px }
.kpi-val { font-size:26px; font-weight:700; color:#333 }
.kpi-val small { font-size:12px; font-weight:400; color:#999 }
.kpi-vs { font-size:11px; color:#aaa; margin-top:4px }
.kpi-vs .up { color:#e74c3c }
.kpi-vs .down { color:#00d4aa }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333 }
.section-tip { font-size:11px; color:#8b5cf6 }

.two-col { display:grid; grid-template-columns:1fr 1fr; gap:12px }
@media (max-width:1000px) { .two-col{grid-template-columns:1fr} }

table { width:100%; border-collapse:collapse; font-size:12px }
th, td { padding:10px 12px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#fafafa; color:#666; font-weight:600 }
td { color:#333 }
.loading { text-align:center; padding:40px; color:#aaa; font-size:13px }
</style>
