<script setup>
import { onMounted, computed, ref, watch } from 'vue';
import { useDashboardStore } from '@/stores/dashboardStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';
import { Bar, Doughnut } from 'vue-chartjs';
import { 
  Chart as ChartJS, 
  Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement
} from 'chart.js';

ChartJS.register(
  Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale, ArcElement
);

const dashboardStore = useDashboardStore();
const { stats, latestOrders, loading, error } = storeToRefs(dashboardStore);

// --- LOGIKA FILTROWANIA ---
const selectedPeriod = ref('all_time'); 
const currentMonth = new Date().getMonth();
const currentYear = new Date().getFullYear();
const selectedMonth = ref(currentMonth);
const selectedYear = ref(currentYear);

// --- POPRAWKA: Przechowujemy aktywną etykietę w 'ref', a nie 'computed' ---
const activeFilterText = ref('(Cały okres)');
// --- KONIEC POPRAWKI ---

const months = ref([
  { value: 0, name: 'Styczeń' }, { value: 1, name: 'Luty' }, { value: 2, name: 'Marzec' },
  { value: 3, name: 'Kwiecień' }, { value: 4, name: 'Maj' }, { value: 5, name: 'Czerwiec' },
  { value: 6, name: 'Lipiec' }, { value: 7, name: 'Sierpień' }, { value: 8, name: 'Wrzesień' },
  { value: 9, name: 'Październik' }, { value: 10, name: 'Listopad' }, { value: 11, name: 'Grudzień' }
]);
const years = computed(() => {
  const startYear = 2023;
  const endYear = currentYear;
  let yearArray = [];
  for (let y = endYear; y >= startYear; y--) {
    yearArray.push(y);
  }
  return yearArray;
});

const formatDateForApi = (date) => {
  return date.toISOString().split('T')[0];
}

// --- POPRAWKA: 'fetchData' teraz ręcznie ustawia etykietę ---
const fetchData = (period) => {
  selectedPeriod.value = period;
  let params = {};
  const today = new Date();
  
  if (period === 'last_7_days') {
    const startDate = new Date();
    startDate.setDate(today.getDate() - 7);
    params.start_date = formatDateForApi(startDate);
    params.end_date = formatDateForApi(today);
    
    // Ustaw etykietę
    activeFilterText.value = '(Ostatnie 7 dni)';
    
  } else if (period === 'custom_month') {
    const year = selectedYear.value;
    const month = selectedMonth.value;
    const startDate = new Date(year, month, 1);
    const endDate = new Date(year, month + 1, 0); 
    params.start_date = formatDateForApi(startDate);
    params.end_date = formatDateForApi(endDate);
    
    // Ustaw etykietę
    const monthName = months.value.find(m => m.value === month)?.name;
    activeFilterText.value = `(${monthName} ${year})`;
    
  } else {
    // Domyślnie 'all_time'
    activeFilterText.value = '(Cały okres)';
  }

  dashboardStore.fetchDashboardStats(params);
  dashboardStore.fetchLatestOrders(); 
}
// --- KONIEC POPRAWKI ---

onMounted(() => {
  fetchData('all_time');
});

// --- Usunęliśmy 'filterPeriodText' computed ---

// --- Dane dla wykresów (bez zmian) ---
const topClientsData = computed(() => {
  const data = stats.value?.charts?.top_clients || [];
  return {
    labels: data.map(client => client.username),
    datasets: [{
      label: 'Liczba zamówień',
      backgroundColor: '#0d6efd',
      data: data.map(client => client.orders),
      borderRadius: 4
    }]
  };
});
const topProductsData = computed(() => {
  const data = stats.value?.charts?.top_products || [];
  return {
    labels: data.map(product => product.name),
    datasets: [{
      backgroundColor: ['#0d6efd', '#198754', '#ffc107', '#dc3545', '#6c757d'],
      data: data.map(product => product.quantity)
    }]
  };
});
const chartOptions = { responsive: true, maintainAspectRatio: false };
const doughnutOptions = {
  ...chartOptions,
  plugins: { legend: { position: 'right' } }
};

