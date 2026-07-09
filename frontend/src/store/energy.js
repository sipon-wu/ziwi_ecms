import { defineStore } from 'pinia'
import { ref } from 'vue'

const API = ''

export const useEnergyStore = defineStore('energy', () => {
  const queryDate = ref('2026-05-06')
  const summary = ref(null)
  const trend = ref(null)
  const ranking = ref(null)
  const realtime = ref(null)
  const alarms = ref(null)
  const currentRoute = ref('/dashboard')

  async function fetchJSON(path) {
    const res = await fetch(`${API}${path}`)
    return (await res.json()).data
  }

  async function initDashboard(date) {
    queryDate.value = date || queryDate.value
    const d = queryDate.value
    const [s, t, rk] = await Promise.all([
      fetchJSON(`/api/dashboard/summary?date=${d}`),
      fetchJSON(`/api/dashboard/trend?date=${d}`),
      fetchJSON(`/api/dashboard/ranking?date=${d}&limit=5`),
    ])
    summary.value = s; trend.value = t; ranking.value = rk
  }

  async function fetchRealtime() { realtime.value = await fetchJSON('/api/monitoring/current') }
  async function fetchAlarms(status = 'active') { alarms.value = await fetchJSON(`/api/monitoring/alarms?status=${status}`) }

  async function fetchJSONRaw(path) {
    const res = await fetch(`${API}${path}`)
    return (await res.json()).data
  }

  return { queryDate, summary, trend, ranking, realtime, alarms, currentRoute,
           initDashboard, fetchRealtime, fetchAlarms, fetchJSONRaw, API }
})
