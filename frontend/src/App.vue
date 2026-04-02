<template>
  <div class="app">
    <header class="header">
      <h1>🏅 本周高光</h1>
    </header>

    <nav class="tabs">
      <button
        v-for="tab in TABS"
        :key="tab.key"
        :class="{ active: currentTab === tab.key }"
        @click="currentTab = tab.key"
      >{{ tab.label }}</button>
    </nav>

    <main class="content">
      <Leaderboard v-if="currentTab === 'leaderboard'" />
      <Records v-else-if="currentTab === 'records'" />
      <History v-else-if="currentTab === 'history'" />
      <SubmitRecord v-else-if="currentTab === 'submit'" />
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import Leaderboard from './views/Leaderboard.vue'
import Records from './views/Records.vue'
import History from './views/History.vue'
import SubmitRecord from './views/SubmitRecord.vue'

const TABS = [
  { key: 'leaderboard', label: '🏆 积分榜' },
  { key: 'records', label: '📋 明细' },
  { key: 'history', label: '📦 历史' },
  { key: 'submit', label: '✏️ 录入' }
]

const currentTab = ref('leaderboard')
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }
.app { min-height: 100vh; }
.header {
  background: #1890ff;
  color: #fff;
  padding: 16px 20px;
}
.header h1 { font-size: 18px; font-weight: 600; }
.tabs {
  display: flex;
  background: #fff;
  border-bottom: 1px solid #eee;
  position: sticky;
  top: 0;
}
.tabs button {
  flex: 1;
  padding: 12px;
  border: none;
  background: none;
  font-size: 14px;
  cursor: pointer;
  color: #666;
  border-bottom: 2px solid transparent;
}
.tabs button.active {
  color: #1890ff;
  border-bottom-color: #1890ff;
}
.content { padding-bottom: 24px; }
</style>
