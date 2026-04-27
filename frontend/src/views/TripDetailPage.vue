<template>
  <div class="trip-detail" v-if="trip">
    <!-- 行程概览 -->
    <el-card class="overview-card">
      <template #header>
        <div class="card-header">
          <h2>{{ trip.destination }} {{ trip.days }}天游</h2>
          <div class="header-actions">
            <el-button size="small" @click="showShareDialog = true" :disabled="!trip.itinerary_id">
              分享
            </el-button>
            <el-button
              v-if="isCreator && !tripLocked"
              type="warning"
              size="small"
              @click="handleLock"
            >
              锁定行程
            </el-button>
            <el-button
              v-if="isCreator && tripLocked"
              size="small"
              @click="handleUnlock"
            >
              解锁行程
            </el-button>
          </div>
        </div>
      </template>
      <p class="overview-text">{{ trip.overview }}</p>
      <el-tag v-if="tripLocked" type="success" style="margin-top: 10px">已锁定</el-tag>
    </el-card>

    <!-- 地图展示 POI + 路线 -->
    <el-card class="map-card" v-if="mapPois.length > 0">
      <template #header>
        <div class="card-header">
          <h3>地图总览</h3>
          <el-tag v-if="routeLoading" type="info" size="small">路线加载中...</el-tag>
          <el-tag v-else-if="routeInfo" type="success" size="small">
            共 {{ (routeInfo.total_distance / 1000).toFixed(1) }}km · 步行约 {{ Math.ceil(routeInfo.total_duration / 60) }}分钟
          </el-tag>
        </div>
      </template>
      <MapView
        :show-search="false"
        map-height="400px"
        :pois="mapPois"
        :center="mapCenter"
        :zoom="14"
        :route-segments="routeSegments"
      />
    </el-card>

    <!-- 多方案投票区 -->
    <VotePanel
      v-if="trip.itinerary_id && planOptions.length > 0"
      :itinerary-id="trip.itinerary_id"
      :plan-options="planOptions"
      :vote-stats="voteStats"
      :current-user-vote="currentUserVote"
      :is-locked="tripLocked"
      @voted="handleVoted"
      @plan-changed="handlePlanChanged"
    />

    <!-- 默认方案展示 -->
    <el-card class="plan-card" v-if="planOptions.length === 0">
      <template #header><h3>行程方案</h3></template>
      <div class="day-cards">
        <el-card v-for="item in trip.items" :key="item.day" class="day-card">
          <template #header><h3>{{ item.title }}</h3></template>
          <p>{{ item.summary }}</p>
          <div class="places-list">
            <div v-for="place in item.places" :key="place.name" class="place-item">
              <span class="place-name">{{ place.name }}</span>
              <el-tag size="small">{{ place.category }}</el-tag>
              <p class="place-reason">{{ place.reason }}</p>
            </div>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- 成员列表 -->
    <MemberList v-if="members.length > 0" :members="members" />

    <!-- 分享弹窗 -->
    <ShareDialog
      v-if="trip.itinerary_id"
      v-model="showShareDialog"
      :itinerary-id="trip.itinerary_id"
    />

    <el-button @click="goBack" style="display: block; margin: 30px auto;">
      返回首页
    </el-button>
  </div>

  <div v-else class="loading-wrapper">
    <el-skeleton :rows="6" animated />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useTripStore } from '@/stores/trip'
import { apiClient } from '@/api/itinerary'
import { lockItinerary } from '@/api/lock'
import VotePanel from '@/components/VotePanel.vue'
import ShareDialog from '@/components/ShareDialog.vue'
import MemberList from '@/components/MemberList.vue'
import MapView from '@/components/MapView.vue'
import type { ItineraryResponse, PlanOption } from '@/types/itinerary'
import type { Member, VoteStat } from '@/types/share'

interface RouteSegment {
  from: number
  to: number
  points: { lng: number; lat: number }[]
  distance: number
  duration: number
  from_name?: string
  to_name?: string
}

interface RouteInfo {
  segments: RouteSegment[]
  total_distance: number
  total_duration: number
}

const props = defineProps<{ id: string }>()

const router = useRouter()
const tripStore = useTripStore()

const trip = ref<ItineraryResponse | null>(null)
const members = ref<Member[]>([])
const voteStats = ref<VoteStat[]>([])
const currentUserVote = ref<number | null>(null)
const isCreator = ref(false)
const tripLocked = ref(false)
const showShareDialog = ref(false)
const selectedPlanIndex = ref(0)
const routeSegments = ref<RouteSegment[]>([])
const routeInfo = ref<RouteInfo | null>(null)
const routeLoading = ref(false)

