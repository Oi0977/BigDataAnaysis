<template>
  <div class="hot-products">
    <div class="section-header">
      <h2 class="section-title">🔥 爆款分析</h2>
      <div class="filter-group">
        <select v-model="selectedCategory" class="filter-select" @change="loadProducts">
          <option value="">全部品类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </div>
    </div>

    <div class="products-grid">
      <div
        v-for="product in products"
        :key="product.product_id"
        class="product-card"
      >
        <div class="product-header">
          <span class="product-id">{{ product.product_id }}</span>
          <span class="hot-score">{{ product.hot_score.toFixed(0) }}</span>
        </div>
        <h3 class="product-name">{{ product.name }}</h3>
        <p class="product-category">{{ product.category }}</p>
        <div class="product-stats">
          <div class="stat">
            <span class="stat-label">价格</span>
            <span class="stat-value">¥{{ product.price }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">销量</span>
            <span class="stat-value">{{ product.sales }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">评分</span>
            <span class="stat-value">{{ product.rating }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getHotProducts } from '../api'

export default {
  name: 'HotProducts',
  data() {
    return {
      products: [],
      categories: ['手机', '电脑', '服装', '美妆', '食品', '家居', '数码', '运动'],
      selectedCategory: ''
    }
  },
  async mounted() {
    await this.loadProducts()
  },
  methods: {
    async loadProducts() {
      try {
        const params = { limit: 20 }
        if (this.selectedCategory) {
          params.category = this.selectedCategory
        }
        const res = await getHotProducts(params)
        if (res.data.code === 200) {
          this.products = res.data.data.products
        }
      } catch (error) {
        console.error('加载商品失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.hot-products {
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  color: var(--accent-cyan);
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

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.product-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.product-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--gradient-primary);
}

.product-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--glow-cyan);
}

.product-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.product-id {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.hot-score {
  background: var(--gradient-primary);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  font-weight: 700;
}

.product-name {
  font-size: 1.2rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.product-category {
  color: var(--accent-purple);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.product-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.stat {
  text-align: center;
}

.stat-label {
  display: block;
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.stat-value {
  display: block;
  color: var(--accent-cyan);
  font-weight: 600;
}
</style>
