<template>
  <div class="select-poi-page">
    <div class="page-header">
      <h2>选择您想去的地方</h2>
      <p class="subtitle">{{ destination }} · {{ days }}天行程</p>
    </div>

    <div class="page-content">
      <!-- 左侧：候选 POI 列表 -->
      <div class="poi-list-panel">
        <div class="list-toolbar">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索地点..."
            prefix-icon="Search"
            clearable
            style="width: 200px"
          />
          <el-select v-model="filterCategory" placeholder="分类筛选" clearable style="width: 120px">
            <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
          </el-select>
          <span class="poi-count">共 {{ filteredPois.length }} 个地点</span>
        </div>

        <div class="poi-cards">
          <el-card
            v-for="poi in filteredPois"
            :key="poi.name"
            class="poi-card"
            :class="{ 'is-selected': selectedPois.has(poi.name) }"
            @click="togglePoi(poi)"
          >
            <div class="poi-card-header">
              <span class="poi-name">{{ poi.name }}</span>
              <el-check-tag v-if="selectedPois.has(poi.name)" type="primary">已选</el-check-tag>
            </div>
            <div class="poi-meta">
              <el-tag size="small" type="info">{{ poi.category }}</el-tag>
              <span v-if="poi.price" class="poi-price">{{ poi.price }}</span>
            </div>
            <p class="poi-reason">{{ poi.reason }}</p>
            <p v-if="poi.address" class="poi-address">{{ poi.address }}</p>
          </el-card>
        </div>
      </div>

      <!-- 右侧：已选摘要 + 生成按钮 -->
      <div class="selection-panel">
        <el-card class="selection-card">
          <template #header>
            <div class="selection-header">
              <span>已选地点</span>
              <el-badge :value="selectedPois.size" type="primary" />
            </div>
          </template>

          <div v-if="selectedPois.size === 0" class="empty-selection">
            <p>点击左侧卡片选择想去的地方</p>
          </div>

          <div v-else class="selected-list">
            <div v-for="poi in selectedPoisArray" :key="poi.name" class="selected-item">
              <span class="selected-name">{{ poi.name }}</span>
              <el-tag size="small" type="info">{{ poi.category }}</el-tag>
              <el-button
                :icon="Close"
                size="small"
                circle
                text
                @click="togglePoi(poi)"
              />
            </div>
          </div>

          <div class="selection-actions">
            <el-button @click="clearSelection">清空</el-button>
            <el-button
              type="primary"
              :loading="generating"
              :disabled="selectedPois.size === 0"
              @click="handleGenerate"
            >
              生成行程
            </el-button>
          </div>

          <el-alert
            v-if="selectedPois.size > 0 && selectedPois.size < 3"
            type="warning"
            :closable="false"
            show-icon
            style="margin-top: 12px"
          >
            建议至少选择 3 个地点，以便生成更丰富的行程
          </el-alert>
        </el-card>
      </div>
    </div>

    <!-- 生成结果弹窗 -->
    <el-dialog
      v-model="showResultDialog"
      title="行程生成成功"
      width="600px"
      :close-on-click-modal="false"
    >
      <div v-if="generatedItinerary" class="result-summary">
        <h3>{{ generatedItinerary.destination }} {{ generatedItinerary.items?.length || 0 }}天游</h3>
        <p class="overview">{{ generatedItinerary.overview }}</p>
        <div class="day-list">
          <div v-for="item in generatedItinerary.items" :key="item.day" class="result-day">
            <strong>Day {{ item.day }}: {{ item.title }}</strong>
            <ul>
              <li v-for="place in item.places" :key="place.name">
                {{ place.name }} <span class="place-cat">({{ place.category }})</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showResultDialog = false">继续选择</el-button>
        <el-button type="primary" @click="goToDetail">查看详情</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Close } from '@element-plus/icons-vue'
import { getCandidates, planCustomItinerary } from '@/api/itinerary'
import { useTripStore } from '@/stores/trip'
import type { CandidatePlace, ItineraryResponse, ItineraryRequest } from '@/types/itinerary'

const router = useRouter()
const route = useRoute()
const tripStore = useTripStore()

const destination = ref((route.query.destination as string) || '')
const days = ref(Number(route.query.days) || 1)
const interests = ref<string[]>(route.query.interests ? (route.query.interests as string).split(',') : [])
const rangeMode = ref<'walking' | 'transit'>((route.query.range_mode as 'walking' | 'transit') || 'walking')
const rangeMinutes = ref(Number(route.query.range_minutes) || 20)
const latitude = ref(route.query.latitude ? Number(route.query.latitude) : undefined)
const longitude = ref(route.query.longitude ? Number(route.query.longitude) : undefined)
const address = ref((route.query.address as string) || undefined)
const customTags = ref<string[]>(route.query.custom_tags ? (route.query.custom_tags as string).split(',') : [])

// POI 列表
const allPois = ref<CandidatePlace[]>([])
const loading = ref(true)
const searchKeyword = ref('')
const filterCategory = ref('')

