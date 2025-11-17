// /frontend/public/service-worker.js

console.log("Service Worker załadowany.");

// Listener dla zdarzenia PUSH
self.addEventListener('push', event => {
  console.log('Otrzymano powiadomienie PUSH');
  
  let data;
  try {
    data = event.data.json();
  } catch (e) {
    data = { title: 'Nowa wiadomość', body: event.data.text() };
  }

  const title = data.title || 'Nowe powiadomienie';
  const options = {
    body: data.body || 'Masz nową wiadomość.',
    icon: '/icons/icon-192x192.png', // Ikona PWA
    badge: '/icons/icon-192x192.png',
    data: {
      url: data.data?.url || '/' // URL do otwarcia po kliknięciu
    }
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Listener dla kliknięcia w powiadomienie
self.addEventListener('notificationclick', event => {
  event.notification.close(); // Zamknij powiadomienie

  const urlToOpen = event.notification.data.url || '/';

  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      // Jeśli aplikacja jest już otwarta w zakładce, przejdź do niej
      for (let i = 0; i < clientList.length; i++) {
        let client = clientList[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      // Jeśli nie, otwórz nową zakładkę
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});