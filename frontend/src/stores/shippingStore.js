// /frontend/src/stores/shippingStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';
import Swal from 'sweetalert2';

export const useShippingStore = defineStore('shipping', () => {
    const orders = ref([]);
    const statusCounts = ref(null);
    const loading = ref(false);
    const error = ref(null);

    // ZMIANA: Ta funkcja przyjmuje teraz parametry
    async function fetchAllOrders(params = {}) {
        loading.value = true;
        error.value = null;
        try {
            // 1. Pobierz listę zamówień (tak jak było)
            const response = await apiClient.get('/shipping/orders', { params });
            orders.value = response.data;
            
            // 2. JEDNOCZEŚNIE odśwież liczniki
            // (Nie czekamy na to, niech się dzieje w tle)
            fetchStatusCounts();
        } catch (err) {
            error.value = 'Nie udało się pobrać zamówień.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

// NOWA FUNKCJA DO POBIERANIA LICZNIKÓW
    async function fetchStatusCounts() {
        try {
            const response = await apiClient.get('/shipping/orders/counts');
            statusCounts.value = response.data;
        } catch (err) {
            console.error("Nie udało się pobrać liczników statusów:", err);
            // To nie jest krytyczne, nie ustawiamy globalnego błędu
        }
    }


    async function shipItems(orderId, itemsToShip) {
        try {
            const response = await apiClient.post(`/shipping/orders/${orderId}/ship`, {
                items: itemsToShip
            });
            const index = orders.value.findIndex(o => o.id === orderId);
            if (index !== -1) {
                orders.value[index] = response.data;
            }

            fetchStatusCounts();

        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || 'Wystąpił nieznany błąd serwera.');
        }
    }

    async function downloadOrderPdf(orderId) {
        try {
            const response = await apiClient.get(`/orders/${orderId}/pdf`, {
                responseType: 'blob'
            });
            const file = new Blob([response.data], { type: 'application/pdf' });
            const fileURL = URL.createObjectURL(file);
            window.open(fileURL);
        } catch (err) {
            console.error("Błąd podczas pobierania PDF:", err);
            throw new Error("Nie udało się pobrać pliku PDF.");
        }
    }
    
    async function fetchOrderShipments(order) {
        if (order.shipments) {
            return;
        }
        order.shipmentsLoading = true;
        try {
            const response = await apiClient.get(`/orders/${order.id}/shipments`);
            order.shipments = response.data;
        } catch (err) {
            console.error("Błąd pobierania historii wysyłek:", err);
            Swal.fire({
                icon: 'error',
                title: 'Błąd',
                text: 'Nie udało się pobrać historii wysyłek dla tego zamówienia.'
            });
        } finally {
            order.shipmentsLoading = false;
        }
    }
    
    // --- NOWA FUNKCJA DO LISTY ZBIORCZEJ ---
    async function generatePickingListPdf(orderIds) {
        if (!orderIds || orderIds.length === 0) {
            throw new Error("Nie wybrano żadnych zamówień.");
        }
        
        try {
            const response = await apiClient.post('/shipping/picking-list-pdf', 
                { order_ids: orderIds },
                { responseType: 'blob' } // Oczekujemy pliku PDF
            );
            
            const file = new Blob([response.data], { type: 'application/pdf' });
            const fileURL = URL.createObjectURL(file);
            window.open(fileURL); // Otwórz PDF w nowej karcie

        } catch (err) {
            // Backend zwraca błąd 404 jeśli nie ma nic do spakowania
            if (err.response && err.response.status === 404) {
                throw new Error(err.response.data.msg || "Brak pozycji do spakowania.");
            }
            console.error("Błąd podczas generowania listy do spakowania:", err);
            throw new Error("Nie udało się pobrać pliku PDF.");
        }
    }
    // --- KONIEC NOWEJ FUNKCJI ---


    return { 
        orders, 
        statusCounts, // <-- UPEWNIJ SIĘ, ŻE DODAŁEŚ TĘ LINIĘ
        loading, 
        error,
        fetchAllOrders,
        shipItems,
        downloadOrderPdf,
        fetchOrderShipments,
        generatePickingListPdf,
        fetchStatusCounts
    };
});