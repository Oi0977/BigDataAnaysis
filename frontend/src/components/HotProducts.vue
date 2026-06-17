<template>
  <div class="hot-products">
    <div class="section-header">
      <h2 class="section-title">🔥 爆款分析</h2>
      <div class="filter-group">
        <select v-model="selectedCategory" class="filter-select" @change="onCategoryChange">
          <option value="">全部品类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
        <span class="result-count">共 {{ total }} 个商品</span>
      </div>
    </div>

    <!-- 图表分析区域 -->
    <div class="charts-section">
      <div class="chart-row">
        <div class="chart-card">
          <h3 class="chart-title">品类爆款数量分布</h3>
          <div ref="categoryBarChart" class="chart-container"></div>
        </div>
        <div class="chart-card">
          <h3 class="chart-title">爆款指数 vs 销量</h3>
          <div ref="scatterChart" class="chart-container"></div>
        </div>
      </div>
      <div class="chart-row">
        <div class="chart-card">
          <h3 class="chart-title">各品类平均爆款指数</h3>
          <div ref="avgHotScoreChart" class="chart-container"></div>
        </div>
        <div class="chart-card">
          <h3 class="chart-title">价格区间分布</h3>
          <div ref="pricePieChart" class="chart-container"></div>
        </div>
      </div>
    </div>

    <!-- 商品卡片列表 -->
    <div class="products-section">
      <h3 class="sub-title">商品列表</h3>
      <div class="products-grid">
        <div
          v-for="product in products"
          :key="product.product_id"
          class="product-card"
        >
          <div class="product-image">
            <img :src="product.image_url" :alt="product.name" @error="onImgError" />
            <span class="hot-badge">{{ (product.hot_score || 0).toFixed(0) }}</span>
          </div>
          <div class="product-body">
            <span class="product-id">{{ product.product_id }}</span>
            <h3 class="product-name">{{ product.name }}</h3>

            <!-- Mock原始数据 -->
            <div class="data-section mock-data">
              <span class="data-tag tag-mock">原始数据</span>
              <div class="data-items">
                <span class="data-item">{{ product.brand }}</span>
                <span class="data-item">{{ product.category }}</span>
                <span class="data-item price">¥{{ product.price }}</span>
              </div>
            </div>

            <!-- Spark计算结果 -->
            <div class="data-section spark-data">
              <span class="data-tag tag-spark">Spark计算</span>
              <div class="data-items">
                <span class="data-item">
                  <span class="item-label">总销量</span>
                  <span class="item-value">{{ (product.total_sales || 0).toLocaleString() }}</span>
                </span>
                <span class="data-item">
                  <span class="item-label">评分</span>
                  <span class="item-value">{{ product.avg_rating || 0 }}</span>
                </span>
                <span class="data-item">
                  <span class="item-label">好评率</span>
                  <span class="item-value">{{ ((product.positive_rate || 0) * 100).toFixed(1) }}%</span>
                </span>
                <span class="data-item">
                  <span class="item-label">增长率</span>
                  <span class="item-value" :class="product.monthly_growth >= 0 ? 'growth-up' : 'growth-down'">
                    {{ product.monthly_growth >= 0 ? '+' : '' }}{{ (product.monthly_growth || 0).toFixed(1) }}%
                  </span>
                </span>
              </div>
            </div>

            <p class="product-desc">{{ product.description }}</p>
          </div>
        </div>
      </div>

      <div v-if="products.length === 0" class="empty-state">
        <p>暂无数据</p>
      </div>

      <div class="pagination" v-if="totalPages > 1">
        <button class="page-btn" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</button>
        <template v-for="p in displayedPages" :key="p">
          <button v-if="p === '...'" class="page-btn ellipsis" disabled>...</button>
          <button v-else class="page-btn" :class="{ active: p === currentPage }" @click="goPage(p)">{{ p }}</button>
        </template>
        <button class="page-btn" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</button>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import { getHotProducts } from '../api'

