<template>
  <div class="agent-exam-layout">
    <!-- Top Header Bar -->
    <header class="top-header">
      <div class="header-brand">
        <span class="brand-icon">🎓</span>
        <span class="brand-name">Agent for Exam</span>
      </div>
      <div class="header-actions">
        <el-button size="small" plain @click="showSettings = true">
          <el-icon><Setting /></el-icon>
          Settings
        </el-button>
      </div>
    </header>

    <div class="main-body">
      <!-- ===== LEFT PANEL: Conversation + Document Management ===== -->
      <aside class="left-panel" :class="{ collapsed: leftCollapsed }">
        <div class="left-panel-toggle" @click="leftCollapsed = !leftCollapsed">
          <el-icon><component :is="leftCollapsed ? 'ArrowRight' : 'ArrowLeft'" /></el-icon>
        </div>

        <div v-show="!leftCollapsed" class="left-panel-content">
          <!-- Conversation Management -->
          <section class="panel-section">
            <div class="section-header">
              <span class="section-title">Conversations</span>
              <el-button size="small" type="primary" @click="createConversation" class="new-btn">
                + New
              </el-button>
            </div>

            <div class="conversation-list">
              <div
                v-for="conv in conversations"
                :key="conv.id"
                class="conversation-item"
                :class="{ active: activeConversationId === conv.id }"
                @click="selectConversation(conv.id)"
              >
                <div class="conv-info">
                  <span class="conv-title">{{ conv.title }}</span>
                  <span class="conv-meta">{{ conv.docCount }} doc{{ conv.docCount !== 1 ? 's' : '' }}</span>
                </div>
                <el-button
                  link
                  size="small"
                  class="conv-delete"
                  @click.stop="deleteConversation(conv.id)"
                >
                  <el-icon><Close /></el-icon>
                </el-button>
              </div>
              <div v-if="conversations.length === 0" class="empty-hint">
                No conversations yet.
              </div>
            </div>
          </section>

          <!-- Document Management -->
          <section class="panel-section doc-section">
            <div class="section-header">
              <span class="section-title">Documents</span>
              <el-upload
                :http-request="handleUpload"
                :show-file-list="false"
                :multiple="true"
                accept=".pdf,.pptx,.docx"
              >
                <el-button size="small" type="primary" class="new-btn">+ Upload</el-button>
              </el-upload>
            </div>

            <div class="doc-list">
              <div
                v-for="doc in documents"
                :key="doc.id"
                class="doc-item"
              >
                <div class="doc-icon">
                  <span class="doc-type-badge" :class="doc.type">{{ doc.type.toUpperCase() }}</span>
                </div>
                <div class="doc-info">
                  <span class="doc-name">{{ doc.name }}</span>
                  <el-tag
                    size="small"
                    :type="doc.status === 'completed' ? 'success' : doc.status === 'processing' ? 'warning' : 'info'"
                    class="doc-status"
                  >
                    {{ doc.status }}
                  </el-tag>
                </div>
              </div>
              <div v-if="documents.length === 0" class="empty-hint">
                No documents uploaded.
              </div>
            </div>
          </section>
        </div>
      </aside>

      <!-- ===== MIDDLE PANEL: Chat Area ===== -->
      <main class="chat-panel">
        <!-- Messages -->
        <div class="messages-area" ref="messagesAreaRef">
          <div v-if="messages.length === 0" class="chat-empty-state">
            <div class="empty-icon">✨</div>
            <h3>How can I help you study?</h3>
            <p>Ask questions about your documents, request summaries, or explore the knowledge graph.</p>
          </div>

          <div v-else class="message-list">
            <div
              v-for="(msg, idx) in messages"
              :key="idx"
              class="message-row"
              :class="msg.role"
            >
              <div class="msg-avatar">{{ msg.role === 'user' ? 'U' : 'A' }}</div>
              <div class="msg-body">
                <div class="msg-sender">{{ msg.role === 'user' ? 'You' : 'Assistant' }}</div>
                <div class="msg-bubble" :class="msg.role">
                  <div v-if="msg.role === 'assistant'" v-html="renderMarkdown(msg.content)"></div>
                  <div v-else>{{ msg.content }}</div>
                </div>
                <div v-if="msg.role === 'assistant' && msg.citations" class="msg-citations">
                  <span class="citation-label">Sources:</span>
                  <el-tag
                    v-for="(cite, ci) in msg.citations"
                    :key="ci"
                    size="small"
                    type="info"
                    class="citation-tag"
                  >
                    {{ cite }}
                  </el-tag>
                </div>
              </div>
            </div>

            <!-- Streaming indicator -->
            <div v-if="isStreaming" class="message-row assistant">
              <div class="msg-avatar">A</div>
              <div class="msg-body">
                <div class="msg-sender">Assistant</div>
                <div class="msg-bubble assistant streaming">
                  <span v-if="streamingContent">{{ streamingContent }}</span>
                  <span v-else class="typing-dots">
                    <span></span><span></span><span></span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Input Area -->
        <div class="input-area">
          <div class="input-mode-bar">
            <el-select v-model="chatMode" size="small" class="mode-select">
              <el-option label="Hybrid Mode" value="hybrid" />
              <el-option label="Local Mode" value="local" />
              <el-option label="Global Mode" value="global" />
              <el-option label="Naive Mode" value="naive" />
            </el-select>
          </div>
          <div class="input-box">
            <textarea
              v-model="inputText"
              class="chat-textarea"
              placeholder="Ask anything about your documents..."
              rows="1"
              @keydown.enter.exact.prevent="sendMessage"
              @input="autoResize"
              ref="textareaRef"
            ></textarea>
            <button
              class="send-btn"
              :disabled="!inputText.trim() || isStreaming"
              @click="sendMessage"
            >
              <el-icon v-if="!isStreaming"><Position /></el-icon>
              <el-icon v-else class="is-loading"><Loading /></el-icon>
            </button>
          </div>
          <div class="input-footer-hint">
            Assistant output may contain errors. Verify critical facts against your materials.
          </div>
        </div>
      </main>

      <!-- ===== RIGHT PANEL: Tabs (Graph, Docs, Mindmap, etc.) ===== -->
      <aside class="right-panel" :class="{ collapsed: rightCollapsed }">
        <div class="right-panel-toggle" @click="rightCollapsed = !rightCollapsed">
          <el-icon><component :is="rightCollapsed ? 'ArrowLeft' : 'ArrowRight'" /></el-icon>
        </div>

        <div v-show="!rightCollapsed" class="right-panel-content">
          <el-tabs v-model="activeRightTab" class="right-tabs">
            <!-- PPT View Tab -->
            <el-tab-pane label="📄 PPT View" name="ppt">
              <div class="tab-pane-content">
                <div v-if="documents.filter(d => d.type === 'pptx').length === 0" class="tab-empty">
                  <el-empty description="No PPT files uploaded yet." :image-size="80" />
                </div>
                <div v-else class="ppt-viewer">
                  <div class="ppt-file-list">
                    <div
                      v-for="doc in documents.filter(d => d.type === 'pptx')"
                      :key="doc.id"
                      class="ppt-file-item"
                      :class="{ active: activePptId === doc.id }"
                      @click="activePptId = doc.id"
                    >
                      <el-icon><Presentation /></el-icon>
                      {{ doc.name }}
                    </div>
                  </div>
                  <div class="ppt-slide-area">
                    <el-empty description="Select a file to preview slides." :image-size="60" />
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- Knowledge Graph Tab -->
            <el-tab-pane label="🕸 Knowledge Graph" name="graph">
              <div class="tab-pane-content graph-tab">
                <div class="graph-header">
                  <span class="graph-stats" v-if="graphData.nodes.length > 0">
                    Entities: {{ graphData.nodes.length }} | Relations: {{ graphData.edges.length }}
                  </span>
                  <div class="graph-controls">
                    <el-button size="small" @click="refreshGraph" :loading="graphLoading">
                      <el-icon><Refresh /></el-icon>
                      Refresh
                    </el-button>
                    <el-button size="small" @click="fitGraph">Fit</el-button>
                  </div>
                </div>

                <!-- Graph Filters -->
                <div class="graph-filters">
                  <div class="filter-section">
                    <div class="filter-label">Search Entity</div>
                    <el-input
                      v-model="graphFilter.search"
                      size="small"
                      placeholder="Enter entity name..."
                      clearable
                      @input="applyGraphFilter"
                    />
                  </div>
                  <div class="filter-section">
                    <div class="filter-label">Entity Type</div>
                    <div class="type-checkboxes">
                      <el-checkbox
                        v-for="type in entityTypes"
                        :key="type.value"
                        v-model="type.checked"
                        @change="applyGraphFilter"
                        class="type-checkbox"
                      >
                        <span class="type-dot" :style="{ background: type.color }"></span>
                        {{ type.label }}
                      </el-checkbox>
                    </div>
                  </div>
                  <div class="filter-section">
                    <div class="filter-label">Min Connections: {{ graphFilter.minDegree }}</div>
                    <el-slider
                      v-model="graphFilter.minDegree"
                      :min="0"
                      :max="10"
                      size="small"
                      @change="applyGraphFilter"
                    />
                  </div>
                </div>

                <!-- Cytoscape Graph Canvas -->
                <div class="graph-canvas-wrapper">
                  <div ref="cyContainerRef" class="cy-canvas"></div>
                  <div v-if="graphLoading" class="graph-loading-overlay">
                    <el-icon class="is-loading" :size="32"><Loading /></el-icon>
                    <span>Loading graph...</span>
                  </div>
                  <div v-if="!graphLoading && graphData.nodes.length === 0" class="graph-empty">
                    <el-empty description="No knowledge graph data yet. Start chatting to build the graph." :image-size="80" />
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- Agent Trace Tab -->
            <el-tab-pane label="🤖 Agent Trace" name="trace">
              <div class="tab-pane-content">
                <div v-if="agentTraces.length === 0" class="tab-empty">
                  <el-empty description="No agent traces yet. Start a conversation to see tool calls." :image-size="80" />
                </div>
                <div v-else class="trace-list">
                  <div
                    v-for="(trace, ti) in agentTraces"
                    :key="ti"
                    class="trace-item"
                    :class="trace.status"
                  >
                    <div class="trace-header" @click="trace.expanded = !trace.expanded">
                      <div class="trace-icon">
                        <el-icon v-if="trace.status === 'success'" color="#67C23A"><CircleCheck /></el-icon>
                        <el-icon v-else-if="trace.status === 'error'" color="#F56C6C"><CircleClose /></el-icon>
                        <el-icon v-else class="is-loading" color="#E6A23C"><Loading /></el-icon>
                      </div>
                      <span class="trace-name">{{ trace.toolName }}</span>
                      <span class="trace-time">{{ trace.duration }}ms</span>
                      <el-icon class="trace-expand-icon">
                        <component :is="trace.expanded ? 'ArrowUp' : 'ArrowDown'" />
                      </el-icon>
                    </div>
                    <div v-if="trace.expanded" class="trace-body">
                      <div class="trace-section">
                        <div class="trace-section-label">Arguments</div>
                        <pre class="trace-code">{{ JSON.stringify(trace.arguments, null, 2) }}</pre>
                      </div>
                      <div v-if="trace.result" class="trace-section">
                        <div class="trace-section-label">Result</div>
                        <pre class="trace-code">{{ typeof trace.result === 'string' ? trace.result : JSON.stringify(trace.result, null, 2) }}</pre>
                      </div>
                      <div v-if="trace.error" class="trace-section error">
                        <div class="trace-section-label">Error</div>
                        <pre class="trace-code error">{{ trace.error }}</pre>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- Exam Analysis Tab -->
            <el-tab-pane label="📝 Exam Analysis" name="exam">
              <div class="tab-pane-content">
                <div v-if="examItems.length === 0" class="tab-empty">
                  <el-empty description="No exam analysis yet. Upload exam papers to get started." :image-size="80" />
                </div>
                <div v-else class="exam-list">
                  <div
                    v-for="(item, ei) in examItems"
                    :key="ei"
                    class="exam-item"
                  >
                    <div class="exam-item-header">
                      <span class="exam-q-num">Q{{ ei + 1 }}</span>
                      <el-tag
                        size="small"
                        :type="item.correct ? 'success' : 'danger'"
                      >
                        {{ item.correct ? 'Correct' : 'Incorrect' }}
                      </el-tag>
                      <span class="exam-score">{{ item.score }}/{{ item.maxScore }}</span>
                    </div>
                    <div class="exam-question">{{ item.question }}</div>
                    <div class="exam-answer">
                      <span class="answer-label">Your Answer:</span> {{ item.userAnswer }}
                    </div>
                    <div class="exam-correct-answer">
                      <span class="answer-label">Correct Answer:</span> {{ item.correctAnswer }}
                    </div>
                    <div v-if="item.explanation" class="exam-explanation">
                      <span class="answer-label">Explanation:</span> {{ item.explanation }}
                    </div>
                  </div>
                </div>
              </div>
            </el-tab-pane>

            <!-- Personal Records Tab -->
            <el-tab-pane label="📊 Personal Records" name="records">
              <div class="tab-pane-content">
                <div class="records-summary">
                  <div class="record-stat-card">
                    <div class="stat-value">{{ records.totalSessions }}</div>
                    <div class="stat-label">Study Sessions</div>
                  </div>
                  <div class="record-stat-card">
                    <div class="stat-value">{{ records.totalMessages }}</div>
                    <div class="stat-label">Messages Sent</div>
                  </div>
                  <div class="record-stat-card">
                    <div class="stat-value">{{ records.docsProcessed }}</div>
                    <div class="stat-label">Docs Processed</div>
                  </div>
                  <div class="record-stat-card accent">
                    <div class="stat-value">{{ records.avgScore }}%</div>
                    <div class="stat-label">Avg Exam Score</div>
                  </div>
                </div>

                <div class="records-history">
                  <div class="records-history-title">Recent Activity</div>
                  <div
                    v-for="(activity, ai) in records.recentActivity"
                    :key="ai"
                    class="activity-item"
                  >
                    <div class="activity-icon">{{ activity.icon }}</div>
                    <div class="activity-info">
                      <div class="activity-text">{{ activity.text }}</div>
                      <div class="activity-time">{{ activity.time }}</div>
                    </div>
                  </div>
                  <div v-if="records.recentActivity.length === 0" class="empty-hint">
                    No activity recorded yet.
                  </div>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </aside>
    </div>

    <!-- Settings Dialog -->
    <el-dialog v-model="showSettings" title="Settings" width="480px">
      <div class="settings-content">
        <el-form label-width="140px" size="small">
          <el-form-item label="Chat Model">
            <el-input v-model="settings.chatModel" placeholder="e.g. gpt-4o" />
          </el-form-item>
          <el-form-item label="API Base URL">
            <el-input v-model="settings.apiBase" placeholder="https://api.openai.com/v1" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="settings.apiKey" type="password" show-password placeholder="sk-..." />
          </el-form-item>
          <el-form-item label="Embedding Model">
            <el-input v-model="settings.embeddingModel" placeholder="e.g. text-embedding-3-small" />
          </el-form-item>
        </el-form>
      </div>
      <template #footer>
        <el-button @click="showSettings = false">Cancel</el-button>
        <el-button type="primary" @click="saveSettings">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, watch } from 'vue'
