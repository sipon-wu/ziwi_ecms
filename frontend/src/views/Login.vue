<template>
<div class="login-page">
  <div class="login-card">
    <div class="login-header">
      <img :src="logoUrl" class="login-logo" alt="logo" />
      <h1>知微能碳管理系统</h1>
      <p class="sub">访客演示系统 / 管理员请切换账号</p>
    </div>
    <div class="login-form">
      <div class="field">
        <label>用户名</label>
        <input v-model="username" placeholder="请输入用户名" @keyup.enter="login" />
      </div>
      <div class="field">
        <label>密码</label>
        <input v-model="password" type="password" placeholder="请输入密码" @keyup.enter="login" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="login-btn" @click="login" :disabled="loading">
        {{ loading ? '登录中...' : '登 录' }}
      </button>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('guest')
const password = ref('123')
const error = ref('')
const loading = ref(false)
const logoUrl = '/demo/ecms/ziwilogo.png'

async function login() {
  if (!username.value || !password.value) { error.value = '请输入用户名和密码'; return }
  loading.value = true; error.value = ''
  try {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: username.value, password: password.value }),
    })
    const d = await resp.json()
    if (d.code === 0) {
      localStorage.setItem('user', JSON.stringify(d.data.user))
      localStorage.setItem('token', d.data.token)
      router.push('/dashboard')
    } else {
      error.value = d.message || '登录失败'
    }
  } catch (e) {
    error.value = '网络错误：' + e.message
  }
  loading.value = false
}
</script>

<style scoped>
.login-page {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0d7377 0%, #0a5c5f 50%, #0a4a4d 100%);
}
.login-card {
  background: #fff; border-radius: 16px; padding: 48px 40px;
  width: 380px; box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}
.login-header { text-align: center; margin-bottom: 32px }
.login-logo { width: 48px; height: 48px; margin-bottom: 12px }
.login-header h1 { font-size: 20px; color: #212529; margin: 0 0 6px }
.sub { font-size: 13px; color: #888; margin: 0 }
.field { margin-bottom: 18px }
.field label { display: block; font-size: 13px; color: #555; margin-bottom: 6px }
.field input {
  width: 100%; padding: 10px 14px; border: 1px solid #d0d5dd; border-radius: 8px;
  font-size: 14px; box-sizing: border-box; outline: none; transition: border 0.2s
}
.field input:focus { border-color: #0d7377 }
.error { color: #dc3545; font-size: 12px; margin: -8px 0 12px }
.login-btn {
  width: 100%; padding: 12px; background: #0d7377; color: #fff; border: none;
  border-radius: 8px; font-size: 15px; cursor: pointer; font-weight: 500
}
.login-btn:hover { background: #0a5c5f }
.login-btn:disabled { opacity: 0.6 }
</style>
