<template>
<div class="page"><h2 class="title">碳配额管理</h2>
<div v-if="data" class="kpi-row"><div class="kpi-card"><div class="kl">年度总配额</div><div class="kv">{{data.total_quota_ton}} tCO2</div></div><div class="kpi-card"><div class="kl">已使用</div><div class="kv">{{data.total_used_ton}} tCO2</div></div><div class="kpi-card"><div class="kl">盈余</div><div class="kv">{{data.surplus_ton}} tCO2</div></div></div>
<div v-if="data" class="section"><table><thead><tr><th>组织</th><th>总配额(吨)</th><th>已使用(吨)</th><th>剩余(吨)</th><th>使用率</th></tr></thead><tbody><tr v-for="d in data.details" :key="d.org_id"><td>{{d.org_id===1?'知微集团':'德耐尔工厂'}}</td><td>{{d.total_quota_ton}}</td><td>{{d.used_ton}}</td><td>{{d.surplus_ton}}</td><td><div class="bar"><div class="fill" :style="{width:(d.used_ton/d.total_quota_ton*100)+'%',background:d.used_ton/d.total_quota_ton>0.8?'#f57c00':'#0d7377'}"></div></div> {{(d.used_ton/d.total_quota_ton*100).toFixed(1)}}%</td></tr></tbody></table></div>
<div v-else class="loading">加载中...</div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'

function pad(n) { return String(n).padStart(2,'0') }
function todayStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function pastDays(n) { const d=new Date(); d.setDate(d.getDate()-n); return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate()) }
function thisMonthStr() { const d=new Date(); return d.getFullYear()+'-'+pad(d.getMonth()+1) }

const store=useEnergyStore(),data=ref(null)
onMounted(async()=>{ data.value=await store.fetchJSONRaw(`/api/carbon_asset/quota?year=${new Date().getFullYear()}`) })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.kpi-card{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:18px;text-align:center}.kl{font-size:12px;color:#999}.kv{font-size:24px;font-weight:700;color:#333;margin-top:6px}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.bar{display:inline-block;width:100px;height:6px;background:#eee;border-radius:3px;overflow:hidden;margin-right:6px;vertical-align:middle}.fill{height:100%;border-radius:3px}.loading{text-align:center;padding:60px;color:#aaa}
</style>
