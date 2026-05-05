<template>
  <div class="flashcard-page">
    <!-- Header -->
    <header class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon><Memo /></el-icon>
          Flashcards
        </h2>
        <p class="page-subtitle">Spaced-repetition study for <strong>{{ subjectName }}</strong></p>
      </div>
      <div class="header-right">
        <el-button
          v-if="!studyMode"
          type="primary"
          :loading="store.generating"
          :disabled="store.generating"
          round
          @click="generateCards"
        >
          <el-icon><MagicStick /></el-icon>
          Generate Cards
        </el-button>
        <el-button
          v-if="!studyMode && store.cards.length > 0"
          type="success"
          round
          @click="startStudy"
        >
          <el-icon><VideoPlay /></el-icon>
          Study Now ({{ store.stats.due }} due)
        </el-button>
        <el-button v-if="studyMode" plain round @click="exitStudy">
          Exit Study
        </el-button>
      </div>
    </header>

    <!-- Stats row -->
    <div v-if="!studyMode" class="stats-row">
      <div class="stat-chip total">
        <span class="stat-num">{{ store.stats.total }}</span>
        <span class="stat-label">Total</span>
      </div>
      <div class="stat-chip due">
        <span class="stat-num">{{ store.stats.due }}</span>
        <span class="stat-label">Due Today</span>
      </div>
      <div class="stat-chip mastered">
        <span class="stat-num">{{ store.stats.mastered }}</span>
        <span class="stat-label">Mastered</span>
      </div>
      <div class="stat-chip new-card">
        <span class="stat-num">{{ store.stats.new }}</span>
        <span class="stat-label">New</span>
      </div>
    </div>

    <!-- Loading skeleton -->
    <div v-if="store.loading" class="skeleton-area">
      <el-skeleton :rows="4" animated />
    </div>

    <!-- Study Mode -->
    <div v-else-if="studyMode" class="study-area">
      <div class="study-progress">
        <span>{{ studyIndex + 1 }} / {{ studyQueue.length }}</span>
        <el-progress
          :percentage="Math.round(((studyIndex) / studyQueue.length) * 100)"
          :stroke-width="6"
          status="success"
          style="width: 200px"
        />
      </div>

      <!-- Flip Card -->
      <div class="flip-container" @click="flipped = !flipped">
        <div class="flipper" :class="{ flipped }">
          <div class="card-face front">
            <div class="card-label">Question</div>
            <p class="card-text">{{ currentCard.front }}</p>
            <div class="tap-hint">Tap to reveal answer</div>
          </div>
          <div class="card-face back">
            <div class="card-label">Answer</div>
            <p class="card-text">{{ currentCard.back }}</p>
            <p v-if="currentCard.source_doc" class="card-source">
              <el-icon><Document /></el-icon> {{ currentCard.source_doc }}
            </p>
          </div>
        </div>
      </div>

      <!-- Rating buttons (only shown after flip) -->
      <transition name="fade">
        <div v-if="flipped" class="rating-buttons">
          <p class="rating-hint">How well did you know this?</p>
          <div class="rating-row">
            <el-button class="rate-btn rate-0" @click="rate(0)">
              Blackout<br><small>Complete blank</small>
            </el-button>
            <el-button class="rate-btn rate-1" @click="rate(1)">
              Again<br><small>Wrong, but familiar</small>
            </el-button>
            <el-button class="rate-btn rate-3" @click="rate(3)">
              Hard<br><small>Correct with effort</small>
            </el-button>
            <el-button class="rate-btn rate-4" @click="rate(4)">
              Good<br><small>Correct with pause</small>
            </el-button>
            <el-button class="rate-btn rate-5" @click="rate(5)">
              Easy<br><small>Perfect recall</small>
            </el-button>
          </div>
        </div>
      </transition>
    </div>

    <!-- Session complete -->
    <div v-else-if="sessionDone" class="session-done">
      <div class="done-icon">🎉</div>
      <h3>Session Complete!</h3>
      <p>You reviewed {{ studyQueue.length }} cards.</p>
      <el-button type="primary" round @click="exitStudy">Back to Cards</el-button>
    </div>

    <!-- Card Grid (browse mode) -->
    <div v-else-if="store.cards.length > 0" class="card-grid">
      <div
        v-for="card in store.cards"
        :key="card.card_id"
        class="card-tile"
        :class="{ mastered: card.repetitions >= 3 && card.last_quality >= 4 }"
      >
        <div class="tile-badge">
          <el-tag size="small" :type="cardTagType(card)">{{ cardTagLabel(card) }}</el-tag>
        </div>
        <p class="tile-front">{{ card.front }}</p>
        <p class="tile-back">{{ card.back }}</p>
        <div class="tile-footer">
          <span class="tile-source">{{ card.source_doc }}</span>
          <span class="tile-next">Next: {{ formatDate(card.next_review) }}</span>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="empty-state">
      <el-empty description="No flashcards yet." :image-size="140">
        <el-button type="primary" :loading="store.generating" @click="generateCards">
          Generate Flashcards with AI
        </el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Memo, MagicStick, VideoPlay, Document } from '@element-plus/icons-vue'
