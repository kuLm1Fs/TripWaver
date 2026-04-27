<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
    <header class="app-header" v-if="authStore.isLoggedIn">
      <div class="header-content">
        <h1 class="app-logo" @click="router.push('/')">🌍 TripWeaver</h1>
        <div class="header-right">
          <span class="user-name">{{ authStore.nickname || '用户' }}</span>
          <el-button text @click="handleLogout">退出</el-button>
        </div>
      </div>
    </header>

    <!-- 页面内容 -->
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.app-header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 12px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.app-logo {
  margin: 0;
  font-size: 22px;
  color: #303133;
  cursor: pointer;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-name {
  color: #606266;
  font-size: 14px;
}

.app-main {
  padding: 20px;
}
</style>

