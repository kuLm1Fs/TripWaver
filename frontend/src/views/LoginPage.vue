<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="login-header">
          <h2>TripWeaver</h2>
          <p>智能行程规划</p>
        </div>
      </template>

      <el-form :model="form" @submit.prevent="handleLogin" label-width="80px">
        <el-form-item label="手机号">
          <el-input
            v-model="form.phone"
            placeholder="请输入手机号"
            maxlength="11"
            size="large"
          />
        </el-form-item>

        <el-form-item label="验证码">
          <div class="code-row">
            <el-input
              v-model="form.code"
              placeholder="验证码"
              maxlength="6"
              size="large"
            />
            <el-button
              size="large"
              :disabled="codeSent && countdown > 0"
              @click="handleSendCode"
            >
              {{ codeSent && countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </el-button>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { sendCode } from '@/api/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = ref({ phone: '', code: '' })
const loading = ref(false)
const codeSent = ref(false)
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const handleSendCode = async () => {
  if (!/^1[3-9]\d{9}$/.test(form.value.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  try {
    const res = await sendCode({ phone: form.value.phone })
    codeSent.value = true
    countdown.value = 60
    timer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0 && timer) {
        clearInterval(timer)
        timer = null
      }
    }, 1000)
    ElMessage.success(res.message || '验证码已发送')
  } catch {
    ElMessage.error('发送验证码失败')
  }
}

const handleLogin = async () => {
  if (!/^1[3-9]\d{9}$/.test(form.value.phone)) {
    ElMessage.warning('请输入正确的手机号')
    return
  }
  if (form.value.code.length !== 6) {
    ElMessage.warning('请输入6位验证码')
    return
  }
  loading.value = true
  try {
    await authStore.login(form.value.phone, form.value.code)
    ElMessage.success('登录成功')
    router.push('/')
  } catch {
    ElMessage.error('登录失败，请检查手机号和验证码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 420px;
}

.login-header {
  text-align: center;
}

.login-header h2 {
  margin: 0 0 8px;
  font-size: 28px;
  color: #303133;
}

.login-header p {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.code-row {
  display: flex;
  gap: 10px;
  width: 100%;
}

.code-row .el-input {
  flex: 1;
}
</style>
