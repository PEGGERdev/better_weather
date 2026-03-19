import { createApp } from 'vue'
import { buildAppContext } from './bootstrap/appBootstrap'
import { registerDashboardWidgets } from './bootstrap/widgetRegistrations'
import { APP_CTX_KEY } from './core/injection'
import './app/theme.css'
import App from './App.vue'

const app = createApp(App)
const appContext = buildAppContext()

registerDashboardWidgets()

app.provide(APP_CTX_KEY, appContext)

app.mount('#app')
