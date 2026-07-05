<template>
  <aside class="sidebar">
    <!-- Brand -->
    <router-link :to="homePath" class="sidebar-brand">
      <span class="logo-mark">CP</span>
      <span class="brand-name">Cyber Panchayat</span>
    </router-link>

    <!-- Nav links -->
    <nav class="sidebar-nav">
      <template v-for="item in navItems" :key="item.label">
        <router-link v-if="item.type === 'link'" :to="item.path" class="nav-link" :class="{ active: isActive(item) }">
          {{ item.label }}
        </router-link>
        <div v-else class="nav-group">
          <div class="nav-group-label">{{ item.label }}</div>
          <router-link v-for="sub in item.items" :key="sub.path" :to="sub.path" class="nav-link nav-sublink" :class="{ active: isActive(sub) }">
            {{ sub.label }}
          </router-link>
        </div>
      </template>
    </nav>

    <!-- Bottom: notifications + user -->
    <div class="sidebar-footer">
      <router-link to="/notifications" class="footer-link notif-link">
        <span>Notifications</span>
        <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
      </router-link>

      <div class="user-section">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info">
          <div class="user-name">{{ auth.user?.name }}</div>
          <div class="user-role">{{ roleLabel }}</div>
        </div>
        <button class="logout-btn" @click="logout" title="Logout">&#10132;</button>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import api from '../api'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const unreadCount = ref(0)

const userInitial = computed(() => auth.user?.name?.charAt(0)?.toUpperCase() || 'U')
const roleLabel   = computed(() => auth.role ? auth.role.charAt(0).toUpperCase() + auth.role.slice(1) : '')
const homePath    = computed(() => {
  if (auth.isAdmin) return '/admin/dashboard'
  if (auth.isStaff) return '/staff/dashboard'
  return '/dashboard'
})

onMounted(() => {
  api.get('/notifications').then(res => { unreadCount.value = res.data.unread_count || 0 }).catch(() => {})
})

watch(() => route.fullPath, () => {
  api.get('/notifications').then(res => { unreadCount.value = res.data.unread_count || 0 }).catch(() => {})
})

function logout() {
  auth.logout()
  router.push('/login')
}

function isActive(item) {
  if (!item.path) return false
  if (item.exact) return route.path === item.path
  return route.path === item.path || route.path.startsWith(item.path + '/')
}

const citizenNav = [
  { type: 'link',  label: 'Dashboard',      path: '/dashboard', exact: true },
  { type: 'group', label: 'Complaints', items: [
    { label: 'Submit Complaint', path: '/submit' },
    { label: 'My Complaints',    path: '/complaints' },
    { label: 'Track Complaint',  path: '/track' },
  ]},
  { type: 'group', label: 'Facilities', items: [
    { label: 'Book Facility', path: '/facilities' },
    { label: 'My Bookings',   path: '/bookings' },
    { label: 'Payments',      path: '/payments' },
  ]},
  { type: 'link', label: 'Premium Subscription', path: '/subscription' },
  { type: 'group', label: 'Community', items: [
    { label: 'Community Feed', path: '/feed' },
    { label: 'Announcements',  path: '/announcements' },
  ]},
]

const staffNav = [
  { type: 'link', label: 'Dashboard',          path: '/staff/dashboard', exact: true },
  { type: 'link', label: 'Assigned Complaints', path: '/staff/complaints' },
  { type: 'link', label: 'Community Posts',     path: '/staff/community' },
  { type: 'link', label: 'Announcements',       path: '/announcements' },
]

const adminNav = [
  { type: 'link',  label: 'Dashboard', path: '/admin/dashboard', exact: true },
  { type: 'group', label: 'Complaints', items: [
    { label: 'Complaints',  path: '/admin/complaints' },
    { label: 'Departments', path: '/admin/departments' },
    { label: 'Officers',    path: '/admin/officers' },
  ]},
  { type: 'group', label: 'Resources', items: [
    { label: 'Facilities',     path: '/admin/facilities' },
    { label: 'Bookings',       path: '/admin/bookings' },
    { label: 'Subscriptions',  path: '/admin/subscriptions' },
  ]},
  { type: 'link', label: 'Users',         path: '/admin/users' },
  { type: 'link', label: 'Community',     path: '/admin/community' },
  { type: 'link', label: 'Announcements', path: '/announcements' },
]

const navItems = computed(() => {
  if (auth.isAdmin) return adminNav
  if (auth.isStaff) return staffNav
  return citizenNav
})
</script>

<style scoped>
.sidebar {
  width: 220px;
  min-width: 220px;
  height: 100vh;
  position: sticky;
  top: 0;
  background: var(--surface-dark);
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  z-index: 100;
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 1.25rem 1rem;
  text-decoration: none;
  border-bottom: 1px solid rgba(255,255,255,0.07);
  flex-shrink: 0;
}
.logo-mark {
  width: 32px; height: 32px;
  background: var(--primary);
  color: #fff;
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.7rem;
  flex-shrink: 0;
}
.brand-name {
  font-weight: 700;
  font-size: 0.88rem;
  color: #fff;
  white-space: nowrap;
}

/* Nav */
.sidebar-nav {
  flex: 1;
  padding: 0.75rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 2px;
  overflow-y: auto;
}
.nav-link {
  display: block;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  color: #93A3C2;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: var(--transition);
}
.nav-link:hover  { background: rgba(255,255,255,0.06); color: #fff; }
.nav-link.active { background: rgba(0,82,255,0.2); color: #fff; }
.nav-sublink     { padding-left: 1.25rem; font-size: 0.8rem; }

.nav-group { margin-top: 0.5rem; }
.nav-group-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6B7A99;
  padding: 0.4rem 0.75rem 0.25rem;
}

/* Footer */
.sidebar-footer {
  border-top: 1px solid rgba(255,255,255,0.07);
  padding: 0.75rem 0.6rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  flex-shrink: 0;
}
.footer-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  color: #93A3C2;
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 500;
  transition: var(--transition);
}
.footer-link:hover { background: rgba(255,255,255,0.06); color: #fff; }
.notif-link { justify-content: space-between; }
.notif-badge {
  background: var(--danger);
  color: #fff;
  font-size: 0.6rem;
  font-weight: 800;
  min-width: 16px; height: 16px;
  padding: 0 3px;
  border-radius: 100px;
  display: flex; align-items: center; justify-content: center;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  background: rgba(255,255,255,0.04);
}
.user-avatar {
  width: 30px; height: 30px;
  background: var(--primary);
  color: #fff;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.72rem; font-weight: 700;
  flex-shrink: 0;
}
.user-info { flex: 1; min-width: 0; }
.user-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.user-role {
  font-size: 0.65rem;
  color: #6B7A99;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.logout-btn {
  background: none;
  border: none;
  color: #6B7A99;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem;
  border-radius: 4px;
  transition: var(--transition);
  flex-shrink: 0;
}
.logout-btn:hover { color: var(--danger); }
</style>
