<template>
<div class="page">
  <h2 class="title">供应商管理</h2>
  <p class="subtitle">管理所有供应商及其能碳数据。在此导入供应商列表，点击供应商名称查看其数据提交详情。</p>

  <div class="toolbar">
    <div class="toolbar-left">
      <span class="count">共 {{ total }} 家供应商</span>
    </div>
    <div class="toolbar-right">
      <button class="btn btn-outline" @click="downloadTemplate">📥 下载导入模板</button>
      <label class="btn btn-primary upload-btn">📤 批量导入供应商<input type="file" accept=".xlsx" hidden @change="importSuppliers" /></label>
      <button class="btn btn-primary" @click="showAdd=!showAdd">+ 新增供应商</button>
    </div>
  </div>

  <!-- 新增供应商弹窗 -->
  <div v-if="showAdd" class="modal-overlay" @click.self="showAdd=false">
    <div class="modal"><h3>新增供应商</h3>
      <div class="field"><label>供应商编码</label><input v-model="newCode" placeholder="SHTEEL001" /></div>
      <div class="field"><label>供应商名称</label><input v-model="newName" placeholder="上海XX钢材有限公司" /></div>
      <div class="field"><label>联系人</label><input v-model="newContact" placeholder="张三" /></div>
      <div class="field"><label>联系电话</label><input v-model="newPhone" placeholder="138****8888" /></div>
      <div class="modal-actions">
        <button class="btn btn-outline" @click="showAdd=false">取消</button>
        <button class="btn btn-primary" @click="addSupplier">保存并创建账号</button>
      </div>
    </div>
  </div>

  <!-- 供应商列表 -->
  <div class="section">
    <table v-if="items.length">
      <thead><tr><th>编码</th><th>供应商名称</th><th>联系人</th><th>碳评分</th><th>等级</th><th>最新提交</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="s in items" :key="s.id">
          <td><span class="code">{{ s.supplier_code }}</span></td>
          <td><router-link :to="`/supply/supplier/${s.id}`" class="link">{{ s.supplier_name }}</router-link></td>
          <td>{{ s.contact_person || '—' }}</td>
          <td><span class="score" :class="scoreClass(s.carbon_score)">{{ s.carbon_score || '—' }}</span></td>
          <td><span class="level-badge" :class="'level-'+s.carbon_level">{{ s.carbon_level || '—' }}</span></td>
          <td class="td-desc">{{ s.last_submit || '从未提交' }}</td>
          <td><span class="badge" :class="s.status==='active'?'badge-green':'badge-gray'">{{ s.status }}</span></td>
          <td>
            <button class="btn-link" @click="resetPwd(s)">重置密码</button>
            <button class="btn-link danger" @click="delSupplier(s)">删除</button>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">
      <p>暂无供应商数据</p>
      <p class="hint">请先「批量导入供应商」或「新增供应商」</p>
    </div>
  </div>

  <!-- 新生成的账号信息 -->
  <div v-if="newAccount" class="section account-info">
    <h3 class="sec-title">🔑 供应商账号已生成</h3>
    <div class="account-detail">
      <div class="ac-row"><span class="ac-label">登录地址：</span><span class="ac-val">http://<span class="hostname">{{ loginHost }}</span>/gys/</span></div>
      <div class="ac-row"><span class="ac-label">用户名：</span><span class="ac-val highlight">{{ newAccount.username }}</span></div>
      <div class="ac-row"><span class="ac-label">初始密码：</span><span class="ac-val highlight">{{ newAccount.password }}</span></div>
      <p class="ac-note">⚠️ 请将以上信息线下提供给供应商。供应商登录后可在「数据上传」页面下载模板并上传数据。</p>
      <button class="btn btn-sm" @click="newAccount=null">我知道了</button>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'
const store = useEnergyStore()
const items = ref([]); const total = ref(0)
const showAdd = ref(false); const newAccount = ref(null)
const newCode = ref(''); const newName = ref(''); const newContact = ref(''); const newPhone = ref('')
const loginHost = ref(window.location.hostname)

function scoreClass(s) { if (!s) return ''; return s >= 80 ? 'score-a' : s >= 60 ? 'score-b' : 'score-c' }

