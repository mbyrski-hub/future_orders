<script setup>
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/themeStore';
import { Icon } from '@iconify/vue'; 
import NotificationBell from '@/components/NotificationBell.vue'; // Import dzwonka

const authStore = useAuthStore();
const themeStore = useThemeStore();
const handleLogout = () => { authStore.logout(); };
</script>

<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
      <div class="container-fluid">
        <RouterLink :to="{ name: 'shipping-dashboard' }" class="navbar-brand">
          <Icon icon="mdi:truck-fast-outline" class="me-2 fs-4" />
          Panel Spedycji
        </RouterLink>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#shippingNavbar">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="shippingNavbar">
          <ul class="navbar-nav me-auto mb-2 mb-lg-0">
            <li class="nav-item">
              <RouterLink :to="{ name: 'shipping-dashboard' }" class="nav-link" active-class="active">
                Lista Zamówień
              </RouterLink>
            </li>
          </ul>
          
          <span class="navbar-text me-3 d-none d-lg-inline">
            Zalogowany jako: <strong>{{ authStore.user?.username }}</strong>
          </span>
          
          <NotificationBell /> <button 
            class="btn btn-outline-secondary me-2" 
            @click.prevent="themeStore.toggleTheme" 
            :title="themeStore.theme === 'light' ? 'Włącz tryb ciemny' : 'Włącz tryb jasny'"
          >
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
  </div>
</template>

<style scoped>
.navbar-nav .nav-link.active {
  font-weight: bold;
}
.btn .iconify, .navbar-brand .iconify {
  vertical-align: middle;
  margin-bottom: .1em; 
}
</style>