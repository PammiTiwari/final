// ── Mock API — imports all data from seed.js ──────────────────────────────────
// To change what appears in the app, edit seed.js only.
// This file handles routing: matches the URL → returns the right data.

import {
  USERS, REQUESTS, DEPARTMENTS, OFFICERS,
  FACILITIES, BOOKINGS, PAYMENTS, NOTIFICATIONS, POSTS, ANNOUNCEMENTS,
} from "./seed.js"

const delay = (ms = 80) => new Promise(r => setTimeout(r, ms))

// Mirrors backend/apps/models.py DEPT_MAP — a request's department is always
// derived from its category, from the moment it's submitted, never left blank
// until an admin assigns it.
const DEPT_MAP = {
  road: "Road Maintenance",
  electricity: "Electricity Department",
  water: "Water Supply Department",
  sanitation: "Sanitation Department",
  waste: "Sanitation Department",
  parks: "Parks & Public Spaces",
  complaint: "General Affairs",
  maintenance: "General Affairs",
  other: "General Affairs",
}

// Base64 data URLs (not blob: URLs) so the picked photo keeps rendering even
// after a page reload — blob URLs are only valid for the page load that made them.
function fileToDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result)
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

function currentUser() {
  try { return JSON.parse(localStorage.getItem("civic_user") || "null") } catch { return null }
}

function matchId(url, prefix) {
  const m = url.match(new RegExp(`^${prefix}/(\\d+)(.*)?$`))
  return m ? { id: parseInt(m[1]), rest: m[2] || "" } : null
}

function byStatus(list, s) {
  return list.filter(r => r.status === s).length
}

