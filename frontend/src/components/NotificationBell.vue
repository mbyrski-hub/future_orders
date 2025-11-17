<script setup>
import { useNotificationStore } from '@/stores/notificationStore';
import { storeToRefs } from 'pinia';
import { Icon } from '@iconify/vue';
import { useRouter } from 'vue-router';

const notificationStore = useNotificationStore();
const { notifications, unreadCount } = storeToRefs(notificationStore);
const router = useRouter();

// Funkcja wywoływana po otwarciu dzwonka
const onDropdownOpen = () => {
  // Dajmy API chwilę na zapisanie, zanim odświeżymy
  setTimeout(() => {
    notificationStore.markAllAsRead();
  }, 2000); // Oznacz jako przeczytane po 2 sekundach
};

// Funkcja do formatowania daty (jak dawno temu)
const timeAgo = (dateString) => {
  const date = new Date(dateString);
  const seconds = Math.floor((new Date() - date) / 1000);
  
  let interval = seconds / 31536000;
  if (interval > 1) return Math.floor(interval) + " lat temu";
  interval = seconds / 2592000;
  if (interval > 1) return Math.floor(interval) + " mies. temu";
  interval = seconds / 86400;
  if (interval > 1) return Math.floor(interval) + " dni temu";
  interval = seconds / 3600;
  if (interval > 1) return Math.floor(interval) + " godz. temu";
  interval = seconds / 60;
  if (interval > 1) return Math.floor(interval) + " min. temu";
  return "przed chwilą";
};

// Funkcja kliknięcia w powiadomienie
const handleNotificationClick = (notification) => {
  if (notification.link_url) {
    // Użyj routera, aby przenieść do linku
    router.push(notification.link_url);
  }
};
</script>

<template>
  <div class="dropdown me-2">
    <button 
      class="btn btn-outline-secondary" 
      type="button" 
      data-bs-toggle="dropdown" 
      aria-expanded="false"
      @click="onDropdownOpen"
      title="Powiadomienia"
    >
      <Icon icon="mdi:bell-outline" class="fs-5" />
      <span 
        v-if="unreadCount > 0" 
        class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger"
      >
        {{ unreadCount }}
        <span class="visually-hidden">nieprzeczytane powiadomienia</span>
      </span>
    </button>
    
    <ul class="dropdown-menu dropdown-menu-end shadow-lg" style="width: 350px;">
      <li class="px-3 py-2 d-flex justify-content-between align-items-center">
        <h6 class="mb-0">Powiadomienia</h6>
      </li>
      <li><hr class="dropdown-divider"></li>
      
      <div class="notification-list-container">
        <li v-if="notifications.length === 0" class="px-3 py-2 text-center text-muted">
          <small>Brak nowych powiadomień.</small>
        </li>
        
        <li v-for="n in notifications" :key="n.id">
          <a 
            class="dropdown-item notification-item" 
            :class="{ 'is-unread': !n.is_read }"
            href="#"
            @click.prevent="handleNotificationClick(n)"
          >
            <div class="d-flex justify-content-between">
              <strong class="text-truncate">{{ n.title }}</strong>
              <small class="text-muted ms-2 flex-shrink-0">{{ timeAgo(n.created_at) }}</small>
            </div>
            <p class="small mb-0 text-wrap">{{ n.body }}</p>
          </a>
        </li>
      </div>

      <li><hr class="dropdown-divider"></li>
      <li class="text-center py-1">
        <small class="text-muted">Wyświetlono 20 ostatnich</small>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.btn .iconify {
  vertical-align: middle;
  margin-bottom: .1em;
}
/* Upewnij się, że dzwonek ma relatywną pozycję dla kropki */
.btn {
  position: relative;
}

.notification-list-container {
  max-height: 400px;
  overflow-y: auto;
}

.notification-item {
  white-space: normal; /* Pozwól na zawijanie tekstu */
}

/* Podświetl nieprzeczytane */
.notification-item.is-unread {
  background-color: var(--bs-primary-bg-subtle);
}
.notification-item.is-unread strong {
  font-weight: 900;
}
</style>