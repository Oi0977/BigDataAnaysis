<template>
  <div class="review-analysis">
    <div class="section-header">
      <h2 class="section-title">差评分析</h2>
    </div>

    <div class="analysis-grid">
      <!-- 卡片1: 高频关键词 -->
      <div class="analysis-card">
        <h3 class="card-title">高频关键词</h3>
        <div class="keywords-list">
          <div
            v-for="(item, index) in highFreqKeywords.slice(0, 10)"
            :key="index"
            class="keyword-item"
          >
            <span class="keyword-rank">{{ index + 1 }}</span>
            <span class="keyword">{{ item.word || item[0] }}</span>
            <div class="keyword-bar-wrap">
              <div class="keyword-bar" :style="{ width: getKeywordWidth(item.count || item.score || item[1] || 0) + '%' }"></div>
            </div>
            <span class="count">{{ item.count || item.score || item[1] || 0 }}次</span>
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
            <div class="complaint-rank" :class="'rank-' + (index + 1)">{{ index + 1 }}</div>
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
        <div class="chart-wrap" ref="sentimentChart"></div>
      </div>

      <!-- 卡片4: 评分分布 -->
      <div class="analysis-card">
        <h3 class="card-title">评分分布</h3>
        <div class="chart-wrap" ref="ratingChart"></div>
      </div>

      <!-- 卡片5: LDA投诉主题 -->
      <div class="analysis-card">
        <h3 class="card-title">投诉主题 (LDA)</h3>
        <div class="chart-wrap" ref="topicChart"></div>
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
      const maxScore = Math.max(...this.highFreqKeywords.slice(0, 10).map(item => {
        return (item.count || item.score || item[1] || 0)
      }))
      return maxScore > 0 ? (score / maxScore) * 100 : 0
    },
    getTooltip() {
      return {
        backgroundColor: '#fff',
        borderColor: '#E8ECF1',
        borderWidth: 1,
        textStyle: { color: '#1A2138', fontSize: 13 },
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.08)'
      }
    },
    initCharts() {
      this.initSentimentChart()
      this.initRatingChart()
      this.initTopicChart()
    },
    initSentimentChart() {
      const chart = echarts.init(this.$refs.sentimentChart)
      const data = [
        { value: this.sentimentDistribution.negative || 0, name: '负面', itemStyle: { color: '#EF4444' } },
        { value: this.sentimentDistribution.neutral || 0, name: '中性', itemStyle: { color: '#F59E0B' } },
        { value: this.sentimentDistribution.positive || 0, name: '正面', itemStyle: { color: '#22C55E' } }
      ].filter(d => d.value > 0)
      const option = {
        backgroundColor: 'transparent',
        tooltip: { ...this.getTooltip(), trigger: 'item' },
        series: [{
          type: 'pie',
          radius: ['42%', '72%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 3 },
          label: { show: true, color: '#4A5568', fontSize: 12 },
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
        tooltip: { ...this.getTooltip(), trigger: 'axis' },
        grid: { top: 20, right: 20, bottom: 30, left: 40, containLabel: false },
        xAxis: {
          type: 'category',
          data: Object.keys(this.ratingDistribution).map(r => r + '星'),
          axisLine: { lineStyle: { color: '#E8ECF1' } },
          axisLabel: { color: '#8492A6', fontSize: 12 },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          axisLabel: { color: '#8492A6', fontSize: 12 },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } }
        },
        series: [{
          type: 'bar',
          data: Object.values(this.ratingDistribution),
          barWidth: '50%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#4F6EF7' },
              { offset: 1, color: '#7B93FF' }
            ]),
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
          ...this.getTooltip(), trigger: 'axis',
          formatter(params) {
            const p = params[0]
            const kws = topicKw[p.dataIndex] ? topicKw[p.dataIndex].slice(0, 5).join('、') : ''
            return `<b>${p.name}</b><br/>权重: ${(p.value * 100).toFixed(1)}%<br/>关键词: ${kws}`
          }
        },
        grid: { top: 10, right: 30, bottom: 30, left: 180 },
        xAxis: {
          type: 'value', max: 1,
          axisLine: { lineStyle: { color: '#E8ECF1' } },
          axisLabel: { color: '#8492A6', fontSize: 12, formatter: v => (v * 100).toFixed(0) + '%' },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } }
        },
        yAxis: {
          type: 'category',
          data: topicLabels,
          axisLine: { lineStyle: { color: '#E8ECF1' } },
          axisLabel: { color: '#8492A6', fontSize: 11, width: 170, overflow: 'truncate' },
          axisTick: { show: false }
        },
        series: [{
          type: 'bar',
          data: this.topicDistribution,
          barWidth: 18,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#B6C4FF' },
              { offset: 1, color: '#4F6EF7' }
            ]),
            borderRadius: [0, 4, 4, 0]
          },
          label: { show: true, position: 'right', color: '#4A5568', fontSize: 11, fontWeight: 600, formatter: p => (p.value * 100).toFixed(1) + '%' }
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
.review-analysis {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-title);
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.analysis-card {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.card-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

/* Keywords */
.keywords-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.keyword-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.keyword-rank {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--border);
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.7rem;
  font-weight: 700;
  flex-shrink: 0;
}

.keyword-item:nth-child(-n+3) .keyword-rank {
  background: var(--color-primary);
  color: #fff;
}

.keyword {
  min-width: 70px;
  color: var(--text-title);
  font-size: 0.875rem;
  font-weight: 500;
}

.keyword-bar-wrap {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.keyword-bar {
  height: 100%;
  background: var(--color-primary);
  border-radius: 3px;
  transition: width 0.5s ease;
}

.count {
  min-width: 50px;
  color: var(--text-secondary);
  font-family: 'Space Mono', monospace;
  font-size: 0.75rem;
  text-align: right;
}

/* Complaints */
.complaints-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.complaint-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.6rem 0.75rem;
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-light);
}

.complaint-rank {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8rem;
  flex-shrink: 0;
  background: var(--border);
  color: var(--text-secondary);
}

.complaint-rank.rank-1 { background: #FEF2F2; color: #EF4444; }
.complaint-rank.rank-2 { background: #FFF7ED; color: #F97316; }
.complaint-rank.rank-3 { background: #FFFBEB; color: #F59E0B; }

.complaint-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.complaint-keyword {
  color: var(--text-title);
  font-weight: 500;
  font-size: 0.9rem;
}

.complaint-count {
  color: var(--text-secondary);
  font-size: 0.85rem;
  font-family: 'Space Mono', monospace;
}

/* Charts */
.chart-wrap {
  height: 220px;
}

/* Clusters */
.clusters-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.cluster-item {
  background: var(--bg-white);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
}

.cluster-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.cluster-badge {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.cluster-count {
  color: var(--text-secondary);
  font-size: 0.8rem;
  font-family: 'Space Mono', monospace;
}

.cluster-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.cluster-tag {
  background: var(--bg-page);
  color: var(--text-body);
  padding: 0.15rem 0.5rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  border: 1px solid var(--border);
}

@media (max-width: 768px) {
  .analysis-grid { grid-template-columns: 1fr; }
}
</style>
