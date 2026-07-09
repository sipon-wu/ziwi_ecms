<template>
<div class="page"><h2 class="title">CCER项目管理</h2>
<div v-if="projects.length" class="section"><table><thead><tr><th>项目名称</th><th>类型</th><th>状态</th><th>预计减排(吨)</th><th>进度</th></tr></thead><tbody><tr v-for="p in projects" :key="p.name"><td>{{p.name}}</td><td>{{p.type}}</td><td><span class="badge" :class="p.status==='已核证'?'badge-s':p.status==='开发中'?'badge-w':'badge-i'">{{p.status}}</span></td><td>{{p.estimated_reduction_ton}}</td><td><div class="bar"><div class="fill" :style="{width:p.progress+'%'}"></div></div> {{p.progress}}%</td></tr></tbody></table></div>
<div v-else class="loading">加载中...</div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),projects=ref([])
onMounted(async()=>{ const d=await store.fetchJSONRaw('/api/carbon_asset/ccer')||{}; projects.value=d.projects||[] })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.badge{padding:2px 8px;border-radius:4px;font-size:11px}.badge-s{background:#e6f7f1;color:#00a870}.badge-w{background:#fff3e0;color:#f57c00}.badge-i{background:#e3f2fd;color:#1976d2}.bar{display:inline-block;width:100px;height:6px;background:#eee;border-radius:3px;overflow:hidden;margin-right:6px;vertical-align:middle}.fill{height:100%;border-radius:3px;background:#0d7377}.loading{text-align:center;padding:60px;color:#aaa}
</style>
