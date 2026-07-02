import pytest
import json
from apps import create_app, db as _db


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def tokens(client):
    """Register and login all three roles, return their tokens."""
    roles = {}

    # Admin
    r = client.post("/api/auth/register", json={
        "name": "Test Admin", "email": "testadmin@civic.gov",
        "password": "Admin@123", "role": "citizen"  # register as citizen then promote
    })
    roles["admin_user_id"] = r.json["user"]["id"]
    # Directly make admin via db
    with client.application.app_context():
        from apps.models import User
        u = _db.session.get(User, roles["admin_user_id"])
        u.role = "admin"
        _db.session.commit()
    r2 = client.post("/api/auth/login", json={"email": "testadmin@civic.gov", "password": "Admin@123"})
    roles["admin"] = r2.json["token"]

    # Staff
    r = client.post("/api/auth/register", json={
        "name": "Test Staff", "email": "teststaff@civic.gov",
        "password": "Staff@123", "role": "citizen"
    })
    roles["staff_user_id"] = r.json["user"]["id"]
    with client.application.app_context():
        from apps.models import User
        u = _db.session.get(User, roles["staff_user_id"])
        u.role = "staff"
        u.department = "Road Maintenance"
        _db.session.commit()
    r2 = client.post("/api/auth/login", json={"email": "teststaff@civic.gov", "password": "Staff@123"})
    roles["staff"] = r2.json["token"]

    # Second staff member, same department (for reassignment tests)
    r = client.post("/api/auth/register", json={
        "name": "Test Staff Two", "email": "teststaff2@civic.gov",
        "password": "Staff@123", "role": "citizen"
    })
    roles["staff2_user_id"] = r.json["user"]["id"]
    with client.application.app_context():
        from apps.models import User
        u = _db.session.get(User, roles["staff2_user_id"])
        u.role = "staff"
        u.department = "Road Maintenance"
        _db.session.commit()

    # Citizen
    r = client.post("/api/auth/register", json={
        "name": "Test Citizen", "email": "testcitizen@gmail.com",
        "password": "Citizen@123"
    })
    roles["citizen_user_id"] = r.json["user"]["id"]
    roles["citizen"] = r.json["token"]

    return roles


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        r = client.post("/api/auth/register", json={
            "name": "New User", "email": "newuser@test.com", "password": "Pass@123"
        })
        assert r.status_code == 201
        assert "token" in r.json
        assert r.json["user"]["role"] == "citizen"

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "name": "Dup", "email": "dup@test.com", "password": "Pass@123"
        })
        r = client.post("/api/auth/register", json={
            "name": "Dup2", "email": "dup@test.com", "password": "Pass@123"
        })
        assert r.status_code == 409

    def test_register_missing_fields(self, client):
        r = client.post("/api/auth/register", json={"name": "Incomplete"})
        assert r.status_code == 400

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "name": "Login Test", "email": "logintest@test.com", "password": "Pass@123"
        })
        r = client.post("/api/auth/login", json={
            "email": "logintest@test.com", "password": "Pass@123"
        })
        assert r.status_code == 200
        assert "token" in r.json

    def test_login_wrong_password(self, client):
        r = client.post("/api/auth/login", json={
            "email": "logintest@test.com", "password": "WrongPass"
        })
        assert r.status_code == 401

    def test_login_nonexistent_user(self, client):
        r = client.post("/api/auth/login", json={
            "email": "nobody@test.com", "password": "Pass@123"
        })
        assert r.status_code == 401

    def test_me_requires_auth(self, client):
        r = client.get("/api/auth/me")
        assert r.status_code == 401

    def test_me_returns_profile(self, client, tokens):
        r = client.get("/api/auth/me", headers=auth_header(tokens["citizen"]))
        assert r.status_code == 200
        assert r.json["email"] == "testcitizen@gmail.com"


# ── Service Request Tests ─────────────────────────────────────────────────────

