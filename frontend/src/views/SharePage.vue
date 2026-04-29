<template>
  <div class="share-page" v-if="detail">
    <el-card class="overview-card">
      <template #header>
        <div class="card-header">
          <h2>{{ detail.destination }} {{ detail.days }}天游</h2>
          <el-tag v-if="detail.is_locked" type="success">已锁定</el-tag>
        </div>
      </template>
      <p>创建者：{{ detail.creator_nickname }}</p>
      <p>成员：{{ detail.members.length }}人</p>
    </el-card>

    <!-- 多方案投票 -->
    <VotePanel
      v-if="planOptions.length > 0"
      :itinerary-id="detail.itinerary_id"
      :plan-options="planOptions"
      :vote-stats="detail.vote_stats"
      :current-user-vote="detail.current_user_vote"
      :is-locked="detail.is_locked"
      @voted="handleVoted"
    />

    <!-- 方案详情展示 -->
    <el-card v-if="selectedPlan" class="plan-detail-card">
      <template #header><h3>{{ selectedPlan.title || '行程方案' }}</h3></template>
      <div class="day-cards">
        <DayCard v-for="item in selectedPlan.items" :key="item.day" :item="item" />
      </div>
    </el-card>

    <!-- 成员列表 -->
    <MemberList v-if="detail.members.length > 0" :members="detail.members" />

    <el-button @click="goHome" style="display: block; margin: 30px auto;">
      返回首页
    </el-button>
  </div>

  <div v-else-if="error" class="error-wrapper">
    <el-result icon="warning" :title="error" sub-title="分享链接可能已过期">
      <template #extra>
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </template>
    </el-result>
  </div>

  <div v-else class="loading-wrapper">
    <el-skeleton :rows="6" animated />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSharedItinerary } from '@/api/share'
import VotePanel from '@/components/VotePanel.vue'
import MemberList from '@/components/MemberList.vue'
import DayCard from '@/components/DayCard.vue'
import type { ItineraryDetailResponse, VoteStat } from '@/types/share'
import type { PlanOption } from '@/types/itinerary'

const props = defineProps<{ shareId: string }>()

const router = useRouter()
const detail = ref<ItineraryDetailResponse | null>(null)
const error = ref('')

const planOptions = computed((): PlanOption[] => {
  return detail.value?.plan_results?.plan_options || []
})

const selectedPlan = computed(() => {
  if (!detail.value) return null
  const fi = detail.value.final_plan_index
  if (fi !== null && fi !== undefined && planOptions.value[fi]) {
    return planOptions.value[fi]
  }
  // 默认展示第一个方案或 plan_results 的 items
  if (planOptions.value.length > 0) return planOptions.value[0]
  return detail.value.plan_results || null
})

const handleVoted = (stats: VoteStat[], planIndex: number) => {
  if (detail.value) {
    detail.value.vote_stats = stats
    detail.value.current_user_vote = planIndex
  }
}

const goHome = () => {
  router.push('/')
}

onMounted(async () => {
  try {
    detail.value = await getSharedItinerary(props.shareId)
  } catch (e: any) {
    error.value = e.response?.data?.error || '获取分享行程失败'
  }
})
</script>

<style scoped>
.share-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
}

.plan-detail-card {
  margin-bottom: 20px;
}

.day-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error-wrapper,
.loading-wrapper {
  max-width: 600px;
  margin: 60px auto;
}
</style>
