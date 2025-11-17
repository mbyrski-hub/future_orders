<script setup>
import { onMounted, onUnmounted, ref, inject, computed } from 'vue';
import { useUserStore } from '@/stores/userStore';
import { useProductStore } from '@/stores/productStore';
import { storeToRefs } from 'pinia';
import { Modal } from 'bootstrap';
import { Icon } from '@iconify/vue';

const $swal = inject('$swal');
const userStore = useUserStore();
const { users, loading, error: storeError, currentUserProducts } = storeToRefs(userStore);
const productStore = useProductStore();
const { products: allProducts, loading: productsLoading } = storeToRefs(productStore);

const userModalElement = ref(null);
let bsUserModal = null;
const deleteModalElement = ref(null);
let bsDeleteModal = null;
const assignModalElement = ref(null);
let bsAssignModal = null; 
const editMode = ref(false);

onMounted(() => {
  userStore.fetchUsers();
  if (userModalElement.value) bsUserModal = new Modal(userModalElement.value);
  if (deleteModalElement.value) bsDeleteModal = new Modal(deleteModalElement.value);
  if (assignModalElement.value) bsAssignModal = new Modal(assignModalElement.value);
});

onUnmounted(() => {
  bsUserModal?.dispose();
  bsDeleteModal?.dispose();
  bsAssignModal?.dispose();
});

// --- ZMIANA: Dodano nowe pola do formularza ---
const getInitialFormData = () => ({
  id: null,
  username: '',
  email: '',
  password: '',
  role: 'user',
  first_name: '', // <-- DODANO
  last_name: '',  // <-- DODANO
  address: ''     // <-- DODANO
});

const formData = ref(getInitialFormData());
const roles = ['user', 'admin', 'shipping', 'power_user'];

const openAddModal = () => {
  editMode.value = false;
  formData.value = getInitialFormData();
  bsUserModal.show();
};

const openEditModal = (user) => {
  editMode.value = true;
  formData.value = {
    id: user.id,
    username: user.username,
    email: user.email,
    password: '',
    role: user.role,
    first_name: user.first_name || '', // <-- DODANO
    last_name: user.last_name || '',   // <-- DODANO
    address: user.address || ''        // <-- DODANO
  };
  bsUserModal.show();
};

const handleSubmit = async () => {
  loading.value = true;
  
  try {
    const dataToSend = { ...formData.value };
    
    if (editMode.value && !dataToSend.password) {
      delete dataToSend.password;
    } else if (!editMode.value && !dataToSend.password) {
      throw new Error("Hasło jest wymagane przy tworzeniu użytkownika.");
    }
    
    if (editMode.value) {
      await userStore.updateUser(dataToSend.id, dataToSend);
    } else {
      await userStore.createUser(dataToSend);
    }
    
    bsUserModal.hide();
    
    $swal.fire({
      icon: 'success',
      title: 'Zapisano!',
      text: `Użytkownik "${dataToSend.username}" został zapisany.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2000
    });
    
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd zapisu',
      text: err.message || "Wystąpił nieoczekiwany błąd."
    });
  } finally {
    loading.value = false;
  }
};

const userToDelete = ref(null);
const openDeleteModal = (user) => {
  userToDelete.value = user;
  bsDeleteModal.show();
};
const handleDeleteConfirm = async () => {
  if (!userToDelete.value) return;
  loading.value = true;
  try {
    const username = userToDelete.value.username;
    await userStore.deleteUser(userToDelete.value.id);
    bsDeleteModal.hide();
    $swal.fire({
      icon: 'success',
      title: 'Usunięto!',
      text: `Użytkownik "${username}" został usunięty.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2000
    });
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd',
      text: err.message || 'Błąd podczas usuwania użytkownika.'
    });
    bsDeleteModal.hide();
  } finally {
    userToDelete.value = null;
    loading.value = false;
  }
};