import {
  Setting, Close, Position, Loading, Refresh,
  ArrowLeft, ArrowRight, ArrowUp, ArrowDown,
  CircleCheck, CircleClose, Presentation
} from '@element-plus/icons-vue'
import cytoscape from 'cytoscape'
import { marked } from 'marked'
import { ElMessage, ElMessageBox } from 'element-plus'

// ─── UI State ────────────────────────────────────────────────────────────────
const leftCollapsed = ref(false)
const rightCollapsed = ref(false)
const showSettings = ref(false)
const activeRightTab = ref('graph')
const activePptId = ref(null)

// ─── Settings ────────────────────────────────────────────────────────────────
const settings = reactive({
  chatModel: '',
  apiBase: '',
  apiKey: '',
  embeddingModel: ''
})

const saveSettings = () => {
  showSettings.value = false
  ElMessage.success('Settings saved.')
}

// ─── Conversations ────────────────────────────────────────────────────────────
const conversations = ref([
  { id: '1', title: 'Conversation 28', docCount: 0 },
  { id: '2', title: 'Conversation 27', docCount: 1 },
  { id: '3', title: 'Conversation 26', docCount: 1 },
  { id: '4', title: 'Conversation 18', docCount: 1 }
])
const activeConversationId = ref('1')

const createConversation = () => {
  const id = String(Date.now())
  conversations.value.unshift({ id, title: `Conversation ${conversations.value.length + 1}`, docCount: 0 })
  activeConversationId.value = id
  messages.value = []
}

