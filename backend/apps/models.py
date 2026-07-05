import json
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

MAX_IMAGES = 3


def _dump_urls(urls):
    if urls is None:
        urls = []
    elif isinstance(urls, str):
        # A bare string would otherwise be iterated character-by-character.
        urls = [urls]
    elif not isinstance(urls, (list, tuple)):
        urls = []
    return json.dumps(list(urls)[:MAX_IMAGES])


def _load_urls(raw):
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return []


class Role:
    CITIZEN = "citizen"
    STAFF = "staff"
    ADMIN = "admin"
    ALL = [CITIZEN, STAFF, ADMIN]

class RequestStatus:
    PENDING = "pending"
    ASSIGNED = "assigned"
    REASSIGNED = "reassigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    REJECTED = "rejected"
    ON_HOLD_WEATHER = "on_hold_weather"
    ALL = [PENDING, ASSIGNED, REASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, REOPENED, REJECTED, ON_HOLD_WEATHER]

class Priority:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
    ALL = [LOW, MEDIUM, HIGH, URGENT]

class BookingStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus:
    PENDING = "pending"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"

class SubscriptionStatus:
    ACTIVE = "active"
    CANCELLED = "cancelled"

SUBSCRIPTION_FEE = 100.0  # Rs./month — flat, no GST (a membership fee, not a facility booking)

DEPT_MAP = {
    "road": "Road Maintenance",
    "electricity": "Electricity Department",
    "water": "Water Supply Department",
    "sanitation": "Sanitation Department",
    "waste": "Sanitation Department",
    "parks": "Parks & Public Spaces",
    "complaint": "General Affairs",
    "maintenance": "General Affairs",
    "other": "General Affairs",
}

IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    """Naive IST wall-clock — the app serves one Indian locality, and the
    host/WSL clock runs UTC, so timestamps are stored as IST directly and
    serialized with an explicit +05:30 offset in to_dict()."""
    return datetime.now(IST).replace(tzinfo=None)