const userToAssign = ref(null);
const selectedProductIds = ref([]);
const assignLoading = ref(false);
const openAssignModal = async (user) => {
  userToAssign.value = user;
  assignLoading.value = true;
  try {
    if (allProducts.value.length === 0) {
      await productStore.fetchProducts();
    }
    await userStore.fetchUserProducts(user.id);
    selectedProductIds.value = currentUserProducts.value.slice();
    bsAssignModal.show();
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd wczytywania',
      text: err.message || 'Nie udało się wczytać danych.'
    });
  } finally {
    assignLoading.value = false;
  }
};
const handleAssignSubmit = async () => {
  if (!userToAssign.value) return;
  assignLoading.value = true;
  try {
    await userStore.updateUserProducts(userToAssign.value.id, selectedProductIds.value);
    bsAssignModal.hide();
    $swal.fire({
      icon: 'success',
      title: 'Zapisano!',
      text: `Zaktualizowano listę produktów dla ${userToAssign.value.username}.`,
      toast: true,
      position: 'top-end',
      showConfirmButton: false,
      timer: 2000
    });
  } catch (err) {
    $swal.fire({
      icon: 'error',
      title: 'Błąd zapisu',
      text: err.message || 'Nie udało się zapisać przypisań.'
    });
  } finally {
    assignLoading.value = false;
  }
};
</script>