class TestServiceRequests:
    def test_create_request_success(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "complaint",
            "title": "Broken streetlight",
            "description": "The streetlight on MG Road has been out for 3 days",
            "address": "MG Road, Ward-1",
            "ward": "Ward-1",
            "priority": "high"
        })
        assert r.status_code == 201
        assert r.json["status"] == "pending"
        return r.json["id"]

    def test_create_request_unauthenticated(self, client):
        r = client.post("/api/requests", json={
            "category": "complaint", "title": "Test", "description": "Test", "address": "Test"
        })
        assert r.status_code == 401

    def test_create_request_staff_forbidden(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["staff"]), json={
            "category": "complaint", "title": "Test", "description": "Test", "address": "Test"
        })
        assert r.status_code == 403

    def test_create_request_invalid_category(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "invalid_cat", "title": "T", "description": "D", "address": "A"
        })
        assert r.status_code == 400

    def test_citizen_sees_only_own_requests(self, client, tokens):
        r = client.get("/api/requests", headers=auth_header(tokens["citizen"]))
        assert r.status_code == 200
        for req in r.json:
            assert req["citizen_id"] == tokens["citizen_user_id"]

    def test_admin_sees_all_requests(self, client, tokens):
        r = client.get("/api/requests", headers=auth_header(tokens["admin"]))
        assert r.status_code == 200
        assert isinstance(r.json, list)


class TestComplaintCommunityAndUpvotes:
    def test_community_feed_excludes_pii(self, client, tokens):
        # Citizen A creates a complaint in Ward-1
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road", "title": "Pothole near the market",
            "description": "Deep pothole, hard to see at night",
            "address": "Market Road", "ward": "Ward-1"
        })
        assert r.status_code == 201

        # Citizen B (different ward setup, no ward set) reads the community feed
        r = client.post("/api/auth/register", json={
            "name": "Community Viewer", "email": "communityviewer@gmail.com", "password": "Pass@123"
        })
        viewer_token = r.json["token"]

        r = client.get("/api/requests/community", headers=auth_header(viewer_token))
        assert r.status_code == 200
        for c in r.json:
            assert "citizen_name" not in c
            assert "citizen_email" not in c
            assert "citizen_phone" not in c
            assert "id" in c and "cmp_id" in c

    def test_upvote_toggle(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "water", "title": "Low water pressure",
            "description": "Pressure has been low all week", "address": "Sector 5"
        })
        request_id = r.json["id"]

        r = client.post(f"/api/requests/{request_id}/upvote", headers=auth_header(tokens["staff"]))
        assert r.status_code == 200
        assert r.json == {"upvoted": True, "upvotes_count": 1}

        r = client.post(f"/api/requests/{request_id}/upvote", headers=auth_header(tokens["staff"]))
        assert r.status_code == 200
        assert r.json == {"upvoted": False, "upvotes_count": 0}


