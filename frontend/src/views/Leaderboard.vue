<template>
  <div class="view">
    <h2>🏆 本周积分榜</h2>
    <div class="week-badge">第 {{ data?.week_num || '—' }} 周</div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!leaderboard.length" class="empty">暂无数据</div>
    <div v-else class="leaderboard">
      <div
        v-for="(item, idx) in leaderboard"
        :key="item.target"
        class="rank-item"
        :class="{ top3: idx < 3 }"
      >
        <span class="rank">{{ idx + 1 }}</span>
        <span class="name">{{ item.target }}</span>
        <span class="points">{{ item.total_points }} 分</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getWeeklyLeaderboard } from '../api/points'

const data = ref(null)
const loading = ref(true)

const leaderboard = computed(() => data.value?.leaderboard || [])

onMounted(async () => {
  try {
    const res = await getWeeklyLeaderboard()
    data.value = res.data.data
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.view { padding: 16px; }
.week-badge {
  display: inline-block;
  background: #f0f0f0;
  border-radius: 12px;
  padding: 4px 12px;
  font-size: 13px;
  color: #666;
  margin-bottom: 16px;
}
.loading, .empty { color: #999; padding: 24px; text-align: center; }
.leaderboard { display: flex; flex-direction: column; gap: 8px; }
.rank-item {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
}
.rank-item.top3 { background: #fffbe6; border-color: #ffe58f; }
.rank {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  border-radius: 50%;
  background: #eee; font-weight: bold; font-size: 13px;
}
.top3 .rank { background: #ffc53d; color: #fff; }
.name { flex: 1; font-weight: 500; }
.points { color: #fa8c16; font-weight: bold; }
</style>
