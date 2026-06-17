<template>
  <div class="review-analysis">
    <div class="section-header">
      <h2 class="section-title">💬 差评分析</h2>
    </div>

    <div class="analysis-grid">
      <!-- 卡片1: 高频关键词 -->
      <div class="analysis-card">
        <h3 class="card-title">高频关键词 (TextRank)</h3>
        <div class="keywords-list">
          <div
            v-for="(item, index) in highFreqKeywords"
            :key="index"
            class="keyword-item"
          >
            <span class="keyword">{{ item.word || item[0] }}</span>
            <span class="count">{{ item.count || item.score || item[1] || 0 }}次</span>
            <div class="keyword-bar" :style="{ width: getKeywordWidth(item.count || item.score || item[1] || 0) + '%' }"></div>
          </div>
        </div>
      </div>

      <!-- 卡片2: 用户痛点 TOP5 -->
      <div class="analysis-card">
        <h3 class="card-title">用户痛点 TOP5</h3>
        <div class="complaints-list">
          <div
            v-for="(complaint, index) in topComplaints"
            :key="index"
            class="complaint-item"
          >
            <div class="complaint-rank">{{ index + 1 }}</div>
            <div class="complaint-info">
              <span class="complaint-keyword">{{ complaint.keyword }}</span>
              <span class="complaint-count">{{ typeof complaint.count === 'number' ? complaint.count + '次' : complaint.count?.toFixed(4) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 卡片3: 情感分布 -->
      <div class="analysis-card">
        <h3 class="card-title">情感分布</h3>
        <div class="sentiment-chart" ref="sentimentChart"></div>
      </div>

      <!-- 卡片4: 评分分布 -->
      <div class="analysis-card">
        <h3 class="card-title">评分分布</h3>
        <div class="rating-chart" ref="ratingChart"></div>
      </div>

      <!-- 卡片5: LDA投诉主题 -->
      <div class="analysis-card">
        <h3 class="card-title">投诉主题 (LDA)</h3>
        <div class="topic-chart" ref="topicChart"></div>
      </div>

      <!-- 卡片6: K-Means差评聚类 -->
      <div class="analysis-card">
        <h3 class="card-title">差评聚类 (K-Means)</h3>
        <div class="clusters-list">
          <div
            v-for="(count, clusterId) in clusterLabels"
            :key="clusterId"
            class="cluster-item"
          >
            <div class="cluster-header">
              <span class="cluster-badge">簇 {{ clusterId }}</span>
              <span class="cluster-count">{{ count }} 条</span>
            </div>
            <div class="cluster-keywords">
              <span
                v-for="(kw, ki) in (clusterKeywords[clusterId] || [])"
                :key="ki"
                class="cluster-tag"
              >{{ kw }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getReviewAnalysis } from '../api'

export default {
  name: 'ReviewAnalysis',
  data() {
    return {
      highFreqKeywords: [],
      topComplaints: [],
      sentimentDistribution: {},
      ratingDistribution: {},
      topicDistribution: [],
      topicKeywords: [],
      clusterLabels: {},
      clusterKeywords: {},
      sentimentChart: null,
      ratingChart: null,
      topicChart: null
    }
  },
  async mounted() {
    await this.loadAnalysis()
    this.initCharts()
  },
  methods: {
    async loadAnalysis() {
      try {
        const res = await getReviewAnalysis()
        if (res.data.code === 200) {
          const data = res.data.data
          this.highFreqKeywords = data.highFreqKeywords || []
          this.topComplaints = data.topComplaints || []
          this.sentimentDistribution = data.sentimentDistribution || {}
          this.ratingDistribution = data.ratingDistribution || {}
          this.topicDistribution = data.topicDistribution || []
          this.topicKeywords = data.topicKeywords || []
          this.clusterLabels = data.clusterLabels || {}
          this.clusterKeywords = data.clusterKeywords || {}
        }
      } catch (error) {
        console.error('加载差评分析失败:', error)
      }
    },
    getKeywordWidth(score) {
      if (!this.highFreqKeywords.length) return 0
      const maxScore = Math.max(...this.highFreqKeywords.map(item => {
        return (item.count || item.score || item[1] || 0)
      }))
      return maxScore > 0 ? (score / maxScore) * 100 : 0
    },
    initCharts() {
      this.initSentimentChart()
      this.initRatingChart()
      this.initTopicChart()
    },
    initSentimentChart() {
      const chart = echarts.init(this.$refs.sentimentChart)
      const data = [
        { value: this.sentimentDistribution.negative || 0, name: '负面', itemStyle: { color: '#ef4444' } },
        { value: this.sentimentDistribution.neutral || 0, name: '中性', itemStyle: { color: '#f59e0b' } },
        { value: this.sentimentDistribution.positive || 0, name: '正面', itemStyle: { color: '#10b981' } }
      ].filter(d => d.value > 0)
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: '#a855f7',
          textStyle: { color: '#e2e8f0' }
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          itemStyle: { borderRadius: 10, borderColor: '#1a2332', borderWidth: 2 },
          label: { show: true, color: '#e2e8f0' },
          data
        }]
      }
      chart.setOption(option)
      this.sentimentChart = chart
    },
    initRatingChart() {
      const chart = echarts.init(this.$refs.ratingChart)
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: '#a855f7',
          textStyle: { color: '#e2e8f0' }
        },
        xAxis: {
          type: 'category',
          data: Object.keys(this.ratingDistribution).map(r => r + '星'),
          axisLine: { lineStyle: { color: '#374151' } },
          axisLabel: { color: '#94a3b8' }
        },
        yAxis: {
          type: 'value',
          axisLine: { lineStyle: { color: '#374151' } },
          axisLabel: { color: '#94a3b8' },
          splitLine: { lineStyle: { color: 'rgba(55, 65, 81, 0.5)' } }
        },
        series: [{
          type: 'bar',
          data: Object.values(this.ratingDistribution),
          itemStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: '#a855f7' }, { offset: 1, color: '#ec4899' }]
            },
            borderRadius: [4, 4, 0, 0]
          }
        }]
      }
      chart.setOption(option)
      this.ratingChart = chart
    },
    initTopicChart() {
      if (!this.topicDistribution.length || !this.topicKeywords.length) return
      const chart = echarts.init(this.$refs.topicChart)
      const topicKw = this.topicKeywords
      const topicLabels = this.topicDistribution.map((_, i) => {
        const kws = (topicKw[i] || []).slice(0, 3).join('、')
        return `主题${i + 1}: ${kws}`
      })
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: '#00f5ff',
          textStyle: { color: '#e2e8f0' },
          formatter(params) {
            const p = params[0]
            const kws = topicKw[p.dataIndex] ? topicKw[p.dataIndex].slice(0, 5).join('、') : ''
            return `<b>${p.name}</b><br/>权重: ${(p.value * 100).toFixed(1)}%<br/>关键词: ${kws}`
          }
        },
        grid: { top: 10, right: 30, bottom: 30, left: 180 },
        xAxis: {
          type: 'value',
          max: 1,
          axisLine: { lineStyle: { color: '#374151' } },
          axisLabel: { color: '#94a3b8', formatter: v => (v * 100).toFixed(0) + '%' },
          splitLine: { lineStyle: { color: 'rgba(55, 65, 81, 0.3)' } }
        },
        yAxis: {
          type: 'category',
          data: topicLabels,
          axisLine: { lineStyle: { color: '#374151' } },
          axisLabel: { color: '#94a3b8', fontSize: 11, width: 170, overflow: 'truncate' }
        },
        series: [{
          type: 'bar',
          data: this.topicDistribution,
          barWidth: 20,
          itemStyle: {
            color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [{ offset: 0, color: '#0ea5e9' }, { offset: 1, color: '#00f5ff' }]
            },
            borderRadius: [0, 4, 4, 0]
          },
          label: { show: true, position: 'right', color: '#e2e8f0', formatter: p => (p.value * 100).toFixed(1) + '%' }
        }]
      }
      chart.setOption(option)
      this.topicChart = chart
    }
  },
  beforeUnmount() {
    if (this.sentimentChart) this.sentimentChart.dispose()
    if (this.ratingChart) this.ratingChart.dispose()
    if (this.topicChart) this.topicChart.dispose()
  }
}
</script>