class Department(db.Model):
    __tablename__ = "departments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    officer_incharge_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=now_ist)
    officer = db.relationship("User", foreign_keys=[officer_incharge_id])

    def to_dict(self):
        return {
            "id": self.id,
            "dept_id": f"DPT{str(self.id).zfill(2)}",
            "name": self.name,
            "description": self.description,
            "officer_incharge_id": self.officer_incharge_id,
            "officer_name": self.officer.name if self.officer else None,
            "officer_phone": self.officer.phone if self.officer else None,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=Role.CITIZEN)
    phone = db.Column(db.String(20))
    address = db.Column(db.String(300))
    ward = db.Column(db.String(50))
    department = db.Column(db.String(100))  # for staff: their department name
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)

    service_requests = db.relationship("ServiceRequest", foreign_keys="ServiceRequest.citizen_id", backref="citizen", lazy="dynamic")
    assignments = db.relationship("Assignment", foreign_keys="Assignment.staff_id", backref="staff", lazy="dynamic")
    bookings = db.relationship("Booking", foreign_keys="Booking.citizen_id", backref="citizen", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            "id": self.id,
            "officer_id": f"OFF{str(self.id).zfill(2)}",
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "phone": self.phone,
            "address": self.address,
            "ward": self.ward,
            "department": self.department,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class ServiceRequest(db.Model):
    __tablename__ = "service_requests"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    address = db.Column(db.String(300), nullable=False)
    ward = db.Column(db.String(50))
    latitude = db.Column(db.Float)   # geotag from the map picker (optional)
    longitude = db.Column(db.Float)
    priority = db.Column(db.String(20), nullable=False, default=Priority.MEDIUM)
    status = db.Column(db.String(30), nullable=False, default=RequestStatus.PENDING)
    admin_notes = db.Column(db.Text)
    _image_urls = db.Column("image_urls", db.Text)
    _evidence_urls = db.Column("evidence_urls", db.Text)
    rating = db.Column(db.Integer)        # 1-5, given by citizen when closing a resolved request
    feedback = db.Column(db.Text)
    reopen_count = db.Column(db.Integer, nullable=False, default=0)
    pending_funds = db.Column(db.Boolean, nullable=False, default=False)  # admin-tagged: needs budget allocation before work can proceed
    hold_reason = db.Column(db.Text)      # why a request is on_hold_weather (or other admin hold), shown to the citizen
    department_override = db.Column(db.String(100))  # set when admin assigns to an officer outside the category's default department (e.g. citizen miscategorized it)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    updated_at = db.Column(db.DateTime, default=now_ist, onupdate=now_ist, nullable=False)
    resolved_at = db.Column(db.DateTime)
    assignment = db.relationship("Assignment", backref="request", uselist=False, cascade="all, delete-orphan")
    upvotes = db.relationship("ComplaintUpvote", backref="request", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def image_urls(self):
        return _load_urls(self._image_urls)

    @image_urls.setter
    def image_urls(self, value):
        self._image_urls = _dump_urls(value)

    @property
    def evidence_urls(self):
        return _load_urls(self._evidence_urls)

    @evidence_urls.setter
    def evidence_urls(self, value):
        self._evidence_urls = _dump_urls(value)

    def get_department(self):
        return self.department_override or DEPT_MAP.get(self.category, "General Affairs")

    def to_dict(self):
        return {
            "id": self.id,
            "cmp_id": f"CMP{str(self.id).zfill(4)}",
            "citizen_id": self.citizen_id,
            "citizen_name": self.citizen.name if self.citizen else None,
            "citizen_email": self.citizen.email if self.citizen else None,
            "citizen_phone": self.citizen.phone if self.citizen else None,
            "category": self.category,
            "department": self.get_department(),
            "title": self.title,
            "description": self.description,
            "address": self.address,
            "ward": self.ward,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "priority": self.priority,
            "status": self.status,
            "admin_notes": self.admin_notes,
            "image_urls": self.image_urls,
            "evidence_urls": self.evidence_urls,
            "rating": self.rating,
            "feedback": self.feedback,
            "reopen_count": self.reopen_count,
            "pending_funds": self.pending_funds,
            "hold_reason": self.hold_reason,
            "upvotes_count": self.upvotes.count(),
            "assignment": self.assignment.to_dict() if self.assignment else None,
            "created_at": self.created_at.isoformat() + "+05:30",
            "updated_at": self.updated_at.isoformat() + "+05:30",
            "resolved_at": self.resolved_at.isoformat() + "+05:30" if self.resolved_at else None,
        }

    def to_public_dict(self):
        """Safe subset for the unauthenticated public tracking page.
        Excludes citizen name/email/phone (PII) and internal admin_notes/evidence_urls —
        keeps everything about the *complaint* itself (location, description, status,
        assigned department) since that's the point of a public tracking lookup."""
        return {
            "id": self.id,
            "cmp_id": f"CMP{str(self.id).zfill(4)}",
            "category": self.category,
            "department": self.get_department(),
            "title": self.title,
            "description": self.description,
            "address": self.address,
            "ward": self.ward,
            "priority": self.priority,
            "status": self.status,
            "hold_reason": self.hold_reason,
            "pending_funds": self.pending_funds,
            "image_urls": self.image_urls,
            "assignment": self.assignment.to_dict() if self.assignment else None,
            "upvotes_count": self.upvotes.count(),
            "created_at": self.created_at.isoformat() + "+05:30",
            "updated_at": self.updated_at.isoformat() + "+05:30",
            "resolved_at": self.resolved_at.isoformat() + "+05:30" if self.resolved_at else None,
        }


class Assignment(db.Model):
    __tablename__ = "assignments"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), unique=True, nullable=False)
    staff_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    notes = db.Column(db.Text)
    assigned_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    completed_at = db.Column(db.DateTime)
    assigner = db.relationship("User", foreign_keys=[assigned_by])

    def to_dict(self):
        return {
            "id": self.id,
            "request_id": self.request_id,
            "staff_id": self.staff_id,
            "staff_name": self.staff.name if self.staff else None,
            "staff_department": self.staff.department if self.staff else None,
            "assigned_by": self.assigned_by,
            "notes": self.notes,
            "assigned_at": self.assigned_at.isoformat() + "+05:30",
            "completed_at": self.completed_at.isoformat() + "+05:30" if self.completed_at else None,
        }


