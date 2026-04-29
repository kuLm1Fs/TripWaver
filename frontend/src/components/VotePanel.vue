<template>
  <el-card class="vote-panel">
    <template #header>
      <div class="panel-header">
        <h3>方案投票</h3>
        <el-tag v-if="isLocked" type="success">投票已结束</el-tag>
        <el-tag v-else type="warning">进行中</el-tag>
      </div>
    </template>

    <div class="plan-options">
      <div
        v-for="(option, index) in planOptions"
        :key="index"
        class="plan-option"
        :class="{
          'is-voted': currentUserVote === index,
          'is-winner': isLocked && winnerIndex === index,
        }"
      >
        <div class="option-header">
          <h4>{{ option.title || `方案${index + 1}` }}</h4>
          <div class="vote-count">
            <span class="count">{{ getCount(index) }}</span>
            <span class="label">票</span>
          </div>
        </div>

        <p class="option-desc">{{ option.description }}</p>

        <!-- 简要行程预览 -->
        <div class="option-preview" v-if="option.items">
          <div v-for="item in option.items.slice(0, 2)" :key="item.day" class="preview-day">
            <strong>Day {{ item.day }}:</strong> {{ item.title }}
          </div>
          <div v-if="option.items.length > 2" class="preview-more">
            共 {{ option.items.length }} 天...
          </div>
        </div>

        <!-- 投票进度条 -->
        <el-progress
          :percentage="getPercent(index)"
          :color="currentUserVote === index ? '#409eff' : '#e4e7ed'"
          :stroke-width="8"
          style="margin: 10px 0"
        />

        <div class="option-actions">
          <el-button
            size="small"
            @click="handleViewPlan(index)"
            :type="viewingPlan === index ? 'success' : 'default'"
          >
            {{ viewingPlan === index ? '查看中' : '查看此方案' }}
          </el-button>
          <el-button
            v-if="!isLocked && currentUserVote === null"
            type="primary"
            size="small"
            @click="handleVote(index)"
            :loading="voting"
          >
            投票
          </el-button>
          <el-tag
            v-if="currentUserVote === index"
            type="primary"
            effect="dark"
          >
            已投票
          </el-tag>
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { votePlan } from '@/api/vote'
import { getVoteCount, getVotePercentage, getWinnerIndex } from '@/utils/vote'
import type { PlanOption } from '@/types/itinerary'
import type { VoteStat } from '@/types/share'

const props = defineProps<{
  itineraryId: number
  planOptions: PlanOption[]
  voteStats: VoteStat[]
  currentUserVote: number | null
  isLocked: boolean
}>()

const emit = defineEmits<{
  voted: [stats: VoteStat[], planIndex: number]
  planChanged: [planIndex: number]
}>()

const voting = ref(false)
const viewingPlan = ref<number | null>(null)

const winnerIndex = computed(() => getWinnerIndex(props.voteStats))

const getCount = (index: number) => getVoteCount(props.voteStats, index)
const getPercent = (index: number) => getVotePercentage(props.voteStats, index)

const handleViewPlan = (planIndex: number) => {
  viewingPlan.value = planIndex
  emit('planChanged', planIndex)
}

const handleVote = async (planIndex: number) => {
  voting.value = true
  try {
    const res = await votePlan({
      itinerary_id: props.itineraryId,
      plan_index: planIndex,
    })
    emit('voted', res.vote_stats, planIndex)
    ElMessage.success('投票成功')
  } catch {
    ElMessage.error('投票失败')
  } finally {
    voting.value = false
  }
}
</script>

<style scoped>
.vote-panel {
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
}

.plan-options {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plan-option {
  border: 2px solid #e4e7ed;
  border-radius: 8px;
  padding: 16px;
  transition: border-color 0.3s;
}

.plan-option.is-voted {
  border-color: #409eff;
  background: #f0f7ff;
}

.plan-option.is-winner {
  border-color: #67c23a;
  background: #f0f9eb;
}

.option-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.option-header h4 {
  margin: 0;
  font-size: 16px;
}

.vote-count {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.vote-count .count {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.vote-count .label {
  font-size: 12px;
  color: #909399;
}

.option-desc {
  color: #606266;
  font-size: 14px;
  margin: 0 0 10px;
}

.option-preview {
  background: #fafafa;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 13px;
  color: #606266;
}

.preview-day {
  margin-bottom: 4px;
}

.preview-more {
  color: #c0c4cc;
  font-size: 12px;
}

.option-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-top: 12px;
}
</style>
