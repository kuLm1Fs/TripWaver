<template>
  <el-card class="member-list-card">
    <template #header>
      <h3>行程成员 ({{ members.length }}人)</h3>
    </template>
    <div class="members">
      <div v-for="member in members" :key="member.user_id" class="member-item">
        <el-avatar :size="32" :src="member.avatar || undefined">
          {{ member.nickname?.[0] || '?' }}
        </el-avatar>
        <span class="member-name">{{ member.nickname }}</span>
        <span class="member-joined">{{ formatDate(member.joined_at) }} 加入</span>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import type { Member } from '@/types/share'

defineProps<{
  members: Member[]
}>()

const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.member-list-card {
  margin-bottom: 20px;
}

.member-list-card h3 {
  margin: 0;
}

.members {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.member-name {
  font-weight: 500;
  flex: 1;
}

.member-joined {
  color: #c0c4cc;
  font-size: 12px;
}
</style>
