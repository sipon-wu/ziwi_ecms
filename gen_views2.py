import os
base = "D:/工业元/数云_新质力/ziwi_project_dna/frontend/src/views"

def write_view(fname, template, script, style):
    content = f"<template>{template}</template>\n<script setup>{script}</script>\n<style scoped>{style}</style>"
    path = os.path.join(base, fname)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"  OK: {fname}")
    return path

# CarbonAccounting.vue
write_view("CarbonAccounting.vue", '''
<div class="page"><h2 class="title">碳排放核算</h2>
<div class="toolbar"><label>起始:</label><input type="date" v-model="s" /><label>结束:</label><input type="date" v-model="e" /><button class="btn btn-primary" @click="load">查询</button><button class="btn" @click="genReport" style="margin-left:auto">生成报告</button></div>
<div v-if="data" class="kpi-row"><div class="kpi-card"><div class="kl">总排放</div><div class="kv">{{data.total_co2_kg?.toLocaleString()}} kg</div></div><div class="kpi-card"><div class="kl">折合吨数</div><div class="kv">{{data.total_co2_ton}} tCO2</div></div><div class="kpi-card"><div class="kl">核算周期</div><div class="kv" style="font-size:14px">{{data.period}}</div></div></div>
<div v-if="data" class="two-col"><div class="section"><h3>排放来源</h3><div ref="pie" style="height:320px"></div></div><div class="section"><h3>明细</h3><table><thead><tr><th>来源</th><th>耗电</th><th>CO2(kg)</th><th>占比</th></tr></thead><tbody><tr v-for="x in data.source_breakdown" :key="x.source"><td>{{x.source}}</td><td>{{x.kwh}}</td><td>{{x.co2_kg}}</td><td>{{x.ratio_pct}}%</td></tr></tbody></table></div></div>
<div v-else class="loading">加载中...</div></div>''',
'''import { ref,onMounted,nextTick } from 'vue';import * as e from 'echarts';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),s=ref('2026-05-01'),e=ref('2026-05-07'),data=ref(null),pie=ref(null)
function genReport(){ alert('碳排放报告已生成！') }
async function load(){ data.value=await store.fetchJSONRaw('/api/carbon/accounting?start_date='+s.value+'&end_date='+e.value+'&scope=1,2'); nextTick(()=>{ if(data.value?.source_breakdown){ const ch=e.init(pie.value); ch.setOption({tooltip:{trigger:'item'},series:[{type:'pie',radius:'55%',data:data.value.source_breakdown.map(x=>({name:x.source,value:x.co2_kg})),label:{formatter:'{b}: {d}%'}}]}) } }) }
onMounted(load)''',
'''.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.toolbar{display:flex;align-items:center;gap:10px;background:#fff;padding:12px 16px;border-radius:10px;border:1px solid #e8eaed}.toolbar input{padding:6px 10px;border:1px solid #ddd;border-radius:6px}.kpi-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.kpi-card{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:18px;text-align:center}.kl{font-size:12px;color:#999}.kv{font-size:24px;font-weight:700;color:#333;margin-top:6px}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}h3{font-size:14px;color:#555;margin-bottom:12px}.two-col{display:grid;grid-template-columns:1fr 1fr;gap:12px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{padding:8px 10px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer}.btn-primary{background:#0d7377;color:#fff}.loading{text-align:center;padding:60px;color:#aaa}@media(max-width:1000px){.two-col{grid-template-columns:1fr}}''')

print("done")
