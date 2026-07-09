<template>
  <div class="page">
    <h2 class="page-title">供应链碳管理</h2>

    <div v-if="loading" class="loading">加载中...</div>

    <template v-if="!loading && data">
      <!-- 供应商评价总览 -->
      <div class="kpi-row" v-if="data.suppliers">
        <div class="kpi-card">
          <div class="kpi-label">供应商总数</div>
          <div class="kpi-val">{{ data.suppliers.length || 0 }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">A级供应商</div>
          <div class="kpi-val">{{ gradeCount('A') }}</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">年均碳排放</div>
          <div class="kpi-val">{{ avgCarbon() }} <small>吨</small></div>
        </div>
      </div>

      <!-- 供应商表格 -->
      <div class="section">
        <h3>供应商碳评价</h3>
        <table>
          <thead>
            <tr><th>供应商名称</th><th>碳评分</th><th>等级</th><th>年碳排放(吨)</th><th>评价</th></tr>
          </thead>
          <tbody>
            <tr v-for="s in suppliers" :key="s.name">
              <td>{{ s.name || s.supplier_name || '-' }}</td>
              <td>
                <div class="score-bar-wrap">
                  <div class="score-bar" :style="{ width: scorePct(s) + '%' }" :class="scoreBarClass(s)"></div>
                </div>
                <span class="score-val">{{ s.score || s.carbon_score || 0 }}</span>
              </td>
              <td>
                <span :class="gradeBadgeClass(s.grade || s.level)">
                  {{ s.grade || s.level || '-' }}
                </span>
              </td>
              <td>{{ (s.annual_emission || s.carbon_annual || 0).toLocaleString() }}</td>
              <td class="eval-cell">{{ evaluationText(s) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'

const store = useEnergyStore()
const loading = ref(true)
const data = ref(null)

const suppliers = computed(() => data.value?.suppliers || [])

async function load() {
  loading.value = true
  try {
    data.value = await store.fetchJSONRaw('/api/carbon/supply')
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

function gradeCount(grade) {
  return suppliers.value.filter(s => (s.grade || s.level) === grade).length
}

function avgCarbon() {
  if (!suppliers.value.length) return 0
  const sum = suppliers.value.reduce((t, s) => t + (s.annual_emission || s.carbon_annual || 0), 0)
  return Math.round(sum / suppliers.value.length).toLocaleString()
}

function scorePct(s) {
  return Math.min((s.score || s.carbon_score || 0), 100)
}

function scoreBarClass(s) {
  const score = s.score || s.carbon_score || 0
  if (score >= 80) return 'bar-high'
  if (score >= 60) return 'bar-mid'
  return 'bar-low'
}

function gradeBadgeClass(grade) {
  const g = (grade || '').toString().toUpperCase()
  if (g === 'A') return 'badge badge-green'
  if (g === 'B') return 'badge badge-blue'
  if (g === 'C') return 'badge badge-yellow'
  return 'badge badge-gray'
}

function evaluationText(s) {
  const grade = (s.grade || s.level || '').toString().toUpperCase()
  if (grade === 'A') return '碳管理优秀'
  if (grade === 'B') return '碳管理良好'
  if (grade === 'C') return '需改进'
  return '-'
}

onMounted(() => { load() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:18px; font-weight:700; color:#1a1a1a; margin:0 }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.section h3 { font-size:15px; color:#333; margin:0 0 16px 0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.kpi-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:12px }
.kpi-card { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:16px; position:relative }
.kpi-card::before { content:''; position:absolute; left:0; top:0; width:3px; height:100%; background:#0d7377; border-radius:3px 0 0 3px }
.kpi-label { font-size:12px; color:#999; margin-bottom:4px }
.kpi-val { font-size:24px; font-weight:700; color:#333 }
.kpi-val small { font-size:12px; font-weight:400; color:#999 }

table { width:100%; border-collapse:collapse; font-size:12px }
th, td { padding:10px 12px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#fafafa; color:#666; font-weight:600 }
td { color:#333 }
.eval-cell { font-size:11px; color:#666 }

.score-bar-wrap { display:inline-block; width:60px; height:6px; background:#f0f0f0; border-radius:3px; margin-right:6px; vertical-align:middle }
.score-bar { height:100%; border-radius:3px }
.bar-high { background:#0d7377 }
.bar-mid { background:#4da6ff }
.bar-low { background:#f59e0b }
.score-val { font-size:11px; color:#666; vertical-align:middle }

.badge { padding:2px 10px; border-radius:10px; font-size:11px; font-weight:600 }
.badge-green { background:#e6f7e6; color:#0d7377 }
.badge-blue { background:#e6f0ff; color:#2563eb }
.badge-yellow { background:#fef3e2; color:#d97706 }
.badge-gray { background:#f3f4f6; color:#6b7280 }
</style>
