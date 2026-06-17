<template>
  <div class="home">
    <div class="page-header">
      <div>
        <h1 class="page-title">数据概览</h1>
        <p class="page-subtitle">实时掌握电商数据动态</p>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card" v-for="stat in stats" :key="stat.label">
        <div class="stat-icon-wrap" :style="{ background: stat.bgColor }">
          <span class="stat-icon">{{ stat.icon }}</span>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <div class="charts-grid">
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">品类分布</h3>
        </div>
        <div class="chart-body" ref="categoryChart"></div>
      </div>
      <div class="chart-card">
        <div class="chart-header">
          <h3 class="chart-title">爆款指数趋势</h3>
        </div>
        <div class="chart-body" ref="trendChart"></div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getDashboardStats, getDashboardTrend } from '../api'

const COLORS = ['#4F6EF7', '#F97316', '#22C55E', '#EF4444', '#F59E0B', '#8B5CF6', '#EC4899', '#06B6D4']

export default {
  name: 'Home',
  data() {
    return {
      stats: [
        { icon: '📦', value: '0', label: '商品总数', bgColor: '#EEF1FE' },
        { icon: '💬', value: '0', label: '评价总数', bgColor: '#ECFDF5' },
        { icon: '🔥', value: '0', label: '爆款数量', bgColor: '#FFFBEB' },
        { icon: '📊', value: '0', label: '品类数量', bgColor: '#FEF2F2' }
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
          backgroundColor: '#fff',
          borderColor: '#E8ECF1',
          borderWidth: 1,
          textStyle: { color: '#1A2138', fontSize: 13 },
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.08)'
        },
        series: [{
          type: 'pie',
          radius: ['45%', '72%'],
          center: ['50%', '50%'],
          itemStyle: {
            borderRadius: 6,
            borderColor: '#fff',
            borderWidth: 3
          },
          label: {
            show: true,
            color: '#4A5568',
            fontSize: 12,
            formatter: '{b}\n{d}%'
          },
          labelLine: {
            lineStyle: { color: '#B0BEC5' }
          },
          emphasis: {
            label: { fontSize: 14, fontWeight: '600' },
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' }
          },
          data: this.categoryData.length > 0 ? this.categoryData : [
            { value: 0, name: '暂无数据', itemStyle: { color: '#E8ECF1' } }
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
          backgroundColor: '#fff',
          borderColor: '#E8ECF1',
          borderWidth: 1,
          textStyle: { color: '#1A2138', fontSize: 13 },
          shadowBlur: 10,
          shadowColor: 'rgba(0,0,0,0.08)'
        },
        xAxis: {
          type: 'category',
          data: this.trendMonths.length > 0 ? this.trendMonths : ['暂无数据'],
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
        grid: { top: 20, right: 20, bottom: 30, left: 50, containLabel: false },
        series: [{
          data: this.trendData.length > 0 ? this.trendData : [0],
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#4F6EF7', width: 2.5 },
          itemStyle: { color: '#4F6EF7', borderColor: '#fff', borderWidth: 2 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(79, 110, 247, 0.15)' },
              { offset: 1, color: 'rgba(79, 110, 247, 0.01)' }
            ])
          }
        }]
      }
      chart.setOption(option)
      this.trendChart = chart
    }
  },
  beforeUnmount() {
    if (this.categoryChart) this.categoryChart.dispose()
    if (this.trendChart) this.trendChart.dispose()
  }
}
</script>

<style scoped>
.home {
  animation: fadeIn 0.4s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.page-header {
  margin-bottom: 1.75rem;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-title);
  letter-spacing: -0.02em;
  margin-bottom: 0.25rem;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 0.925rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: all var(--transition);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.stat-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-family: 'Space Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-title);
  line-height: 1.2;
}

.stat-label {
  color: var(--text-secondary);
  font-size: 0.825rem;
  margin-top: 0.15rem;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.chart-card {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.chart-header {
  padding: 1.25rem 1.25rem 0;
}

.chart-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-title);
}

.chart-body {
  height: 300px;
  padding: 0.5rem;
}

@media (max-width: 1024px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .charts-grid { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .stats-grid { grid-template-columns: 1fr; }
}
</style>
