<template>
  <el-card class="trip-form-card">
    <template #header>
      <h2>📝 行程规划助手</h2>
    </template>

    <!-- 地图选点 -->
    <div class="map-section">
      <p class="section-label">选择目的地</p>
      <MapView
        :show-search="true"
        map-height="350px"
        @place-selected="handlePlaceSelected"
        @place-cleared="handlePlaceCleared"
      />
    </div>

    <el-divider />

    <el-form :model="form" label-width="100px" @submit.prevent="handleSubmit">
      <el-form-item label="目的地">
        <el-input
          v-model="form.destination"
          placeholder="在地图上搜索或点击选择"
          size="large"
          readonly
        />
      </el-form-item>

      <el-form-item label="游玩天数">
        <el-input-number v-model="form.days" :min="1" :max="30" size="large" />
      </el-form-item>

      <!-- 范围选择 -->
      <el-form-item label="游玩范围">
        <div class="range-selector">
          <el-radio-group v-model="form.range_mode" size="large">
            <el-radio-button value="walking">
              <el-icon><Position /></el-icon> 步行
            </el-radio-button>
            <el-radio-button value="transit">
              <el-icon><Van /></el-icon> 公交
            </el-radio-button>
          </el-radio-group>
          <div class="range-slider">
            <el-slider
              v-model="form.range_minutes"
              :min="5"
              :max="60"
              :step="5"
              show-stops
              :marks="rangeMarks"
            />
            <span class="range-label">{{ form.range_minutes }} 分钟</span>
          </div>
        </div>
      </el-form-item>

      <!-- 兴趣偏好 -->
      <el-form-item label="兴趣偏好">
        <el-select
          v-model="selectedInterests"
          multiple
          filterable
          allow-create
          default-first-option
          placeholder="选择预设标签或输入自定义标签后回车"
          size="large"
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
        <div class="tag-hint">可直接输入自定义标签，如"咖啡"、"拍照"、"书店"等</div>
      </el-form-item>

      <el-form-item>
        <el-button
          type="primary"
          size="large"
          @click="handleSubmit"
          :loading="props.loading"
          :disabled="!form.destination"
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
import { ElMessage } from 'element-plus'
import { Position, Van } from '@element-plus/icons-vue'
import MapView from '@/components/MapView.vue'
import type { ItineraryRequest } from '@/types/itinerary'

// 预设标签值集合，用于区分自定义标签
const PRESET_VALUES = new Set(['food', 'museum', 'history', 'nature', 'shopping', 'family', 'nightlife'])

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
  range_mode: 'walking',
  range_minutes: 20,
  custom_tags: [],
})

const selectedInterests = ref<string[]>([])

const rangeMarks: Record<number, string> = {
  5: '5',
  15: '15',
  30: '30',
  45: '45',
  60: '60',
}

const handlePlaceSelected = (place: { name: string; address?: string; location?: { lng: number; lat: number } }) => {
  form.value.destination = place.name
  if (place.location) {
    form.value.latitude = place.location.lat
    form.value.longitude = place.location.lng
  }
  if (place.address) {
    form.value.address = place.address
  }
}

const handlePlaceCleared = () => {
  form.value.destination = ''
  form.value.latitude = undefined
  form.value.longitude = undefined
  form.value.address = undefined
}

const handleSubmit = () => {
  if (!form.value.destination) {
    ElMessage.warning('请先在地图上选择目的地')
    return
  }
  // 分离预设标签和自定义标签
  form.value.interests = selectedInterests.value.filter(v => PRESET_VALUES.has(v))
  form.value.custom_tags = selectedInterests.value.filter(v => !PRESET_VALUES.has(v))
  emit('submit', form.value)
}
</script>

<style scoped>
.trip-form-card {
  max-width: 700px;
  margin: 20px auto;
}

.map-section {
  margin-bottom: 10px;
}

.section-label {
  margin: 0 0 8px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.range-selector {
  width: 100%;
}

.range-slider {
  margin-top: 12px;
  padding: 0 8px;
}

.range-label {
  display: inline-block;
  margin-top: 4px;
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
}

.tag-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
