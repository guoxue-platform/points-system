import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({ baseURL: BASE_URL })

// 查询当周看板
export function getWeeklyLeaderboard(week) {
  const params = week ? { week } : {}
  return api.get('/api/v1/points/weekly', { params })
}

// 查询积分明细
export function getRecords({ target, week, page = 1, pageSize = 20 } = {}) {
  return api.get('/api/v1/points/records', {
    params: { target, week, page, page_size: pageSize }
  })
}

// 查询历史归档
export function getHistory(week) {
  const params = week ? { week } : {}
  return api.get('/api/v1/points/history', { params })
}

// 录入积分
export function submitRecord({ proposer, target, reason, points, createdBy }, branch = 'dev') {
  return api.post('/api/v1/points/record',
    { proposer, target, reason, points, created_by: createdBy },
    { headers: { 'X-Agent-Branch': branch } }
  )
}

export default api
