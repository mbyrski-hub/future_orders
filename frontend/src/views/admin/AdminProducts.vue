<script setup>
import { onMounted, onUnmounted, ref, inject } from 'vue'; // <-- DODANO 'inject'
import { useProductStore } from '@/stores/productStore';
import { storeToRefs } from 'pinia';
import { Modal } from 'bootstrap';
import { Icon } from '@iconify/vue'; // <-- Dodano import Iconify

// --- WSTRZYKNIJ $swal ---
const $swal = inject('$swal');

// --- STORE ---
const productStore = useProductStore();
const { products, loading, error: storeError } = storeToRefs(productStore);

// --- MODALE ---
const productModalElement = ref(null);
let bsProductModal = null;
const deleteModalElement = ref(null);
let bsDeleteModal = null;

// const formError = ref(null); // <-- Już niepotrzebne, $swal przejmuje błędy
const editMode = ref(false);

onMounted(() => {
  productStore.fetchProducts();
  
  if (productModalElement.value) {
    bsProductModal = new Modal(productModalElement.value);
  }
  if (deleteModalElement.value) {
    bsDeleteModal = new Modal(deleteModalElement.value);
  }
});

onUnmounted(() => {
  bsProductModal?.dispose();
  bsDeleteModal?.dispose();
});

// --- DANE FORMULARZA ---
const formData = ref(getInitialProductData());
const productToDelete = ref(null);

function getInitialProductData() {
  return {
    id: null,
    name: '',
    description: '',
    image_url: '',
    variants: [
      { size: 'Uniwersalny', price: null }
    ]
  };
}

// --- FUNKCJE OBSŁUGI MODALI ---
const openAddModal = () => {
  editMode.value = false;
  // formError.value = null; // <-- Usunięte
  formData.value = getInitialProductData();
  bsProductModal.show();
};

const openEditModal = (product) => {
  editMode.value = true;
  // formError.value = null; // <-- Usunięte
  formData.value = JSON.parse(JSON.stringify(product));
  bsProductModal.show();
};

const openDeleteModal = (product) => {
  productToDelete.value = product;
  bsDeleteModal.show();
};

// --- FUNKCJE OBSŁUGI WARIANTÓW ---
const addVariant = () => {
  formData.value.variants.push({ size: '', price: null });
};

const removeVariant = (index) => {
  if (formData.value.variants.length > 1) {
    formData.value.variants.splice(index, 1);
  } else {
    // ZMIANA: Zastąpiono 'alert' i 'formError' na $swal
    $swal.fire({
      icon: 'warning',
      title: 'Ostrzeżenie',
      text: 'Produkt musi mieć przynajmniej jeden wariant.'
    });
  }
};

// --- FUNKCJE OBSŁUGI FORMULARZY (SUBMIT) ---

// Zapis (Dodaj lub Edytuj)
const handleSubmit = async () => {
  // formError.value = null; // <-- Usunięte
  
  try {
    if (formData.value.variants.some(v => v.price != null && v.price < 0)) {
        throw new Error("Cena nie może być ujemna.");
    }
    
    if (editMode.value) {
      await productStore.updateProduct(formData.value.id, formData.value);
    } else {
      await productStore.createProduct(formData.value);
    }
    
    bsProductModal.hide(); // Sukces, zamknij modal
    
    // --- ZMIANA: Dodano powiadomienie o sukcesie ---
    $swal.fire({
      icon: 'success',
      title: 'Zapisano!',
      text: `Produkt "${formData.value.name}" został pomyślnie zapisany.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2000
    });
    
  } catch (err) {
    // --- ZMIANA: Zastąpiono 'formError' na $swal ---
    $swal.fire({
      icon: 'error',
      title: 'Błąd zapisu',
      text: err.message || 'Wystąpił nieoczekiwany błąd.'
    });
  }
};

// Potwierdzenie Usunięcia
const handleDeleteConfirm = async () => {
  if (!productToDelete.value) return;

  try {
    const productName = productToDelete.value.name; // Zapisz nazwę przed usunięciem
    await productStore.deleteProduct(productToDelete.value.id);
    bsDeleteModal.hide(); 
    
    // --- ZMIANA: Dodano powiadomienie o sukcesie ---
    $swal.fire({
      icon: 'success',
      title: 'Usunięto!',
      text: `Produkt "${productName}" został usunięty.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2000
    });

  } catch (err) {
    // --- ZMIANA: Zastąpiono 'storeError' na $swal ---
    $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: err.message || 'Błąd podczas usuwania produktu.'
    });
    bsDeleteModal.hide();
  } finally {
    productToDelete.value = null;
  }
};