const planOptions = computed((): PlanOption[] => {
  return trip.value?.plan_options || []
})

// 地图 POI 标记（根据选中方案）
const mapPois = computed(() => {
  if (!trip.value) return []

  // 从选中方案中提取 POI
  const options = trip.value.plan_options || []
  let items = trip.value.items

  if (options.length > 0 && selectedPlanIndex.value < options.length) {
    items = options[selectedPlanIndex.value].items || []
  }

  const pois: { name: string; lng: number; lat: number; category?: string; address?: string }[] = []
  const seen = new Set<string>()
  for (const item of items) {
    for (const place of item.places) {
      if (place.longitude && place.latitude && !seen.has(place.name)) {
        seen.add(place.name)
        pois.push({
          name: place.name,
          lng: place.longitude,
          lat: place.latitude,
          category: place.category,
          address: place.address || undefined,
        })
      }
    }
  }
  return pois
})

const mapCenter = computed((): [number, number] | undefined => {
  if (mapPois.value.length > 0) {
    return [mapPois.value[0].lng, mapPois.value[0].lat]
  }
  return undefined
})

const fetchTripDetail = async () => {
  try {
    const response = await apiClient.get(`/itineraries/${props.id}`)
    const data = response.data
    trip.value = {
      itinerary_id: data.itinerary_id || data.id,
      destination: data.destination,
      overview: data.overview || '',
      items: data.items || [],
      plan_options: data.plan_options || [],
    }
    members.value = data.members || []
    voteStats.value = data.vote_stats || []
    currentUserVote.value = data.current_user_vote ?? null
    isCreator.value = data.is_creator ?? false
    tripLocked.value = data.is_locked ?? false
  } catch {
    ElMessage.error('获取行程详情失败')
  }
}

const handleVoted = (stats: VoteStat[], planIndex: number) => {
  voteStats.value = stats
  currentUserVote.value = planIndex
}

const handlePlanChanged = (planIndex: number) => {
  selectedPlanIndex.value = planIndex
  fetchRoute(planIndex)
}

const fetchRoute = async (planIndex: number = 0) => {
  if (!trip.value?.itinerary_id) return
  routeLoading.value = true
  try {
    const response = await apiClient.get(`/itineraries/${trip.value.itinerary_id}/route`, {
      params: { plan_index: planIndex },
    })
    routeInfo.value = response.data
    routeSegments.value = response.data.segments || []
  } catch {
    // 路线获取失败不影响主流程
    routeSegments.value = []
    routeInfo.value = null
  } finally {
    routeLoading.value = false
  }
}

const handleLock = async () => {
  if (!trip.value?.itinerary_id) return
  try {
    await ElMessageBox.confirm('锁定后投票将结束，确认锁定？', '确认锁定')
    const res = await lockItinerary(trip.value.itinerary_id, 'lock')
    tripLocked.value = res.is_locked
    ElMessage.success('行程已锁定')
  } catch {
    // 用户取消
  }
}

const handleUnlock = async () => {
  if (!trip.value?.itinerary_id) return
  try {
    const res = await lockItinerary(trip.value.itinerary_id, 'unlock')
    tripLocked.value = res.is_locked
    ElMessage.success('行程已解锁')
  } catch {
    ElMessage.error('解锁失败')
  }
}

const goBack = () => {
  router.push('/')
}

onMounted(async () => {
  // 优先从 store 取，否则从 API 拉取
  if (tripStore.currentTrip?.itinerary_id === Number(props.id)) {
    trip.value = tripStore.currentTrip
    await fetchTripDetail()
  } else {
    await fetchTripDetail()
  }
  // 拉取路线数据
  fetchRoute(selectedPlanIndex.value)
})
</script>

<style scoped>
.trip-detail {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.overview-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.overview-text {
  color: #606266;
  line-height: 1.6;
}

.plan-card {
  margin-bottom: 20px;
}

.map-card {
  margin-bottom: 20px;
}

.map-card h3 {
  margin: 0;
}

.day-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.day-card {
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.08);
}

.places-list {
  margin-top: 12px;
}

.place-item {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
}

.place-item:last-child {
  border-bottom: none;
}

.place-name {
  font-weight: 600;
  margin-right: 8px;
}

.place-reason {
  color: #909399;
  font-size: 13px;
  margin: 4px 0 0;
}

.loading-wrapper {
  max-width: 900px;
  margin: 40px auto;
  padding: 20px;
}
</style>