export default {
  name: 'HotProducts',
  data() {
    return {
      products: [],
      categories: ['手机', '电脑', '服装', '美妆', '食品', '家居', '数码', '运动'],
      selectedCategory: '',
      total: 0,
      currentPage: 1,
      pageSize: 20,
      // 图表数据（全量数据用于图表分析）
      chartProducts: [],
      // 图表实例引用
      chartInstances: []
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.pageSize)
    },
    displayedPages() {
      const pages = []
      const tp = this.totalPages
      const cur = this.currentPage
      if (tp <= 7) {
        for (let i = 1; i <= tp; i++) pages.push(i)
      } else {
        pages.push(1)
        if (cur > 3) pages.push('...')
        for (let i = Math.max(2, cur - 1); i <= Math.min(tp - 1, cur + 1); i++) {
          pages.push(i)
        }
        if (cur < tp - 2) pages.push('...')
        pages.push(tp)
      }
      return pages
    }
  },
  mounted() {
    this.loadAllData()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    this.disposeCharts()
  },
  methods: {
    // 加载全量数据（用于图表分析）
    async loadAllData() {
      try {
        const res = await getHotProducts({ limit: 100, page: 1 })
        if (res.data.code === 200) {
          this.chartProducts = res.data.data.products || []
          this.total = res.data.data.total || 0
          this.updatePageProducts()
          this.$nextTick(() => {
            this.initCharts()
          })
        }
      } catch (error) {
        console.error('加载全量数据失败:', error)
      }
    },
    // 分页：从 chartProducts 中取当前页数据
    updatePageProducts() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + this.pageSize
      this.products = this.chartProducts.slice(start, end)
    },
    onCategoryChange() {
      this.currentPage = 1
      this.filterAndRender()
    },
    async filterAndRender() {
      try {
        const params = { limit: 100, page: 1 }
        if (this.selectedCategory) {
          params.category = this.selectedCategory
        }
        const res = await getHotProducts(params)
        if (res.data.code === 200) {
          this.chartProducts = res.data.data.products || []
          this.total = res.data.data.total || 0
          this.updatePageProducts()
          this.$nextTick(() => {
            this.renderCharts()
          })
        }
      } catch (error) {
        console.error('筛选数据失败:', error)
      }
    },
    goPage(page) {
      if (page < 1 || page > this.totalPages) return
      this.currentPage = page
      this.updatePageProducts()
    },
    onImgError(e) {
      e.target.src = 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect fill="%23333" width="100" height="100"/><text fill="%23666" x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-size="14">暂无图片</text></svg>'
    },
    // ========== 图表相关方法 ==========
    disposeCharts() {
      this.chartInstances.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.dispose()
        }
      })
      this.chartInstances = []
    },
    handleResize() {
      this.chartInstances.forEach(chart => {
        if (chart && !chart.isDisposed()) {
          chart.resize()
        }
      })
    },
    // 创建通用的图表基础配置
    getBaseOption() {
      return {
        backgroundColor: 'transparent',
        textStyle: {
          fontFamily: 'Rajdhani, sans-serif',
          color: '#94a3b8'
        },
        grid: {
          top: 40,
          right: 20,
          bottom: 30,
          left: 50,
          containLabel: true
        }
      }
    },
    // 品类爆款数量分布 - 柱状图
    renderCategoryBarChart() {
      if (this.chartInstances[0]) {
        this.chartInstances[0].dispose()
      }
      const dom = this.$refs.categoryBarChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[0] = chart

      // 按品类统计数量
      const categoryCount = {}
      this.chartProducts.forEach(p => {
        categoryCount[p.category] = (categoryCount[p.category] || 0) + 1
      })
      const sortedCategories = Object.keys(categoryCount).sort((a, b) => categoryCount[b] - categoryCount[a])
      const counts = sortedCategories.map(c => categoryCount[c])

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: 'rgba(0, 245, 255, 0.3)',
          textStyle: { color: '#e2e8f0' }
        },
        xAxis: {
          type: 'category',
          data: sortedCategories,
          axisLabel: { color: '#94a3b8', fontSize: 12 },
          axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.2)' } },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          name: '数量',
          nameTextStyle: { color: '#94a3b8' },
          axisLabel: { color: '#94a3b8' },
          splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.08)' } },
          axisLine: { show: false }
        },
        series: [{
          type: 'bar',
          data: counts,
          barWidth: '50%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#00f5ff' },
              { offset: 1, color: 'rgba(0, 245, 255, 0.2)' }
            ])
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#a855f7' },
                { offset: 1, color: 'rgba(168, 85, 247, 0.3)' }
              ])
            }
          }
        }]
      })
    },
    // 爆款指数 vs 销量 - 散点图
    renderScatterChart() {
      if (this.chartInstances[1]) {
        this.chartInstances[1].dispose()
      }
      const dom = this.$refs.scatterChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[1] = chart

      // 按品类分组散点
      const categoryColorMap = {
        '手机': '#00f5ff', '电脑': '#a855f7', '服装': '#ec4899',
        '美妆': '#f59e0b', '食品': '#10b981', '家居': '#6366f1',
        '数码': '#ef4444', '运动': '#06b6d4'
      }
      const seriesData = {}
      this.chartProducts.forEach(p => {
        if (!seriesData[p.category]) {
          seriesData[p.category] = []
        }
        seriesData[p.category].push([p.total_sales || 0, p.hot_score, p.name, p.price])
      })

      const series = Object.keys(seriesData).map(cat => ({
        name: cat,
        type: 'scatter',
        data: seriesData[cat],
        symbolSize: 12,
        itemStyle: {
          color: categoryColorMap[cat] || '#94a3b8',
          shadowBlur: 6,
          shadowColor: (categoryColorMap[cat] || '#94a3b8') + '80'
        },
        emphasis: {
          itemStyle: { borderColor: '#fff', borderWidth: 2 }
        }
      }))

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: 'rgba(0, 245, 255, 0.3)',
          textStyle: { color: '#e2e8f0' },
          formatter(params) {
            const [sales, hotScore, name, price] = params.data
            return `<b>${name}</b><br/>品类: ${params.seriesName}<br/>销量: ${sales.toLocaleString()}<br/>爆款指数: ${hotScore}<br/>价格: ¥${price}`
          }
        },
        legend: {
          type: 'scroll',
          top: 0,
          right: 0,
          textStyle: { color: '#94a3b8', fontSize: 11 },
          pageTextStyle: { color: '#94a3b8' }
        },
        xAxis: {
          type: 'value',
          name: '销量',
          nameTextStyle: { color: '#94a3b8' },
          axisLabel: { color: '#94a3b8', formatter: v => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v },
          splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.08)' } },
          axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.2)' } }
        },
        yAxis: {
          type: 'value',
          name: '爆款指数',
          nameTextStyle: { color: '#94a3b8' },
          axisLabel: { color: '#94a3b8' },
          splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.08)' } },
          axisLine: { show: false }
        },
        series
      })
    },
    // 各品类平均爆款指数 - 横向柱状图
    renderAvgHotScoreChart() {
      if (this.chartInstances[2]) {
        this.chartInstances[2].dispose()
      }
      const dom = this.$refs.avgHotScoreChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[2] = chart

      // 按品类计算平均爆款指数
      const categoryHotSum = {}
      const categoryCount = {}
      this.chartProducts.forEach(p => {
        categoryHotSum[p.category] = (categoryHotSum[p.category] || 0) + p.hot_score
        categoryCount[p.category] = (categoryCount[p.category] || 0) + 1
      })
      const categories = Object.keys(categoryHotSum)
      const avgScores = categories.map(c => +(categoryHotSum[c] / categoryCount[c]).toFixed(1))
      // 按平均值排序
      const sorted = categories
        .map((c, i) => ({ name: c, value: avgScores[i] }))
        .sort((a, b) => a.value - b.value)

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: 'rgba(168, 85, 247, 0.3)',
          textStyle: { color: '#e2e8f0' },
          formatter(params) {
            const p = params[0]
            return `${p.name}<br/>平均爆款指数: <b>${p.value}</b>`
          }
        },
        grid: {
          top: 20,
          right: 30,
          bottom: 20,
          left: 10,
          containLabel: true
        },
        xAxis: {
          type: 'value',
          name: '平均爆款指数',
          nameTextStyle: { color: '#94a3b8' },
          axisLabel: { color: '#94a3b8' },
          splitLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.08)' } },
          axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.2)' } }
        },
        yAxis: {
          type: 'category',
          data: sorted.map(s => s.name),
          axisLabel: { color: '#94a3b8', fontSize: 12 },
          axisLine: { lineStyle: { color: 'rgba(0, 245, 255, 0.2)' } },
          axisTick: { show: false }
        },
        series: [{
          type: 'bar',
          data: sorted.map(s => s.value),
          barWidth: '55%',
          label: {
            show: true,
            position: 'right',
            color: '#e2e8f0',
            fontSize: 12,
            fontFamily: 'Orbitron, sans-serif'
          },
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: 'rgba(168, 85, 247, 0.3)' },
              { offset: 1, color: '#a855f7' }
            ])
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: 'rgba(0, 245, 255, 0.3)' },
                { offset: 1, color: '#00f5ff' }
              ])
            }
          }
        }]
      })
    },
    // 价格区间分布 - 饼图
    renderPricePieChart() {
      if (this.chartInstances[3]) {
        this.chartInstances[3].dispose()
      }
      const dom = this.$refs.pricePieChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[3] = chart

      const priceRanges = [
        { name: '0-500', min: 0, max: 500 },
        { name: '500-1000', min: 500, max: 1000 },
        { name: '1000-2000', min: 1000, max: 2000 },
        { name: '2000-5000', min: 2000, max: 5000 },
        { name: '5000+', min: 5000, max: Infinity }
      ]
      const rangeColors = ['#00f5ff', '#a855f7', '#ec4899', '#f59e0b', '#10b981']
      const pieData = priceRanges.map((range, idx) => {
        const count = this.chartProducts.filter(p => p.price >= range.min && p.price < range.max).length
        return { name: range.name, value: count, itemStyle: { color: rangeColors[idx] } }
      }).filter(d => d.value > 0)

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          trigger: 'item',
          backgroundColor: 'rgba(17, 24, 39, 0.9)',
          borderColor: 'rgba(0, 245, 255, 0.3)',
          textStyle: { color: '#e2e8f0' },
          formatter: '{b}: {c} 个 ({d}%)'
        },
        legend: {
          orient: 'vertical',
          right: 10,
          top: 'center',
          textStyle: { color: '#94a3b8', fontSize: 12 },
          icon: 'circle',
          itemWidth: 10,
          itemHeight: 10
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: true,
          label: {
            show: true,
            color: '#e2e8f0',
            fontSize: 12,
            formatter: '{b}\n{d}%'
          },
          labelLine: {
            lineStyle: { color: 'rgba(148, 163, 184, 0.5)' }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 20,
              shadowColor: 'rgba(0, 245, 255, 0.5)'
            }
          },
          data: pieData
        }]
      })
    },
    initCharts() {
      this.disposeCharts()
      this.$nextTick(() => {
        this.renderCategoryBarChart()
        this.renderScatterChart()
        this.renderAvgHotScoreChart()
        this.renderPricePieChart()
      })
    },
    renderCharts() {
      this.renderCategoryBarChart()
      this.renderScatterChart()
      this.renderAvgHotScoreChart()
      this.renderPricePieChart()
    }
  }
}
</script>

