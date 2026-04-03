<template>
  <div class="view">
    <h2>📦 历史归档</h2>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!weeks.length" class="empty">暂无归档记录</div>
    <div v-else class="weeks">
      <div v-for="w in weeks" :key="w.week_num" class="week-block">
        <div class="week-header">第 {{ w.week_num }} 周</div>
        <div class="leaderboard">
          <div v-for="(item, idx) in w.leaderboard" :key="item.target" class="rank-item">
            <span class="rank">{{ idx + 1 }}</span>
            <span class="name">{{ item.target }}</span>
            <span class="points">{{ item.total_points }} 分</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getHistory } from '../api/points'

const weeks = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await getHistory()
    weeks.value = res.data.data.weeks
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.view { padding: 16px; }
.loading, .empty { color: #999; padding: 24px; text-align: center; }
.weeks { display: flex; flex-direction: column; gap: 20px; }
.week-block { background: #fafafa; border-radius: 8px; overflow: hidden; }
.week-header {
  background: #1890ff; color: #fff;
  padding: 8px 16px; font-weight: bold; font-size: 14px;
}
.leaderboard { padding: 8px; display: flex; flex-direction: column; gap: 4px; }
.rank-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 12px; background: #fff; border-radius: 6px;
}
.rank { width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #eee; font-size: 12px; font-weight: bold; }
.name { flex: 1; }
.points { color: #fa8c16; font-weight: bold; }
</style>