async function load() {
  try { const d = await store.fetchJSONRaw('/api/admin/suppliers'); items.value = d?.items || []; total.value = d?.total || 0 } catch {}
}
async function addSupplier() {
  if (!newCode.value || !newName.value) { alert('编码和名称必填'); return }
  try {
    const resp = await fetch('/api/admin/suppliers', { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ supplier_code: newCode.value, supplier_name: newName.value, contact_person: newContact.value, contact_phone: newPhone.value }) })
    const d = await resp.json()
    if (d.code === 0) { newAccount.value = d.data; showAdd.value = false; newCode.value = ''; newName.value = ''; newContact.value = ''; newPhone.value = ''; load() }
    else { alert(d.message) }
  } catch (e) { alert('操作失败：' + e.message) }
}
async function delSupplier(s) {
  if (!confirm(`确认删除「${s.supplier_name}」？`)) return
  try { await fetch(`/api/admin/suppliers/${s.id}`, { method: 'DELETE' }); load() } catch {}
}
async function resetPwd(s) {
  if (!confirm(`确认重置「${s.supplier_name}」的密码？`)) return
  try {
    const resp = await fetch(`/api/admin/suppliers/${s.id}/reset_password`, { method: 'POST' })
    const d = await resp.json()
    if (d.code === 0) newAccount.value = d.data
  } catch {}
}
async function downloadTemplate() {
  try {
    const resp = await fetch('/api/admin/suppliers/template')
    const blob = await resp.blob()
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = '知微能碳-导入模板-供应商基础信息.xlsx'; a.click()
  } catch {}
}
async function importSuppliers(e) {
  const file = e.target.files[0]; if (!file) return
  const fd = new FormData(); fd.append('file', file)
  try {
    const resp = await fetch('/api/admin/suppliers/import', { method: 'POST', body: fd })
    const d = await resp.json()
    if (d.code === 0) { alert(`导入成功：${d.data?.imported || 0} 条`); load() }
    else { alert('导入失败：' + d.message) }
  } catch (e) { alert('导入异常：' + e.message) }
  e.target.value = ''
}
onMounted(load)
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}
.title{font-size:18px;color:#333;margin-bottom:0}.subtitle{font-size:12px;color:#888;margin:0}
.toolbar{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}
.count{font-size:13px;color:#666}
.btn{padding:7px 16px;border-radius:6px;font-size:12px;cursor:pointer;border:none}
.btn-sm{padding:4px 12px;font-size:11px}
.btn-primary{background:#0d7377;color:#fff}
.btn-outline{background:#fff;color:#0d7377;border:1px solid #0d7377}
.upload-btn{display:inline-flex;align-items:center;gap:4px;position:relative}
.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0;text-align:left}
th{background:#f5f7fa;color:#666;font-weight:500}
.code{font-family:monospace;font-size:12px;color:#555;background:#f5f5f5;padding:2px 6px;border-radius:3px}
.link{color:#0d7377;text-decoration:none;font-weight:500}.link:hover{text-decoration:underline}
.td-desc{font-size:12px;color:#888}
.score{font-weight:600;padding:2px 8px;border-radius:4px;font-size:12px}
.score-a{color:#2e7d32;background:#e8f5e9}.score-b{color:#ef6c00;background:#fff3e0}.score-c{color:#b91c1c;background:#fef2f2}
.level-badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;font-weight:600}
.level-A{background:#e8f5e9;color:#2e7d32}.level-B{background:#fff3e0;color:#ef6c00}.level-C{background:#fef2f2;color:#b91c1c}.level-D{background:#fce4ec;color:#c62828}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px}
.badge-green{background:#e8f5e9;color:#2e7d32}.badge-gray{background:#f5f5f5;color:#888}
.btn-link{background:none;border:none;color:#0d7377;cursor:pointer;font-size:12px;text-decoration:underline;margin-right:8px}
.btn-link.danger{color:#b91c1c}
.empty{text-align:center;padding:40px;color:#aaa;font-size:14px}.hint{font-size:12px;color:#ccc;margin-top:8px}
.account-info{background:#f0faf0;border-color:#b8e6b8}
.sec-title{font-size:15px;color:#2e7d32;margin:0 0 12px}
.account-detail{font-size:13px}.ac-row{margin:6px 0}.ac-label{color:#555;display:inline-block;width:100px}.ac-val{color:#333}.highlight{color:#0d7377;font-weight:600;font-family:monospace;background:#e8f4fd;padding:2px 8px;border-radius:3px}
.ac-note{font-size:12px;color:#888;margin:12px 0 8px}
.field{margin-bottom:12px}.field label{display:block;font-size:12px;color:#555;margin-bottom:4px}
.field input{width:100%;padding:8px 10px;border:1px solid #d0d5dd;border-radius:6px;font-size:13px;box-sizing:border-box}
.modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:28px;width:420px;max-width:90vw}
.modal h3{margin:0 0 16px;font-size:16px}
.modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:16px}
</style>
