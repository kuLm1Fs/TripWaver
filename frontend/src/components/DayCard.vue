<template>
  <el-card class="day-card">
    <template #header>
      <h3>{{ item.title }}</h3>
    </template>
    <p class="day-summary">{{ item.summary }}</p>
    <div class="places-list">
      <div v-for="place in item.places" :key="place.name" class="place-item">
        <span class="place-name">{{ place.name }}</span>
        <el-tag size="small" type="info">{{ place.category }}</el-tag>
        <p v-if="place.reason" class="place-reason">{{ place.reason }}</p>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { ItineraryItem } from '@/types/itinerary'

defineProps<{
  item: ItineraryItem
}>()
</script>

<style scoped>
.day-card {
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.08);
}

.day-summary {
  color: #606266;
  font-size: 14px;
  margin: 0 0 12px;
}

.places-list {
  margin-top: 8px;
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
</style>
