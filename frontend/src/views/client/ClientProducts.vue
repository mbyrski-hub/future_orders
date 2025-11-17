<script setup>
import { onMounted, ref, watch, inject } from 'vue';
import { useClientStore } from '@/stores/clientStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';
import OrderViewSwitcher from '@/components/OrderViewSwitcher.vue'; // <-- 1. IMPORTUJ PRZEŁĄCZNIK

const $swal = inject('$swal'); 
const clientStore = useClientStore();
const { products, loading, error } = storeToRefs(clientStore);
const variantQuantities = ref({});

watch(products, (newProducts) => {
  if (newProducts) {
    newProducts.forEach(product => {
      product.variants.forEach(variant => {
        if (variantQuantities.value[variant.id] === undefined) {
          variantQuantities.value[variant.id] = 0; 
        }
      });
    });
  }
}, { immediate: true });

onMounted(() => {
  if (products.value.length === 0) {
    clientStore.fetchMyProducts();
  }
});

const handleAddToCartMultiple = (product) => {
  let itemsAddedCount = 0; 
  product.variants.forEach(variant => {
    const qty = parseInt(variantQuantities.value[variant.id]) || 0;
    if (qty > 0) {
      clientStore.addToCart(product, variant, qty);
      itemsAddedCount++;
      variantQuantities.value[variant.id] = 0;
    }
  });

  if (itemsAddedCount > 0) {
    $swal.fire({
      icon: 'success',
      title: 'Dodano!',
      text: 'Produkty zostały dodane do koszyka.',
      toast: true,
      position: 'top-end',
      timer: 2000,
      showConfirmButton: false
    });
  } else {
    $swal.fire({
      icon: 'info',
      title: 'Koszyk jest pusty',
      text: 'Nie wybrano żadnych produktów (ilość musi być większa od 0).'
    });
  }
};
</script>

<template>
  <OrderViewSwitcher />

  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1>Katalog Produktów</h1>
  </div>

  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
      <span class="visually-hidden">Ładowanie...</span>
    </div>
  </div>
  <div v-if="error" class="alert alert-danger">
    {{ error }}
  </div>

  <div v-if="!loading && products.length > 0" class="row g-4">
    <div v-for="product in products" :key="product.id" class="col-md-6 col-lg-4">
      
      <div class="card h-100 d-flex flex-column shadow-sm product-card">
        
        <div v-if="product.image_url">
          <img :src="product.image_url" class="card-img-top" :alt="'Zdjęcie ' + product.name">
        </div>
        <div v-else class="card-img-top d-flex align-items-center justify-content-center bg-light text-muted" style="height: 200px;">
          <Icon icon="mdi:image-off-outline" class="fs-1" />
        </div>

        <div class="card-body d-flex flex-column flex-grow-1 p-4">
          
          <div>
            <h4 class="card-title">{{ product.name }}</h4>
            <p class="card-text text-muted small mb-3">{{ product.description }}</p>
          </div>

          <h6 class="mt-2 text-uppercase small fw-bold">Wybierz ilość:</h6>
          
          <ul class="list-group variant-list mb-3 flex-shrink-1" style="max-height: 200px; overflow-y: auto;">
            
            <li 
              v-for="variant in product.variants" 
              :key="variant.id" 
              class="list-group-item d-flex justify-content-between align-items-center"
            >
              <div>
                <label :for="'variant-' + variant.id" class="form-label mb-0 fw-bold">
                  {{ variant.size }}
                </label>
                <span v-if="variant.price !== null" class="ms-2 text-success small d-block">
                  {{ variant.price }} zł
                </span>
              </div>
              
              <div style="width: 80px;">
                <input 
                  :id="'variant-' + variant.id"
                  type="number" 
                  class="form-control form-control-sm text-center"
                  min="0"
                  step="1"
                  v-model.number="variantQuantities[variant.id]"
                  aria-label="Ilość"
                >
              </div>
            </li>
          </ul>

          <button 
            class="btn btn-primary w-100 mt-auto" 
            @click="handleAddToCartMultiple(product)"
          >
            <Icon icon="mdi:cart-plus" class="me-1 fs-5" />
            Dodaj wybrane do koszyka
          </button>

        </div>
      </div>
    </div>
  </div>

  <div v-if="!loading && products.length === 0 && !error" class="alert alert-info">
    Nie masz jeszcze przypisanych żadnych produktów. Skontaktuj się z administratorem.
  </div>
</template>


<style scoped>
/* Cała sekcja <style> pozostaje BEZ ZMIAN */
.btn .iconify {
  vertical-align: middle;
  margin-bottom: .1em; 
}
.product-card {
  background-color: var(--bs-card-bg);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.product-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--bs-shadow-lg) !important;
}
.variant-list {
  --bs-list-group-border-color: transparent;
  --bs-list-group-item-padding-x: 0;
}
.variant-list .list-group-item {
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  border-top: 1px solid var(--bs-border-color-translucent);
}
.variant-list .list-group-item:first-child {
  border-top: 0;
}
.card-img-top {
  height: 200px;
  object-fit: cover;
}
</style>