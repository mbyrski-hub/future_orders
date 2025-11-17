<script setup>
// Cała sekcja <script setup> jest poprawna i pozostaje BEZ ZMIAN
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth';
import { useClientStore } from '@/stores/clientStore';
import { storeToRefs } from 'pinia';
import { useThemeStore } from '@/stores/themeStore';
import { Icon } from '@iconify/vue';
import { onMounted, ref } from 'vue'; 
import { usePwaStore } from '@/stores/pwaStore';
import InstallPwaModal from '@/components/InstallPwaModal.vue';
import NotificationBell from '@/components/NotificationBell.vue';

const authStore = useAuthStore();
const clientStore = useClientStore();
const { cartItemCount } = storeToRefs(clientStore);
const themeStore = useThemeStore();
const pwaStore = usePwaStore();
const { installPromptEvent } = storeToRefs(pwaStore);

const isPwaMode = ref(false);
const showInstallPrompt = ref(false);
const showNotifyPrompt = ref(false);
const installModal = ref(null); 

onMounted(() => {
  if (window.matchMedia('(display-mode: standalone)').matches) {
    isPwaMode.value = true;
  }
  const hasSeenPwaInfo = localStorage.getItem('hasSeenPwaInstallPrompt');
  if (!isPwaMode.value && !hasSeenPwaInfo) {
    setTimeout(() => { 
      if (installModal.value) {
        installModal.value.open();
        localStorage.setItem('hasSeenPwaInstallPrompt', 'true');
      }
    }, 2000);
  }
  setTimeout(() => {
    if (installPromptEvent.value && !isPwaMode.value) {
      showInstallPrompt.value = true;
    }
    if (Notification.permission === 'default') {
      showNotifyPrompt.value = true;
    }
  }, 3000); 
});

const handleInstallClick = () => {
  pwaStore.promptToInstall();
  showInstallPrompt.value = false;
};
const handleNotifyClick = () => {
  pwaStore.subscribeToNotifications();
  showNotifyPrompt.value = false;
};
const handleLogout = () => {
  authStore.logout();
};
const openInstallInstructions = () => {
  if (installModal.value) {
    installModal.value.open();
  }
};
</script>

