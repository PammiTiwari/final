import os
import uuid
import json
from datetime import datetime, date, time, timezone
from flask import request, current_app, send_from_directory
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)
from werkzeug.utils import secure_filename
from rapidfuzz import fuzz
from . import db
from .models import (now_ist, 
    User, ServiceRequest, Assignment, Facility, Booking, Payment, Notification,
    Post, PostComment, PostLike, ComplaintUpvote, Department,
    Role, RequestStatus, Priority, BookingStatus, PaymentStatus, DEPT_MAP
)

import re

# ── Input validators (shared) ─────────────────────────────────────────────────
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s.'-]{1,79}$")   # letters/spaces only, no digits
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
PHONE_RE = re.compile(r"^[6-9]\d{9}$")                    # 10-digit Indian mobile

def _validate_person(data, require_password=True):
    """Common checks for any human account (register / officer create).
    Returns an error tuple or None."""
    name = (data.get("name") or "").strip()
    if not NAME_RE.match(name):
        return {"message": "Please enter a valid name — letters only, numbers are not a name"}, 400
    email = (data.get("email") or "").lower().strip()
    if not EMAIL_RE.match(email):
        return {"message": "Please enter a valid email address"}, 400
    if require_password and len(data.get("password") or "") < 6:
        return {"message": "Password must be at least 6 characters"}, 400
    phone = (data.get("phone") or "").strip()
    if phone and not PHONE_RE.match(phone):
        return {"message": "Phone must be a valid 10-digit mobile number"}, 400
    return None


SIMILAR_THRESHOLD = 70  # rapidfuzz token_set_ratio cutoff for "looks like a duplicate"
PROXIMITY_M = 300       # complaints within this distance (metres) count as nearby duplicates

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}

def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ── Helpers ───────────────────────────────────────────────────────────────────

def _current_user():
    uid = int(get_jwt_identity())
    return db.session.get(User, uid)


def _require_role(*roles):
    uid = int(get_jwt_identity())
    user = db.session.get(User, uid)
    if not user or user.role not in roles:
        return {"message": "Forbidden: insufficient role"}, 403
    return None


def _notify(user_id, title, message, notif_type="info"):
    n = Notification(user_id=user_id, title=title, message=message, notif_type=notif_type)
    db.session.add(n)


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def _haversine_m(lat1, lng1, lat2, lng2):
    """Great-circle distance in metres between two lat/lng points."""
    import math
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def _find_similar(category, ward, description, lat=None, lng=None, limit=5):
    """Open complaints in the same category that look like duplicates — by fuzzy
    text and, when coordinates are supplied, by geographic proximity (which
    replaces the ward filter, since location is the stronger signal)."""
    has_geo = lat is not None and lng is not None
    q = ServiceRequest.query.filter(
        ServiceRequest.category == category,
        ServiceRequest.status.notin_([RequestStatus.CLOSED, RequestStatus.REJECTED]),
    )
    if ward and not has_geo:
        q = q.filter(ServiceRequest.ward == ward)
    candidates = q.order_by(ServiceRequest.created_at.desc()).limit(50).all()
    scored = []
    for r in candidates:
        score = fuzz.token_set_ratio(description, r.description or "")
        near = (has_geo and r.latitude is not None and r.longitude is not None
                and _haversine_m(lat, lng, r.latitude, r.longitude) <= PROXIMITY_M)
        if score >= SIMILAR_THRESHOLD or near:
            scored.append((1 if near else 0, score, r))  # nearby first, then by text score
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)
    return [r for _, _, r in scored[:limit]]


def _parse_time(s):
    return datetime.strptime(s, "%H:%M").time()


