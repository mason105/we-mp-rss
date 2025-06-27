<template>
  <div class="login-container">
    <div class="login-layout">
      <!-- 左侧介绍区域 -->
      <div class="login-left">
        <div class="login-intro">
          <h1 class="intro-title">WeRSS - 微信公众号订阅助手</h1>
          <p class="intro-text">
            一个用于订阅和管理微信公众号内容的工具，提供RSS订阅功能
          </p>
          <div class="login-features">
            <div class="feature-item">
              <icon-check-circle />
              <span>微信公众号内容抓取和解析</span>
            </div>
            <div class="feature-item">
              <icon-check-circle />
              <span>RSS订阅生成</span>
            </div>
            <div class="feature-item">
              <icon-check-circle />
              <span>定时自动更新内容</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧登录区域 -->
      <div class="login-right">
        <a-card class="login-card" :bordered="false">
          <a-form :model="form" @submit="handleSubmit">
            <a-form-item field="username" label="用户名">
              <a-input v-model="form.username" placeholder="请输入用户名">
                <template #prefix><icon-user /></template>
              </a-input>
            </a-form-item>
            
            <a-form-item field="password" label="密码">
              <a-input-password v-model="form.password" placeholder="请输入密码">
                <template #prefix><icon-lock /></template>
              </a-input-password>
            </a-form-item>
            
            <a-form-item>
              <a-button type="primary" html-type="submit" :loading="loading" long>
                登录
              </a-button>
            </a-form-item>
          </a-form>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { login } from '@/api/auth'

const appTitle = computed(() => import.meta.env.VITE_APP_LOGIN_TITLE || '登录')

const router = useRouter()
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleSubmit = async () => {
  loading.value = true
  try {
    // 使用URLSearchParams格式发送请求
    const formData = new URLSearchParams()
    formData.append('username', form.value.username)
    formData.append('password', form.value.password)
    
    const res = await login({
      username: form.value.username,
      password: form.value.password
    })
    
          if (res.access_token) {
            // 存储token和过期时间
            localStorage.setItem('token', res.access_token)
            localStorage.setItem('token_expire', 
              Date.now() + (res.expires_in * 1000))
        
            console.log('Token stored:', localStorage.getItem('token')) // 调试日志
        
            // 处理重定向
            const redirect = router.currentRoute.value.query.redirect
            await router.push(redirect ? redirect.toString() : '/')
            Message.success('登录成功')
    } else {
      throw new Error('无效的响应格式')
    }
  } catch (error) {
    console.error('登录错误:', error)
    const errorMsg = error.response?.data?.detail || 
                    error.response?.data?.message || 
                    error.message || 
                    '登录失败，请检查用户名和密码'
    // Message.error(errorMsg)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  padding: 0;
  margin: 0;
}

.login-layout {
  display: flex;
  height: 100%;
  transition: all 0.3s ease;
}

.login-container {
  background: linear-gradient(90deg, #3b82f6 0%, #f0f4f8 100%);
}

.login-left {
  flex: 0 0 55%;
  padding: 80px;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: transparent;
}

.login-right {
  flex: 0 0 45%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(5px);
  border: none;
  box-shadow: none;
}

.login-form {
  border: none;
  background: transparent;
  padding: 40px;
  border-radius: 12px;
}

.login-intro {
  max-width: 600px;
  margin-bottom: 60px;
}

.intro-title {
  font-size: 2.5rem;
  margin-bottom: 24px;
  font-weight: 600;
}

.intro-text {
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 32px;
  opacity: 0.9;
}

.login-features {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1rem;
}

.login-ad {
  margin-top: auto;
}

.login-ad img {
  width: 100%;
  max-width: 600px;
  border-radius: 8px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  border: none;
}

:deep(.arco-form-item-label) {
  color: #333 !important;
}

:deep(.arco-input-wrapper) {
  height: 48px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #1a202c;
  transition: all 0.2s ease;
}

:deep(.arco-input-wrapper:hover) {
  border-color: #cbd5e0;
  background: #fff;
}

:deep(.arco-input-wrapper:focus-within) {
  border-color: #4299e1;
  box-shadow: 0 0 0 2px rgba(66, 153, 225, 0.2);
  background: #fff;
}

:deep(.arco-input::placeholder) {
  color: #a0aec0;
}

.login-title {
  text-align: center;
  margin-bottom: 32px;
}

.login-title h2 {
  color: #1a202c;
  font-weight: 600;
  font-size: 28px;
  letter-spacing: -0.5px;
  margin-bottom: 8px;
}

.login-title p {
  color: #4a5568;
  font-size: 15px;
  line-height: 1.5;
}

:deep(.arco-form-item-label) {
  color: #2d3748 !important;
  font-weight: 500;
  font-size: 15px;
  margin-bottom: 6px;
  display: block;
}

:deep(.arco-input-wrapper) {
  border-radius: 8px;
  transition: all 0.2s ease;
}

:deep(.arco-input-wrapper:hover) {
  border-color: #4299e1;
}

:deep(.arco-btn-primary) {
  height: 48px;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-weight: 500;
  font-size: 15px;
  background: #4299e1;
  border-color: #4299e1;
  color: white;
}

:deep(.arco-btn-primary:hover) {
  background: #3182ce;
  border-color: #3182ce;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
}

:deep(.arco-btn-primary:active) {
  transform: translateY(0);
  box-shadow: none;
}

:deep(.arco-form-item-error .arco-input-wrapper) {
  border-color: #e53e3e;
  background-color: #fff5f5;
}

:deep(.arco-form-message) {
  color: #e53e3e;
  font-size: 13px;
  margin-top: 6px;
  display: flex;
  align-items: center;
}

:deep(.arco-form-message)::before {
  content: "!";
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  margin-right: 6px;
  background: #e53e3e;
  color: white;
  border-radius: 50%;
  font-size: 12px;
  font-weight: bold;
}

.login-footer {
  margin-top: 24px;
  text-align: center;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.login-footer a {
  color: #4299e1;
  text-decoration: none;
  transition: all 0.2s ease;
  font-size: 0.875rem;
  font-weight: 500;
  margin: 0 8px;
}

.login-footer a:hover {
  color: #3182ce;
  text-decoration: underline;
}

.login-footer .divider {
  color: #cbd5e0;
  user-select: none;
}

@media (max-width: 992px) {
  .login-layout {
    flex-direction: column;
  }
  
  .login-left,
  .login-right {
    flex: 1;
    padding: 40px;
  }
  
  .login-ad {
  }
}
</style>