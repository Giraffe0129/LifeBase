import { createRouter, createWebHashHistory } from 'vue-router'

const router = createRouter({
  // Use hash history for Electron compatibility
  history: createWebHashHistory(),
  routes: [
    {
      path: '/',
      redirect: '/tasks',
    },
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/pages/LoginPage.vue'),
    },
    {
      path: '/tasks',
      name: 'Tasks',
      component: () => import('@/pages/TasksPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/travel',
      name: 'Travel',
      component: () => import('@/pages/TravelPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/notes',
      name: 'Notes',
      component: () => import('@/pages/NotesPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/settings',
      name: 'Settings',
      component: () => import('@/pages/SettingsPage.vue'),
      meta: { requiresAuth: true },
    },
    // Electron 便签模式 - 无需认证
    {
      path: '/sticky',
      name: 'Sticky',
      component: () => import('@/pages/StickyPage.vue'),
    },
  ],
})

// 路由守卫
router.beforeEach(async (to, _from, next) => {
  const { useAuthStore } = await import('@/stores/useAuthStore')
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && auth.isLoggedIn) {
    next('/tasks')
  } else {
    next()
  }
})

export default router
