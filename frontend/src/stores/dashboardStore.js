// /frontend/src/stores/dashboardStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';

export const useDashboardStore = defineStore('dashboard', () => {
    const stats = ref(null); 
    const latestOrders = ref([]);
    const loading = ref(false);
    const error = ref(null);

    // ZMIANA: fetchDashboardStats przyjmuje teraz obiekt 'params'
    async function fetchDashboardStats(params = {}) {
        loading.value = true;
        error.value = null;
        stats.value = null; // Zresetuj statystyki przed nowym pobraniem
        try {
            // Przekaż 'params' (start_date, end_date) do API
            const response = await apiClient.get('/admin/dashboard-stats', { params });
            stats.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać statystyk kokpitu.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

    async function fetchLatestOrders() {
        // Ta funkcja pozostaje bez zmian (zawsze pokazuje 5 ostatnich)
        try {
            const response = await apiClient.get('/admin/latest-orders');
            latestOrders.value = response.data;
        } catch (err) {
            console.error('Nie udało się pobrać ostatnich zamówień:', err);
        }
    }

    return { 
        stats, 
        latestOrders,
        loading, 
        error, 
        fetchDashboardStats,
        fetchLatestOrders
    };
});