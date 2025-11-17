<script setup>
import { onMounted, ref, computed, inject } from 'vue'; // <-- DODAJ 'inject'
import { useAdminPushStore } from '@/stores/adminPushStore';
import { useUserStore } from '@/stores/userStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';

// --- WSTRZYKNIJ $swal ---
const $swal = inject('$swal');

// Inicjalizacja store'ów
const pushStore = useAdminPushStore();
const { subscriptions, loading: pushLoading, error: pushError } = storeToRefs(pushStore);
const userStore = useUserStore();
const { users } = storeToRefs(userStore);

// Logika formularza wysyłania
const pushForm = ref({
  title: '',
  body: '',
  user_id: 'all'
});
const sendLoading = ref(false);
// const sendSuccess = ref(''); // <-- JUŻ NIEPOTRZEBNE
// const sendError = ref(''); // <-- JUŻ NIEPOTRZEBNE

onMounted(() => {
  pushStore.fetchSubscriptions();
  if (users.value.length === 0) {
    userStore.fetchUsers();
  }
});

const clientUsers = computed(() => {
  return users.value.filter(u => u.role === 'user');
});

// Logika usuwania (teraz używa $swal.fire do potwierdzenia)
const handleDelete = async (sub) => {
  const result = await $swal.fire({
    icon: 'warning',
    title: 'Czy na pewno?',
    text: `Chcesz usunąć subskrypcję dla ${sub.username}?`,
    showCancelButton: true,
    confirmButtonText: 'Tak, usuń',
    cancelButtonText: 'Anuluj',
    confirmButtonColor: '#d33',
  });

  if (result.isConfirmed) {
    try {
      await pushStore.deleteSubscription(sub.id);
      $swal.fire({
        icon: 'success',
        title: 'Usunięto!',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 2000
      });
    } catch (err) {
      pushError.value = err.message; 
    }
  }
};

// Logika wysyłania (teraz używa $swal do obsługi odpowiedzi)
const handleSendPush = async () => {
  sendLoading.value = true;
  // sendSuccess.value = ''; // <-- Usunięte
  // sendError.value = ''; // <-- Usunięte

  try {
    const payload = {
      title: pushForm.value.title,
      body: pushForm.value.body
    };
    if (pushForm.value.user_id !== 'all') {
      payload.user_id = pushForm.value.user_id;
    }

    const response = await pushStore.sendCustomPush(payload);
    
    // --- ZMIANA NA $swal ---
    $swal.fire({
      icon: 'success',
      title: 'Wysłano!',
      text: response.msg, // Pokaż komunikat z API
    });
    
    // Wyczyść formularz
    pushForm.value.title = '';
    pushForm.value.body = '';

  } catch (err) {
    // --- ZMIANA NA $swal ---
    $swal.fire({
      icon: 'error',
      title: 'Błąd wysyłki',
      text: err.message,
    });
  } finally {
    sendLoading.value = false;
  }
};

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('pl-PL');
};
</script>

<template>
  <h1 class="mb-4">Zarządzanie Powiadomieniami Push</h1>

  <div class="row g-5">
    <div class="col-lg-5">
      <div class="card shadow-sm">
        <div class="card-body p-4">
          <h4 class="card-title mb-3">Wyślij nowe powiadomienie</h4>
          
          <form @submit.prevent="handleSendPush">
            <div class="mb-3">
              <label for="pushTitle" class="form-label">Tytuł</label>
              <input type="text" class="form-control" id="pushTitle" v-model="pushForm.title" required>
            </div>
            <div class="mb-3">
              <label for="pushBody" class="form-label">Treść (Body)</label>
              <textarea class="form-control" id="pushBody" rows="3" v-model="pushForm.body" required></textarea>
            </div>
            <div class="mb-3">
              <label for="pushUser" class="form-label">Odbiorca</label>
              <select class="form-select" id="pushUser" v-model="pushForm.user_id">
                <option value="all">Wszyscy subskrybenci</option>
                <optgroup label="Konkretni klienci">
                  <option v-for="user in clientUsers" :key="user.id" :value="user.id">
                    {{ user.username }} (ID: {{ user.id }})
                  </option>
                </optgroup>
              </select>
            </div>
            
            <button type="submit" class="btn btn-primary w-100" :disabled="sendLoading">
              <span v-if="sendLoading" class="spinner-border spinner-border-sm me-2"></span>
              {{ sendLoading ? 'Wysyłanie...' : 'Wyślij powiadomienie' }}
            </button>
          </form>
        </div>
      </div>
    </div>

    <div class="col-lg-7">
      <div class="card shadow-sm">
        <div class="card-body">
          <h4 class="card-title mb-3">Aktywne Subskrypcje</h4>
          
          <div v-if="pushLoading" class="text-center">
            <div class="spinner-border" role="status"></div>
          </div>
          <div v-if="pushError" class="alert alert-danger">{{ pushError }}</div>

          <div v-if="!pushLoading && subscriptions.length === 0" class="alert alert-info">
            Brak aktywnych subskrypcji.
          </div>

          <div v-if="subscriptions.length > 0" class="table-responsive">
            <table class="table table-sm table-hover align-middle">
              <thead class="table-light">
                <tr>
                  <th>ID</th>
                  <th>Użytkownik</th>
                  <th>Data subskrypcji</th>
                  <th class="text-end">Akcje</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="sub in subscriptions" :key="sub.id">
                  <td>{{ sub.id }}</td>
                  <td>{{ sub.username }}</td>
                  <td>{{ formatDate(sub.created_at) }}</td>
                  <td class="text-end">
                    <button class="btn btn-sm btn-outline-danger" @click="handleDelete(sub)">
                      <Icon icon="mdi:trash-can-outline" />
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            <small class="text-muted">
              Wyświetlana jest tylko lista urządzeń. Pełne dane subskrypcji (klucze) są bezpiecznie przechowywane na serwerze.
            </small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.iconify {
  vertical-align: middle;
}
</style>