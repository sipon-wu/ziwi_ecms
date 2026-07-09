<template>
<div class="page"><h2 class="title">用户管理</h2>
<div class="toolbar"><button class="btn btn-primary" @click="showAdd=true">+ 添加用户</button></div>
<div v-if="users.length" class="section"><table><thead><tr><th>ID</th><th>用户名</th><th>角色</th><th>创建时间</th><th>操作</th></tr></thead><tbody><tr v-for="u in users" :key="u.id"><td>{{u.id}}</td><td>{{u.username}}</td><td><span class="badge" :class="u.role==='超级管理员'?'badge-r':'badge-i'">{{u.role}}</span></td><td>{{u.created_at}}</td><td><button class="btn btn-danger btn-sm" @click="del(u)">删除</button></td></tr></tbody></table></div>
<div v-else class="loading">加载中...</div>
<div v-if="showAdd" class="modal"><div class="modal-c"><h3>添加用户</h3><input v-model="newU.username" placeholder="用户名" /><select v-model="newU.role"><option>操作员</option><option>审核员</option></select><div class="modal-btns"><button class="btn btn-primary" @click="add">保存</button><button class="btn" @click="showAdd=false">取消</button></div></div></div></div></template>
<script setup>
import { ref,onMounted } from 'vue';import { useEnergyStore } from '../store/energy'
const store=useEnergyStore(),users=ref([]),showAdd=ref(false),newU=ref({username:'',role:'操作员'})
function add(){ users.value.push({id:Date.now(),...newU.value,created_at:new Date().toISOString().slice(0,10)});showAdd.value=false;newU.value={username:'',role:'操作员'} }
function del(u){ if(confirm('确认删除用户 '+u.username+'?')) users.value=users.value.filter(x=>x.id!==u.id) }
onMounted(async()=>{ const d=await store.fetchJSONRaw('/api/system/users')||{}; users.value=d.users||[] })
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}.title{font-size:18px;color:#333}.toolbar{display:flex;background:#fff;padding:12px 16px;border-radius:10px;border:1px solid #e8eaed}.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px;overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0}th{background:#f5f7fa;color:#666}.badge{padding:2px 8px;border-radius:4px;font-size:11px}.badge-r{background:#ffebee;color:#d32f2f}.badge-i{background:#e3f2fd;color:#1976d2}.btn{padding:6px 16px;border:none;border-radius:6px;cursor:pointer}.btn-sm{padding:4px 10px;font-size:11px}.btn-primary{background:#0d7377;color:#fff}.btn-danger{background:#d32f2f;color:#fff}.modal{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;z-index:1000}.modal-c{background:#fff;padding:24px;border-radius:10px;width:360px;display:flex;flex-direction:column;gap:12px}.modal-c input,.modal-c select{padding:8px;border:1px solid #ddd;border-radius:6px;font-size:13px}.modal-btns{display:flex;gap:8px;justify-content:flex-end}.loading{text-align:center;padding:60px;color:#aaa}
</style>
