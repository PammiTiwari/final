import { createRouter, createWebHistory } from "vue-router"
import { useAuthStore } from "../stores/auth"

const routes = [
  // Public routes
  { path: "/", name: "home", component: () => import("../views/LandingView.vue"), meta: { public: true } },
  { path: "/login", name: "login", component: () => import("../views/LoginView.vue"), meta: { public: true } },
  { path: "/register", name: "register", component: () => import("../views/RegisterView.vue"), meta: { public: true } },
  { path: "/forgot-password", name: "forgot-password", component: () => import("../views/ForgotPasswordView.vue"), meta: { public: true } },
  { path: "/track", name: "track-public", component: () => import("../views/citizen/TrackComplaint.vue"), meta: { public: true } },

  // Shared (all authenticated roles)
  { path: "/feed", name: "community-feed", component: () => import("../views/citizen/CommunityFeed.vue"), meta: { roles: ["citizen", "staff", "admin"] } },
  { path: "/announcements", name: "announcements", component: () => import("../views/AnnouncementsView.vue"), meta: { roles: ["citizen", "staff", "admin"] } },
  { path: "/notifications", name: "notifications", component: () => import("../views/NotificationsView.vue"), meta: { roles: ["citizen", "staff", "admin"] } },
  { path: "/profile", name: "profile", redirect: to => {
    // Redirect based on role — router guard handles it
    return "/dashboard"
  }, meta: { roles: ["citizen", "staff", "admin"] } },

  // Citizen routes
  { path: "/dashboard", name: "citizen-dashboard", component: () => import("../views/citizen/CitizenDashboard.vue"), meta: { roles: ["citizen"] } },
  { path: "/submit", name: "new-request", component: () => import("../views/citizen/NewRequest.vue"), meta: { roles: ["citizen"] } },
  { path: "/complaints", name: "my-requests", component: () => import("../views/citizen/MyRequests.vue"), meta: { roles: ["citizen"] } },
  { path: "/complaints/:id", name: "complaint-detail", component: () => import("../views/citizen/ComplaintDetail.vue"), meta: { roles: ["citizen"] } },

  // Legacy citizen route paths
  { path: "/requests", redirect: "/complaints", meta: { roles: ["citizen"] } },
  { path: "/requests/new", redirect: "/submit", meta: { roles: ["citizen"] } },
  { path: "/facilities", name: "facilities", component: () => import("../views/citizen/FacilitiesView.vue"), meta: { roles: ["citizen"] } },
  { path: "/bookings", name: "my-bookings", component: () => import("../views/citizen/MyBookings.vue"), meta: { roles: ["citizen"] } },
  { path: "/payments", name: "my-payments", component: () => import("../views/citizen/MyPayments.vue"), meta: { roles: ["citizen"] } },
  { path: "/subscription", name: "my-subscription", component: () => import("../views/citizen/MySubscription.vue"), meta: { roles: ["citizen"] } },

  // Staff routes
  { path: "/staff/dashboard", name: "staff-dashboard", component: () => import("../views/staff/StaffDashboard.vue"), meta: { roles: ["staff"] } },
  { path: "/staff/complaints", name: "staff-complaints", component: () => import("../views/staff/MyAssignments.vue"), meta: { roles: ["staff"] } },
  { path: "/staff/complaints/:id", name: "staff-update-status", component: () => import("../views/staff/UpdateStatus.vue"), meta: { roles: ["staff"] } },
  { path: "/staff/assignments", redirect: "/staff/complaints", meta: { roles: ["staff"] } },
  { path: "/staff/community", name: "staff-community", component: () => import("../views/staff/StaffCommunityPosts.vue"), meta: { roles: ["staff"] } },
  { path: "/staff/announcements", redirect: "/announcements", meta: { roles: ["staff"] } },

  // Admin routes
  { path: "/admin/dashboard", name: "admin-dashboard", component: () => import("../views/admin/AdminDashboard.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/departments", name: "admin-departments", component: () => import("../views/admin/ManageDepartments.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/officers", name: "admin-officers", component: () => import("../views/admin/ManageOfficers.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/complaints", name: "admin-complaints", component: () => import("../views/admin/ManageRequests.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/requests", redirect: "/admin/complaints", meta: { roles: ["admin"] } },
  { path: "/admin/community", name: "admin-community", component: () => import("../views/admin/CommunityManagement.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/reports", name: "admin-reports", component: () => import("../views/admin/ReportsAnalytics.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/users", name: "admin-users", component: () => import("../views/admin/ManageUsers.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/facilities", name: "admin-facilities", component: () => import("../views/admin/ManageFacilities.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/bookings", name: "admin-bookings", component: () => import("../views/admin/ManageBookings.vue"), meta: { roles: ["admin"] } },
  { path: "/admin/subscriptions", name: "admin-subscriptions", component: () => import("../views/admin/ManageSubscriptions.vue"), meta: { roles: ["admin"] } },

  { path: "/:pathMatch(.*)*", redirect: "/" },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach((to) => {
  const auth = useAuthStore()

  // Public routes - allow (including /login and /register even if already
  // logged in, so a user can switch accounts without an explicit logout step)
  if (to.meta.public) {
    return true
  }

  // Not logged in - redirect to login
  if (!auth.isLoggedIn) return "/login"

  // Check role-based access
  if (to.meta.roles && !to.meta.roles.includes(auth.role)) {
    if (auth.isCitizen) return "/dashboard"
    if (auth.isStaff) return "/staff/dashboard"
    if (auth.isAdmin) return "/admin/dashboard"
    return "/login"
  }

  return true
})

export default router
