import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_restful import Api

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

db = SQLAlchemy()
jwt = JWTManager()


def create_app(env="development"):
    from .config import config_map
    app = Flask(__name__)
    app.config.from_object(config_map[env])

    db.init_app(app)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @jwt.token_in_blocklist_loader
    def _reject_deactivated_user(jwt_header, jwt_payload):
        from .models import User
        user = db.session.get(User, int(jwt_payload["sub"]))
        return user is None or not user.is_active

    api = Api(app, prefix="/api", errors={
        "RequestEntityTooLarge": {
            "message": "That file is over 5MB — please choose a smaller photo.",
            "status": 413,
        },
    })

    from .api import register_resources
    register_resources(api)

    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    from datetime import datetime, timedelta, timezone
    from .models import (User, Department, ServiceRequest, Assignment,
                         Facility, Post, PostComment, PostLike, Notification,
                         Role, Priority, RequestStatus)

    if User.query.count() > 0:
        return

    def dt(days_ago, hour=10, minute=0):
        return datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(tzinfo=None) - timedelta(days=days_ago) + timedelta(hours=hour-10, minutes=minute)

    # ── Users ─────────────────────────────────────────────────────────────────
    admin = User(name="Preetam Nagar Admin", email="admin@civic.gov", role=Role.ADMIN,
                 phone="9000000001", ward="Central", department="Administration", created_at=dt(60))
    admin.set_password("Admin@123")

    # Officers (staff) — one per department
    o1 = User(name="Rajesh Kumar", email="rajesh@civic.gov", role=Role.STAFF,
              phone="9876543210", department="Road Maintenance", created_at=dt(60))
    o1.set_password("Staff@123")

    o2 = User(name="Priya Singh", email="priya@civic.gov", role=Role.STAFF,
              phone="9876543212", department="Electricity Department", created_at=dt(60))
    o2.set_password("Staff@123")

    o3 = User(name="Imran Khan", email="imran@civic.gov", role=Role.STAFF,
              phone="9876543213", department="Water Supply Department", created_at=dt(60))
    o3.set_password("Staff@123")

    o4 = User(name="Sandeep Yadav", email="sandeep@civic.gov", role=Role.STAFF,
              phone="9876543214", department="Sanitation Department", created_at=dt(60))
    o4.set_password("Staff@123")

    o5 = User(name="Kavita Sharma", email="kavita@civic.gov", role=Role.STAFF,
              phone="9876543215", department="Parks & Public Spaces", created_at=dt(60))
    o5.set_password("Staff@123")

    # Citizens — all residents of Preetam Nagar; street names below are
    # internal to this one colony and consistently mapped to its wards:
    #   Ward-1: MG Road, Block A, School Road, Stadium Road
    #   Ward-2: Park Street, Colony Gate, Main Boulevard, Green Avenue
    #   Ward-3: Civil Lines Road, Nehru Chowk, Library Road, Nehru Colony
    #   Central: Civic Center, Central Park
    c1 = User(name="Amit Sharma", email="amit@gmail.com", role=Role.CITIZEN,
              phone="9111111101", ward="Ward-1", created_at=dt(45))
    c1.set_password("Citizen@123")

    c2 = User(name="Neha Verma", email="neha@gmail.com", role=Role.CITIZEN,
              phone="9111111102", ward="Ward-2", created_at=dt(40))
    c2.set_password("Citizen@123")

    c3 = User(name="Ravi Gupta", email="ravi.g@gmail.com", role=Role.CITIZEN,
              phone="9111111103", ward="Ward-3", created_at=dt(35))
    c3.set_password("Citizen@123")

    c4 = User(name="Sunita Mehta", email="sunita@gmail.com", role=Role.CITIZEN,
              phone="9111111104", ward="Ward-2", created_at=dt(30))
    c4.set_password("Citizen@123")

    c5 = User(name="Arjun Singh", email="arjun@gmail.com", role=Role.CITIZEN,
              phone="9111111105", ward="Ward-3", created_at=dt(25))
    c5.set_password("Citizen@123")

    db.session.add_all([admin, o1, o2, o3, o4, o5, c1, c2, c3, c4, c5])
    db.session.flush()

    # ── Departments ───────────────────────────────────────────────────────────
    depts = [
        Department(name="Road Maintenance", description="Handles road repairs, potholes, and street maintenance", officer_incharge_id=o1.id),
        Department(name="Electricity Department", description="Manages streetlights, electrical poles, and power supply issues", officer_incharge_id=o2.id),
        Department(name="Water Supply Department", description="Handles water supply, pipeline leakage, and drainage issues", officer_incharge_id=o3.id),
        Department(name="Sanitation Department", description="Manages garbage collection, sewage, and cleanliness", officer_incharge_id=o4.id),
        Department(name="Parks & Public Spaces", description="Maintains parks, public gardens, and recreational areas", officer_incharge_id=o5.id),
    ]
    db.session.add_all(depts)

    # ── Facilities ────────────────────────────────────────────────────────────
    facilities = [
        Facility(name="City Community Hall", facility_type="Community Hall",
                 address="1, Civic Center, Preetam Nagar (Central)", ward="Central",
                 capacity=200, fee_per_hour=500, description="Large community hall for events",
                 amenities="AC, Projector, Stage, Parking, Restrooms",
                 image_urls=["/api/uploads/community-hall.jpg"]),
        Facility(name="Ward-1 Sports Ground", facility_type="Sports Ground",
                 address="Stadium Road, Preetam Nagar (Ward-1)", ward="Ward-1",
                 capacity=100, fee_per_hour=100, description="Open ground for sports",
                 amenities="Changing Rooms, Floodlights, Drinking Water",
                 image_urls=["/api/uploads/sports-ground.jpg"]),
        Facility(name="Public Library Conference Room", facility_type="Conference Room",
                 address="Library Building, Civil Lines Road, Preetam Nagar (Ward-3)", ward="Ward-3",
                 capacity=50, fee_per_hour=200, description="Quiet conference room",
                 amenities="AC, WiFi, Whiteboard, Projector",
                 image_urls=["/api/uploads/library-room.jpg"]),
        Facility(name="Ward-2 Recreation Park", facility_type="Park",
                 address="Colony Gate, Preetam Nagar (Ward-2)", ward="Ward-2",
                 capacity=300, fee_per_hour=0, description="Open park for community events",
                 amenities="Open Space, Seating, Parking",
                 image_urls=["/api/uploads/recreation-park.jpg"]),
    ]
    db.session.add_all(facilities)

    # ── Service Requests (8 complaints — a small, deliberately curated set) ─────
    # Every photo below was manually opened and checked (filenames are not always
    # accurate — e.g. "manhole.jpg" is actually an open street drain). No photo is
    # shared between two different complaints, and no "before" photo contradicts
    # its own "after" evidence — e.g. dark-street.jpg (working, lit lamps) only
    # ever appears as the RESOLVED evidence for the power-outage complaint, never
    # as a "before" photo for a still-broken streetlight elsewhere.
    requests_data = [
        dict(citizen_id=c1.id, category="road", title="Large potholes on MG Road causing accidents",
             description="There are multiple large potholes near the main junction on MG Road. Three vehicles have been damaged this week. Requires urgent repair.",
             address="MG Road Junction, Preetam Nagar (Ward-1)", ward="Ward-1", priority=Priority.URGENT,
             status=RequestStatus.IN_PROGRESS, created_at=dt(12), staff=o1, notes="Assigned to road repair team. Work started.",
             image_urls=["/api/uploads/pothole.jpg", "/api/uploads/footpath.jpg"]),
        dict(citizen_id=c1.id, category="electricity", title="Street light not working near Block A park",
             description="The street light near the Block A park has not been working for 3 days. It is very unsafe to walk at night. Children play in this area.",
             address="Block A Park Gate, Preetam Nagar (Ward-1)", ward="Ward-1", priority=Priority.HIGH,
             status=RequestStatus.IN_PROGRESS, created_at=dt(3), staff=o2, notes="Maintenance team assigned. Bulb replacement in progress.",
             image_urls=["/api/uploads/streetlight.jpg", "/api/uploads/electric-pole.jpg"]),
        dict(citizen_id=c3.id, category="road", title="Road cave-in at Nehru Chowk",
             description="A section of road near Nehru Chowk has caved in after recent rains. The hole is about 3 feet deep and very dangerous for traffic.",
             address="Nehru Chowk, Preetam Nagar (Ward-3)", ward="Ward-3", priority=Priority.URGENT,
             status=RequestStatus.RESOLVED, created_at=dt(20), resolved_at=dt(15), staff=o1, notes="Road fully repaired and patched.",
             image_urls=["/api/uploads/road-damage.jpg"], evidence_urls=["/api/uploads/road-repaired.jpg"]),
        dict(citizen_id=c3.id, category="electricity", title="Power outage affecting entire block",
             description="Our entire residential block has had no electricity for 2 days. The transformer may have blown. Please send a technician.",
             address="Civil Lines Road, Preetam Nagar (Ward-3)", ward="Ward-3", priority=Priority.URGENT,
             status=RequestStatus.CLOSED, created_at=dt(15), resolved_at=dt(13), staff=o2, notes="Transformer replaced. Power restored.",
             evidence_urls=["/api/uploads/dark-street.jpg"],
             rating=4, feedback="Power was restored quickly once the team arrived. Good work."),
        dict(citizen_id=c3.id, category="waste", title="Garbage not collected for a week",
             description="Garbage has not been collected from our area for over a week. The garbage is piling up and causing health hazards. Rats and flies are increasing.",
             address="Civil Lines Road, Preetam Nagar (Ward-3)", ward="Ward-3", priority=Priority.HIGH,
             status=RequestStatus.PENDING, created_at=dt(7),
             image_urls=["/api/uploads/garbage.jpg", "/api/uploads/garbage-bins.jpg"]),
        dict(citizen_id=c2.id, category="water", title="Clogged drainage causing flooding",
             description="The main drainage channel near our colony is completely blocked. Rainwater is flooding homes. Please clear immediately.",
             address="Colony Gate, Preetam Nagar (Ward-2)", ward="Ward-2", priority=Priority.HIGH,
             status=RequestStatus.RESOLVED, created_at=dt(18), resolved_at=dt(16), staff=o3, notes="Drainage cleared. Good for monsoon season.",
             image_urls=["/api/uploads/manhole.jpg"],
             evidence_urls=["/api/uploads/garbage-collected.jpg"]),
        dict(citizen_id=c1.id, category="parks", title="Broken playground equipment in Block A park",
             description="The slides and swings in the Block A park are broken and rusted. Children have been injured. Please repair or replace the equipment.",
             address="Block A Park, Preetam Nagar (Ward-1)", ward="Ward-1", priority=Priority.MEDIUM,
             status=RequestStatus.CLOSED, created_at=dt(10), resolved_at=dt(4), staff=o5, notes="Old equipment removed and new playset installed.",
             image_urls=["/api/uploads/playground.jpg"], evidence_urls=["/api/uploads/playground-repaired.jpg"],
             rating=5, feedback="Great work — the new playset is wonderful, kids love it!"),
        dict(citizen_id=c5.id, category="sanitation", title="Blocked sewage drain overflowing in Nehru Colony",
             description="The open sewage drain in Nehru Colony is completely blocked with rags and plastic waste. Dirty water is stagnating and overflowing near homes, and the foul smell is unbearable. Needs urgent cleaning.",
             address="Nehru Colony, Preetam Nagar (Ward-3)", ward="Ward-3", priority=Priority.HIGH,
             status=RequestStatus.ASSIGNED, created_at=dt(2), staff=o4, notes="Sanitation crew scheduled to clear the blocked drain this week.",
             image_urls=["/api/uploads/sewage-drain.jpg"]),
    ]

    created_requests = []
    for rd in requests_data:
        staff = rd.pop("staff", None)
        notes = rd.pop("notes", None)
        r = ServiceRequest(**rd)
        db.session.add(r)
        created_requests.append((r, staff, notes))

    db.session.flush()

    # Create assignments for those with staff
    from datetime import timedelta
    for r, staff, notes in created_requests:
        if staff:
            a = Assignment(request_id=r.id, staff_id=staff.id, assigned_by=admin.id,
                          notes=notes, assigned_at=r.created_at + timedelta(hours=2))
            if r.status in [RequestStatus.RESOLVED, RequestStatus.CLOSED]:
                a.completed_at = r.resolved_at
            r.admin_notes = notes
            db.session.add(a)

    # ── Community Posts (5 — kept small, no images on announcements) ──────────
    posts = [
        Post(citizen_id=c1.id,
             content="Street light not working near Block A park since 3 days. Very unsafe for evening walkers. Please fix it urgently! @ElectricityDept",
             category="general", location="Block A Park, Preetam Nagar (Ward-1)", ward="Ward-1",
             image_urls=["/api/uploads/electric-pole.jpg", "/api/uploads/streetlight.jpg"],
             created_at=dt(0, hour=8)),
        Post(citizen_id=c2.id,
             content="Garbage not collected from our area last 2 days. The smell is unbearable and we can see rats near the garbage dump. Please take action!",
             category="general", location="Park Street, Preetam Nagar (Ward-2)", ward="Ward-2",
             image_urls=["/api/uploads/garbage.jpg", "/api/uploads/garbage-bins.jpg"],
             created_at=dt(0, hour=11)),
        Post(citizen_id=c1.id,
             content="Successfully got the pothole repaired near my house in just 5 days after submitting the complaint. Thank you Road Maintenance team! Great initiative by the colony administration.",
             category="general", location="Block A, Preetam Nagar (Ward-1)", ward="Ward-1",
             created_at=dt(3, hour=16)),
        Post(citizen_id=admin.id,
             title="Water Supply Maintenance Notice",
             content="Dear Residents, water supply will be interrupted across Preetam Nagar on 18 May 2024 from 9 AM to 5 PM due to pipeline maintenance work. We apologize for the inconvenience. Emergency water tankers will be available.",
             category="announcement", location="All of Preetam Nagar", ward="Central",
             is_official=True, created_at=dt(5, hour=9)),
        Post(citizen_id=admin.id,
             title="Clean Colony Drive - Join Us!",
             content="Join us for a Clean Colony Drive on 25 May 2024 at Central Park, Preetam Nagar. Bring gloves and bags. Free refreshments for all participants. Let's make our colony cleaner together! Register at the civic center.",
             category="announcement", location="Central Park, Preetam Nagar (Central)", ward="Central",
             is_official=True, created_at=dt(6, hour=10)),
    ]
    db.session.add_all(posts)
    db.session.flush()

    # Add comments to posts
    comments = [
        PostComment(post_id=posts[0].id, user_id=c2.id,
                    content="Same problem in our area too! Three lights not working near the bus stop.", created_at=dt(0, hour=8, minute=30)),
        PostComment(post_id=posts[0].id, user_id=o2.id,
                    content="We have received your complaint. Maintenance team has been assigned. Expected resolution within 48 hours.",
                    is_official=True, created_at=dt(0, hour=9)),
        PostComment(post_id=posts[1].id, user_id=c3.id,
                    content="Same issue in Ward-3! The garbage truck hasn't come for 5 days now.", created_at=dt(0, hour=11, minute=30)),
        PostComment(post_id=posts[1].id, user_id=o4.id,
                    content="Our team has been informed. Collection vehicle will reach your area today by 4 PM.",
                    is_official=True, created_at=dt(0, hour=12)),
    ]
    db.session.add_all(comments)

    # Add likes
    likes_data = [
        (posts[0].id, c2.id), (posts[0].id, c3.id), (posts[0].id, c4.id),
        (posts[1].id, c1.id), (posts[1].id, c3.id),
        (posts[2].id, c2.id), (posts[2].id, c3.id), (posts[2].id, c5.id),
    ]
    for post_id, user_id in likes_data:
        db.session.add(PostLike(post_id=post_id, user_id=user_id))

    # ── Notifications ─────────────────────────────────────────────────────────
    notifs = [
        Notification(user_id=c1.id, title="Complaint Assigned", message="Your complaint CMP0001 (Large potholes on MG Road) has been assigned to Road Maintenance Department.", notif_type="info"),
        Notification(user_id=c1.id, title="Complaint In Progress", message="Work has started on your complaint CMP0001. Expected completion in 3-5 days.", notif_type="info"),
        Notification(user_id=c3.id, title="Complaint Resolved", message="Your complaint CMP0003 (Road cave-in at Nehru Chowk) has been resolved. Please verify and close.", notif_type="success"),
        Notification(user_id=c1.id, title="Complaint In Progress", message="Work has started on your complaint CMP0002 (Street light not working). Our crew is on site.", notif_type="info"),
        Notification(user_id=o1.id, title="New Assignment", message="You have been assigned complaint CMP0001 - Large potholes on MG Road. Please take action.", notif_type="warning"),
        Notification(user_id=admin.id, title="New Complaints", message="A few new complaints have been submitted in the last 24 hours. Please review and assign.", notif_type="info"),
    ]
    db.session.add_all(notifs)

    # ── Bookings & Payments ───────────────────────────────────────────────────
    from datetime import date, time as dtime
    from .models import Booking, Payment, BookingStatus, PaymentStatus
    import uuid

    f1 = facilities[0]  # Community Hall (₹500/hr)
    f2 = facilities[1]  # Sports Ground (₹100/hr)
    f3 = facilities[2]  # Conference Room (₹200/hr)
    f4 = facilities[3]  # Recreation Park (free)

    bookings = [
        Booking(facility_id=f1.id, citizen_id=c1.id,
                booking_date=date(2026, 7, 10), start_time=dtime(10, 0), end_time=dtime(13, 0),
                purpose="Ward-1 Community Meeting", attendees=80, status=BookingStatus.CONFIRMED,
                fee=1500.0, admin_notes="Confirmed. Please arrive 15 mins early."),
        Booking(facility_id=f2.id, citizen_id=c2.id,
                booking_date=date(2026, 7, 15), start_time=dtime(7, 0), end_time=dtime(9, 0),
                purpose="Youth Cricket Practice", attendees=22, status=BookingStatus.PENDING,
                fee=200.0),
        Booking(facility_id=f3.id, citizen_id=c3.id,
                booking_date=date(2026, 7, 20), start_time=dtime(14, 0), end_time=dtime(16, 0),
                purpose="NGO Workshop", attendees=30, status=BookingStatus.CONFIRMED,
                fee=400.0, admin_notes="Please bring your ID proof."),
        Booking(facility_id=f4.id, citizen_id=c4.id,
                booking_date=date(2026, 7, 25), start_time=dtime(9, 0), end_time=dtime(11, 0),
                purpose="Yoga & Fitness Camp", attendees=50, status=BookingStatus.PENDING,
                fee=0.0),
        Booking(facility_id=f1.id, citizen_id=c5.id,
                booking_date=date(2026, 6, 5), start_time=dtime(18, 0), end_time=dtime(21, 0),
                purpose="Cultural Evening Event", attendees=150, status=BookingStatus.COMPLETED,
                fee=1500.0, admin_notes="Event completed successfully."),
    ]
    db.session.add_all(bookings)
    db.session.flush()

    # Payments for paid bookings
    payments = [
        Payment(booking_id=bookings[0].id, citizen_id=c1.id, amount=1500.0,
                status=PaymentStatus.PAID, method="upi",
                transaction_ref=f"TXN{uuid.uuid4().hex[:10].upper()}",
                paid_at=dt(10)),
        Payment(booking_id=bookings[1].id, citizen_id=c2.id, amount=200.0,
                status=PaymentStatus.PENDING, method="online"),
        Payment(booking_id=bookings[2].id, citizen_id=c3.id, amount=400.0,
                status=PaymentStatus.PAID, method="netbanking",
                transaction_ref=f"TXN{uuid.uuid4().hex[:10].upper()}",
                paid_at=dt(5)),
        Payment(booking_id=bookings[4].id, citizen_id=c5.id, amount=1500.0,
                status=PaymentStatus.PAID, method="card",
                transaction_ref=f"TXN{uuid.uuid4().hex[:10].upper()}",
                paid_at=dt(35)),
    ]
    db.session.add_all(payments)

    # ── Subscriptions (Cyber Panchayat Premium — Rs.100/month) ────────────────
    # Only the first billing cycle is seeded by hand; the live lazy-sync
    # (_sync_subscription_billing, called from /subscriptions/me and
    # /admin/subscriptions) generates any cycle that's since come due the
    # first time each subscription is actually read — same mechanism a real
    # user would trigger, just demonstrated from seed data instead of a fresh
    # signup.
    from .models import Subscription, SubscriptionPayment, SubscriptionStatus, SUBSCRIPTION_FEE
    from .api import _add_month

    def sub_txn():
        return f"SUB-TXN-{uuid.uuid4().hex[:10].upper()}"

    # Amit Sharma — subscribed 40 days ago; first cycle paid, and since that
    # cycle has already ended, the next cycle's payment shows up as "due" the
    # moment this subscription is next read.
    amit_p1_start = dt(40).date()
    amit_p1_end = _add_month(amit_p1_start)
    sub_amit = Subscription(citizen_id=c1.id, status=SubscriptionStatus.ACTIVE,
                             started_at=dt(40), next_billing_date=amit_p1_end)
    db.session.add(sub_amit)
    db.session.flush()
    db.session.add(SubscriptionPayment(
        subscription_id=sub_amit.id, citizen_id=c1.id, amount=SUBSCRIPTION_FEE,
        period_start=amit_p1_start, period_end=amit_p1_end,
        status=PaymentStatus.PAID, method="upi", transaction_ref=sub_txn(), paid_at=dt(39)))

    # Ravi Gupta — subscribed 20 days ago, first cycle paid, current cycle
    # still running (nothing due yet) — a "good standing" premium member.
    ravi_p1_start = dt(20).date()
    ravi_p1_end = _add_month(ravi_p1_start)
    sub_ravi = Subscription(citizen_id=c3.id, status=SubscriptionStatus.ACTIVE,
                             started_at=dt(20), next_billing_date=ravi_p1_end)
    db.session.add(sub_ravi)
    db.session.flush()
    db.session.add(SubscriptionPayment(
        subscription_id=sub_ravi.id, citizen_id=c3.id, amount=SUBSCRIPTION_FEE,
        period_start=ravi_p1_start, period_end=ravi_p1_end,
        status=PaymentStatus.PAID, method="card", transaction_ref=sub_txn(), paid_at=dt(19)))

    # Arjun Singh — subscribed then cancelled; shows up as a churned member
    # in admin's subscription list.
    arjun_p1_start = dt(50).date()
    arjun_p1_end = _add_month(arjun_p1_start)
    sub_arjun = Subscription(citizen_id=c5.id, status=SubscriptionStatus.CANCELLED,
                              started_at=dt(50), next_billing_date=arjun_p1_end, cancelled_at=dt(5))
    db.session.add(sub_arjun)
    db.session.flush()
    db.session.add(SubscriptionPayment(
        subscription_id=sub_arjun.id, citizen_id=c5.id, amount=SUBSCRIPTION_FEE,
        period_start=arjun_p1_start, period_end=arjun_p1_end,
        status=PaymentStatus.PAID, method="online", transaction_ref=sub_txn(), paid_at=dt(49)))

    db.session.commit()
    print("[SEED] Database seeded successfully with rich demo data!")
