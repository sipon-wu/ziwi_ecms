<template>
  <div class="page">
    <h2 class="page-title">碳预算管理</h2>

    <div class="page-toolbar">
      <label class="toolbar-label">月份:</label>
      <input type="month" v-model="month" @change="load" class="date-input" />
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-if="!loading && data">
      <!-- 预算卡片 -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">预算额度</div>
          <div class="kpi-val">{{ (data.allocated_ton * 1000 || 0).toLocaleString() }} <small>kgCO₂</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">已用量</div>
          <div class="kpi-val">{{ (data.used_ton * 1000 || 0).toLocaleString() }} <small>kgCO₂</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">剩余量</div>
          <div class="kpi-val">{{ remaining().toLocaleString() }} <small>kgCO₂</small></div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">使用比例</div>
          <div class="kpi-val">{{ usagePct().toFixed(1) }}<small>%</small></div>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="section">
        <h3>预算使用进度</h3>
        <div class="progress-wrap">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: usagePct() + '%' }" :class="progressClass()"></div>
          </div>
          <div class="progress-text">
            <span>{{ usagePct().toFixed(1) }}%</span>
            <span>{{ (data.used_ton * 1000 || 0).toLocaleString() }} / {{ (data.allocated_ton * 1000 || 0).toLocaleString() }} kgCO₂</span>
          </div>
        </div>
      </div>

      <!-- 超预算警告 -->
      <div v-if="usagePct() > 80" class="alert alert-warning">
        <span class="alert-icon">⚠</span>
        <div class="alert-content">
          <div class="alert-title">碳预算超过 80% 警告线</div>
          <div class="alert-desc">当前使用率 {{ usagePct().toFixed(1) }}%，请关注碳排放并采取减排措施。</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'

function pad(n) { return String(n).padStart(2,'0') }
function todayStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function pastDays(n) { const d=new Date(); d.setDate(d.getDate()-n); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function thisMonthStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1) }

const store = useEnergyStore()
const loading = ref(true)
const data = ref(null)
const month = ref(thisMonthStr())

async function load() {
  loading.value = true
  try {
    data.value = await store.fetchJSONRaw(`/api/carbon/budget?month=${month.value}`)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function usagePct() {
  if (!data.value || !data.value.allocated_ton) return 0
  return ((data.value.used_ton || 0) / data.value.allocated_ton) * 100
}

function remaining() {
  if (!data.value) return 0
  return Math.max(0, ((data.value.allocated_ton || 0) - (data.value.used_ton || 0)) * 1000)
}

function progressClass() {
  const pct = usagePct()
  if (pct > 90) return 'fill-danger'
  if (pct > 80) return 'fill-warning'
  return 'fill-normal'
}

onMounted(() => { load() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:18px; font-weight:700; color:#1a1a1a; margin:0 }
.page-toolbar { display:flex; gap:10px; align-items:center }
.toolbar-label { font-size:13px; color:#666 }
.date-input { padding:6px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section h3 { font-size:15px; color:#333; margin:0 0 20px 0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#0d7377; border-radius:3px 0 0 3px }
.kpi-label { font-size:12px; color:#999; margin-bottom:6px }
.kpi-val { font-size:26px; font-weight:700; color:#333 }
.kpi-val small { font-size:12px; font-weight:400; color:#999 }

.progress-wrap { padding: 10px 0 }
.progress-bar { width:100%; height:32px; background:#f0f0f0; border-radius:16px; overflow:hidden }
.progress-fill { height:100%; border-radius:16px; transition:width 0.6s ease; min-width:0 }
.fill-normal { background:linear-gradient(90deg, #0d7377, #14b8a6) }
.fill-warning { background:linear-gradient(90deg, #d97706, #f59e0b) }
.fill-danger { background:linear-gradient(90deg, #dc2626, #ef4444) }
.progress-text { display:flex; justify-content:space-between; margin-top:10px; font-size:13px; color:#666 }

.alert { display:flex; gap:14px; padding:16px 20px; border-radius:10px; align-items:flex-start }
.alert-warning { background:#fef3e2; border:1px solid #fcd34d }
.alert-icon { font-size:22px; flex-shrink:0; margin-top:2px }
.alert-title { font-size:14px; font-weight:600; color:#92400e; margin-bottom:4px }
.alert-desc { font-size:12px; color:#b45309 }
</style>
