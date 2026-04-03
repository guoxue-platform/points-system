<template>
  <div class="view">
    <h2>📋 积分明细</h2>

    <div class="filters">
      <input v-model="filterTarget" placeholder="按人员筛选" class="input" />
      <button @click="fetchRecords" class="btn">查询</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="!records.length" class="empty">暂无记录</div>
    <div v-else>
      <div class="total">共 {{ total }} 条记录</div>
      <div class="list">
        <div v-for="r in records" :key="r.id" class="record-item">
          <div class="record-header">
            <span class="target">{{ r.target }}</span>
            <span class="points" :class="r.points > 0 ? 'pos' : 'neg'">
              {{ r.points > 0 ? '+' : '' }}{{ r.points }}
            </span>
          </div>
          <div class="record-body">
            <span class="reason">{{ r.reason }}</span>
            <span class="meta">by {{ r.proposer }} · {{ formatTime(r.created_at) }}</span>
          </div>
        </div>
      </div>
      <div class="pagination">
        <button :disabled="page <= 1" @click="page--; fetchRecords()">上一页</button>
        <span>{{ page }} / {{ totalPages }}</span>
        <button :disabled="page >= totalPages" @click="page++; fetchRecords()">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getRecords } from '../api/points'

const filterTarget = ref('')
const records = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)

const totalPages = computed(() => Math.ceil(total.value / pageSize))

async function fetchRecords() {
  loading.value = true
  try {
    const res = await getRecords({
      target: filterTarget.value || undefined,
      page: page.value,
      pageSize
    })
    const d = res.data.data
    records.value = d.records
    total.value = d.total
  } finally {
    loading.value = false
  }
}

function formatTime(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })
}

onMounted(fetchRecords)
</script>

<style scoped>
.view { padding: 16px; }
.filters { display: flex; gap: 8px; margin-bottom: 16px; }
.input { flex: 1; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; }
.btn { padding: 8px 16px; background: #1890ff; color: #fff; border: none; border-radius: 6px; cursor: pointer; }
.loading, .empty { color: #999; padding: 24px; text-align: center; }
.total { font-size: 13px; color: #888; margin-bottom: 12px; }
.list { display: flex; flex-direction: column; gap: 8px; }
.record-item {
  padding: 12px 16px;
  background: #fff;
  border: 1px solid #eee;
  border-radius: 8px;
}
.record-header { display: flex; justify-content: space-between; margin-bottom: 6px; }
.target { font-weight: 500; }
.points { font-weight: bold; font-size: 15px; }
.points.pos { color: #52c41a; }
.points.neg { color: #ff4d4f; }
.record-body { display: flex; flex-direction: column; gap: 2px; }
.reason { color: #333; font-size: 14px; }
.meta { color: #999; font-size: 12px; }
.pagination { display: flex; justify-content: center; align-items: center; gap: 12px; margin-top: 16px; }
.pagination button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 4px;
  cursor: pointer;
}
.pagination button:disabled { color: #ccc; cursor: not-allowed; }
</style>
