<template>
<div class="page">
  <h2 class="title">数据导入</h2>
  <p class="subtitle">上传 Excel 文件批量导入数据。所有数据追加写入，不影响原有 API 接口。</p>

  <!-- 导入流程步骤 -->
  <div class="steps">
    <div class="step"><span class="step-num">1</span> 选择数据类型</div>
    <div class="step-arrow">→</div>
    <div class="step"><span class="step-num">2</span> 下载模板</div>
    <div class="step-arrow">→</div>
    <div class="step"><span class="step-num">3</span> 按模板填数据</div>
    <div class="step-arrow">→</div>
    <div class="step"><span class="step-num">4</span> 上传导入</div>
  </div>

  <!-- 导入面板 -->
  <div class="section">
    <div class="panel-row">
      <div class="panel-left">
        <label class="label">选择导入类型：</label>
        <select v-model="selectedTable" class="select">
          <option value="">-- 请选择 --</option>
          <option v-for="t in tables" :key="t.table_name" :value="t.table_name">
            {{ t.title }}（{{ t.field_count }}个字段）
          </option>
        </select>
        <p v-if="selectedDesc" class="desc">{{ selectedDesc }}</p>
      </div>
      <div class="panel-right">
        <button class="btn btn-outline" :disabled="!selectedTable" @click="downloadTemplate">📥 下载模板</button>
        <label class="btn btn-primary upload-btn">
          上传 Excel 导入
          <input type="file" accept=".xlsx,.xls" hidden @change="uploadFile" />
        </label>
      </div>
    </div>
  </div>

  <!-- 导入结果 -->
  <div v-if="resultMsg" class="section result" :class="{ success: resultOk, error: !resultOk }">
    <span v-html="resultMsg"></span>
  </div>

  <!-- 数据源清单 -->
  <div class="section">
    <h3 class="section-title">📋 数据源清单</h3>
    <table>
      <thead>
        <tr><th>#</th><th>数据源</th><th>说明</th><th>当前状态</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="(t, i) in tables" :key="t.table_name">
          <td>{{ i + 1 }}</td>
          <td>{{ t.title }}</td>
          <td class="td-desc">{{ t.desc }}</td>
          <td><span class="badge" :class="i < 9 ? 'badge-green' : 'badge-orange'">{{ i < 9 ? 'DB已有' : '需导入' }}</span></td>
          <td><button class="btn-link" @click="selectedTable=t.table_name; downloadTemplate()">下载模板</button></td>
        </tr>
      </tbody>
    </table>
  </div>
</div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'

const store = useEnergyStore()
const tables = ref([])
const selectedTable = ref('')
const resultMsg = ref('')
const resultOk = ref(false)

const selectedDesc = computed(() => {
  const t = tables.value.find(t => t.table_name === selectedTable.value)
  return t ? t.desc : ''
})

onMounted(async () => {
  try {
    const d = await store.fetchJSONRaw('/api/import/tables')
    tables.value = d?.tables || []
  } catch { tables.value = [] }
})

async function downloadTemplate() {
  if (!selectedTable.value) return
  const url = `/api/import/${selectedTable.value}/template`
  try {
    const resp = await fetch(url)
    if (!resp.ok) { resultMsg.value = `下载失败：${resp.status}`; resultOk.value = false; return }
    const blob = await resp.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `知微能碳-导入模板-${selectedTable.value}.xlsx`
    link.click()
    URL.revokeObjectURL(link.href)
    resultMsg.value = `✅ 模板已下载，请在 Excel 中填入数据后重新上传导入`
    resultOk.value = true
  } catch (e) {
    resultMsg.value = `下载异常：${e.message}`
    resultOk.value = false
  }
}

async function uploadFile(e) {
  const file = e.target.files[0]
  if (!file || !selectedTable.value) return
  if (!file.name.endsWith('.xlsx')) {
    resultMsg.value = '⚠️ 仅支持 .xlsx 格式'
    resultOk.value = false; return
  }
  const formData = new FormData()
  formData.append('file', file)
  try {
    const resp = await fetch(`/api/import/${selectedTable.value}`, { method: 'POST', body: formData })
    const d = await resp.json()
    if (d.code === 0) {
      resultMsg.value = `✅ 导入成功！共导入 <b>${d.data.imported}</b> 条记录到「${d.data.title}」`
      resultOk.value = true
    } else {
      resultMsg.value = `⚠️ 导入失败：${d.message}`
      resultOk.value = false
    }
  } catch (e) {
    resultMsg.value = `⚠️ 导入异常：${e.message}`
    resultOk.value = false
  }
  e.target.value = ''
}
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.title { font-size:18px; color:#333; margin-bottom:0 }
.subtitle { font-size:13px; color:#888; margin:0 }
.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px }
.steps { display:flex; align-items:center; gap:12px; justify-content:center; margin:8px 0 16px }
.step { display:flex; align-items:center; gap:8px; padding:8px 16px; background:#f0f7ff; border-radius:20px; font-size:13px; color:#333 }
.step-num { display:inline-flex; width:22px; height:22px; border-radius:50%; background:#0d7377; color:#fff; align-items:center; justify-content:center; font-size:12px; font-weight:bold }
.step-arrow { color:#bbb; font-size:16px }

.panel-row { display:flex; align-items:flex-start; gap:20px; justify-content:space-between; flex-wrap:wrap }
.panel-left { flex:1; min-width:250px }
.panel-right { display:flex; gap:10px; align-items:center; flex-wrap:wrap }
.label { font-size:13px; color:#555; margin-bottom:6px; display:block }
.select { width:100%; padding:8px 12px; border:1px solid #d0d5dd; border-radius:6px; font-size:13px; background:#fff }
.desc { font-size:12px; color:#888; margin:6px 0 0 }
.btn { padding:8px 20px; border-radius:6px; font-size:13px; cursor:pointer; white-space:nowrap }
.btn-primary { background:#0d7377; color:#fff; border:none }
.btn-outline { background:#fff; color:#0d7377; border:1px solid #0d7377 }
.btn:disabled { opacity:0.5; cursor:not-allowed }
.upload-btn { position:relative; display:inline-flex; align-items:center; gap:4px }
.btn-link { background:none; border:none; color:#0d7377; cursor:pointer; font-size:12px; text-decoration:underline }
.result { text-align:center; font-size:14px }
.result.success { background:#f0faf0; border-color:#b8e6b8; color:#2e7d32 }
.result.error { background:#fef2f2; border-color:#fecaca; color:#b91c1c }
.section-title { font-size:15px; color:#333; margin:0 0 12px }
table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 14px; border-bottom:1px solid #f0f0f0; text-align:left }
th { background:#f5f7fa; color:#666; font-weight:500 }
.td-desc { color:#888; font-size:12px; max-width:300px }
.badge { display:inline-block; padding:2px 10px; border-radius:10px; font-size:11px }
.badge-green { background:#e8f5e9; color:#2e7d32 }
.badge-orange { background:#fff3e0; color:#ef6c00 }
</style>
