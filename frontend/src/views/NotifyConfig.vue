<template>
<div class="page">
  <h2 class="title">通知配置</h2>
  <p class="subtitle">配置告警通知渠道。当前为配置预览阶段，填写后保存配置，正式发送将在后续版本启用。</p>

  <div class="section">
    <h3 class="sec-title">📧 邮件服务器</h3>
    <div class="form-grid">
      <div class="field"><label>SMTP 服务器</label><input v-model="smtp.host" placeholder="smtp.example.com" /></div>
      <div class="field"><label>端口</label><input v-model="smtp.port" placeholder="465" /></div>
      <div class="field"><label>发件人邮箱</label><input v-model="smtp.from" placeholder="noreply@ziwi.cn" /></div>
      <div class="field"><label>密码/授权码</label><input v-model="smtp.pwd" type="password" placeholder="********" /></div>
    </div>
  </div>

  <div class="section">
    <h3 class="sec-title">💬 企业微信</h3>
    <div class="form-grid">
      <div class="field"><label>Webhook URL</label><input v-model="wecom.webhook" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" /></div>
      <div class="field"><label>@提醒人(手机号)</label><input v-model="wecom.at" placeholder="多个用|分隔" /></div>
    </div>
  </div>

  <div class="section">
    <h3 class="sec-title">🔔 告警升级规则</h3>
    <table>
      <thead><tr><th>级别</th><th>通知方式</th><th>超时升级(分钟)</th><th>升级后通知</th></tr></thead>
      <tbody>
        <tr><td>Warning</td><td><select v-model="rules.warning"><option value="email">邮件</option><option value="wecom">企业微信</option></select></td><td><input v-model="rules.warningTimeout" class="si" /> 分钟</td><td>升级为 Error</td></tr>
        <tr><td>Error</td><td><select v-model="rules.error"><option value="email">邮件</option><option value="wecom">企业微信</option><option value="both">邮件+企业微信</option></select></td><td>—</td><td>直接通知管理员</td></tr>
      </tbody>
    </table>
  </div>

  <div class="actions">
    <button class="btn btn-primary" @click="saveConfig">💾 保存配置</button>
    <span v-if="saved" class="saved-msg">✅ 配置已保存（发送功能将在后续版本启用）</span>
  </div>
</div>
</template>
<script setup>
import { ref, reactive } from 'vue'
const smtp=reactive({host:'',port:'465',from:'',pwd:''})
const wecom=reactive({webhook:'',at:''})
const rules=reactive({warning:'email',warningTimeout:30,error:'both'})
const saved=ref(false)

function saveConfig(){
  const cfg={smtp,wecom,rules}
  localStorage.setItem('notify_config',JSON.stringify(cfg))
  saved.value=true
  setTimeout(()=>saved.value=false,3000)
}
</script>
<style scoped>
.page{display:flex;flex-direction:column;gap:16px}
.title{font-size:18px;color:#333;margin-bottom:0}
.subtitle{font-size:12px;color:#888;margin:0}
.section{background:#fff;border:1px solid #e8eaed;border-radius:10px;padding:20px}
.sec-title{font-size:15px;color:#333;margin:0 0 12px}
.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.field label{display:block;font-size:12px;color:#555;margin-bottom:4px}
.field input,.field select{width:100%;padding:8px 10px;border:1px solid #d0d5dd;border-radius:6px;font-size:13px;box-sizing:border-box}
.si{width:60px;padding:6px 8px;border:1px solid #d0d5dd;border-radius:6px;font-size:13px;text-align:center}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 14px;border-bottom:1px solid #f0f0f0;text-align:left}
th{background:#f5f7fa;color:#666;font-weight:500}
.actions{display:flex;align-items:center;gap:12px}
.btn{padding:8px 20px;border-radius:6px;font-size:13px;cursor:pointer}
.btn-primary{background:#0d7377;color:#fff;border:none}
.saved-msg{font-size:12px;color:#2e7d32}
</style>
