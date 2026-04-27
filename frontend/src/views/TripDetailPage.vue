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

    <!-- 锁定行程弹窗 -->
    <el-dialog
      v-model="showLockDialog"
      title=""
      width="480px"
      :close-on-click-modal="false"
      class="lock-dialog"
    >
      <div class="lock-dialog-body">
        <div class="lock-icon-wrap">
          <el-icon :size="48" color="#E6A23C"><WarningFilled /></el-icon>
        </div>
        <h3 class="lock-title">确认锁定行程？</h3>
        <p class="lock-desc">锁定后将结束投票，最终方案确定后不可更改。</p>

        <!-- 投票统计 -->
        <div class="lock-vote-summary">
          <div class="lock-vote-header">当前投票情况</div>
          <div
            v-for="(option, index) in planOptions"
            :key="index"
            class="lock-plan-row"
            :class="{ 'is-leading': getLockWinnerIndex() === index && getTotalLockVotes() > 0 }"
          >
            <div class="lock-plan-info">
              <span class="lock-plan-name">{{ option.title || `方案${index + 1}` }}</span>
              <el-tag
                v-if="getLockWinnerIndex() === index && getTotalLockVotes() > 0"
                type="success"
                size="small"
                effect="dark"
              >
                领先
              </el-tag>
            </div>
            <div class="lock-plan-votes">
              <el-progress
                :percentage="getLockVotePercentage(index)"
                :stroke-width="10"
                :color="getLockWinnerIndex() === index ? '#67c23a' : '#dcdfe6'"
                :show-text="false"
                style="flex: 1"
              />
              <span class="lock-vote-num">{{ getLockVoteCount(index) }}票</span>
            </div>
          </div>
          <div v-if="getTotalLockVotes() === 0" class="lock-no-votes">
            暂无人投票，锁定后将以第一个方案为准
          </div>
        </div>
      </div>

      <template #footer>
        <div class="lock-dialog-footer">
          <el-button @click="showLockDialog = false">再想想</el-button>
          <el-button type="warning" @click="confirmLock" :loading="lockLoading">
            确认锁定
          </el-button>
        </div>
      </template>
    </el-dialog>

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
import { ElMessage } from 'element-plus'
import { WarningFilled } from '@element-plus/icons-vue'
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
const showLockDialog = ref(false)
const lockLoading = ref(false)
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

const handleLock = () => {
  if (!trip.value?.itinerary_id) return
  showLockDialog.value = true
}

// 锁定弹窗内的投票统计
const getLockVoteCount = (index: number): number => {
  const stat = voteStats.value.find((s) => s.plan_index === index)
  return stat?.count || 0
}

const getTotalLockVotes = (): number => {
  return voteStats.value.reduce((sum, s) => sum + s.count, 0)
}

const getLockVotePercentage = (index: number): number => {
  const total = getTotalLockVotes()
  if (total === 0) return 0
  return Math.round((getLockVoteCount(index) / total) * 100)
}

const getLockWinnerIndex = (): number => {
  let maxVotes = 0
  let winner = 0
  voteStats.value.forEach((s) => {
    if (s.count > maxVotes) {
      maxVotes = s.count
      winner = s.plan_index
    }
  })
  return winner
}

const confirmLock = async () => {
  if (!trip.value?.itinerary_id) return
  lockLoading.value = true
  try {
    const winnerIndex = getTotalLockVotes() > 0 ? getLockWinnerIndex() : 0
    const res = await lockItinerary(trip.value.itinerary_id, 'lock', winnerIndex)
    tripLocked.value = res.is_locked
    showLockDialog.value = false
    ElMessage.success('行程已锁定')
  } catch {
    ElMessage.error('锁定失败')
  } finally {
    lockLoading.value = false
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

/* 锁定弹窗样式 */
.lock-dialog-body {
  text-align: center;
  padding: 0 8px;
}

.lock-icon-wrap {
  margin-bottom: 16px;
}

.lock-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0 0 8px;
}

.lock-desc {
  color: #909399;
  font-size: 14px;
  margin: 0 0 24px;
}

.lock-vote-summary {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
  text-align: left;
}

.lock-vote-header {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 12px;
}

.lock-plan-row {
  padding: 10px 12px;
  border-radius: 6px;
  margin-bottom: 8px;
  background: #fff;
  border: 1px solid #ebeef5;
  transition: all 0.2s;
}

.lock-plan-row:last-child {
  margin-bottom: 0;
}

.lock-plan-row.is-leading {
  border-color: #67c23a;
  background: #f0f9eb;
}

.lock-plan-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.lock-plan-name {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.lock-plan-votes {
  display: flex;
  align-items: center;
  gap: 10px;
}

.lock-vote-num {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  min-width: 36px;
  text-align: right;
}

.lock-no-votes {
  color: #c0c4cc;
  font-size: 13px;
  text-align: center;
  padding: 8px 0;
}

.lock-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
