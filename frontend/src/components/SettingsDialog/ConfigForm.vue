<template>
  <el-form :model="localConfig" label-width="120px" label-position="left">
    <!-- 模型选择 -->
    <el-form-item label="模型">
      <el-select
        v-model="localConfig.model"
        filterable
        allow-create
        default-first-option
        :reserve-keyword="false"
        placeholder="选择或输入模型名称"
        style="width: 100%"
        @change="handleModelChange"
      >
        <el-option
          v-for="model in availableModels"
          :key="model"
          :label="model"
          :value="model"
        />
      </el-select>
      <div class="form-tip">可以从列表选择，也可以手动输入自定义模型名称</div>
    </el-form-item>

    <!-- 保存按钮 -->
    <el-form-item>
      <el-button type="primary" @click="handleSave" :loading="saving">
        保存配置
      </el-button>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, watch, computed } from 'vue'

const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  modelLists: {
    type: Object,
    default: () => ({})
  },
  // 允许指定 binding（用于 embedding 场景）
  defaultBinding: {
    type: String,
    default: 'siliconflow'
  }
})

const emit = defineEmits(['update'])

const SILICONFLOW_HOST = 'https://api.siliconflow.cn/v1'
const OPENAI_DEFAULT_HOST = 'https://api.deepseek.com'

function defaultHostForBinding(binding) {
  if (binding === 'siliconflow') return SILICONFLOW_HOST
  if (binding === 'openai') return OPENAI_DEFAULT_HOST
  return ''
}

const localConfig = ref({
  binding: props.defaultBinding,
  model: '',
  host: defaultHostForBinding(props.defaultBinding)
})

const saving = ref(false)

const availableModels = computed(() => {
  return props.modelLists[props.defaultBinding] || []
})

watch(() => props.config, (newConfig) => {
  if (newConfig) {
    const binding = props.defaultBinding
    localConfig.value = {
      binding,
      model: newConfig.model || '',
      host: (newConfig.host || '').trim() || defaultHostForBinding(binding)
    }
  }
}, { immediate: true })

// 模型变化
function handleModelChange() {
  // 可以在这里添加验证逻辑
}

function handleSave() {
  saving.value = true

  const binding = props.defaultBinding
  const host =
    binding === 'siliconflow'
      ? SILICONFLOW_HOST
      : (localConfig.value.host || '').trim() || OPENAI_DEFAULT_HOST

  emit('update', {
    binding,
    model: localConfig.value.model,
    host
  })
  saving.value = false
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