def _booking_conflicts(facility_id, booking_date, start_time, end_time, exclude_id=None):
    q = Booking.query.filter(
        Booking.facility_id == facility_id,
        Booking.booking_date == booking_date,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    if exclude_id:
        q = q.filter(Booking.id != exclude_id)
    return q.first() is not None


def _calculate_fee(facility, start_time, end_time):
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    hours = (end_dt - start_dt).seconds / 3600
    return round(facility.fee_per_hour * hours, 2)


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterResource(Resource):
    def post(self):
        data = request.get_json() or {}
        required = ["name", "email", "password"]
        missing = [f for f in required if not str(data.get(f) or "").strip()]
        if missing:
            return {"message": f"Missing fields: {', '.join(missing)}"}, 400

        invalid = _validate_person(data)
        if invalid:
            return invalid

        if User.query.filter_by(email=data["email"].lower().strip()).first():
            return {"message": "Email already registered"}, 409

        # Public self-registration only ever creates citizens — staff/admin
        # accounts must be created by an Admin via the Officer management flow.
        user = User(
            name=data["name"].strip(),
            email=data["email"].lower().strip(),
            role=Role.CITIZEN,
            phone=data.get("phone", ""),
            address=data.get("address", ""),
            ward=data.get("ward", ""),
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.commit()
        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"token": token, "user": user.to_dict()}, 201


class LoginResource(Resource):
    def post(self):
        data = request.get_json() or {}
        email = data.get("email", "").lower().strip()
        password = data.get("password", "")
        if not email or not password:
            return {"message": "Email and password required"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"message": "Invalid credentials"}, 401
        if not user.is_active:
            return {"message": "Account disabled. Contact admin."}, 403

        token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
        return {"token": token, "user": user.to_dict()}, 200


class MeResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        if not user:
            return {"message": "User not found"}, 404
        return user.to_dict(), 200

    @jwt_required()
    def put(self):
        user = _current_user()
        data = request.get_json() or {}
        if "name" in data and not NAME_RE.match((data["name"] or "").strip()):
            return {"message": "Please enter a valid name — letters only, numbers are not a name"}, 400
        if data.get("phone") and not PHONE_RE.match(data["phone"].strip()):
            return {"message": "Phone must be a valid 10-digit mobile number"}, 400
        for field in ["name", "phone", "address", "ward"]:
            if field in data:
                setattr(user, field, data[field].strip() if isinstance(data[field], str) else data[field])
        db.session.commit()
        return user.to_dict(), 200


# ── Service Requests ──────────────────────────────────────────────────────────

VALID_CATEGORIES = ["complaint", "road", "water", "electricity", "sanitation", "waste", "parks", "maintenance", "other"]

class RequestListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        status_filter = request.args.get("status")
        category_filter = request.args.get("category")
        ward_filter = request.args.get("ward")
        pending_funds_filter = request.args.get("pending_funds")
        sort_by = request.args.get("sort")  # "upvotes" to surface the most-backed complaints first

        if user.role == Role.CITIZEN:
            q = ServiceRequest.query.filter_by(citizen_id=user.id)
        elif user.role == Role.STAFF:
            q = ServiceRequest.query.join(Assignment).filter(Assignment.staff_id == user.id)
        else:
            q = ServiceRequest.query

        if status_filter:
            q = q.filter_by(status=status_filter)
        if category_filter:
            q = q.filter_by(category=category_filter)
        if ward_filter:
            q = q.filter_by(ward=ward_filter)
        if pending_funds_filter is not None:
            q = q.filter_by(pending_funds=(pending_funds_filter.lower() == "true"))

        requests_list = q.order_by(ServiceRequest.created_at.desc()).all()
        if sort_by == "upvotes":
            requests_list.sort(key=lambda r: r.upvotes.count(), reverse=True)
        return [r.to_dict() for r in requests_list], 200

    @jwt_required()
    def post(self):
        user = _current_user()
        err = _require_role(Role.CITIZEN)
        if err:
            return err

        data = request.get_json() or {}
        required = ["category", "description", "address"]
        missing = [f for f in required if not str(data.get(f) or "").strip()]
        if missing:
            return {"message": f"Missing: {', '.join(missing)}"}, 400

        if data["category"] not in VALID_CATEGORIES:
            return {"message": "Invalid category"}, 400

        priority = data.get("priority", Priority.MEDIUM)
        if priority not in Priority.ALL:
            priority = Priority.MEDIUM

        title = data.get("title") or f"{data['category'].title()} issue at {data['address'][:50]}"

        try:
            lat = float(data["latitude"]) if data.get("latitude") is not None else None
            lng = float(data["longitude"]) if data.get("longitude") is not None else None
        except (TypeError, ValueError):
            lat = lng = None

        sr = ServiceRequest(
            citizen_id=user.id,
            category=data["category"],
            title=title.strip(),
            description=data["description"].strip(),
            address=data["address"].strip(),
            ward=data.get("ward", user.ward or ""),
            latitude=lat,
            longitude=lng,
            priority=priority,
            image_urls=data.get("image_urls") or [],
        )
        db.session.add(sr)

        # notify all admins
        admins = User.query.filter_by(role=Role.ADMIN).all()
        for admin in admins:
            _notify(admin.id, "New Service Request",
                    f"{user.name} submitted a {data['category']} request: {title}", "request")

        db.session.commit()
        return sr.to_dict(), 201


class RequestResource(Resource):
    @jwt_required()
    def get(self, request_id):
        user = _current_user()
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404
        if user.role == Role.CITIZEN and sr.citizen_id != user.id:
            return {"message": "Forbidden"}, 403
        if user.role == Role.STAFF and (not sr.assignment or sr.assignment.staff_id != user.id):
            return {"message": "Forbidden"}, 403
        return sr.to_dict(), 200

    @jwt_required()
    def put(self, request_id):
        user = _current_user()
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404

        if user.role == Role.CITIZEN:
            if sr.citizen_id != user.id:
                return {"message": "Forbidden"}, 403
            if sr.status not in [RequestStatus.PENDING]:
                return {"message": "Cannot edit a request that has been picked up"}, 400
        if user.role == Role.STAFF and (not sr.assignment or sr.assignment.staff_id != user.id):
            return {"message": "Forbidden"}, 403

        data = request.get_json() or {}
        if "priority" in data and data["priority"] not in Priority.ALL:
            return {"message": "Invalid priority"}, 400
        for field in ["title", "description", "address"]:
            if field in data and not str(data[field] or "").strip():
                return {"message": f"{field.title()} cannot be blank"}, 400
        editable = ["title", "description", "address", "ward", "priority", "admin_notes"]
        for field in editable:
            if field in data:
                if user.role == Role.CITIZEN and field == "admin_notes":
                    continue
                setattr(sr, field, data[field].strip() if isinstance(data[field], str) else data[field])

        sr.updated_at = now_ist()
        db.session.commit()
        return sr.to_dict(), 200

    @jwt_required()
    def delete(self, request_id):
        user = _current_user()
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404
        if user.role == Role.CITIZEN:
            if sr.citizen_id != user.id or sr.status != RequestStatus.PENDING:
                return {"message": "Cannot delete this request"}, 403
        elif user.role == Role.STAFF:
            return {"message": "Forbidden"}, 403
        elif user.role == Role.ADMIN and sr.status in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
            return {"message": "Cannot delete a resolved/closed request — it's part of the public accountability record"}, 400

        db.session.delete(sr)
        db.session.commit()
        return {"message": "Request deleted"}, 200


class RequestStatusResource(Resource):
    @jwt_required()
    def put(self, request_id):
        user = _current_user()
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        new_status = data.get("status")

        if not new_status or new_status not in RequestStatus.ALL:
            return {"message": "Invalid status"}, 400

        if new_status == RequestStatus.ON_HOLD_WEATHER and user.role != Role.ADMIN:
            return {"message": "Only an admin can place a request on hold"}, 403

        if new_status == RequestStatus.REJECTED:
            if user.role != Role.ADMIN:
                return {"message": "Only an admin can reject a request"}, 403
            if sr.status != RequestStatus.PENDING:
                return {"message": "Only a pending (unassigned) request can be rejected"}, 400
            if not (data.get("admin_notes") or "").strip():
                return {"message": "A reason is required to reject a request"}, 400

        if user.role == Role.CITIZEN:
            if sr.citizen_id != user.id:
                return {"message": "Forbidden"}, 403
            if sr.status != RequestStatus.RESOLVED or new_status not in [RequestStatus.CLOSED, RequestStatus.REOPENED]:
                return {"message": "Citizens can only close or reopen resolved requests"}, 400
            if new_status == RequestStatus.REOPENED and sr.reopen_count >= 2:
                return {"message": "Already reopened twice. Please contact the department for further help."}, 400
            rating = data.get("rating")
            if rating is not None and (not isinstance(rating, int) or rating < 1 or rating > 5):
                return {"message": "Rating must be an integer from 1 to 5"}, 400

        if user.role == Role.STAFF:
            if not sr.assignment or sr.assignment.staff_id != user.id:
                return {"message": "Not your assignment"}, 403
            if sr.status == RequestStatus.CLOSED:
                return {"message": "Citizen has closed this request — it can no longer be changed"}, 400
            if sr.status == RequestStatus.ON_HOLD_WEATHER:
                return {"message": "This request is on hold for weather restrictions — an admin needs to resume it first"}, 400
            if sr.status == RequestStatus.RESOLVED:
                return {"message": "This request is already resolved — no further updates until the citizen reopens or closes it"}, 400
            if sr.status == RequestStatus.REJECTED:
                return {"message": "This request was rejected and can no longer be updated"}, 400
            allowed = [RequestStatus.IN_PROGRESS, RequestStatus.RESOLVED]
            if new_status not in allowed:
                return {"message": "Staff can only mark in_progress or resolved"}, 400

        old_status = sr.status
        sr.status = new_status
        if data.get("admin_notes"):
            sr.admin_notes = data["admin_notes"]
        # Evidence photos are proof-of-completion — only accepted the moment a request is being resolved.
        if data.get("evidence_urls") and new_status == RequestStatus.RESOLVED:
            sr.evidence_urls = data["evidence_urls"]

        if new_status == RequestStatus.ON_HOLD_WEATHER:
            sr.hold_reason = (data.get("hold_reason") or "").strip() or "Physical work is paused due to weather restrictions (e.g. rainy season) and will resume once conditions improve."
        elif old_status == RequestStatus.ON_HOLD_WEATHER:
            sr.hold_reason = None

        if new_status == RequestStatus.CLOSED and user.role == Role.CITIZEN:
            if data.get("rating") is not None:
                sr.rating = data["rating"]
            if data.get("feedback"):
                sr.feedback = data["feedback"].strip()

        if new_status in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
            sr.resolved_at = now_ist()
            if sr.assignment:
                sr.assignment.completed_at = now_ist()

        if new_status == RequestStatus.REOPENED:
            sr.reopen_count += 1
            if sr.assignment:
                sr.assignment.completed_at = None

        sr.updated_at = now_ist()

        if new_status == RequestStatus.REJECTED:
            reason = data.get("admin_notes", "").strip()
            msg = f"Your request '{sr.title}' was rejected." + (f" Reason: {reason}" if reason else "")
            _notify(sr.citizen_id, "Request Rejected", msg, "status")
        elif new_status == RequestStatus.REOPENED:
            msg = f"{user.name} reopened request '{sr.title}' — the work wasn't satisfactory. Please review again."
            if sr.assignment:
                _notify(sr.assignment.staff_id, "Request Reopened", msg, "status")
            for admin in User.query.filter_by(role=Role.ADMIN).all():
                _notify(admin.id, "Request Reopened", msg, "status")
        elif new_status == RequestStatus.ON_HOLD_WEATHER:
            msg = f"Your request '{sr.title}' has been put on hold. {sr.hold_reason}"
            _notify(sr.citizen_id, "Request On Hold — Weather Restrictions", msg, "warning")
            if sr.assignment:
                _notify(sr.assignment.staff_id, "Request On Hold", msg, "warning")
        elif old_status == RequestStatus.ON_HOLD_WEATHER:
            msg = f"Work on your request '{sr.title}' has resumed."
            _notify(sr.citizen_id, "Request Resumed", msg, "info")
            if sr.assignment:
                _notify(sr.assignment.staff_id, "Request Resumed", msg, "info")
        else:
            _notify(sr.citizen_id, "Request Status Updated",
                    f"Your request '{sr.title}' status changed from {old_status} to {new_status}.",
                    "status")

        db.session.commit()
        return sr.to_dict(), 200


class RequestBudgetTagResource(Resource):
    """Admin/ward-member toggle for flagging a verified complaint as 'Pending Funds',
    so it can be compiled into a list for the next budget allocation meeting."""
    @jwt_required()
    def put(self, request_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        if "pending_funds" not in data:
            return {"message": "Missing: pending_funds"}, 400
        sr.pending_funds = bool(data["pending_funds"])
        sr.updated_at = now_ist()
        db.session.commit()
        return sr.to_dict(), 200


# ── Complaint community visibility & upvotes ──────────────────────────────────

class RequestSimilarResource(Resource):
    """Looks for existing open complaints that might be the same issue, so a
    citizen can upvote/"me too" an existing one instead of filing a duplicate.
    Uses to_public_dict() — this runs before the complaint is even submitted,
    so the citizen is looking at other citizens' complaints; no PII exposure."""
    @jwt_required()
    def post(self):
        user = _current_user()
        data = request.get_json() or {}
        category = data.get("category")
        description = (data.get("description") or "").strip()
        ward = data.get("ward")
        if not category or not description:
            return [], 200
        try:
            lat = float(data["latitude"]) if data.get("latitude") is not None else None
            lng = float(data["longitude"]) if data.get("longitude") is not None else None
        except (TypeError, ValueError):
            lat = lng = None
        matches = _find_similar(category, ward, description, lat, lng)
        upvoted_ids = {u.request_id for u in ComplaintUpvote.query.filter_by(user_id=user.id)}
        result = []
        for m in matches:
            d = m.to_public_dict()
            d["upvoted_by_me"] = m.id in upvoted_ids
            result.append(d)
        return result, 200


class RequestUpvoteResource(Resource):
    """'Me too' toggle — lets a citizen flag they're facing the same issue
    without filing a duplicate complaint. Does not require ownership."""
    @jwt_required()
    def post(self, request_id):
        user = _current_user()
        sr = db.session.get(ServiceRequest, request_id)
        if not sr:
            return {"message": "Not found"}, 404
        existing = ComplaintUpvote.query.filter_by(request_id=request_id, user_id=user.id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return {"upvoted": False, "upvotes_count": ComplaintUpvote.query.filter_by(request_id=request_id).count()}, 200
        db.session.add(ComplaintUpvote(request_id=request_id, user_id=user.id))
        db.session.commit()
        return {"upvoted": True, "upvotes_count": ComplaintUpvote.query.filter_by(request_id=request_id).count()}, 200


class RequestCommunityResource(Resource):
    """Read-only feed of complaints for the citizen Community Feed, scoped to
    the viewer's ward (falls back to all wards if the viewer has no ward).
    Uses to_public_dict() — never exposes another citizen's name/email/phone,
    same privacy bar as the public tracking endpoint (see to_public_dict)."""
    @jwt_required()
    def get(self):
        user = _current_user()
        q = ServiceRequest.query
        if user.ward:
            q = q.filter(ServiceRequest.ward == user.ward)
        complaints = q.order_by(ServiceRequest.created_at.desc()).limit(50).all()
        upvoted_ids = {u.request_id for u in ComplaintUpvote.query.filter_by(user_id=user.id)}
        result = []
        for c in complaints:
            d = c.to_public_dict()
            d["upvoted_by_me"] = c.id in upvoted_ids
            result.append(d)
        return result, 200


# ── Assignments ───────────────────────────────────────────────────────────────

class AssignmentListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        if user.role == Role.CITIZEN:
            return {"message": "Forbidden"}, 403
        if user.role == Role.STAFF:
            assignments = Assignment.query.filter_by(staff_id=user.id).all()
        else:
            assignments = Assignment.query.all()
        return [a.to_dict() for a in assignments], 200

    @jwt_required()
    def post(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        admin = _current_user()
        data = request.get_json() or {}
        required = ["request_id", "staff_id"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {"message": f"Missing: {', '.join(missing)}"}, 400

        sr = db.session.get(ServiceRequest, data["request_id"])
        if not sr:
            return {"message": "Request not found"}, 404
        if sr.status in [RequestStatus.RESOLVED, RequestStatus.CLOSED, RequestStatus.REJECTED]:
            return {"message": "Cannot assign a completed/closed request"}, 400

        staff = db.session.get(User, data["staff_id"])
        if not staff or staff.role != Role.STAFF:
            return {"message": "Invalid staff member"}, 400
        if not staff.is_active:
            return {"message": "Cannot assign to a deactivated officer"}, 400
        # An admin can deliberately assign across departments to correct a
        # miscategorized complaint — the chosen officer's department then
        # becomes the request's department of record going forward.
        if staff.department != sr.get_department():
            sr.department_override = staff.department

        # Assignment.request_id is unique=True — there is always at most one
        # assignment per request, so a re-assignment must UPDATE that row in
        # place rather than delete-then-insert. SQLAlchemy's unit of work
        # flushes INSERTs before DELETEs in the same commit, so a delete+
        # insert pair against a unique column trips the constraint while
        # both rows briefly coexist (IntegrityError on request_id).
        if sr.assignment:
            prev_staff_id = sr.assignment.staff_id
            assignment = sr.assignment
            assignment.staff_id = staff.id
            assignment.assigned_by = admin.id
            assignment.notes = data.get("notes", "")
            assignment.assigned_at = now_ist()
            assignment.completed_at = None
            sr.status = RequestStatus.REASSIGNED
            sr.admin_notes = data.get("notes") or f"Reassigned to {staff.name} ({staff.department})"
            sr.updated_at = now_ist()

            if prev_staff_id != staff.id:
                _notify(prev_staff_id, "Request Reassigned",
                        f"Request '{sr.title}' has been reassigned to another officer.", "assignment")
            _notify(staff.id, "New Assignment",
                    f"You've been assigned request: '{sr.title}' (Priority: {sr.priority})", "assignment")
            _notify(sr.citizen_id, "Request Reassigned",
                    f"Your request '{sr.title}' has been reassigned to a different officer.", "status")

            db.session.commit()
            return assignment.to_dict(), 200

        assignment = Assignment(
            request_id=sr.id,
            staff_id=staff.id,
            assigned_by=admin.id,
            notes=data.get("notes", ""),
        )
        db.session.add(assignment)
        sr.status = RequestStatus.ASSIGNED
        sr.admin_notes = data.get("notes") or f"Assigned to {staff.name} ({staff.department})"
        sr.updated_at = now_ist()

        _notify(staff.id, "New Assignment",
                f"You've been assigned request: '{sr.title}' (Priority: {sr.priority})", "assignment")
        _notify(sr.citizen_id, "Request Assigned",
                f"Your request '{sr.title}' has been assigned to a staff member.", "status")

        db.session.commit()
        return assignment.to_dict(), 201


class AssignmentResource(Resource):
    @jwt_required()
    def put(self, assignment_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        assignment = db.session.get(Assignment, assignment_id)
        if not assignment:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        if "staff_id" in data:
            staff = db.session.get(User, data["staff_id"])
            if not staff or staff.role != Role.STAFF:
                return {"message": "Invalid staff member"}, 400
            if not staff.is_active:
                return {"message": "Cannot assign to a deactivated officer"}, 400
            if staff.department != assignment.request.get_department():
                assignment.request.department_override = staff.department
            assignment.staff_id = staff.id
        if "notes" in data:
            assignment.notes = data["notes"]
        db.session.commit()
        return assignment.to_dict(), 200


# ── Facilities ────────────────────────────────────────────────────────────────

class FacilityListResource(Resource):
    @jwt_required()
    def get(self):
        active_only = request.args.get("active", "true").lower() == "true"
        user = _current_user()
        q = Facility.query
        if active_only and user.role == Role.CITIZEN:
            q = q.filter_by(is_active=True)
        facilities = q.order_by(Facility.name).all()
        return [f.to_dict() for f in facilities], 200

    @jwt_required()
    def post(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        data = request.get_json() or {}
        required = ["name", "facility_type", "address", "capacity"]
        missing = [f for f in required if f not in data]
        if missing:
            return {"message": f"Missing: {', '.join(missing)}"}, 400

        try:
            capacity = int(data["capacity"])
            fee_per_hour = float(data.get("fee_per_hour", 0))
        except (TypeError, ValueError):
            return {"message": "Capacity and fee per hour must be numbers"}, 400
        if capacity < 1 or capacity > 100000:
            return {"message": "Capacity must be between 1 and 100000"}, 400
        if fee_per_hour < 0:
            return {"message": "Fee per hour cannot be negative"}, 400
        if not data["name"].strip() or not data["address"].strip():
            return {"message": "Name and address cannot be blank"}, 400

        facility = Facility(
            name=data["name"].strip(),
            facility_type=data["facility_type"].strip(),
            address=data["address"].strip(),
            ward=data.get("ward", ""),
            capacity=capacity,
            description=data.get("description", ""),
            amenities=data.get("amenities", ""),
            fee_per_hour=fee_per_hour,
            image_urls=data.get("image_urls") or [],
        )
        db.session.add(facility)
        db.session.commit()
        return facility.to_dict(), 201


class FacilityResource(Resource):
    @jwt_required()
    def get(self, facility_id):
        f = db.session.get(Facility, facility_id)
        if not f:
            return {"message": "Not found"}, 404
        return f.to_dict(), 200

    @jwt_required()
    def put(self, facility_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        f = db.session.get(Facility, facility_id)
        if not f:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        if "capacity" in data:
            try:
                data["capacity"] = int(data["capacity"])
            except (TypeError, ValueError):
                return {"message": "Capacity must be a number"}, 400
            if data["capacity"] < 1 or data["capacity"] > 100000:
                return {"message": "Capacity must be between 1 and 100000"}, 400
        if "fee_per_hour" in data:
            try:
                data["fee_per_hour"] = float(data["fee_per_hour"])
            except (TypeError, ValueError):
                return {"message": "Fee per hour must be a number"}, 400
            if data["fee_per_hour"] < 0:
                return {"message": "Fee per hour cannot be negative"}, 400
        for field in ["name", "facility_type", "address"]:
            if field in data and not str(data[field] or "").strip():
                return {"message": f"{field.replace('_', ' ').title()} cannot be blank"}, 400
        for field in ["name", "facility_type", "address", "ward", "capacity",
                      "description", "amenities", "fee_per_hour", "image_urls", "is_active"]:
            if field in data:
                setattr(f, field, data[field])
        db.session.commit()
        return f.to_dict(), 200

    @jwt_required()
    def delete(self, facility_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        f = db.session.get(Facility, facility_id)
        if not f:
            return {"message": "Not found"}, 404
        # Bookings (and their payments) cascade-delete with the facility, which would
        # silently wipe citizens' payment/transaction history. Block deletion entirely
        # if the facility has ANY booking history, not just active ones — admin should
        # deactivate instead to preserve records.
        total_bookings = f.bookings.count()
        if total_bookings > 0:
            return {"message": "Cannot delete a facility with existing bookings — deactivate it instead to preserve booking/payment history"}, 400

        db.session.delete(f)
        db.session.commit()
        return {"message": "Facility deleted"}, 200


class FacilityAvailabilityResource(Resource):
    @jwt_required()
    def get(self, facility_id):
        booking_date_str = request.args.get("date")
        if not booking_date_str:
            return {"message": "Date required"}, 400

        try:
            booking_date = _parse_date(booking_date_str)
        except ValueError:
            return {"message": "Invalid date format. Use YYYY-MM-DD"}, 400

        bookings = Booking.query.filter(
            Booking.facility_id == facility_id,
            Booking.booking_date == booking_date,
            Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED])
        ).all()

        return {
            "facility_id": facility_id,
            "date": booking_date_str,
            "booked_slots": [
                {"start": b.start_time.strftime("%H:%M"), "end": b.end_time.strftime("%H:%M"), "status": b.status}
                for b in bookings
            ]
        }, 200


# ── Bookings ──────────────────────────────────────────────────────────────────

class BookingListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        if user.role == Role.STAFF:
            return {"message": "Forbidden"}, 403
        status_filter = request.args.get("status")

        if user.role == Role.CITIZEN:
            q = Booking.query.filter_by(citizen_id=user.id)
        else:
            q = Booking.query

        if status_filter:
            q = q.filter_by(status=status_filter)

        bookings = q.order_by(Booking.created_at.desc()).all()
        return [b.to_dict() for b in bookings], 200

    @jwt_required()
    def post(self):
        user = _current_user()
        err = _require_role(Role.CITIZEN)
        if err:
            return err

        data = request.get_json() or {}
        required = ["facility_id", "booking_date", "start_time", "end_time", "purpose"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {"message": f"Missing: {', '.join(missing)}"}, 400

        facility = db.session.get(Facility, data["facility_id"])
        if not facility or not facility.is_active:
            return {"message": "Facility not found or inactive"}, 404

        try:
            booking_date = _parse_date(data["booking_date"])
            start_time = _parse_time(data["start_time"])
            end_time = _parse_time(data["end_time"])
        except ValueError:
            return {"message": "Invalid date/time format. Use YYYY-MM-DD and HH:MM"}, 400

        if booking_date < date.today():
            return {"message": "Cannot book for a past date"}, 400

        if booking_date == now_ist().date() and start_time <= now_ist().time():
            return {"message": "Cannot book a time slot that has already passed today"}, 400

        if start_time >= end_time:
            return {"message": "Start time must be before end time"}, 400

        start_hour = start_time.hour
        end_hour = end_time.hour + (1 if end_time.minute > 0 else 0)
        if start_hour < 6 or end_hour > 22:
            return {"message": "Bookings allowed only between 06:00 and 22:00"}, 400

        try:
            attendees = int(data.get("attendees", 1))
        except (TypeError, ValueError):
            return {"message": "Attendees must be a number"}, 400
        if attendees < 1:
            return {"message": "Attendees must be at least 1"}, 400
        if attendees > facility.capacity:
            return {"message": f"Attendees exceed facility capacity of {facility.capacity}"}, 400

        if _booking_conflicts(facility.id, booking_date, start_time, end_time):
            return {"message": "This time slot is already booked"}, 409

        fee = _calculate_fee(facility, start_time, end_time)

        booking = Booking(
            facility_id=facility.id,
            citizen_id=user.id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            purpose=data["purpose"].strip(),
            attendees=attendees,
            fee=fee,
        )
        db.session.add(booking)

        if fee > 0:
            payment = Payment(
                booking_id=None,
                citizen_id=user.id,
                amount=fee,
            )
            db.session.flush()
            payment.booking_id = booking.id
            db.session.add(payment)

        admins = User.query.filter_by(role=Role.ADMIN).all()
        for admin in admins:
            _notify(admin.id, "New Facility Booking",
                    f"{user.name} has requested to book {facility.name} on {booking_date}", "booking")

        db.session.commit()
        return booking.to_dict(), 201


class BookingResource(Resource):
    @jwt_required()
    def get(self, booking_id):
        user = _current_user()
        b = db.session.get(Booking, booking_id)
        if not b:
            return {"message": "Not found"}, 404
        if user.role == Role.CITIZEN and b.citizen_id != user.id:
            return {"message": "Forbidden"}, 403
        return b.to_dict(), 200

    @jwt_required()
    def delete(self, booking_id):
        user = _current_user()
        b = db.session.get(Booking, booking_id)
        if not b:
            return {"message": "Not found"}, 404

        if user.role == Role.CITIZEN:
            if b.citizen_id != user.id:
                return {"message": "Forbidden"}, 403
            if b.status not in [BookingStatus.PENDING]:
                return {"message": "Can only cancel pending bookings"}, 400
        elif user.role == Role.STAFF:
            return {"message": "Forbidden"}, 403

        b.status = BookingStatus.CANCELLED
        if b.payment and b.payment.status == PaymentStatus.PAID:
            b.payment.status = PaymentStatus.REFUNDED
            _notify(b.citizen_id, "Booking Cancelled & Refund Initiated",
                    f"Your booking for {b.facility.name} was cancelled. Refund of Rs.{b.fee} initiated.", "refund")
        else:
            _notify(b.citizen_id, "Booking Cancelled",
                    f"Your booking for {b.facility.name} on {b.booking_date} was cancelled.", "booking")

        db.session.commit()
        return {"message": "Booking cancelled"}, 200


class BookingStatusResource(Resource):
    @jwt_required()
    def put(self, booking_id):
        err = _require_role(Role.ADMIN, Role.STAFF)
        if err:
            return err

        b = db.session.get(Booking, booking_id)
        if not b:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        new_status = data.get("status")

        valid_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCELLED, BookingStatus.COMPLETED]
        if new_status not in valid_statuses:
            return {"message": "Invalid status"}, 400
        if b.status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED]:
            return {"message": f"A {b.status} booking can no longer be changed"}, 400

        user = _current_user()
        if user.role == Role.STAFF and new_status not in [BookingStatus.COMPLETED]:
            return {"message": "Staff can only mark bookings as completed"}, 403

        b.status = new_status
        if data.get("admin_notes"):
            b.admin_notes = data["admin_notes"]

        if new_status == BookingStatus.CANCELLED and b.payment and b.payment.status == PaymentStatus.PAID:
            b.payment.status = PaymentStatus.REFUNDED
            _notify(b.citizen_id, "Booking Cancelled & Refund Initiated",
                    f"Your booking for {b.facility.name} was cancelled. Refund of Rs.{b.fee} initiated.", "refund")
        else:
            status_msgs = {
                BookingStatus.CONFIRMED: f"Your booking for {b.facility.name} on {b.booking_date} is confirmed!",
                BookingStatus.CANCELLED: f"Your booking for {b.facility.name} on {b.booking_date} was cancelled.",
                BookingStatus.COMPLETED: f"Your booking for {b.facility.name} is marked as completed.",
            }
            if new_status in status_msgs:
                _notify(b.citizen_id, f"Booking {new_status.title()}", status_msgs[new_status], "booking")

        db.session.commit()
        return b.to_dict(), 200


# ── Payments ──────────────────────────────────────────────────────────────────

class PaymentListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        if user.role == Role.STAFF:
            return {"message": "Forbidden"}, 403
        if user.role == Role.CITIZEN:
            payments = Payment.query.filter_by(citizen_id=user.id).all()
        else:
            payments = Payment.query.all()
        return [p.to_dict() for p in payments], 200


class PaymentPayResource(Resource):
    @jwt_required()
    def post(self, payment_id):
        user = _current_user()
        if user.role == Role.STAFF:
            return {"message": "Forbidden"}, 403
        payment = db.session.get(Payment, payment_id)
        if not payment:
            return {"message": "Not found"}, 404

        if payment.citizen_id != user.id and user.role == Role.CITIZEN:
            return {"message": "Forbidden"}, 403

        if payment.status != PaymentStatus.PENDING:
            return {"message": f"Payment is already {payment.status}"}, 400

        data = request.get_json() or {}
        method = data.get("method", "online")
        if method not in ["online", "upi", "card", "netbanking"]:
            return {"message": "Invalid payment method"}, 400

        import uuid
        payment.status = PaymentStatus.PAID
        payment.method = method
        payment.transaction_ref = f"TXN-{uuid.uuid4().hex[:10].upper()}"
        payment.paid_at = now_ist()

        booking = payment.booking
        if booking and booking.status == BookingStatus.PENDING:
            booking.status = BookingStatus.CONFIRMED
            _notify(booking.citizen_id, "Payment Successful",
                    f"Payment of Rs.{payment.amount} for {booking.facility.name} received. Booking confirmed!", "payment")

            admins = User.query.filter_by(role=Role.ADMIN).all()
            for admin in admins:
                _notify(admin.id, "Payment Received",
                        f"{user.name} paid Rs.{payment.amount} for {booking.facility.name}", "payment")

        db.session.commit()
        return payment.to_dict(), 200


# ── Notifications ─────────────────────────────────────────────────────────────

class NotificationListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        notifications = Notification.query.filter_by(user_id=user.id)\
            .order_by(Notification.created_at.desc()).limit(50).all()
        unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        return {"notifications": [n.to_dict() for n in notifications], "unread_count": unread}, 200


class NotificationReadResource(Resource):
    @jwt_required()
    def put(self, notif_id):
        user = _current_user()
        if notif_id == 0:
            Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
        else:
            n = db.session.get(Notification, notif_id)
            if not n:
                return {"message": "Not found"}, 404
            if n.user_id != user.id:
                return {"message": "Forbidden"}, 403
            n.is_read = True
        db.session.commit()
        return {"message": "Marked as read"}, 200


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()

        if user.role == Role.CITIZEN:
            my_requests = ServiceRequest.query.filter_by(citizen_id=user.id)
            my_bookings = Booking.query.filter_by(citizen_id=user.id)
            pending_payments = Payment.query.filter_by(citizen_id=user.id, status=PaymentStatus.PENDING).count()
            return {
                "requests": {
                    "total": my_requests.count(),
                    "pending": my_requests.filter_by(status=RequestStatus.PENDING).count(),
                    "in_progress": my_requests.filter(ServiceRequest.status.in_(
                        [RequestStatus.ASSIGNED, RequestStatus.REASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.REOPENED, RequestStatus.ON_HOLD_WEATHER])).count(),
                    "resolved": my_requests.filter_by(status=RequestStatus.RESOLVED).count(),
                },
                "bookings": {
                    "total": my_bookings.count(),
                    "pending": my_bookings.filter_by(status=BookingStatus.PENDING).count(),
                    "confirmed": my_bookings.filter_by(status=BookingStatus.CONFIRMED).count(),
                },
                "pending_payments": pending_payments,
                "unread_notifications": Notification.query.filter_by(user_id=user.id, is_read=False).count(),
            }, 200

        elif user.role == Role.STAFF:
            my_assignments = Assignment.query.filter_by(staff_id=user.id)
            assigned_ids = [a.request_id for a in my_assignments.all()]
            my_requests = ServiceRequest.query.filter(ServiceRequest.id.in_(assigned_ids))
            return {
                "assignments": {
                    "total": my_assignments.count(),
                    "active": my_requests.filter(ServiceRequest.status.in_(
                        [RequestStatus.ASSIGNED, RequestStatus.REASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.REOPENED, RequestStatus.ON_HOLD_WEATHER])).count(),
                    "pending": my_requests.filter(ServiceRequest.status.in_(
                        [RequestStatus.ASSIGNED, RequestStatus.REASSIGNED, RequestStatus.REOPENED, RequestStatus.ON_HOLD_WEATHER])).count(),
                    "in_progress": my_requests.filter_by(status=RequestStatus.IN_PROGRESS).count(),
                    "resolved": my_requests.filter_by(status=RequestStatus.RESOLVED).count(),
                },
                "recent": [r.to_dict() for r in my_requests.order_by(ServiceRequest.created_at.desc()).limit(5).all()],
                "unread_notifications": Notification.query.filter_by(user_id=user.id, is_read=False).count(),
            }, 200

        else:  # admin
            return {
                "requests": {
                    "total": ServiceRequest.query.count(),
                    "pending": ServiceRequest.query.filter_by(status=RequestStatus.PENDING).count(),
                    "assigned": ServiceRequest.query.filter_by(status=RequestStatus.ASSIGNED).count(),
                    "reassigned": ServiceRequest.query.filter_by(status=RequestStatus.REASSIGNED).count(),
                    "in_progress": ServiceRequest.query.filter_by(status=RequestStatus.IN_PROGRESS).count(),
                    "resolved": ServiceRequest.query.filter_by(status=RequestStatus.RESOLVED).count(),
                    "closed": ServiceRequest.query.filter_by(status=RequestStatus.CLOSED).count(),
                    "reopened": ServiceRequest.query.filter_by(status=RequestStatus.REOPENED).count(),
                    "on_hold_weather": ServiceRequest.query.filter_by(status=RequestStatus.ON_HOLD_WEATHER).count(),
                    "pending_funds": ServiceRequest.query.filter_by(pending_funds=True).count(),
                },
                "bookings": {
                    "total": Booking.query.count(),
                    "pending": Booking.query.filter_by(status=BookingStatus.PENDING).count(),
                    "confirmed": Booking.query.filter_by(status=BookingStatus.CONFIRMED).count(),
                },
                "users": {
                    "total": User.query.count(),
                    "citizens": User.query.filter_by(role=Role.CITIZEN).count(),
                    "staff": User.query.filter_by(role=Role.STAFF).count(),
                },
                "payments": {
                    "collected": db.session.query(db.func.sum(Payment.amount))
                        .filter_by(status=PaymentStatus.PAID).scalar() or 0,
                    "pending": Payment.query.filter_by(status=PaymentStatus.PENDING).count(),
                },
                "facilities": {
                    "total": Facility.query.count(),
                    "active": Facility.query.filter_by(is_active=True).count(),
                },
                "unread_notifications": Notification.query.filter_by(user_id=user.id, is_read=False).count(),
            }, 200


# ── Admin: Users ──────────────────────────────────────────────────────────────

class AdminUserListResource(Resource):
    @jwt_required()
    def get(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        role_filter = request.args.get("role")
        q = User.query
        if role_filter:
            q = q.filter_by(role=role_filter)
        users = q.order_by(User.created_at.desc()).all()
        return [u.to_dict() for u in users], 200


class AdminUserResource(Resource):
    @jwt_required()
    def put(self, user_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err

        user = db.session.get(User, user_id)
        if not user:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}

        if "role" in data:
            if data["role"] == Role.STAFF:
                return {"message": "Use Manage Officers to create staff accounts (requires a department)"}, 400
            if data["role"] in Role.ALL:
                user.role = data["role"]
        if "is_active" in data:
            user.is_active = bool(data["is_active"])
        if "ward" in data:
            user.ward = data["ward"]

        db.session.commit()
        return user.to_dict(), 200


class StaffListResource(Resource):
    @jwt_required()
    def get(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        staff = User.query.filter_by(role=Role.STAFF, is_active=True).all()
        return [u.to_dict() for u in staff], 200


# ── Departments ───────────────────────────────────────────────────────────────

class DepartmentListResource(Resource):
    def get(self):
        depts = Department.query.order_by(Department.id).all()
        return [d.to_dict() for d in depts], 200

    @jwt_required()
    def post(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        data = request.get_json() or {}
        name = (data.get("name") or "").strip()
        if not name:
            return {"message": "Name required"}, 400
        if Department.query.filter(db.func.lower(Department.name) == name.lower()).first():
            return {"message": "Department already exists"}, 409
        dept = Department(
            name=name,
            description=data.get("description", ""),
            officer_incharge_id=data.get("officer_incharge_id") or None,
        )
        db.session.add(dept)
        db.session.commit()
        return dept.to_dict(), 201


class DepartmentResource(Resource):
    @jwt_required()
    def put(self, dept_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        dept = db.session.get(Department, dept_id)
        if not dept:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        if "name" in data:
            new_name = (data["name"] or "").strip()
            if not new_name:
                return {"message": "Name cannot be blank"}, 400
            clash = Department.query.filter(
                db.func.lower(Department.name) == new_name.lower(),
                Department.id != dept.id,
            ).first()
            if clash:
                return {"message": "A department with this name already exists"}, 409
            dept.name = new_name
        if "description" in data:
            dept.description = data["description"]
        if "officer_incharge_id" in data:
            dept.officer_incharge_id = data["officer_incharge_id"] or None
        db.session.commit()
        return dept.to_dict(), 200

    @jwt_required()
    def delete(self, dept_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        dept = db.session.get(Department, dept_id)
        if not dept:
            return {"message": "Not found"}, 404
        db.session.delete(dept)
        db.session.commit()
        return {"message": "Deleted"}, 200


# ── Officers ──────────────────────────────────────────────────────────────────

class OfficerListResource(Resource):
    @jwt_required()
    def get(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        officers = User.query.filter_by(role=Role.STAFF).order_by(User.id).all()
        return [u.to_dict() for u in officers], 200

    @jwt_required()
    def post(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        data = request.get_json() or {}
        if not data.get("email") or not data.get("name") or not data.get("password"):
            return {"message": "Name, email and password required"}, 400
        invalid = _validate_person(data)
        if invalid:
            return invalid
        if User.query.filter_by(email=data["email"]).first():
            return {"message": "Email already in use"}, 409
        u = User(
            name=data["name"], email=data["email"], role=Role.STAFF,
            phone=data.get("phone", ""), ward=data.get("ward", ""),
            department=data.get("department", ""),
        )
        u.set_password(data["password"])
        db.session.add(u)
        db.session.commit()
        return u.to_dict(), 201


class OfficerResource(Resource):
    @jwt_required()
    def put(self, officer_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        u = db.session.get(User, officer_id)
        if not u or u.role != Role.STAFF:
            return {"message": "Not found"}, 404
        data = request.get_json() or {}
        if "name" in data and not NAME_RE.match((data["name"] or "").strip()):
            return {"message": "Please enter a valid name — letters only, numbers are not a name"}, 400
        if data.get("phone") and not PHONE_RE.match(data["phone"].strip()):
            return {"message": "Phone must be a valid 10-digit mobile number"}, 400
        for field in ["name", "phone", "department"]:
            if field in data:
                setattr(u, field, (data[field] or "").strip() if isinstance(data[field], str) else data[field])
        if data.get("is_active") is not None:
            u.is_active = data["is_active"]
        db.session.commit()
        return u.to_dict(), 200

    @jwt_required()
    def delete(self, officer_id):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        u = db.session.get(User, officer_id)
        if not u or u.role != Role.STAFF:
            return {"message": "Not found"}, 404
        u.is_active = False
        open_count = (
            ServiceRequest.query.join(Assignment)
            .filter(Assignment.staff_id == u.id,
                    ServiceRequest.status.in_([RequestStatus.ASSIGNED, RequestStatus.REASSIGNED, RequestStatus.IN_PROGRESS, RequestStatus.REOPENED]))
            .count()
        )
        db.session.commit()
        msg = "Officer deactivated"
        if open_count:
            msg += f". They had {open_count} open complaint(s) — reassign them from Manage Complaints."
        return {"message": msg, "open_complaints": open_count}, 200


# ── Public Track ──────────────────────────────────────────────────────────────

class PublicTrackResource(Resource):
    def get(self):
        cmp_id = request.args.get("id", "").strip().upper()
        if not cmp_id:
            return {"message": "Provide complaint ID"}, 400
        try:
            req_id = int(cmp_id.replace("CMP", "").lstrip("0") or "0")
        except ValueError:
            return {"message": "Invalid ID format"}, 400
        if req_id <= 0 or req_id > 2**31:
            return {"message": "Complaint not found"}, 404
        r = db.session.get(ServiceRequest, req_id)
        if not r:
            return {"message": "Complaint not found"}, 404
        return r.to_public_dict(), 200


class PublicStatsResource(Resource):
    """Aggregate counts only (no PII, no per-complaint detail) for the
    logged-out landing page's stats section."""
    def get(self):
        return {
            "total_complaints": ServiceRequest.query.count(),
            "resolved": ServiceRequest.query.filter(ServiceRequest.status.in_(
                [RequestStatus.RESOLVED, RequestStatus.CLOSED])).count(),
            "in_progress": ServiceRequest.query.filter(ServiceRequest.status.in_(
                [RequestStatus.ASSIGNED, RequestStatus.REASSIGNED, RequestStatus.IN_PROGRESS,
                 RequestStatus.REOPENED, RequestStatus.ON_HOLD_WEATHER])).count(),
            "departments": Department.query.count(),
        }, 200


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportsResource(Resource):
    @jwt_required()
    def get(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        from datetime import timedelta

        today = now_ist().date()
        from_str = request.args.get("from")
        to_str = request.args.get("to")
        try:
            range_to = datetime.strptime(to_str, "%Y-%m-%d").date() if to_str else today
        except ValueError:
            range_to = today
        try:
            range_from = datetime.strptime(from_str, "%Y-%m-%d").date() if from_str else range_to - timedelta(days=13)
        except ValueError:
            range_from = range_to - timedelta(days=13)
        if range_from > range_to:
            range_from, range_to = range_to, range_from
        # cap the chart window so a huge range doesn't render hundreds of bars
        if (range_to - range_from).days > 60:
            range_from = range_to - timedelta(days=60)

        all_requests = ServiceRequest.query.filter(
            ServiceRequest.created_at >= datetime.combine(range_from, datetime.min.time()),
            ServiceRequest.created_at < datetime.combine(range_to + timedelta(days=1), datetime.min.time()),
        ).all()

        days = []
        span = (range_to - range_from).days
        for i in range(span + 1):
            d = range_from + timedelta(days=i)
            count = sum(1 for r in all_requests if r.created_at.date() == d)
            days.append({"date": d.strftime("%d %b"), "count": count})

        # Derive department buckets straight from DEPT_MAP so this never drifts
        # out of sync with the routing logic used for real assignment.
        dept_names = sorted(set(DEPT_MAP.values()))
        dept_perf = []
        for dept_name in dept_names:
            cats = [c for c, d in DEPT_MAP.items() if d == dept_name]
            total = sum(1 for r in all_requests if r.category in cats)
            resolved = sum(1 for r in all_requests if r.category in cats and r.status in ["resolved", "closed"])
            pct = round((resolved / total * 100) if total > 0 else 0)
            dept_perf.append({"name": dept_name, "total": total, "resolved": resolved, "pct": pct})
        return {
            "complaints_over_time": days,
            "department_performance": dept_perf,
            "total": len(all_requests),
            "by_status": {
                "pending": sum(1 for r in all_requests if r.status == "pending"),
                "in_progress": sum(1 for r in all_requests if r.status in ["assigned", "reassigned", "in_progress", "reopened", "on_hold_weather"]),
                "resolved": sum(1 for r in all_requests if r.status == "resolved"),
                "closed": sum(1 for r in all_requests if r.status == "closed"),
            }
        }, 200


# ── Community Posts ───────────────────────────────────────────────────────────

class PostListResource(Resource):
    @jwt_required()
    def get(self):
        user = _current_user()
        category = request.args.get("category")
        ward = request.args.get("ward")
        q = Post.query
        if category:
            q = q.filter_by(category=category)
        else:
            # The general community feed never mixes in official announcements —
            # those only ever show on the dedicated Announcements page.
            q = q.filter(Post.category != "announcement")
        if ward:
            q = q.filter_by(ward=ward)
        posts = q.order_by(Post.created_at.desc()).limit(50).all()
        return [p.to_dict(user.id) for p in posts], 200

    @jwt_required()
    def post(self):
        user = _current_user()
        data = request.get_json() or {}
        content = (data.get("content") or "").strip()
        if not content:
            return {"message": "Content required"}, 400
        # Only an admin can publish an official announcement — everyone else's
        # posts land in the regular community feed, announcement or not.
        category = data.get("category", "general")
        if category == "announcement" and user.role != Role.ADMIN:
            category = "general"
        post = Post(
            citizen_id=user.id,
            title=(data.get("title") or "").strip(),
            content=content,
            category=category,
            location=data.get("location", ""),
            ward=data.get("ward", user.ward or ""),
            image_urls=data.get("image_urls") or [],
            is_official=user.role in ["staff", "admin"],
        )
        db.session.add(post)
        db.session.commit()
        return post.to_dict(user.id), 201

    @jwt_required()
    def delete(self):
        err = _require_role(Role.ADMIN)
        if err:
            return err
        post_id = request.args.get("post_id")
        if not post_id:
            return {"message": "post_id required"}, 400
        try:
            post_id = int(post_id)
        except ValueError:
            return {"message": "post_id must be a number"}, 400
        p = db.session.get(Post, post_id)
        if not p:
            return {"message": "Not found"}, 404
        db.session.delete(p)
        db.session.commit()
        return {"message": "Deleted"}, 200


class PostResourceItem(Resource):
    @jwt_required()
    def delete(self, post_id):
        user = _current_user()
        p = db.session.get(Post, post_id)
        if not p:
            return {"message": "Not found"}, 404
        if user.role != Role.ADMIN and p.citizen_id != user.id:
            return {"message": "Forbidden"}, 403
        db.session.delete(p)
        db.session.commit()
        return {"message": "Deleted"}, 200


class PostLikeResource(Resource):
    @jwt_required()
    def post(self, post_id):
        user = _current_user()
        if not db.session.get(Post, post_id):
            return {"message": "Post not found"}, 404
        existing = PostLike.query.filter_by(post_id=post_id, user_id=user.id).first()
        if existing:
            db.session.delete(existing)
            db.session.commit()
            return {"liked": False}, 200
        like = PostLike(post_id=post_id, user_id=user.id)
        db.session.add(like)
        db.session.commit()
        return {"liked": True}, 200


class PostCommentListResource(Resource):
    @jwt_required()
    def get(self, post_id):
        comments = PostComment.query.filter_by(post_id=post_id).order_by(PostComment.created_at).all()
        return [c.to_dict() for c in comments], 200

    @jwt_required()
    def post(self, post_id):
        user = _current_user()
        if not db.session.get(Post, post_id):
            return {"message": "Post not found"}, 404
        data = request.get_json() or {}
        content = (data.get("content") or "").strip()
        if not content:
            return {"message": "Content required"}, 400
        comment = PostComment(
            post_id=post_id,
            user_id=user.id,
            content=content,
            is_official=user.role in ["staff", "admin"],
        )
        db.session.add(comment)
        db.session.commit()
        return comment.to_dict(), 201


class PostCommentResource(Resource):
    @jwt_required()
    def delete(self, post_id, comment_id):
        user = _current_user()
        c = PostComment.query.filter_by(id=comment_id, post_id=post_id).first()
        if not c:
            return {"message": "Not found"}, 404
        if not (user.role == Role.ADMIN or c.user_id == user.id):
            return {"message": "You can only delete your own comments"}, 403
        db.session.delete(c)
        db.session.commit()
        return {"success": True}, 200


# ── Image Upload ──────────────────────────────────────────────────────────────

class UploadResource(Resource):
    @jwt_required()
    def post(self):
        if "file" not in request.files:
            return {"message": "No file provided"}, 400
        file = request.files["file"]
        if file.filename == "" or not _allowed_file(file.filename):
            return {"message": "Invalid file type"}, 400
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = os.path.join(os.path.dirname(__file__), "..", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        file.save(os.path.join(upload_folder, filename))
        return {"url": f"/api/uploads/{filename}"}, 201


class UploadServeResource(Resource):
    def get(self, filename):
        upload_folder = os.path.join(os.path.dirname(__file__), "..", "uploads")
        return send_from_directory(os.path.abspath(upload_folder), filename)


# ── AI Category Suggestion (Gemini) ──────────────────────────────────────────

class AISuggestResource(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json() or {}
        description = data.get("description", "").strip()
        if not description:
            return {"category": "", "message": "No description provided"}, 400

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            # Fallback: simple keyword matching if no API key
            desc_lower = description.lower()
            if any(w in desc_lower for w in ["road", "pothole", "footpath", "speed", "manhole"]):
                return {"category": "road", "confidence": "keyword_match"}
            if any(w in desc_lower for w in ["light", "electric", "power", "wire", "pole"]):
                return {"category": "electricity", "confidence": "keyword_match"}
            if any(w in desc_lower for w in ["water", "pipe", "leak", "drainage", "flood"]):
                return {"category": "water", "confidence": "keyword_match"}
            if any(w in desc_lower for w in ["garbage", "trash", "waste", "dirty", "sanit"]):
                return {"category": "sanitation", "confidence": "keyword_match"}
            if any(w in desc_lower for w in ["park", "playground", "bench", "garden", "tree", "swing", "slide"]):
                return {"category": "parks", "confidence": "keyword_match"}
            return {"category": "other", "confidence": "keyword_match"}

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = (
                f"You are a civic complaint classifier. Classify this complaint into exactly one category.\n"
                f"Categories: road, water, electricity, sanitation, waste, parks, maintenance, other\n"
                f"Complaint: \"{description}\"\n"
                f"Reply with only the category word, nothing else."
            )
            result = model.generate_content(prompt)
            category = result.text.strip().lower().split()[0]
            valid = {"road", "water", "electricity", "sanitation", "waste", "parks", "maintenance", "other"}
            if category not in valid:
                category = "other"
            return {"category": category, "confidence": "ai"}
        except Exception as e:
            return {"category": "other", "confidence": "error", "message": str(e)}


class AIExtractFromImageResource(Resource):
    """Reads a photo of a handwritten/printed complaint note and extracts
    structured fields (category, title, description, address, priority) using
    Gemini's vision model, so a citizen can fill the complaint form just by
    photographing a paper note instead of typing everything out."""
    @jwt_required()
    def post(self):
        if "file" not in request.files:
            return {"message": "No file provided"}, 400
        file = request.files["file"]
        if file.filename == "" or not _allowed_file(file.filename):
            return {"message": "Invalid file type"}, 400

        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return {"message": "AI scanning isn't configured on this server (no GEMINI_API_KEY)."}, 503

        image_bytes = file.read()
        mime_type = file.mimetype or "image/jpeg"

        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            prompt = (
                "This image is a photo of a handwritten or printed note describing a civic complaint "
                "(e.g. a broken streetlight, pothole, water leak). Read it and extract the details.\n"
                "Reply with ONLY a JSON object, no other text, in exactly this shape:\n"
                '{"category": "...", "title": "...", "description": "...", "address": "...", "priority": "..."}\n'
                "- category must be exactly one of: road, water, electricity, sanitation, waste, parks, maintenance, complaint, other\n"
                "- priority must be exactly one of: low, medium, high, urgent\n"
                "- title: a short summary (under 10 words)\n"
                "- description: the full complaint detail in your own words, based on what's written\n"
                "- address: the location/address mentioned in the note, or an empty string if none is mentioned\n"
                "If the image doesn't look like a complaint note at all, still do your best with whatever text is visible."
            )
            result = model.generate_content([
                prompt,
                {"mime_type": mime_type, "data": image_bytes},
            ])
            raw = result.text.strip()
            if raw.startswith("```"):
                raw = raw.strip("`").lstrip("json").strip()
            extracted = json.loads(raw)
        except json.JSONDecodeError:
            return {"message": "Could not read structured details from that image. Try a clearer photo, or fill the form manually."}, 422
        except Exception as e:
            return {"message": f"AI scan failed: {e}"}, 502

        category = str(extracted.get("category", "")).strip().lower()
        if category not in VALID_CATEGORIES:
            category = "other"
        priority = str(extracted.get("priority", "")).strip().lower()
        if priority not in Priority.ALL:
            priority = Priority.MEDIUM

        # Save the scanned photo so it can double as the complaint's attached photo
        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        upload_folder = os.path.join(os.path.dirname(__file__), "..", "uploads")
        os.makedirs(upload_folder, exist_ok=True)
        with open(os.path.join(upload_folder, filename), "wb") as f:
            f.write(image_bytes)

        return {
            "category": category,
            "title": str(extracted.get("title", "")).strip()[:200],
            "description": str(extracted.get("description", "")).strip(),
            "address": str(extracted.get("address", "")).strip(),
            "priority": priority,
            "image_url": f"/api/uploads/{filename}",
        }, 200


# ── Booking Invoice ───────────────────────────────────────────────────────────

class BookingInvoiceResource(Resource):
    @jwt_required()
    def get(self, booking_id):
        user = _current_user()
        booking = db.session.get(Booking, booking_id)
        if not booking:
            return {"message": "Booking not found"}, 404
        if user.role == Role.STAFF:
            return {"message": "Access denied"}, 403
        if user.role == Role.CITIZEN and booking.citizen_id != user.id:
            return {"message": "Access denied"}, 403

        # Calculate hours and total
        start = datetime.combine(booking.booking_date, booking.start_time)
        end = datetime.combine(booking.booking_date, booking.end_time)
        hours = (end - start).seconds / 3600
        fee_per_hour = booking.facility.fee_per_hour if booking.facility else 0
        subtotal = fee_per_hour * hours
        tax = round(subtotal * 0.18, 2)   # 18% GST
        total = round(subtotal + tax, 2)

        return {
            "invoice_number": f"INV-{booking.id:05d}",
            "booking_id": booking.id,
            "citizen_name": booking.citizen.name if booking.citizen else "",
            "citizen_phone": booking.citizen.phone if booking.citizen else "",
            "facility_name": booking.facility.name if booking.facility else "",
            "facility_address": booking.facility.address if booking.facility else "",
            "booking_date": booking.booking_date.isoformat(),
            "start_time": booking.start_time.strftime("%H:%M"),
            "end_time": booking.end_time.strftime("%H:%M"),
            "hours": hours,
            "purpose": booking.purpose,
            "attendees": booking.attendees,
            "fee_per_hour": fee_per_hour,
            "subtotal": round(subtotal, 2),
            "gst_18_percent": tax,
            "total": total,
            "payment_status": booking.payment.status if booking.payment else "free",
            "issued_at": now_ist().strftime("%d %b %Y, %I:%M %p"),
        }


# ── Register all resources ────────────────────────────────────────────────────

def register_resources(api):
    # Auth
    api.add_resource(RegisterResource, "/auth/register")
    api.add_resource(LoginResource, "/auth/login")
    api.add_resource(MeResource, "/auth/me")

    # Requests
    api.add_resource(RequestListResource, "/requests")
    api.add_resource(RequestResource, "/requests/<int:request_id>")
    api.add_resource(RequestStatusResource, "/requests/<int:request_id>/status")
    api.add_resource(RequestBudgetTagResource, "/requests/<int:request_id>/budget-tag")
    api.add_resource(RequestCommunityResource, "/requests/community")
    api.add_resource(RequestSimilarResource, "/requests/similar")
    api.add_resource(RequestUpvoteResource, "/requests/<int:request_id>/upvote")

    # Assignments
    api.add_resource(AssignmentListResource, "/assignments")
    api.add_resource(AssignmentResource, "/assignments/<int:assignment_id>")

    # Facilities
    api.add_resource(FacilityListResource, "/facilities")
    api.add_resource(FacilityResource, "/facilities/<int:facility_id>")
    api.add_resource(FacilityAvailabilityResource, "/facilities/<int:facility_id>/availability")

    # Bookings
    api.add_resource(BookingListResource, "/bookings")
    api.add_resource(BookingResource, "/bookings/<int:booking_id>")
    api.add_resource(BookingStatusResource, "/bookings/<int:booking_id>/status")

    # Payments
    api.add_resource(PaymentListResource, "/payments")
    api.add_resource(PaymentPayResource, "/payments/<int:payment_id>/pay")

    # Notifications
    api.add_resource(NotificationListResource, "/notifications")
    api.add_resource(NotificationReadResource, "/notifications/<int:notif_id>/read")

    # Dashboard
    api.add_resource(DashboardResource, "/dashboard")

    # Admin Users
    api.add_resource(AdminUserListResource, "/admin/users")
    api.add_resource(AdminUserResource, "/admin/users/<int:user_id>")
    api.add_resource(StaffListResource, "/admin/staff")

    # Departments
    api.add_resource(DepartmentListResource, "/departments")
    api.add_resource(DepartmentResource, "/departments/<int:dept_id>")

    # Officers
    api.add_resource(OfficerListResource, "/officers")
    api.add_resource(OfficerResource, "/officers/<int:officer_id>")

    # Public Track
    api.add_resource(PublicTrackResource, "/track")
    api.add_resource(PublicStatsResource, "/public-stats")

    # Reports
    api.add_resource(ReportsResource, "/reports")

    # Community Posts
    api.add_resource(PostListResource, "/posts")
    api.add_resource(PostResourceItem, "/posts/<int:post_id>")
    api.add_resource(PostLikeResource, "/posts/<int:post_id>/like")
    api.add_resource(PostCommentListResource, "/posts/<int:post_id>/comments")
    api.add_resource(PostCommentResource, "/posts/<int:post_id>/comments/<int:comment_id>")

    # File Upload
    api.add_resource(UploadResource, "/upload")
    api.add_resource(UploadServeResource, "/uploads/<string:filename>")

    # AI
    api.add_resource(AISuggestResource, "/ai/suggest")
    api.add_resource(AIExtractFromImageResource, "/ai/extract-from-image")

    # Invoice
    api.add_resource(BookingInvoiceResource, "/bookings/<int:booking_id>/invoice")
