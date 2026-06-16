<template>
  <div id="app">
    <nav class="navbar">
      <div class="navbar-brand">
        <div class="logo-container">
          <span class="logo-icon">📊</span>
          <div class="logo-glow"></div>
        </div>
        <span class="title">抖音电商竞品智能分析</span>
      </div>
      <div class="navbar-menu">
        <router-link to="/" class="nav-item">
          <span class="nav-icon">🏠</span>
          <span class="nav-text">首页</span>
        </router-link>
        <router-link to="/analysis" class="nav-item">
          <span class="nav-icon">📈</span>
          <span class="nav-text">数据分析</span>
        </router-link>
      </div>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;500;700&family=Rajdhani:wght@300;400;500;600;700&display=swap');

:root {
  --bg-primary: #0a0e17;
  --bg-secondary: #111827;
  --bg-card: #1a2332;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --accent-cyan: #00f5ff;
  --accent-purple: #a855f7;
  --accent-pink: #ec4899;
  --accent-green: #10b981;
  --gradient-primary: linear-gradient(135deg, #00f5ff 0%, #a855f7 100%);
  --gradient-secondary: linear-gradient(135deg, #ec4899 0%, #a855f7 100%);
  --glow-cyan: 0 0 20px rgba(0, 245, 255, 0.5);
  --glow-purple: 0 0 20px rgba(168, 85, 247, 0.5);
  --border-glow: 1px solid rgba(0, 245, 255, 0.3);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Rajdhani', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}

body::before {
  content: '';
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background:
    radial-gradient(ellipse at 20% 20%, rgba(0, 245, 255, 0.1) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(168, 85, 247, 0.1) 0%, transparent 50%);
  pointer-events: none;
  z-index: -1;
}

#app {
  min-height: 100vh;
}

.navbar {
  background: rgba(17, 24, 39, 0.8);
  backdrop-filter: blur(20px);
  border-bottom: var(--border-glow);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.logo-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-icon {
  font-size: 2rem;
  z-index: 1;
}

.logo-glow {
  position: absolute;
  width: 50px;
  height: 50px;
  background: var(--gradient-primary);
  border-radius: 50%;
  filter: blur(15px);
  opacity: 0.6;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  50% {
    transform: scale(1.2);
    opacity: 0.8;
  }
}

.title {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  background: var(--gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  text-shadow: 0 0 30px rgba(0, 245, 255, 0.5);
}

.navbar-menu {
  display: flex;
  gap: 1rem;
}

.nav-item {
  color: var(--text-secondary);
  text-decoration: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.nav-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 245, 255, 0.2), transparent);
  transition: left 0.5s ease;
}

.nav-item:hover::before {
  left: 100%;
}

.nav-item:hover {
  color: var(--accent-cyan);
  border-color: rgba(0, 245, 255, 0.3);
  box-shadow: var(--glow-cyan);
}

.nav-item.router-link-active {
  color: var(--accent-cyan);
  background: rgba(0, 245, 255, 0.1);
  border-color: rgba(0, 245, 255, 0.5);
}

.nav-icon {
  font-size: 1.1rem;
}

.nav-text {
  font-weight: 500;
}

.main-content {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

/* 全局滚动条样式 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--gradient-primary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--accent-cyan);
}
</style>
