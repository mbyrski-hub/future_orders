<script setup>
import { ref, inject, computed } from 'vue';
import { useAuthStore } from '@/stores/auth';
import { RouterLink } from 'vue-router';
import { Icon } from '@iconify/vue';
import { useThemeStore } from '@/stores/themeStore';
import InstallPwaModal from '@/components/InstallPwaModal.vue'; // Importujemy komponent modala

const authStore = useAuthStore();
const $swal = inject('$swal');
const themeStore = useThemeStore();

// --- Logotypy ---
// Główne logo (nad "Logowanie")
const logoSrc = computed(() => {
  if (themeStore.theme === 'dark') {
    return '/logo_b.png'; // Zakładam, że plik jest w /public/logo_b.png
  }
  return '/logo_cz.png'; // Zakładam, że plik jest w /public/logo_cz.png
});

// Logo "h" (w sekcji kontaktu)
const hLogoSrc = computed(() => {
  if (themeStore.theme === 'dark') {
    return '/h_b.png'; // Zakładam, że plik jest w /public/h_b.png
  }
  return '/h_cz.png'; // Zakładam, że plik jest w /public/h_cz.png
});

// --- Logika Logowania ---
const username = ref('');
const password = ref('');

const handleSubmit = async () => {
  try {
    // Logika logowania (wraz z obsługą błędów przez $swal)
    // znajduje się teraz w całości w authStore
    await authStore.login(username.value, password.value);
  } catch (error) {
    // Ten 'catch' złapie tylko ewentualne błędy krytyczne
    // samej aplikacji, a nie błędy API (bo te łapie store).
    $swal.fire({
      icon: 'error',
      title: 'Błąd Aplikacji',
      text: error.message
    });
  }
};

// --- Logika Modala Instrukcji ---
const installModal = ref(null); // Ref do *komponentu* modala

const openInstallModal = () => {
  if (installModal.value) {
    installModal.value.open(); // Wywołujemy metodę 'open' z komponentu
  }
};
</script>

<template>
  <div class="container vh-100 d-flex justify-content-center align-items-center">
    <div class="card p-4 shadow-sm" style="width: 100%; max-width: 400px;">
      
      <div class="text-center mb-4">
        <img 
          :src="logoSrc" 
          alt="Logo Firmy" 
          class="img-fluid" 
          style="max-height: 70px;"
        >
      </div>

      <h2 class="text-center mb-4">Logowanie</h2>
      
      <form @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label for="username" class="form-label">Nazwa użytkownika</label>
          <input 
            type="text" 
            class="form-control" 
            id="username" 
            v-model="username" 
            required
          >
        </div>
        <div class="mb-3">
          <label for="password" class="form-label">Hasło</label>
          <input 
            type="password" 
            class="form-control" 
            id="password" 
            v-model="password" 
            required
          >
        </div>
        <button type="submit" class="btn btn-primary w-100">
          Zaloguj się
        </button>
        
        <div class="d-flex justify-content-between align-items-center mt-3">
          <RouterLink :to="{ name: 'forgot-password' }">
            Nie pamiętam hasła
          </RouterLink>
          
          <button 
            type="button" 
            class="btn btn-link btn-sm p-0" 
            @click="openInstallModal"
          >
            <Icon icon="mdi:cellphone-arrow-down" class="me-1" />
            Jak zainstalować aplikację na telefon?
          </button>
        </div>
      </form>
      
      <hr>
      
      <div class="text-center text-muted small">
        
        <div class="mb-3">
          <img 
            :src="hLogoSrc" 
            alt="Logo H" 
            class="img-fluid" 
            style="max-height: 40px;"
          >
        </div>

        <h6 class="text-uppercase small fw-bold mb-3">Kontakt techniczny</h6>
        <p class="mb-1">
          <strong>Maksym Seliuhin</strong>
        </p>
        <p class="mb-1">
          <Icon icon="mdi:phone-outline" /> tel.: 690 118 377
        </p>
        <p class="mb-0">
          <Icon icon="mdi:email-outline" /> email: m.seliuhin@hoxa.pl
        </p>
      </div>

    </div>
  </div>

  <InstallPwaModal ref="installModal" />
</template>

<style scoped>
.iconify {
  vertical-align: middle;
  margin-bottom: 2px;
}
/* Dodajemy płynne przejście dla obu obrazków */
img {
  transition: all 0.3s ease;
}
</style>