class TestAssignments:
    def test_assign_request(self, client, tokens):
        # Create a request first
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road",
            "title": "Pothole near Central Park",
            "description": "The road near Central Park has a large pothole",
            "address": "Central Park", "ward": "Ward-1"
        })
        assert r.status_code == 201
        request_id = r.json["id"]

        # Admin assigns to staff
        r = client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": request_id,
            "staff_id": tokens["staff_user_id"],
            "notes": "Please handle urgently"
        })
        assert r.status_code == 201
        assert r.json["staff_id"] == tokens["staff_user_id"]

        # Verify request status changed to assigned
        r2 = client.get(f"/api/requests/{request_id}", headers=auth_header(tokens["admin"]))
        assert r2.json["status"] == "assigned"

    def test_citizen_cannot_assign(self, client, tokens):
        r = client.post("/api/assignments", headers=auth_header(tokens["citizen"]), json={
            "request_id": 1, "staff_id": tokens["staff_user_id"]
        })
        assert r.status_code == 403

    def test_assign_to_non_staff_fails(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "waste", "title": "Garbage not collected",
            "description": "3 days missed", "address": "Sector 3"
        })
        request_id = r.json["id"]
        r = client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": request_id,
            "staff_id": tokens["citizen_user_id"]  # citizen, not staff
        })
        assert r.status_code == 400

    def test_reassign_to_different_officer(self, client, tokens):
        # Regression test for a delete-then-insert-against-a-unique-column bug:
        # Assignment.request_id is unique=True, so re-assigning must UPDATE the
        # existing row in place rather than delete the old one and insert a new
        # one — SQLAlchemy flushes INSERTs before DELETEs in the same commit,
        # which previously tripped the UNIQUE constraint on the second assign.
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road", "title": "Broken kerb on MG Road",
            "description": "Kerb stone broken near junction", "address": "MG Road"
        })
        request_id = r.json["id"]

        r = client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": request_id, "staff_id": tokens["staff_user_id"]
        })
        assert r.status_code == 201

        r = client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": request_id, "staff_id": tokens["staff2_user_id"]
        })
        assert r.status_code == 200
        assert r.json["staff_id"] == tokens["staff2_user_id"]

        r2 = client.get(f"/api/requests/{request_id}", headers=auth_header(tokens["admin"]))
        assert r2.json["status"] == "reassigned"
        assert r2.json["assignment"]["staff_id"] == tokens["staff2_user_id"]


class TestRequestStatusFlow:
    def test_full_status_flow(self, client, tokens):
        # Citizen creates request
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road", "title": "Pothole on Main St",
            "description": "Large pothole causing accidents", "address": "Main St"
        })
        rid = r.json["id"]

        # Admin assigns
        client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": rid, "staff_id": tokens["staff_user_id"]
        })

        # Staff marks in_progress
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "in_progress"})
        assert r.status_code == 200
        assert r.json["status"] == "in_progress"

        # Staff resolves
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "resolved"})
        assert r.status_code == 200
        assert r.json["status"] == "resolved"

        # Citizen closes
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "closed"})
        assert r.status_code == 200
        assert r.json["status"] == "closed"

    def test_citizen_cannot_mark_in_progress(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "other", "title": "Test", "description": "Test", "address": "Test"
        })
        rid = r.json["id"]
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "in_progress"})
        assert r.status_code == 400


class TestWeatherHoldAndBudgetTag:
    def _assigned_request(self, client, tokens, ward="Ward-9"):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road", "title": "Road washed out",
            "description": "Heavy rain damaged the road surface", "address": "Test Rd",
            "ward": ward,
        })
        rid = r.json["id"]
        client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": rid, "staff_id": tokens["staff_user_id"]
        })
        return rid

    def test_only_admin_can_place_on_hold(self, client, tokens):
        rid = self._assigned_request(client, tokens)
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "on_hold_weather"})
        assert r.status_code == 403
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "on_hold_weather"})
        assert r.status_code == 403

    def test_admin_holds_and_resumes(self, client, tokens):
        rid = self._assigned_request(client, tokens)

        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["admin"]),
                       json={"status": "on_hold_weather", "hold_reason": "Monsoon season"})
        assert r.status_code == 200
        assert r.json["status"] == "on_hold_weather"
        assert r.json["hold_reason"] == "Monsoon season"

        # Staff is blocked from acting while on hold
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "in_progress"})
        assert r.status_code == 400

        # Admin resumes — hold_reason is cleared
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["admin"]),
                       json={"status": "in_progress"})
        assert r.status_code == 200
        assert r.json["status"] == "in_progress"
        assert r.json["hold_reason"] is None

        # Staff can act again now that the hold is lifted
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "resolved"})
        assert r.status_code == 200

    def test_budget_tag_admin_only(self, client, tokens):
        rid = self._assigned_request(client, tokens)
        r = client.put(f"/api/requests/{rid}/budget-tag", headers=auth_header(tokens["staff"]),
                       json={"pending_funds": True})
        assert r.status_code == 403

        r = client.put(f"/api/requests/{rid}/budget-tag", headers=auth_header(tokens["admin"]),
                       json={"pending_funds": True})
        assert r.status_code == 200
        assert r.json["pending_funds"] is True

        r = client.put(f"/api/requests/{rid}/budget-tag", headers=auth_header(tokens["admin"]),
                       json={"pending_funds": False})
        assert r.status_code == 200
        assert r.json["pending_funds"] is False

    def test_ward_filter_and_upvote_sort(self, client, tokens):
        rid = self._assigned_request(client, tokens, ward="Ward-UpvoteTest")
        client.post(f"/api/requests/{rid}/upvote", headers=auth_header(tokens["staff"]))

        r = client.get("/api/requests?ward=Ward-UpvoteTest", headers=auth_header(tokens["admin"]))
        assert r.status_code == 200
        assert all(req["ward"] == "Ward-UpvoteTest" for req in r.json)
        assert any(req["id"] == rid and req["upvotes_count"] == 1 for req in r.json)

        r = client.get("/api/requests?sort=upvotes", headers=auth_header(tokens["admin"]))
        assert r.status_code == 200
        counts = [req["upvotes_count"] for req in r.json]
        assert counts == sorted(counts, reverse=True)

    def test_pending_funds_filter(self, client, tokens):
        rid = self._assigned_request(client, tokens)
        client.put(f"/api/requests/{rid}/budget-tag", headers=auth_header(tokens["admin"]),
                   json={"pending_funds": True})
        r = client.get("/api/requests?pending_funds=true", headers=auth_header(tokens["admin"]))
        assert r.status_code == 200
        assert all(req["pending_funds"] for req in r.json)
        assert any(req["id"] == rid for req in r.json)


