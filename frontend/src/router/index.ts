import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomePage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/trip/:id',
      name: 'trip-detail',
      component: () => import('@/views/TripDetailPage.vue'),
      meta: { requiresAuth: true },
      props: true,
    },
    {
      path: '/share/:shareId',
      name: 'share',
      component: () => import('@/views/SharePage.vue'),
      meta: { requiresAuth: true },
      props: true,
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.name === 'login' && authStore.isLoggedIn) {
    return { name: 'home' }
  }
})

export default router