// --- Funkcje pomocnicze dla listy (bez zmian) ---
const getStatusClass = (status) => {
  if (status === 'completed') return 'text-bg-success';
  if (status === 'partial') return 'text-bg-warning';
  return 'text-bg-primary';
};
const formatDate = (dateString) => {
  return new Date(dateString).toLocaleString('pl-PL', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' });
};
const formatStatus = (status) => {
  if (status === 'new') return 'Nowe';
  if (status === 'partial') return 'Częściowe';
  if (status === 'completed') return 'Zrealizowane';
  return status;
};
</script>

<template>
  <div>
    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
      <h1 class="mb-0">Kokpit</h1>
      
      <div class="d-flex align-items-center flex-wrap gap-2">
        <div class="btn-group" role="group">
          <button 
            class="btn" 
            :class="selectedPeriod === 'all_time' ? 'btn-primary' : 'btn-outline-primary'"
            @click="fetchData('all_time')"
          >
            Wszystko
          </button>
          <button 
            class="btn" 
            :class="selectedPeriod === 'last_7_days' ? 'btn-primary' : 'btn-outline-primary'"
            @click="fetchData('last_7_days')"
          >
            Ost. 7 Dni
          </button>
        </div>
        <div class="d-flex align-items-center">
          <select class="form-select form-select-sm" v-model="selectedMonth" style="width: 120px;" aria-label="Wybierz miesiąc">
            <option v-for="month in months" :key="month.value" :value="month.value">{{ month.name }}</option>
          </select>
          <select class="form-select form-select-sm mx-2" v-model="selectedYear" style="width: 90px;" aria-label="Wybierz rok">
            <option v-for="year in years" :key="year" :value="year">{{ year }}</option>
          </select>
          <button 
            class="btn"
            :class="selectedPeriod === 'custom_month' ? 'btn-primary' : 'btn-outline-primary'"
            @click="fetchData('custom_month')"
            title="Filtruj wg wybranego miesiąca"
          >
            <Icon icon="mdi:filter-variant" /> Zastosuj Miesiąc
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
        <span class="visually-hidden">Ładowanie statystyk...</span>
      </div>
    </div>
    
    <div v-if="error" class="alert alert-danger">
      {{ error }}
    </div>

    <div v-if="stats && !loading">
      
      <div class="row g-4 mb-4">
        <div class="col-md-6 col-lg-3">
          <div class="card shadow-sm h-100">
            <div class="card-body d-flex align-items-center">
              <Icon icon="mdi:currency-usd" class="display-4 text-success me-3" />
              <div>
                <h6 class="card-subtitle text-muted">
                  Wartość Zam. <small class="d-block">{{ activeFilterText }}</small>
                </h6>
                <h2 class="card-title mb-0">
                  {{ stats.summary.total_revenue.toFixed(2) }} zł
                </h2>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6 col-lg-3">
          <div class="card shadow-sm h-100">
            <div class="card-body d-flex align-items-center">
              <Icon icon="mdi:package-variant-closed" class="display-4 text-primary me-3" />
              <div>
                <h6 class="card-subtitle text-muted">
                  Zamówienia <small class="d-block">{{ activeFilterText }}</small>
                </h6>
                <h2 class="card-title mb-0">{{ stats.summary.total_orders }}</h2>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6 col-lg-3">
          <div class="card shadow-sm h-100">
            <div class="card-body d-flex align-items-center">
              <Icon icon="mdi:account-group-outline" class="display-4 text-info me-3" />
              <div>
                <h6 class="card-subtitle text-muted">
                  Klienci <small class="d-block">(Globalnie)</small>
                </h6>
                <h2 class="card-title mb-0">{{ stats.summary.total_users }}</h2>
              </div>
            </div>
          </div>
        </div>
        <div class="col-md-6 col-lg-3">
          <div class="card shadow-sm h-100">
            <div class="card-body d-flex align-items-center">
              <Icon icon="mdi:tshirt-crew-outline" class="display-4 text-warning me-3" />
              <div>
                <h6 class="card-subtitle text-muted">
                  Produkty <small class="d-block">(Globalnie)</small>
                </h6>
                <h2 class="card-title mb-0">{{ stats.summary.total_products }}</h2>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row g-4 mb-4">
        <div class="col-lg-7">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">
                Top 5 Klientów <small class="text-muted">{{ activeFilterText }}</small>
              </h5>
              <div style="height: 350px;">
                <Bar 
                  v-if="stats.charts.top_clients.length > 0"
                  :data="topClientsData" 
                  :options="chartOptions" 
                />
                <p v-else class="text-muted text-center mt-5">Brak danych do wyświetlenia dla tego okresu.</p>
              </div>
            </div>
          </div>
        </div>
        <div class="col-lg-5">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title">
                Top 5 Produktów <small class="text-muted">{{ activeFilterText }}</small>
              </h5>
              <div style="height: 350px;">
                <Doughnut 
                  v-if="stats.charts.top_products.length > 0"
                  :data="topProductsData" 
                  :options="doughnutOptions" 
                />
                <p v-else class="text-muted text-center mt-5">Brak danych do wyświetlenia dla tego okresu.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="row g-4">
        <div class="col-12">
          <div class="card shadow-sm">
            <div class="card-body">
              <h5 class="card-title mb-3">Ostatnie zamówienia (globalnie)</h5>
              <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                  <thead class="table-light">
                    <tr>
                      <th>ID</th>
                      <th>Klient</th>
                      <th>Data</th>
                      <th>Status</th>
                      <th class="text-end">Ilość pozycji</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="latestOrders.length === 0">
                      <td colspan="5" class="text-center text-muted">Brak ostatnich zamówień.</td>
                    </tr>
                    <tr v-for="order in latestOrders" :key="order.id">
                      <th>#{{ order.id }}</th>
                      <td>{{ order.user_info.username }}</td>
                      <td>{{ formatDate(order.created_at) }}</td>
                      <td>
                        <span class="badge fs-6" :class="getStatusClass(order.status)">
                          {{ formatStatus(order.status) }}
                        </span>
                      </td>
                      <td class="text-end">{{ order.items.length }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}
.card-subtitle {
  color: var(--bs-secondary-color);
}
</style>