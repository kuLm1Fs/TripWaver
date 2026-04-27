<template>
  <div class="home-page">
    <TripForm @submit="handleFormSubmit" :loading="loading" />

    <el-divider>我的行程</el-divider>

    <TripList />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import TripForm from '@/components/TripForm.vue'
import TripList from '@/components/TripList.vue'
import { planItinerary } from '@/api/itinerary'
import { useTripStore } from '@/stores/trip'
import type { ItineraryRequest } from '@/types/itinerary'

const router = useRouter()
const tripStore = useTripStore()
const loading = ref(false)

const handleFormSubmit = async (request: ItineraryRequest) => {
  loading.value = true
  try {
    const result = await planItinerary(request)
    tripStore.setTrip(result)
    if (result.itinerary_id) {
      router.push(`/trip/${result.itinerary_id}`)
    }
    ElMessage.success('行程生成成功！')
  } catch {
    ElMessage.error('行程生成失败，请稍后重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.home-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}
</style>
