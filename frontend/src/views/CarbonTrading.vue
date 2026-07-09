<template>
<div class="page"><h2 class="title">碳交易管理</h2>
<div v-if="data" class="kpi-row"><div class="kpi-card"><div class="kl">当前碳价</div><div class="kv">{{data.current_price}} 元/吨</div></div><div class="kpi-card"><div class="kl">今日交易量</div><div class="kv">{{data.volume_today?.toLocaleString()}} 吨</div></div></div>
<div v-if="data" class="section"><h3>碳价走势</h3><div ref="chart" style="height:320px"></div></div>
<div v-if="data" class="section"><h3>交易模拟</h3><div class="trade-row"><select v-model="action" class="sel"><option>买入</option><option>卖出</option></select><input type="number" v-model="qty" placeholder="数量(吨)" class="inp" /><button class="btn btn-primary" @click="trade">提交交易</button></div></div>
<div v-if="!data" class="loading">加载中...</div></div></template>
<script setup>
import { ref,onMounted,nextTick } from 'vue';import * as echarts from 'echarts';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),data=ref(null),chart=ref(null),action=ref('买入'),qty=ref(100)
function trade(){ alert(action.value+' '+qty.value+'吨 CO2 配额\n交易模拟已提交！') }
onMounted(async()=>{ data.value=await store.fetchJSONRaw('/api/carbon_asset/trading'); nextTick(()=>{ if(data.value?.trend){ const ch=echarts.init(chart.value); ch.setOption({tooltip:{trigger:'axis'},xAxis:{type:'category',data:data.value.trend.map(x=>x.date)},yAxis:{type:'value',name:'元/吨'},series:[{type:'line',data:data.value.trend.map(x=>x.price),smooth:true,lineStyle:{color:'#0d7377',width:2},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(13,115,119,0.15)'},{offset:1,color:'rgba(13,115,119,0)'}])}}]}) } }) })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.kpi-row{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}.kpi-card{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:18px;text-align:center}.kl{font-size:12px;color:#999}.kv{font-size:28px;font-weight:700;color:#333;margin-top:6px}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}h3{font-size:14px;color:#555;margin-bottom:12px}.trade-row{display:flex;gap:12px;align-items:center}.sel,.inp{padding:8px 12px;border:1px solid #ddd;border-radius:6px;font-size:13px}.btn{padding:8px 20px;border:none;border-radius:6px;cursor:pointer}.btn-primary{background:#0d7377;color:#fff}.loading{text-align:center;padding:60px;color:#aaa}
</style>
