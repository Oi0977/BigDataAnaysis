<template>
  <div class="ai-copywriting">
    <div class="section-header">
      <h2 class="section-title">✨ AI文案生成</h2>
    </div>

    <div class="copywriting-form">
      <div class="form-group">
        <label class="form-label">商品ID</label>
        <input
          v-model="form.productId"
          type="text"
          class="form-input"
          placeholder="输入商品ID，如 P000001"
        />
      </div>

      <div class="form-group">
        <label class="form-label">文案风格</label>
        <div class="style-options">
          <button
            v-for="style in styles"
            :key="style.value"
            :class="['style-btn', { active: form.style === style.value }]"
            @click="form.style = style.value"
          >
            <span class="style-icon">{{ style.icon }}</span>
            <span class="style-name">{{ style.name }}</span>
          </button>
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">特殊要求（可选）</label>
        <textarea
          v-model="form.requirements"
          class="form-textarea"
          placeholder="输入特殊要求，如：突出产品性价比、强调售后保障..."
          rows="3"
        ></textarea>
      </div>

      <div class="form-group">
        <label class="form-label">生成数量</label>
        <select v-model="form.count" class="form-select">
          <option :value="1">1条</option>
          <option :value="2">2条</option>
          <option :value="3">3条</option>
          <option :value="5">5条</option>
        </select>
      </div>

      <button class="generate-btn" @click="generate" :disabled="loading">
        <span v-if="loading" class="loading-spinner"></span>
        <span v-else class="btn-icon">✨</span>
        <span class="btn-text">{{ loading ? '生成中...' : '生成文案' }}</span>
      </button>
    </div>

    <div class="copywriting-results" v-if="copywritingList.length > 0">
      <h3 class="results-title">生成结果</h3>
      <div class="results-list">
        <div
          v-for="item in copywritingList"
          :key="item.id"
          class="result-card"
        >
          <div class="result-header">
            <span class="result-index">#{{ item.id }}</span>
            <span class="result-style">{{ getStyleName(item.style) }}</span>
          </div>
          <div class="result-content">{{ item.content }}</div>
          <div class="result-actions">
            <button class="action-btn" @click="copyContent(item.content)">
              📋 复制
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { generateCopywriting } from '../api'

export default {
  name: 'AICopywriting',
  data() {
    return {
      form: {
        productId: '',
        style: 'professional',
        requirements: '',
        count: 3
      },
      styles: [
        { value: 'professional', name: '专业', icon: '💼' },
        { value: 'casual', name: '轻松', icon: '😊' },
        { value: 'emotional', name: '情感', icon: '❤️' }
      ],
      copywritingList: [],
      loading: false
    }
  },
  methods: {
    async generate() {
      if (!this.form.productId.trim()) {
        alert('请输入商品ID')
        return
      }

      this.loading = true
      try {
        const res = await generateCopywriting({
          product_id: this.form.productId,
          style: this.form.style,
          requirements: this.form.requirements || null,
          count: this.form.count
        })

        if (res.data.code === 200) {
          this.copywritingList = res.data.data.copywritingList
        } else {
          alert(res.data.message)
        }
      } catch (error) {
        console.error('生成文案失败:', error)
        alert('生成文案失败，请重试')
      } finally {
        this.loading = false
      }
    },
    getStyleName(value) {
      const style = this.styles.find(s => s.value === value)
      return style ? style.name : value
    },
    async copyContent(content) {
      try {
        await navigator.clipboard.writeText(content)
        alert('已复制到剪贴板')
      } catch (error) {
        console.error('复制失败:', error)
      }
    }
  }
}
</script>

<style scoped>
.ai-copywriting {
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
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.copywriting-form {
  background: var(--bg-secondary);
  border: var(--border-glow);
  border-radius: 12px;
  padding: 2rem;
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-label {
  display: block;
  color: var(--accent-cyan);
  font-family: 'Orbitron', sans-serif;
  font-size: 0.9rem;
  margin-bottom: 0.75rem;
}

.form-input,
.form-textarea,
.form-select {
  width: 100%;
  background: var(--bg-primary);
  border: var(--border-glow);
  border-radius: 8px;
  padding: 1rem;
  color: var(--text-primary);
  font-family: 'Rajdhani', sans-serif;
  font-size: 1rem;
  transition: all 0.3s ease;
}

.form-input:focus,
.form-textarea:focus,
.form-select:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.2);
}

.form-textarea {
  resize: vertical;
  min-height: 80px;
}

.style-options {
  display: flex;
  gap: 1rem;
}

.style-btn {
  flex: 1;
  background: var(--bg-primary);
  border: var(--border-glow);
  border-radius: 8px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-secondary);
}

.style-btn:hover {
  border-color: var(--accent-purple);
}

.style-btn.active {
  background: rgba(168, 85, 247, 0.2);
  border-color: var(--accent-purple);
  color: var(--accent-purple);
}

.style-icon {
  font-size: 1.5rem;
}

.style-name {
  font-weight: 500;
}

.generate-btn {
  width: 100%;
  background: var(--gradient-primary);
  border: none;
  border-radius: 8px;
  padding: 1rem 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.generate-btn:hover:not(:disabled) {
  transform: scale(1.02);
  box-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
}

.generate-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-icon {
  font-size: 1.2rem;
}

.btn-text {
  font-family: 'Rajdhani', sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: white;
}

.loading-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid transparent;
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.results-title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--accent-cyan);
  margin-bottom: 1.5rem;
}

.results-list {
  display: flex;
  flex-direction: column;
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
  border-color: var(--accent-purple);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.result-index {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.2rem;
  color: var(--accent-cyan);
}

.result-style {
  background: rgba(168, 85, 247, 0.2);
  color: var(--accent-purple);
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.8rem;
}

.result-content {
  color: var(--text-primary);
  line-height: 1.8;
  white-space: pre-wrap;
  margin-bottom: 1rem;
  padding: 1rem;
  background: var(--bg-primary);
  border-radius: 8px;
}

.result-actions {
  display: flex;
  justify-content: flex-end;
}

.action-btn {
  background: rgba(0, 245, 255, 0.1);
  border: 1px solid rgba(0, 245, 255, 0.3);
  border-radius: 8px;
  padding: 0.5rem 1rem;
  color: var(--accent-cyan);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.action-btn:hover {
  background: rgba(0, 245, 255, 0.2);
  box-shadow: 0 0 15px rgba(0, 245, 255, 0.3);
}
</style>