const selectConversation = (id) => {
  activeConversationId.value = id
  messages.value = []
}

const deleteConversation = (id) => {
  ElMessageBox.confirm('Delete this conversation? This cannot be undone.', 'Delete Conversation', {
    confirmButtonText: 'Delete',
    cancelButtonText: 'Cancel',
    type: 'warning'
  }).then(() => {
    conversations.value = conversations.value.filter(c => c.id !== id)
    if (activeConversationId.value === id) {
      activeConversationId.value = conversations.value[0]?.id || null
      messages.value = []
    }
  }).catch(() => {})
}

// ─── Documents ────────────────────────────────────────────────────────────────
const documents = ref([
  { id: 'd1', name: 'T0.pdf', type: 'pdf', status: 'completed' },
  { id: 'd2', name: 'T2.pptx', type: 'pptx', status: 'completed' }
])

const handleUpload = ({ file }) => {
  const ext = file.name.split('.').pop().toLowerCase()
  const newDoc = {
    id: String(Date.now()),
    name: file.name,
    type: ext,
    status: 'processing'
  }
  documents.value.push(newDoc)
  ElMessage.info(`Uploading ${file.name}...`)
  setTimeout(() => {
    newDoc.status = 'completed'
    ElMessage.success(`${file.name} processed successfully.`)
  }, 2000)
}

