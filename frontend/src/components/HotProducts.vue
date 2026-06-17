<template>
  <div class="hot-products">
    <div class="section-header">
      <h2 class="section-title">爆款分析</h2>
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
          @click="openDetail(product)"
        >
          <div class="product-body">
            <div class="product-top">
              <span class="product-id">{{ product.product_id }}</span>
              <span class="hot-badge">{{ (product.hot_score || 0).toFixed(2) }}</span>
            </div>
            <h3 class="product-name">{{ product.name }}</h3>
            <p class="product-category">{{ product.brand }} · {{ product.category }}</p>
            <div class="product-stats">
              <div class="stat">
                <span class="stat-label">价格</span>
                <span class="stat-value price">¥{{ product.price }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">日增长</span>
                <span class="stat-value" :class="(product.daily_growth || 0) >= 0 ? 'growth-up' : 'growth-down'">
                  {{ (product.daily_growth || 0) >= 0 ? '+' : '' }}{{ (product.daily_growth || 0).toFixed(1) }}%
                </span>
              </div>
              <div class="stat">
                <span class="stat-label">好评率</span>
                <span class="stat-value">{{ ((product.positive_rate || 0) * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <p class="click-hint">点击查看详情</p>
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

    <!-- 详情弹窗 -->
    <div v-if="detailProduct" class="modal-overlay" @click.self="closeDetail">
      <div class="modal-content">
        <button class="modal-close" @click="closeDetail">&times;</button>

        <div class="modal-header">
          <div class="modal-info">
            <span class="modal-id">{{ detailProduct.product_id }}</span>
            <h2 class="modal-name">{{ detailProduct.name }}</h2>
            <p class="modal-brand">{{ detailProduct.brand }} · {{ detailProduct.category }} · {{ detailProduct.shop_name }}</p>
            <p class="modal-desc">{{ detailProduct.description }}</p>
          </div>
        </div>

        <!-- 月度销量趋势图 -->
        <div class="modal-section">
          <h3 class="modal-section-title">近30天销量趋势</h3>
          <div ref="monthlyTrendChart" class="modal-chart"></div>
        </div>

        <!-- 商品信息 -->
        <div class="modal-section">
          <h3 class="modal-section-title">商品信息</h3>
          <div class="modal-grid">
            <div class="modal-stat">
              <span class="modal-stat-label">品牌</span>
              <span class="modal-stat-value">{{ detailProduct.brand }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">品类</span>
              <span class="modal-stat-value">{{ detailProduct.category }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">当前价格</span>
              <span class="modal-stat-value price">¥{{ detailProduct.price }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">原价</span>
              <span class="modal-stat-value">¥{{ detailProduct.original_price }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">店铺</span>
              <span class="modal-stat-value">{{ detailProduct.shop_name }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">上架时间</span>
              <span class="modal-stat-value">{{ detailProduct.create_time }}</span>
            </div>
          </div>
        </div>

        <!-- 统计分析 -->
        <div class="modal-section">
          <h3 class="modal-section-title">统计分析</h3>
          <div class="modal-grid">
            <div class="modal-stat highlight full-width">
              <span class="modal-stat-label">爆款指数</span>
              <span class="modal-stat-value hot">{{ (detailProduct.hot_score || 0).toFixed(2) }}<small>/1.00</small></span>
              <div class="score-breakdown" v-if="detailProduct.score_breakdown">
                <div class="score-bar-row">
                  <span class="score-label">销量 (40%)</span>
                  <div class="score-bar-bg"><div class="score-bar-fill sales" :style="{ width: (detailProduct.score_breakdown.sales || 0) * 100 + '%' }"></div></div>
                  <span class="score-val">{{ (detailProduct.score_breakdown.sales || 0).toFixed(2) }}</span>
                </div>
                <div class="score-bar-row">
                  <span class="score-label">增长 (30%)</span>
                  <div class="score-bar-bg"><div class="score-bar-fill growth" :style="{ width: (detailProduct.score_breakdown.growth || 0) * 100 + '%' }"></div></div>
                  <span class="score-val">{{ (detailProduct.score_breakdown.growth || 0).toFixed(2) }}</span>
                </div>
                <div class="score-bar-row">
                  <span class="score-label">评分 (20%)</span>
                  <div class="score-bar-bg"><div class="score-bar-fill rating" :style="{ width: (detailProduct.score_breakdown.rating || 0) * 100 + '%' }"></div></div>
                  <span class="score-val">{{ (detailProduct.score_breakdown.rating || 0).toFixed(2) }}</span>
                </div>
                <div class="score-bar-row">
                  <span class="score-label">评价 (10%)</span>
                  <div class="score-bar-bg"><div class="score-bar-fill review" :style="{ width: (detailProduct.score_breakdown.review || 0) * 100 + '%' }"></div></div>
                  <span class="score-val">{{ (detailProduct.score_breakdown.review || 0).toFixed(2) }}</span>
                </div>
              </div>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">总销量</span>
              <span class="modal-stat-value">{{ (detailProduct.total_sales || 0).toLocaleString() }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">平均评分</span>
              <span class="modal-stat-value">{{ detailProduct.avg_rating || 0 }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">评价数</span>
              <span class="modal-stat-value">{{ detailProduct.review_count || 0 }}</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">好评率</span>
              <span class="modal-stat-value">{{ ((detailProduct.positive_rate || 0) * 100).toFixed(1) }}%</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">差评率</span>
              <span class="modal-stat-value">{{ ((detailProduct.negative_rate || 0) * 100).toFixed(1) }}%</span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">日增长率</span>
              <span class="modal-stat-value" :class="(detailProduct.daily_growth || 0) >= 0 ? 'growth-up' : 'growth-down'">
                {{ (detailProduct.daily_growth || 0) >= 0 ? '+' : '' }}{{ (detailProduct.daily_growth || 0).toFixed(1) }}%
              </span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">周增长率</span>
              <span class="modal-stat-value" :class="(detailProduct.weekly_growth || 0) >= 0 ? 'growth-up' : 'growth-down'">
                {{ (detailProduct.weekly_growth || 0) >= 0 ? '+' : '' }}{{ (detailProduct.weekly_growth || 0).toFixed(1) }}%
              </span>
            </div>
            <div class="modal-stat">
              <span class="modal-stat-label">高频标签</span>
              <span class="modal-stat-value tags">{{ detailProduct.top_tags || '无' }}</span>
            </div>
          </div>
        </div>
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
      chartProducts: [],
      chartInstances: [],
      detailProduct: null,
      monthlyChart: null
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
    openDetail(product) {
      this.detailProduct = product
      this.$nextTick(() => { this.renderMonthlyTrendChart() })
    },
    closeDetail() {
      if (this.monthlyChart && !this.monthlyChart.isDisposed()) {
        this.monthlyChart.dispose()
      }
      this.monthlyChart = null
      this.detailProduct = null
    },
    renderMonthlyTrendChart() {
      this.$nextTick(() => {
        const el = this.$refs.monthlyTrendChart
        if (!el) return
        if (this.monthlyChart && !this.monthlyChart.isDisposed()) {
          this.monthlyChart.dispose()
        }
        this.monthlyChart = echarts.init(el)
        const trend = this.detailProduct.sales_trend
        let months = []
        if (typeof trend === 'string') {
          try { months = JSON.parse(trend) } catch { months = [] }
        } else if (Array.isArray(trend)) {
          months = trend
        }
        const now = new Date()
        const labels = []
        for (let i = months.length - 1; i >= 0; i--) {
          const d = new Date(now)
          d.setDate(d.getDate() - i)
          labels.push(`${d.getMonth() + 1}/${d.getDate()}`)
        }
        this.monthlyChart.setOption({
          backgroundColor: 'transparent',
          textStyle: { fontFamily: 'DM Sans, Noto Sans SC, sans-serif', color: '#4A5568' },
          tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E8ECF1', borderWidth: 1, textStyle: { color: '#1A2138' }, formatter: p => `${p[0].name}<br/>销量: ${p[0].value.toLocaleString()}` },
          grid: { top: 30, right: 20, bottom: 30, left: 50, containLabel: true },
          xAxis: { type: 'category', data: labels, axisLabel: { color: '#8492A6', rotate: 45, fontSize: 10 }, axisLine: { lineStyle: { color: '#E8ECF1' } }, axisTick: { show: false } },
          yAxis: { type: 'value', axisLabel: { color: '#8492A6' }, splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } }, axisLine: { show: false } },
          series: [{
            type: 'line', data: months, smooth: true,
            lineStyle: { color: '#4F6EF7', width: 2 },
            areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(79, 110, 247, 0.15)' }, { offset: 1, color: 'rgba(79, 110, 247, 0.01)' }
            ]) },
            itemStyle: { color: '#4F6EF7' },
            symbol: 'circle', symbolSize: 4
          }]
        })
      })
    },
    disposeCharts() {
      this.chartInstances.forEach(chart => {
        if (chart && !chart.isDisposed()) chart.dispose()
      })
      this.chartInstances = []
    },
    handleResize() {
      this.chartInstances.forEach(chart => {
        if (chart && !chart.isDisposed()) chart.resize()
      })
    },
    getBaseOption() {
      return {
        backgroundColor: 'transparent',
        textStyle: { fontFamily: 'DM Sans, Noto Sans SC, sans-serif', color: '#4A5568' },
        grid: { top: 40, right: 20, bottom: 30, left: 50, containLabel: true }
      }
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
    renderCategoryBarChart() {
      if (this.chartInstances[0]) this.chartInstances[0].dispose()
      const dom = this.$refs.categoryBarChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[0] = chart

      const categoryCount = {}
      this.chartProducts.forEach(p => {
        categoryCount[p.category] = (categoryCount[p.category] || 0) + 1
      })
      const sortedCategories = Object.keys(categoryCount).sort((a, b) => categoryCount[b] - categoryCount[a])
      const counts = sortedCategories.map(c => categoryCount[c])

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: { ...this.getTooltip(), trigger: 'axis' },
        xAxis: {
          type: 'category', data: sortedCategories,
          axisLabel: { color: '#8492A6', fontSize: 12 },
          axisLine: { lineStyle: { color: '#E8ECF1' } },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value', name: '数量',
          nameTextStyle: { color: '#8492A6', fontSize: 12 },
          axisLabel: { color: '#8492A6' },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } },
          axisLine: { show: false }
        },
        series: [{
          type: 'bar', data: counts, barWidth: '50%',
          itemStyle: {
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#4F6EF7' },
              { offset: 1, color: '#7B93FF' }
            ])
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#3D5BD9' },
                { offset: 1, color: '#4F6EF7' }
              ])
            }
          }
        }]
      })
    },
    renderScatterChart() {
      if (this.chartInstances[1]) this.chartInstances[1].dispose()
      const dom = this.$refs.scatterChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[1] = chart

      const categoryColorMap = {
        '手机': '#4F6EF7', '电脑': '#8B5CF6', '服装': '#EC4899',
        '美妆': '#F59E0B', '食品': '#22C55E', '家居': '#6366F1',
        '数码': '#EF4444', '运动': '#06B6D4'
      }
      const seriesData = {}
      this.chartProducts.forEach(p => {
        if (!seriesData[p.category]) seriesData[p.category] = []
        seriesData[p.category].push([p.total_sales || 0, p.hot_score, p.name, p.price])
      })

      const series = Object.keys(seriesData).map(cat => ({
        name: cat,
        type: 'scatter',
        data: seriesData[cat],
        symbolSize: 10,
        itemStyle: { color: categoryColorMap[cat] || '#8492A6' },
        emphasis: { itemStyle: { borderColor: '#fff', borderWidth: 2, shadowBlur: 6, shadowColor: 'rgba(0,0,0,0.15)' } }
      }))

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          ...this.getTooltip(), trigger: 'item',
          formatter(params) {
            const [sales, hotScore, name, price] = params.data
            return `<b>${name}</b><br/>品类: ${params.seriesName}<br/>销量: ${sales.toLocaleString()}<br/>爆款指数: ${hotScore.toFixed(2)}<br/>价格: ¥${price}`
          }
        },
        legend: {
          type: 'scroll', top: 0, right: 0,
          textStyle: { color: '#8492A6', fontSize: 11 },
          pageTextStyle: { color: '#8492A6' }
        },
        xAxis: {
          type: 'value', name: '销量',
          nameTextStyle: { color: '#8492A6' },
          axisLabel: { color: '#8492A6', formatter: v => v >= 1000 ? (v / 1000).toFixed(0) + 'k' : v },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } },
          axisLine: { lineStyle: { color: '#E8ECF1' } }
        },
        yAxis: {
          type: 'value', name: '爆款指数',
          nameTextStyle: { color: '#8492A6' },
          axisLabel: { color: '#8492A6' },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } },
          axisLine: { show: false }
        },
        series
      })
    },
    renderAvgHotScoreChart() {
      if (this.chartInstances[2]) this.chartInstances[2].dispose()
      const dom = this.$refs.avgHotScoreChart
      if (!dom) return
      const chart = echarts.init(dom)
      this.chartInstances[2] = chart

      const categoryHotSum = {}
      const categoryCount = {}
      this.chartProducts.forEach(p => {
        categoryHotSum[p.category] = (categoryHotSum[p.category] || 0) + p.hot_score
        categoryCount[p.category] = (categoryCount[p.category] || 0) + 1
      })
      const categories = Object.keys(categoryHotSum)
      const avgScores = categories.map(c => +(categoryHotSum[c] / categoryCount[c]).toFixed(2))
      const sorted = categories
        .map((c, i) => ({ name: c, value: avgScores[i] }))
        .sort((a, b) => a.value - b.value)

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          ...this.getTooltip(), trigger: 'axis',
          formatter(params) {
            const p = params[0]
            return `${p.name}<br/>平均爆款指数: <b>${p.value.toFixed(2)}</b>`
          }
        },
        grid: { top: 20, right: 30, bottom: 20, left: 10, containLabel: true },
        xAxis: {
          type: 'value', name: '平均爆款指数',
          nameTextStyle: { color: '#8492A6' },
          axisLabel: { color: '#8492A6' },
          splitLine: { lineStyle: { color: '#F0F2F5', type: 'dashed' } },
          axisLine: { lineStyle: { color: '#E8ECF1' } }
        },
        yAxis: {
          type: 'category',
          data: sorted.map(s => s.name),
          axisLabel: { color: '#8492A6', fontSize: 12 },
          axisLine: { lineStyle: { color: '#E8ECF1' } },
          axisTick: { show: false }
        },
        series: [{
          type: 'bar',
          data: sorted.map(s => s.value),
          barWidth: '55%',
          label: {
            show: true, position: 'right',
            color: '#4A5568', fontSize: 12, fontWeight: 600
          },
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: '#B6C4FF' },
              { offset: 1, color: '#4F6EF7' }
            ])
          },
          emphasis: {
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: '#3D5BD9' },
                { offset: 1, color: '#3D5BD9' }
              ])
            }
          }
        }]
      })
    },
    renderPricePieChart() {
      if (this.chartInstances[3]) this.chartInstances[3].dispose()
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
      const rangeColors = ['#4F6EF7', '#8B5CF6', '#F97316', '#22C55E', '#EF4444']
      const pieData = priceRanges.map((range, idx) => {
        const count = this.chartProducts.filter(p => p.price >= range.min && p.price < range.max).length
        return { name: range.name, value: count, itemStyle: { color: rangeColors[idx] } }
      }).filter(d => d.value > 0)

      chart.setOption({
        ...this.getBaseOption(),
        tooltip: {
          ...this.getTooltip(), trigger: 'item',
          formatter: '{b}: {c} 个 ({d}%)'
        },
        legend: {
          orient: 'vertical', right: 10, top: 'center',
          textStyle: { color: '#4A5568', fontSize: 12 },
          icon: 'circle', itemWidth: 10, itemHeight: 10
        },
        series: [{
          type: 'pie',
          radius: ['42%', '72%'],
          center: ['40%', '50%'],
          avoidLabelOverlap: true,
          label: { show: true, color: '#4A5568', fontSize: 12, formatter: '{b}\n{d}%' },
          labelLine: { lineStyle: { color: '#B0BEC5' } },
          emphasis: {
            itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.1)' }
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
  from { opacity: 0; transform: translateX(-12px); }
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
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-title);
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.result-count {
  color: var(--text-secondary);
  font-size: 0.85rem;
}

.filter-select {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.55rem 1rem;
  color: var(--text-body);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition);
  font-family: inherit;
}

.filter-select:hover,
.filter-select:focus {
  border-color: var(--color-primary);
  outline: none;
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

/* ========== Charts ========== */
.charts-section {
  margin-bottom: 2rem;
}

.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1rem;
}

.chart-card {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.25rem;
  transition: all var(--transition);
}

.chart-card:hover {
  box-shadow: var(--shadow-sm);
}

.chart-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 0.75rem;
}

.chart-container {
  width: 100%;
  height: 260px;
}

/* ========== Product List ========== */
.products-section {
  margin-top: 1rem;
}

.sub-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid var(--border);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}

.product-card {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: all var(--transition);
  cursor: pointer;
}

.product-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary-light);
}

