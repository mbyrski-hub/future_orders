// /frontend/src/main.js

import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap'
import VueSweetalert2 from 'vue-sweetalert2'; // <-- 1. DODAJ IMPORT
import 'sweetalert2/dist/sweetalert2.min.css'

import { createApp, markRaw } from 'vue' // <-- DODAJ 'markRaw'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { useThemeStore } from './stores/themeStore'

const app = createApp(App)
const pinia = createPinia() // <-- Stwórz instancję Pinia

// --- NOWA LOGIKA ---
// Tworzymy prosty plugin, który dodaje 'router' do każdego store'a.
// 'markRaw' mówi Vue, aby nie próbował robić routera reaktywnym.
pinia.use(({ store }) => {
  store.router = markRaw(router)
})
// --- KONIEC NOWEJ LOGIKI ---

app.use(router) // Router musi być zainstalowany jako pierwszy
app.use(pinia)  // Pinia jako druga
app.use(VueSweetalert2);

useThemeStore() // Inicjalizacja motywu

app.mount('#app')

// --- NOWA LOGIKA: Rejestracja Service Workera ---
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('Service Worker zarejestrowany pomyślnie:', registration);
      })
      .catch(error => {
        console.error('Rejestracja Service Workera nie powiodła się:', error);
      });
  });
}