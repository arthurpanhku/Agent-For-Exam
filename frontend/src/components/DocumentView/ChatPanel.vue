<template>
  <div class="chat-panel">
    <!-- 消息列表区域 -->
    <div class="messages-container" ref="messagesContainer">
      <div v-if="messages.length === 0" class="empty-state">
        <el-empty description="开始对话吧！" :image-size="120" />
      </div>
      
      <div v-for="(message, index) in messages" :key="index" class="message-wrapper">
        <!-- 用户消息 -->
        <div v-if="message.role === 'user'" class="message user-message">
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
        
        <!-- AI 回复 -->
        <div v-else class="message assistant-message">
          <div class="message-content">
            <!-- Think 内容折叠栏（在顶部） -->
            <div v-if="hasThinkContent(message.content)" class="think-section">
              <el-collapse v-model="thinkCollapseStates">
                <el-collapse-item :name="index" :title="'Thinking Process'" class="think-collapse">
                  <div class="think-content" v-html="formatThinkContent(message.content)"></div>
                </el-collapse-item>
              </el-collapse>
            </div>
            
            <!-- 如果有 streamItems，按顺序显示工具调用和文本 -->
            <template v-if="message.streamItems && message.streamItems.length > 0">
              <template v-for="(item, itemIndex) in message.streamItems" :key="itemIndex">
                <!-- 工具调用（紧凑形式）- 只显示有效的工具调用（toolName 存在且不为空） -->
                <div v-if="item.type === 'tool_call' && item.toolName && item.toolName.trim()" class="tool-calls-section">
                  <ToolCallInline
                    :tool-name="item.toolName"
                    :tool-arguments="item.arguments"
                    :result="item.result"
                    :error-message="item.errorMessage"
                    :status="item.status"
                  />
                </div>
                <!-- 文本内容 -->
                <div v-else-if="item.type === 'text'" class="message-text">
                  <span v-html="formatMessageWithWarning(item.content)"></span>
                </div>
              </template>
            </template>
            <!-- 如果没有 streamItems，使用旧的显示方式（向后兼容） -->
            <template v-else>
              <!-- 工具调用（紧凑形式）- 只显示有效的工具调用（toolName 存在且不为空） -->
              <div v-if="message.toolCalls && message.toolCalls.length > 0 && message.toolCalls.some(tc => tc.toolName && tc.toolName.trim())" class="tool-calls-section">
                <ToolCallInline
                  v-for="(toolCall, toolIndex) in message.toolCalls.filter(tc => tc.toolName && tc.toolName.trim())"
                  :key="toolIndex"
                  :tool-name="toolCall.toolName"
                  :tool-arguments="toolCall.arguments"
                  :result="toolCall.result"
                  :error-message="toolCall.errorMessage"
                  :status="toolCall.status"
                />
              </div>
              
              <div class="message-text" v-html="formatMessageWithWarning(message.content)"></div>
            </template>
            
            <CitationHintsBlock
              v-if="message.citationAnalysis"
              :data="message.citationAnalysis"
            />
            <div class="message-time">{{ formatTime(message.timestamp) }}</div>
          </div>
        </div>
      </div>
      
      <!-- 流式输出中显示加载 -->
      <div v-if="isStreaming" class="message assistant-message">
        <div class="message-content">
          <!-- Think 内容折叠栏（在顶部） -->
          <div v-if="hasStreamingThinkContent" class="think-section">
            <el-collapse v-model="streamingThinkCollapse">
              <el-collapse-item name="streaming" :title="'Thinking Process'" class="think-collapse">
                <div class="think-content" v-html="formatThinkContent(currentStreamContent)"></div>
              </el-collapse-item>
            </el-collapse>
          </div>
          
          <!-- 按顺序显示工具调用和文本 -->
          <template v-for="(item, itemIndex) in streamItems" :key="itemIndex">
            <!-- 工具调用（紧凑形式）- 只显示有效的工具调用（toolName 存在且不为空） -->
            <div v-if="item.type === 'tool_call' && item.toolName && item.toolName.trim()" class="tool-calls-section">
              <ToolCallInline
                :tool-name="item.toolName"
                :tool-arguments="item.arguments"
                :result="item.result"
                :error-message="item.errorMessage"
                :status="item.status"
              />
            </div>
            <!-- 文本内容 -->
            <div v-else-if="item.type === 'text'" class="message-text">
              <span v-html="formatMessageWithWarning(item.content)"></span>
            </div>
          </template>
          
           <!-- 向后兼容：如果 streamItems 为空，显示旧的工具调用和文本 -->
           <template v-if="streamItems.length === 0">
             <!-- 流式工具调用（紧凑形式）- 只显示有效的工具调用（toolName 存在且不为空） -->
             <div v-if="currentStreamToolCalls.length > 0 && currentStreamToolCalls.some(tc => tc.toolName && tc.toolName.trim())" class="tool-calls-section">
               <ToolCallInline
                 v-for="(toolCall, toolIndex) in currentStreamToolCalls.filter(tc => tc.toolName && tc.toolName.trim())"
                 :key="toolIndex"
                 :tool-name="toolCall.toolName"
                 :tool-arguments="toolCall.arguments"
                 :result="toolCall.result"
                 :error-message="toolCall.errorMessage"
                 :status="toolCall.status"
               />
             </div>
            
            <!-- 文本内容 -->
            <div v-if="currentStreamContent" class="message-text">
            <span v-if="currentStreamWarning" class="warning-text" v-html="formatMarkdown(currentStreamWarning)"></span>
            <span v-if="currentStreamWarning && currentStreamContent" v-html="formatMarkdown('\n\n')"></span>
            <span v-html="formatMessageWithWarning(currentStreamContent)"></span>
              <span class="streaming-cursor">|</span>
            </div>
          </template>
          
          <!-- 如果使用新的混合显示，显示光标在最后 -->
          <div v-if="streamItems.length > 0" class="message-text">
            <span v-if="currentStreamWarning" class="warning-text" v-html="formatMarkdown(currentStreamWarning)"></span>
            <span v-if="currentStreamWarning" v-html="formatMarkdown('\n\n')"></span>
            <span class="streaming-cursor">|</span>
          </div>
          <CitationHintsBlock
            v-if="streamingCitationAnalysis"
            :data="streamingCitationAnalysis"
          />
        </div>
      </div>
    </div>

    <el-dialog v-model="variantDialogVisible" title="变式题（绑定讲义检索）" width="560px" destroy-on-close>
      <div class="variant-form">
        <el-input v-model="variantTopic" type="textarea" :rows="2" placeholder="考查主题或知识点" />
        <div class="variant-row">
          <span class="variant-label">题量</span>
          <el-input-number v-model="variantCount" :min="1" :max="10" size="small" />
          <span class="variant-label">难度基调</span>
          <el-select v-model="variantDifficulty" size="small" style="width: 120px">
            <el-option label="偏易" value="easy" />
            <el-option label="中等" value="medium" />
            <el-option label="偏难" value="hard" />
          </el-select>
        </div>
      </div>
      <div v-if="variantQuestions.length" class="variant-results">
        <div v-for="(q, qi) in variantQuestions" :key="qi" class="variant-card">
          <div class="variant-meta">
            <el-tag size="small" type="info">{{ q.difficulty || '—' }}</el-tag>
            <el-tag size="small" class="ml6">{{ bloomLabel(q.bloom_level) }}</el-tag>
          </div>
          <div class="variant-stem">{{ q.stem }}</div>
          <ul class="variant-options">
            <li v-for="(opt, oi) in (q.options || [])" :key="oi">{{ opt }}</li>
          </ul>
          <div class="variant-answer-block">
            <div><strong>答案：</strong>{{ q.answer }}</div>
            <div v-if="q.rationale" class="variant-rationale">{{ q.rationale }}</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="variantDialogVisible = false">关闭</el-button>
        <el-button type="primary" :loading="variantLoading" @click="runVariantQuestions">生成</el-button>
      </template>
    </el-dialog>
    
    <!-- 输入区域 -->
    <div class="input-container">
      <div class="input-toolbar">
        <el-tooltip
          :visible="modeGuideVisible"
          manual
          placement="top-start"
          popper-class="retrieval-mode-guide"
          content="Local: definitions and formulas. Mix: general questions. Global: cross-chapter synthesis; verify precise facts."
        >
          <el-select
            v-model="selectedMode"
            size="small"
            style="width: 132px;"
            placeholder="查询模式"
            :disabled="!graphReady || agentModeEnabled"
            @visible-change="dismissModeGuide"
            @change="dismissModeGuide"
          >
            <el-option label="Simple" value="naive" />
            <el-option
              label="Mix"
              value="mix"
              :disabled="!graphReady"
            />
            <el-option
              label="Local"
              value="local"
              :disabled="!graphReady"
            />
            <el-option
              label="Global"
              value="global"
              :disabled="!graphReady"
            />
          </el-select>
        </el-tooltip>
        <el-tag class="mode-chip" size="small" :type="selectedMode === 'global' ? 'warning' : 'info'">
          {{ agentModeEnabled ? 'Agent' : modeLabel }}
        </el-tag>
        <el-tooltip
          v-if="selectedMode === 'global' && !agentModeEnabled"
          content="Global synthesis mode: verify exact definitions and formulas against cited sources."
          placement="top"
        >
          <el-icon class="warning-icon"><Warning /></el-icon>
        </el-tooltip>
        <el-switch
          v-model="agentModeEnabled"
          active-text="助手"
          inactive-text="普通"
          size="small"
          style="margin-left: 8px;"
          @change="handleAgentModeChange"
        />
        <el-tooltip 
          v-if="!graphReady && !agentModeEnabled" 
          content="知识图谱尚未完全生成，仅可使用简单模式"
          placement="top"
        >
          <el-icon class="warning-icon"><Warning /></el-icon>
        </el-tooltip>
        <el-tooltip 
          v-if="agentModeEnabled" 
          content="助手模式：模型可按需调用注册的工具（例如生成思维导图）"
          placement="top"
        >
          <el-icon class="info-icon"><InfoFilled /></el-icon>
        </el-tooltip>
        <el-radio-group
          v-if="agentModeEnabled"
          v-model="studyChatStyle"
          size="small"
          class="study-style-toggle"
        >
          <el-radio-button label="default">答疑</el-radio-button>
          <el-radio-button label="socratic">考我</el-radio-button>
        </el-radio-group>
        <el-tooltip content="在回复结束后附加引用块可信度与跨文档冲突提示（基于图谱检索）" placement="top">
          <el-switch
            v-model="includeCitationAnalysis"
            size="small"
            class="citation-switch"
            inline-prompt
            active-text="引用"
            inactive-text="关闭"
            :disabled="!graphReady && !agentModeEnabled"
          />
        </el-tooltip>
      </div>
      
      <div class="input-area">
        <el-input
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入您的问题..."
          @keydown.enter.exact.prevent="handleSend"
          @keydown.enter.shift.exact="handleNewLine"
        />
        <div class="input-actions">
          <el-button
            v-if="graphReady"
            size="small"
            @click="openVariantDialog"
            :disabled="!convStore.currentConversationId || isStreaming"
          >
            变式题
          </el-button>
          <el-button
            type="primary"
            :icon="Promotion"
            @click="handleSend"
            :loading="isStreaming"
            :disabled="!inputText.trim() || !convStore.currentConversationId"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { Promotion, Warning, InfoFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { marked } from 'marked'
import katex from 'katex'
import { useConversationStore } from '../../stores/conversationStore'
import { useChatStore } from '../../stores/chatStore'
import { useGraphStore } from '../../stores/graphStore'
import ToolCallCard from './ToolCallCard.vue'
import ToolCallInline from './ToolCallInline.vue'
import { useDocumentStore } from '../../stores/documentStore'
import { api } from '../../services/api'
import CitationHintsBlock from './CitationHintsBlock.vue'

// 配置 marked 选项
marked.setOptions({
  breaks: true, // 支持换行
  gfm: true,    // 支持 GitHub 风格 Markdown
})

const convStore = useConversationStore()
const chatStore = useChatStore()
const graphStore = useGraphStore()
const docStore = useDocumentStore()

const messagesContainer = ref(null)
const inputText = ref('')
const selectedMode = ref('naive')
const modeGuideVisible = ref(false)
const isStreaming = ref(false)
const currentStreamContent = ref('')
const currentStreamWarning = ref('')
const currentStreamToolCalls = ref([]) // 流式输出中的工具调用列表（保留用于向后兼容）
const streamItems = ref([]) // 按顺序存储工具调用和文本片段 {type: 'tool_call'|'text', data: ...}
const thinkCollapseStates = ref([]) // 存储展开的消息索引数组（el-collapse需要数组）
const streamingThinkCollapse = ref([]) // 流式输出时的think折叠状态（默认折叠，空数组）
const graphReady = ref(false) // 知识图谱是否完全生成
const graphStatusLoading = ref(false) // 检查知识图谱状态的加载状态
const agentModeEnabled = ref(false) // 助手（工具）模式开关
const studyChatStyle = ref('default') // default | socratic（与助手模式配合）
const includeCitationAnalysis = ref(true)
const streamingCitationAnalysis = ref(null)
const variantDialogVisible = ref(false)
const variantTopic = ref('')
const variantCount = ref(3)
const variantDifficulty = ref('medium')
const variantLoading = ref(false)
const variantQuestions = ref([])
const modeLabel = computed(() => {
  const labels = {
    naive: 'Simple',
    mix: 'Mix',
    local: 'Local',
    global: 'Global'
  }
  return labels[selectedMode.value] || selectedMode.value
})

onMounted(() => {
  if (typeof window !== 'undefined' && !window.localStorage.getItem('studyforge.retrievalModeGuideSeen')) {
    modeGuideVisible.value = true
  }
})

const dismissModeGuide = () => {
  if (!modeGuideVisible.value) return
  modeGuideVisible.value = false
  if (typeof window !== 'undefined') {
    window.localStorage.setItem('studyforge.retrievalModeGuideSeen', '1')
  }
}

// 检查消息是否有有效内容
const hasValidContent = (message) => {
  // 用户消息必须有 content
  if (message.role === 'user') {
    return message.content && message.content.trim()
  }
  
  // assistant 消息检查
  if (message.role === 'assistant') {
    // 检查 streamItems 中是否有有效内容
    if (message.streamItems && Array.isArray(message.streamItems) && message.streamItems.length > 0) {
      const hasValidItem = message.streamItems.some(item => {
        if (item.type === 'tool_call') {
          // 有效的工具调用必须有 toolName
          return item.toolName && item.toolName.trim()
        } else if (item.type === 'text') {
          // 有效的文本必须有内容
          return item.content && item.content.trim()
        }
        return false
      })
      if (hasValidItem) return true
    }
    
    // 检查 toolCalls 中是否有有效内容
    if (message.toolCalls && Array.isArray(message.toolCalls) && message.toolCalls.length > 0) {
      const hasValidToolCall = message.toolCalls.some(tc => tc.toolName && tc.toolName.trim())
      if (hasValidToolCall) return true
    }
    
    // 检查 content 是否有内容（排除 think 标签）
    if (message.content) {
      const contentWithoutThink = message.content.replace(/<(?:think|redacted_reasoning)>[\s\S]*?<\/(?:think|redacted_reasoning)>/gi, '').trim()
      if (contentWithoutThink) return true
    }
    
    return false
  }
  
  return true
}

// 消息列表（从 chatStore 获取）
const messages = computed(() => {
  if (!convStore.currentConversationId) return []
  const allMessages = chatStore.getMessages(convStore.currentConversationId)
  // 过滤掉 tool 消息和没有有效内容的 assistant 消息
  const filteredMessages = allMessages.filter(msg => {
    if (msg.role === 'tool') return false
    return hasValidContent(msg)
  })
  // console.log(`🔄 [前端] 消息列表计算: 原始消息数=${allMessages.length}, 过滤后消息数=${filteredMessages.length}`)
  return filteredMessages
})

// 计算属性：流式输出时是否有think内容（确保响应式更新）
const hasStreamingThinkContent = computed(() => {
  return hasThinkContent(currentStreamContent.value)
})

// 检查知识图谱状态
const checkGraphStatus = async (conversationId) => {
  if (!conversationId) {
    graphReady.value = false
    return
  }
  
  graphStatusLoading.value = true
  try {
    const status = await graphStore.getGraphStatus(conversationId)
    graphReady.value = status.is_ready
    
    // 如果知识图谱未就绪，强制使用简单模式
    if (!status.is_ready && selectedMode.value !== 'naive') {
      selectedMode.value = 'naive'
    }
  } catch (error) {
    console.error('检查知识图谱状态失败:', error)
    graphReady.value = false
  } finally {
    graphStatusLoading.value = false
  }
}

// 监听对话变化，加载历史消息和图谱
watch(() => convStore.currentConversationId, async (newId) => {
  if (newId) {
    await chatStore.loadMessages(newId)
    // 同时加载图谱数据
    try {
      await graphStore.loadGraph(newId)
    } catch (error) {
      console.error('加载图谱失败:', error)
    }
    // 检查知识图谱状态
    await checkGraphStatus(newId)
  } else {
    chatStore.clearMessages()
    graphStore.clearGraph()
    graphReady.value = false
  }
}, { immediate: true })

// 监听文档处理状态变化，定期检查知识图谱状态
watch(() => docStore.extractionProgress, async () => {
  if (convStore.currentConversationId) {
    // 延迟一下再检查，避免频繁请求
    setTimeout(() => {
      checkGraphStatus(convStore.currentConversationId)
    }, 2000)
  }
}, { deep: true })

// 监听消息变化，滚动到底部
watch(() => messages.value.length, () => {
  nextTick(() => {
    scrollToBottom()
  })
})

// 滚动到底部
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

// 发送消息
const handleSend = async () => {
  if (!inputText.value.trim() || !convStore.currentConversationId) {
    return
  }
  
  const query = inputText.value.trim()
  inputText.value = ''
  
  // 添加用户消息到本地
  chatStore.addMessage(convStore.currentConversationId, {
    role: 'user',
    content: query,
    timestamp: Date.now()
  })
  
  // 开始流式查询
  isStreaming.value = true
  currentStreamContent.value = ''
  currentStreamWarning.value = ''
  currentStreamToolCalls.value = [] // 重置工具调用列表
  streamItems.value = [] // 重置混合内容数组
  streamingThinkCollapse.value = [] // 重置流式think折叠状态（默认折叠）
  streamingCitationAnalysis.value = null
  
  try {
    // 如果 Agent 模式开启，使用 agent 模式
    const mode = agentModeEnabled.value ? "agent" : selectedMode.value
    const streamOptions = {
      chatStyle: agentModeEnabled.value ? studyChatStyle.value : 'default',
      includeCitationAnalysis: includeCitationAnalysis.value
    }
    
    await chatStore.queryStream(convStore.currentConversationId, query, mode, null, (chunk) => {
      // 处理 Agent 模式的特殊响应
      if (typeof chunk === 'object') {
        if (chunk.type === 'tool_call') {
          // 工具调用开始：添加到混合数组
          // 在添加 tool_call 之前，确保将 currentStreamContent 中的文本内容先添加到 streamItems
          if (currentStreamContent.value && currentStreamContent.value.trim()) {
            const lastItem = streamItems.value[streamItems.value.length - 1]
            if (lastItem && lastItem.type === 'text') {
              // 如果最后一个项是文本，追加内容
              lastItem.content += currentStreamContent.value
            } else {
              // 否则创建新的文本项
              streamItems.value.push({
                type: 'text',
                content: currentStreamContent.value
              })
            }
            // 清空 currentStreamContent，因为已经添加到 streamItems 了
            currentStreamContent.value = ''
          }
          
          const toolCall = chunk.tool_call
          console.log('收到 tool_call:', toolCall)
          
          let argumentsObj = {}
          try {
            // 尝试解析 arguments（可能是字符串格式的 JSON）
            const argsStr = toolCall.function?.arguments || '{}'
            argumentsObj = typeof argsStr === 'string' ? JSON.parse(argsStr) : argsStr
          } catch (e) {
            console.warn('解析工具调用参数失败:', e)
            argumentsObj = {}
          }
          
          const toolCallItem = {
            type: 'tool_call',
            toolName: toolCall.function?.name || '',
            arguments: argumentsObj,
            result: null,
            errorMessage: null,
            timestamp: Date.now(),
            status: 'pending'
          }
          
          console.log('添加 tool_call 到 streamItems:', toolCallItem)
          streamItems.value.push(toolCallItem)
          // 同时添加到 currentStreamToolCalls（用于向后兼容）
          currentStreamToolCalls.value.push({
            toolName: toolCallItem.toolName,
            arguments: toolCallItem.arguments,
            result: null,
            errorMessage: null,
            timestamp: toolCallItem.timestamp,
            status: 'pending'
          })
          console.log('当前 streamItems:', streamItems.value)
        } else if (chunk.type === 'tool_result') {
          // 工具执行结果
          const toolResult = chunk.tool_result
          const result = toolResult.result || {}
          
          // 更新 streamItems 中对应的工具调用（从后往前找，找到最后一个未完成的）
          let toolCallIndex = -1
          for (let i = streamItems.value.length - 1; i >= 0; i--) {
            if (streamItems.value[i].type === 'tool_call' && 
                streamItems.value[i].toolName === toolResult.tool_name && 
                !streamItems.value[i].result) {
              toolCallIndex = i
              break
            }
          }
          
          if (toolCallIndex !== -1) {
            // 更新 streamItems 中的工具调用
            streamItems.value[toolCallIndex].arguments = toolResult.arguments || {}
            streamItems.value[toolCallIndex].result = result
            streamItems.value[toolCallIndex].status = result.status === 'success' ? 'success' : (result.status === 'error' ? 'error' : 'pending')
          }
          
          // 查找或创建工具调用记录（用于向后兼容）
          let toolCallIndex2 = currentStreamToolCalls.value.findIndex(
            tc => tc.toolName === toolResult.tool_name && !tc.result
          )
          
          if (toolCallIndex2 === -1) {
            // 创建新的工具调用记录
            currentStreamToolCalls.value.push({
              toolName: toolResult.tool_name,
              arguments: toolResult.arguments || {},
              result: result,
              errorMessage: null,
              timestamp: Date.now(),
              status: result.status === 'success' ? 'success' : (result.status === 'error' ? 'error' : 'pending')
            })
          } else {
            // 更新现有记录
            currentStreamToolCalls.value[toolCallIndex2].result = result
            currentStreamToolCalls.value[toolCallIndex2].status = result.status === 'success' ? 'success' : (result.status === 'error' ? 'error' : 'pending')
          }
          
          // 如果是思维脑图工具，更新思维脑图
          if (toolResult.tool_name === 'generate_mindmap' && result.status === 'success') {
            const mindmapContent = result.mindmap_content || result.result?.mindmap_content
            if (mindmapContent) {
              // 导入 mindmapStore 并更新
              import('../../stores/mindmapStore').then(({ useMindMapStore }) => {
                const mindmapStore = useMindMapStore()
                mindmapStore.mindmapContent = mindmapContent
              })
            }
          }
        } else if (chunk.type === 'tool_error') {
          // 工具执行错误
          // 更新 streamItems 中对应的工具调用
          let toolCallIndex = -1
          for (let i = streamItems.value.length - 1; i >= 0; i--) {
            if (streamItems.value[i].type === 'tool_call' && 
                streamItems.value[i].toolName === chunk.tool_name && 
                !streamItems.value[i].result) {
              toolCallIndex = i
              break
            }
          }
          
          if (toolCallIndex !== -1) {
            streamItems.value[toolCallIndex].errorMessage = chunk.message
            streamItems.value[toolCallIndex].status = 'error'
          }
          
          // 向后兼容
          currentStreamToolCalls.value.push({
            toolName: chunk.tool_name,
            arguments: {},
            result: null,
            errorMessage: chunk.message,
            timestamp: Date.now(),
            status: 'error'
          })
        } else if (chunk.type === 'mindmap_content') {
          // 思维脑图内容（流式）
          import('../../stores/mindmapStore').then(({ useMindMapStore }) => {
            const mindmapStore = useMindMapStore()
            mindmapStore.mindmapContent = chunk.content
          })
        } else if (chunk.type === 'warning') {
        currentStreamWarning.value = chunk.content
        } else if (chunk.type === 'error') {
          // 错误信息：显示友好提示
          ElMessage.error(chunk.content || '查询失败，请重试')
          chatStore.addMessage(convStore.currentConversationId, {
            role: 'assistant',
            content: chunk.content || '抱歉，查询失败。请检查网络连接或稍后重试。',
            timestamp: Date.now()
          })
          // 不抛出异常，让流式处理正常结束
        } else if (chunk.type === 'response') {
          // Agent 模式的正常响应
          // console.log('📥 [前端] 收到 response 事件:', chunk.content)
          // Agent 模式使用 streamItems 显示，不需要添加到 currentStreamContent（避免重复）
          // 追加到最后一个文本项或创建新项
          const lastItem = streamItems.value[streamItems.value.length - 1]
          if (lastItem && lastItem.type === 'text') {
            lastItem.content += chunk.content
          } else {
            streamItems.value.push({
              type: 'text',
              content: chunk.content
            })
          }
        } else if (chunk.type === 'citation_analysis') {
          streamingCitationAnalysis.value = chunk.content || null
        }
      } else if (typeof chunk === 'string') {
        // 普通响应内容（非 Agent 模式）
        currentStreamContent.value += chunk
      }
      nextTick(() => {
        scrollToBottom()
      })
    }, streamOptions)
    
    // 流式结束，保存完整回复（包含警告提示）
    // 在提取内容之前，确保 currentStreamContent 中剩余的内容也被添加到 streamItems
    if (currentStreamContent.value && currentStreamContent.value.trim()) {
      const lastItem = streamItems.value[streamItems.value.length - 1]
      if (lastItem && lastItem.type === 'text') {
        // 如果最后一个项是文本，追加内容
        lastItem.content += currentStreamContent.value
      } else {
        // 否则创建新的文本项
        streamItems.value.push({
          type: 'text',
          content: currentStreamContent.value
        })
      }
      // 清空 currentStreamContent，因为已经添加到 streamItems 了
      currentStreamContent.value = ''
    }
    
    // 从 streamItems 中提取文本内容和工具调用
    let fullContent = ''
    const toolCallsFromStream = []
    
    if (currentStreamWarning.value) {
      fullContent = currentStreamWarning.value + '\n\n'
    }
    
    // 从 streamItems 中提取内容
    for (const item of streamItems.value) {
      if (item.type === 'text') {
        fullContent += item.content
      } else if (item.type === 'tool_call') {
        toolCallsFromStream.push({
          toolName: item.toolName,
          arguments: item.arguments,
          result: item.result,
          errorMessage: item.errorMessage,
          timestamp: item.timestamp,
          status: item.status
        })
      }
    }
    
    // 向后兼容：如果没有 streamItems，使用旧的方式
    if (streamItems.value.length === 0 && currentStreamContent.value) {
      fullContent += currentStreamContent.value
    }
    
    const finalToolCalls = toolCallsFromStream.length > 0 ? toolCallsFromStream : 
                           (currentStreamToolCalls.value.length > 0 ? currentStreamToolCalls.value : undefined)
    const citationSnapshot = streamingCitationAnalysis.value
      ? JSON.parse(JSON.stringify(streamingCitationAnalysis.value))
      : null
    
    if (fullContent || finalToolCalls) {
      const newMessageIndex = messages.value.length
      chatStore.addMessage(convStore.currentConversationId, {
        role: 'assistant',
        content: fullContent,
        toolCalls: finalToolCalls,
        streamItems: streamItems.value.length > 0 ? [...streamItems.value] : undefined, // 保存 streamItems 以便后续显示
        citationAnalysis: citationSnapshot || undefined,
        timestamp: Date.now()
      })
      
      // 如果新消息包含think内容，确保默认折叠（不在thinkCollapseStates数组中）
      if (hasThinkContent(fullContent)) {
        // 确保新消息的索引不在折叠状态数组中（默认折叠）
        nextTick(() => {
          const index = thinkCollapseStates.value.indexOf(newMessageIndex)
          if (index > -1) {
            thinkCollapseStates.value.splice(index, 1)
          }
        })
      }
      
      // 保存到后端（包含工具调用信息和 streamItems）
      await chatStore.saveMessage(
        convStore.currentConversationId, 
        query, 
        fullContent,
        finalToolCalls,
        streamItems.value.length > 0 ? [...streamItems.value] : null,
        citationSnapshot,
        mode
      )
    }
    
    currentStreamContent.value = ''
    currentStreamWarning.value = ''
    streamItems.value = [] // 重置混合内容数组
    streamingCitationAnalysis.value = null
    streamingThinkCollapse.value = [] // 重置流式think折叠状态
  } catch (error) {
    console.error('查询失败:', error)
    ElMessage.error('查询失败，请重试')
    
    // 添加错误消息
    chatStore.addMessage(convStore.currentConversationId, {
      role: 'assistant',
      content: '抱歉，查询失败。请检查网络连接或稍后重试。',
      timestamp: Date.now()
    })
  } finally {
    isStreaming.value = false
    nextTick(() => {
      scrollToBottom()
    })
  }
}

// 助手（工具）模式切换
const handleAgentModeChange = (enabled) => {
  if (enabled) {
    ElMessage.info('已启用助手模式：可按需调用工具完成任务')
  } else {
    ElMessage.info('已切换到普通模式')
  }
}

watch(agentModeEnabled, (enabled) => {
  if (!enabled) {
    studyChatStyle.value = 'default'
  }
})

const bloomLabel = (b) => {
  const m = {
    remember: '记忆',
    understand: '理解',
    apply: '应用',
    analyze: '分析',
    evaluate: '评价',
    create: '创造'
  }
  const key = (b || '').toLowerCase()
  return m[key] || b || '—'
}

const openVariantDialog = () => {
  if (!convStore.currentConversationId) {
    ElMessage.warning('请先选择对话')
    return
  }
  variantTopic.value = inputText.value.trim() || variantTopic.value
  variantQuestions.value = []
  variantDialogVisible.value = true
}

const runVariantQuestions = async () => {
  const tid = convStore.currentConversationId
  const topic = (variantTopic.value || '').trim()
  if (!tid || !topic) {
    ElMessage.warning('请填写考查主题')
    return
  }
  variantLoading.value = true
  try {
    const mode = agentModeEnabled.value ? 'mix' : selectedMode.value
    const res = await api.post(`/api/conversations/${tid}/variant-questions`, {
      topic,
      mode: mode === 'agent' ? 'mix' : mode,
      count: variantCount.value,
      base_difficulty: variantDifficulty.value
    })
    variantQuestions.value = res.questions || []
    if (!variantQuestions.value.length) {
      ElMessage.info('未生成题目，请换主题或检查模型与检索配置')
    }
  } catch (e) {
    const d = e?.response?.data?.detail
    const msg = typeof d === 'string' ? d : (Array.isArray(d) ? d.map((x) => x.msg || x).join('; ') : (e?.message || '生成失败'))
    ElMessage.error(msg)
  } finally {
    variantLoading.value = false
  }
}

// Shift+Enter 换行
const handleNewLine = () => {
  // 默认行为是换行，不需要特殊处理
}

// 格式化时间
const formatTime = (timestamp) => {
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

// 检查是否有 think 内容（支持流式输出时的部分标签）
const hasThinkContent = (text) => {
  if (!text) return false
  // 检测开始标签即可（支持流式输出时标签未闭合的情况）
  return /<(?:think|redacted_reasoning)>/i.test(text)
}

// 提取并格式化 think 内容（支持流式输出时的部分内容）
const formatThinkContent = (text) => {
  if (!text) return ''
  
  // 支持 <think> 和 <redacted_reasoning> 两种标签
  // 先尝试匹配完整的标签对
  let thinkMatch = text.match(/<(?:think|redacted_reasoning)>([\s\S]*?)<\/(?:think|redacted_reasoning)>/i)
  
  // 如果没匹配到完整标签对，尝试匹配只有开始标签的情况（流式输出中）
  if (!thinkMatch) {
    const openTagMatch = text.match(/<(?:think|redacted_reasoning)>([\s\S]*)$/i)
    if (openTagMatch) {
      thinkMatch = openTagMatch
    } else {
      return ''
    }
  }
  
  let thinkText = thinkMatch[1] || ''
  return formatEnhancedMarkdown(thinkText)
}

// 格式化消息，识别警告提示并应用斜体样式，移除 think 标签
const formatMessageWithWarning = (text) => {
  if (!text) return ''
  
  // 先移除 think 标签（不在主内容中显示），支持两种标签格式
  // 先移除完整的标签对
  let content = text.replace(/<(?:think|redacted_reasoning)>[\s\S]*?<\/(?:think|redacted_reasoning)>/gi, '')
  // 再移除未闭合的开始标签及其内容（流式输出时的情况）
  content = content.replace(/<(?:think|redacted_reasoning)>[\s\S]*$/gi, '')
  
  // 使用 marked 解析 Markdown
  let html = formatEnhancedMarkdown(content)
  
  // 处理警告提示（以 ⚠️ 开头，到第一个换行或文本结束）- 在 HTML 中处理
  html = html.replace(/(⚠️[^：:]*[：:][^<\n]*)/g, '<span class="warning-text">$1</span>')
  
  return html
}

// 在 Markdown 文本中先渲染 LaTeX 为 KaTeX HTML
const renderMathInText = (text) => {
  if (!text) return ''
  
  let result = text

  // 先处理块级公式：$$ ... $$
  result = result.replace(/\$\$([\s\S]+?)\$\$/g, (match, tex) => {
    const html = katex.renderToString(tex.trim(), {
      displayMode: true,
      throwOnError: false
    })
    return html
  })

  // 再处理行内公式：$ ... $（避免与块级公式冲突）
  result = result.replace(/\$([^$\n]+?)\$/g, (match, tex) => {
    const html = katex.renderToString(tex.trim(), {
      displayMode: false,
      throwOnError: false
    })
    return html
  })

  return result
}

// 使用 marked 库进行 Markdown 格式化
const formatEnhancedMarkdown = (text) => {
  if (!text) return ''
  
  try {
    // 先把 LaTeX 替换为 KaTeX HTML，再交给 marked 解析 Markdown
    const source = renderMathInText(text)
    const html = marked.parse(source)
    return html
  } catch (error) {
    console.error('Markdown 解析错误:', error)
    // 降级处理：简单转义并换行
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
  }
}

// 简单的 Markdown 格式化（用于流式输出等场景）
const formatMarkdown = (text) => {
  if (!text) return ''
  
  try {
    // 先把 LaTeX 替换为 KaTeX HTML，再交给 marked 解析 Markdown
    const source = renderMathInText(text)
    return marked.parse(source)
  } catch (error) {
    console.error('Markdown 解析错误:', error)
    return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>')
  }
}
</script>

<style scoped>
.chat-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #fff;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.message-wrapper {
  display: flex;
}

.message {
  max-width: 80%;
  display: flex;
}

.user-message {
  margin-left: auto;
}

.assistant-message {
  margin-right: auto;
}

.message-content {
  padding: 12px 16px;
  border-radius: 8px;
  position: relative;
}

.user-message .message-content {
  background-color: #409eff;
  color: #fff;
}

.assistant-message .message-content {
  background-color: #f0f2f5;
  color: #303133;
}

.tool-calls-section {
  margin: 12px 0;
}

.message-text {
  line-height: 1.6;
  word-wrap: break-word;
}

.message-text :deep(code) {
  background-color: rgba(0, 0, 0, 0.1);
  padding: 2px 4px;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
}

.message-text :deep(pre) {
  background-color: rgba(0, 0, 0, 0.05);
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  margin: 8px 0;
}

.warning-text {
  font-style: italic;
  color: #909399;
}

.message-time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 6px;
}

