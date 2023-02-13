import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.provide('config',  {'backend': '.', 'log_limit': 2000})
// app.provide('config',  {'backend': 'http://localhost:8010', 'log_limit': 2000})

app.use(router)

app.mount('#app')
