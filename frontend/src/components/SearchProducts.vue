<template>
  <div class="search-products">
    <div class="section-header">
      <h2 class="section-title">🔍 相似爆款检索</h2>
    </div>

    <div class="search-box">
      <input
        v-model="searchQuery"
        type="text"
        class="search-input"
        placeholder="输入关键词搜索相似爆款..."
        @keyup.enter="search"
      />
      <button class="search-btn" @click="search">
        <span class="btn-icon">🔍</span>
        <span class="btn-text">搜索</span>
      </button>
    </div>

    <div class="search-results" v-if="products.length > 0">
      <h3 class="results-title">搜索结果 ({{ products.length }}条)</h3>
      <div class="results-grid">
        <div
          v-for="product in products"
          :key="product.productId"
          class="result-card"
        >
          <div class="result-header">
            <span class="result-score">相关度: {{ product.score?.toFixed(2) }}</span>
            <span class="result-id">{{ product.productId }}</span>
          </div>
          <h4 class="result-name">{{ product.name }}</h4>
          <p class="result-category">{{ product.category }}</p>
          <p class="result-desc">{{ product.description?.substring(0, 60) }}...</p>
          <div class="result-stats">
            <div class="stat">
              <span class="stat-label">价格</span>
              <span class="stat-value">¥{{ product.price }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">原价</span>
              <span class="stat-value">¥{{ product.originalPrice }}</span>
            </div>
            <div class="stat">
              <span class="stat-label">店铺</span>
              <span class="stat-value">{{ product.shopName }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="empty-state" v-else-if="searched">
      <span class="empty-icon">🔍</span>
      <p class="empty-text">未找到相关商品</p>
    </div>
  </div>
</template>

<script>
import { searchProducts } from '../api'

export default {
  name: 'SearchProducts',
  data() {
    return {
      searchQuery: '',
      products: [],
      searched: false
    }
  },
  methods: {
    async search() {
      if (!this.searchQuery.trim()) return

      try {
        const res = await searchProducts(this.searchQuery)
        if (res.data.code === 200) {
          this.products = res.data.data.products
          this.searched = true
        }
      } catch (error) {
        console.error('搜索失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.search-products {
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
  color: var(--accent-pink);
}

.search-box {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
}

.search-input {
  flex: 1;
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  color: var(--text-primary);
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  transition: all 0.3s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--accent-pink);
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.search-btn {
  background: var(--gradient-secondary);
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.search-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.5);
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-text {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: white;
}

.results-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--accent-cyan);
  margin-bottom: 1.5rem;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.result-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.result-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 0 20px rgba(236, 72, 153, 0.3);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.result-score {
  background: rgba(236, 72, 153, 0.2);
  color: var(--accent-pink);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
}

.result-id {
  font-family: 'Orbitron', sans-serif;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.result-name {
  font-size: 1.2rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.result-category {
  color: var(--accent-purple);
  font-size: 0.9rem;
  margin-bottom: 0.5rem;
}

.result-desc {
  color: var(--text-secondary);
  font-size: 0.85rem;
  line-height: 1.5;
  margin-bottom: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-stats {
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

.empty-state {
  text-align: center;
  padding: 3rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
  display: block;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 1.2rem;
}
</style>