class TestReopenAndRating:
    def _resolved_request(self, client, tokens):
        r = client.post("/api/requests", headers=auth_header(tokens["citizen"]), json={
            "category": "road", "title": "Reopen/rating test",
            "description": "Issue for the reopen/rating flow", "address": "Test St"
        })
        rid = r.json["id"]
        client.post("/api/assignments", headers=auth_header(tokens["admin"]), json={
            "request_id": rid, "staff_id": tokens["staff_user_id"]
        })
        client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                   json={"status": "resolved"})
        return rid

    def test_close_with_rating(self, client, tokens):
        rid = self._resolved_request(client, tokens)
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "closed", "rating": 5, "feedback": "Great work"})
        assert r.status_code == 200
        assert r.json["status"] == "closed"
        assert r.json["rating"] == 5
        assert r.json["feedback"] == "Great work"

    def test_invalid_rating_rejected(self, client, tokens):
        rid = self._resolved_request(client, tokens)
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "closed", "rating": 9})
        assert r.status_code == 400

    def test_reopen_increments_count(self, client, tokens):
        rid = self._resolved_request(client, tokens)
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "reopened"})
        assert r.status_code == 200
        assert r.json["status"] == "reopened"
        assert r.json["reopen_count"] == 1

    def test_reopen_limit_enforced(self, client, tokens):
        rid = self._resolved_request(client, tokens)
        for _ in range(2):
            client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "reopened"})
            client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["staff"]),
                       json={"status": "resolved"})
        # third reopen is blocked (already reopened twice)
        r = client.put(f"/api/requests/{rid}/status", headers=auth_header(tokens["citizen"]),
                       json={"status": "reopened"})
        assert r.status_code == 400


# ── Booking Tests ─────────────────────────────────────────────────────────────