import { useFlashcardStore } from '../store/flashcardStore'
import { useSubjectStore } from '../../subjects/store/subjectStore'

const route = useRoute()
const store = useFlashcardStore()
const subjectStore = useSubjectStore()

const subjectId = computed(() => route.params.id || route.params.subjectId)
const subjectName = computed(() => {
  const s = subjectStore.subjects.find(s => s.subject_id === subjectId.value)
  return s?.name || 'this subject'
})

// Study mode state
const studyMode = ref(false)
const studyQueue = ref([])
const studyIndex = ref(0)
const flipped = ref(false)
const sessionDone = ref(false)

const currentCard = computed(() => studyQueue.value[studyIndex.value] || {})

onMounted(async () => {
  await store.loadCards(subjectId.value)
})

watch(subjectId, async (id) => {
  if (id) await store.loadCards(id)
})

async function generateCards() {
  const { value } = await ElMessageBox.prompt(
    'How many cards to generate? (5–30)',
    'Generate Flashcards',
    { inputValue: '15', confirmButtonText: 'Generate', cancelButtonText: 'Cancel' }
  ).catch(() => ({ value: null }))
  if (!value) return
  const n = Math.min(30, Math.max(5, parseInt(value) || 15))
  try {
    await store.generate(subjectId.value, n)
    ElMessage.success(`Generated ${n} new flashcards!`)
  } catch (e) {
    // error shown by api interceptor
  }
}

function startStudy() {
  const due = store.cards.filter(c => new Date(c.next_review) <= new Date())
  if (!due.length) {
    ElMessage.info('No cards due right now — great job staying ahead!')
    return
  }
  studyQueue.value = [...due]
  studyIndex.value = 0
  flipped.value = false
  sessionDone.value = false
  studyMode.value = true
}

async function rate(quality) {
  await store.reviewCard(subjectId.value, currentCard.value.card_id, quality)
  if (studyIndex.value + 1 >= studyQueue.value.length) {
    studyMode.value = false
    sessionDone.value = true
  } else {
    studyIndex.value++
    flipped.value = false
  }
}

function exitStudy() {
  studyMode.value = false
  sessionDone.value = false
  flipped.value = false
}

function cardTagType(card) {
  if (card.repetitions >= 3 && card.last_quality >= 4) return 'success'
  if (card.repetitions === 0) return 'info'
  if (new Date(card.next_review) <= new Date()) return 'warning'
  return ''
}

function cardTagLabel(card) {
  if (card.repetitions >= 3 && card.last_quality >= 4) return 'Mastered'
  if (card.repetitions === 0) return 'New'
  if (new Date(card.next_review) <= new Date()) return 'Due'
  return 'Learning'
}

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const today = new Date()
  const diff = Math.round((d - today) / 86400000)
  if (diff <= 0) return 'Today'
  if (diff === 1) return 'Tomorrow'
  return `In ${diff} days`
}
</script>

