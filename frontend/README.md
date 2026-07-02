# Cyber Panchayat — Frontend

Vue 3 + Vite frontend for the Cyber Panchayat civic services platform.

> **Note:** This submission uses a built-in mock API — no backend server is required. All pages are fully navigable with realistic sample data.

---

## Prerequisites

- Node.js 18 or later
- npm 9 or later

---

## Setup & Run

```bash
# Install dependencies
npm install

# Start the development server
npm run dev
```

Open **http://localhost:3000** in your browser.

---

## Demo Login Credentials

| Role    | Email               | Password     | Name                  | Ward    |
|---------|---------------------|--------------|-----------------------|---------|
| Admin   | admin@civic.gov     | Admin@123    | Preetam Nagar Admin   | Central |
| Staff   | rajesh@civic.gov    | Staff@123    | Rajesh Kumar          | Ward-1  |
| Staff   | priya@civic.gov     | Staff@123    | Priya Singh           | Ward-2  |
| Staff   | imran@civic.gov     | Staff@123    | Imran Khan            | Ward-3  |
| Staff   | sandeep@civic.gov   | Staff@123    | Sandeep Yadav         | Ward-4  |
| Staff   | kavita@civic.gov    | Staff@123    | Kavita Sharma         | Ward-5  |
| Citizen | amit@gmail.com      | Citizen@123  | Amit Sharma           | Ward-1  |
| Citizen | neha@gmail.com      | Citizen@123  | Neha Verma            | Ward-2  |
| Citizen | ravi.g@gmail.com    | Citizen@123  | Ravi Gupta            | Ward-3  |
| Citizen | sunita@gmail.com    | Citizen@123  | Sunita Mehta          | Ward-4  |
| Citizen | arjun@gmail.com     | Citizen@123  | Arjun Singh           | Ward-5  |

Use any of these to log in and explore the corresponding dashboard.

---

## Pages & Navigation

### Citizen
- **Dashboard** `/dashboard` — complaint stats and recent activity
- **Submit Complaint** `/submit` — new civic complaint with map location picker
- **My Complaints** `/complaints` — list of submitted complaints
- **Track Complaint** `/track` — public complaint tracker (no login needed)
- **Book Facility** `/facilities` — community halls and grounds
- **My Bookings** `/bookings`
- **Payments** `/payments`
- **Community Feed** `/feed`
- **Announcements** `/announcements`
- **Notifications** `/notifications`

### Admin
- **Dashboard** `/admin/dashboard` — city-wide stats and charts
- **Complaints** `/admin/complaints` — manage and assign complaints
- **Departments** `/admin/departments`
- **Officers** `/admin/officers`
- **Facilities** `/admin/facilities`
- **Bookings** `/admin/bookings`
- **Users** `/admin/users`
- **Community** `/admin/community`

### Staff / Field Officer
- **Dashboard** `/staff/dashboard`
- **Assigned Complaints** `/staff/complaints` — update status, upload completion photo
- **Community Posts** `/staff/community`

---

## Build for Production

```bash
npm run build
# Output: dist/
```

---

## Project Structure

```
src/
  api/          # Mock API (replace index.js with real axios client for backend integration)
  assets/       # Global CSS
  components/   # AppSidebar, LocationPicker, NotificationsPanel, etc.
  router/       # Vue Router (role-based guards)
  stores/       # Pinia auth store
  views/
    citizen/    # Citizen-facing pages
    staff/      # Staff/officer pages
    admin/      # Admin pages
```

---

## Tech Stack

- Vue 3 (Composition API)
- Vite
- Vue Router 4
- Pinia (state management)
- Leaflet (interactive maps)
- Axios-compatible mock API
