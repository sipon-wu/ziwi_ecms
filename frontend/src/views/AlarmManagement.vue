<template>
  <div class="page">
    <h2 class="page-title">报警管理</h2>

    <!-- Tabs -->
    <div class="tabs">
      <button :class="['tab-btn', { active: activeTab === 'active' }]" @click="switchTab('active')">实时报警</button>
      <button :class="['tab-btn', { active: activeTab === 'history' }]" @click="switchTab('history')">历史报警</button>
      <button :class="['tab-btn', { active: activeTab === 'rules' }]" @click="switchTab('rules')">报警规则</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 实时/历史报警表格 -->
    <div class="section" v-if="activeTab !== 'rules' && !loading">
      <table v-if="alarms.length">
        <thead>
          <tr>
            <th>时间</th>
            <th>设备</th>
            <th>仪表</th>
            <th>报警等级</th>
            <th>报警信息</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in alarms" :key="a.id">
            <td>{{ a.created_at }}</td>
            <td>{{ a.device_group }}</td>
            <td>{{ a.meter_name }}</td>
            <td>
              <span class="level-badge" :class="a.alarm_level === 'error' ? 'level-danger' : 'level-warning'">
                {{ a.alarm_level === 'error' ? '严重' : a.alarm_level === 'info' ? '提示' : '警告' }}
              </span>
            </td>
            <td>{{ a.alarm_msg }}</td>
            <td>
              <span class="status-badge" :class="a.status === 'active' ? 'status-active' : 'status-resolved'">
                {{ a.status === 'active' ? '未处理' : a.status === 'pending' ? '待确认' : '已处理' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">暂无报警数据</div>
    </div>

    <!-- 报警规则 Tab -->
    <div class="section" v-if="activeTab === 'rules' && !loading">
      <div class="section-header">
        <h3>报警规则</h3>
        <button class="btn btn-primary" @click="showAddRule = true">添加规则</button>
      </div>
      <table v-if="rules.length">
        <thead>
          <tr>
            <th>规则名称</th>
            <th>设备/仪表</th>
            <th>指标</th>
            <th>条件</th>
            <th>阈值</th>
            <th>等级</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id">
            <td>{{ r.message }}</td>
            <td>{{ r.device_group }}</td>
            <td>{{ r.metric }}</td>
            <td>{{ r.operator === 'gt' ? '大于' : r.operator === 'lt' ? '小于' : r.operator }}</td>
            <td>{{ r.threshold }}</td>
            <td>
              <span class="level-badge" :class="r.level === 'error' ? 'level-danger' : 'level-warning'">
                {{ r.level === 'error' ? '严重' : '警告' }}
              </span>
            </td>
            <td>
              <span class="status-badge" :class="r.enabled ? 'status-active' : 'status-resolved'">
                {{ r.enabled ? '启用' : '停用' }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">暂无报警规则</div>
    </div>

    <!-- 添加规则弹窗 -->
    <div class="modal-overlay" v-if="showAddRule" @click.self="showAddRule = false">
      <div class="modal">
        <h3>添加报警规则</h3>
        <form @submit.prevent="submitRule">
          <div class="form-group">
            <label>规则名称</label>
            <input v-model="newRule.name" type="text" required />
          </div>
          <div class="form-group">
            <label>设备/仪表</label>
            <input v-model="newRule.device_name" type="text" required />
          </div>
          <div class="form-group">
            <label>指标</label>
            <input v-model="newRule.metric" type="text" required />
          </div>
          <div class="form-group">
            <label>条件</label>
            <select v-model="newRule.condition">
              <option value=">">大于</option>
              <option value="<">小于</option>
              <option value=">=">大于等于</option>
              <option value="<=">小于等于</option>
              <option value="==">等于</option>
            </select>
          </div>
          <div class="form-group">
            <label>阈值</label>
            <input v-model.number="newRule.threshold" type="number" step="0.01" required />
          </div>
          <div class="form-group">
            <label>报警等级</label>
            <select v-model="newRule.level">
              <option value="warning">警告</option>
              <option value="danger">严重</option>
            </select>
          </div>
          <div class="modal-btns">
            <button type="button" class="btn btn-cancel" @click="showAddRule = false">取消</button>
            <button type="submit" class="btn btn-primary">确认添加</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useEnergyStore } from '../store/energy'

const store = useEnergyStore()
const loading = ref(true)
const activeTab = ref('active')
const alarms = ref([])
const rules = ref([])
const showAddRule = ref(false)
const newRule = ref({
  name: '',
  device_name: '',
  metric: '',
  condition: '>',
  threshold: 0,
  level: 'warning'
})

async function switchTab(tab) {
  activeTab.value = tab
  loading.value = true
  try {
    if (tab === 'active') {
      const resp = await store.fetchJSONRaw('/api/monitoring/alarms?status=active')
      alarms.value = resp?.items || resp || []
    } else if (tab === 'history') {
      const resp = await store.fetchJSONRaw('/api/monitoring/alarms?status=all')
      alarms.value = resp?.items || resp || []
    } else if (tab === 'rules') {
      const resp = await store.fetchJSONRaw('/api/monitoring/alarm_rules')
      rules.value = resp?.items || resp?.rules || resp || []
    }
  } finally {
    loading.value = false
  }
}

function submitRule() {
  rules.value.unshift({ ...newRule.value, id: Date.now(), status: true })
  showAddRule.value = false
  newRule.value = { name: '', device_name: '', metric: '', condition: '>', threshold: 0, level: 'warning' }
}

onMounted(() => { switchTab('active') })
</script>

<style scoped>
.page { display:flex; flex-direction:column; gap:16px }
.page-title { font-size:20px; color:#333; margin:0 }
.loading { text-align:center; padding:60px; color:#aaa; font-size:14px }

.tabs { display:flex; gap:8px }
.tab-btn { padding:8px 20px; border:1px solid #d9d9d9; border-radius:6px; background:#fff; color:#666; cursor:pointer; font-size:13px; transition:all 0.2s }
.tab-btn.active { background:#0d7377; color:#fff; border-color:#0d7377 }
.tab-btn:hover:not(.active) { border-color:#0d7377; color:#0d7377 }

.section { background:#fff; border:1px solid #e8eaed; border-radius:10px; padding:20px; overflow-x:auto }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px }
.section-header h3 { font-size:15px; color:#333; margin:0 }

table { width:100%; border-collapse:collapse; font-size:13px }
th, td { padding:10px 12px; text-align:left; border-bottom:1px solid #f0f0f0 }
th { background:#fafafa; color:#666; font-weight:600; white-space:nowrap }
td { color:#333 }

.level-badge { display:inline-block; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600 }
.level-danger { background:#fff1f0; color:#e74c3c }
.level-warning { background:#fff7e6; color:#f39c12 }

.status-badge { display:inline-block; padding:3px 10px; border-radius:10px; font-size:12px; font-weight:600 }
.status-active { background:#fff1f0; color:#e74c3c }
.status-resolved { background:#e6f7ec; color:#00a854 }

.empty { text-align:center; padding:40px; color:#aaa; font-size:13px }

.btn { padding:8px 18px; border:none; border-radius:6px; cursor:pointer; font-size:13px }
.btn-primary { background:#0d7377; color:#fff }
.btn-primary:hover { opacity:0.85 }
.btn-cancel { background:#f0f0f0; color:#666 }

.modal-overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.4); display:flex; align-items:center; justify-content:center; z-index:1000 }
.modal { background:#fff; border-radius:12px; padding:24px; width:460px; max-height:80vh; overflow-y:auto }
.modal h3 { font-size:17px; margin:0 0 18px; color:#333 }

.form-group { margin-bottom:14px }
.form-group label { display:block; font-size:13px; color:#666; margin-bottom:4px }
.form-group input, .form-group select { width:100%; padding:8px 12px; border:1px solid #d9d9d9; border-radius:6px; font-size:13px; box-sizing:border-box }
.form-group input:focus, .form-group select:focus { outline:none; border-color:#0d7377 }

.modal-btns { display:flex; gap:10px; justify-content:flex-end; margin-top:20px }
</style>
