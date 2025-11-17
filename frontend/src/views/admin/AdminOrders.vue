<script setup>
import { onMounted, inject, ref, onUnmounted, watch } from 'vue';
import { useShippingStore } from '@/stores/shippingStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';
import { Modal } from 'bootstrap';

const $swal = inject('$swal');
const shippingStore = useShippingStore();
// ZMIANA: Pobieramy 'statusCounts'
const { orders, loading, error, statusCounts } = storeToRefs(shippingStore);

const historyModalElement = ref(null);
let bsHistoryModal = null;
const selectedOrder = ref(null);
const statusFilter = ref('all');
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

onMounted(() => {
  fetchData();
  if (historyModalElement.value) {
    bsHistoryModal = new Modal(historyModalElement.value);
  }
});
onUnmounted(() => {
  bsHistoryModal?.dispose();
});

const openHistoryModal = async (order) => {
  selectedOrder.value = order;
  await shippingStore.fetchOrderShipments(order);
  bsHistoryModal.show();
};
const handleDownloadPdf = async (orderId) => {
  try {
    await shippingStore.downloadOrderPdf(orderId);
  } catch (err) {
    $swal.fire({ icon: 'error', title: 'Błąd', text: err.message });
  }
};
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
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Wszystkie Zamówienia (Podgląd)</h1>
    <button class="btn btn-primary" @click="fetchData" :disabled="loading">
      <Icon icon="mdi:refresh" class="me-2" />
      Odśwież Listę
    </button>
  </div>
  
  <div class="card shadow-sm">
    <div class="card-body">
      <div class="mb-3">
        <input 
          type="text" 
          class="form-control" 
          placeholder="Filtruj po nazwie klienta..."
          v-model="searchQuery"
        >
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
              <th>ID Zam.</th>
              <th>Data</th>
              <th>Klient</th>
              <th>Pozycje (Wysłano/Zamówiono)</th>
              <th>Status</th>
              <th class="text-end">Akcje</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="loading">
              <td colspan="6" class="text-center text-muted py-4">
                <div class="spinner-border spinner-border-sm" role="status"></div>
                <span class="ms-2">Ładowanie zamówień...</span>
              </td>
            </tr>
            <tr v-else-if="error">
              <td colspan="6" class="text-center text-danger py-4">
                {{ error }}
              </td>
            </tr>
            <tr v-else-if="orders.length === 0">
              <td colspan="6" class="text-center text-muted py-4">
                Brak zamówień pasujących do filtrów.
              </td>
            </tr>
            <tr v-for="order in orders" :key="order.id">
              <th>#{{ order.id }}</th>
              <td>{{ formatDate(order.created_at) }}</td>
              <td>
                <span class="fw-bold">{{ order.user_info.first_name }} {{ order.user_info.last_name }}</span>
                <small class="d-block text-muted">{{ order.user_info.username }} ({{ order.user_info.email }})</small>
              </td>
              <td>
                <ul v-if="order.items" class="list-unstyled mb-0 small">
                  <li v-for="item in order.items" :key="item.id" :class="{'text-muted': item.shipped_quantity === item.quantity}">
                    <strong>({{ item.shipped_quantity }}/{{ item.quantity }})</strong> 
                    {{ item.product_name }} ({{ item.variant_size }})
                  </li>
                </ul>
              </td>
              <td>
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
                  class="btn btn-sm btn-outline-danger" 
                  title="Pobierz PDF"
                  @click="handleDownloadPdf(order.id)"
                >
                  <Icon icon="mdi:file-pdf-box" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <Teleport to="body">
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
.btn .iconify {
  vertical-align: middle;
}
.text-muted {
  color: #888 !important;
}

/* Style dla zakładek (bez zmian) */
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
}
/* Poprawka dla badge wewnątrz przycisku */
.nav-link .badge {
  font-size: 0.8em;
}
</style>