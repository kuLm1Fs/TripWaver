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
      >
        <div class="trip-card-content" @click="goToDetail(trip.id)">
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
        <el-button
          class="delete-btn"
          type="danger"
          :icon="Delete"
          size="small"
          circle
          plain
          @click.stop="openDeleteConfirm(trip)"
        />
      </el-card>
    </div>

    <!-- 删除确认弹窗 -->
    <ConfirmDialog
      v-model="showDeleteDialog"
      title="删除行程"
      :message="deleteTarget ? `确定删除「${deleteTarget.destination}」行程？删除后不可恢复。` : ''"
      confirm-text="删除"
      cancel-text="取消"
      type="danger"
      :loading="deleteLoading"
      @confirm="confirmDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { apiClient, deleteItinerary } from '@/api/itinerary'
import type { ItinerarySummary } from '@/types/itinerary'
import ConfirmDialog from './ConfirmDialog.vue'

const router = useRouter()
const trips = ref<ItinerarySummary[]>([])
const loading = ref(true)
const showDeleteDialog = ref(false)
const deleteTarget = ref<ItinerarySummary | null>(null)
const deleteLoading = ref(false)

const fetchTrips = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/itineraries')
    trips.value = response.data
  } catch {
    trips.value = []
  } finally {
    loading.value = false
  }
}

const goToDetail = (id: number) => {
  router.push(`/trip/${id}`)
}

const openDeleteConfirm = (trip: ItinerarySummary) => {
  deleteTarget.value = trip
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  if (!deleteTarget.value) return
  deleteLoading.value = true
  try {
    await deleteItinerary(deleteTarget.value.id)
    trips.value = trips.value.filter((t) => t.id !== deleteTarget.value!.id)
    ElMessage.success('行程已删除')
    showDeleteDialog.value = false
  } catch {
    ElMessage.error('删除失败')
  } finally {
    deleteLoading.value = false
    deleteTarget.value = null
  }
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
  position: relative;
  cursor: pointer;
  transition: transform 0.2s;
}

.trip-card:hover {
  transform: translateY(-2px);
}

.delete-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.trip-card:hover .delete-btn {
  opacity: 1;
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
