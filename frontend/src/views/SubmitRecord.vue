<template>
  <div class="view">
    <h2>✏️ 录入积分</h2>

    <form @submit.prevent="submit" class="form">
      <div class="field">
        <label>提议人 (proposer)</label>
        <input v-model="form.proposer" placeholder="你的名字" required />
      </div>

      <div class="field">
        <label>被评分人 (target)</label>
        <input v-model="form.target" placeholder="被评分的 Agent" required />
      </div>

      <div class="field">
        <label>分值</label>
        <div class="points-grid">
          <button
            v-for="p in POINT_OPTIONS"
            :key="p"
            type="button"
            class="point-btn"
            :class="{ selected: form.points === p }"
            @click="form.points = p"
          >{{ p > 0 ? '+' : '' }}{{ p }}</button>
        </div>
      </div>

      <div class="field">
        <label>事由 (reason)</label>
        <textarea v-model="form.reason" placeholder="简短说明积分原因" rows="3" required></textarea>
      </div>

      <div class="field">
        <label>提交人 (created_by)</label>
        <input v-model="form.createdBy" placeholder="你的名字" required />
      </div>

      <div class="field">
        <label>提交分支</label>
        <select v-model="form.branch">
          <option value="dev">dev</option>
          <option value="main">main</option>
        </select>
      </div>

      <button type="submit" class="btn-submit" :disabled="submitting">
        {{ submitting ? '提交中...' : '提交' }}
      </button>

      <div v-if="msg" class="msg" :class="msg.type">{{ msg.text }}</div>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { submitRecord } from '../api/points'

const POINT_OPTIONS = [-5, -3, -1, 1, 3, 5]

const form = ref({
  proposer: '',
  target: '',
  points: 1,
  reason: '',
  createdBy: '',
  branch: 'dev'
})

const submitting = ref(false)
const msg = ref(null)

async function submit() {
  submitting.value = true
  msg.value = null
  try {
    await submitRecord(form.value, form.value.branch)
    msg.value = { type: 'success', text: '提交成功 ✅' }
    form.value = { ...form.value, target: '', reason: '', points: 1 }
  } catch (e) {
    msg.value = { type: 'error', text: e.response?.data?.detail || '提交失败' }
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.view { padding: 16px; }
.form { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 4px; }
label { font-size: 13px; color: #666; font-weight: 500; }
input, textarea, select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}
textarea { resize: vertical; }
.points-grid { display: flex; gap: 8px; flex-wrap: wrap; }
.point-btn {
  width: 44px; height: 36px;
  border: 1px solid #ddd;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
}
.point-btn.selected { background: #1890ff; color: #fff; border-color: #1890ff; }
.btn-submit {
  padding: 10px;
  background: #52c41a;
  color: #fff;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
}
.btn-submit:disabled { background: #ccc; }
.msg { padding: 10px; border-radius: 6px; font-size: 14px; text-align: center; }
.msg.success { background: #f6ffed; border: 1px solid #b7eb8f; color: #52c41a; }
.msg.error { background: #fff2f0; border: 1px solid #ffccc7; color: #ff4d4f; }
</style>
