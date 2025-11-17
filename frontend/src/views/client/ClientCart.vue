<script setup>
import { ref, inject } from 'vue'; // <-- DODANO 'inject'
import { useClientStore } from '@/stores/clientStore';
import { storeToRefs } from 'pinia';
import { useRouter } from 'vue-router';
import { Icon } from '@iconify/vue';

// Wstrzykujemy SweetAlert
const $swal = inject('$swal'); 

const clientStore = useClientStore();
const { cart, cartItemCount } = storeToRefs(clientStore);

const loading = ref(false);
const error = ref(null);
const router = useRouter();
const orderNotes = ref('');

// --- ZMIANA: Używamy $swal.fire do potwierdzenia ---
const handleRemove = async (variant_id) => {
  const result = await $swal.fire({
    icon: 'warning',
    title: 'Czy na pewno?',
    text: "Produkt zostanie usunięty z koszyka.",
    showCancelButton: true,
    confirmButtonText: 'Tak, usuń',
    cancelButtonText: 'Anuluj',
    confirmButtonColor: '#d33',
    cancelButtonColor: '#3085d6',
  });

  if (result.isConfirmed) {
    clientStore.removeFromCart(variant_id);
    // Małe powiadomienie o sukcesie
    $swal.fire({
      icon: 'success',
      title: 'Usunięto',
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 1500
    });
  }
};
    
// --- ZMIANA: Używamy $swal.fire do obsługi zamówienia ---
const handlePlaceOrder = async () => {
  loading.value = true;
  error.value = null;
  try {
    // Odbieramy odpowiedź (dzięki zmianie w store)
    const response = await clientStore.createOrder(orderNotes.value); 
    
    let title = 'Zamówienie złożone!';
    let text = 'Potwierdzenie zostało wysłane na Twój e-mail.';
    let icon = 'success';

    // Sprawdzamy, czy backend zgłosił problem z e-mailem
    if (response && response.email_warning) {
      title = 'Zamówienie przyjęte!';
      text = `Twoje zamówienie zostało pomyślnie zapisane, ale nie udało się wysłać e-maila z potwierdzeniem. (Błąd: ${response.email_warning})`;
      icon = 'warning'; // Zmieniamy ikonę na ostrzeżenie
    }

    // Pokaż modal sukcesu/ostrzeżenia i poczekaj na kliknięcie "OK"
    await $swal.fire({
      icon: icon,
      title: title,
      text: text,
      confirmButtonText: 'OK'
    });

    // Dopiero teraz przekieruj
    router.push({ name: 'client-orders' });
        
  } catch (err) {
    // Błąd krytyczny (np. błąd bazy danych) pokaże się w divie 'error'
    error.value = err.message || "Wystąpił błąd podczas składania zamówienia.";
  } finally {
    loading.value = false;
  }
};
</script>
    
<template>
  <h1>Twój Koszyk</h1>

  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
      <span class="visually-hidden">Składanie zamówienia...</span>
    </div>
    <p class="mt-2">Proszę czekać, generujemy potwierdzenie...</p>
  </div>

  <div v-if="error" class="alert alert-danger">
    {{ error }}
  </div>

  <div v-if="!loading && cartItemCount === 0" class="alert alert-info">
    Twój koszyk jest pusty.
  </div>

  <form v-if="!loading && cartItemCount > 0" @submit.prevent="handlePlaceOrder">
    <div class="card shadow-sm">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table align-middle">
            <thead>
              <tr>
                <th>Produkt</th>
                <th>Wariant</th>
                <th>Cena</th>
                <th>Ilość</th>
                <th>Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in cart" :key="item.variant_id">
                <td>{{ item.name }}</td>
                <td>{{ item.size }}</td>
                <td>
                  {{ item.price !== null ? (item.price * item.quantity).toFixed(2) + ' zł' : 'Brak ceny' }}
                </td>
                <td>{{ item.quantity }}</td>
                <td>
                  <button class="btn btn-sm btn-outline-danger" @click.prevent="handleRemove(item.variant_id)">
                    <Icon icon="mdi:trash-can-outline" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div class="card-body border-top">
        <div class="mb-3">
          <label for="orderNotes" class="form-label fw-bold">Uwagi do zamówienia (opcjonalnie)</label>
          <textarea 
            class="form-control" 
            id="orderNotes" 
            rows="3" 
            v-model="orderNotes"
            placeholder="Informacje dla spedycji, specjalne instrukcje..."
          ></textarea>
        </div>
      </div>
      
      <div class="card-footer text-end p-3">
        <button type:="submit" class="btn btn-success btn-lg">
          <Icon icon="mdi:check-all" class="me-2" />
          Złóż zamówienie
        </button>
      </div>
    </div>
  </form>
</template>

<style scoped>
.btn .iconify {
  vertical-align: middle;
  margin-bottom: .1em;
}
</style>