// /frontend/src/stores/notificationStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';

export const useNotificationStore = defineStore('notification', () => {
    const notifications = ref([]);
    const unreadCount = ref(0);
    const loading = ref(false);
    
    let pollInterval = null; // Zmienna do przechowywania interwału

    // Pobiera powiadomienia z API
    async function fetchNotifications() {
        loading.value = true;
        try {
            const response = await apiClient.get('/me/notifications');
            notifications.value = response.data.notifications;
            unreadCount.value = response.data.unread_count;
        } catch (error) {
            console.error("Nie udało się pobrać powiadomień:", error);
        } finally {
            loading.value = false;
        }
    }

    // Oznacza wszystkie jako przeczytane
    async function markAllAsRead() {
        if (unreadCount.value === 0) return; // Nie rób nic, jeśli nie ma co czytać
        
        try {
            await apiClient.post('/me/notifications/mark-read');
            notifications.value.forEach(n => n.is_read = true);
            unreadCount.value = 0;
        } catch (error) {
            console.error("Nie udało się oznaczyć powiadomień jako przeczytane:", error);
        }
    }

    // --- Logika odpytywania (Polling) ---

    // Startuje pętlę, która co 30 sekund sprawdza powiadomienia
    function startPolling() {
        // Upewnij się, że nie ma już aktywnej pętli
        stopPolling(); 
        
        console.log("Startuję odpytywanie o powiadomienia...");
        // Pobierz od razu przy starcie
        fetchNotifications();
        
        // Ustaw pętlę
        pollInterval = setInterval(() => {
            fetchNotifications();
        }, 30000); // 30 sekund
    }

    // Zatrzymuje pętlę (np. przy wylogowaniu)
    function stopPolling() {
        if (pollInterval) {
            console.log("Zatrzymuję odpytywanie o powiadomienia.");
            clearInterval(pollInterval);
            pollInterval = null;
        }
        // Wyczyść dane po wylogowaniu
        notifications.value = [];
        unreadCount.value = 0;
    }

    return { 
        notifications, 
        unreadCount, 
        loading,
        fetchNotifications,
        markAllAsRead,
        startPolling,
        stopPolling
    };
});