class Facility(db.Model):
    __tablename__ = "facilities"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    facility_type = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(300), nullable=False)
    ward = db.Column(db.String(50))
    capacity = db.Column(db.Integer, nullable=False, default=50)
    description = db.Column(db.Text)
    amenities = db.Column(db.String(500))
    fee_per_hour = db.Column(db.Float, nullable=False, default=0.0)
    _image_urls = db.Column("image_urls", db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    bookings = db.relationship("Booking", backref="facility", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def image_urls(self):
        return _load_urls(self._image_urls)

    @image_urls.setter
    def image_urls(self, value):
        self._image_urls = _dump_urls(value)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "facility_type": self.facility_type,
            "address": self.address, "ward": self.ward, "capacity": self.capacity,
            "description": self.description, "amenities": self.amenities,
            "fee_per_hour": self.fee_per_hour, "image_urls": self.image_urls, "is_active": self.is_active,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class Booking(db.Model):
    __tablename__ = "bookings"
    id = db.Column(db.Integer, primary_key=True)
    facility_id = db.Column(db.Integer, db.ForeignKey("facilities.id"), nullable=False)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    purpose = db.Column(db.String(300), nullable=False)
    attendees = db.Column(db.Integer, default=1)
    status = db.Column(db.String(20), nullable=False, default=BookingStatus.PENDING)
    fee = db.Column(db.Float, nullable=False, default=0.0)
    admin_notes = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    payment = db.relationship("Payment", backref="booking", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "facility_id": self.facility_id,
            "facility_name": self.facility.name if self.facility else None,
            "facility_type": self.facility.facility_type if self.facility else None,
            "citizen_id": self.citizen_id,
            "citizen_name": self.citizen.name if self.citizen else None,
            "booking_date": self.booking_date.isoformat(),
            "start_time": self.start_time.strftime("%H:%M"),
            "end_time": self.end_time.strftime("%H:%M"),
            "purpose": self.purpose, "attendees": self.attendees,
            "status": self.status, "fee": self.fee, "admin_notes": self.admin_notes,
            "payment": self.payment.to_dict() if self.payment else None,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id"), unique=True, nullable=False)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING)
    method = db.Column(db.String(50), default="online")
    transaction_ref = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    paid_at = db.Column(db.DateTime)
    payer = db.relationship("User", foreign_keys=[citizen_id])

    def to_dict(self):
        return {
            "id": self.id, "booking_id": self.booking_id,
            "citizen_id": self.citizen_id,
            "citizen_name": self.payer.name if self.payer else None,
            "amount": self.amount, "status": self.status, "method": self.method,
            "transaction_ref": self.transaction_ref,
            "created_at": self.created_at.isoformat() + "+05:30",
            "paid_at": self.paid_at.isoformat() + "+05:30" if self.paid_at else None,
        }


class Subscription(db.Model):
    """One row per citizen — the recurring membership itself. Actual money
    changes hands via SubscriptionPayment, one per billing cycle (like a
    Booking having many months instead of just one)."""
    __tablename__ = "subscriptions"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=SubscriptionStatus.ACTIVE)
    started_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    next_billing_date = db.Column(db.Date, nullable=False)
    cancelled_at = db.Column(db.DateTime)
    subscriber = db.relationship("User", foreign_keys=[citizen_id])
    payments = db.relationship("SubscriptionPayment", backref="subscription",
                                lazy="dynamic", cascade="all, delete-orphan",
                                order_by="SubscriptionPayment.id.desc()")

    def to_dict(self):
        latest = self.payments.first()
        return {
            "id": self.id,
            "citizen_id": self.citizen_id,
            "citizen_name": self.subscriber.name if self.subscriber else None,
            "citizen_email": self.subscriber.email if self.subscriber else None,
            "status": self.status,
            "monthly_fee": SUBSCRIPTION_FEE,
            "started_at": self.started_at.isoformat() + "+05:30",
            "next_billing_date": self.next_billing_date.isoformat(),
            "cancelled_at": self.cancelled_at.isoformat() + "+05:30" if self.cancelled_at else None,
            # True while a cancelled-but-still-paid-up member keeps access through
            # the period they already paid for — status only flips to CANCELLED
            # for real once that period ends (see _sync_subscription_billing).
            "pending_cancellation": bool(self.cancelled_at and self.status == SubscriptionStatus.ACTIVE),
            "latest_payment_status": latest.status if latest else None,
        }


class SubscriptionPayment(db.Model):
    """One invoice-able charge for a single billing cycle of a Subscription."""
    __tablename__ = "subscription_payments"
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey("subscriptions.id"), nullable=False)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=SUBSCRIPTION_FEE)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default=PaymentStatus.PENDING)
    method = db.Column(db.String(50))
    transaction_ref = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)
    paid_at = db.Column(db.DateTime)
    payer = db.relationship("User", foreign_keys=[citizen_id])

    def to_dict(self):
        return {
            "id": self.id,
            "subscription_id": self.subscription_id,
            "citizen_id": self.citizen_id,
            "citizen_name": self.payer.name if self.payer else None,
            "amount": self.amount,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "status": self.status,
            "method": self.method,
            "transaction_ref": self.transaction_ref,
            "created_at": self.created_at.isoformat() + "+05:30",
            "paid_at": self.paid_at.isoformat() + "+05:30" if self.paid_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notif_type = db.Column(db.String(50), default="info")
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=now_ist, nullable=False)

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id, "title": self.title,
            "message": self.message, "notif_type": self.notif_type,
            "is_read": self.is_read, "created_at": self.created_at.isoformat() + "+05:30",
        }


