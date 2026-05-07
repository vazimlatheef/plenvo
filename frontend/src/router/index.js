import { createRouter, createWebHistory } from 'vue-router'

import { loadSessionUser, user } from '@/composables/session'
import { getToken } from '@/services/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import AdminAssignView from '@/views/AdminAssignView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'
import CreateTrainingView from '@/views/CreateTrainingView.vue'
import EditTrainingView from '@/views/EditTrainingView.vue'
import EmployeeAssignmentsView from '@/views/EmployeeAssignmentsView.vue'
import HomeRedirectView from '@/views/HomeRedirectView.vue'
import LoginView from '@/views/LoginView.vue'
import TrainingSummaryView from '@/views/TrainingSummaryView.vue'
import AiTerminalView from '@/views/AiTerminalView.vue'
import LandingView from '@/views/LandingView.vue'
import SignupView from '@/views/SignupView.vue'
import AboutView from '@/views/AboutView.vue'
import SecurityView from '@/views/SecurityView.vue'
import PrivacyView from '@/views/PrivacyView.vue'
import TermsView from '@/views/TermsView.vue'
import AdminProjectsView from '@/views/AdminProjectsView.vue'
import AdminProjectTasksView from '@/views/AdminProjectTasksView.vue'



const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
      meta: { public: true, title: 'Plenvo — AI-powered team management' },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true, title: 'Sign in' },
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView,
      meta: { public: true, title: 'Start free trial' },
    },
    {
      path: '/about',
      name: 'about',
      component: AboutView,
      meta: { public: true, title: 'About' },
    },
    {
      path: '/security',
      name: 'security',
      component: SecurityView,
      meta: { public: true, title: 'Security' },
    },
    { path: '/privacy', name: 'privacy', component: PrivacyView, meta: { public: true, title: 'Privacy Policy' } },
    { path: '/terms', name: 'terms', component: TermsView, meta: { public: true, title: 'Terms of Service' } },
    {
      path: '/app',
      component: AppLayout,
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'home',
          component: HomeRedirectView,
          meta: { title: 'Home' },
        },
        {
          path: 'admin',
          name: 'admin-dashboard',
          component: AdminDashboardView,
          meta: { title: 'Admin dashboard', adminOnly: true },
        },
        {
          path: 'admin/trainings/new',
          name: 'create-training',
          component: CreateTrainingView,
          meta: { title: 'Create training', adminOnly: true },
        },
        {
          path: 'admin/trainings/:trainingId/edit',
          name: 'edit-training',
          component: EditTrainingView,
          meta: { title: 'Edit training', adminOnly: true },
        },
        {
          path: 'admin/trainings/:trainingId/summary',
          name: 'training-summary',
          component: TrainingSummaryView,
          meta: { title: 'Training summary', adminOnly: true },
        },
        {
          path: 'admin/assign',
          name: 'admin-assign',
          component: AdminAssignView,
          meta: { title: 'Assign training', adminOnly: true },
        },
        {
          path: 'admin/ai-terminal',
          name: 'ai-terminal',
          component: AiTerminalView,
          meta: { title: 'AI Terminal', adminOnly: true },
        },
        {
          path: 'assignments',
          name: 'employee-assignments',
          component: EmployeeAssignmentsView,
          meta: { title: 'My assignments' },
        },
        {
          path: 'projects',
          name: 'admin-projects',
          component: AdminProjectsView,
          meta: { title: 'Projects', adminOnly: true },
        },
        {
          path: 'projects/:projectId/tasks',
          name: 'project-tasks',
          component: AdminProjectTasksView,
          meta: { title: 'Project Tasks', adminOnly: true },
        },
      ],
    },
    { path: '/:pathMatch(.*)*', name: 'not-found', redirect: { name: 'landing' } },
  ],
})

router.beforeEach(async (to) => {
  const token = getToken()
  const isPublic = to.meta.public === true
  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)

  if (isPublic && (to.name === 'login' || to.name === 'landing' || to.name === 'signup')) {
    if (token && to.name !== 'landing') {
      await loadSessionUser()
      if (user.value) {
        return {
          name: user.value.role === 'admin' ? 'admin-dashboard' : 'employee-assignments',
        }
      }
    }
    return true
  }

  if (needsAuth && !token) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }

  if (needsAuth && token) {
    await loadSessionUser()
    if (!user.value) {
      return { name: 'login', query: { redirect: to.fullPath } }
    }
    if (to.meta.adminOnly && user.value.role !== 'admin') {
      return { name: 'employee-assignments' }
    }
  }

  return true
})

router.afterEach((to) => {
  document.title = to.meta.title ? `${to.meta.title} · Plenvo` : 'Plenvo'
})

export default router