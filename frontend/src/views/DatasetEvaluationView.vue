<template>
  <div class="dataset-eval-page">
    <header class="page-header">
      <h1>Dataset description &amp; evaluation plan</h1>
      <p class="lead">
        Canonical Markdown:
        <code>docs/DATASET_AND_EVALUATION.md</code>
        — rendered below for quick reading inside the app.
      </p>
    </header>

    <section class="per-subject-panel">
      <h2>Per-subject dataset description</h2>
      <p class="panel-hint">
        Stored on the server with each knowledge base. Use it for course reports: corpus sources,
        languages, exam materials, privacy constraints, and evaluation goals specific to that subject.
        You can also edit this field on the subject’s <strong>Documents &amp; Exams</strong> page.
      </p>
      <div v-if="subjectStore.subjects.length === 0" class="empty-hint">
        No subjects yet. Create a knowledge base from Home, then return here to add notes.
      </div>
      <template v-else>
        <el-form label-position="top" class="subject-form">
          <el-form-item label="Subject">
            <el-select
              v-model="selectedSubjectId"
              placeholder="Select a subject"
              filterable
              style="width: 100%"
            >
              <el-option
                v-for="s in subjectStore.subjects"
                :key="s.subject_id"
                :label="s.name"
                :value="s.subject_id"
              />
            </el-select>
          </el-form-item>
          <el-form-item label="Dataset description (this subject)">
            <el-input
              v-model="subjectDatasetDraft"
              type="textarea"
              :rows="8"
              maxlength="20000"
              show-word-limit
              placeholder="Describe documents, labeling, evaluation scope, and retention constraints for this knowledge base..."
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="subjectSaving" @click="saveSubjectDataset">
              Save subject notes
            </el-button>
          </el-form-item>
        </el-form>
      </template>
    </section>

    <el-divider />

    <article class="markdown-body" v-html="rendered" />
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { marked } from 'marked'
import { ElMessage } from 'element-plus'
import rawMarkdown from '../../../docs/DATASET_AND_EVALUATION.md?raw'
import { useSubjectStore } from '../modules/subjects/store/subjectStore'

marked.setOptions({
  gfm: true,
  breaks: false
})

const subjectStore = useSubjectStore()
const selectedSubjectId = ref('')
const subjectDatasetDraft = ref('')
const subjectSaving = ref(false)

const rendered = computed(() => marked.parse(rawMarkdown))

onMounted(async () => {
  try {
    await subjectStore.loadSubjects()
    if (subjectStore.subjects.length && !selectedSubjectId.value) {
      selectedSubjectId.value = subjectStore.subjects[0].subject_id
    }
  } catch {
    ElMessage.error('Failed to load subjects')
  }
})

watch(
  () => subjectStore.subjects,
  (list) => {
    if (!list.length) {
      selectedSubjectId.value = ''
      subjectDatasetDraft.value = ''
      return
    }
    if (!selectedSubjectId.value || !list.some((s) => s.subject_id === selectedSubjectId.value)) {
      selectedSubjectId.value = list[0].subject_id
    }
  },
  { deep: true }
)

watch(
  () => selectedSubjectId.value,
  (id) => {
    if (!id) {
      subjectDatasetDraft.value = ''
      return
    }
    const row = subjectStore.subjects.find((s) => s.subject_id === id)
    subjectDatasetDraft.value = row?.dataset_description ?? ''
  },
  { immediate: true }
)

async function saveSubjectDataset() {
  const id = selectedSubjectId.value
  if (!id) return
  subjectSaving.value = true
  try {
    await subjectStore.updateSubject(id, { dataset_description: subjectDatasetDraft.value })
    ElMessage.success('Dataset description saved')
  } catch {
    ElMessage.error('Save failed')
  } finally {
    subjectSaving.value = false
  }
}
</script>

<style scoped>
.dataset-eval-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 32px 24px 64px;
  color: var(--text-primary, #303133);
  font-family: var(--font-sans, system-ui, sans-serif);
}

.page-header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle, #e4e7ed);
}

.page-header h1 {
  margin: 0 0 12px;
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.lead {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-secondary, #606266);
}

.lead code {
  font-size: 13px;
  padding: 2px 6px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
}

.per-subject-panel {
  margin-bottom: 24px;
}

.per-subject-panel h2 {
  margin: 0 0 8px;
  font-size: 1.15rem;
  font-weight: 600;
  color: var(--color-accent, #da7756);
}

.panel-hint {
  margin: 0 0 16px;
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-secondary, #606266);
}

.empty-hint {
  font-size: 14px;
  color: var(--text-tertiary, #909399);
}

.subject-form {
  max-width: 100%;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.4em;
  margin-bottom: 0.6em;
  font-weight: 600;
  line-height: 1.35;
}

.markdown-body :deep(h1) {
  font-size: 1.35rem;
}

.markdown-body :deep(h2) {
  font-size: 1.15rem;
  color: var(--color-accent, #da7756);
}

.markdown-body :deep(h3) {
  font-size: 1.05rem;
}

.markdown-body :deep(p),
.markdown-body :deep(li) {
  font-size: 14px;
  line-height: 1.65;
  color: var(--text-secondary, #606266);
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.35rem;
}

.markdown-body :deep(li + li) {
  margin-top: 0.35em;
}

.markdown-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin: 1em 0;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid var(--border-subtle, #e4e7ed);
  padding: 8px 10px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: rgba(218, 119, 86, 0.08);
  font-weight: 600;
  color: var(--text-primary, #303133);
}

.markdown-body :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-subtle, #e4e7ed);
  margin: 2rem 0;
}

.markdown-body :deep(code) {
  font-family: ui-monospace, monospace;
  font-size: 12px;
  padding: 2px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.06);
}

.markdown-body :deep(pre) {
  overflow-x: auto;
  padding: 12px 14px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.04);
  margin: 1em 0;
}

.markdown-body :deep(pre code) {
  padding: 0;
  background: none;
  font-size: 12px;
}

.markdown-body :deep(blockquote) {
  margin: 1em 0;
  padding: 8px 14px;
  border-left: 4px solid var(--color-accent, #da7756);
  background: rgba(218, 119, 86, 0.06);
  color: var(--text-secondary, #606266);
}

.markdown-body :deep(a) {
  color: var(--color-accent, #da7756);
  text-decoration: none;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

.markdown-body :deep(strong) {
  color: var(--text-primary, #303133);
}
</style>