// ─── Chat ─────────────────────────────────────────────────────────────────────
const messages = ref([
  {
    role: 'user',
    content: 'Who is Tony Lam?'
  },
  {
    role: 'assistant',
    content: `**Tony Lam's background summary:**

- **Professional Experience:** He has served as an algorithmic developer and quantitative trader at hedge funds and banks, and founded **AlgoGene**, a company focused on algorithmic trading technology.

- **Academic Background:** He holds a Bachelor's and Master's degree from **The University of Hong Kong (HKU)**, majoring in Mathematics, Risk Management, Precision Engineering, and Computer Science.

- **Achievements & Awards:** Tony Lam has received numerous awards in algorithmic trading and quantitative analysis, including:
  - Winner of the **WorldQuant Challenge** in 2014 and 2015.
  - Winner of the **CASH Algo Trading Contest**.
  - Winner of the **Rotman International Trading Competition** in 2017.
  - Named champion and researcher of *"Guest All Over the World — Global Quantitative Competition"* by CCTV Securities Channel in 2017/2018.

- **Other Roles:** He also serves as the Deputy Director of the **Algo Challenge Association**, dedicated to promoting algorithmic trading competitions and activities.

If you are interested in Tony Lam's detailed background or his teaching content in the **COMP7415** course, you can further explore the course materials and teaching resources he provides.`,
    citations: ['T0.pdf', 'T2.pptx']
  }
])
const inputText = ref('')
const isStreaming = ref(false)
const streamingContent = ref('')
const chatMode = ref('hybrid')
const messagesAreaRef = ref(null)
const textareaRef = ref(null)

