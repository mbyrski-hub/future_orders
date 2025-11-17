<script setup>
import { onMounted, onUnmounted, ref, computed, inject, watch } from 'vue';
import { useShippingStore } from '@/stores/shippingStore';
import { storeToRefs } from 'pinia';
import { Modal } from 'bootstrap';
import { Icon } from '@iconify/vue';

// --- WSTRZYKNIJ $swal ---
const $swal = inject('$swal');

// --- STORE ---
const shippingStore = useShippingStore();
const { orders, loading, error, statusCounts } = storeToRefs(shippingStore);

// --- MODALE ---
const shippingModalElement = ref(null); // Modal do WYSYŁANIA
let bsShippingModal = null;
const historyModalElement = ref(null);  // Modal do HISTORII
let bsHistoryModal = null;

// --- DANE DLA MODALI ---
const orderToShip = ref(null); // Zamówienie do wysłania
const selectedOrder = ref(null); // Zamówienie do podglądu historii
const shippingData = ref({});
const shippingLoading = ref(false);

// --- LOGIKA DLA LISTY ZBIORCZEJ ---
const selectedOrderIds = ref([]); // Przechowuje ID zaznaczonych zamówień
const pickingListLoading = ref(false);

// Zaznaczanie / Odznaczanie wszystkich
const areAllSelected = computed({
  get: () => {
    const visibleOrders = orders.value.filter(o => o.status !== 'completed');
    return visibleOrders.length > 0 && selectedOrderIds.value.length === visibleOrders.length;
  },
  set: (value) => {
    if (value) {
      selectedOrderIds.value = orders.value
        .filter(o => o.status !== 'completed')
        .map(o => o.id);
    } else {
      selectedOrderIds.value = [];
    }
  }
});

onMounted(() => {
  fetchData(); // Pobierz dane przy starcie
  if (shippingModalElement.value) {
    bsShippingModal = new Modal(shippingModalElement.value);
  }
  if (historyModalElement.value) {
    bsHistoryModal = new Modal(historyModalElement.value);
  }
});

onUnmounted(() => {
  bsShippingModal?.dispose();
  bsHistoryModal?.dispose();
});

// Watcher dla globalnego błędu
watch(error, (newError) => {
  if (newError) {
    $swal.fire({ icon: 'error', title: 'Błąd Krytyczny', text: newError });
  }
});

// --- FUNKCJE POMOCNICZE ---
const getStatusClass = (status) => {
  if (status === 'completed') return 'text-bg-success';
  if (status === 'partial') return 'text-bg-warning';
  return 'text-bg-primary';
};
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
};
const formatStatus = (status) => {
  if (status === 'new') return 'Nowe';
  if (status === 'partial') return 'Częściowe';
  if (status === 'completed') return 'Zrealizowane';
  return status;
};
const getItemRemaining = (item) => {
  return item.quantity - item.shipped_quantity;
};

// --- LOGIKA FILTROWANIA ---
const statusFilter = ref('new'); // Domyślna zakładka
const searchQuery = ref('');

const fetchData = async () => {
  const params = {
    status: statusFilter.value,
    search: searchQuery.value
  };
  // Ta funkcja automatycznie pobierze też liczniki (dzięki zmianom w store)
  await shippingStore.fetchAllOrders(params);
};

watch(statusFilter, fetchData);
let searchTimeout = null;
watch(searchQuery, () => {
  clearTimeout(searchTimeout);
  searchTimeout = setTimeout(() => {
    fetchData();
  }, 500); 
});

// --- LOGIKA MODALA WYSYŁKI ---
const openShippingModal = (order) => {
  orderToShip.value = order;
  shippingData.value = {};
  order.items.forEach(item => {
    shippingData.value[item.id] = 0;
  });
  bsShippingModal.show();
};

