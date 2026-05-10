import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: '/tasks',
    },
    {
      path: '/tasks',
      name: 'Tasks',
      component: () => import('@/pages/TasksPage.vue'),
    },
    {
      path: '/travel',
      name: 'Travel',
      component: () => import('@/pages/TravelPage.vue'),
    },
    {
      path: '/notes',
      name: 'Notes',
      component: () => import('@/pages/NotesPage.vue'),
    },
  ],
})

export default router
