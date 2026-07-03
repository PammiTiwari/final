# Connecting the Frontend to the Backend

The frontend currently runs in **mock mode** — every API call is intercepted by
`frontend/src/api/index.js`, which fakes the whole backend in browser memory
using demo data from `frontend/src/api/seed.js`. No network requests are made.

The mock was deliberately built with the **exact same interface and JSON shapes
as the real Flask backend** (same endpoints, same field names, same permission
rules). Because of that, switching to the real backend is a small, contained
change: **one file is replaced, one file is deleted, one config line is added.
No `.vue` file, router, store, or component needs to change.**

---

## Step 1 — Replace the mock in `frontend/src/api/index.js`

Delete the entire contents of `frontend/src/api/index.js` and replace with:

```js
import axios from "axios"

const api = axios.create({ baseURL: "/api" })

// Attach the JWT to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("civic_token")
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On an expired/invalid session, clear it and return to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("civic_token")
      localStorage.removeItem("civic_user")
      window.location.href = "/login"
    }
    return Promise.reject(err)
  }
)

export default api
```

Why this is enough: every view calls `api.get(...)` / `api.post(...)` etc. and
reads `res.data`. The mock exposed the identical `{ get, post, put, delete,
patch }` interface, so nothing upstream can tell the difference.

## Step 2 — Add the dev proxy in `frontend/vite.config.js`

This is the **complete final content** of `frontend/vite.config.js` after the
change — you can replace the whole file with this (only the `proxy` block is
new; everything else is unchanged):

```js
import { fileURLToPath, URL } from "node:url"
import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 3000,
    open: true,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
  },
})
```

The browser keeps talking to `localhost:3000`; Vite silently forwards every
`/api/*` request to Flask on port 5000. No CORS issues in development.

> Note: the backend also has CORS enabled (`flask_cors` in
> `backend/apps/__init__.py`), so pointing `baseURL` directly at
> `http://localhost:5000/api` works too. The proxy is preferred because image
> paths like `/api/uploads/pothole.jpg` then resolve on the same origin without
> any changes.

## Step 3 — Delete `frontend/src/api/seed.js`

It was the mock's demo data. Nothing else imports it — once the mock is gone
it's dead code. (Verified: no `.vue` file or store imports it directly.)

## Step 4 — Run both servers together

```bash
# Terminal 1 — backend (Flask on :5000)
cd backend
pip install -r requirements.txt        # first time only
python3 main.py                        # creates + seeds civic.db if empty

# Terminal 2 — frontend (Vite on :3000)
cd frontend
npm install                            # first time only
npm run dev
```

Open http://localhost:3000 — the app now runs against the real database.

Demo credentials (same as mock): admin `admin@civic.gov` / `Admin@123`,
officer `rajesh@civic.gov` / `Staff@123`, citizen `amit@gmail.com` /
`Citizen@123`.

---

## What does NOT need to change (and why)

| Area | Change needed | Why it already works |
|---|---|---|
| All 37 `.vue` views/components | None | They only know the axios-style interface, which is unchanged |
| `src/router/index.js` (routes + guards) | None | Role checks read the Pinia store, not the API layer |
| `src/stores/auth.js` | None | Already written for the real flow: expects `{ token, user }` from `/auth/login`, stores the JWT, calls `/auth/me` |
| `MultiImageUpload.vue` | None | Already sends a real `multipart/form-data` `FormData` to `POST /upload`; the backend returns `{ url: "/api/uploads/<file>" }` which renders as-is through the proxy |
| Business rules (who can do what) | None | The backend enforces the same rules the mock did — staff limited to their own assignment + `in_progress`/`resolved`, citizen close/reopen only on resolved, announcements admin-only, etc. Both layers were kept in sync deliberately |
| JSON field names | None | `cmp_id`, `assignment {staff_id, staff_name, staff_department, ...}`, `admin_notes`, `image_urls`, `evidence_urls`, `upvotes_count`, `rating`/`feedback` — identical on both sides |

## What you gain immediately after connecting

- **Persistence** — data survives page refreshes (SQLite `backend/civic.db`;
  delete the file to reseed fresh demo data on next start).
- **Similar-complaints suggestions** — the mock stubbed `/requests/similar` to
  `[]`; the real backend matches by category + ward + description text +
  location, so the "upvote instead of filing a duplicate" story comes alive.
- **Real AI assist** — category suggestion / photo & handwritten-note
  extraction run through the configured Gemini key (`backend/.env`) instead of
  canned mock responses.
- **Real uploads** — photos are stored as files in `backend/uploads/` instead
  of base64 strings in browser memory.

## Gotchas / checklist

1. **Start order doesn't matter**, but both must be running; if the frontend
   shows network errors, check Flask is up on :5000 (`curl
   http://localhost:5000/api/public-stats`).
2. **`backend/.env`** must exist (copy `backend/.env.example` and fill
   `GEMINI_API_KEY`) for the AI endpoints; everything else works without it.
3. **Stale sessions**: after switching, old `localStorage` from mock mode holds
   a fake token — the first real API call returns 401 and the interceptor
   redirects to login. Log in once and everything is normal.
4. **Production build**: the Vite proxy is dev-only. For a deployed build,
   either serve the built `dist/` through Flask (same origin, no proxy needed)
   or set `baseURL` to the backend's public URL — CORS is already enabled.
