<template>
  <div class="trip-result" v-if="itinerary">
    <el-card class="overview-card">
      <template #header>
        <h2>✨ 行程概览</h2>
      </template>
      <h3>{{ itinerary.destination }} {{ itinerary.items.length }}天游</h3>
      <p class="overview-text">{{ itinerary.overview }}</p>
    </el-card>

    <div class="day-cards">
      <el-card class="day-card" v-for="item in itinerary.items" :key="item.day">
        <template #header>
          <h3>📅 {{ item.title }}</h3>
        </template>
        <p class="day-summary">{{ item.summary }}</p>
        
        <h4>📍 推荐地点</h4>
        <div class="places-list">
          <div class="place-item-card" v-for="place in item.places" :key="place.name">
            <div class="place-header">
              <span class="place-name">{{ place.name }}</span>
              <el-tag size="small" type="info">{{ place.category }}</el-tag>
            </div>
            <p class="place-reason">{{ place.reason }}</p>
          </div>
        </div>
      </el-card>
    </div>

    <el-button type="primary" @click="handleReset" style="display: block; margin: 30px auto;">
      重新规划
    </el-button>
  </div>
</template>

<script setup lang="ts">
import type { ItineraryResponse } from '@/types/itinerary'

const props = defineProps<{
  itinerary: ItineraryResponse | null
}>()

const emit = defineEmits<{
  reset: []
}>()

const handleReset = () => {
  emit('reset')
}
</script>

<style scoped>
.trip-result {
  max-width: 800px;
  margin: 20px auto;
}

.overview-card {
  margin-bottom: 30px;
}

.overview-text {
  font-size: 16px;
  line-height: 1.6;
  color: #606266;
  margin-top: 10px;
}

.day-cards {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.day-card {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.day-summary {
  font-size: 15px;
  color: #606266;
  margin-bottom: 20px;
}

.place-item {
  width: 100%;
}

.place-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.place-name {
  font-weight: 600;
  font-size: 15px;
}

.place-reason {
  color: #909399;
  font-size: 14px;
  margin: 0;
}

.places-list {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.place-item-card {
  padding: 15px 20px;
  border-bottom: 1px solid #e4e7ed;
}

.place-item-card:last-child {
  border-bottom: none;
}
</style>
