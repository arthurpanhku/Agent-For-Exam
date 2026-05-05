<template>
  <el-form :model="localConfig" label-width="120px" label-position="left">
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

    <el-form-item>
      <el-button type="primary" @click="handleSave" :loading="saving">
        保存配置
      </el-button>
      <el-button @click="handleTest" :loading="testing">
        测试联通
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
  defaultBinding: {
    type: String,
    default: 'siliconflow'
  }
})

const emit = defineEmits(['update', 'test'])

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
const testing = ref(false)

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

function handleModelChange() {
}

function handleSave() {
  saving.value = true

  emit('update', buildPayload())
  saving.value = false
}

function handleTest() {
  testing.value = true
  emit('test', buildPayload())
  testing.value = false
}

function buildPayload() {
  const binding = props.defaultBinding
  const host =
    binding === 'siliconflow'
      ? SILICONFLOW_HOST
      : (localConfig.value.host || '').trim() || OPENAI_DEFAULT_HOST

  return {
    binding,
    model: localConfig.value.model,
    host
  }
}
</script>

<style scoped>
.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
