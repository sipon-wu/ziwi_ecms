<template>
  <div class="page">
    <h2 class="title">能流分析 — 桑基图</h2>
    <div class="toolbar">
      <label>起始:</label><input type="date" v-model="start" />
      <label>结束:</label><input type="date" v-model="end" />
      <button class="btn btn-primary" @click="load">查询</button>
      <span class="hint">展示能源从购入→转换→分配→利用的全过程流动与损耗</span>
    </div>

    <div v-if="data" class="section">
      <h3>总能流图 <small>（kWh）</small></h3>
      <div ref="chart" style="width:100%;height:520px"></div>
    </div>

    <div v-if="data" class="section">
      <h3>节点明细</h3>
      <table>
        <thead><tr><th>节点名称</th><th>流入(kWh)</th><th>流出(kWh)</th><th>净流量(kWh)</th></tr></thead>
        <tbody>
          <tr v-for="n in nodeStats" :key="n.name">
            <td><span class="color-dot" :style="{background:n.color}"></span> {{ n.name }}</td>
            <td>{{ n.inflow.toLocaleString() }}</td>
            <td>{{ n.outflow.toLocaleString() }}</td>
            <td :class="n.net>=0?'positive':'negative'">{{ n.net>=0?'+':'' }}{{ n.net.toLocaleString() }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="loading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { useEnergyStore } from '../store/energy'

function pad(n) { return String(n).padStart(2,'0') }
function todayStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function pastDays(n) { const d=new Date(); d.setDate(d.getDate()-n); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function thisMonthStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1) }

const store = useEnergyStore()
const start = ref(todayStr())
const end = ref(todayStr())
const data = ref(null)
const chart = ref(null)
let ch = null

// 节点流入流出统计
const nodeStats = computed(() => {
  if (!data.value) return []
  const map = {}
  for (const n of data.value.nodes) {
    map[n.name] = { name: n.name, color: n.itemStyle?.color || '#999', inflow: 0, outflow: 0, net: 0 }
  }
  for (const l of data.value.links) {
    if (map[l.target]) map[l.target].inflow += l.value
    if (map[l.source]) map[l.source].outflow += l.value
  }
  for (const k of Object.keys(map)) {
    map[k].inflow = Math.round(map[k].inflow * 100) / 100
    map[k].outflow = Math.round(map[k].outflow * 100) / 100
    map[k].net = Math.round((map[k].inflow - map[k].outflow) * 100) / 100
  }
  return Object.values(map).sort((a, b) => b.inflow - a.inflow)
})

async function load() {
  data.value = await store.fetchJSONRaw(
    `/api/analysis/energy_flow?start_date=${start.value}&end_date=${end.value}`
  )
  nextTick(render)
}

function render() {
  if (!chart.value || !data.value) return
  if (!ch) ch = echarts.init(chart.value)

  ch.setOption({
    tooltip: {
      trigger: 'item',
      triggerOn: 'mousemove',
      formatter: function(p) {
        if (p.dataType === 'edge' || p.data.source) {
          return `<b>${p.data.source}</b> → <b>${p.data.target}</b><br/>流量: <b>${p.data.value.toLocaleString()} kWh</b>`
        }
        return `<b>${p.name}</b>`
      }
    },
    series: [{
      type: 'sankey',
      layout: 'none',
      emphasis: { focus: 'adjacency' },
      nodeAlign: 'left',
      layoutIterations: 32,
      data: data.value.nodes,
      links: data.value.links.map(l => ({ ...l, lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.4 } })),
      label: { fontSize: 12, color: '#333' },
      lineStyle: { color: 'gradient', curveness: 0.5, opacity: 0.3 },
    }],
  }, true)
}

onMounted(load)
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.title { font-size:18px; color:#333; margin:0 }
.toolbar {
  display:flex; align-items:center; gap:10px;
  background:#fff; padding:12px 16px; border-radius:10px; border:1px solid #e8eaed;
  flex-wrap:wrap;
}
.toolbar label { font-size:13px; color:#666 }
.toolbar input { padding:6px 10px; border:1px solid #ddd; border-radius:6px; font-size:13px }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px; overflow-x:auto }
h3 { font-size:15px; color:#333; margin:0 0 16px 0 }
h3 small { font-size:12px; color:#999; font-weight:400 }
.hint { font-size:12px; color:#999; margin-left:auto }
table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 14px; border-bottom:1px solid #f0f0f0; text-align:left }
th { background:#f5f7fa; color:#666; font-weight:600 }
.color-dot { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:middle }
.positive { color:#00a870 }
.negative { color:#d32f2f }
.btn { padding:6px 16px; border:none; border-radius:6px; cursor:pointer; font-size:13px }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }
.loading { text-align:center; padding:80px; color:#aaa; font-size:14px }
</style>
