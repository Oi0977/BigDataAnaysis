<template>
  <div id="app">
    <nav class="sidebar">
      <div class="sidebar-header">
        <div class="logo">
          <span class="logo-icon">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <rect width="28" height="28" rx="8" fill="#4F6EF7"/>
              <path d="M7 14L11 18L21 10" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </span>
          <span class="logo-text">竞品智能分析</span>
        </div>
      </div>
      <div class="sidebar-nav">
        <router-link to="/" class="nav-item">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="7" height="7" rx="1"/>
            <rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/>
            <rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          <span>数据概览</span>
        </router-link>
        <router-link to="/analysis" class="nav-item">
          <svg class="nav-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="22,12 18,12 15,21 9,3 6,12 2,12"/>
          </svg>
          <span>数据分析</span>
        </router-link>
      </div>
      <div class="sidebar-footer">
        <div class="sidebar-badge">
          <span class="badge-dot"></span>
          <span>大数据平台 v1.0</span>
        </div>
      </div>
    </nav>
    <main class="main-area">
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
/* ===== Design System: Professional E-commerce Analytics ===== */

:root {
  /* Colors */
  --color-primary: #4F6EF7;
  --color-primary-light: #7B93FF;
  --color-primary-bg: #EEF1FE;
  --color-success: #22C55E;
  --color-success-bg: #ECFDF5;
  --color-warning: #F59E0B;
  --color-warning-bg: #FFFBEB;
  --color-danger: #EF4444;
  --color-danger-bg: #FEF2F2;
  --color-orange: #F97316;

  /* Neutrals */
  --bg-page: #F5F6FA;
  --bg-white: #FFFFFF;
  --bg-hover: #F8F9FC;
  --border: #E8ECF1;
  --border-light: #F0F2F5;

  /* Text */
  --text-title: #1A2138;
  --text-body: #4A5568;
  --text-secondary: #8492A6;
  --text-muted: #B0BEC5;

  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.06);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.05), 0 2px 4px rgba(0,0,0,0.04);
  --shadow-lg: 0 10px 25px rgba(0,0,0,0.06), 0 4px 10px rgba(0,0,0,0.04);

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --radius-xl: 20px;

  /* Transitions */
  --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'DM Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-page);
  color: var(--text-body);
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
  position: relative;
}

/* ===== Sidebar ===== */
.sidebar {
  width: 220px;
  background: var(--bg-white);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  padding: 1.5rem 1.25rem;
  border-bottom: 1px solid var(--border-light);
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.logo-text {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-title);
  letter-spacing: -0.01em;
}

.sidebar-nav {
  padding: 0.75rem;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.7rem 1rem;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.925rem;
  font-weight: 500;
  transition: all var(--transition);
}

.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text-title);
}

.nav-item.router-link-active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.nav-icon {
  flex-shrink: 0;
}

.sidebar-footer {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border-light);
}

.sidebar-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--color-success);
  animation: dotPulse 2s ease infinite;
}

@keyframes dotPulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ===== Main Area ===== */
.main-area {
  margin-left: 220px;
  width: calc(100vw - 220px);
  min-height: 100vh;
  padding: 1.75rem 2rem;
}

/* ===== Global Scrollbar ===== */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: var(--text-muted);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .sidebar {
    width: 60px;
  }
  .logo-text,
  .nav-item span,
  .sidebar-badge span:last-child {
    display: none;
  }
  .sidebar-header {
    padding: 1rem 0.5rem;
    display: flex;
    justify-content: center;
  }
  .nav-item {
    justify-content: center;
    padding: 0.7rem;
  }
  .main-area {
    margin-left: 60px;
    width: calc(100vw - 60px);
    padding: 1rem;
  }
}
</style>
