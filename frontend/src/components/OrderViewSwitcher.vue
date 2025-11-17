<script setup>
import { Icon } from '@iconify/vue';
import { RouterLink } from 'vue-router';
</script>

<template>
  <div class="d-flex justify-content-end mb-3">
    <div class="btn-group" role="group" aria-label="Przełącznik widoku zamówienia">
      <RouterLink 
        :to="{ name: 'client-products-grid' }" 
        class="btn btn-outline-primary" 
        active-class="active"
        title="Widok katalogu (siatka)"
      >
        <Icon icon="mdi:view-grid-outline" class="fs-4" />
        <span class="ms-1 d-none d-md-inline">Widok siatki</span>
      </RouterLink>
      <RouterLink 
        :to="{ name: 'client-products-table' }" 
        class="btn btn-outline-primary" 
        active-class="active"
        title="Szybkie zamówienie (tabela)"
      >
        <Icon icon="mdi:format-list-checks" class="fs-4" />
        <span class="ms-1 d-none d-md-inline">Szybkie zamówienie</span>
      </RouterLink>
    </div>
  </div>
</template>

<style scoped>
/* Poprawia wyrównanie ikon w przyciskach */
.btn .iconify { 
  vertical-align: middle; 
  margin-bottom: 0.1em; 
}

/* Bootstrap domyślnie nie zmienia koloru tekstu na biały
  w przyciskach 'outline' gdy są aktywne.
*/
.btn.active {
  color: white; 
}
</style>