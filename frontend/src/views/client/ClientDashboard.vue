<script setup>
import { ref, computed, watch, onMounted } from 'vue'; // <-- DODANO onMounted
import { useAuthStore } from '@/stores/auth';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';

const authStore = useAuthStore();
const { user } = storeToRefs(authStore); 

// --- NOWA LOGIKA POBIERANIA ---
// Kiedy ten komponent się ładuje, każemy mu pobrać
// pełne dane profilowe (imię, nazwisko, itp.)
onMounted(() => {
  // Sprawdzamy, czy mamy pełne dane (czy jest imię). 
  // Jeśli nie, pobieramy.
  if (!user.value?.first_name) {
    authStore.fetchUserProfile();
  }
});
// --- KONIEC NOWEJ LOGIKI ---

// --- Formularz Danych Profilowych ---
const profileData = ref({ email: '', first_name: '', last_name: '' });
const profileSuccess = ref('');
const profileError = ref('');
const profileLoading = ref(false);

// 'watch' jest nadal potrzebny, aby wypełnić formularz, gdy dane dotrą
watch(user, (newUser) => {
  if (newUser) {
    profileData.value.email = newUser.email || '';
    profileData.value.first_name = newUser.first_name || '';
    profileData.value.last_name = newUser.last_name || '';
  }
}, { immediate: true });

// Powitanie
const welcomeMessage = computed(() => {
  // To jest logika, o którą prosiłeś:
  // Jeśli mamy imię, pokaż "Witaj, [imię]!"
  // Jeśli nie (bo jeszcze się ładuje), pokaż "Witaj w panelu klienta"
  if (user.value?.first_name) { 
    return `Witaj, ${user.value.first_name}!`;
  }
  return 'Witaj w panelu klienta'; // Domyślny tekst, jeśli dane się jeszcze ładują
});

const handleProfileUpdate = async () => {
  profileLoading.value = true;
  profileSuccess.value = '';
  profileError.value = '';
  try {
    await authStore.updateProfile(profileData.value);
    profileSuccess.value = "Twoje dane zostały pomyślnie zaktualizowane.";
  } catch (err) {
    profileError.value = err.message;
  } finally {
    profileLoading.value = false;
  }
};

// --- Formularz Hasła ---
const passwordData = ref({ current_password: '', new_password: '' });
const passwordSuccess = ref('');
const passwordError = ref('');
const passwordLoading = ref(false);

const handlePasswordUpdate = async () => {
  passwordLoading.value = true;
  passwordSuccess.value = '';
  passwordError.value = '';
  try {
    const response = await authStore.updatePassword(passwordData.value);
    passwordSuccess.value = response.msg;
    passwordData.value = { current_password: '', new_password: '' };
  } catch (err) {
    passwordError.value = err.message;
  } finally {
    passwordLoading.value = false;
  }
};
</script>

<template>
  <h1 class="mb-4">{{ welcomeMessage }}</h1>
  <p class="lead mb-4">
    Tutaj możesz zarządzać informacjami o swoim koncie oraz zmienić hasło.
  </p>

  <div class="row g-5">
    <div class="col-lg-6">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="card-title mb-3">
            <Icon icon="mdi:account-edit-outline" class="me-2" />
            Twój Profil
          </h4>
          
          <form @submit.prevent="handleProfileUpdate">
            <div v-if="profileSuccess" class="alert alert-success">
              {{ profileSuccess }}
            </div>
            <div v-if="profileError" class="alert alert-danger">
              {{ profileError }}
            </div>

            <div class="mb-3">
              <label class="form-label">Nazwa użytkownika (login)</label>
              <input type="text" :value="user?.username" class="form-control" disabled readonly>
              <div class="form-text">Nazwy użytkownika nie można zmienić.</div>
            </div>
            
            <div class="mb-3">
              <label for="email" class="form-label">Adres e-mail</label>
              <input type="email" class="form-control" id="email" v-model="profileData.email" required>
            </div>
            
            <div class="row">
              <div class="col-md-6 mb-3">
                <label for="first_name" class="form-label">Imię</label>
                <input type="text" class="form-control" id="first_name" v-model="profileData.first_name" placeholder="np. Jan">
              </div>
              <div class="col-md-6 mb-3">
                <label for="last_name" class="form-label">Nazwisko</label>
                <input type="text" class="form-control" id="last_name" v-model="profileData.last_name" placeholder="np. Kowalski">
              </div>
            </div>
            
            <button type="submit" class="btn btn-primary" :disabled="profileLoading">
              <span v-if="profileLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ profileLoading ? 'Zapisywanie...' : 'Zapisz zmiany profilu' }}
            </button>
          </form>
        </div>
      </div>
    </div>
    
    <div class="col-lg-6">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="card-title mb-3">
            <Icon icon="mdi:lock-reset" class="me-2" />
            Zmień hasło
          </h4>
          
          <form @submit.prevent="handlePasswordUpdate">
            <div v-if="passwordSuccess" class="alert alert-success">
              {{ passwordSuccess }}
            </div>
            <div v-if="passwordError" class="alert alert-danger">
              {{ passwordError }}
            </div>

            <div class="mb-3">
              <label for="current_password" class="form-label">Obecne hasło</label>
              <input type="password" class="form-control" id="current_password" v-model="passwordData.current_password" required>
            </div>
            
            <div class="mb-3">
              <label for="new_password" class="form-label">Nowe hasło</label>
              <input type="password" class="form-control" id="new_password" v-model="passwordData.new_password" required>
            </div>
            
            <button type="submit" class="btn btn-warning" :disabled="passwordLoading">
              <span v-if="passwordLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
              {{ passwordLoading ? 'Zmienianie...' : 'Zmień hasło' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.iconify {
  vertical-align: middle;
  margin-bottom: .1em;
}
</style>