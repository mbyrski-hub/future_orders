// /frontend/src/stores/productStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api'; // Używamy naszego centralnego klienta!

export const useProductStore = defineStore('products', () => {
    const products = ref([]); // Lista produktów
    const loading = ref(false); // Flaga ładowania
    const error = ref(null); // Przechowywanie błędów

    // --- AKCJE ---

    // Pobierz wszystkie produkty
    async function fetchProducts() {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/products');
            products.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać produktów.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

    // Stwórz nowy produkt
    async function createProduct(productData) {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.post('/products', productData);
            // Dodaj nowy produkt do naszej listy w store
            products.value.push(response.data);
            
        } catch (err) {
            error.value = 'Błąd podczas tworzenia produktu.';
            console.error(err.response?.data);
            // Przekaż błąd dalej, aby formularz wiedział
            throw new Error(err.response?.data?.msg || error.value);
        } finally {
            loading.value = false;
        }
    }
    
    // Zaktualizuj produkt
    async function updateProduct(productId, productData) {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.put(`/products/${productId}`, productData);
            
            // Znajdź indeks produktu w tablicy
            const index = products.value.findIndex(p => p.id === productId);
            if (index !== -1) {
                // Zaktualizuj produkt w liście
                products.value[index] = response.data;
            }
            
        } catch (err) {
            error.value = 'Błąd podczas aktualizacji produktu.';
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || error.value);
        } finally {
            loading.value = false;
        }
    }

    // Usuń produkt
    async function deleteProduct(productId) {
        loading.value = true;
        error.value = null;
        try {
            await apiClient.delete(`/products/${productId}`);
            
            // Usuń produkt z listy w store
            products.value = products.value.filter(p => p.id !== productId);
            
        } catch (err) {
            error.value = 'Błąd podczas usuwania produktu.';
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || error.value);
        } finally {
            loading.value = false;
        }
    }

    return { products, loading, error, fetchProducts, createProduct, updateProduct, deleteProduct };
});