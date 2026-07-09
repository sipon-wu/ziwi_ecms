<template>
<div class="page"><h2 class="title">组织架构</h2>
<div class="two-col"><div class="section"><h3>组织树</h3>
  <div v-for="n in flatTree" :key="n.id" class="tnode" :style="{paddingLeft:(n.level*24+12)+'px'}" @click="selOrg(n)">
    <span class="tarrow" v-if="n.children?.length" @click.stop="toggleNode(n.id)">{{n.expanded?'▾':'▸'}}</span>
    <span :class="{tsel:selectedOrg===n.id}">{{n.name}}</span>
  </div>
</div>
<div class="section" v-if="orgData"><h3>碳配额数据</h3>
  <div class="kpi-card"><div class="kl">年度配额</div><div class="kv">{{orgData.total_quota_ton}} t</div></div>
  <div class="kpi-card" style="margin-top:8px"><div class="kl">已使用</div><div class="kv">{{orgData.used_ton}} t</div></div>
</div></div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),tree=ref([]),flatTree=ref([]),selectedOrg=ref(null),orgData=ref(null)
function flatten(nodes){ let r=[]; for(const n of nodes){ r.push({...n,expanded:true}); if(n.expanded!==false&&n.children) r.push(...flatten(n.children)) } return r }
function toggleNode(id){ const f=(nodes)=>{ for(const n of nodes){ if(n.id===id){ n.expanded=!n.expanded; return true } if(n.children&&f(n.children)) return true }; return false }; f(tree.value); flatTree.value=flatten(tree.value) }
async function selOrg(n){ selectedOrg.value=n.id; orgData.value=await store.fetchJSONRaw('/api/organization/carbon?org_id='+n.id) }
onMounted(async()=>{ const d=await store.fetchJSONRaw('/api/organization/tree')||{}; tree.value=d.tree||[]; flatTree.value=flatten(tree.value) })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.two-col{display:grid;grid-template-columns:300px 1fr;gap:12px}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}h3{font-size:14px;color:#555;margin-bottom:12px}.tnode{cursor:pointer;padding:8px 12px;font-size:13px;color:#333;border-radius:4px;transition:background 0.15s}.tnode:hover{background:#f5f7fa}.tsel{color:#0d7377;font-weight:600}.tarrow{display:inline-block;width:16px;color:#999;cursor:pointer}.kpi-card{background:#f5f7fa;padding:14px;border-radius:8px;text-align:center}.kl{font-size:11px;color:#999}.kv{font-size:22px;font-weight:700;color:#333;margin-top:4px}
</style>
