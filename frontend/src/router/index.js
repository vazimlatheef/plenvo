import { createRouter, createWebHistory } from 'vue-router'

import { appHomeRoute, loadSessionUser, user } from '@/composables/session'
import { getToken } from '@/services/auth'
import AppLayout from '@/layouts/AppLayout.vue'
import AdminAssignView from '@/views/AdminAssignView.vue'
import AdminDashboardView from '@/views/AdminDashboardView.vue'
import CreateTrainingView from '@/views/CreateTrainingView.vue'
import EditTrainingView from '@/views/EditTrainingView.vue'
import EmployeeAssignmentsView from '@/views/EmployeeAssignmentsView.vue'
import HomeRedirectView from '@/views/HomeRedirectView.vue'
import LoginView from '@/views/LoginView.vue'
import ForgotPasswordView from '@/views/ForgotPasswordView.vue'
import ResetPasswordView from '@/views/ResetPasswordView.vue'
import TrainingSummaryView from '@/views/TrainingSummaryView.vue'
import AiTerminalView from '@/views/AiTerminalView.vue'
import LandingView from '@/views/LandingView.vue'
import SignupView from '@/views/SignupView.vue'
import VerifyEmail from '@/views/VerifyEmail.vue'
import AboutView from '@/views/AboutView.vue'
import SecurityView from '@/views/SecurityView.vue'
import SupportView from '@/views/SupportView.vue'
import PrivacyView from '@/views/PrivacyView.vue'
import TermsView from '@/views/TermsView.vue'
import AdminProjectsView from '@/views/AdminProjectsView.vue'
import AdminProjectTasksView from '@/views/AdminProjectTasksView.vue'
import AdminTeamView from '@/views/AdminTeamView.vue'
import AdminTrainingsView from '@/views/AdminTrainingsView.vue'
import CalendarView from '@/views/CalendarView.vue'
import MyTasks from '@/views/MyTasks.vue'
import ProfileView from '@/views/ProfileView.vue'
import AccountView from '@/views/AccountView.vue'
import TrainingView from '@/views/TrainingView.vue'




const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  scrollBehavior(to, _from, savedPosition) {
    if (savedPosition) return savedPosition
    if (to.hash) return { el: to.hash, behavior: 'smooth', top: 80 }
    return { top: 0 }
  },
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
      meta: { public: true, title: 'Plenvo — Notes become assigned work' },
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true, title: 'Sign in' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPasswordView,
      meta: { public: true, title: 'Forgot password' },
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPasswordView,
      meta: { public: true, title: 'Reset password' },
    },
    {
      path: '/signup',
      name: 'signup',
      component: SignupView,
      meta: { public: true, title: 'Start for free' },
    },
    {
      path: '/verify-email',
      name: 'verify-email',
      component: VerifyEmail,
      meta: { public: true, title: 'Verify email' },
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
    {
      path: '/support',
      name: 'support',
      component: SupportView,
      meta: { public: true, title: 'Support' },
    },
    { path: '/privacy', name: 'privacy', component: PrivacyView, meta: { public: true, title: 'Privacy Policy' } },
    { path: '/terms', name: 'terms', component: TermsView, meta: { public: true, title: 'Terms of Service' } },
    {
      path: '/training/:token',
      name: 'training-magic-link',
      component: TrainingView,
      meta: { public: true, title: 'Your training' },
    },
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
          path: 'admin/trainings',
          name: 'trainings-list',
          component: AdminTrainingsView,
          meta: { title: 'Training', adminOnly: true },
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
          meta: { title: 'Plenvo AI', adminOnly: true },
        },
        {
          path: 'assignments',
          name: 'employee-assignments',
          component: EmployeeAssignmentsView,
          meta: { title: 'My assignments' },
        },
        {
          path: 'tasks',
          name: 'my-tasks',
          component: MyTasks,
          meta: { title: 'My tasks' },
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
        {
          path: 'team',
          name: 'admin-team',
          component: AdminTeamView,
          meta: { title: 'Team', adminOnly: true },
        },
        {
          path: 'calendar',
          name: 'calendar',
          component: CalendarView,
          meta: { title: 'Calendar', adminOnly: true },
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
          meta: { title: 'Profile' },
        },
        {
          path: 'account',
          name: 'account',
          component: AccountView,
          meta: { title: 'Account & Subscription' },
        },
      ],
    },    { path: '/:pathMatch(.*)*', name: 'not-found', redirect: { name: 'landing' } },
  ],
})

router.beforeEach(async (to) => {
  const token = getToken()
  const isPublic = to.meta.public === true
  const needsAuth = to.matched.some((r) => r.meta.requiresAuth)

  if (isPublic && to.name === 'landing' && token) {
    await loadSessionUser()
    return true
  }

  if (isPublic && (to.name === 'login' || to.name === 'signup' || to.name === 'training-magic-link')) {
    if (token) {
      await loadSessionUser()
      if (user.value) {
        return appHomeRoute(user.value)
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
  const raw = to.meta.title
  if (!raw) {
    document.title = 'Plenvo — Notes become assigned work'
    return
  }
  document.title = String(raw).startsWith('Plenvo') ? raw : `${raw} · Plenvo`
})

export default router