<template>
  <div :class="{ 'pwa-view': isPwaMode }">

    <nav v-if="!isPwaMode" class="navbar navbar-expand-lg navbar-dark bg-dark sticky-top">
      <div class="container-fluid">
        <RouterLink :to="{ name: 'client-dashboard' }" class="navbar-brand">
          <Icon icon="mdi:account-circle-outline" class="me-2 fs-5" />
          Panel Klienta
        </RouterLink>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#userNavbar">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="userNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            
            <li class="nav-item">
              <RouterLink 
                :to="{ name: 'client-products-grid' }" 
                class="nav-link" 
                active-class="active"
              >
                <Icon icon="mdi:plus-box-outline" class="me-1" />
                Złóż Zamówienie
              </RouterLink>
            </li>
            
            <li class="nav-item">
              <RouterLink :to="{ name: 'client-orders' }" class="nav-link" active-class="active">
                <Icon icon="mdi:clipboard-list-outline" class="me-1" />
                Moje Zamówienia
              </RouterLink>
            </li>
            <li class="nav-item">
              <a href="#" class="nav-link" @click.prevent="openInstallInstructions">
                <Icon icon="mdi:cellphone-arrow-down" class="me-1" />
                Instalacja Aplikacji
              </a>
            </li>
          </ul>

          <span class="navbar-text me-3 d-none d-lg-inline">
            Zalogowany jako: <strong>{{ authStore.user?.username }}</strong>
          </span>
          
          <NotificationBell /> <RouterLink :to="{ name: 'client-cart' }" class="btn btn-outline-info me-2">
            <Icon icon="mdi:cart-outline" class="me-1 fs-5" />
            Koszyk
            <span class="badge bg-danger ms-1">{{ cartItemCount }}</span>
          </RouterLink>
          
          <button class="btn btn-outline-secondary me-2" @click.prevent="themeStore.toggleTheme" :title="themeStore.theme === 'light' ? 'Włącz tryb ciemny' : 'Włącz tryb jasny'">
            <Icon :icon="themeStore.theme === 'light' ? 'mdi:weather-night' : 'mdi:white-balance-sunny'" class="fs-5" />
          </button>
          
          <button class="btn btn-outline-light" @click="handleLogout">
            <Icon icon="mdi:logout" class="me-2 fs-5" />
            <span class="d-lg-none">Wyloguj się</span>
          </button>
          </div>
      </div>
    </nav>

    <main class="container p-4">
      <RouterView />
    </main>

    <nav v-if="isPwaMode" class="bottom-nav shadow-lg">
      <RouterLink :to="{ name: 'client-dashboard' }" class="bottom-nav-item" active-class="active">
        <Icon icon="mdi:home-outline" class="fs-3" />
        <span>Profil</span>
      </RouterLink>
      
      <RouterLink :to="{ name: 'client-products-grid' }" class="bottom-nav-item" active-class="active">
        <Icon icon="mdi:plus-box-outline" class="fs-3" />
        <span>Zamów</span>
      </RouterLink>
      
      <RouterLink :to="{ name: 'client-cart' }" class="bottom-nav-item" active-class="active">
        <Icon icon="mdi:cart-outline" class="fs-3" />
        <span>Koszyk</span>
        <span v-if="cartItemCount > 0" class="badge bg-danger pwa-badge">{{ cartItemCount }}</span>
      </RouterLink>
      <RouterLink :to="{ name: 'client-orders' }" class="bottom-nav-item" active-class="active">
        <Icon icon="mdi:clipboard-list-outline" class="fs-3" />
        <span>Zamówienia</span>
      </RouterLink>
    </nav>

    <div class="toast-container position-fixed bottom-0 end-0 p-3" style="z-index: 1100">
      <div class="toast" :class="{ 'show': showInstallPrompt }" role="alert">
        <div class="toast-header">
          <Icon icon="mdi:cellphone-arrow-down" class="me-2 fs-5 text-primary" />
          <strong class="me-auto">Zainstaluj Aplikację</strong>
          <button type="button" class="btn-close" @click="showInstallPrompt = false"></button>
        </div>
        <div class="toast-body">
          <p>Chcesz dodać aplikację do ekranu głównego?</p>
          <button class="btn btn-primary btn-sm" @click="handleInstallClick">
            Tak, zainstaluj
          </button>
        </div>
      </div>
      <div class="toast mt-3" :class="{ 'show': showNotifyPrompt }" role="alert">
        <div class="toast-header">
          <Icon icon="mdi:bell-ring-outline" class="me-2 fs-5 text-danger" />
          <strong class="me-auto">Powiadomienia</strong>
          <button type="button" class="btn-close" @click="showNotifyPrompt = false"></button>
        </div>
        <div class="toast-body">
          <p>Włącz powiadomienia o statusie zamówień.</p>
          <button class="btn btn-success btn-sm" @click="handleNotifyClick">
            Tak, włącz
          </button>
        </div>
      </div>
    </div>

    <InstallPwaModal ref="installModal" />

  </div>
</template>

<style scoped>
/* Lepsze wyrównanie ikonek Iconify (wersja web) */
.navbar .btn .iconify, .navbar-brand .iconify, .nav-link .iconify {
  vertical-align: middle;
  margin-bottom: .1em; 
}
/* Style dla layoutu PWA (bez zmian) */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 65px;
  background-color: var(--bs-body-bg);
  border-top: 1px solid var(--bs-border-color-translucent);
  display: flex;
  justify-content: space-around;
  align-items: center;
  z-index: 1000;
}
.bottom-nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-decoration: none;
  color: var(--bs-text-muted);
  font-size: 0.75rem;
  position: relative;
}
.bottom-nav-item.active {
  color: var(--bs-primary);
}
.pwa-badge {
  position: absolute;
  top: -5px;
  right: -10px;
  font-size: 0.6rem;
  padding: 3px 5px;
  border-radius: 50%;
}
.pwa-view {
  padding-bottom: 70px;
}
</style>