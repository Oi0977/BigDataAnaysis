<template>
  <div class="analysis">
    <div class="page-header">
      <h1 class="page-title">数据分析</h1>
      <p class="page-subtitle">深度洞察电商数据</p>
    </div>

    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['tab-btn', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        <span class="tab-text">{{ tab.name }}</span>
      </button>
    </div>

    <div class="tab-content">
      <HotProducts v-if="activeTab === 'hot'" />
      <ReviewAnalysis v-if="activeTab === 'review'" />
      <SellingPoints v-if="activeTab === 'selling'" />
      <SearchProducts v-if="activeTab === 'search'" />
    </div>
  </div>
</template>

<script>
import HotProducts from '../components/HotProducts.vue'
import ReviewAnalysis from '../components/ReviewAnalysis.vue'
import SellingPoints from '../components/SellingPoints.vue'
import SearchProducts from '../components/SearchProducts.vue'

export default {
  name: 'Analysis',
  components: {
    HotProducts,
    ReviewAnalysis,
    SellingPoints,
    SearchProducts
  },
  data() {
    return {
      activeTab: 'hot',
      tabs: [
        { id: 'hot', name: '爆款分析' },
        { id: 'review', name: '差评分析' },
        { id: 'selling', name: '卖点推荐' },
        { id: 'search', name: '相似检索' }
      ]
    }
  }
}
</script>

<style scoped>
.analysis {
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

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0;
}

.tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  padding: 0.85rem 1.25rem;
  cursor: pointer;
  transition: all var(--transition);
  color: var(--text-secondary);
  font-size: 0.925rem;
  font-weight: 500;
  font-family: inherit;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: var(--text-title);
}

.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
  font-weight: 600;
}

.tab-content {
  background: var(--bg-white);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 1.75rem;
  min-height: 500px;
}
</style>