.product-body {
  padding: 1rem 1.25rem 1.125rem;
}

.product-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.product-id {
  font-family: 'Space Mono', monospace;
  font-size: 0.7rem;
  color: var(--text-muted);
}

.hot-badge {
  background: linear-gradient(135deg, #F97316, #EF4444);
  color: #fff;
  padding: 3px 10px;
  border-radius: 20px;
  font-family: 'Space Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
}

.product-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 0.3rem;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.product-category {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-bottom: 0.75rem;
}

.product-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  border-top: 1px solid var(--border-light);
  padding-top: 0.75rem;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  color: var(--text-muted);
  font-size: 0.7rem;
  margin-bottom: 0.15rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-value {
  display: block;
  color: var(--text-title);
  font-weight: 600;
  font-size: 0.9rem;
}

.stat-value.price {
  color: var(--color-orange);
}

.growth-up {
  color: var(--color-success);
}

.growth-down {
  color: var(--color-danger);
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-muted);
}

.click-hint {
  text-align: center;
  font-size: 0.75rem;
  color: var(--color-primary);
  margin-top: 0.75rem;
  opacity: 0;
  transition: opacity var(--transition);
}

.product-card:hover .click-hint {
  opacity: 1;
}

/* ========== Pagination ========== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0.35rem;
  margin-top: 1.75rem;
}

.page-btn {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.8rem;
  color: var(--text-body);
  font-size: 0.85rem;
  cursor: pointer;
  transition: all var(--transition);
  font-family: inherit;
}

.page-btn:hover:not(:disabled):not(.active) {
  border-color: var(--color-primary);
  color: var(--color-primary);
}

.page-btn.active {
  background: var(--color-primary);
  color: #fff;
  font-weight: 600;
  border-color: var(--color-primary);
}

.page-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.page-btn.ellipsis {
  border: none;
  background: transparent;
  color: var(--text-muted);
}

/* ========== Modal ========== */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
  animation: fadeInOverlay 0.2s ease;
}

