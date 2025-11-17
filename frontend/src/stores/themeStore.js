// /frontend/src/stores/themeStore.js
import { defineStore } from 'pinia';
import { ref, watchEffect } from 'vue';

export const useThemeStore = defineStore('theme', () => {
    // Wczytaj motyw z localStorage lub użyj 'light' jako domyślny
    const theme = ref(localStorage.getItem('theme') || 'light');

    function setTheme(newTheme) {
        theme.value = newTheme;
        localStorage.setItem('theme', newTheme);
    }

    function toggleTheme() {
        setTheme(theme.value === 'light' ? 'dark' : 'light');
    }

    // Ten 'watchEffect' to magia.
    // Będzie automatycznie uruchamiany, gdy 'theme.value' się zmieni.
    // Ustawia atrybut 'data-bs-theme' na głównym elemencie <html>,
    // co mówi Bootstrapowi, aby zmienił motyw.
    watchEffect(() => {
        document.documentElement.setAttribute('data-bs-theme', theme.value);
    });

    return { theme, toggleTheme };
});