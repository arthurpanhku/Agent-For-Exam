<template>
  <div class="dashboard-page">
    <header class="page-header">
      <div>
        <h2 class="page-title">
          <el-icon><TrendCharts /></el-icon>
          Study Dashboard
        </h2>
        <p class="page-subtitle">Your learning analytics at a glance</p>
      </div>
      <el-button plain round @click="load" :loading="loading">
        <el-icon><Refresh /></el-icon>
        Refresh
      </el-button>
    </header>

    <el-skeleton v-if="loading" :rows="6" animated style="margin-top: 20px" />

    <template v-else>
      <!-- KPI chips -->
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #fdf1ed">📚</div>
          <div>
            <div class="kpi-num">{{ stats.subjects }}</div>
            <div class="kpi-label">Knowledge Bases</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #ecf5ff">💬</div>
          <div>
            <div class="kpi-num">{{ stats.conversations }}</div>
            <div class="kpi-label">Conversations</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #f0f9eb">📄</div>
          <div>
            <div class="kpi-num">{{ stats.documents }}</div>
            <div class="kpi-label">Documents</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #fdf6ec">🔥</div>
          <div>
            <div class="kpi-num">{{ stats.streak_days }}</div>
            <div class="kpi-label">Day Streak</div>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-icon" style="background: #f4f4f5">📝</div>
          <div>
            <div class="kpi-num">{{ stats.exams }}</div>
            <div class="kpi-label">Exams Analyzed</div>
          </div>
        </div>
      </div>

      <!-- Activity calendar heatmap -->
      <section class="chart-section">
        <h3 class="section-title">Activity Calendar</h3>
        <div ref="calendarChart" class="chart-box" style="height: 160px" />
      </section>

      <!-- Bottom row: bar chart + flashcard progress -->
      <div class="bottom-row">
        <section class="chart-section flex-1">
          <h3 class="section-title">Monthly Activity</h3>
          <div ref="barChart" class="chart-box" style="height: 220px" />
        </section>

        <section class="chart-section" style="width: 280px">
          <h3 class="section-title">Flashcard Progress</h3>
          <div ref="pieChart" class="chart-box" style="height: 220px" />
        </section>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { TrendCharts, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { analyticsService } from '../services/analyticsService'
import { useFlashcardStore } from '../../flashcards/store/flashcardStore'
import { useSubjectStore } from '../../subjects/store/subjectStore'

const loading = ref(false)
const stats = ref({ subjects: 0, conversations: 0, documents: 0, exams: 0, streak_days: 0, activity_calendar: {} })

const calendarChart = ref(null)
const barChart = ref(null)
const pieChart = ref(null)

let calInst = null
let barInst = null
let pieInst = null

const fcStore = useFlashcardStore()
const subjStore = useSubjectStore()

onMounted(() => { load() })
onBeforeUnmount(() => {
  calInst?.dispose()
  barInst?.dispose()
  pieInst?.dispose()
})

async function load() {
  loading.value = true
  try {
    stats.value = await analyticsService.globalStats()

    // Load flashcard stats for the first subject as sample
    if (subjStore.subjects.length) {
      const sid = subjStore.subjects[0].subject_id
      await fcStore.loadStats(sid)
    }

    await nextTick()
    drawCalendar()
    drawBar()
    drawPie()
  } finally {
    loading.value = false
  }
}

function drawCalendar() {
  if (!calendarChart.value) return
  calInst?.dispose()
  calInst = echarts.init(calendarChart.value)

  const raw = stats.value.activity_calendar || {}
  const data = Object.entries(raw).map(([date, val]) => [date, val])

  // build 12-month range
  const end = new Date()
  const start = new Date(end)
  start.setMonth(start.getMonth() - 11)

  calInst.setOption({
    tooltip: { formatter: (p) => `${p.data[0]}: ${p.data[1]} activities` },
    visualMap: {
      min: 0, max: 10, type: 'piecewise',
      show: false,
      inRange: { color: ['#ebedf0', '#c6e48b', '#40c463', '#30a14e', '#216e39'] }
    },
    calendar: {
      range: [start.toISOString().slice(0, 7), end.toISOString().slice(0, 7)],
      cellSize: ['auto', 14],
      left: 40,
      top: 20,
      bottom: 10,
      itemStyle: { borderWidth: 2, borderColor: '#fff' },
      yearLabel: { show: false },
      monthLabel: { fontSize: 11, color: '#8c8c8c' },
      dayLabel: { fontSize: 10, color: '#8c8c8c', firstDay: 1 }
    },
    series: [{ type: 'heatmap', coordinateSystem: 'calendar', data }]
  })
}

function drawBar() {
  if (!barChart.value) return
  barInst?.dispose()
  barInst = echarts.init(barChart.value)

  const raw = stats.value.activity_calendar || {}
  // Aggregate by month
  const monthly = {}
  Object.entries(raw).forEach(([date, val]) => {
    const m = date.slice(0, 7)
    monthly[m] = (monthly[m] || 0) + val
  })
  const months = Object.keys(monthly).sort().slice(-6)
  const values = months.map(m => monthly[m])

  barInst.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: months, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{
      type: 'bar',
      data: values,
      itemStyle: { color: '#DA7756', borderRadius: [4, 4, 0, 0] },
      barMaxWidth: 48,
    }],
    grid: { left: 40, right: 16, top: 16, bottom: 36 },
  })
}

function drawPie() {
  if (!pieChart.value) return
  pieInst?.dispose()
  pieInst = echarts.init(pieChart.value)

  const s = fcStore.stats
  const total = s.total || 1
  const mastered = s.mastered || 0
  const newCards = s.new || 0
  const learning = total - mastered - newCards

  pieInst.setOption({
    tooltip: { trigger: 'item' },
    legend: { bottom: 0, fontSize: 11 },
    series: [{
      type: 'pie',
      radius: ['40%', '65%'],
      center: ['50%', '42%'],
      data: [
        { name: 'Mastered', value: mastered, itemStyle: { color: '#67c23a' } },
        { name: 'Learning', value: Math.max(0, learning), itemStyle: { color: '#e6a23c' } },
        { name: 'New', value: newCards, itemStyle: { color: '#909399' } },
      ],
      label: { show: false },
    }],
  })
}
</script>

<style scoped>
.dashboard-page { max-width: 1000px; margin: 0 auto; }

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

/* KPI */
.kpi-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 32px;
}

.kpi-card {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 16px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  flex: 1;
  min-width: 140px;
  box-shadow: var(--shadow-card);
}

.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.kpi-num { font-size: 26px; font-weight: 700; font-family: var(--font-serif); color: var(--text-primary); }
.kpi-label { font-size: 12px; color: var(--text-tertiary); margin-top: 2px; }

/* Charts */
.chart-section {
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  padding: 20px 20px 16px;
  margin-bottom: 16px;
  box-shadow: var(--shadow-card);
}

.section-title {
  font-family: var(--font-sans);
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
  margin: 0 0 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.chart-box { width: 100%; }

.bottom-row {
  display: flex;
  gap: 16px;
  align-items: stretch;
}

.flex-1 { flex: 1; }
</style>
