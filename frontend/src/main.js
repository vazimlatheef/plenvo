import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { loadSessionUser } from './composables/session'
import { getToken } from './services/auth'
import './assets/base.css'

if (getToken()) loadSessionUser()

createApp(App).use(router).mount('#app')