@keyframes fadeInOverlay {
  from { opacity: 0; }
  to { opacity: 1; }
}

.modal-content {
  background: var(--bg-white);
  border-radius: var(--radius-xl);
  width: 90%; max-width: 800px; max-height: 85vh;
  overflow-y: auto;
  padding: 2rem;
  position: relative;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.15);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.modal-close {
  position: absolute; top: 1rem; right: 1rem;
  background: var(--bg-hover); border: none;
  color: var(--text-secondary); font-size: 1.5rem; cursor: pointer;
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--transition);
  line-height: 1;
}

.modal-close:hover { background: var(--border); color: var(--text-title); }

.modal-header { margin-bottom: 1.5rem; }
.modal-id { font-family: 'Space Mono', monospace; font-size: 0.75rem; color: var(--text-muted); }
.modal-name { font-size: 1.4rem; font-weight: 700; color: var(--text-title); margin: 0.3rem 0; }
.modal-brand { color: var(--color-primary); font-size: 0.875rem; margin-bottom: 0.5rem; }
.modal-desc { color: var(--text-secondary); font-size: 0.85rem; line-height: 1.5; }

.modal-section { margin-top: 1.5rem; }
.modal-section-title {
  font-size: 0.95rem; font-weight: 600; color: var(--text-title);
  margin-bottom: 0.75rem; padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}
