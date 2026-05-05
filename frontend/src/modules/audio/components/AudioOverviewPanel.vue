<template>
  <div class="audio-panel">
    <!-- Generating state -->
    <div v-if="generating" class="generating-state">
      <div class="wave-bars">
        <span v-for="i in 5" :key="i" class="bar" :style="{ animationDelay: `${i * 0.12}s` }" />
      </div>
      <p>Generating podcast script with AI…</p>
    </div>

    <!-- No script yet -->
    <div v-else-if="!overview" class="empty-panel">
      <div class="pod-icon">🎙️</div>
      <h4>Audio Overview</h4>
      <p class="panel-desc">
        Generate a NotebookLM-style podcast dialogue summarising your documents.
        Play it back using your browser's text-to-speech.
      </p>
      <el-button type="primary" round @click="generate">
        <el-icon><Microphone /></el-icon>
        Generate Audio Overview
      </el-button>
    </div>

    <!-- Script ready -->
    <div v-else class="script-ready">
      <div class="script-header">
        <div class="script-meta">
          <span class="pod-badge">🎙️ Podcast Script</span>
          <span class="script-date">Generated {{ formatDate(overview.generated_at) }}</span>
        </div>
        <div class="script-controls">
          <el-button
            v-if="!playing"
            type="primary"
            size="small"
            round
            @click="play"
            :disabled="!speechSupported"
          >
            <el-icon><VideoPlay /></el-icon>
            {{ speechSupported ? 'Play' : 'TTS not supported' }}
          </el-button>
          <el-button v-else size="small" round type="warning" @click="stop">
            <el-icon><VideoPause /></el-icon>
            Stop
          </el-button>
          <el-button size="small" round plain @click="regenerate">
            Regenerate
          </el-button>
        </div>
      </div>

      <!-- Playback progress -->
      <div v-if="playing" class="playback-bar">
        <div class="wave-bars small">
          <span v-for="i in 5" :key="i" class="bar" :style="{ animationDelay: `${i * 0.1}s` }" />
        </div>
        <span>{{ currentSpeaker }} is speaking…</span>
      </div>

      <!-- Transcript -->
      <div class="transcript">
        <div
          v-for="(turn, i) in overview.script"
          :key="i"
          class="turn"
          :class="{ 'active-turn': playing && i === currentTurnIndex, [speakerClass(turn.speaker)]: true }"
        >
          <div class="speaker-badge" :class="speakerClass(turn.speaker)">
            {{ turn.speaker }}
          </div>
          <p class="turn-text">{{ turn.text }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Microphone, VideoPlay, VideoPause } from '@element-plus/icons-vue'
import { audioOverviewService } from '../services/audioOverviewService'

const props = defineProps({ subjectId: { type: String, required: true } })

const overview = ref(null)
const generating = ref(false)
const playing = ref(false)
const currentTurnIndex = ref(0)

const speechSupported = typeof window !== 'undefined' && 'speechSynthesis' in window

let utteranceQueue = []
let activeUtterance = null

const currentSpeaker = computed(() =>
  overview.value?.script?.[currentTurnIndex.value]?.speaker || ''
)

async function fetchOverview() {
  try {
    overview.value = await audioOverviewService.get(props.subjectId)
  } catch {
    overview.value = null
  }
}

async function generate() {
  generating.value = true
  try {
    overview.value = await audioOverviewService.generate(props.subjectId)
    ElMessage.success('Audio overview generated!')
  } catch {
    // error shown by interceptor
  } finally {
    generating.value = false
  }
}

async function regenerate() {
  await ElMessageBox.confirm(
    'Replace the existing podcast script with a new one?',
    'Regenerate',
    { confirmButtonText: 'Yes, regenerate', cancelButtonText: 'Cancel', type: 'warning' }
  ).catch(() => { throw new Error('cancelled') })
  await audioOverviewService.delete(props.subjectId)
  overview.value = null
  await generate()
}

// ── TTS playback ─────────────────────────────────────────────────────────────

function play() {
  if (!speechSupported || !overview.value?.script) return
  window.speechSynthesis.cancel()
  playing.value = true
  currentTurnIndex.value = 0
  playTurn(0)
}

function playTurn(idx) {
  const script = overview.value?.script || []
  if (idx >= script.length) {
    playing.value = false
    return
  }
  currentTurnIndex.value = idx
  const turn = script[idx]

  const u = new SpeechSynthesisUtterance(turn.text)
  u.lang = 'en-US'
  u.rate = 0.95

  // Assign different voices for Alex vs Sam if available
  const voices = window.speechSynthesis.getVoices()
  const alexVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Male'))
    || voices.find(v => v.lang.startsWith('en'))
  const samVoice = voices.find(v => v.lang.startsWith('en') && v.name.includes('Female'))
    || voices[1]
  u.voice = turn.speaker === 'Alex' ? alexVoice : (samVoice || alexVoice)

  u.onend = () => playTurn(idx + 1)
  u.onerror = () => { playing.value = false }

  activeUtterance = u
  window.speechSynthesis.speak(u)
}

function stop() {
  window.speechSynthesis.cancel()
  playing.value = false
}

onBeforeUnmount(() => stop())

function speakerClass(speaker) {
  return speaker === 'Alex' ? 'speaker-alex' : 'speaker-sam'
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleString()
}

// Load on mount
fetchOverview()
</script>

<style scoped>
.audio-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 24px;
  box-shadow: var(--shadow-card);
}

/* Empty / generating */
.empty-panel, .generating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 12px;
  padding: 20px 0;
}

.pod-icon { font-size: 48px; }

.empty-panel h4 {
  font-size: 18px;
  font-family: var(--font-serif);
  margin: 0;
}

.panel-desc {
  color: var(--text-secondary);
  font-size: 14px;
  max-width: 360px;
  line-height: 1.6;
}

/* Wave animation */
.wave-bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 36px;
}

.wave-bars.small { height: 20px; gap: 3px; }

.wave-bars .bar {
  width: 5px;
  background: var(--color-accent);
  border-radius: 3px;
  animation: wave 1s ease-in-out infinite;
}

.wave-bars.small .bar { width: 4px; }

@keyframes wave {
  0%, 100% { height: 8px; }
  50% { height: 28px; }
}

.wave-bars.small @keyframes wave {
  0%, 100% { height: 4px; }
  50% { height: 18px; }
}

/* Script ready */
.script-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  flex-wrap: wrap;
  gap: 10px;
}

.script-meta { display: flex; align-items: center; gap: 10px; }

.pod-badge {
  background: var(--color-accent-light);
  color: var(--color-accent);
  border-radius: 20px;
  padding: 3px 10px;
  font-size: 13px;
  font-weight: 600;
}

.script-date { font-size: 12px; color: var(--text-tertiary); }
.script-controls { display: flex; gap: 8px; }

/* Playback bar */
.playback-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--color-accent-light);
  border-radius: 8px;
  padding: 8px 14px;
  margin-bottom: 16px;
  font-size: 13px;
  color: var(--color-accent);
}

/* Transcript */
.transcript {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 4px;
}

.turn {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border-radius: 10px;
  transition: background 0.2s;
}

.turn.active-turn { background: var(--color-accent-light); }

.speaker-badge {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 700;
  min-width: 52px;
  text-align: center;
}

.speaker-badge.speaker-alex {
  background: #ecf5ff;
  color: #409eff;
}

.speaker-badge.speaker-sam {
  background: #fdf1ed;
  color: var(--color-accent);
}

.turn-text {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  margin: 0;
}

/* Scrollbar */
.transcript::-webkit-scrollbar { width: 4px; }
.transcript::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 4px; }
</style>
