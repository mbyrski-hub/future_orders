// /frontend/src/stores/auth.js
import { defineStore } from 'pinia'
import apiClient from '@/api'
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notificationStore';
import Swal from 'sweetalert2'; // <-- 1. DODAJ IMPORT (do bloku 'catch')

// Definiujemy bazowy URL naszego API
const API_URL = 'http://127.0.0.1:5000/api'

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || null)
    const user = ref(JSON.parse(localStorage.getItem('user')) || null)
    
    const router = useRouter()

    async function login(username, password) {
        try {
            const response = await apiClient.post(`/login`, { 
                username: username,
                password: password
            });
            
            const data = response.data;
            token.value = data.access_token;
            
            user.value = data.user; 
            localStorage.setItem('token', token.value);
            localStorage.setItem('user', JSON.stringify(user.value));

            // --- 2. ZMIANA: Startujemy pętlę powiadomień ---
            const notificationStore = useNotificationStore();
            notificationStore.startPolling();
            // --- KONIEC ZMIANY ---

            // Natychmiastowe przekierowanie
            redirectToDashboard(user.value.role);

        } catch (error) {
            
            // --- 3. ZMIANA: Zastępujemy 'alert()' na 'Swal.fire()' ---
            if (error && error.response && error.response.data) {
                console.error("Błąd logowania (API):", error.response.data.msg);
                Swal.fire({
                    icon: 'error',
                    title: 'Błąd logowania',
                    text: error.response.data.msg
                });
            } else {
                console.error("Nieoczekiwany błąd podczas logowania:", error.message, error);
                Swal.fire({
                    icon: 'error',
                    title: 'Błąd krytyczny',
                    text: "Wystąpił nieoczekiwany błąd: " + error.message
                });
            }
            // --- KONIEC ZMIANY ---
        }
    }

    async function fetchUserProfile() {
      if (!token.value) {
        return;
      }
      try {
        const response = await apiClient.get('/me');
        user.value = response.data; 
        localStorage.setItem('user', JSON.stringify(user.value));

        // --- 4. ZMIANA: Startujemy pętlę przy odświeżeniu strony (F5) ---
        const notificationStore = useNotificationStore();
        notificationStore.startPolling();
        // --- KONIEC ZMIANY ---

      } catch (error) {
        console.error("Nie udało się pobrać profilu użytkownika:", error);
        logout();
      }
    }

    async function updateProfile(profileData) {
      try {
        const response = await apiClient.put('/me', profileData);
        user.value = response.data;
        localStorage.setItem('user', JSON.stringify(user.value));
      } catch (err) {
        console.error("Błąd aktualizacji profilu:", err.response?.data);
        throw new Error(err.response?.data?.msg || "Błąd serwera.");
      }
    }

    async function updatePassword(passwordData) {
      try {
        const response = await apiClient.put('/me/password', passwordData);
        return response.data;
      } catch (err) {
        console.error("Błąd zmiany hasła:", err.response?.data);
        throw new Error(err.response?.data?.msg || "Błąd serwera.");
      }
    }

    function logout() {
        // --- 5. ZMIANA: Zatrzymujemy pętlę przy wylogowaniu ---
        const notificationStore = useNotificationStore();
        notificationStore.stopPolling();
        // --- KONIEC ZMIANY ---

        token.value = null;
        user.value = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        router.push('/login'); // Używamy 'router'
    }

    // --- POPRAWIONA FUNKCJA (bez zmian w stosunku do Twojego kodu) ---
    function redirectToDashboard(role) {
        if (role === 'admin') {
            router.push('/admin/dashboard');
        } else if (role === 'user') {
            router.push('/dashboard');
        } else if (role === 'shipping') {
            router.push('/shipping');
        } else if (role === 'power_user') {
            router.push('/admin/dashboard');
        } else {
            router.push('/');
        }
    }

    return { token, user, login, logout, redirectToDashboard,fetchUserProfile, updateProfile, updatePassword  }
});