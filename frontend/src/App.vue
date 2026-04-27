<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import TripForm from './components/TripForm.vue'
import TripResult from './components/TripResult.vue'
import { planItinerary } from './api/itinerary'
import type { ItineraryRequest, ItineraryResponse } from './types/itinerary'

const itinerary = ref<ItineraryResponse | null>(null)
const loading = ref(false)

const handleFormSubmit = async (request: ItineraryRequest) => {
  loading.value = true
  try {
    const result = await planItinerary(request)
    itinerary.value = result
    ElMessage.success('行程生成成功！')
  } catch (err) {
    console.error(err)
    ElMessage.error('行程生成失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  itinerary.value = null
}
</script>

<template>
  <div class="app-container">
    <h1 class="app-title">🌍 TripWeaver 智能行程规划</h1>
    
    <div v-if="!itinerary">
      <TripForm @submit="handleFormSubmit" />
    </div>
    
    <div v-else>
      <TripResult :itinerary="itinerary" @reset="handleReset" />
    </div>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: #f5f7fa;
  padding: 40px 20px;
}

.app-title {
  text-align: center;
  color: #303133;
  margin-bottom: 30px;
  font-size: 32px;
}
</style>