// ── Route handler ─────────────────────────────────────────────────────────────
async function handle(method, url, body) {
  await delay()
  const path = url.replace(/^\/api/, "").replace(/\?.*$/, "")
  const qs   = url.includes("?") ? url.split("?")[1] : ""
  const M    = method.toUpperCase()
  const user = currentUser()

  // Auth
  if (M === "POST" && path === "/auth/login") {
    const found = USERS[body?.email]
    if (!found) throw { response: { status: 401, data: { message: "Invalid email or password." } } }
    const token = "mock-jwt-" + found.role + "-" + found.id
    localStorage.setItem("civic_token", token)
    localStorage.setItem("civic_user", JSON.stringify(found))
    return { data: { token, user: found } }
  }
  if (M === "POST" && path === "/auth/register") {
    // Same validation rules as the real backend (see api.py _validate_person)
    const name = (body?.name || "").trim()
    if (!/^[A-Za-z][A-Za-z\s.'-]{1,79}$/.test(name)) {
      throw { response: { status: 400, data: { message: "Please enter a valid name — letters only, numbers are not a name" } } }
    }
    const email = (body?.email || "").toLowerCase().trim()
    if (!/^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/.test(email)) {
      throw { response: { status: 400, data: { message: "Please enter a valid email address" } } }
    }
    if ((body?.password || "").length < 6) {
      throw { response: { status: 400, data: { message: "Password must be at least 6 characters" } } }
    }
    if (USERS[email]) {
      throw { response: { status: 409, data: { message: "Email already registered" } } }
    }
    const nextId = Math.max(...Object.values(USERS).map(u => u.id)) + 1
    const newUser = { id: nextId, name, email, role: "citizen", ward: body.ward || "Ward-1", phone: body.phone || "", address: body.address || null, is_active: true, created_at: new Date().toISOString() }
    USERS[email] = newUser
    const token = `mock-jwt-citizen-${nextId}`
    localStorage.setItem("civic_token", token)
    localStorage.setItem("civic_user", JSON.stringify(newUser))
    return { data: { token, user: newUser } }
  }
  if (M === "GET"  && path === "/auth/me") {
    if (!user) throw { response: { status: 401, data: {} } }
    return { data: user }
  }
  if (M === "POST" && path === "/auth/forgot-password") {
    return { data: { message: "If that email exists, a reset link has been sent." } }
  }

  // Dashboard (returns different shape per role)
  if (M === "GET" && path === "/dashboard") {
    if (user?.role === "admin") {
      return { data: {
        requests: { total: REQUESTS.length, pending: byStatus(REQUESTS,"pending"), assigned: byStatus(REQUESTS,"assigned"), reassigned: byStatus(REQUESTS,"reassigned"), in_progress: byStatus(REQUESTS,"in_progress"), on_hold_weather: byStatus(REQUESTS,"on_hold_weather"), reopened: byStatus(REQUESTS,"reopened"), resolved: byStatus(REQUESTS,"resolved"), closed: byStatus(REQUESTS,"closed") },
        users: { citizens: 5, staff: OFFICERS.length },
        recent: [...REQUESTS].slice(-5).reverse(),
      }}
    }
    if (user?.role === "staff") {
      const mine = REQUESTS.filter(r => r.assignment?.staff_id === user?.id || r.assignment?.staff_name === user?.name)
      return { data: {
        assignments: { total: mine.length, pending: byStatus(mine,"assigned"), in_progress: byStatus(mine,"in_progress"), resolved: byStatus(mine,"resolved") },
        recent: mine.slice(-5).reverse(),
      }}
    }
    // citizen
    const mine = REQUESTS.filter(r => r.citizen_id === user?.id)
    return { data: {
      requests: { total: mine.length, pending: byStatus(mine,"pending"), in_progress: mine.filter(r => ["assigned","in_progress","reassigned","reopened"].includes(r.status)).length, resolved: byStatus(mine,"resolved") },
      recent: mine.slice(-5).reverse(),
    }}
  }

  // Reports
  if (M === "GET" && path === "/reports") {
    const days = Array.from({ length: 14 }, (_, i) => {
      const d = new Date("2026-06-18"); d.setDate(d.getDate() + i)
      return { date: d.toISOString().split("T")[0], count: Math.floor(Math.random()*5)+1, resolved: Math.floor(Math.random()*4) }
    })
    return { data: {
      complaints_over_time: days,
      department_performance: DEPARTMENTS.map(d => {
        const total    = REQUESTS.filter(r => r.department === d.name).length
        const resolved = REQUESTS.filter(r => r.department === d.name && r.status === "resolved").length
        const pct      = total > 0 ? Math.round((resolved / total) * 100) : 0
        return { name: d.name, total, resolved, pct, avg_days: (Math.random()*4 + 1).toFixed(1) }
      }),
    }}
  }

  // Notifications
  const _notifUser = Object.values(USERS).find(u => u.email === user?.email)
  const _myId = _notifUser?.id ?? user?.id
  if (M === "GET" && path === "/notifications") {
    const mine = NOTIFICATIONS.filter(n => n.user_id === _myId)
    return { data: { notifications: [...mine].reverse(), unread_count: mine.filter(n => !n.is_read).length } }
  }
  const notifMatch = matchId(path, "/notifications")
  if (M === "PUT" && notifMatch) {
    if (notifMatch.id === 0) NOTIFICATIONS.filter(n => n.user_id === _myId).forEach(n => { n.is_read = true })
    else { const n = NOTIFICATIONS.find(n => n.id === notifMatch.id); if (n) n.is_read = true }
    return { data: { success: true } }
  }

  // Requests
  if (M === "GET" && path === "/requests") {
    if (user?.role === "citizen") return { data: REQUESTS.filter(r => r.citizen_id === user.id || r.citizen_name === user.name) }
    if (user?.role === "staff") return { data: REQUESTS.filter(r => r.assignment?.staff_id === user?.id || r.assignment?.staff_name === user?.name) }
    return { data: REQUESTS }
  }
  if (M === "POST" && path === "/requests") {
    const nextId = REQUESTS.reduce((max, r) => Math.max(max, r.id), 0) + 1
    const newReq = { id: nextId, cmp_id: `CMP${String(nextId).padStart(4, "0")}`, citizen_id: user?.id, citizen_name: user?.name, status: "pending", priority: "medium", upvotes_count: 0, upvoted_by_me: false, pending_funds: false, reopen_count: 0, hold_reason: null, image_urls: [], evidence_urls: [], assignment: null, created_at: new Date().toISOString(), updated_at: new Date().toISOString(), ...body, department: DEPT_MAP[body?.category] || "General Affairs" }
    REQUESTS.push(newReq)
    return { data: newReq }
  }
  if (M === "POST" && path === "/requests/similar") return { data: [] }
  if (M === "GET"  && path === "/requests/community") {
    const ward = user?.ward
    const list = ward ? REQUESTS.filter(r => r.ward === ward) : REQUESTS.slice(0, 20)
    return { data: [...list].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 50) }
  }

  const reqMatch = matchId(path, "/requests")
  if (reqMatch) {
    const req = REQUESTS.find(r => r.id === reqMatch.id)
    if (M === "GET") return { data: req || null }
    if (M === "DELETE" && !reqMatch.rest) {
      if (!req) return Promise.reject({ response: { status: 404, data: { message: "Not found" } } })
      if (user?.role === "staff") {
        return Promise.reject({ response: { status: 403, data: { message: "Forbidden" } } })
      }
      if (user?.role === "citizen" && (req.citizen_id !== user.id || req.status !== "pending")) {
        return Promise.reject({ response: { status: 403, data: { message: "Cannot delete this request" } } })
      }
      if (user?.role === "admin" && ["resolved", "closed"].includes(req.status)) {
        return Promise.reject({ response: { status: 400, data: { message: "Cannot delete a resolved/closed request — it's part of the public accountability record" } } })
      }
      const idx = REQUESTS.indexOf(req)
      if (idx > -1) REQUESTS.splice(idx, 1)
      return { data: { message: "Request deleted" } }
    }
    if (M === "PUT" && reqMatch.rest === "/status") {
      if (req) {
        const newStatus = body?.status || req.status
        if (newStatus === "rejected") {
          if (user?.role !== "admin") {
            return Promise.reject({ response: { status: 403, data: { message: "Only an admin can reject a request" } } })
          }
          if (req.status !== "pending") {
            return Promise.reject({ response: { status: 400, data: { message: "Only a pending (unassigned) request can be rejected" } } })
          }
          if (!(body?.admin_notes || "").trim()) {
            return Promise.reject({ response: { status: 400, data: { message: "A reason is required to reject a request" } } })
          }
        }
        if (user?.role === "staff") {
          if (!req.assignment || req.assignment.staff_id !== user.id) {
            return Promise.reject({ response: { status: 403, data: { message: "Not your assignment" } } })
          }
          if (req.status === "closed") {
            return Promise.reject({ response: { status: 400, data: { message: "Citizen has closed this request — it can no longer be changed" } } })
          }
          if (req.status === "on_hold_weather") {
            return Promise.reject({ response: { status: 400, data: { message: "This request is on hold for weather restrictions — an admin needs to resume it first" } } })
          }
          if (req.status === "resolved") {
            return Promise.reject({ response: { status: 400, data: { message: "This request is already resolved — no further updates until the citizen reopens or closes it" } } })
          }
          if (req.status === "rejected") {
            return Promise.reject({ response: { status: 400, data: { message: "This request was rejected and can no longer be updated" } } })
          }
          if (!["in_progress", "resolved"].includes(newStatus)) {
            return Promise.reject({ response: { status: 400, data: { message: "Staff can only mark in_progress or resolved" } } })
          }
        } else if (user?.role === "citizen") {
          if (newStatus === "closed" && req.status !== "resolved") {
            return Promise.reject({ response: { status: 400, data: { message: "Only a resolved complaint can be closed" } } })
          }
          if (newStatus === "reopened") {
            if (req.status !== "resolved") {
              return Promise.reject({ response: { status: 400, data: { message: "Only a resolved complaint can be reopened" } } })
            }
            if (req.reopen_count >= 2) {
              return Promise.reject({ response: { status: 400, data: { message: "This complaint has already been reopened twice — please contact the department directly" } } })
            }
            req.reopen_count = (req.reopen_count || 0) + 1
          }
        }
        Object.assign(req, { status: newStatus, hold_reason: body?.hold_reason || req.hold_reason, updated_at: new Date().toISOString() })
        if (body?.admin_notes) req.admin_notes = body.admin_notes
        if (body?.evidence_urls?.length && newStatus === "resolved") req.evidence_urls = body.evidence_urls
        if (newStatus === "closed" && user?.role === "citizen") {
          if (body?.rating != null) req.rating = body.rating
          if (body?.feedback) req.feedback = body.feedback.trim()
        }
      }
      return { data: req }
    }
    if (M === "PUT" && reqMatch.rest === "/budget-tag") {
      if (req) { req.needs_funds = body?.needs_funds ?? req.needs_funds; req.updated_at = new Date().toISOString() }
      return { data: req }
    }
    if (M === "PUT"  && reqMatch.rest === "/reopen") { if (req) { req.status = "reopened"; req.updated_at = new Date().toISOString() } return { data: req } }
    if (M === "POST" && reqMatch.rest === "/upvote") { if (req) { req.upvoted_by_me = !req.upvoted_by_me; req.upvotes_count = Math.max(0, (req.upvotes_count || 0) + (req.upvoted_by_me ? 1 : -1)) } return { data: { upvoted: req?.upvoted_by_me, upvotes_count: req?.upvotes_count } } }
  }

  // Public track & stats
  if (M === "GET" && path === "/track") {
    const id = qs.match(/id=([^&]+)/)?.[1]
    const found = REQUESTS.find(r => r.cmp_id === id)
    if (!found) throw { response: { status: 404, data: { message: "Complaint not found." } } }
    return { data: found }
  }
  if (M === "GET" && path === "/public-stats") {
    const inProgressStatuses = ["assigned", "reassigned", "in_progress", "reopened", "on_hold_weather"]
    return { data: {
      total_complaints: REQUESTS.length,
      resolved: REQUESTS.filter(r => ["resolved", "closed"].includes(r.status)).length,
      in_progress: REQUESTS.filter(r => inProgressStatuses.includes(r.status)).length,
      departments: DEPARTMENTS.length,
    } }
  }

  // Assignments
  if (M === "POST" && path === "/assignments") {
    const req     = REQUESTS.find(r => r.id === body?.request_id)
    const officer = OFFICERS.find(o => o.id === (body?.staff_id || body?.officer_id))
    if (!req) return Promise.reject({ response: { status: 404, data: { message: "Request not found" } } })
    if (["resolved", "closed", "rejected"].includes(req.status)) {
      return Promise.reject({ response: { status: 400, data: { message: "Cannot assign a completed/closed request" } } })
    }
    if (!officer) return Promise.reject({ response: { status: 400, data: { message: "Invalid staff member" } } })
    if (!officer.is_active) return Promise.reject({ response: { status: 400, data: { message: "Cannot assign to a deactivated officer" } } })
    const wasReassign = !!req.assignment
    const assignment = {
      id: req.assignment?.id || REQUESTS.reduce((max, r) => Math.max(max, r.assignment?.id || 0), 0) + 1,
      request_id: req.id,
      staff_id: officer.id,
      staff_name: officer.name,
      staff_department: officer.department,
      assigned_by: user?.id,
      notes: body?.notes || "",
      assigned_at: new Date().toISOString(),
      completed_at: null,
    }
    req.assignment = assignment
    req.status = wasReassign ? "reassigned" : "assigned"
    req.department = officer.department
    req.admin_notes = body?.notes || `${wasReassign ? "Reassigned" : "Assigned"} to ${officer.name} (${officer.department})`
    req.updated_at = new Date().toISOString()
    return { data: assignment }
  }
  const asgMatch = matchId(path, "/assignments")
  if (asgMatch && M === "PUT") {
    const req = REQUESTS.find(r => r.id === asgMatch.id)
    if (req) { Object.assign(req, { status: body?.status || "in_progress", updated_at: new Date().toISOString() }); if (body?.evidence_urls?.length) req.evidence_urls = body.evidence_urls }
    return { data: { success: true } }
  }

  // Staff assignments
  if (M === "GET" && path === "/staff/assignments") {
    const mine = REQUESTS.filter(r => r.assignment?.staff_id === user?.id)
    return { data: { assignments: mine.map(r => ({ request: r, officer: user })) } }
  }

  // Departments
  if (M === "GET"  && path === "/departments") return { data: DEPARTMENTS }
  if (M === "POST" && path === "/departments") { const d = { id: DEPARTMENTS.length + 1, officer_count: 0, ...body }; DEPARTMENTS.push(d); return { data: d } }
  const deptMatch = matchId(path, "/departments")
  if (deptMatch) {
    const d = DEPARTMENTS.find(x => x.id === deptMatch.id)
    if (M === "PUT")    {
      if (!d) return Promise.reject({ response: { status: 404, data: { message: "Not found" } } })
      const newName = (body?.name || "").trim()
      if ("name" in (body || {})) {
        if (!newName) return Promise.reject({ response: { status: 400, data: { message: "Name cannot be blank" } } })
        if (DEPARTMENTS.some(x => x.id !== d.id && x.name.toLowerCase() === newName.toLowerCase())) {
          return Promise.reject({ response: { status: 409, data: { message: "A department with this name already exists" } } })
        }
      }
      Object.assign(d, body, "name" in (body || {}) ? { name: newName } : {})
      return { data: d }
    }
    if (M === "DELETE") { const i = DEPARTMENTS.indexOf(d); if (i > -1) DEPARTMENTS.splice(i, 1); return { data: { success: true } } }
  }

  // Officers
  if (M === "GET"  && path === "/officers") return { data: OFFICERS }
  if (M === "POST" && path === "/officers") { const o = { id: OFFICERS.length + 20, assigned_count: 0, is_active: true, ...body }; OFFICERS.push(o); return { data: o } }
  const offMatch = matchId(path, "/officers")
  if (offMatch) {
    const o = OFFICERS.find(x => x.id === offMatch.id)
    if (M === "PUT")    { Object.assign(o, body); return { data: o } }
    if (M === "DELETE") { if (o) o.is_active = false; return { data: { success: true } } }
  }

  // Admin users
  if (M === "GET" && path === "/admin/users") return { data: Object.values(USERS) }
  const userMatch = matchId(path, "/admin/users")
  if (userMatch && M === "PUT") return { data: { success: true } }

  // Facilities
  if (M === "GET"  && path === "/facilities") return { data: FACILITIES }
  if (M === "POST" && path === "/facilities") {
    const cap = parseInt(body?.capacity), fee = parseFloat(body?.fee_per_hour ?? 0)
    if (!(body?.name || "").trim() || !(body?.address || "").trim()) throw { response: { status: 400, data: { message: "Name and address cannot be blank" } } }
    if (isNaN(cap) || cap < 1 || cap > 100000) throw { response: { status: 400, data: { message: "Capacity must be between 1 and 100000" } } }
    if (isNaN(fee) || fee < 0) throw { response: { status: 400, data: { message: "Fee per hour cannot be negative" } } }
    const f = { id: FACILITIES.length + 1, image_urls: [], is_active: true, ...body, capacity: cap, fee_per_hour: fee }
    FACILITIES.push(f)
    return { data: f }
  }
  const facMatch = matchId(path, "/facilities")
  if (facMatch) {
    const f = FACILITIES.find(x => x.id === facMatch.id)
    if (M === "GET"  && !facMatch.rest)                      return { data: f }
    if (M === "PUT")                                          { Object.assign(f, body); return { data: f } }
    if (M === "DELETE")                                       { if (f) f.is_active = false; return { data: { success: true } } }
    if (M === "GET"  && facMatch.rest.includes("availability")) {
      // Same shape as the backend: existing pending/confirmed bookings that day
      const dateParam = new URLSearchParams(qs).get("date")
      const booked = BOOKINGS.filter(x => x.facility_id === facMatch.id && x.booking_date === dateParam &&
        ["pending", "confirmed"].includes(x.status))
      return { data: { facility_id: facMatch.id, date: dateParam, booked_slots: booked.map(x => ({ start: x.start_time, end: x.end_time, status: x.status })) } }
    }
    if (M === "POST")                                         return { data: { url: "" } }
  }

  // Bookings
  if (M === "GET" && path === "/bookings") {
    return { data: user?.role === "citizen" ? BOOKINGS.filter(b => b.citizen_id === user.id || b.citizen_name === user.name) : BOOKINGS }
  }
  if (M === "POST" && path === "/bookings") {
    const facility = FACILITIES.find(f => f.id === body?.facility_id)
    // Same rules as the backend BookingListResource
    const bad = (msg) => { throw { response: { status: 400, data: { message: msg } } } }
    if (!facility) throw { response: { status: 404, data: { message: "Facility not found or inactive" } } }
    if (!(body?.purpose || "").trim()) bad("Purpose is required")
    const today = new Date(); today.setHours(0, 0, 0, 0)
    const bDate = new Date(body?.booking_date + "T00:00:00")
    if (isNaN(bDate)) bad("Invalid date/time format. Use YYYY-MM-DD and HH:MM")
    if (bDate < today) bad("Cannot book for a past date")
    if (body?.start_time >= body?.end_time) bad("Start time must be before end time")
    const attendees = parseInt(body?.attendees ?? 1)
    if (isNaN(attendees) || attendees < 1) bad("Attendees must be at least 1")
    if (attendees > facility.capacity) bad(`Attendees exceed facility capacity of ${facility.capacity}`)
    const clash = BOOKINGS.some(x => x.facility_id === facility.id && x.booking_date === body.booking_date &&
      x.status !== "cancelled" && x.start_time < body.end_time && body.start_time < x.end_time)
    if (clash) throw { response: { status: 409, data: { message: "This time slot is already booked" } } }
    const b = { id: BOOKINGS.length + 1, user_id: user?.id, user_name: user?.name, facility_name: facility?.name, status: "pending", paid: false, payment_id: null, total_amount: 0, created_at: new Date().toISOString(), ...body, attendees }
    BOOKINGS.push(b)
    return { data: b }
  }
  const bookMatch = matchId(path, "/bookings")
  if (bookMatch) {
    const b = BOOKINGS.find(x => x.id === bookMatch.id)
    if (M === "PUT"  && !bookMatch.rest)                    { Object.assign(b, body); return { data: b } }
    if (M === "PUT"  && bookMatch.rest.includes("status"))  {
      if (b && ["cancelled", "completed"].includes(b.status)) {
        return Promise.reject({ response: { status: 400, data: { message: `A ${b.status} booking can no longer be changed` } } })
      }
      if (b) b.status = body?.status || b.status
      return { data: b }
    }
    if (M === "DELETE")                                     { if (b) b.status = "cancelled"; return { data: { success: true } } }
    if (M === "GET"  && bookMatch.rest.includes("invoice")) {
      const facility = FACILITIES.find(f => f.id === b?.facility_id)
      const hours = b ? (parseInt(b.end_time) - parseInt(b.start_time)) || 1 : 1
      const subtotal = (facility?.fee_per_hour || 0) * hours
      const gst = Math.round(subtotal * 0.18)
      return { data: {
        invoice_number: `INV-${String(bookMatch.id).padStart(4,'0')}`,
        issued_at: new Date().toLocaleDateString('en-IN'),
        citizen_name: b?.citizen_name || user?.name,
        citizen_phone: user?.phone || '—',
        facility_name: b?.facility_name,
        facility_address: facility?.address || '—',
        booking_date: b?.booking_date,
        start_time: b?.start_time,
        end_time: b?.end_time,
        hours,
        purpose: b?.purpose,
        fee_per_hour: facility?.fee_per_hour || 0,
        subtotal,
        gst_18_percent: gst,
        total: subtotal + gst,
        payment_status: b?.payment?.status === "paid" ? 'paid' : (facility?.fee_per_hour === 0 ? 'free' : 'due'),
      }}
    }
    if (M === "POST" && bookMatch.rest.includes("pay")) {
      if (b) { b.paid = true; b.status = "approved"; b.payment_id = "PAY-" + Math.random().toString(36).slice(2,8).toUpperCase() }
      const p = { id: PAYMENTS.length + 1, booking_id: bookMatch.id, user_id: user?.id, amount: b?.total_amount || 0, status: "paid", method: body?.method || "UPI", transaction_id: "TXN" + Math.random().toString(36).slice(2,10).toUpperCase(), created_at: new Date().toISOString(), facility_name: b?.facility_name }
      PAYMENTS.push(p)
      return { data: p }
    }
  }

  // Payments
  if (M === "GET" && path === "/payments") {
    return { data: user?.role === "citizen" ? PAYMENTS.filter(p => p.citizen_id === user.id || p.citizen_name === user.name) : PAYMENTS }
  }
  const payMatch = matchId(path, "/payments")
  if (payMatch && M === "POST" && payMatch.rest.includes("pay")) {
    const p = { id: PAYMENTS.length + 1, user_id: user?.id, amount: body?.amount || 0, status: "paid", method: body?.method || "UPI", transaction_id: "TXN" + Math.random().toString(36).slice(2,10).toUpperCase(), created_at: new Date().toISOString() }
    PAYMENTS.push(p)
    return { data: p }
  }

  // Posts
  if (M === "GET" && path === "/posts") {
    const cat = qs.match(/category=([^&]+)/)?.[1]
    if (cat === "announcement") return { data: ANNOUNCEMENTS.map(a => ({ ...a, type: "announcement" })) }
    // The general community feed never mixes in official announcements —
    // those only ever show on the dedicated Announcements page.
    // Each post is copied (not the live POSTS objects) — the frontend applies
    // its own like/comment-count deltas on top of what it fetched, so handing
    // out shared references would let a later mock mutation double-apply.
    return { data: POSTS.filter(p => p.category !== "announcement").map(p => ({ ...p })) }
  }
  if (M === "POST" && path === "/posts") {
    const content = (body?.content || "").trim()
    if (!content && !(body?.image_urls || []).length) {
      throw { response: { status: 400, data: { message: "Content required" } } }
    }
    // Only an admin can publish an official announcement — everyone else's
    // posts land in the regular community feed, announcement or not.
    const category = body?.category === "announcement" && user?.role === "admin" ? "announcement" : (body?.category || "general")
    const p = { id: POSTS.length + 1, citizen_id: user?.id, author_name: user?.name, author_role: user?.role, author_department: user?.department || null, is_official: user?.role === "staff" || user?.role === "admin", likes_count: 0, comments_count: 0, liked_by_me: false, created_at: new Date().toISOString(), comments_list: [], image_urls: [], ...body, content, category }
    POSTS.unshift(p)
    return { data: p }
  }
  const postMatch = matchId(path, "/posts")
  if (postMatch) {
    const p = POSTS.find(x => x.id === postMatch.id)
    // Comment delete must be matched before the post delete below — both are
    // DELETEs under /posts/:id, only the rest of the path differs.
    const commentDel = postMatch.rest.match(/^\/comments\/(\d+)$/)
    if (M === "DELETE" && commentDel) {
      const cid = parseInt(commentDel[1])
      const idx = (p?.comments_list || []).findIndex(c => c.id === cid)
      if (idx === -1) return Promise.reject({ response: { status: 404, data: { message: "Not found" } } })
      const c = p.comments_list[idx]
      if (!(user?.role === "admin" || c.user_id === user?.id)) {
        return Promise.reject({ response: { status: 403, data: { message: "You can only delete your own comments" } } })
      }
      p.comments_list.splice(idx, 1)
      p.comments_count--
      return { data: { success: true } }
    }
    if (M === "DELETE")                                       { const i = POSTS.indexOf(p); if (i > -1) POSTS.splice(i, 1); return { data: { success: true } } }
    if (M === "POST" && postMatch.rest.includes("like"))      { if (p) { p.liked_by_me = !p.liked_by_me; p.likes_count += p.liked_by_me ? 1 : -1 } return { data: { liked: p?.liked_by_me, likes_count: p?.likes_count } } }
    // Return a copy, not the live array — the frontend also appends its own new
    // comment locally after posting, so sharing the same reference here would
    // make that comment show up twice (server-side push + client-side push).
    if (M === "GET"  && postMatch.rest.includes("comments"))  return { data: [...(p?.comments_list || [])] }
    if (M === "POST" && postMatch.rest.includes("comments")) {
      const content = (body?.content || "").trim()
      if (!content) throw { response: { status: 400, data: { message: "Content required" } } }
      const c = { id: Date.now(), user_id: user?.id, author_name: user?.name, author_department: user?.department || null, is_official: user?.role === "staff" || user?.role === "admin", content, created_at: new Date().toISOString() }
      if (p) { p.comments_list.push(c); p.comments_count++ }
      return { data: c }
    }
  }

  // Announcements
  if (M === "GET"  && path === "/announcements") return { data: ANNOUNCEMENTS }
  if (M === "POST" && path === "/announcements") { const a = { id: ANNOUNCEMENTS.length + 1, author_name: user?.name, created_at: new Date().toISOString(), ...body }; ANNOUNCEMENTS.unshift(a); return { data: a } }
  const annMatch = matchId(path, "/announcements")
  if (annMatch && M === "DELETE") { const i = ANNOUNCEMENTS.findIndex(a => a.id === annMatch.id); if (i > -1) ANNOUNCEMENTS.splice(i, 1); return { data: { success: true } } }

  // Upload / AI — uses the actual picked file (as a base64 data URL) so the
  // photo you see afterwards is the one you uploaded, not a random demo image.
  if (M === "POST" && path === "/upload") {
    const file = body?.get?.("file")
    const url = file ? await fileToDataUrl(file) : ""
    return { data: { url } }
  }
  if (M === "POST" && path === "/requests/scan-paper")   return { data: { title: "Broken footpath near market", category: "Roads & Footpaths", description: "Paper scan detected: footpath damaged near the main market entrance.", location_text: "Market Area, Ward 5", image_url: null } }
  if (M === "POST" && path === "/ai/extract-from-image") {
    const file = body?.get?.("file")
    const image_url = file ? await fileToDataUrl(file) : null
    return { data: { title: "Damaged road surface", category: "Roads & Footpaths", description: "Road surface appears damaged with visible cracks and potholes.", location_text: "", image_url } }
  }
  if (M === "POST" && path === "/ai/suggest")            return { data: { suggestions: ["Add your exact location to help officers find the site.", "High-priority issues are usually resolved within 3 working days.", "Adding a photo speeds up resolution."] } }

  console.warn("[MockAPI] Unhandled:", M, url)
  return { data: {} }
}

// ── Axios-compatible interface ────────────────────────────────────────────────
function wrap(method) {
  return async (url, dataOrConfig, _config) => {
    const body = (method === "get" || method === "delete") ? null : dataOrConfig
    // axios-style `{ params: {...} }` config on GET/DELETE → append as query string
    const params = (method === "get" || method === "delete") ? dataOrConfig?.params : _config?.params
    if (params && Object.keys(params).length) {
      const qs = new URLSearchParams(params).toString()
      url += (url.includes("?") ? "&" : "?") + qs
    }
    try {
      return await handle(method, url, body)
    } catch (err) {
      if (err?.response?.status === 401) {
        localStorage.removeItem("civic_token")
        localStorage.removeItem("civic_user")
        window.location.href = "/login"
      }
      return Promise.reject(err)
    }
  }
}

export default { get: wrap("get"), post: wrap("post"), put: wrap("put"), delete: wrap("delete"), patch: wrap("patch") }
