<template>
  <div class="selling-points">
    <div class="section-header">
      <h2 class="section-title">卖点推荐</h2>
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
          <span class="point-priority" :class="point.priority">{{ point.priority }}优先级</span>
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
  from { opacity: 0; transform: translateX(-12px); }
  to { opacity: 1; transform: translateX(0); }
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-title);
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

.selling-points-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.selling-point-card {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  transition: all var(--transition);
}

.selling-point-card:hover {
  box-shadow: var(--shadow-sm);
  border-color: var(--border);
}

.point-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.point-priority {
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 600;
}

.point-priority.高 {
  background: #FEF2F2;
  color: #EF4444;
  border: 1px solid #FECACA;
}

.point-priority.中 {
  background: #FFFBEB;
  color: #D97706;
  border: 1px solid #FDE68A;
}

.point-mentions {
  color: var(--text-muted);
  font-size: 0.8rem;
  font-family: 'Space Mono', monospace;
}

.point-index {
  color: var(--text-muted);
  font-family: 'Space Mono', monospace;
  font-size: 0.8rem;
}

.point-pain {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 0.5rem;
}

.point-suggestion {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 0.875rem;
}

.point-example {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-top: 0.75rem;
  padding: 0.6rem 0.85rem;
  background: var(--bg-white);
  border-radius: var(--radius-sm);
  border-left: 3px solid var(--color-primary);
  line-height: 1.5;
}

.pain-points-section {
  background: var(--bg-page);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-md);
  padding: 1.25rem;
}

.section-subtitle {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-title);
  margin-bottom: 1rem;
}

.pain-points-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.pain-point-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.85rem;
}

.pain-point-name {
  color: var(--text-body);
  font-size: 0.85rem;
}

.pain-point-count {
  color: var(--color-primary);
  font-family: 'Space Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
}
</style>
