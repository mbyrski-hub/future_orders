<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { Modal } from 'bootstrap';
import { Icon } from '@iconify/vue';

// Ten komponent będzie zarządzany przez Bootstrapa
const modalElement = ref(null);
let bsModal = null;

onMounted(() => {
  if (modalElement.value) {
    bsModal = new Modal(modalElement.value);
  }
});

onUnmounted(() => {
  bsModal?.dispose();
});

// "Wystaw" funkcję 'open' na zewnątrz
const open = () => {
  bsModal.show();
};
defineExpose({
  open
});
</script>

<template>
  <Teleport to="body">
    <div class="modal fade" id="installPwaModal" ref="modalElement" tabindex="-1" aria-labelledby="installModalLabel" aria-hidden="true">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title" id="installModalLabel">
              <Icon icon="mdi:cellphone-arrow-down" class="me-1" />
              Instrukcja Aplikacji
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
          </div>
          <div class="modal-body">
            
            <h5 class="mb-3">
              <Icon icon="mdi:cellphone-arrow-down" />
              Instalacja Aplikacji na Telefonie
            </h5>
            <p>
              Naszą aplikację możesz zainstalować na ekranie głównym swojego telefonu, aby mieć do niej szybki dostęp, tak jak do zwykłej aplikacji.
            </p>
            <div class="row g-4">
              <div class="col-md-6">
                <h6>
                  <Icon icon="mdi:google-chrome" class="me-1" /> 
                  Android (Chrome)
                </h6>
                <ol class="list-group list-group-numbered list-group-flush small">
                  <li class="list-group-item">Otwórz stronę w przeglądarce Chrome.</li>
                  <li class="list-group-item">Naciśnij menu (trzy kropki) w rogu.</li>
                  <li class="list-group-item">Wybierz <strong>"Zainstaluj aplikację"</strong> lub <strong>"Dodaj do ekranu głównego"</strong>.</li>
                  <li class="list-group-item">Potwierdź, a ikona pojawi się na pulpicie.</li>
                </ol>
              </div>
              <div class="col-md-6">
                <h6>
                  <Icon icon="mdi:apple-safari" class="me-1" />
                  iOS / iPhone (Safari)
                </h6>
                <ol class="list-group list-group-numbered list-group-flush small">
                  <li class="list-group-item">Otwórz stronę w przeglądarce Safari.</li>
                  <li class="list-group-item">Naciśnij przycisk <strong>Udostępnij</strong> (kwadrat ze strzałką) na dolnym pasku.</li>
                  <li class="list-group-item">Przewiń listę w dół i wybierz <strong>"Dodaj do ekranu początkowego"</strong>.</li>
                  <li class="list-group-item">Potwierdź, a ikona pojawi się na pulpicie.</li>
                </ol>
              </div>
            </div>

            <hr class="my-4">

            <h5 class="mb-3">
              <Icon icon="mdi:bell-ring-outline" />
              Jak włączyć powiadomienia?
            </h5>
            <p>
              Jeśli przypadkowo zablokowałeś powiadomienia, możesz je włączyć ręcznie w ustawieniach przeglądarki, aby otrzymywać informacje o statusie swoich zamówień.
            </p>
            <div class="row g-4">
              <div class="col-md-6">
                <h6>
                  <Icon icon="mdi:google-chrome" class="me-1" /> 
                  Komputer (Chrome/Edge/Firefox)
                </h6>
                <ol class="list-group list-group-numbered list-group-flush small">
                  <li class="list-group-item">Kliknij ikonę <strong>kłódki</strong> (<Icon icon="mdi:lock-outline" />) obok adresu URL w pasku adresu.</li>
                  <li class="list-group-item">Znajdź opcję <strong>"Powiadomienia"</strong>.</li>
                  <li class="list-group-item">Zmień ustawienie z "Blokuj" na <strong>"Zezwalaj"</strong>.</li>
                </ol>
              </div>
              <div class="col-md-6">
                <h6>
                  <Icon icon="mdi:cellphone-cog" class="me-1" />
                  Telefon (Android/iOS)
                </h6>
                <ol class="list-group list-group-numbered list-group-flush small">
                  <li class="list-group-item">Wejdź w <strong>Ustawienia</strong> swojego telefonu.</li>
                  <li class="list-group-item">Przejdź do sekcji "Aplikacje" lub "Powiadomienia".</li>
                  <li class="list-group-item">Znajdź na liście swoją przeglądarkę (np. Chrome) lub zainstalowaną aplikację (Moje Zamowienia).</li>
                  <li class="list-group-item">Wejdź w jej "Uprawnienia" i włącz <strong>"Powiadomienia"</strong>.</li>
                </ol>
              </div>
            </div>
            </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Zamknij</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.iconify {
  vertical-align: middle;
  margin-bottom: 2px;
}
/* Poprawki stylistyczne dla listy w modalu */
.list-group-item {
  background-color: transparent;
  border-color: var(--bs-border-color-translucent);
  padding-left: 0.5rem;
}
</style>