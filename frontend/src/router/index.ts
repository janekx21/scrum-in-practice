import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import FPSView from '../views/FPSView.vue'
import LiveStreamingView from '../views/LiveStreamingView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/fps',
      name: 'fps-view',
      component: FPSView,
    },
    {
      path: '/livestreaming',
      name: 'live-stream',
      component: LiveStreamingView,
    }
  ],
})

export default router
