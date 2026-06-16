<template>
  <div class="review-analysis">
    <div class="section-header">
      <h2 class="section-title">💬 差评分析</h2>
    </div>

    <div class="analysis-grid">
      <div class="analysis-card">
        <h3 class="card-title">高频关键词</h3>
        <div class="keywords-list">
          <div
            v-for="(item, index) in highFreqKeywords"
            :key="index"
            class="keyword-item"
          >
            <span class="keyword">{{ item[0] }}</span>
            <span class="count">{{ item[1] }}次</span>
            <div class="keyword-bar" :style="{ width: (item[1] / maxCount * 100) + '%' }"></div>
          </div>
        </div>
      </div>

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
              <span class="complaint-count">{{ complaint.count }}次 ({{ complaint.percentage }}%)</span>
            </div>
          </div>
        </div>
      </div>

      <div class="analysis-card">
        <h3 class="card-title">情感分布</h3>
        <div class="sentiment-chart" ref="sentimentChart"></div>
      </div>

      <div class="analysis-card">
        <h3 class="card-title">评分分布</h3>
        <div class="rating-chart" ref="ratingChart"></div>
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
      sentimentChart: null,
      ratingChart: null
    }
  },
  computed: {
    maxCount() {
      if (this.highFreqKeywords.length === 0) return 1
      return Math.max(...this.highFreqKeywords.map(item => item[1]))
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
          this.highFreqKeywords = data.highFreqKeywords
          this.topComplaints = data.topComplaints
          this.sentimentDistribution = data.sentimentDistribution
          this.ratingDistribution = data.ratingDistribution
        }
      } catch (error) {
        console.error('加载差评分析失败:', error)
      }
    },
    initCharts() {
      this.initSentimentChart()
      this.initRatingChart()
    },
    initSentimentChart() {
      const chart = echarts.init(this.$refs.sentimentChart)
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
          itemStyle: {
            borderRadius: 10,
            borderColor: '#1a2332',
            borderWidth: 2
          },
          label: {
            show: true,
            color: '#e2e8f0'
          },
          data: [
            { value: this.sentimentDistribution.negative || 0, name: '负面', itemStyle: { color: '#ef4444' } },
            { value: this.sentimentDistribution.neutral || 0, name: '中性', itemStyle: { color: '#f59e0b' } }
          ]
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
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: '#a855f7' },
                { offset: 1, color: '#ec4899' }
              ]
            },
            borderRadius: [4, 4, 0, 0]
          }
        }]
      }
      chart.setOption(option)
      this.ratingChart = chart
    }
  },
  beforeUnmount() {
    if (this.sentimentChart) {
      this.sentimentChart.dispose()
    }
    if (this.ratingChart) {
      this.ratingChart.dispose()
    }
  }
}
</script>

<style scoped>
.review-analysis {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.section-header {
  margin-bottom: 1.5rem;
}

.section-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  color: var(--accent-purple);
}

.analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.analysis-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.5rem;
}

.card-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  color: var(--accent-cyan);
  margin-bottom: 1rem;
}

.keywords-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.keyword-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
}

.keyword {
  min-width: 80px;
  color: var(--text-primary);
}

.count {
  min-width: 50px;
  color: var(--accent-cyan);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
}

.keyword-bar {
  height: 8px;
  background: var(--gradient-primary);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.complaints-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.complaint-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.complaint-rank {
  width: 30px;
  height: 30px;
  background: var(--gradient-secondary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
}

.complaint-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.complaint-keyword {
  color: var(--text-primary);
}

.complaint-count {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.sentiment-chart,
.rating-chart {
  height: 200px;
}

@media (max-width: 768px) {
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