<template>
  <div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Zarządzanie Użytkownikami</h1>
    <button class="btn btn-primary" @click="openAddModal">
      <Icon icon="mdi:account-plus-outline" class="me-1" />
      Dodaj Użytkownika
    </button>
  </div>

  <div v-if="loading && users.length === 0" class="text-center">
    <div class="spinner-border" role="status"></div>
  </div>
  <div v-if="storeError" class="alert alert-danger">
    {{ storeError }}
  </div>

  <div v-if="!loading || users.length > 0" class="card shadow-sm">
    <div class="card-body">
      <table class="table table-hover align-middle">
        <thead class="table-light">
          <tr>
            <th scope="col">Nazwa użytkownika</th>
            <th scope="col">Imię i Nazwisko</th>
            <th scope="col">Email</th>
            <th scope="col">Rola</th>
            <th scope="col" class="text-end">Akcje</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>
              <strong>{{ user.username }}</strong>
              <small class="d-block text-muted">ID: {{ user.id }}</small>
            </td>
            <td>
              {{ user.first_name }} {{ user.last_name }}
              <small v.if="user.address" class="d-block text-muted">{{ user.address }}</small>
            </td>
            <td>{{ user.email }}</td>
            <td>
              <span class="badge" :class="{
                'bg-primary': user.role === 'admin',
                'bg-warning text-dark': user.role === 'power_user',
                'bg-secondary': user.role === 'user',
                'bg-info': user.role === 'shipping'
              }">{{ user.role }}</span>
            </td>
            <td class="text-end">
              <button 
                class="btn btn-sm btn-outline-info me-2" 
                @click="openAssignModal(user)"
                title="Przypisz produkty"
                :disabled="user.role !== 'user'" 
              >
                <Icon icon="mdi:package-variant-closed-plus" />
              </button>
              <button class="btn btn-sm btn-outline-secondary me-2" @click="openEditModal(user)">
                <Icon icon="mdi:account-edit-outline" /> Edytuj
              </button>
              <button class="btn btn-sm btn-outline-danger" @click="openDeleteModal(user)">
                <Icon icon="mdi:trash-can-outline" /> Usuń
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div v-if="!loading && users.length === 0 && !storeError" class="alert alert-info">
    Nie znaleziono żadnych użytkowników. Dodaj pierwszego!
  </div>

  <div class="modal fade" id="userModal" ref="userModalElement" tabindex="-1" aria-labelledby="userModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg"> <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="userModalLabel">
            {{ editMode ? 'Edytuj Użytkownika' : 'Nowy Użytkownik' }}
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        
        <form @submit.prevent="handleSubmit">
          <div class="modal-body">
            
            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="username" class="form-label">Nazwa użytkownika (Login) <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" id="username" v-model="formData.username" required>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="email" class="form-label">Email <span class="text-danger">*</span></label>
                  <input type="email" class="form-control" id="email" v-model="formData.email" required>
                </div>
              </div>
            </div>

            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="password" class="form-label">Hasło <span v-if="!editMode" class="text-danger">*</span></label>
                  <input type="password" class="form-control" id="password" v-model="formData.password" :required="!editMode">
                  <div class="form-text" v-if="editMode">Wypełnij tylko jeśli chcesz zmienić hasło.</div>
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="role" class="form-label">Rola <span class="text-danger">*</span></label>
                  <select class="form-select" id="role" v-model="formData.role">
                    <option v-for="role in roles" :key="role" :value="role">{{ role }}</option>
                  </select>
                </div>
              </div>
            </div>

            <hr>
            <p class="text-muted">Pola opcjonalne:</p>

            <div class="row">
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="first_name" class="form-label">Imię</label>
                  <input type="text" class="form-control" id="first_name" v-model="formData.first_name">
                </div>
              </div>
              <div class="col-md-6">
                <div class="mb-3">
                  <label for="last_name" class="form-label">Nazwisko</label>
                  <input type="text" class="form-control" id="last_name" v-model="formData.last_name">
                </div>
              </div>
            </div>
            
            <div class="mb-3">
              <label for="address" class="form-label">Adres</label>
              <textarea class="form-control" id="address" rows="2" v-model="formData.address"></textarea>
            </div>

          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
            <button type="submit" class="btn btn-primary" :disabled="loading">
              <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              Zapisz
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>

  <div class="modal fade" id="deleteConfirmModal" ref="deleteModalElement" tabindex="-1" aria-labelledby="deleteModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="deleteModalLabel">Potwierdź Usunięcie</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          Czy na pewno chcesz usunąć użytkownika: 
          <strong>{{ userToDelete?.username }}</strong>?
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
          <button type="button" class="btn btn-danger" @click="handleDeleteConfirm" :disabled="loading">
            {{ loading ? 'Usuwanie...' : 'Usuń' }}
          </button>
        </div>
      </div>
    </div>
  </div>

  <div class="modal fade" id="assignModal" ref="assignModalElement" tabindex="-1" aria-labelledby="assignModalLabel" aria-hidden="true">
    <div class="modal-dialog modal-lg">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="assignModalLabel">
            Przypisz produkty dla: <strong>{{ userToAssign?.username }}</strong>
          </h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <form @submit.prevent="handleAssignSubmit">
          <div class="modal-body">
            <div v-if="assignLoading || productsLoading" class="text-center">
              <div class="spinner-border" role="status"></div>
            </div>
            <div v-if="!assignLoading && !productsLoading && allProducts.length === 0" class="alert alert-warning">
              Nie zdefiniowano jeszcze żadnych produktów w systemie. Najpierw dodaj produkty.
            </div>
            <div v-if="!assignLoading && !productsLoading && allProducts.length > 0">
              <p>Zaznacz produkty, które ten klient będzie mógł zamawiać.</p>
              <div v-for="product in allProducts" :key="product.id" class="form-check">
                <input 
                  class="form-check-input" 
                  type="checkbox" 
                  :value="product.id" 
                  :id="'product-check-' + product.id"
                  v-model="selectedProductIds"
                >
                <label class="form-check-label" :for="'product-check-' + product.id">
                  <strong>{{ product.name }}</strong> 
                  <small class="text-muted">({{ product.variants.length }} wariantów)</small>
                </label>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Anuluj</button>
            <button type="submit" class="btn btn-primary" :disabled="assignLoading || productsLoading">
              <span v-if="assignLoading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
              Zapisz przypisania
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
  
</template>

<style scoped>
.btn .iconify {
  vertical-align: middle;
  margin-bottom: 0.1em;
}
</style>