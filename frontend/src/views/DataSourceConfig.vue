<template>
<div class="page">
  <h2 class="title">数据源管理</h2>
  <p class="subtitle">管理所有数据采集来源。第一阶段仅支持 Excel，后续版本将支持 MQTT/HTTP/ERP。</p>
  <div class="section">
    <div class="toolbar"><h3 class="sec-title">📡 数据源列表</h3></div>
    <table v-if="sources.length">
      <thead><tr><th>名称</th><th>类型</th><th>状态</th><th>备注</th><th>创建时间</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="s in sources" :key="s.id">
          <td>{{s.source_name}}</td>
          <td><span class="badge-type">{{s.source_type}}</span></td>
          <td><span class="badge" :class="s.status==='active'?'badge-green':'badge-gray'">{{s.status}}</span></td>
          <td class="td-desc">{{s.remark||'—'}}</td>
          <td>{{s.created_at?.split(' ')[0]||'—'}}</td>
          <td><button class="btn-link" @click="delSource(s.id)">删除</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">暂无数据源，请先通过数据导入功能导入数据</div>
  </div>
  <div class="section">
    <h3 class="sec-title">📋 导入记录</h3>
    <table v-if="logs.length">
      <thead><tr><th>目标表</th><th>文件名</th><th>记录数</th><th>状态</th><th>导入人</th><th>时间</th></tr></thead>
      <tbody>
        <tr v-for="l in logs" :key="l.id">
          <td>{{l.table_name}}</td><td class="td-desc">{{l.file_name||'—'}}</td>
          <td>{{l.records_imported}}</td>
          <td><span class="badge" :class="l.status==='success'?'badge-green':'badge-red'">{{l.status}}</span></td>
          <td>{{l.imported_by||'—'}}</td>
          <td>{{l.imported_at?.split(' ')[0]||'—'}}</td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">暂无导入记录</div>
  </div>
  <div class="section notice">
    <p>📖 <b>API 采集方式（即将支持）</b>：后续版本将支持 MQTT、HTTP 和 ERP 数据采集对接。</p>
    <p>技术对接请联系：<a href="mailto:fengliang@ziwi.cn">fengliang@ziwi.cn</a></p>
  </div>
</div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'
const store=useEnergyStore()
const sources=ref([]),logs=ref([])

onMounted(async()=>{
  try{const d=await store.fetchJSONRaw('/api/datasource/list');sources.value=d?.sources||[]}catch{}
  try{const d=await store.fetchJSONRaw('/api/datasource/logs');logs.value=d?.items||[]}catch{}
})
async function delSource(id){
  if(!confirm('确认删除？'))return
  try{await fetch(`/api/datasource/${id}`,{method:'DELETE'});sources.value=sources.value.filter(s=>s.id!==id)}catch{}
}
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}
.title{font-size:18px;color:#333;margin-bottom:0}
.subtitle{font-size:12px;color:#888;margin:0}
.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}
.notice{background:#f8fbff;border-color:#cce5ff}
.notice p{margin:4px 0;font-size:12px;color:#555}
.notice a{color:#0d7377}
.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.sec-title{font-size:15px;color:#333;margin:0}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0;text-align:left}
th{background:#f5f7fa;color:#666;font-weight:500}
.td-desc{color:#888;font-size:12px}
.empty{text-align:center;padding:30px;color:#aaa;font-size:13px}
.badge{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px}
.badge-green{background:#e8f5e9;color:#2e7d32}
.badge-gray{background:#f5f5f5;color:#888}
.badge-red{background:#fef2f2;color:#b91c1c}
.badge-type{display:inline-block;padding:2px 8px;border-radius:8px;font-size:11px;background:#e8f4fd;color:#0d5e6b}
.btn-link{background:none;border:none;color:#0d7377;cursor:pointer;font-size:12px;text-decoration:underline}
</style>
