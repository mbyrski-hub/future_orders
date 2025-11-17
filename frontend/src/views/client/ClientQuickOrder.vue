<script setup>
// ... (cała sekcja <script setup> pozostaje BEZ ZMIAN) ...
import { onMounted, ref, computed, inject } from 'vue';
import { useClientStore } from '@/stores/clientStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';
import OrderViewSwitcher from '@/components/OrderViewSwitcher.vue'; // <-- 1. IMPORTUJ PRZEŁĄCZNIK

const $swal = inject('$swal');
const clientStore = useClientStore();
const { products, loading, error } = storeToRefs(clientStore);

const orderRows = ref([
  { 
    id: 1, 
    selectedProduct: null,
    selectedVariantId: null,
    quantity: 1
  }
]);

onMounted(() => {
  if (products.value.length === 0) {
    clientStore.fetchMyProducts();
  }
});

const addRow = () => {
  orderRows.value.push({
    id: Date.now(),
    selectedProduct: null,
    selectedVariantId: null,
    quantity: 1
  });
};

const removeRow = (index) => {
  orderRows.value.splice(index, 1);
};

const onProductSelected = (row) => {
  row.selectedVariantId = null;
  if (row.selectedProduct && row.selectedProduct.variants.length === 1) {
    row.selectedVariantId = row.selectedProduct.variants[0].id;
  }
};

const isSubmitting = ref(false);

const handleQuickSubmit = async () => {
  isSubmitting.value = true;
  let itemsAddedCount = 0;

  try {
    for (const row of orderRows.value) {
      if (row.selectedProduct && row.selectedVariantId && row.quantity > 0) {
        
        const selectedVariant = row.selectedProduct.variants.find(
          v => v.id === row.selectedVariantId
        );

        if (selectedVariant) {
          clientStore.addToCart(row.selectedProduct, selectedVariant, row.quantity);
          itemsAddedCount++;
        }
      }
    }

    if (itemsAddedCount > 0) {
      $swal.fire({
        icon: 'success',
        title: 'Dodano!',
        text: `Pomyślnie dodano ${itemsAddedCount} pozycji do koszyka.`,
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 2000
      });
      orderRows.value = [{ 
        id: Date.now(), 
        selectedProduct: null, 
        selectedVariantId: null, 
        quantity: 1 
      }];
    } else {
      $swal.fire({
        icon: 'info',
        title: 'Koszyk jest pusty',
        text: 'Nie wybrano żadnych poprawnych produktów lub ilości.'
      });
    }

  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: err.message
    });
  } finally {
    isSubmitting.value = false;
  }
};
</script>

<template>
  <OrderViewSwitcher />

  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Szybkie Zamówienie</h1>
  </div>

  <p class="lead">
    Użyj tego formularza, aby szybko dodać wiele produktów do koszyka.
  </p>

  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status"></div>
  </div>
  <div v-if="error" class="alert alert-danger">
    {{ error }}
  </div>

  <div v-if="!loading && products.length === 0" class="alert alert-info">
    Nie masz jeszcze przypisanych żadnych produktów.
  </div>

  <form v-if="!loading && products.length > 0" @submit.prevent="handleQuickSubmit">
    <div class="card shadow-sm">
      <div class="card-body">
        <div class="table-responsive">
          <table class="table align-middle quick-order-table">
            <thead class="table-light">
              <tr>
                <th style="width: 45%;">Wybierz Produkt</th>
                <th style="width: 30%;">Wybierz Wariant (Rozmiar)</th>
                <th style="width: 15%;">Ilość</th>
                <th style="width: 10%;" class="text-end">Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in orderRows" :key="row.id">
                
                <td>
                  <select 
                    class="form-select" 
                    v-model="row.selectedProduct"
                    @change="onProductSelected(row)"
                    required
                  >
                    <option :value="null" disabled>Wyszukaj lub wybierz produkt...</option>
                    <option v-for="product in products" :key="product.id" :value="product">
                      {{ product.name }}
                    </option>
                  </select>
                </td>
                
                <td>
                  <select 
                    class="form-select" 
                    v-model="row.selectedVariantId"
                    :disabled="!row.selectedProduct"
                    required
                  >
                    <option :value="null" disabled>Wybierz wariant...</option>
                    <option 
                      v-for="variant in row.selectedProduct?.variants" 
                      :key="variant.id" 
                      :value="variant.id"
                    >
                      {{ variant.size }} 
                      <span v-if="variant.price !== null">({{ variant.price }} zł)</span>
                    </option>
                  </select>
                </td>
                
                <td>
                  <input 
                    type="number" 
                    class="form-control" 
                    min="1"
                    v-model.number="row.quantity"
                    :disabled="!row.selectedVariantId"
                    required
                  >
                </td>
                
                <td class="text-end">
                  <button 
                    type="button" 
                    class="btn btn-outline-danger btn-sm"
                    @click="removeRow(index)"
                    :disabled="orderRows.length <= 1"
                    title="Usuń wiersz"
                  >
                    <Icon icon="mdi:trash-can-outline" />
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      
      <div class="card-footer d-flex justify-content-between p-3">
        <button type="button" class="btn btn-outline-secondary" @click="addRow">
          <Icon icon="mdi:plus" class="me-1" />
          Dodaj kolejny wiersz
        </button>
        <button type="submit" class="btn btn-success btn-lg" :disabled="isSubmitting">
          <span v-if="isSubmitting" class="spinner-border spinner-border-sm me-2"></span>
          Dodaj wszystko do koszyka
        </button>
      </div>
    </div>
  </form>
</template>

<style scoped>
/* Cała sekcja <style> pozostaje BEZ ZMIAN */
.btn .iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}
.quick-order-table th, .quick-order-table td {
  vertical-align: top;
  padding-top: 1rem;
  padding-bottom: 1rem;
}
</style>