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
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-text">{{ tab.name }}</span>
      </button>
    </div>

    <div class="tab-content">
      <HotProducts v-if="activeTab === 'hot'" />
      <ReviewAnalysis v-if="activeTab === 'review'" />
      <SellingPoints v-if="activeTab === 'selling'" />
      <SearchProducts v-if="activeTab === 'search'" />
      <AICopywriting v-if="activeTab === 'copywriting'" />
    </div>
  </div>
</template>

<script>
import HotProducts from '../components/HotProducts.vue'
import ReviewAnalysis from '../components/ReviewAnalysis.vue'
import SellingPoints from '../components/SellingPoints.vue'
import SearchProducts from '../components/SearchProducts.vue'
import AICopywriting from '../components/AICopywriting.vue'

export default {
  name: 'Analysis',
  components: {
    HotProducts,
    ReviewAnalysis,
    SellingPoints,
    SearchProducts,
    AICopywriting
  },
  data() {
    return {
      activeTab: 'hot',
      tabs: [
        { id: 'hot', name: '爆款分析', icon: '🔥' },
        { id: 'review', name: '差评分析', icon: '💬' },
        { id: 'selling', name: '卖点推荐', icon: '💡' },
        { id: 'search', name: '相似检索', icon: '🔍' },
        { id: 'copywriting', name: 'AI文案', icon: '✨' }
      ]
    }
  }
}
</script>

<style scoped>
.analysis {
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
  background: var(--gradient-secondary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.page-subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
}

.tabs {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  justify-content: center;
  flex-wrap: wrap;
}

.tab-btn {
  background: var(--bg-card);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 1rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}

.tab-btn:hover {
  border-color: var(--accent-purple);
  box-shadow: var(--glow-purple);
}

.tab-btn.active {
  background: linear-gradient(135deg, rgba(168, 85, 247, 0.2) 0%, rgba(236, 72, 153, 0.2) 100%);
  border-color: var(--accent-purple);
  color: var(--accent-purple);
}

.tab-icon {
  font-size: 1.2rem;
}

.tab-text {
  font-weight: 500;
}

.tab-content {
  background: var(--bg-card);
  border: var(--border-glow);
  border-radius: 16px;
  padding: 2rem;
  min-height: 500px;
}
</style>
