<template>
  <div class="selling-points">
    <div class="section-header">
      <h2 class="section-title">💡 卖点推荐</h2>
      <div class="filter-group">
        <select v-model="selectedCategory" class="filter-select" @change="loadSellingPoints">
          <option value="">选择品类</option>
          <option v-for="category in categories" :key="category" :value="category">
            {{ category }}
          </option>
        </select>
      </div>
    </div>

    <div class="selling-points-grid">
      <div
        v-for="(point, index) in sellingPoints"
        :key="index"
        class="selling-point-card"
      >
        <div class="point-header">
          <span class="point-priority" :class="point.priority">{{ point.priority }}</span>
          <span class="point-mentions" v-if="point.mentionCount">{{ point.mentionCount }}次提及</span>
          <span class="point-index">#{{ index + 1 }}</span>
        </div>
        <h3 class="point-pain">{{ point.painPoint }}</h3>
        <p class="point-suggestion">{{ point.suggestion }}</p>
        <p class="point-example" v-if="point.example">{{ point.example }}</p>
      </div>
    </div>

    <div class="pain-points-section" v-if="painPointStats.length > 0">
      <h3 class="section-subtitle">用户痛点统计</h3>
      <div class="pain-points-list">
        <div
          v-for="(item, index) in painPointStats"
          :key="index"
          class="pain-point-item"
        >
          <span class="pain-point-name">{{ item[0] }}</span>
          <span class="pain-point-count">{{ item[1] }}次</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getSellingPoints } from '../api'

export default {
  name: 'SellingPoints',
  data() {
    return {
      sellingPoints: [],
      painPointStats: [],
      categories: ['手机', '电脑', '服装', '美妆', '食品', '家居', '数码', '运动'],
      selectedCategory: ''
    }
  },
  async mounted() {
    await this.loadSellingPoints()
  },
  methods: {
    async loadSellingPoints() {
      try {
        const params = {}
        if (this.selectedCategory) {
          params.category = this.selectedCategory
        }
        const res = await getSellingPoints(params)
        if (res.data.code === 200) {
          this.sellingPoints = res.data.data.sellingPoints
          this.painPointStats = res.data.data.painPointStats
        }
      } catch (error) {
        console.error('加载卖点推荐失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.selling-points {
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
  color: var(--accent-green);
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
  border-color: var(--accent-green);
  outline: none;
}

.selling-points-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.selling-point-card {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.5rem;
  transition: all 0.3s ease;
}

.selling-point-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.3);
}

.point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.point-priority {
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.point-mentions {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.point-example {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-top: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255,255,255,0.03);
  border-radius: 6px;
  border-left: 3px solid var(--accent-pink);
}

.point-priority.高 {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.point-priority.中 {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border: 1px solid #f59e0b;
}

.point-index {
  font-family: 'Orbitron', sans-serif;
  color: var(--text-secondary);
}

.point-pain {
  font-size: 1.1rem;
  color: var(--accent-cyan);
  margin-bottom: 0.75rem;
}

.point-suggestion {
  color: var(--text-secondary);
  line-height: 1.6;
}

.pain-points-section {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1.5rem;
}

.section-subtitle {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--accent-purple);
  margin-bottom: 1rem;
}

.pain-points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
}

.pain-point-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: rgba(168, 85, 247, 0.1);
  border: 1px solid rgba(168, 85, 247, 0.3);
  border-radius: 20px;
  padding: 0.5rem 1rem;
}

.pain-point-name {
  color: var(--text-primary);
}

.pain-point-count {
  color: var(--accent-purple);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
}
</style>
