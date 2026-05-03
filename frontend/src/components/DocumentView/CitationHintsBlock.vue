<template>
  <div v-if="hasContent" class="citation-panel">
    <el-collapse>
      <el-collapse-item title="引用可信度与冲突提示" name="citation">
        <div v-for="(h, i) in (data.hints || [])" :key="'h' + i" class="citation-hint">{{ h }}</div>
        <div v-if="(data.conflicts || []).length" class="citation-subtitle">潜在冲突</div>
        <el-alert
          v-for="(c, j) in (data.conflicts || [])"
          :key="'c' + j"
          type="warning"
          :closable="false"
          class="citation-alert"
          :title="c.entity_label || '实体'"
          :description="c.message"
        />
        <div v-if="(data.citations || []).length" class="citation-subtitle">检索块可信度</div>
        <div v-for="(ci, k) in (data.citations || []).slice(0, 8)" :key="'ci' + k" class="citation-row">
          <el-tag :type="trustTag(ci.trust)" size="small">{{ trustText(ci.trust) }}</el-tag>
          <span class="citation-preview">#{{ ci.rank }} {{ ci.preview }}</span>
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: null }
})

const hasContent = computed(() => {
  const d = props.data
  if (!d || typeof d !== 'object') return false
  const h = d.hints?.length
  const c = d.conflicts?.length
  const t = d.citations?.length
  return !!(h || c || t)
})

function trustText(t) {
  const m = { high: '可信较高', medium: '中等', low: '较低' }
  return m[t] || t || '—'
}

function trustTag(t) {
  const m = { high: 'success', medium: 'warning', low: 'info' }
  return m[t] || 'info'
}
</script>

<style scoped>
.citation-panel {
  margin-top: 10px;
  border-top: 1px solid #ebeef5;
  padding-top: 8px;
}
.citation-hint {
  font-size: 13px;
  color: #606266;
  margin-bottom: 6px;
  line-height: 1.5;
}
.citation-subtitle {
  font-size: 12px;
  font-weight: 600;
  color: #909399;
  margin: 10px 0 6px;
}
.citation-alert {
  margin-bottom: 8px;
}
.citation-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  margin-bottom: 6px;
}
.citation-preview {
  color: #606266;
  line-height: 1.45;
  word-break: break-word;
}
</style>