.assistant-message .message-time {
  color: #909399;
}

.streaming-cursor {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.input-container {
  border-top: 1px solid #e4e7ed;
  padding: 12px;
  background-color: #fff;
}

.input-toolbar {
  margin-bottom: 8px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.mode-chip {
  font-weight: 600;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 8px;
}

.study-style-toggle {
  margin-left: 8px;
}

.citation-switch {
  margin-left: 4px;
}

.variant-form {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.variant-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.variant-label {
  font-size: 13px;
  color: #606266;
}

.variant-results {
  margin-top: 16px;
  max-height: 360px;
  overflow-y: auto;
}

.variant-card {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fafafa;
}

.variant-meta {
  margin-bottom: 8px;
}

.ml6 {
  margin-left: 6px;
}

.variant-stem {
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 8px;
}

.variant-options {
  margin: 0 0 10px 16px;
  padding: 0;
  font-size: 13px;
  color: #303133;
}

.variant-answer-block {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.variant-rationale {
  margin-top: 6px;
}

/* Think 内容样式 */
.think-section {
  margin-top: 0;
  margin-bottom: 5px;
  border-bottom: 1px solid #e4e7ed;
  border-radius: 6px;
  background-color: #fafbfc;
  padding: 3px 8px;
}

.think-collapse :deep(.el-collapse-item__header) {
  font-size: 12px;
  color: #909399;
  padding: 3px 0;
  height: auto;
  line-height: 1.5;
  border-radius: 4px;
  background-color: transparent;
}

.think-collapse :deep(.el-collapse-item__content) {
  padding: 0;
  padding-bottom: 3px;
}

.think-content {
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.5;
  color: #606266;
  margin-top: 8px;
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
}

.think-content :deep(h1),
.think-content :deep(h2),
.think-content :deep(h3),
.think-content :deep(h4) {
  margin: 8px 0 4px 0;
  font-weight: 600;
  color: #303133;
}

.think-content :deep(h1) { font-size: 18px; }
.think-content :deep(h2) { font-size: 16px; }
.think-content :deep(h3) { font-size: 14px; }
.think-content :deep(h4) { font-size: 13px; }

.think-content :deep(ul),
.think-content :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.think-content :deep(li) {
  margin: 4px 0;
}

/* 主消息内容也支持增强的 Markdown */
.message-text :deep(h1),
.message-text :deep(h2),
.message-text :deep(h3),
.message-text :deep(h4) {
  margin: 12px 0 6px 0;
  font-weight: 600;
}

.message-text :deep(h1) { font-size: 20px; }
.message-text :deep(h2) { font-size: 18px; }
.message-text :deep(h3) { font-size: 16px; }
.message-text :deep(h4) { font-size: 14px; }

.message-text :deep(ul),
.message-text :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
}

.message-text :deep(li) {
  margin: 4px 0;
}

.message-text :deep(ul li) {
  list-style-type: disc;
}

.message-text :deep(ol li) {
  list-style-type: decimal;
}

/* 嵌套列表样式 */
.message-text :deep(ul ul),
.message-text :deep(ol ul) {
  list-style-type: circle;
}

.message-text :deep(ul ul ul),
.message-text :deep(ol ul ul) {
  list-style-type: square;
}

/* 表格样式 - 支持 marked 生成的标准表格 */
.message-text :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 12px 0;
  font-size: 14px;
}

.message-text :deep(table th),
.message-text :deep(table td) {
  border: 1px solid #e4e7ed;
  padding: 8px 12px;
  text-align: left;
}

.message-text :deep(table th) {
  background-color: #f5f7fa;
  font-weight: 600;
}

.message-text :deep(table tr:nth-child(even)) {
  background-color: #fafafa;
}

/* 代码块样式 */
.message-text :deep(pre) {
  background-color: #f6f8fa;
  border-radius: 6px;
  padding: 12px;
  overflow-x: auto;
  margin: 12px 0;
}

.message-text :deep(pre code) {
  background-color: transparent;
  padding: 0;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.5;
}

/* 行内代码样式 */
.message-text :deep(code) {
  background-color: rgba(175, 184, 193, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 0.9em;
}

/* 引用块样式 */
.message-text :deep(blockquote) {
  border-left: 4px solid #dfe2e5;
  margin: 12px 0;
  padding: 8px 16px;
  color: #6a737d;
  background-color: #f6f8fa;
}

/* 链接样式 */
.message-text :deep(a) {
  color: #409eff;
  text-decoration: none;
}

.message-text :deep(a:hover) {
  text-decoration: underline;
}

/* 水平线样式 */
.message-text :deep(hr) {
  border: none;
  border-top: 1px solid #e4e7ed;
  margin: 16px 0;
}

/* 段落样式 */
.message-text :deep(p) {
  margin: 8px 0;
  line-height: 1.6;
}

/* 强调样式 */
.message-text :deep(strong) {
  font-weight: 600;
}

.message-text :deep(em) {
  font-style: italic;
}
</style>
