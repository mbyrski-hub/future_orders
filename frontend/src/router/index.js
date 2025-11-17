// /frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'

// Importy Admina
import AdminLayout from '@/layouts/AdminLayout.vue';
import AdminDashboard from '@/views/admin/AdminDashboard.vue';
import AdminProducts from '@/views/admin/AdminProducts.vue';
import AdminUsers from '@/views/admin/AdminUsers.vue';
import AdminOrders from '@/views/admin/AdminOrders.vue';
import AdminPush from '@/views/admin/AdminPush.vue';

// Importy Klienta
import UserLayout from '@/layouts/UserLayout.vue';
import ClientDashboard from '@/views/client/ClientDashboard.vue';
import ClientProducts from '@/views/client/ClientProducts.vue'; // Nasz widok siatki
import ClientQuickOrder from '@/views/client/ClientQuickOrder.vue'; // Nasz widok tabeli
// Plik ClientOrderChooser.vue można USUNĄĆ
import ClientOrders from '@/views/client/ClientOrders.vue';
import ClientCart from '@/views/client/ClientCart.vue';

// Importy Spedycji
import ShippingLayout from '@/layouts/ShippingLayout.vue';
import ShippingDashboard from '@/views/shipping/ShippingDashboard.vue';

// Importy Resetowania Hasła
import ForgotPassword from '@/views/ForgotPassword.vue';
import ResetPassword from '@/views/ResetPassword.vue';

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: HomeView 
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: ForgotPassword,
      meta: { guest: true }
    },
    {
      path: '/reset-password',
      name: 'reset-password',
      component: ResetPassword,
      meta: { guest: true }
    },
    {
        path: '/',
        redirect: '/login'
    },

    // --- Trasy Admina i Power Usera ---
    {
      path: '/admin',
      component: AdminLayout,
      meta: { requiresAuth: true, roles: ['admin', 'power_user'] }, 
      children: [
        { path: 'dashboard', name: 'admin-dashboard', component: AdminDashboard },
        { path: 'orders', name: 'admin-orders', component: AdminOrders },
        { path: 'products', name: 'admin-products', component: AdminProducts, meta: { role: 'admin' } },
        { path: 'users', name: 'admin-users', component: AdminUsers, meta: { role: 'admin' } },
        { path: 'push', name: 'admin-push', component: AdminPush, meta: { role: 'admin' } }
      ]
    },

    // --- Trasy Klienta (rola 'user') ---
    {
      path: '/dashboard',
      component: UserLayout,
      meta: { requiresAuth: true, role: 'user' },
      children: [
        { path: '', name: 'client-dashboard', component: ClientDashboard },
        
        // --- ZMIENIONA STRUKTURA ZAMAWIANIA ---
        // 1. Usunęliśmy 'client-order-chooser'
        // 2. Link w menu będzie teraz prowadził do 'client-products-grid'
        { 
          path: 'products-grid', // Widok siatki (katalog)
          name: 'client-products-grid', 
          component: ClientProducts 
        },
        { 
          path: 'products-table', // Widok tabeli (szybkie zam.)
          name: 'client-products-table', 
          component: ClientQuickOrder 
        },
        // --- KONIEC ZMIAN ---
        
        { path: 'orders', name: 'client-orders', component: ClientOrders },
        { path: 'cart', name: 'client-cart', component: ClientCart }
      ]
    },

    // --- Trasy Spedycji (rola 'shipping') ---
    {
      path: '/shipping',
      component: ShippingLayout,
      meta: { requiresAuth: true, role: 'shipping' }, 
      children: [
        { path: '', name: 'shipping-dashboard', component: ShippingDashboard }
      ]
    }
  ]
});

// --- AUTH GUARD (Strażnik Nawigacji) ---
router.beforeEach((to, from, next) => {
    // Cała ta sekcja pozostaje BEZ ZMIAN
    const token = localStorage.getItem('token');
    const userJson = localStorage.getItem('user');
    const user = userJson ? JSON.parse(userJson) : null;
    const requiresAuth = to.meta.requiresAuth;
    const requiredRole = to.meta.role;
    const requiredRoles = to.meta.roles;

    if (requiresAuth && !token) {
        return next('/login');
    }
    if (requiresAuth && token) {
        let hasPermission = true; 
        if (requiredRoles) {
            if (!requiredRoles.includes(user.role)) hasPermission = false;
        } else if (requiredRole) {
            if (user.role !== requiredRole) hasPermission = false;
        }
        if (!hasPermission) {
            if (user.role === 'user') return next('/dashboard');
            if (user.role === 'shipping') return next('/shipping');
            if (user.role === 'power_user') return next('/admin/dashboard'); 
            return next('/login');
        }
        return next();
    }
    if (token && (to.name === 'login' || to.name === 'home' || to.name ==='forgot-password' || to.name === 'reset-password')) {
        if (user.role === 'admin') return next('/admin/dashboard');
        if (user.role === 'user') return next('/dashboard'); 
        if (user.role === 'shipping') return next('/shipping');
        if (user.role === 'power_user') return next('/admin/dashboard');
    }
    return next();
});

export default router