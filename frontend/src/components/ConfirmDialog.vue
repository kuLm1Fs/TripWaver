<template>
  <el-dialog
    v-model="dialogVisible"
    :title="title"
    width="420px"
    :close-on-click-modal="false"
    class="confirm-dialog"
  >
    <div class="confirm-body">
      <div class="confirm-icon-wrap">
        <el-icon :size="48" :color="iconColor">
          <WarnTriangleFilled v-if="type === 'danger'" />
          <WarningFilled v-else-if="type === 'warning'" />
          <InfoFilled v-else />
        </el-icon>
      </div>
      <p class="confirm-message">{{ message }}</p>
    </div>

    <template #footer>
      <div class="confirm-footer">
        <el-button @click="handleCancel">{{ cancelText }}</el-button>
        <el-button :type="confirmType" :loading="loading" @click="handleConfirm">
          {{ confirmText }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarnTriangleFilled, WarningFilled, InfoFilled } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  type?: 'danger' | 'warning' | 'info'
  loading?: boolean
}>(), {
  title: '',
  confirmText: '确认',
  cancelText: '取消',
  type: 'danger',
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  cancel: []
}>()

const dialogVisible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const iconColor = computed(() => {
  switch (props.type) {
    case 'danger':
      return '#F56C6C'
    case 'warning':
      return '#E6A23C'
    default:
      return '#409EFF'
  }
})

const confirmType = computed(() => {
  return props.type === 'info' ? 'primary' : props.type
})

const handleConfirm = () => {
  emit('confirm')
}

const handleCancel = () => {
  emit('update:modelValue', false)
  emit('cancel')
}
</script>

<style scoped>
.confirm-body {
  text-align: center;
  padding: 8px 0 0;
}

.confirm-icon-wrap {
  margin-bottom: 16px;
}

.confirm-message {
  color: #303133;
  font-size: 15px;
  line-height: 1.6;
  margin: 0;
}

.confirm-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
