// /frontend/src/stores/userStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';

export const useUserStore = defineStore('users', () => {
    const users = ref([]);
    const loading = ref(false);
    const error = ref(null);
    const currentUserProducts = ref([]);

    async function fetchUsers() {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/users');
            users.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać użytkowników.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

    async function createUser(userData) {
        // userData = { username, email, password, role }
        try {
            const response = await apiClient.post('/users', userData);
            users.value.push(response.data);
        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || 'Błąd podczas tworzenia użytkownika.');
        }
    }

    async function updateUser(userId, userData) {
        // userData = { username?, email?, password?, role? }
        // Hasło jest opcjonalne, wysyłaj je tylko jeśli jest zmieniane
        try {
            const response = await apiClient.put(`/users/${userId}`, userData);
            
            const index = users.value.findIndex(u => u.id === userId);
            if (index !== -1) {
                users.value[index] = response.data;
            }
        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || 'Błąd podczas aktualizacji użytkownika.');
        }
    }

    async function deleteUser(userId) {
        try {
            await apiClient.delete(`/users/${userId}`);
            users.value = users.value.filter(u => u.id !== userId);
        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || 'Błąd podczas usuwania użytkownika.');
        }
    }

// NOWA FUNKCJA
    async function fetchUserProducts(userId) {
        // Nie ustawiamy globalnego 'loading', bo to będzie działo się w modalu
        try {
            const response = await apiClient.get(`/users/${userId}/products`);
            currentUserProducts.value = response.data; // Oczekujemy listy ID, np. [1, 5]
        } catch (err) {
            console.error(err);
            throw new Error('Nie udało się pobrać przypisanych produktów.');
        }
    }

    // NOWA FUNKCJA
    async function updateUserProducts(userId, productIds) {
        // productIds to będzie lista ID, np. [1, 5, 12]
        try {
            const response = await apiClient.put(`/users/${userId}/products`, {
                product_ids: productIds 
            });
            currentUserProducts.value = response.data;
        } catch (err) {
            console.error(err.response?.data);
            throw new Error(err.response?.data?.msg || 'Błąd podczas aktualizacji produktów.');
        }
    }

    // Zaktualizuj 'return' na końcu pliku
    return { 
        users, loading, error, 
        fetchUsers, createUser, updateUser, deleteUser,
        currentUserProducts, fetchUserProducts, updateUserProducts // DODAJ NOWE
    };
});