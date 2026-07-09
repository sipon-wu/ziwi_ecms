<template>
<div class="page">
  <h2 class="title">数据字典管理</h2>
  <div class="tabs">
    <span v-for="tab in dictTabs" :key="tab.code" class="tab" :class="{active:activeTab===tab.code}" @click="switchTab(tab)">{{tab.name}}</span>
  </div>
  <div class="section">
    <div class="toolbar"><span class="dict-desc">{{activeDesc}}</span><button class="btn btn-primary btn-sm" @click="showAdd=true">+ 新增</button></div>
    <table v-if="items.length">
      <thead><tr><th>键</th><th>值</th><th>排序</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="item in items" :key="item.id">
          <td>{{item.item_key}}</td><td>{{item.item_value}}</td><td>{{item.sort_order||0}}</td>
          <td><button class="btn-link" @click="delItem(item.id)">删除</button></td>
        </tr>
      </tbody>
    </table>
    <div v-else class="empty">暂无数据，请先新增</div>
  </div>
  <div v-if="showAdd" class="modal-overlay" @click.self="showAdd=false">
    <div class="modal"><h3>新增字典条目</h3>
      <div class="field"><label>键</label><input v-model="newKey" placeholder="英文代码" /></div>
      <div class="field"><label>值</label><input v-model="newVal" placeholder="中文名称" /></div>
      <div class="field"><label>排序</label><input v-model.number="newSort" type="number" placeholder="0" /></div>
      <div class="modal-actions"><button class="btn btn-outline" @click="showAdd=false">取消</button><button class="btn btn-primary" @click="addItem">保存</button></div>
    </div>
  </div>
</div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'
const store = useEnergyStore()
const dictTabs = ref([
  {code:'DEVICE_TYPE',name:'设备类型',desc:'管理设备分类'},
  {code:'ENERGY_TYPE',name:'能源类型',desc:'管理能源种类'},
  {code:'EMISSION_SOURCE',name:'排放源',desc:'管理碳排放源类别'},
  {code:'PRODUCT_MODEL',name:'产品型号',desc:'管理产品目录'},
])
const activeTab=ref('DEVICE_TYPE'),activeDesc=ref(''),items=ref([]),showAdd=ref(false)
const newKey=ref(''),newVal=ref(''),newSort=ref(0)

function switchTab(t){ activeTab.value=t.code; activeDesc.value=t.desc; loadItems() }

async function loadItems(){
  try{const d=await store.fetchJSONRaw(`/api/dict/items?dict_code=${activeTab.value}`);items.value=d?.items||[]}catch{items.value=[]}
}
async function addItem(){
  try{
    const resp=await fetch('/api/dict/types',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dict_code:activeTab.value,dict_name:activeDesc.value})})
    const td=await resp.json()
    const typeId=td.data?.id||1
    await fetch('/api/dict/items',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({dict_type_id:typeId,item_key:newKey.value,item_value:newVal.value,sort_order:newSort.value})})
    showAdd.value=false;newKey.value='';newVal.value='';newSort.value=0;loadItems()
  }catch(e){alert('操作失败：'+e.message)}
}
async function delItem(id){
  if(!confirm('确认删除？'))return
  try{await fetch(`/api/dict/items/${id}`,{method:'DELETE'});loadItems()}catch{}
}
onMounted(()=>{activeDesc.value=dictTabs.value[0].desc;loadItems()})
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}
.title{font-size:18px;color:#333}
.tabs{display:flex;gap:4px;background:#f5f7fa;padding:4px;border-radius:8px;width:fit-content}
.tab{padding:8px 18px;font-size:13px;cursor:pointer;border-radius:6px;color:#666;transition:all.15s}
.tab.active{background:#fff;color:#0d7377;font-weight:500;box-shadow:0 1px 3px rgba(0,0,0,.08)}
.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}
.toolbar{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px}
.dict-desc{font-size:12px;color:#888}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0;text-align:left}
th{background:#f5f7fa;color:#666;font-weight:500}
.empty{text-align:center;padding:40px;color:#aaa;font-size:13px}
.btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer}.btn-sm{padding:4px 10px;font-size:11px}
.btn-primary{background:#0d7377;color:#fff}.btn-outline{background:#fff;color:#0d7377;border:1px solid #0d7377}
.btn-link{background:none;border:none;color:#0d7377;cursor:pointer;font-size:12px;text-decoration:underline}
.field{margin-bottom:12px}.field label{display:block;font-size:12px;color:#555;margin-bottom:4px}
.field input{width:100%;padding:8px 10px;border:1px solid #d0d5dd;border-radius:6px;font-size:13px;box-sizing:border-box}
.modal-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;z-index:100}
.modal{background:#fff;border-radius:12px;padding:28px;width:380px;max-width:90vw}
.modal h3{margin:0 0 16px;font-size:16px}
.modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:16px}
</style>