class Post(db.Model):
    __tablename__ = "posts"
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200))
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="general")
    location = db.Column(db.String(200))
    ward = db.Column(db.String(50))
    _image_urls = db.Column("image_urls", db.Text)
    is_official = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_ist)
    author = db.relationship("User", foreign_keys=[citizen_id])
    comments = db.relationship("PostComment", backref="post", lazy="dynamic", cascade="all, delete-orphan")
    likes = db.relationship("PostLike", backref="post", lazy="dynamic", cascade="all, delete-orphan")

    @property
    def image_urls(self):
        return _load_urls(self._image_urls)

    @image_urls.setter
    def image_urls(self, value):
        self._image_urls = _dump_urls(value)

    def to_dict(self, current_user_id=None):
        return {
            "id": self.id, "citizen_id": self.citizen_id,
            "author_name": self.author.name if self.author else None,
            "author_role": self.author.role if self.author else None,
            "author_department": self.author.department if self.author else None,
            "title": self.title, "content": self.content,
            "category": self.category, "location": self.location,
            "ward": self.ward, "image_urls": self.image_urls,
            "is_official": self.is_official,
            "likes_count": self.likes.count(),
            "comments_count": self.comments.count(),
            "liked_by_me": self.likes.filter_by(user_id=current_user_id).count() > 0 if current_user_id else False,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class PostComment(db.Model):
    __tablename__ = "post_comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_official = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=now_ist)
    author = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": self.id, "post_id": self.post_id, "user_id": self.user_id,
            "author_name": self.author.name if self.author else None,
            "author_role": self.author.role if self.author else None,
            "author_department": self.author.department if self.author else None,
            "content": self.content, "is_official": self.is_official,
            "created_at": self.created_at.isoformat() + "+05:30",
        }


class PostLike(db.Model):
    __tablename__ = "post_likes"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("post_id", "user_id"),)


class ComplaintUpvote(db.Model):
    """'Me too' upvotes on a complaint — lets a citizen flag that they're
    facing the same issue, without needing to file a duplicate complaint."""
    __tablename__ = "complaint_upvotes"
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey("service_requests.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    __table_args__ = (db.UniqueConstraint("request_id", "user_id"),)
