<template>
<div class="page">
  <div class="breadcrumb-bar">
    <router-link to="/supply/management" class="back-link">← 供应商管理</router-link>
    <span class="sep">/</span>
    <span>{{ supplier?.supplier_name || '加载中...' }}</span>
  </div>

  <!-- 供应商信息卡片 -->
  <div v-if="supplier" class="section info-card">
    <div class="info-left">
      <h3>{{ supplier.supplier_name }}</h3>
      <p class="info-meta">编码：{{ supplier.supplier_code }} | 联系人：{{ supplier.contact_person || '—' }} | 电话：{{ supplier.contact_phone || '—' }}</p>
    </div>
    <div class="info-right">
      <div class="kpi"><span class="kpi-val" :class="scoreClass">{{ supplier.carbon_score || '—' }}</span><span class="kpi-label">碳评分</span></div>
      <div class="kpi"><span class="kpi-val level">{{ supplier.carbon_level || '—' }}</span><span class="kpi-label">等级</span></div>
      <div class="kpi"><span class="kpi-val">{{ latestMonth || '—' }}</span><span class="kpi-label">最新提交</span></div>
    </div>
  </div>

  <!-- 登录地址提示 -->
  <div class="section notice">
    <p>🔗 供应商登录地址：<b>http://{{ host }}/gys/</b>（账号由管理员分配，初始密码在创建供应商时生成）</p>
    <p>📧 如有对接问题请联系：<a href="mailto:fengliang@ziwi.cn">fengliang@ziwi.cn</a></p>
  </div>

  <!-- 月度数据列表 -->
  <div class="section">
    <h3 class="sec-title">📊 月度能碳数据</h3>
    <table v-if="monthlyData.length">
      <thead><tr><th>月份</th><th>产品产量</th><th>电力(kWh)</th><th>天然气(m³)</th><th>水(吨)</th><th>碳排放(kg)</th><th>碳评分</th><th>等级</th><th>来源</th><th>提交时间</th></tr></thead>
      <tbody>
        <tr v-for="m in monthlyData" :key="m.id">
          <td><b>{{ m.report_month?.slice(0,7) }}</b></td>
          <td>{{ m.production_units || 0 }}</td>
          <td>{{ (m.electricity_kwh || 0).toLocaleString() }}</td>
          <td>{{ m.natural_gas_m3 || 0 }}</td>
          <td>{{ m.water_ton || 0 }}</td>
          <td>{{ (m.calculated_co2_kg || 0).toFixed(1) }}</td>
          <td><span class="score-badge" :class="scoreClass(m.carbon_score)">{{ m.carbon_score || '—' }}</span></td>
          <td><span class="lv" :class="'lv-'+m.carbon_level">{{ m.carbon_level || '—' }}</span></td>
          <td><span class="src-badge">{{ m.data_source || 'excel' }}</span></td>
          <td class="td-desc">{{ m.submitted_at?.split('T')[0] || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">该供应商尚未提交任何数据</div>
  </div>

  <!-- 提交日志 -->
  <div class="section">
    <h3 class="sec-title">📋 提交日志</h3>
    <table v-if="logs.length">
      <thead><tr><th>时间</th><th>文件名</th><th>记录数</th><th>状态</th></tr></thead>
      <tbody>
        <tr v-for="l in logs" :key="l.id">
          <td>{{ l.uploaded_at || l.imported_at }}</td>
          <td class="td-desc">{{ l.file_name || '—' }}</td>
          <td>{{ l.records_imported || '—' }}</td>
          <td><span class="badge" :class="l.status==='success'?'bg-green':'bg-red'">{{ l.status }}</span></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">暂无提交记录</div>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useEnergyStore } from '../store/energy'
const store = useEnergyStore()
const route = useRoute()
const supplier = ref(null); const monthlyData = ref([]); const logs = ref([])

const scoreClass = computed(() => {
  const s = supplier.value?.carbon_score || 0
  return s >= 80 ? 'score-a' : s >= 60 ? 'score-b' : 'score-c'
})
const latestMonth = computed(() => {
  if (!monthlyData.value.length) return ''
  return monthlyData.value[0].report_month?.slice(0,7) || ''
})
const host = ref(window.location.hostname)

onMounted(async () => {
  const id = route.params.id
  try {
    // 获取供应商信息
    const d = await store.fetchJSONRaw('/api/admin/suppliers')
    if (d?.items) supplier.value = d.items.find(s => s.id == id)
    // 获取月度数据（模拟）
    const sd = await store.fetchJSONRaw(`/api/admin/suppliers/${id}/data`)
    if (sd?.items) monthlyData.value = sd.items
  } catch {}
})
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}
.breadcrumb-bar{font-size:13px;color:#888}
.back-link{color:#0d7377;text-decoration:none}.back-link:hover{text-decoration:underline}
.sep{margin:0 8px;color:#ddd}
.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}
.info-card{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px}
.info-left h3{margin:0 0 6px;font-size:18px;color:#333}
.info-meta{font-size:12px;color:#888;margin:0}
.info-right{display:flex;gap:24px}
.kpi{text-align:center}.kpi-val{display:block;font-size:24px;font-weight:700;color:#333}
.kpi-val.level{font-size:20px}.kpi-label{font-size:11px;color:#888}
.score-a{color:#2e7d32}.score-b{color:#ef6c00}.score-c{color:#b91c1c}
.notice{background:#f8fbff;border-color:#cce5ff;font-size:12px;color:#555}
.notice p{margin:4px 0}.notice a{color:#0d7377}
.sec-title{font-size:15px;color:#333;margin:0 0 12px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0;text-align:left}
th{background:#f5f7fa;color:#666;font-weight:500}
.td-desc{color:#888;font-size:12px}
.empty{text-align:center;padding:30px;color:#aaa;font-size:13px}
.score-badge{padding:2px 8px;border-radius:4px;font-size:12px;font-weight:600}
.lv{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600}
.lv-A{background:#e8f5e9;color:#2e7d32}.lv-B{background:#fff3e0;color:#ef6c00}.lv-C{background:#fef2f2;color:#b91c1c}
.src-badge{background:#e8f4fd;color:#0d5e6b;padding:2px 6px;border-radius:3px;font-size:11px}
.badge{padding:2px 8px;border-radius:8px;font-size:11px}
.bg-green{background:#e8f5e9;color:#2e7d32}.bg-red{background:#fef2f2;color:#b91c1c}
</style>