<style scoped>
.review-analysis { animation: slideIn 0.3s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
.section-header { margin-bottom: 1.5rem; }
.section-title { font-family: 'Orbitron', sans-serif; font-size: 1.5rem; color: var(--accent-purple); }
.analysis-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
.analysis-card { background: var(--bg-secondary); border: var(--border-glow); border-radius: 12px; padding: 1.5rem; }
.card-title { font-family: 'Orbitron', sans-serif; font-size: 1rem; color: var(--accent-cyan); margin-bottom: 1rem; }

/* 关键词 */
.keywords-list { display: flex; flex-direction: column; gap: 0.75rem; }
.keyword-item { display: flex; align-items: center; gap: 1rem; position: relative; }
.keyword { min-width: 80px; color: var(--text-primary); }
.count { min-width: 60px; color: var(--accent-cyan); font-family: 'Orbitron', sans-serif; font-size: 0.8rem; }
.keyword-bar { height: 8px; background: var(--gradient-primary); border-radius: 4px; transition: width 0.5s ease; }

/* 痛点 */
.complaints-list { display: flex; flex-direction: column; gap: 1rem; }
.complaint-item { display: flex; align-items: center; gap: 1rem; }
.complaint-rank { width: 30px; height: 30px; background: var(--gradient-secondary); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-family: 'Orbitron', sans-serif; font-weight: 700; }
.complaint-info { flex: 1; display: flex; justify-content: space-between; align-items: center; }
.complaint-keyword { color: var(--text-primary); }
.complaint-count { color: var(--text-secondary); font-size: 0.9rem; }

/* 图表 */
.sentiment-chart, .rating-chart, .topic-chart { height: 220px; }

/* 聚类 */
.clusters-list { display: flex; flex-direction: column; gap: 1rem; }
.cluster-item { background: rgba(255,255,255,0.03); border-radius: 8px; padding: 0.75rem 1rem; }
.cluster-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.cluster-badge { background: rgba(168, 85, 247, 0.2); color: var(--accent-purple); padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.8rem; font-family: 'Orbitron', sans-serif; }
.cluster-count { color: var(--text-secondary); font-size: 0.85rem; }
.cluster-keywords { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.cluster-tag { background: rgba(0, 245, 255, 0.1); color: var(--accent-cyan); padding: 0.15rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }

@media (max-width: 768px) { .analysis-grid { grid-template-columns: 1fr; } }
</style>
