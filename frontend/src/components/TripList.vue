<template>
  <div class="trip-list">
    <div v-if="loading" class="loading-wrapper">
      <el-skeleton :rows="3" animated />
    </div>

    <div v-else-if="trips.length === 0" class="empty-wrapper">
      <el-empty description="还没有行程，快去规划吧" />
    </div>

    <div v-else class="trip-cards">
      <el-card
        v-for="trip in trips"
        :key="trip.id"
        class="trip-card"
        shadow="hover"
        @click="goToDetail(trip.id)"
      >
        <div class="trip-card-content">
          <div class="trip-info">
            <h3>{{ trip.destination }}</h3>
            <p>{{ trip.days }}天行程 · {{ trip.interests?.join('、') || '无偏好' }}</p>
          </div>
          <div class="trip-meta">
            <el-tag v-if="trip.is_locked" type="success" size="small">已锁定</el-tag>
            <el-tag v-else type="info" size="small">进行中</el-tag>
            <span class="trip-date">{{ formatDate(trip.created_at) }}</span>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/itinerary'
import type { ItinerarySummary } from '@/types/itinerary'

const router = useRouter()
const trips = ref<ItinerarySummary[]>([])
const loading = ref(true)

const fetchTrips = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/itineraries')
    trips.value = response.data
  } catch {
    // 接口可能不存在，静默失败
    trips.value = []
  } finally {
    loading.value = false
  }
}

const goToDetail = (id: number) => {
  router.push(`/trip/${id}`)
}

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

onMounted(fetchTrips)
</script>

<style scoped>
.trip-list {
  margin-top: 20px;
}

.trip-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.trip-card {
  cursor: pointer;
  transition: transform 0.2s;
}

.trip-card:hover {
  transform: translateY(-2px);
}

.trip-card-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.trip-info h3 {
  margin: 0 0 4px;
  font-size: 16px;
}

.trip-info p {
  margin: 0;
  color: #909399;
  font-size: 13px;
}

.trip-meta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trip-date {
  color: #c0c4cc;
  font-size: 12px;
}

.loading-wrapper,
.empty-wrapper {
  padding: 40px 0;
}
</style>
