<template>
  <el-dialog v-model="visible" title="分享行程" width="480px" @close="handleClose">
    <div v-if="!shareUrl" class="share-form">
      <el-form label-width="80px">
        <el-form-item label="有效期">
          <el-select v-model="expireDays" style="width: 100%">
            <el-option label="7天" :value="7" />
            <el-option label="30天" :value="30" />
            <el-option label="永久" :value="0" />
          </el-select>
        </el-form-item>
      </el-form>
      <el-button type="primary" :loading="loading" @click="handleCreate" style="width: 100%">
        生成分享链接
      </el-button>
    </div>

    <div v-else class="share-result">
      <p class="share-hint">扫描二维码或复制链接邀请好友加入投票</p>
      <div class="qr-wrap">
        <img v-if="qrDataUrl" :src="qrDataUrl" class="qr-image" alt="分享二维码" />
      </div>
      <el-input v-model="shareUrl" readonly size="small">
        <template #append>
          <el-button @click="handleCopy">复制</el-button>
        </template>
      </el-input>
      <p class="share-expire" v-if="expireAt">
        有效期至：{{ new Date(expireAt).toLocaleDateString('zh-CN') }}
      </p>
      <p class="share-expire" v-else>永久有效</p>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import QRCode from 'qrcode'
import { createShareLink } from '@/api/share'

const props = defineProps<{
  modelValue: boolean
  itineraryId: number
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const visible = ref(props.modelValue)
const loading = ref(false)
const expireDays = ref(7)
const shareUrl = ref('')
const expireAt = ref<string | null>(null)
const qrDataUrl = ref('')

watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (!val) {
      shareUrl.value = ''
      expireAt.value = null
      qrDataUrl.value = ''
    }
  },
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleCreate = async () => {
  loading.value = true
  try {
    const res = await createShareLink({
      itinerary_id: props.itineraryId,
      expire_days: expireDays.value,
    })
    shareUrl.value = `${window.location.origin}${res.share_url}`
    expireAt.value = res.expire_at
    qrDataUrl.value = await QRCode.toDataURL(shareUrl.value, {
      width: 200,
      margin: 2,
      color: { dark: '#303133', light: '#ffffff' },
    })
  } catch {
    ElMessage.error('生成分享链接失败')
  } finally {
    loading.value = false
  }
}

const handleCopy = async () => {
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    ElMessage.success('已复制到剪贴板')
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
}

const handleClose = () => {
  shareUrl.value = ''
  expireAt.value = null
  qrDataUrl.value = ''
}
</script>

<style scoped>
.share-result {
  text-align: center;
}

.share-hint {
  color: #909399;
  font-size: 13px;
  margin: 0 0 16px;
}

.qr-wrap {
  display: flex;
  justify-content: center;
  margin-bottom: 16px;
}

.qr-image {
  width: 180px;
  height: 180px;
  border-radius: 8px;
  border: 1px solid #ebeef5;
  padding: 8px;
  background: #fff;
}

.share-expire {
  margin-top: 10px;
  color: #909399;
  font-size: 13px;
}
</style>
