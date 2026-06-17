import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 10000
})

// 监控大屏API
export const getDashboardStats = () => {
  return api.get('/dashboard/stats')
}

export const getDashboardTrend = () => {
  return api.get('/dashboard/trend')
}

// 爆款分析API
export const getHotProducts = (params = {}) => {
  return api.get('/products/hot', { params })
}

// 搜索商品API
export const searchProducts = (query, limit = 10) => {
  return api.get('/products/search', { params: { query, limit } })
}

// 卖点推荐API
export const getSellingPoints = (params = {}) => {
  return api.get('/products/selling-points', { params })
}

// 差评分析API
export const getReviewAnalysis = (params = {}) => {
  return api.get('/reviews/analysis', { params })
}

// AI文案生成API
export const generateCopywriting = (data) => {
  return api.post('/copywriting/generate', data)
}

export default api
