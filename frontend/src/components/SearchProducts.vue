<template>
  <div class="search-products">
    <div class="section-header">
      <h2 class="section-title">相似爆款检索</h2>
    </div>

    <div class="search-box">
      <div class="search-input-wrap">
        <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="输入关键词搜索相似爆款..."
          @keyup.enter="search"
        />
      </div>
      <button class="search-btn" @click="search">
        搜索
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
            <span class="result-score">相关度 {{ product.score?.toFixed(2) }}</span>
            <span class="result-id">{{ product.productId }}</span>
          </div>
          <h4 class="result-name">{{ product.name }}</h4>
          <p class="result-category">{{ product.category }}</p>
          <p class="result-desc">{{ product.description?.substring(0, 80) }}...</p>
          <div class="result-stats">
            <div class="stat">
              <span class="stat-label">价格</span>
              <span class="stat-value price">¥{{ product.price }}</span>
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
      <svg class="empty-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        <line x1="8" y1="11" x2="14" y2="11"/>
      </svg>
      <p class="empty-text">未找到相关商品</p>
      <p class="empty-hint">试试其他关键词</p>
    </div>

    <div class="initial-state" v-else>
      <svg class="initial-icon" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <p class="initial-text">输入关键词开始搜索</p>
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

.search-box {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2rem;
}

.search-input-wrap {
  flex: 1;
  position: relative;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 1rem;
  color: var(--text-muted);
  pointer-events: none;
}

.search-input {
  width: 100%;
  background: var(--bg-page);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem 0.75rem 2.75rem;
  color: var(--text-title);
  font-size: 0.925rem;
  transition: all var(--transition);
  font-family: inherit;
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-bg);
}

.search-input::placeholder {
  color: var(--text-muted);
}

.search-btn {
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius-md);
  padding: 0.75rem 1.75rem;
  color: #fff;
  font-size: 0.925rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition);
  font-family: inherit;
}

.search-btn:hover {
  background: #3D5BD9;
  box-shadow: 0 4px 12px rgba(79, 110, 247, 0.3);
}

.results-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 1rem;
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.result-card {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  transition: all var(--transition);
}

.result-card:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--border);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.6rem;
}

.result-score {
  background: var(--color-primary-bg);
  color: var(--color-primary);
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
  font-family: 'Space Mono', monospace;
}

.result-id {
  font-family: 'Space Mono', monospace;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.result-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 0.3rem;
}

.result-category {
  color: var(--color-primary);
  font-size: 0.8rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.result-desc {
  color: var(--text-secondary);
  font-size: 0.8rem;
  line-height: 1.5;
  margin-bottom: 0.75rem;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.result-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
  border-top: 1px solid var(--border);
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
  font-size: 0.85rem;
}

.stat-value.price {
  color: var(--color-orange);
}

.empty-state {
  text-align: center;
  padding: 3rem;
}

.empty-icon {
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.empty-text {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 0.25rem;
}

.empty-hint {
  color: var(--text-muted);
  font-size: 0.85rem;
}

.initial-state {
  text-align: center;
  padding: 4rem 2rem;
}

.initial-icon {
  color: var(--border);
  margin-bottom: 1rem;
}

.initial-text {
  color: var(--text-muted);
  font-size: 1rem;
}
</style>
