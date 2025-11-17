// /frontend/src/stores/adminPushStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';

export const useAdminPushStore = defineStore('adminPush', () => {
    // Lista wszystkich subskrypcji
    const subscriptions = ref([]);
    const loading = ref(false);
    const error = ref(null);

    // Akcja do pobierania listy subskrypcji (do podglądu)
    async function fetchSubscriptions() {
        loading.value = true;
        error.value = null;
        try {
            const response = await apiClient.get('/admin/subscriptions');
            subscriptions.value = response.data;
        } catch (err) {
            error.value = 'Nie udało się pobrać listy subskrypcji.';
            console.error(err);
        } finally {
            loading.value = false;
        }
    }

    // Akcja do usuwania subskrypcji
    async function deleteSubscription(subscriptionId) {
        try {
            await apiClient.delete(`/admin/subscriptions/${subscriptionId}`);
            // Usuń subskrypcję z listy w store
            subscriptions.value = subscriptions.value.filter(sub => sub.id !== subscriptionId);
        } catch (err) {
            console.error('Błąd podczas usuwania subskrypcji:', err);
            // Przekaż błąd dalej, aby komponent mógł go wyświetlić
            throw new Error('Nie udało się usunąć subskrypcji.');
        }
    }

    // Akcja do wysyłania personalizowanego powiadomienia
    async function sendCustomPush(payload) {
        // payload to { title, body, user_id (opcjonalny) }
        try {
            const response = await apiClient.post('/admin/send-push', payload);
            return response.data; // Zwróć komunikat sukcesu, np. "Wysłano..."
        } catch (err) {
            console.error('Błąd podczas wysyłania powiadomienia:', err.response?.data);
            throw new Error(err.response?.data?.msg || 'Błąd serwera.');
        }
    }

    return { 
        subscriptions, loading, error,
        fetchSubscriptions,
        deleteSubscription,
        sendCustomPush
    };
});