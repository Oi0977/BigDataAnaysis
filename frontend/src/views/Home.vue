<template>
  <div class="home">
    <div class="page-header">
      <h1 class="page-title">数据监控大屏</h1>
      <p class="page-subtitle">实时掌握电商数据动态</p>
    </div>

    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
        <div class="stat-glow"></div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <h3 class="chart-title">品类分布</h3>
        <div class="chart-container" ref="categoryChart"></div>
      </div>
      <div class="chart-card">
        <h3 class="chart-title">爆款指数趋势</h3>
        <div class="chart-container" ref="trendChart"></div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getDashboardStats, getDashboardTrend } from '../api'

const COLORS = ['#00f5ff', '#a855f7', '#ec4899', '#10b981', '#f59e0b', '#3b82f6', '#ef4444', '#8b5cf6']

export default {
  name: 'Home',
  data() {
    return {
      stats: [
        { icon: '📦', value: '0', label: '商品总数' },
        { icon: '💬', value: '0', label: '评价总数' },
        { icon: '🔥', value: '0', label: '爆款数量' },
        { icon: '📈', value: '0', label: '品类数量' }
      ],
      categoryData: [],
      trendMonths: [],
      trendData: [],
      categoryChart: null,
      trendChart: null
    }
  },
  async mounted() {
    await this.loadData()
    this.initCharts()
  },
  methods: {
    async loadData() {
      try {
        const [statsRes, trendRes] = await Promise.all([
          getDashboardStats(),
          getDashboardTrend()
        ])

        if (statsRes.data.code === 200) {
          const data = statsRes.data.data
          this.stats[0].value = data.totalProducts
          this.stats[1].value = data.totalReviews
          this.stats[2].value = data.hotProductsCount
          this.stats[3].value = Object.keys(data.categoryStats).length

          // 动态生成饼图数据
          this.categoryData = Object.entries(data.categoryStats).map(([name, info], i) => ({
            value: info.count,
            name: name,
            itemStyle: { color: COLORS[i % COLORS.length] }
          }))
        }

        if (trendRes.data.code === 200) {
          const data = trendRes.data.data
          this.trendMonths = data.months || []
          this.trendData = data.hotScores || []
        }
      } catch (error) {
        console.error('加载数据失败:', error)
      }
    },
    initCharts() {
      this.initCategoryChart()
      this.initTrendChart()
    },
    initCategoryChart() {
      const chart = echarts.init(this.$refs.categoryChart)
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: '#00f5ff',
          textStyle: { color: '#e2e8f0' }
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          itemStyle: {
            borderRadius: 10,
            borderColor: '#1a2332',
            borderWidth: 2
          },
          label: {
            show: true,
            color: '#e2e8f0',
            fontSize: 12
          },
          emphasis: {
            label: {
              show: true,
              fontSize: 14,
              fontWeight: 'bold'
            },
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 245, 255, 0.5)'
            }
          },
          data: this.categoryData.length > 0 ? this.categoryData : [
            { value: 0, name: '暂无数据', itemStyle: { color: '#374151' } }
          ]
        }]
      }
      chart.setOption(option)
      this.categoryChart = chart
    },
    initTrendChart() {
      const chart = echarts.init(this.$refs.trendChart)
      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: '#00f5ff',
          textStyle: { color: '#e2e8f0' }
        },
        xAxis: {
          type: 'category',
          data: this.trendMonths.length > 0 ? this.trendMonths : ['暂无数据'],
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
          data: this.trendData.length > 0 ? this.trendData : [0],
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 10,
          lineStyle: {
            color: '#00f5ff',
            width: 3,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 245, 255, 0.5)'
          },
          itemStyle: {
            color: '#00f5ff',
            borderColor: '#0a0e17',
            borderWidth: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(0, 245, 255, 0.3)' },
                { offset: 1, color: 'rgba(0, 245, 255, 0)' }
              ]
            }
          }
        }]
      }
      chart.setOption(option)
      this.trendChart = chart
    }
  },
  beforeUnmount() {
    if (this.categoryChart) {
      this.categoryChart.dispose()
    }
    if (this.trendChart) {
      this.trendChart.dispose()
    }
  }
}
</script>

<style scoped>
.home {
  animation: fadeIn 0.5s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.page-header {
  margin-bottom: 2rem;
  text-align: center;
}

.page-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-card);
  border: var(--border-glow);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--glow-cyan);
}

.stat-icon {
  font-size: 2.5rem;
  z-index: 1;
}

.stat-info {
  z-index: 1;
}

.stat-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent-cyan);
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stat-glow {
  position: absolute;
  width: 100px;
  height: 100px;
  background: var(--gradient-primary);
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.3;
  top: -30px;
  right: -30px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.chart-card {
  background: var(--bg-card);
  border: var(--border-glow);
  border-radius: 16px;
  padding: 1.5rem;
}

.chart-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--accent-cyan);
  margin-bottom: 1rem;
}

.chart-container {
  height: 300px;
}

@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .charts-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
