<template>
  <el-card class="trip-form-card">
    <template #header>
      <h2>📝 行程规划助手</h2>
    </template>
    <el-form :model="form" label-width="100px" @submit.prevent="handleSubmit">
      <el-form-item
        label="目的地"
        prop="destination"
        :rules="[{ required: true, message: '请输入目的地', trigger: 'blur' }]"
      >
        <el-input v-model="form.destination" placeholder="例如：上海、成都" size="large" />
      </el-form-item>

      <el-form-item
        label="游玩天数"
        prop="days"
        :rules="[
          { required: true, message: '请选择游玩天数', trigger: 'change' },
          { type: 'number', min: 1, max: 30, message: '天数范围1-30天', trigger: 'change' }
        ]"
      >
        <el-input-number v-model="form.days" :min="1" :max="30" size="large" />
      </el-form-item>

      <el-form-item label="兴趣偏好">
        <el-select
          v-model="selectedInterests"
          multiple
          placeholder="选择或自定义兴趣标签"
          size="large"
          allow-create
          style="width: 100%"
        >
          <el-option label="美食" value="food" />
          <el-option label="博物馆" value="museum" />
          <el-option label="历史文化" value="history" />
          <el-option label="自然风光" value="nature" />
          <el-option label="购物" value="shopping" />
          <el-option label="亲子" value="family" />
          <el-option label="夜生活" value="nightlife" />
        </el-select>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          size="large"
          @click="handleSubmit"
          :loading="props.loading"
          style="width: 100%"
        >
          {{ props.loading ? '生成中...' : '生成行程' }}
        </el-button>
      </el-form-item>
    </el-form>
  </el-card>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ItineraryRequest } from '@/types/itinerary'

const emit = defineEmits<{
  submit: [request: ItineraryRequest]
}>()

const props = defineProps<{
  loading?: boolean
}>()

const form = ref<ItineraryRequest>({
  destination: '',
  days: 1,
  interests: [],
})

const selectedInterests = ref<string[]>([])

const handleSubmit = () => {
  form.value.interests = selectedInterests.value
  emit('submit', form.value)
}
</script>

<style scoped>
.trip-form-card {
  max-width: 600px;
  margin: 20px auto;
}
</style>