const handleShippingSubmit = async () => {
  if (!orderToShip.value) return;
  shippingLoading.value = true;
  try {
    const itemsToShipApi = Object.keys(shippingData.value)
      .map(itemId => ({
        item_id: parseInt(itemId),
        quantity_to_ship: parseInt(shippingData.value[itemId] || 0)
      }))
      .filter(item => item.quantity_to_ship > 0);

    if (itemsToShipApi.length === 0) {
      throw new Error("Nie wybrano żadnych produktów do wysłania.");
    }
    await shippingStore.shipItems(orderToShip.value.id, itemsToShipApi);
    bsShippingModal.hide();
    $swal.fire({
      icon: 'success',
      title: 'Zrealizowano!',
      text: `Wysyłka dla zamówienia #${orderToShip.value.id} została zatwierdzona.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2500
    });
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: err.message || "Wystąpił błąd."
    });
  } finally {
    shippingLoading.value = false;
  }
};

// --- LOGIKA MODALA HISTORII I PDF ---
const handleDownloadPdf = async (orderId) => {
  try {
    await shippingStore.downloadOrderPdf(orderId);
  } catch (err) {
    $swal.fire({ icon: 'error', title: 'Błąd', text: err.message });
  }
};

const openHistoryModal = async (order) => {
  selectedOrder.value = order;
  await shippingStore.fetchOrderShipments(order);
  bsHistoryModal.show();
};

// --- LOGIKA LISTY ZBIORCZEJ ---
const handleGeneratePickingList = async () => {
  if (selectedOrderIds.value.length === 0) {
    $swal.fire({ icon: 'info', title: 'Brak zamówień', text: 'Najpierw zaznacz zamówienia do spakowania.' });
    return;
  }
  
  pickingListLoading.value = true;
  try {
    await shippingStore.generatePickingListPdf(selectedOrderIds.value);
  } catch (err) {
    $swal.fire({ icon: 'info', title: 'Informacja', text: err.message });
  } finally {
    pickingListLoading.value = false;
  }
};
</script>

<template>
  <div> <div class="d-flex justify-content-between align-items-center mb-3">
      <h1>Panel Spedycji</h1>
      <button class="btn btn-primary" @click="fetchData" :disabled="loading">
        <Icon icon="mdi:refresh" class="me-2" />
        Odśwież Listę
      </button>
    </div>
    
    <div class="card shadow-sm">
      <div class="card-body">
        
        <div class="row g-3 mb-3">
          <div class="col-lg-7">
            <input 
              type="text" 
              class="form-control" 
              placeholder="Filtruj po nazwie klienta..."
              v-model="searchQuery"
            >
          </div>
          <div class="col-lg-5">
            <button 
              class="btn btn-success w-100" 
              @click="handleGeneratePickingList"
              :disabled="selectedOrderIds.length === 0 || pickingListLoading"
            >
              <span v-if="pickingListLoading" class="spinner-border spinner-border-sm me-2"></span>
              <Icon v-else icon="mdi:printer-outline" class="me-2" />
              Drukuj Listę do Spakowania ({{ selectedOrderIds.length }})
            </button>
          </div>
        </div>

        <ul class="nav nav-tabs" id="orderTabs" role="tablist">
          <li class="nav-item" role="presentation">
            <button class="nav-link" :class="{'active': statusFilter === 'all'}" @click="statusFilter = 'all'">
              Wszystkie
              <span v-if="statusCounts" class="badge bg-secondary ms-1">{{ statusCounts.all }}</span>
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link tab-new" :class="{'active': statusFilter === 'new'}" @click="statusFilter = 'new'">
              Nowe
              <span v-if="statusCounts" class="badge bg-primary ms-1">{{ statusCounts.new }}</span>
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link tab-partial" :class="{'active': statusFilter === 'partial'}" @click="statusFilter = 'partial'">
              Częściowe
              <span v-if="statusCounts" class="badge bg-warning text-dark ms-1">{{ statusCounts.partial }}</span>
            </button>
          </li>
          <li class="nav-item" role="presentation">
            <button class="nav-link tab-completed" :class="{'active': statusFilter === 'completed'}" @click="statusFilter = 'completed'">
              Zrealizowane
              <span v-if="statusCounts" class="badge bg-success ms-1">{{ statusCounts.completed }}</span>
            </button>
          </li>
        </ul>

        <div class="table-responsive">
          <table class="table table-hover align-middle">
            <thead class="table-light">
              <tr>
                <th scope="col" class="text-center" style="width: 1%;">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    title="Zaznacz/Odznacz wszystkie widoczne"
                    v-model="areAllSelected"
                  >
                </th>
                <th scope="col">Zamówienie</th>
                <th scope="col">Klient</th>
                <th scope="col">Pozycje (Wysłano / Zamówiono)</th>
                <th scope="col" class="text-center">Status</th>
                <th scope="col" class="text-end">Akcje</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="6" class="text-center text-muted py-4">
                  <div class="spinner-border spinner-border-sm" role="status"></div>
                </td>
              </tr>
              <tr v-else-if="orders.length === 0">
                <td colspan="6" class="text-center text-muted py-4">
                  Brak zamówień pasujących do filtrów.
                </td>
              </tr>
              <tr v-for="order in orders" :key="order.id">
                <td class="text-center">
                  <input 
                    class="form-check-input" 
                    type="checkbox" 
                    :value="order.id"
                    v-model="selectedOrderIds"
                    :disabled="order.status === 'completed'"
                  >
                </td>
                <td>
                  <strong>#{{ order.id }}</strong>
                  <small class="d-block text-muted">{{ formatDate(order.created_at) }}</small>
                </td>
                <td>
                  <span class="fw-bold">{{ order.user_info.first_name }} {{ order.user_info.last_name }}</span>
                  <small class="d-block text-muted">{{ order.user_info.username }} ({{ order.user_info.email }})</small>
                </td>
                <td>
                  <ul class="list-unstyled mb-0 small">
                    <li v-for="item in order.items" :key="item.id" :class="{'text-muted text-decoration-line-through': getItemRemaining(item) === 0}">
                      {{ item.product_name }} ({{ item.variant_size }})
                      <strong>
                        ({{ item.shipped_quantity }} / {{ item.quantity }})
                      </strong>
                    </li>
                  </ul>
                </td>
                <td class="text-center">
                  <span class="badge fs-6" :class="getStatusClass(order.status)">
                    {{ formatStatus(order.status) }}
                  </span>
                </td>
                <td class="text-end">
                  <button 
                    class="btn btn-sm btn-outline-secondary me-2" 
                    title="Zobacz historię wysyłek"
                    @click="openHistoryModal(order)"
                  >
                    <Icon icon="mdi:history" />
                  </button>
                  <button 
                    class="btn btn-sm btn-outline-danger me-2" 
                    title="Pobierz PDF"
                    @click="handleDownloadPdf(order.id)"
                  >
                    <Icon icon="mdi:file-pdf-box" />
                  </button>
                  <button 
                    class="btn btn-primary btn-sm"
                    @click="openShippingModal(order)"
                    :disabled="order.status === 'completed'"
                  >
                    <Icon icon="mdi:truck-delivery-outline" class="me-1" />
                    Zarządzaj wysyłką
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div> 

  <Teleport to="body">
  
    <div class="modal fade" id="shippingModal" ref="shippingModalElement" tabindex="-1" aria-labelledby="shippingModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <form @submit.prevent="handleShippingSubmit">
            <div class="modal-header">
              <h5 class="modal-title" id="shippingModalLabel">
                Realizuj zamówienie #{{ orderToShip?.id }}
              </h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <p>Wprowadź liczbę sztuk, którą **teraz wysyłasz**.</p>
              <table class="table align-middle">
                <thead>
                  <tr>
                    <th>Produkt</th>
                    <th>Info (Wysłano / Zamówiono)</th>
                    <th style="width: 150px;">Wysyłam teraz</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in orderToShip?.items" :key="item.id">
                    <td>
                      {{ item.product_name }}
                      <small class="d-block text-muted">{{ item.variant_size }}</small>
                    </td>
                    <td>
                      <span class="badge text-bg-secondary fs-6">
                        {{ item.shipped_quantity }} / {{ item.quantity }}
                      </span>
                    </td>
                    <td>
                      <input 
                        type="number" 
                        class="form-control"
                        min="0"
                        :max="getItemRemaining(item)"
                        v-model.number="shippingData[item.id]"
                        :disabled="getItemRemaining(item) === 0"
                      >
                      <small class="text-muted" v-if="getItemRemaining(item) > 0">
                        (Max: {{ getItemRemaining(item) }})
                      </small>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
              <button type="submit" class="btn btn-success" :disabled="shippingLoading">
                <span v-if="shippingLoading" class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                {{ shippingLoading ? 'Przetwarzanie...' : 'Zatwierdź wysyłkę' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  
    <div class="modal fade" id="historyModal" ref="historyModalElement" tabindex="-1" aria-labelledby="historyModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="historyModalLabel">
              Historia wysyłek dla zamówienia #{{ selectedOrder?.id }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            
            <div v-if="selectedOrder?.shipmentsLoading" class="text-center my-3">
              <div class="spinner-border spinner-border-sm" role="status"></div>
            </div>

            <div v-if="!selectedOrder?.shipmentsLoading && (!selectedOrder?.shipments || selectedOrder?.shipments.length === 0)" class="alert alert-info">
              Brak szczegółowej historii wysyłek.
            </div>

            <div v-if="selectedOrder?.shipments && selectedOrder.shipments.length > 0">
              <div v-for="shipment in selectedOrder.shipments" :key="shipment.id" class="card mb-3">
                <div class="card-header p-2">
                  <Icon icon="mdi:package-variant-closed" />
                  <strong>Paczka #{{ shipment.id }}</strong>
                  (Wysłano: {{ formatDate(shipment.created_at) }} przez {{ shipment.shipped_by_username }})
                </div>
                <ul class="list-group list-group-flush">
                  <li v-for="item in shipment.items" :key="item.id" class="list-group-item d-flex justify-content-between">
                    <span>{{ item.product_name }} ({{ item.variant_size }})</span>
                    <span class="fw-bold">{{ item.quantity_shipped }} szt.</span>
                  </li>
                </ul>
              </div>
            </div>

          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zamknij</button>
          </div>
        </div>
      </div>
    </div>
    
  </Teleport>
  </template>

<style scoped>
.text-decoration-line-through {
  color: #999 !important;
}
.btn .iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}

/* ================================================================
  STYLE DLA ZAKŁADEK
  ================================================================
*/
.nav-tabs {
  border-bottom: none;
}
.nav-tabs .nav-link {
  border: 1px solid var(--bs-border-color-translucent);
  border-bottom: none;
  margin-right: 2px;
  border-radius: 0.375rem 0.375rem 0 0;
  color: var(--bs-secondary-color);
  font-weight: 500;
}

/* Kolory NIEAKTYWNYCH zakładek */
.nav-tabs .nav-link.tab-new {
  background-color: var(--bs-primary-bg-subtle);
  border-color: var(--bs-primary-border-subtle);
}
.nav-tabs .nav-link.tab-partial {
  background-color: var(--bs-warning-bg-subtle);
  border-color: var(--bs-warning-border-subtle);
}
.nav-tabs .nav-link.tab-completed {
  background-color: var(--bs-success-bg-subtle);
  border-color: var(--bs-success-border-subtle);
}

/* Kolory AKTYWNYCH zakładek */
.nav-tabs .nav-link.tab-new.active {
  background-color: var(--bs-primary);
  border-color: var(--bs-primary);
  color: white;
}
.nav-tabs .nav-link.tab-partial.active {
  background-color: var(--bs-warning);
  border-color: var(--bs-warning);
  color: #333;
}
.nav-tabs .nav-link.tab-completed.active {
  background-color: var(--bs-success);
  border-color: var(--bs-success);
  color: white;
}
.nav-tabs .nav-link:not(.tab-new, .tab-partial, .tab-completed).active {
  color: var(--bs-body-color);
  border-bottom: 3px solid var(--bs-secondary);
}
/* Poprawka dla badge wewnątrz przycisku */
.nav-link .badge {
  font-size: 0.8em;
}
</style>