<style scoped>
.hot-products {
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(-20px); }
  to { opacity: 1; transform: translateX(0); }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  color: var(--accent-cyan);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.result-count {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.filter-select {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  color: var(--text-primary);
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-select:hover,
.filter-select:focus {
  border-color: var(--accent-cyan);
  outline: none;
}

/* ========== 图表区域 ========== */
.charts-section {
  margin-bottom: 2rem;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.chart-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.25rem;
  transition: all 0.3s ease;
}

.chart-card:hover {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 20px rgba(0, 245, 255, 0.15);
}

.chart-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  color: var(--accent-cyan);
  margin-bottom: 0.75rem;
  letter-spacing: 0.5px;
}

.chart-container {
  width: 100%;
  height: 280px;
}

/* ========== 商品列表 ========== */
.products-section {
  margin-top: 1rem;
}

.sub-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem;
  color: var(--accent-purple);
  margin-bottom: 1.25rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(168, 85, 247, 0.2);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s ease;
  position: relative;
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--glow-cyan);
}

.product-image {
  position: relative;
  width: 100%;
  height: 180px;
  background: #1a1a2e;
  overflow: hidden;
}

.product-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hot-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: linear-gradient(135deg, #ff6b35, #ff2e63);
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(255, 46, 99, 0.4);
}