.modal-chart { width: 100%; height: 250px; }
.modal-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 0.6rem; }
.modal-stat {
  background: var(--bg-page); border: 1px solid var(--border-light); border-radius: var(--radius-sm);
  padding: 0.75rem; text-align: center;
}
.modal-stat.highlight { border-color: var(--color-primary); background: var(--color-primary-bg); }
.modal-stat-label { display: block; font-size: 0.7rem; color: var(--text-secondary); margin-bottom: 0.25rem; text-transform: uppercase; letter-spacing: 0.03em; }
.modal-stat-value { display: block; font-size: 1.05rem; color: var(--text-title); font-weight: 600; }
.modal-stat-value.price { color: var(--color-orange); }
.modal-stat-value.hot { color: var(--color-primary); font-size: 1.4rem; }
.modal-stat-value.tags { font-size: 0.8rem; word-break: break-all; }
.modal-stat-value small { font-size: 0.7rem; color: var(--text-muted); font-weight: 400; }
.modal-stat.full-width { grid-column: 1 / -1; text-align: left; }

.score-breakdown { margin-top: 0.8rem; display: flex; flex-direction: column; gap: 0.4rem; }
.score-bar-row { display: flex; align-items: center; gap: 0.5rem; }
.score-label { min-width: 75px; font-size: 0.75rem; color: var(--text-secondary); }
.score-bar-bg { flex: 1; height: 8px; background: var(--border); border-radius: 4px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 4px; transition: width 0.6s ease; }
.score-bar-fill.sales { background: #4F6EF7; }
.score-bar-fill.growth { background: #8B5CF6; }
.score-bar-fill.rating { background: #F97316; }
.score-bar-fill.review { background: #22C55E; }
.score-val { min-width: 30px; font-size: 0.75rem; color: var(--text-title); text-align: right; font-family: 'Space Mono', monospace; font-weight: 600; }

/* ========== Responsive ========== */
@media (max-width: 768px) {
  .chart-row { grid-template-columns: 1fr; }
  .chart-container { height: 240px; }
  .products-grid { grid-template-columns: 1fr; }
}
</style>