// 已选 POI
const selectedPois = ref(new Set<string>())
const selectedPoisArray = computed(() =>
  allPois.value.filter((p) => selectedPois.value.has(p.name))
)

// 分类列表
const categories = computed(() => {
  const cats = new Set(allPois.value.map((p) => p.category))
  return Array.from(cats).sort()
})

// 过滤后的 POI
const filteredPois = computed(() => {
  let result = allPois.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(
      (p) =>
        p.name.toLowerCase().includes(kw) ||
        p.reason.toLowerCase().includes(kw) ||
        p.address?.toLowerCase().includes(kw)
    )
  }
  if (filterCategory.value) {
    result = result.filter((p) => p.category === filterCategory.value)
  }
  return result
})

// 生成状态
const generating = ref(false)
const showResultDialog = ref(false)
const generatedItinerary = ref<ItineraryResponse | null>(null)

const togglePoi = (poi: CandidatePlace) => {
  if (selectedPois.value.has(poi.name)) {
    selectedPois.value.delete(poi.name)
  } else {
    selectedPois.value.add(poi.name)
  }
  // 触发响应式更新
  selectedPois.value = new Set(selectedPois.value)
}

const clearSelection = () => {
  selectedPois.value = new Set()
}

const handleGenerate = async () => {
  if (selectedPois.value.size === 0) {
    ElMessage.warning('请至少选择一个地点')
    return
  }

  generating.value = true
  try {
    const request = {
      destination: destination.value,
      days: days.value,
      interests: interests.value,
      range_mode: rangeMode.value,
      range_minutes: rangeMinutes.value,
      custom_tags: customTags.value,
      latitude: latitude.value,
      longitude: longitude.value,
      address: address.value,
      selected_pois: selectedPoisArray.value,
    }

    const result = await planCustomItinerary(request)
    tripStore.setTrip(result)
    generatedItinerary.value = result
    showResultDialog.value = true
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail || '生成失败，请稍后重试')
  } finally {
    generating.value = false
  }
}

const goToDetail = () => {
  if (generatedItinerary.value?.itinerary_id) {
    router.push(`/trip/${generatedItinerary.value.itinerary_id}`)
  } else {
    showResultDialog.value = false
  }
}

// 加载候选 POI
onMounted(async () => {
  if (!destination.value) {
    ElMessage.error('缺少目的地参数')
    router.push('/')
    return
  }

  loading.value = true
  try {
    const request: ItineraryRequest = {
      destination: destination.value,
      days: days.value,
      interests: interests.value,
      range_mode: rangeMode.value,
      range_minutes: rangeMinutes.value,
      custom_tags: customTags.value,
      latitude: latitude.value,
      longitude: longitude.value,
      address: address.value,
    }
    const response = await getCandidates(request)
    allPois.value = response.pois
  } catch {
    ElMessage.error('获取候选地点失败')
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.select-poi-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px;
}

.subtitle {
  color: #909399;
  margin: 0;
}

.page-content {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.poi-list-panel {
  flex: 1;
  min-width: 0;
}

.list-toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 16px;
}

.poi-count {
  color: #909399;
  font-size: 13px;
  margin-left: auto;
}

.poi-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 12px;
  max-height: calc(100vh - 280px);
  overflow-y: auto;
  padding-right: 8px;
}

.poi-card {
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.poi-card:hover {
  transform: translateY(-2px);
}

.poi-card.is-selected {
  border-color: #409eff;
  background: #f0f7ff;
}

.poi-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.poi-name {
  font-weight: 600;
  font-size: 15px;
}

.poi-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.poi-price {
  color: #909399;
  font-size: 12px;
}

.poi-reason {
  color: #606266;
  font-size: 13px;
  margin: 0 0 4px;
  line-height: 1.4;
}

.poi-address {
  color: #c0c4cc;
  font-size: 12px;
  margin: 0;
}

.selection-panel {
  width: 320px;
  flex-shrink: 0;
  position: sticky;
  top: 20px;
}

.selection-card {
  background: #fafafa;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-selection {
  text-align: center;
  color: #909399;
  padding: 20px 0;
}

.selected-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 300px;
  overflow-y: auto;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

.selected-name {
  flex: 1;
  font-size: 14px;
}

.selection-actions {
  display: flex;
  gap: 8px;
  margin-top: 16px;
}

.result-summary h3 {
  margin: 0 0 8px;
}

.overview {
  color: #606266;
  margin: 0 0 16px;
}

.day-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.result-day {
  padding: 8px;
  background: #f5f7fa;
  border-radius: 4px;
}

.result-day strong {
  font-size: 14px;
}

.result-day ul {
  margin: 4px 0 0;
  padding-left: 20px;
}

.result-day li {
  font-size: 13px;
  color: #606266;
  margin-bottom: 2px;
}

.place-cat {
  color: #909399;
  font-size: 12px;
}
</style>
