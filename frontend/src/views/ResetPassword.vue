<script setup>
import { ref, inject, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import apiClient from '@/api';
import { Icon } from '@iconify/vue';

const $swal = inject('$swal');
const route = useRoute();
const router = useRouter();

const password = ref('');
const passwordConfirm = ref('');
const token = ref(null);
const loading = ref(false);

// Pobierz token z adresu URL przy ładowaniu strony
onMounted(() => {
  token.value = route.query.token;
  if (!token.value) {
    $swal.fire({
      icon: 'error',
      title: 'Brak tokena',
      text: 'Link do resetowania hasła jest nieprawidłowy lub niekompletny.',
    }).then(() => {
      router.push({ name: 'login' });
    });
  }
});

const handleSubmit = async () => {
  if (password.value !== passwordConfirm.value) {
    $swal.fire({ icon: 'error', title: 'Oops...', text: 'Hasła nie są identyczne!' });
    return;
  }
  
  loading.value = true;
  try {
    const response = await apiClient.post('/reset-password', {
      token: token.value,
      new_password: password.value
    });
    
    // Sukces!
    await $swal.fire({
      icon: 'success',
      title: 'Hasło zmienione!',
      text: response.data.msg,
      confirmButtonText: 'Przejdź do logowania'
    });
    router.push({ name: 'login' });
    
  } catch (error) {
    // Błąd (np. token wygasł)
    await $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: error.response?.data?.msg || 'Wystąpił błąd serwera.'
    });
    router.push({ name: 'login' });
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="container vh-100 d-flex justify-content-center align-items-center">
    <div class="card p-4" style="width: 100%; max-width: 450px;">
      <h2 class="text-center mb-4">Ustaw nowe hasło</h2>
      
      <form @submit.prevent="handleSubmit">
        <div class="mb-3">
          <label for="password" class="form-label">Nowe hasło</label>
          <input 
            type="password" 
            class="form-control" 
            id="password" 
            v-model="password" 
            required
          >
        </div>
        <div class="mb-3">
          <label for="passwordConfirm" class="form-label">Powtórz nowe hasło</label>
          <input 
            type="password" 
            class="form-control" 
            id="passwordConfirm" 
            v-model="passwordConfirm" 
            required
          >
        </div>
        
        <button type="submit" class="btn btn-primary w-100" :disabled="loading || !token">
          <span v-if="loading" class="spinner-border spinner-border-sm me-2"></span>
          {{ loading ? 'Zapisywanie...' : 'Zapisz i zaloguj się' }}
        </button>
      </form>
    </div>
  </div>
</template>