.product-body {
  padding: 1rem 1.25rem 1.25rem;
}

.product-id {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.product-name {
  font-size: 1.15rem;
  color: var(--text-primary);
  margin: 0.3rem 0;
}

.product-category {
  color: var(--accent-purple);
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.product-desc {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-bottom: 1rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding-top: 0.75rem;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  color: var(--text-secondary);
  font-size: 0.75rem;
  margin-bottom: 0.2rem;
}

.stat-value {
  display: block;
  color: var(--accent-cyan);
  font-weight: 600;
  font-size: 0.95rem;
}

.stat-value.price {
  color: #ff6b35;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.5rem;
  margin-top: 2rem;
}

.page-btn {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 6px;
  padding: 0.5rem 0.85rem;
  color: var(--text-primary);
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled):not(.active) {
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}

.page-btn.active {
  background: var(--accent-cyan);
  color: #000;
  font-weight: 700;
  border-color: var(--accent-cyan);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-btn.ellipsis {
  border: none;
  background: transparent;
  color: var(--text-secondary);
}

/* ========== 响应式布局 ========== */
@media (max-width: 768px) {
  .chart-row {
    grid-template-columns: 1fr;
  }
  .chart-container {
    height: 240px;
  }
  .products-grid {
    grid-template-columns: 1fr;
  }
}

/* ========== 数据来源标签 ========== */
.data-section {
  margin: 0.5rem 0;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  border-left: 3px solid;
}

.mock-data {
  background: rgba(34, 197, 94, 0.08);
  border-left-color: #22c55e;
}

.spark-data {
  background: rgba(59, 130, 246, 0.08);
  border-left-color: #3b82f6;
}

.data-tag {
  display: inline-block;
  font-size: 0.65rem;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
  margin-bottom: 0.4rem;
  letter-spacing: 0.5px;
}

.tag-mock {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.tag-spark {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.data-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.data-item {
  font-size: 0.8rem;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.05);
  padding: 2px 8px;
  border-radius: 4px;
}

.data-item.price {
  color: #ff6b35;
  font-weight: 600;
}

.item-label {
  color: var(--text-secondary);
  margin-right: 0.3rem;
}

.item-value {
  color: var(--text-primary);
  font-weight: 600;
}

.growth-up {
  color: #22c55e;
}

.growth-down {
  color: #ef4444;
}
</style>