class TestBookings:
    def test_create_booking_success(self, client, tokens):
        # Get a facility
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        assert r.status_code == 200
        facility_id = r.json[0]["id"]

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-07-15",
            "start_time": "10:00",
            "end_time": "12:00",
            "purpose": "Community meeting",
            "attendees": 30
        })
        assert r.status_code == 201
        assert r.json["status"] == "pending"
        return r.json["id"]

    def test_booking_conflict(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        facility_id = r.json[0]["id"]

        client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-08-20",
            "start_time": "14:00",
            "end_time": "16:00",
            "purpose": "First booking",
        })

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-08-20",
            "start_time": "15:00",
            "end_time": "17:00",
            "purpose": "Conflicting booking",
        })
        assert r.status_code == 409

    def test_booking_past_date(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        facility_id = r.json[0]["id"]

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2020-01-01",
            "start_time": "10:00",
            "end_time": "12:00",
            "purpose": "Past booking",
        })
        assert r.status_code == 400

    def test_booking_end_before_start(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        facility_id = r.json[0]["id"]

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-09-01",
            "start_time": "14:00",
            "end_time": "10:00",
            "purpose": "Invalid time",
        })
        assert r.status_code == 400

    def test_booking_over_capacity(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        facility_id = r.json[0]["id"]
        capacity = r.json[0]["capacity"]

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-09-10",
            "start_time": "10:00",
            "end_time": "12:00",
            "purpose": "Too many people",
            "attendees": capacity + 100
        })
        assert r.status_code == 400

    def test_staff_cannot_book(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["staff"]))
        facility_id = r.json[0]["id"]

        r = client.post("/api/bookings", headers=auth_header(tokens["staff"]), json={
            "facility_id": facility_id,
            "booking_date": "2026-09-15",
            "start_time": "10:00",
            "end_time": "12:00",
            "purpose": "Staff booking",
        })
        assert r.status_code == 403


class TestPayments:
    def test_pay_booking(self, client, tokens):
        # Get a paid facility
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        paid_facility = next((f for f in r.json if f["fee_per_hour"] > 0), None)
        if not paid_facility:
            pytest.skip("No paid facility in seed data")

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": paid_facility["id"],
            "booking_date": "2026-10-01",
            "start_time": "09:00",
            "end_time": "11:00",
            "purpose": "Payment test",
        })
        assert r.status_code == 201
        booking = r.json
        assert booking["payment"] is not None
        payment_id = booking["payment"]["id"]

        # Pay
        r = client.post(f"/api/payments/{payment_id}/pay",
                        headers=auth_header(tokens["citizen"]),
                        json={"method": "upi"})
        assert r.status_code == 200
        assert r.json["status"] == "paid"
        assert r.json["transaction_ref"] is not None

    def test_double_payment_fails(self, client, tokens):
        r = client.get("/api/facilities", headers=auth_header(tokens["citizen"]))
        paid_facility = next((f for f in r.json if f["fee_per_hour"] > 0), None)
        if not paid_facility:
            pytest.skip("No paid facility")

        r = client.post("/api/bookings", headers=auth_header(tokens["citizen"]), json={
            "facility_id": paid_facility["id"],
            "booking_date": "2026-10-05",
            "start_time": "13:00",
            "end_time": "15:00",
            "purpose": "Double pay test",
        })
        payment_id = r.json["payment"]["id"]

        client.post(f"/api/payments/{payment_id}/pay",
                    headers=auth_header(tokens["citizen"]), json={"method": "upi"})

        r2 = client.post(f"/api/payments/{payment_id}/pay",
                         headers=auth_header(tokens["citizen"]), json={"method": "upi"})
        assert r2.status_code == 400


class TestDashboard:
    def test_citizen_dashboard(self, client, tokens):
        r = client.get("/api/dashboard", headers=auth_header(tokens["citizen"]))
        assert r.status_code == 200
        assert "requests" in r.json
        assert "bookings" in r.json

    def test_staff_dashboard(self, client, tokens):
        r = client.get("/api/dashboard", headers=auth_header(tokens["staff"]))
        assert r.status_code == 200
        assert "assignments" in r.json

    def test_admin_dashboard(self, client, tokens):
        r = client.get("/api/dashboard", headers=auth_header(tokens["admin"]))
        assert r.status_code == 200
        assert "users" in r.json
        assert "facilities" in r.json
        assert "payments" in r.json

    def test_dashboard_requires_auth(self, client):
        r = client.get("/api/dashboard")
        assert r.status_code == 401
