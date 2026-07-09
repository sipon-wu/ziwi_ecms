<template>
  <div class="page">
    <h2 class="page-title">碳核查支撑</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-if="!loading && data">
      <!-- 核查状态 -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">核查年度</div>
          <div class="kpi-val">{{ data.year || new Date().getFullYear() }}</div>
        </div>
        <div class="kpi-card" :class="statusCardClass()">
          <div class="kpi-label">核查状态</div>
          <div class="kpi-val kpi-status">{{ auditStatusText() }}</div>
        </div>
      </div>

      <!-- 核查清单 -->
      <div class="section">
        <h3>核查清单</h3>
        <div class="checklist">
          <div class="checklist-item" v-for="(item, i) in checklist" :key="i" :class="{ completed: item.done }">
            <div class="check-icon" :class="{ checked: item.done }">
              <span v-if="item.done">&#10003;</span>
              <span v-else>{{ i + 1 }}</span>
            </div>
            <div class="check-content">
              <div class="check-name">{{ item.name }}</div>
              <div class="check-desc" v-if="item.description">{{ item.description }}</div>
            </div>
            <span class="check-status" :class="item.done ? 'text-green' : 'text-gray'">
              {{ item.done ? '已完成' : '待完成' }}
            </span>
          </div>
        </div>
      </div>

      <!-- 材料包 -->
      <div class="section" v-if="data.download_url || data.materials">
        <h3>核查材料</h3>
        <div class="material-card">
          <div class="material-info">
            <div class="material-label">材料包下载地址</div>
            <div class="material-url">{{ data.download_url || data.materials || '-' }}</div>
          </div>
          <button class="btn btn-primary" @click="downloadMaterials">下载材料</button>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'

function pad(n) { return String(n).padStart(2,'0') }
function todayStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function pastDays(n) { const d=new Date(); d.setDate(d.getDate()-n); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function thisMonthStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1) }

const store = useEnergyStore()
const loading = ref(true)
const data = ref(null)

const auditStatus = computed(() => data.value?.audit_status || data.value?.status || 'pending')

const checklist = computed(() => {
  return data.value?.items || data.value?.checklist || [
    { name: '组织边界确认', description: '确认排放源边界和组织范围', done: true },
    { name: '排放源识别', description: '识别范围1和范围2排放源', done: true },
    { name: '活动数据收集', description: '收集能源消耗和物料使用数据', done: false },
    { name: '排放因子确认', description: '确认使用的碳排放因子', done: true },
    { name: '排放量计算', description: '完成碳排放量核算', done: false },
    { name: '数据质量审核', description: '审核数据的完整性和准确性', done: false },
    { name: '核查报告编制', description: '编制碳排放核查报告', done: false }
  ]
})

async function load() {
  loading.value = true
  try {
    data.value = await store.fetchJSONRaw(`/api/carbon/audit_support?year=${new Date().getFullYear()}`)
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function auditStatusText() {
  const map = { pending: '待核查', in_progress: '核查中', completed: '已通过', failed: '未通过' }
  return map[auditStatus.value] || auditStatus.value || '-'
}

function statusCardClass() {
  if (auditStatus.value === 'completed') return 'card-green'
  if (auditStatus.value === 'in_progress') return 'card-blue'
  if (auditStatus.value === 'failed') return 'card-red'
  return ''
}

function downloadMaterials() {
  alert('开始下载核查材料包...')
}

onMounted(() => { load() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:18px; font-weight:700; color:#1a1a1a; margin:0 }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section h3 { font-size:15px; color:#333; margin:0 0 16px 0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:18px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#0d7377; border-radius:3px 0 0 3px }
.kpi-card.card-green::before { background:#14b8a6 }
.kpi-card.card-blue::before { background:#4da6ff }
.kpi-card.card-red::before { background:#dc2626 }
.kpi-label { font-size:12px; color:#999; margin-bottom:6px }
.kpi-val { font-size:22px; font-weight:700; color:#333 }
.kpi-status { color:#0d7377 }

.checklist { display:flex; flex-direction:column; gap:4px }
.checklist-item { display:flex; align-items:flex-start; gap:14px; padding:14px 0; border-bottom:1px solid #f5f5f5 }
.checklist-item:last-child { border-bottom:none }
.checklist-item.completed { opacity:0.7 }
.check-icon { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; flex-shrink:0; border:2px solid #d9d9d9; color:#999; background:#fff }
.check-icon.checked { background:#0d7377; border-color:#0d7377; color:#fff }
.check-content { flex:1; min-width:0 }
.check-name { font-size:14px; color:#333; font-weight:500 }
.check-desc { font-size:12px; color:#999; margin-top:2px }
.check-status { font-size:12px; font-weight:600; flex-shrink:0; padding-top:4px }
.text-green { color:#0d7377 }
.text-gray { color:#999 }

.material-card { display:flex; align-items:center; gap:16px; padding:16px; background:#f8fafc; border:1px solid #e8eaed; border-radius:8px }
.material-info { flex:1; min-width:0 }
.material-label { font-size:12px; color:#999; margin-bottom:4px }
.material-url { font-size:13px; color:#4da6ff; word-break:break-all; font-family:monospace }

.btn { padding:6px 18px; border:none; border-radius:6px; cursor:pointer; font-size:13px; white-space:nowrap }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }
</style>
