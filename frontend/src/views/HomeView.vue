<template>
  <div class="subjects-dashboard">
    <!-- 顶部标题区 -->
    <header class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><Collection /></el-icon>
          Knowledge Bases
        </h2>
        <p class="page-subtitle">Select a subject to manage documents or start a conversation.</p>
      </div>
      <div class="header-right">
        <el-button 
          type="primary" 
          size="large" 
          round
          class="new-subject-btn"
          @click="createNewSubject"
          :loading="subjectStore.loading"
        >
          <el-icon><Plus /></el-icon>
          New Subject
        </el-button>
      </div>
    </header>

    <!-- 学科列表区域 -->
    <section class="subjects-section">
      <div v-if="subjectStore.loading && subjectStore.subjects.length === 0" class="loading-state">
        <el-skeleton :rows="3" animated count="3" class="skeleton-card" />
      </div>

      <div v-else-if="subjectStore.subjects.length === 0" class="empty-state">
        <el-empty description="No subjects yet. Create one to get started." :image-size="160">
          <el-button type="primary" @click="createNewSubject">Create First Subject</el-button>
        </el-empty>
      </div>

      <div v-else class="subjects-grid">
        <div 
          v-for="subject in subjectStore.subjects" 
          :key="subject.subject_id" 
          class="subject-card"
          @click="enterSubject(subject)"
        >
          <div class="card-icon">
            {{ getSubjectIcon(subject.name) }}
          </div>
          
          <div class="card-content">
            <h3 class="subject-title" :title="subject.name">{{ subject.name }}</h3>
            <div class="subject-meta">
              <el-tag size="small" type="info" effect="plain" round>{{ getDocCount(subject.subject_id) }} Docs</el-tag>
              <span class="date">{{ formatDate(subject.created_at) }}</span>
            </div>
          </div>

          <div class="card-actions" @click.stop>
            <el-dropdown trigger="click" @command="(cmd) => handleSubjectCommand(cmd, subject)" @click.stop>
              <el-button link type="info" class="more-btn">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">
                    Rename
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    Delete
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Collection, Plus, MoreFilled } from '@element-plus/icons-vue'
import { useSubjectStore } from '../modules/subjects/store/subjectStore'
import { useDocumentStore } from '../modules/documents/store/documentStore'

const router = useRouter()
const subjectStore = useSubjectStore()
const docStore = useDocumentStore()

onMounted(async () => {
  await subjectStore.loadSubjects()
  await Promise.all(subjectStore.subjects.map(s => docStore.loadDocumentsForSubject(s.subject_id)))
})

const getDocCount = (subjectId) => docStore.getDocumentCountBySubject(subjectId)

const createNewSubject = async () => {
  const { value: title } = await ElMessageBox.prompt('Please enter the subject name', 'New Subject', {
    confirmButtonText: 'Create',
    cancelButtonText: 'Cancel',
    inputPattern: /\S+/,
    inputErrorMessage: 'Name cannot be empty'
  }).catch(() => ({ value: null }))
  
  if (!title) {
    return
  }

  const subject = await subjectStore.createSubject(title)
  ElMessage.success('Subject created')
  enterSubject(subject)
}

const enterSubject = (subject) => {
  subjectStore.selectSubject(subject.subject_id)
  router.push(`/subject/${subject.subject_id}`)
}

const getSubjectIcon = (title) => {
  const firstChar = title ? title.charAt(0).toUpperCase() : 'S'
  return firstChar
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString()
}

const handleSubjectCommand = async (action, subject) => {
  if (action === 'rename') {
    const { value: newName } = await ElMessageBox.prompt('Enter a new subject name', 'Rename subject', {
      confirmButtonText: 'OK',
      cancelButtonText: 'Cancel',
      inputValue: subject.name || '',
      inputPattern: /\S+/,
      inputErrorMessage: 'Name cannot be empty'
    }).catch(() => ({ value: null }))
    
    if (!newName) {
      return
    }
    
    try {
      await subjectStore.updateSubject(subject.subject_id, { name: newName })
      ElMessage.success('Subject renamed')
    } catch (error) {
      console.error('重命名失败:', error)
      ElMessage.error('Rename failed')
    }
  } else if (action === 'delete') {
    await ElMessageBox.confirm(
      'This permanently deletes the subject, its documents, conversations, and history. Continue?',
      'Delete subject',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    ).catch(() => {})
    
    try {
      await subjectStore.deleteSubject(subject.subject_id)
      ElMessage.success('Subject deleted')
    } catch (error) {
      console.error('删除失败:', error)
      ElMessage.error('Delete failed')
    }
  }
}
</script>

<style scoped>
.subjects-dashboard {
  max-width: 1000px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 40px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-title {
  font-family: var(--font-serif);
  font-size: 32px;
  font-weight: 700;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.page-subtitle {
  font-family: var(--font-sans);
  color: var(--text-secondary);
  font-size: 16px;
}

.new-subject-btn {
  background-color: var(--color-accent);
  border-color: var(--color-accent);
}

.new-subject-btn:hover {
  background-color: var(--color-accent-hover);
  border-color: var(--color-accent-hover);
}

/* Grid */
.subjects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.subject-card {
  background-color: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.subject-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-float);
  border-color: var(--color-accent);
}

.card-icon {
  width: 56px;
  height: 56px;
  background-color: var(--color-accent-light);
  color: var(--color-accent);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-serif);
  font-size: 24px;
  font-weight: 700;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
  overflow: hidden;
}

.subject-title {
  font-family: var(--font-sans);
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subject-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 13px;
  color: var(--text-tertiary);
}

.card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.subject-card:hover .card-actions {
  opacity: 1;
}

.more-btn {
  color: var(--text-tertiary);
  padding: 4px;
  font-size: 18px;
}

.more-btn:hover {
  color: var(--text-primary);
  background-color: var(--bg-hover);
}
</style>
