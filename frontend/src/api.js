// /frontend/src/api.js
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:5000/api', // Nasz bazowy URL API
    headers: {
        'Content-Type': 'application/json'
    }
});

// To jest "Interceptor" - funkcja, która przechwytuje KAŻDE zapytanie
// zanim zostanie ono wysłane.
apiClient.interceptors.request.use(
    (config) => {
        // Używamy 'authStore' poza komponentem Vue, 
        // ale musimy ją zainicjować wewnątrz interceptora
        const authStore = useAuthStore(); 
        const token = authStore.token; // Pobieramy token ze store'a

        if (token) {
            // Jeśli token istnieje, dołącz go do nagłówka Authorization
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

export default apiClient;