const renderMarkdown = (text) => {
  if (!text) return ''
  try {
    return marked.parse(text)
  } catch {
    return text
  }
}

const autoResize = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesAreaRef.value) {
      messagesAreaRef.value.scrollTop = messagesAreaRef.value.scrollHeight
    }
  })
}

const sendMessage = async () => {
  const text = inputText.value.trim()
  if (!text || isStreaming.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  scrollToBottom()

  isStreaming.value = true
  streamingContent.value = ''

  // Simulate streaming response
  const demoResponse = `I understand you're asking about **"${text}"**. Based on the documents in your knowledge base, here is what I found:\n\nThis topic relates to several key concepts covered in your course materials. The knowledge graph shows connections between related entities that may help you understand the broader context.\n\n> **Note:** This is a demo response. Connect to your backend API to get real answers from your documents.`

  let i = 0
  const interval = setInterval(() => {
    if (i < demoResponse.length) {
      streamingContent.value += demoResponse[i]
      i++
      scrollToBottom()
    } else {
      clearInterval(interval)
      messages.value.push({
        role: 'assistant',
        content: streamingContent.value,
        citations: documents.value.slice(0, 2).map(d => d.name)
      })
      streamingContent.value = ''
      isStreaming.value = false

      // Add a demo trace
      agentTraces.value.unshift({
        toolName: 'knowledge_graph_search',
        status: 'success',
        duration: 342,
        arguments: { query: text, mode: chatMode.value },
        result: `Found ${Math.floor(Math.random() * 10) + 3} relevant entities.`,
        expanded: false
      })

      scrollToBottom()
    }
  }, 18)
}

// ─── Knowledge Graph ──────────────────────────────────────────────────────────
const cyContainerRef = ref(null)
const cyInstance = ref(null)
const graphLoading = ref(false)
const graphFilter = reactive({ search: '', minDegree: 0 })

const entityTypes = ref([
  { value: 'concept', label: 'Concept', color: '#409EFF', checked: true },
  { value: 'definition', label: 'Definition', color: '#67C23A', checked: true },
  { value: 'method', label: 'Method', color: '#E6A23C', checked: true },
  { value: 'application', label: 'Application', color: '#F56C6C', checked: true },
  { value: 'example', label: 'Example', color: '#909399', checked: true },
  { value: 'unknown', label: 'Unknown', color: '#A0CFFF', checked: true }
])

const graphData = reactive({
  nodes: [
    { id: 'tony_lam', label: 'Tony Lam', type: 'person' },
    { id: 'comp7415', label: 'COMP7415', type: 'concept' },
    { id: 'algogene', label: 'AlgoGene', type: 'organization' },
    { id: 'worldquant', label: 'WorldQuant Challenge', type: 'event' },
    { id: 'rotman', label: 'Rotman International Trading Competition', type: 'event' },
    { id: 'forex', label: 'Forex Market', type: 'concept' },
    { id: 'china_stock', label: 'China stock market', type: 'concept' }
  ],
  edges: [
    { id: 'e1', source: 'tony_lam', target: 'comp7415', label: 'teaches' },
    { id: 'e2', source: 'tony_lam', target: 'algogene', label: 'founded' },
    { id: 'e3', source: 'tony_lam', target: 'worldquant', label: 'won' },
    { id: 'e4', source: 'tony_lam', target: 'rotman', label: 'won' },
    { id: 'e5', source: 'tony_lam', target: 'forex', label: 'researches' },
    { id: 'e6', source: 'tony_lam', target: 'china_stock', label: 'analyzes' },
    { id: 'e7', source: 'comp7415', target: 'forex', label: 'covers' },
    { id: 'e8', source: 'comp7415', target: 'china_stock', label: 'covers' }
  ]
})

const colorMap = {
  person: '#67C23A',
  concept: '#409EFF',
  organization: '#F56C6C',
  event: '#E6A23C',
  definition: '#9C27B0',
  method: '#00BCD4',
  application: '#FF9800',
  example: '#909399',
  unknown: '#A0CFFF'
}

const getNodeColor = (type) => {
  if (!type) return colorMap.unknown
  return colorMap[type.toLowerCase()] || colorMap.unknown
}

const initGraph = () => {
  if (!cyContainerRef.value) return
  if (cyInstance.value) {
    cyInstance.value.destroy()
    cyInstance.value = null
  }

  const checkedTypes = new Set(entityTypes.value.filter(t => t.checked).map(t => t.value))
  const searchLower = graphFilter.search.toLowerCase()

  const filteredNodes = graphData.nodes.filter(n => {
    if (!checkedTypes.has(n.type) && !checkedTypes.has('unknown')) {
      // allow if type not in list (treat as unknown)
    }
    if (searchLower && !n.label.toLowerCase().includes(searchLower)) return false
    return true
  })

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = graphData.edges.filter(
    e => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)
  )

  // Degree filter
  const degreeMap = new Map()
  filteredNodes.forEach(n => degreeMap.set(n.id, 0))
  filteredEdges.forEach(e => {
    degreeMap.set(e.source, (degreeMap.get(e.source) || 0) + 1)
    degreeMap.set(e.target, (degreeMap.get(e.target) || 0) + 1)
  })

  const finalNodes = filteredNodes.filter(n => (degreeMap.get(n.id) || 0) >= graphFilter.minDegree)
  const finalNodeIds = new Set(finalNodes.map(n => n.id))
  const finalEdges = filteredEdges.filter(e => finalNodeIds.has(e.source) && finalNodeIds.has(e.target))

  const elements = [
    ...finalNodes.map(n => ({
      data: {
        id: n.id,
        label: n.label,
        type: n.type
      }
    })),
    ...finalEdges.map(e => ({
      data: {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label
      }
    }))
  ]

  cyInstance.value = cytoscape({
    container: cyContainerRef.value,
    elements,
    style: [
      {
        selector: 'node',
        style: {
          'background-color': (ele) => getNodeColor(ele.data('type')),
          'label': 'data(label)',
          'text-valign': 'center',
          'text-halign': 'center',
          'color': '#fff',
          'font-weight': 'bold',
          'text-outline-width': 1.5,
          'text-outline-color': 'rgba(0,0,0,0.4)',
          'width': (ele) => {
            const l = ele.data('label') || ''
            return Math.min(130, Math.max(55, l.length * 9 + 35))
          },
          'height': (ele) => {
            const l = ele.data('label') || ''
            return Math.min(130, Math.max(55, l.length * 9 + 35))
          },
          'font-size': 11,
          'shape': 'ellipse',
          'border-width': 2,
          'border-color': '#fff',
          'text-wrap': 'wrap',
          'text-max-width': 100
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 4,
          'border-color': '#FFD700'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': '#bbb',
          'target-arrow-color': '#bbb',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'text-rotation': 'autorotate',
          'font-size': 9,
          'color': '#888',
          'text-margin-y': -8
        }
      }
    ],
    layout: {
      name: 'cose',
      animate: true,
      animationDuration: 800,
      fit: true,
      padding: 20,
      nodeRepulsion: () => 4096,
      idealEdgeLength: () => 90,
      randomize: true
    },
    userPanningEnabled: true,
    userZoomingEnabled: true
  })

  cyInstance.value.on('mouseover', 'node', (e) => {
    const node = e.target
    node.connectedEdges().style({ 'width': 3, 'line-color': '#409EFF', 'target-arrow-color': '#409EFF' })
    cyInstance.value.elements().difference(node.union(node.neighborhood())).style('opacity', 0.25)
  })
  cyInstance.value.on('mouseout', 'node', () => {
    cyInstance.value.elements().style({ opacity: 1 })
    cyInstance.value.edges().style({ 'width': 2, 'line-color': '#bbb', 'target-arrow-color': '#bbb' })
  })
}

