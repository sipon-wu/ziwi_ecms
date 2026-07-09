<template>
<div class="page"><h2 class="title">操作日志</h2>
<div class="toolbar"><select v-model="fu" @change="load" class="sel"><option value="">全部用户</option><option v-for="u in users" :key="u" :value="u">{{u}}</option></select></div>
<div v-if="logs.length" class="section"><table><thead><tr><th>时间</th><th>用户名</th><th>操作</th><th>目标</th><th>详情</th></tr></thead><tbody><tr v-for="l in logs" :key="l.id"><td>{{l.created_at}}</td><td>{{l.username}}</td><td><span class="badge badge-i">{{l.action}}</span></td><td>{{l.target}}</td><td>{{l.details}}</td></tr></tbody></table>
<div class="pager"><button :disabled="pg<=1" @click="pg--;load()">上一页</button><span>第 {{pg}} 页</span><button @click="pg++;load()">下一页</button></div></div>
<div v-else class="loading">加载中...</div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),logs=ref([]),pg=ref(1),fu=ref(''),users=ref([])
async function init(){ const u=await store.fetchJSONRaw('/api/system/users')||{}; if(u.data?.length) users.value=u.data.map(x=>x.username).filter(Boolean) }
async function load(){ const d=await store.fetchJSONRaw('/api/system/logs?page='+pg.value+'&page_size=20')||{}; logs.value=d.items||[]; if(fu.value) logs.value=logs.value.filter(l=>l.username===fu.value) }
onMounted(()=>{ init(); load() })
onMounted(load)
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.toolbar{display:flex;background:#fff;padding:12px 16px;border-radius:10px;border:1px solid #e8eaed}.sel{padding:6px 10px;border:1px solid #ddd;border-radius:6px;font-size:13px}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:10px 12px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.badge{padding:2px 8px;border-radius:4px;font-size:11px}.badge-i{background:#e3f2fd;color:#1976d2}.pager{margin-top:16px;display:flex;align-items:center;justify-content:center;gap:16px;font-size:13px;color:#666}.pager button{padding:6px 14px;border:1px solid #ddd;border-radius:6px;background:#fff;cursor:pointer}.pager button:disabled{opacity:0.4;cursor:not-allowed}.loading{text-align:center;padding:60px;color:#aaa}
</style>