const formatVariants = (variants) => {
  if (!variants || variants.length === 0) {
    return 'Brak wariantów';
  }
  return variants.map(v => 
    `${v.size} (${v.price !== null ? v.price + ' zł' : 'brak ceny'})`
  ).join(' | ');
};
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Zarządzanie Produktami</h1>
    <button class="btn btn-primary" @click="openAddModal">
      <Icon icon="mdi:plus-box-outline" class="me-1" />
      Dodaj Nowy Produkt
    </button>
  </div>

  <div v-if="loading && products.length === 0" class="text-center">
    <div class="spinner-border" role="status">
      <span class="visually-hidden">Ładowanie...</span>
    </div>
  </div>

  <div v-if="storeError" class="alert alert-danger">
    {{ storeError }}
  </div>

  <div v-if="!loading || products.length > 0" class="card shadow-sm">
    <div class="card-body">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th scope="col">ID</th>
            <th scope="col">Nazwa</th>
            <th scope="col">Opis</th>
            <th scope="col">Warianty (Rozmiar, Cena)</th>
            <th scope="col" class="text-end">Akcje</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id">
            <th>{{ product.id }}</th>
            <td>{{ product.name }}</td>
            <td>{{ product.description }}</td>
            <td>{{ formatVariants(product.variants) }}</td>
            <td class="text-end">
              <button class="btn btn-sm btn-outline-secondary me-2" @click="openEditModal(product)">
                <Icon icon="mdi:pencil-outline" /> Edytuj
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="openDeleteModal(product)">
                <Icon icon="mdi:trash-can-outline" /> Usuń
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div v-if="!loading && products.length === 0 && !storeError" class="alert alert-info">
    Nie znaleziono żadnych produktów. Dodaj pierwszy!
  </div>


  <div class="modal fade" id="productModal" ref="productModalElement" tabindex="-1" aria-labelledby="productModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="productModalLabel">
            {{ editMode ? 'Edytuj Produkt' : 'Nowy Produkt' }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            
            <div class="mb-3">
              <label for="productName" class="form-label">Nazwa produktu</label>
              <input type="text" class="form-control" id="productName" v-model="formData.name" required>
            </div>
            <div class="mb-3">
              <label for="productDescription" class="form-label">Opis</label>
              <textarea class="form-control" id="productDescription" rows="3" v-model="formData.description"></textarea>
            </div>
            <div class="mb-3">
              <label for="productImageUrl" class="form-label">URL Zdjęcia (opcjonalnie)</label>
              <input 
                type="text" 
                class="form-control" 
                id="productImageUrl" 
                v-model="formData.image_url" 
                placeholder="https://.../obrazek.jpg"
              >
            </div>

            <hr>
            
            <h5>Warianty (rozmiary i ceny)</h5>

            <div v-for="(variant, index) in formData.variants" :key="index" class="row g-3 align-items-center mb-2">
              <div class="col-md-5">
                <label class="form-label">Rozmiar</label>
                <input type="text" class="form-control" v-model="variant.size" placeholder="np. M, L, 42, Uniwersalny" required>
              </div>
              <div class="col-md-4">
                <label class="form-label">Cena (zł) (opcjonalna)</label>
                <input type="number" step="0.01" min="0" class="form-control" v-model.number="variant.price">
              </div>
              <div class="col-md-3 d-flex align-items-end">
                <button type="button" class="btn btn-danger w-100" @click="removeVariant(index)" :disabled="formData.variants.length <= 1">
                  <Icon icon="mdi:delete-outline" class="me-1" /> Usuń
                </button>
              </div>
            </div>

            <button type="button" class="btn btn-outline-primary mt-2" @click="addVariant">
              <Icon icon="mdi:plus" class="me-1" /> Dodaj kolejny wariant
            </button>

          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              {{ loading ? 'Zapisywanie...' : (editMode ? 'Zapisz zmiany' : 'Stwórz Produkt') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div class="modal fade" id="deleteConfirmModal" ref="deleteModalElement" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="deleteModalLabel">Potwierdź Usunięcie</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          Czy na pewno chcesz usunąć produkt: 
          <strong>{{ productToDelete?.name }}</strong>?
          <br>
          Ta operacja jest nieodwracalna.
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
          <button type="button" class="btn btn-danger" @click="handleDeleteConfirm" :disabled="loading">
            <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
            {{ loading ? 'Usuwanie...' : 'Usuń' }}
          </button>
        </div>
      </div>
    </div>
  </div>
  
</template>

<style scoped>
/* Styl dla ikon w przyciskach */
.btn .iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}
</style>