const refreshGraph = async () => {
  graphLoading.value = true
  await nextTick()
  setTimeout(() => {
    initGraph()
    graphLoading.value = false
    ElMessage.success('Graph refreshed.')
  }, 600)
}

const fitGraph = () => {
  if (cyInstance.value) cyInstance.value.fit()
}

const applyGraphFilter = () => {
  nextTick(() => initGraph())
}

// ─── Agent Traces ─────────────────────────────────────────────────────────────
const agentTraces = ref([
  {
    toolName: 'retrieve_documents',
    status: 'success',
    duration: 215,
    arguments: { query: 'Tony Lam background', top_k: 5 },
    result: 'Retrieved 5 relevant document chunks.',
    expanded: false
  },
  {
    toolName: 'knowledge_graph_search',
    status: 'success',
    duration: 342,
    arguments: { query: 'Tony Lam', mode: 'hybrid' },
    result: 'Found 7 related entities and 8 relations.',
    expanded: false
  }
])

// ─── Exam Items ───────────────────────────────────────────────────────────────
const examItems = ref([
  {
    question: 'What is the primary purpose of algorithmic trading?',
    userAnswer: 'To automate trading decisions using computer programs.',
    correctAnswer: 'To use computer algorithms to execute trades at optimal speed and price.',
    correct: true,
    score: 10,
    maxScore: 10,
    explanation: 'Algorithmic trading automates the process of buying and selling financial instruments based on pre-defined criteria.'
  },
  {
    question: 'Which competition did Tony Lam win in 2014?',
    userAnswer: 'Rotman International Trading Competition',
    correctAnswer: 'WorldQuant Challenge',
    correct: false,
    score: 0,
    maxScore: 10,
    explanation: 'Tony Lam won the WorldQuant Challenge in both 2014 and 2015. The Rotman competition was won in 2017.'
  }
])

// ─── Personal Records ─────────────────────────────────────────────────────────
const records = reactive({
  totalSessions: 12,
  totalMessages: 47,
  docsProcessed: 5,
  avgScore: 78,
  recentActivity: [
    { icon: '💬', text: 'Asked about Tony Lam\'s background', time: '2 minutes ago' },
    { icon: '📄', text: 'Uploaded T2.pptx', time: '15 minutes ago' },
    { icon: '📝', text: 'Completed exam analysis (2 questions)', time: '1 hour ago' },
    { icon: '🕸', text: 'Knowledge graph updated with 7 entities', time: '1 hour ago' },
    { icon: '📄', text: 'Uploaded T0.pdf', time: '2 hours ago' }
  ]
})

// ─── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(() => {
  nextTick(() => {
    if (activeRightTab.value === 'graph') {
      initGraph()
    }
  })
})

watch(activeRightTab, (tab) => {
  if (tab === 'graph') {
    nextTick(() => initGraph())
  }
})

onUnmounted(() => {
  if (cyInstance.value) {
    cyInstance.value.destroy()
  }
})
</script>
