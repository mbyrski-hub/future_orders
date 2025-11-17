<script setup>
import { onMounted, inject } from 'vue';
import { useClientStore } from '@/stores/clientStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';

const $swal = inject('$swal');
const clientStore = useClientStore();
const { orders, loading, error } = storeToRefs(clientStore);

onMounted(() => {
  clientStore.fetchMyOrders();
});

const handleDownloadPdf = async (orderId) => {
  try {
    await clientStore.downloadOrderPdf(orderId);
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: err.message
    });
  }
};

const loadShipmentHistory = async (order) => {
  await clientStore.fetchOrderShipments(order);
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
  if (status === 'partial') return 'Częściowo zrealizowane';
  if (status === 'completed') return 'Zrealizowane';
  return status;
};
</script>
    
<template>
  <h1>Moje Zamówienia</h1>

  <div v-if="loading" class="text-center py-5">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Ładowanie...</span>
    </div>
  </div>

  <div v-if="error" class="alert alert-danger">
    {{ error }}
  </div>

  <div v-if="!loading && orders.length === 0" class="alert alert-info">
    Nie złożyłeś jeszcze żadnych zamówień.
  </div>

  <div v-if="!loading && orders.length > 0" class="accordion" id="ordersAccordion">
    <div v-for="order in orders" :key="order.id" class="accordion-item">
      
      <h2 class="accordion-header" :id="'heading' + order.id">
        <button 
          class="accordion-button collapsed d-flex align-items-center" 
          type="button" 
          data-bs-toggle="collapse" 
          :data-bs-target="'#collapse' + order.id"
          @click="loadShipmentHistory(order)"
        >
          <span class="me-3">Zamówienie #{{ order.id }}</span>
          <span class="me-3 text-muted">{{ formatDate(order.created_at) }}</span>
          <span class="badge" :class="getStatusClass(order.status)">
            {{ formatStatus(order.status) }}
          </span>
        </button>
        
        <button 
          class="btn btn-sm btn-outline-danger position-absolute end-0 me-5" 
          style="z-index: 10; top: 12px;"
          title="Pobierz PDF"
          @click.prevent="handleDownloadPdf(order.id)"
        >
          <Icon icon="mdi:file-pdf-box" />
        </button>
      </h2>
      
      <div :id="'collapse' + order.id" class="accordion-collapse collapse" :data-bs-parent="'#ordersAccordion'">
        <div class="accordion-body">
          
          <strong>Pozycje zamówienia:</strong>
          <table class="table table-sm mt-2 align-middle">
            <thead>
              <tr>
                <th>Produkt</th>
                <th>Wariant</th>
                <th>Cena w mom. zakupu</th>
                <th class="text-center">Status (Wysłano / Zamówiono)</th>
              </tr>
            </thead>
            <tbody>
              <tr 
                v-for="item in order.items" 
                :key="item.id" 
                :class="{'text-muted': item.shipped_quantity === item.quantity}"
              >
                <td>{{ item.product_name }}</td>
                <td>{{ item.variant_size }}</td>
                <td>
                  {{ item.price_at_order !== null ? item.price_at_order.toFixed(2) + ' zł' : 'Brak ceny' }}
                </td>
                <td class="text-center">
                  <span class="badge fs-6" :class="item.shipped_quantity === item.quantity ? 'text-bg-light' : 'text-bg-info'">
                    <Icon icon="mdi:package-variant-closed" class="me-1" />
                    {{ item.shipped_quantity }} / {{ item.quantity }} szt.
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
          
          <div v-if="order.notes" class="mt-3">
            <strong class="d-block mb-1">Twoje uwagi do zamówienia:</strong>
            <p class="text-muted" style="white-space: pre-wrap;">{{ order.notes }}</p>
          </div>

          <hr class="my-4">
          <strong>Historia wysyłek:</strong>

          <div v-if="order.shipmentsLoading" class="text-center my-3">
            <div class="spinner-border spinner-border-sm" role="status">
              <span class="visually-hidden">Ładowanie historii...</span>
            </div>
          </div>

          <div v-if="!order.shipmentsLoading && (!order.shipments || order.shipments.length === 0)" class="alert alert-light small p-2 mt-2">
            Brak szczegółowej historii wysyłek dla tego zamówienia.
          </div>

          <div v-if="!order.shipmentsLoading && order.shipments && order.shipments.length > 0" class="mt-2">
            <div v-for="shipment in order.shipments" :key="shipment.id" class="card mb-2">
              <div class="card-header p-2">
                <Icon icon="mdi:truck-delivery-outline" />
                <strong>Paczka #{{ shipment.id }}</strong>
                (Wysłano: {{ formatDate(shipment.created_at) }} przez {{ shipment.shipped_by_username }})
              </div>
              <ul class="list-group list-group-flush">
                <li v-for="item in shipment.items" :key="item.id" class="list-group-item d-flex justify-content-between small">
                  <span>{{ item.product_name }} ({{ item.variant_size }})</span>
                  <span class="fw-bold">{{ item.quantity_shipped }} szt.</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.text-muted {
  color: #888 !important;
}
.text-muted .badge {
  color: #333 !important;
}
.iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}
.accordion-header {
  position: relative;
}
.accordion-button:not(.collapsed) + .btn-outline-danger {
  display: none;
}
</style>