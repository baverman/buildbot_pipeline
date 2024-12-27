import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.provide('config', { log_limit: 2000 })

app.use(router)

app.mount('#app')