<style scoped>
.flashcard-page { max-width: 1000px; margin: 0 auto; }

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 28px;
}

.page-title {
  font-family: var(--font-serif);
  font-size: 28px;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 4px;
}

.page-subtitle { color: var(--text-secondary); font-size: 15px; }

/* Stats row */
.stats-row {
  display: flex;
  gap: 16px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.stat-chip {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 12px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 90px;
  box-shadow: var(--shadow-card);
}

.stat-num { font-size: 28px; font-weight: 700; font-family: var(--font-serif); }
.stat-label { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

.stat-chip.due .stat-num { color: #e6a23c; }
.stat-chip.mastered .stat-num { color: #67c23a; }
.stat-chip.total .stat-num { color: var(--color-accent); }

/* Study area */
.study-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  padding-top: 16px;
}

.study-progress {
  display: flex;
  align-items: center;
  gap: 16px;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 3D Flip card */
.flip-container {
  width: 580px;
  height: 280px;
  perspective: 1200px;
  cursor: pointer;
}

.flipper {
  width: 100%;
  height: 100%;
  position: relative;
  transform-style: preserve-3d;
  transition: transform 0.55s cubic-bezier(0.4, 0.2, 0.2, 1);
}

.flipper.flipped { transform: rotateY(180deg); }

.card-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  background: var(--bg-card);
  border: 2px solid var(--border-subtle);
  border-radius: 20px;
  padding: 32px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  box-shadow: var(--shadow-float);
}

.card-face.back {
  transform: rotateY(180deg);
  background: var(--color-accent-light);
  border-color: var(--color-accent);
}

.card-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-tertiary);
  margin-bottom: 16px;
}

.card-text {
  font-size: 18px;
  line-height: 1.6;
  color: var(--text-primary);
  text-align: center;
  margin: 0;
}

.card-source {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 4px;
  justify-content: center;
}

.tap-hint {
  font-size: 12px;
  color: var(--text-tertiary);
  text-align: center;
  margin-top: 20px;
}

/* Rating */
.rating-buttons {
  text-align: center;
}

.rating-hint { color: var(--text-secondary); font-size: 14px; margin-bottom: 12px; }

.rating-row {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.rate-btn {
  min-width: 90px;
  height: auto;
  padding: 10px 12px;
  line-height: 1.4;
  font-size: 13px;
  border-radius: 10px;
  white-space: normal;
}

.rate-0 { color: #f56c6c; border-color: #f56c6c; }
.rate-1 { color: #e6a23c; border-color: #e6a23c; }
.rate-3 { color: #909399; border-color: #909399; }
.rate-4 { color: #67c23a; border-color: #67c23a; }
.rate-5 { color: #409eff; border-color: #409eff; }

/* Card grid */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.card-tile {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 18px;
  position: relative;
  box-shadow: var(--shadow-card);
  transition: transform 0.2s, box-shadow 0.2s;
}

.card-tile:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-float);
}

.card-tile.mastered { border-color: #67c23a44; background: #f0f9eb; }

.tile-badge { margin-bottom: 8px; }

.tile-front {
  font-weight: 600;
  font-size: 14px;
  color: var(--text-primary);
  margin: 0 0 8px;
  line-height: 1.5;
}

.tile-back {
  font-size: 13px;
  color: var(--text-secondary);
  margin: 0 0 12px;
  line-height: 1.5;
}

.tile-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--text-tertiary);
}

/* Session done */
.session-done {
  text-align: center;
  padding: 60px 20px;
}

.done-icon { font-size: 56px; margin-bottom: 12px; }
.session-done h3 { font-size: 24px; margin-bottom: 8px; }
.session-done p { color: var(--text-secondary); margin-bottom: 24px; }

/* Skeleton */
.skeleton-area { padding: 20px 0; }

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
