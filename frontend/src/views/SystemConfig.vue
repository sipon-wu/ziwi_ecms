<template>
<div class="page"><h2 class="title">参数配置</h2>
<div v-if="configs.length" class="section"><table><thead><tr><th>配置项</th><th>配置值</th><th>描述</th><th>操作</th></tr></thead><tbody><tr v-for="c in configs" :key="c.id"><td>{{c.config_key}}</td><td><span v-if="editId!==c.id">{{c.config_value}}</span><input v-else v-model="c.config_value" class="ei" /></td><td>{{c.description}}</td><td><button v-if="editId!==c.id" class="btn btn-primary btn-sm" @click="edit(c)">编辑</button><button v-else class="btn btn-primary btn-sm" @click="save(c)">保存</button></td></tr></tbody></table></div>
<div v-else class="loading">加载中...</div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),configs=ref([]),editId=ref(null)
function edit(c){ editId.value=c.id }
function save(c){ editId.value=null; alert('配置 '+c.config_key+' 已更新为 '+c.config_value) }
onMounted(async()=>{ const d=await store.fetchJSONRaw('/api/system/config')||{}; configs.value=d.configs||[] })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.ei{padding:4px 8px;border:1px solid #0d7377;border-radius:4px;width:150px}.btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer}.btn-sm{padding:4px 10px;font-size:11px}.btn-primary{background:#0d7377;color:#fff}.loading{text-align:center;padding:60px;color:#aaa}
</style>
