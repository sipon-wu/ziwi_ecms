<template>
  <div class="page">
    <h2 class="page-title">实时数据监控</h2>

    <!-- 总功率显示 -->
    <div v-if="realtime" class="total-power-card">
      <div class="total-label">当前总功率</div>
      <div class="total-val">{{ (realtime.total_active_power_kw || 0).toFixed(2) }} <small>kW</small></div>
      <div class="total-time">数据更新时间: {{ lastUpdate }}</div>
    </div>

    <!-- 工具栏 -->
    <div class="toolbar">
      <button @click="refresh" class="btn btn-primary" :disabled="refreshing">刷新</button>
      <label class="toggle-label">
        <input type="checkbox" v-model="autoRefresh" @change="toggleAutoRefresh" />
        自动刷新 (10s)
      </label>
      <span class="status" :class="{ connected: !fetchError, error: fetchError }">
        {{ fetchError ? '连接异常' : '已连接' }}
      </span>
    </div>

    <!-- 数据表格 -->
    <div class="section" v-if="realtime">
      <table>
        <thead>
          <tr>
            <th>设备名称</th>
            <th>有功功率 (kW)</th>
            <th>电流 (A)</th>
            <th>电压 (V)</th>
            <th>功率因数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in realtime.devices || realtime" :key="d.name || d.device_name">
            <td>{{ d.name || d.device_name }}</td>
            <td>{{ (d.active_power_kw || 0).toFixed(2) }}</td>
            <td>{{ (d.current_a || 0).toFixed(2) }}</td>
            <td>{{ (d.voltage_v || 0).toFixed(1) }}</td>
            <td>{{ (d.power_factor || 0).toFixed(2) }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div v-else class="loading">加载中...</div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useEnergyStore } from '../store/energy'

const store = useEnergyStore()
const realtime = ref(null)
const lastUpdate = ref('')
const autoRefresh = ref(true)
const refreshing = ref(false)
const fetchError = ref(false)
let timer = null

function formatTime() {
  const now = new Date()
  return now.toLocaleTimeString('zh-CN', { hour12: false })
}

async function refresh() {
  refreshing.value = true
  fetchError.value = false
  try {
    realtime.value = await store.fetchJSONRaw('/api/monitoring/current')
    lastUpdate.value = formatTime()
  } catch {
    fetchError.value = true
  } finally {
    refreshing.value = false
  }
}

function toggleAutoRefresh() {
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

function startAutoRefresh() {
  stopAutoRefresh()
  timer = setInterval(refresh, 10000)
}

function stopAutoRefresh() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(async () => {
  await refresh()
  if (autoRefresh.value) startAutoRefresh()
})

onUnmounted(() => { stopAutoRefresh() })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.total-power-card { background:linear-gradient(135deg, #0d7377, #0d9488); border-radius:10px; padding:24px; color:#fff; text-align:center }
.total-label { font-size:14px; opacity:0.85; margin-bottom:8px }
.total-val { font-size:42px; font-weight:700 }
.total-val small { font-size:16px; font-weight:400; opacity:0.8 }
.total-time { font-size:12px; opacity:0.7; margin-top:8px }

.toolbar { display:flex; gap:16px; align-items:center; flex-wrap:wrap }
.btn { padding:8px 20px; border:none; border-radius:6px; cursor:pointer; font-size:13px }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }
.btn-primary:disabled { opacity:0.5; cursor:not-allowed }
.toggle-label { font-size:13px; color:#666; display:flex; align-items:center; gap:6px; cursor:pointer }
.status { font-size:12px; padding:4px 10px; border-radius:10px }
.status.connected { background:#e6f7ec; color:#00a854 }
.status.error { background:#fff1f0; color:#e74c3c }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px; overflow-x:auto }

table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 14px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#fafafa; color:#666; font-weight:600; white-space:nowrap }
td { color:#333 }
tbody tr:hover { background:#f8f9ff }
</style>
