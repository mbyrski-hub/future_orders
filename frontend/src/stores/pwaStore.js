// /frontend/src/stores/pwaStore.js
import { defineStore } from 'pinia';
import { ref } from 'vue';
import apiClient from '@/api';

// Konwerter klucza VAPID (standardowa funkcja)
function urlBase64ToUint8Array(base64String) {
  const padding = '='.repeat((4 - base64String.length % 4) % 4);
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
  const rawData = window.atob(base64);
  const outputArray = new Uint8Array(rawData.length);
  for (let i = 0; i < rawData.length; ++i) {
    outputArray[i] = rawData.charCodeAt(i);
  }
  return outputArray;
}

export const usePwaStore = defineStore('pwa', () => {
  // Wklej tutaj swój KLUCZ PUBLICZNY wygenerowany w Kroku 2
  const VAPID_PUBLIC_KEY = 'BO-h0Xt2ZhYUgLqrxfI9iAwtDJI7Px2sPstn1ArhWOdnxIbgnPLA4PrXwlHMDNjEY5eqtgv1qY3M6TrKKezeZQM';

  const installPromptEvent = ref(null);
  const isNotificationPermissionGranted = ref(Notification.permission === 'granted');

  // Nasłuchuj na gotowość do instalacji PWA
  window.addEventListener('beforeinstallprompt', (event) => {
    event.preventDefault(); // Zapobiegaj automatycznemu pokazaniu
    installPromptEvent.value = event; // Zapisz event, aby użyć go później
    console.log("Gotowy do instalacji PWA (beforeinstallprompt).");
  });

  // Funkcja wywoływana przez nasz przycisk "Zainstaluj"
  function promptToInstall() {
    if (!installPromptEvent.value) {
      alert("Aplikacja nie może być zainstalowana (Twój browser może tego nie wspierać).");
      return;
    }
    installPromptEvent.value.prompt(); // Pokaż natywny dialog instalacji
  }

  // Funkcja wywoływana przez nasz przycisk "Włącz powiadomienia"
  async function subscribeToNotifications() {
    if (!('PushManager' in window)) {
      alert("Powiadomienia Push nie są wspierane w Twojej przeglądarce.");
      return;
    }
    
    try {
      const permission = await Notification.requestPermission();
      if (permission === 'granted') {
        isNotificationPermissionGranted.value = true;
        console.log("Zgoda na powiadomienia uzyskana.");
        
        const swRegistration = await navigator.serviceWorker.ready;
        const subscription = await swRegistration.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(VAPID_PUBLIC_KEY)
        });

        console.log("Uzyskano subskrypcję:", subscription);
        
        // Wyślij subskrypcję do naszego API
        await apiClient.post('/subscribe-push', subscription.toJSON());
        console.log("Subskrypcja wysłana do backendu.");
        
      } else {
        isNotificationPermissionGranted.value = false;
        console.warn("Użytkownik odmówił zgody na powiadomienia.");
      }
    } catch (error) {
      console.error("Błąd podczas subskrypcji powiadomień:", error);
    }
  }

  return { 
    installPromptEvent, 
    isNotificationPermissionGranted,
    promptToInstall,
    subscribeToNotifications
  };
});