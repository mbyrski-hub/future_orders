<script setup>
import { ref, inject } from 'vue';
import apiClient from '@/api';
import { Icon } from '@iconify/vue';
import { RouterLink } from 'vue-router';

const $swal = inject('$swal');
const email = ref('');
const loading = ref(false);

const handleSubmit = async () => {
  loading.value = true;
  try {
    // Używamy 'apiClient', aby obsłużyć błędy sieciowe
    const response = await apiClient.post('/forgot-password', {
      email: email.value
    });
    
    // Pokaż sukces (używamy tego samego komunikatu, co backend)
    await $swal.fire({
      icon: 'success',
      title: 'Wysłano!',
      text: response.data.msg,
      confirmButtonText: 'Wróć do logowania'
    });
    
  } catch (error) {
    // Błąd krytyczny (np. serwer padł)
    await $swal.fire({
      icon: 'error',
      title: 'Błąd serwera',
      text: 'Nie udało się wysłać prośby. Spróbuj ponownie później.'
    });
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="container vh-100 d-flex justify-content-center align-items-center">
    <div class="card p-4" style="width: 100%; max-width: 450px;">
      <h2 class="text-center mb-3">Zresetuj hasło</h2>
      <p class="text-center text-muted mb-4">
        Podaj swój adres e-mail, a wyślemy Ci link do ustawienia nowego hasła.
      </p>
      
      <form @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label for="email" class="form-label">Adres e-mail</label>
          <input 
            type="email" 
            class="form-control" 
            id="email" 
            v-model="email" 
            required
            placeholder="jan.kowalski@example.com"
          >
        </div>
        
        <button type="submit" class="btn btn-primary w-100" :disabled="loading">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Wysyłanie...' : 'Wyślij link' }}
        </button>
      </form>
      
      <div class="text-center mt-4">
        <RouterLink :to="{ name: 'login' }">
          <Icon icon="mdi:arrow-left" /> Wróć do logowania
        </RouterLink>
      </div>
    </div>
  </div>
</template>

<style scoped>
.iconify { vertical-align: middle; }
</style>