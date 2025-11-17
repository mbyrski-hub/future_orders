// /frontend/src/stores/clientStore.js
import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import apiClient from '@/api';
import Swal from 'sweetalert2'; // Importujemy, aby $swal nie był potrzebny

export const useClientStore = defineStore('client', () => {
    // Lista produktów dostępnych dla klienta
    const products = ref([]);
    
    // Koszyk
    const cart = ref([]); // Przechowuje { variant_id, product_id, name, size, quantity }
    const orders = ref([]);
    const loading = ref(false);
    const error = ref(null);

    // --- Akcje dla Produktów ---
    async function fetchMyProducts() {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/my-products');
            products.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać Twoich produktów.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }
    
    // --- Akcje dla Zamówień ---
    async function createOrder(notes) {
        const payload = {
            items: cart.value.map(item => ({
                variant_id: item.variant_id,
                quantity: item.quantity
            })),
            notes: notes 
        };
        
        try {
            const response = await apiClient.post('/orders', payload); 
            clearCart();
            return response.data; 
        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || "Błąd serwera podczas składania zamówienia.");
        }
    }

    async function fetchMyOrders() {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/my-orders');
            orders.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać historii zamówień.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

    // --- Akcje dla Koszyka ---
    function addToCart(product, variant, quantity) {
        const qtyToAdd = parseInt(quantity);
        if (isNaN(qtyToAdd) || qtyToAdd <= 0) {
            console.error("Próbowano dodać nieprawidłową ilość");
            return;
        }
        const existingItem = cart.value.find(item => item.variant_id === variant.id);
        
        if (existingItem) {
            existingItem.quantity += qtyToAdd;
        } else {
            cart.value.push({
                product_id: product.id,
                variant_id: variant.id,
                name: product.name,
                size: variant.size,
                price: variant.price,
                quantity: qtyToAdd 
            });
        }
        console.log("Koszyk:", cart.value);
    }
    
    function removeFromCart(variant_id) {
        cart.value = cart.value.filter(item => item.variant_id !== variant_id);
    }
    
    function clearCart() {
        cart.value = [];
    }
    
    // --- Akcje dla PDF ---
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

    // --- NOWA FUNKCJA DO POBIERANIA HISTORII WYSYŁEK ---
    async function fetchOrderShipments(order) {
        // Funkcja pomocnicza do dołączania danych do obiektu zamówienia
        // Sprawdzamy, czy dane nie zostały już pobrane
        if (order.shipments) {
            return;
        }

        order.shipmentsLoading = true; // Dodajemy flagę ładowania do obiektu
        try {
            const response = await apiClient.get(`/orders/${order.id}/shipments`);
            // Dołączamy pobraną historię bezpośrednio do obiektu zamówienia
            order.shipments = response.data; 
        } catch (err) {
            console.error("Błąd pobierania historii wysyłek:", err);
            // Wyświetlimy błąd w komponencie
            Swal.fire({
                icon: 'error',
                title: 'Błąd',
                text: 'Nie udało się pobrać historii wysyłek dla tego zamówienia.'
            });
        } finally {
            order.shipmentsLoading = false;
        }
    }
    
    // --- Gettery (Computed) ---
    const cartItemCount = computed(() => {
        return cart.value.reduce((total, item) => total + item.quantity, 0);
    });

    return { 
        products, cart, orders, loading, error,
        fetchMyProducts, 
        fetchMyOrders,
        createOrder, 
        addToCart, 
        removeFromCart, 
        clearCart,
        cartItemCount,
        downloadOrderPdf,
        fetchOrderShipments // <-- DODANO NOWĄ FUNKCJĘ
    };
});