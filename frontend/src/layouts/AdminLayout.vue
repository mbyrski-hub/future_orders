<script setup>
import { RouterView, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth';
import { useThemeStore } from '@/stores/themeStore';
import { Icon } from '@iconify/vue'; 
import { computed } from 'vue';
import NotificationBell from '@/components/NotificationBell.vue'; // Import dzwonka

const authStore = useAuthStore();
const themeStore = useThemeStore();

const isFullAdmin = computed(() => {
  return authStore.user?.role === 'admin';
});

const handleLogout = () => {
  authStore.logout();
};
</script>

<template>
  <div class="d-flex" style="min-height: 100vh;">
    <nav class="d-flex flex-column flex-shrink-0 p-3 text-white bg-dark sidebar-custom">
      
      <a href="/admin/dashboard" class="d-flex align-items-center mb-1 text-white text-decoration-none">
        <Icon icon="mdi:shield-account" class="me-2 fs-4" />
        <span class="fs-4">{{ isFullAdmin ? 'Panel Admina' : 'Panel Raportowy' }}</span>
      </a>
      
      <div class="text-white-50 small mb-2">
        Zalogowany: <strong>{{ authStore.user?.username }}</strong>
      </div>

      <div class="d-flex align-items-center mb-2">
        <NotificationBell class="flex-grow-1" />
        
        <button 
          class="btn btn-outline-secondary me-2" 
          @click.prevent="themeStore.toggleTheme" 
          :title="themeStore.theme === 'light' ? 'Włącz tryb ciemny' : 'Włącz tryb jasny'"
        >
          <Icon :icon="themeStore.theme === 'light' ? 'mdi:weather-night' : 'mdi:white-balance-sunny'" />
        </button>
        <button class="btn btn-outline-light" @click="handleLogout">
          <Icon icon="mdi:logout" />
        </button>
      </div>

      <hr>
      
      <ul class="nav nav-pills flex-column mb-auto">
        <li class="nav-item">
          <RouterLink :to="{ name: 'admin-dashboard' }" class="nav-link text-white" active-class="active">
            <Icon icon="mdi:view-dashboard-outline" class="me-2 fs-5" />
            Kokpit
          </RouterLink>
        </li>
        <li>
          <RouterLink :to="{ name: 'admin-orders' }" class="nav-link text-white" active-class="active">
            <Icon icon="mdi:clipboard-list-outline" class="me-2 fs-5" />
            Zamówienia
          </RouterLink>
        </li>
        
        <template v-if="isFullAdmin">
          <li>
            <RouterLink :to="{ name: 'admin-products' }" class="nav-link text-white" active-class="active">
              <Icon icon="mdi:package-variant-closed" class="me-2 fs-5" />
              Produkty
            </RouterLink>
          </li>
          <li>
            <RouterLink :to="{ name: 'admin-users' }" class="nav-link text-white" active-class="active">
              <Icon icon="mdi:account-group-outline" class="me-2 fs-5" />
              Użytkownicy
            </RouterLink>
          </li>
          <li>
            <RouterLink :to="{ name: 'admin-push' }" class="nav-link text-white" active-class="active">
              <Icon icon="mdi:bell-ring-outline" class="me-2 fs-5" />
              Powiadomienia Push
            </RouterLink>
          </li>
        </template>
      </ul>
    </nav>

    <main class="container p-4" style="flex-grow: 1;">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
/* Poprawia wygląd aktywnego linku w ciemnym menu */
.nav-pills .nav-link.active {
  background-color: #0d6efd;
}
/* Helper do lepszego wyrównania ikonek Iconify z tekstem */
.nav-link .iconify, .dropdown-item .iconify {
  vertical-align: middle;
  margin-bottom: .125em; 
}
.nav-pills .nav-link.py-1 {
  padding-top: 0.25rem !important;
  padding-bottom: 0.25rem !important;
}
.sidebar-custom {
  border-right: 1px solid var(--bs-border-color-translucent);
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}
[data-bs-theme="dark"] .sidebar-custom {
  border-right-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.3);
}
/* Poprawka dla ikon w nowych przyciskach */
.btn .iconify {
  vertical-align: middle;
}
</style>