from flask import Flask, render_template, request, redirect, url_for, flash
import os
import sqlite3
from datetime import datetime
from collections import OrderedDict

app = Flask(__name__)
app.secret_key = "last-resort-hotels-dev-secret"
DATABASE = "lastresort.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Each entry is one of the 13 queries from queries.txt.
REPORTS = [
    {"id": 1,  "endpoint": "occupied_rooms",     "label": "Occupied Rooms"},
    {"id": 2,  "endpoint": "available_rooms",    "label": "Available Rooms"},
    {"id": 3,  "endpoint": "customer_totals",    "label": "Customer Totals"},
    {"id": 4,  "endpoint": "pending_charges",    "label": "Pending Charges"},
    {"id": 5,  "endpoint": "upcoming_events",    "label": "Upcoming Events"},
    {"id": 6,  "endpoint": "event_rooms",        "label": "Rooms per Event"},
    {"id": 7,  "endpoint": "missing_deposits",   "label": "Missing Deposits"},
    {"id": 8,  "endpoint": "smoking_pool_rooms", "label": "Smoking / Pool Rooms"},
    {"id": 9,  "endpoint": "rooms_by_dates",     "label": "Rooms by Date Range"},
    {"id": 10, "endpoint": "rooms_by_capacity",  "label": "Rooms by Capacity"},
    {"id": 11, "endpoint": "bed_types",          "label": "Bed Types per Room"},
    {"id": 12, "endpoint": "guest_history",      "label": "Guest Stay History"},
    {"id": 13, "endpoint": "facilities",         "label": "Facilities"},
]


@app.context_processor
def inject_globals():
    # Makes Reports Template
    return {"reports": REPORTS, "current_endpoint": request.endpoint}


# Home
@app.route("/", methods=["GET"])
def home():
    conn = get_db_connection()
    complex_info = conn.execute("SELECT * FROM hotel_complex LIMIT 1").fetchone()
    summary = conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM room)                                     AS totalRooms,
            (SELECT COUNT(*) FROM room_assignment WHERE isActive = 1)       AS occupiedRooms,
            (SELECT COUNT(*) FROM reservation WHERE reservationStatus
                IN ('CONFIRMED', 'PENDING'))                                AS openReservations,
            (SELECT COUNT(*) FROM event WHERE startDatetime > datetime('now')) AS upcomingEvents,
            (SELECT COUNT(*) FROM customer)                                 AS totalCustomers
    """).fetchone()
    conn.close()
    return render_template("index.html", complex=complex_info, summary=summary)


# Rooms  
@app.route("/rooms")
def rooms_showcase():
    conn = get_db_connection()
    rooms = conn.execute("""
        SELECT  r.roomId,
                r.roomNumber,
                r.roomType,
                r.baseRentalRate,
                r.maxSleepingGuests,
                r.status,
                w.wingDesignation,
                b.buildingName
        FROM    room r
                JOIN wing w     ON r.wingId      = w.wingId
                JOIN building b ON w.buildingId  = b.buildingId
        ORDER BY r.roomType, w.wingSequenceNumber, r.roomNumber
    """).fetchall()

    counts_rows = conn.execute("""
        SELECT roomType, COUNT(*) AS n,
               MIN(baseRentalRate) AS minRate
        FROM   room
        GROUP BY roomType
    """).fetchall()
    conn.close()

    counts = {"sleeping": 0, "suite": 0, "meeting": 0}
    rates  = {"sleeping": None, "suite": None, "meeting": None}
    for row in counts_rows:
        key = (row["roomType"] or "").lower()
        if key in counts:
            counts[key] = row["n"]
            rates[key]  = row["minRate"]

    return render_template(
        "rooms_showcase.html",
        rooms=rooms,
        counts=counts,
        rates=rates,
    )


# Amenities showcase

@app.route("/amenities")
def amenities_showcase():
    conn = get_db_connection()
    facilities = conn.execute("""
        SELECT f.facilityId,
               f.facilityName,
               f.facilityType,
               f.locationDescription,
               hc.complexName
        FROM   facility f
               JOIN hotel_complex hc ON f.complexId = hc.complexId
        ORDER BY f.facilityType, f.facilityName
    """).fetchall()
    conn.close()
    return render_template("amenities_showcase.html", facilities=facilities)


# Dashboard 
@app.route("/dashboard")
def dashboard():
    conn = get_db_connection()

    # KPI
    total_revenue = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS s FROM charge"
    ).fetchone()["s"]
    total_rooms = conn.execute("SELECT COUNT(*) AS n FROM room").fetchone()["n"]
    occupied = conn.execute(
        "SELECT COUNT(*) AS n FROM room_assignment WHERE isActive = 1"
    ).fetchone()["n"]
    occupancy_rate = round((occupied / total_rooms) * 100, 1) if total_rooms else 0

    total_guests = conn.execute(
        "SELECT COUNT(*) AS n FROM customer"
    ).fetchone()["n"]
    repeat_guests = conn.execute("""
        SELECT COUNT(*) AS n FROM (
            SELECT guestId
            FROM   room_assignment
            WHERE  guestId IS NOT NULL
            GROUP BY guestId
            HAVING COUNT(*) > 1
        )
    """).fetchone()["n"]

    kpi = {
        "totalRevenue": total_revenue,
        "occupancyRate": occupancy_rate,
        "totalGuests": total_guests,
        "repeatGuests": repeat_guests,
    }

    # Revenue Growth
    revenue_rows = conn.execute("""
        SELECT  strftime('%Y-%m', chargeDatetime) AS ym,
                SUM(amount) AS s
        FROM    charge
        WHERE   chargeDatetime IS NOT NULL
        GROUP BY ym
        ORDER BY ym
    """).fetchall()
    revenue_labels = [r["ym"] for r in revenue_rows]
    revenue_values = [r["s"] or 0 for r in revenue_rows]
    # If we have no charge history at all, seed with today's month so the chart isn't empty
    if not revenue_labels:
        revenue_labels = [datetime.now().strftime("%Y-%m")]
        revenue_values = [0]

    # Occupancy Rate
    available = conn.execute(
        "SELECT COUNT(*) AS n FROM room WHERE status = 'AVAILABLE'"
    ).fetchone()["n"]
    maintenance = conn.execute("""
        SELECT COUNT(*) AS n FROM room
        WHERE  status IN ('RENOVATION', 'MAINTENANCE', 'OUT_OF_SERVICE', 'NEEDS_CLEANING')
    """).fetchone()["n"]
    # cap available so it doesn't double-count occupied rooms with status AVAILABLE
    available = max(available - occupied, 0) + max(0, total_rooms - occupied - available - maintenance)
    if available < 0:
        available = 0

    # Revenue by Charge Type 
    type_rows = conn.execute("""
        SELECT  chargeType, COALESCE(SUM(amount), 0) AS s
        FROM    charge
        GROUP BY chargeType
        ORDER BY s DESC
    """).fetchall()
    type_labels = [r["chargeType"] for r in type_rows]
    type_values = [r["s"] for r in type_rows]
    if not type_labels:
        type_labels = ["No charges yet"]
        type_values = [1]

    # Loyalty Distribution
    loyalty_rows = conn.execute("""
        SELECT guestId, COUNT(*) AS stays
        FROM   room_assignment
        WHERE  guestId IS NOT NULL
        GROUP BY guestId
    """).fetchall()
    buckets = OrderedDict([("1 stay", 0), ("2 stays", 0), ("3 stays", 0),
                           ("4 stays", 0), ("5+ stays", 0)])
    for r in loyalty_rows:
        s = r["stays"]
        if s == 1: buckets["1 stay"] += 1
        elif s == 2: buckets["2 stays"] += 1
        elif s == 3: buckets["3 stays"] += 1
        elif s == 4: buckets["4 stays"] += 1
        else:        buckets["5+ stays"] += 1

    top_guests_rows = conn.execute("""
        SELECT  c.firstName || ' ' || c.lastName AS name,
                COUNT(ra.assignmentId)           AS stays,
                COALESCE(SUM(ch.amount), 0)      AS spend
        FROM    customer c
                LEFT JOIN room_assignment ra ON ra.guestId       = c.customerId
                LEFT JOIN charge          ch ON ch.billedPartyId = c.customerId
        GROUP BY c.customerId
        HAVING stays > 0
        ORDER BY stays DESC, spend DESC
        LIMIT 6
    """).fetchall()

    conn.close()

    charts = {
        "revenue":   {"labels": revenue_labels, "values": revenue_values},
        "occupancy": {"occupied": occupied, "available": available, "maintenance": maintenance},
        "chargeType": {"labels": type_labels, "values": type_values},
        "loyalty":   {"labels": list(buckets.keys()), "values": list(buckets.values())},
    }

    return render_template(
        "dashboard.html",
        kpi=kpi,
        charts=charts,
        topGuests=[{"name": r["name"], "stays": r["stays"], "spend": r["spend"]}
                   for r in top_guests_rows],
    )

# Manage Guests
@app.route("/guests")
def guests():
    conn = get_db_connection()
    customers = conn.execute("""
        SELECT  c.customerId,
                c.firstName || ' ' || c.lastName AS name,
                c.email,
                c.phone,
                COALESCE(s.stays, 0)             AS stays,
                CASE WHEN a.activeId IS NOT NULL THEN 1 ELSE 0 END AS activeStay
        FROM    customer c
                LEFT JOIN (
                    SELECT guestId, COUNT(*) AS stays
                    FROM   room_assignment
                    GROUP BY guestId
                ) s ON s.guestId = c.customerId
                LEFT JOIN (
                    SELECT guestId, MAX(assignmentId) AS activeId
                    FROM   room_assignment
                    WHERE  isActive = 1
                    GROUP BY guestId
                ) a ON a.guestId = c.customerId
        ORDER BY c.lastName, c.firstName
    """).fetchall()
    conn.close()
    return render_template("guests.html", customers=customers)


@app.route("/guests/<int:customer_id>/delete", methods=["POST"])
def delete_guest(customer_id):
    conn = get_db_connection()
    try:
        cust = conn.execute(
            "SELECT firstName || ' ' || lastName AS name FROM customer WHERE customerId = ?",
            (customer_id,)
        ).fetchone()
        if not cust:
            flash("Guest not found.", "error")
            return redirect(url_for("guests"))

        active = conn.execute(
            "SELECT 1 FROM room_assignment WHERE guestId = ? AND isActive = 1",
            (customer_id,)
        ).fetchone()
        if active:
            flash(
                f"Cannot delete {cust['name']} — they're currently checked in. "
                f"Check them out first.",
                "error",
            )
            return redirect(url_for("guests"))

        conn.execute(
            "UPDATE event SET hostCustomerId = NULL WHERE hostCustomerId = ?",
            (customer_id,),
        )
        conn.execute(
            "UPDATE event SET billedPartyId = NULL WHERE billedPartyId = ?",
            (customer_id,),
        )
        conn.execute(
            "UPDATE organization SET contactPersonId = NULL WHERE contactPersonId = ?",
            (customer_id,),
        )

        # Remove dependent rows in dependency order
        conn.execute("DELETE FROM billing_split WHERE customerId = ?", (customer_id,))
        conn.execute("""
            DELETE FROM billing_split
            WHERE  roomAssignmentId IN (
                SELECT assignmentId FROM room_assignment WHERE guestId = ?
            )
        """, (customer_id,))
        conn.execute("DELETE FROM charge WHERE billedPartyId = ?", (customer_id,))
        conn.execute("""
            DELETE FROM charge
            WHERE  roomAssignmentId IN (
                SELECT assignmentId FROM room_assignment WHERE guestId = ?
            )
        """, (customer_id,))
        conn.execute("""
            DELETE FROM reservation_preference
            WHERE  reservationId IN (
                SELECT reservationId FROM reservation WHERE customerId = ?
            )
        """, (customer_id,))
        conn.execute("DELETE FROM room_assignment WHERE guestId = ?", (customer_id,))
        conn.execute("DELETE FROM reservation WHERE customerId = ?", (customer_id,))
        conn.execute("DELETE FROM event_guest WHERE customerId = ?", (customer_id,))
        
        # Card scan log references guest_card
        conn.execute("""
            DELETE FROM card_scan_log
            WHERE  cardId IN (SELECT cardId FROM guest_card WHERE customerId = ?)
        """, (customer_id,))
        conn.execute("DELETE FROM guest_card WHERE customerId = ?", (customer_id,))
        conn.execute("DELETE FROM guest_message WHERE customerId = ?", (customer_id,))
        conn.execute("DELETE FROM customer WHERE customerId = ?", (customer_id,))
        conn.commit()
        flash(f"{cust['name']} and all related records were deleted.", "success")
    except sqlite3.IntegrityError as e:
        conn.rollback()
        flash(f"Could not delete: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("guests"))

# Room Change
@app.route("/room-change", methods=["GET", "POST"])
def room_change():
    conn = get_db_connection()

    if request.method == "POST":
        assignment_id = request.form.get("assignmentId", type=int)
        new_room_id   = request.form.get("newRoomId",   type=int)
        reason        = (request.form.get("reason") or "").strip()

        try:
            old = conn.execute("""
                SELECT  ra.assignmentId, ra.reservationId, ra.guestId,
                        ra.assignedDate, ra.actualCheckIn,
                        r.roomNumber AS oldRoomNumber,
                        c.firstName || ' ' || c.lastName AS guestName
                FROM    room_assignment ra
                        JOIN room     r ON ra.roomId   = r.roomId
                        JOIN customer c ON ra.guestId  = c.customerId
                WHERE   ra.assignmentId = ?
                  AND   ra.isActive = 1
            """, (assignment_id,)).fetchone()

            if not old:
                flash("That stay is no longer active.", "error")
                return redirect(url_for("room_change"))

            new_room = conn.execute("""
                SELECT roomId, roomNumber FROM room WHERE roomId = ?
            """, (new_room_id,)).fetchone()
            if not new_room:
                flash("Destination room not found.", "error")
                return redirect(url_for("room_change"))

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Close Old Assignment
            conn.execute("""
                UPDATE room_assignment
                   SET isActive = 0,
                       actualCheckOut = ?
                 WHERE assignmentId = ?
            """, (now, assignment_id))
            # Free Old Room
            conn.execute("""
                UPDATE room
                   SET status = 'NEEDS_CLEANING',
                       statusUpdatedAt = ?
                 WHERE roomId = (
                    SELECT roomId FROM room_assignment WHERE assignmentId = ?
                 )
            """, (now, assignment_id))

            # Open a New Active Assignment Carrying Over Reservation, Guest, Check-in
            conn.execute("""
                INSERT INTO room_assignment
                    (reservationId, roomId, guestId, assignedDate,
                     actualCheckIn, isActive)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (
                old["reservationId"], new_room_id, old["guestId"],
                now, old["actualCheckIn"] or now,
            ))
            # Mark New Room Occupied
            conn.execute("""
                UPDATE room SET status = 'OCCUPIED', statusUpdatedAt = ?
                 WHERE roomId = ?
            """, (now, new_room_id))

            conn.commit()
            flash(
                f"{old['guestName']} moved from Room {old['oldRoomNumber']} to "
                f"Room {new_room['roomNumber']}.",
                "success",
            )
        except sqlite3.IntegrityError as e:
            conn.rollback()
            flash(f"Could not move guest: {e}", "error")
        finally:
            conn.close()
        return redirect(url_for("room_change"))

    active_assignments = conn.execute("""
        SELECT  ra.assignmentId,
                c.firstName || ' ' || c.lastName AS guestName,
                r.roomNumber, r.roomType,
                ra.actualCheckIn
        FROM    room_assignment ra
                JOIN customer c ON ra.guestId = c.customerId
                JOIN room     r ON ra.roomId  = r.roomId
        WHERE   ra.isActive = 1
        ORDER BY ra.assignmentId DESC
    """).fetchall()

    available_rooms = conn.execute("""
        SELECT  r.roomId, r.roomNumber, r.roomType,
                r.baseRentalRate, r.maxSleepingGuests,
                w.wingDesignation
        FROM    room r
                JOIN wing w ON r.wingId = w.wingId
        WHERE   r.status = 'AVAILABLE'
          AND   r.roomId NOT IN (
                  SELECT roomId FROM room_assignment WHERE isActive = 1
                )
        ORDER BY w.wingSequenceNumber, r.roomNumber
    """).fetchall()

    recent_moves = conn.execute("""
        SELECT  c.firstName || ' ' || c.lastName AS guest,
                r1.roomNumber AS fromRoom,
                r2.roomNumber AS toRoom,
                ra2.assignedDate AS moveDate
        FROM    room_assignment ra1
                JOIN room_assignment ra2
                  ON ra1.guestId = ra2.guestId
                 AND ra2.assignmentId > ra1.assignmentId
                 AND ra2.reservationId IS ra1.reservationId
                JOIN room r1 ON ra1.roomId = r1.roomId
                JOIN room r2 ON ra2.roomId = r2.roomId
                JOIN customer c ON ra1.guestId = c.customerId
        WHERE   ra1.isActive = 0
          AND   ra1.actualCheckOut IS NOT NULL
        ORDER BY ra2.assignmentId DESC
        LIMIT 10
    """).fetchall()

    conn.close()
    return render_template(
        "room_change.html",
        active_assignments=active_assignments,
        available_rooms=available_rooms,
        recent_moves=recent_moves,
    )

# Q1: Currently occupied rooms with guest info
@app.route("/occupied-rooms")
def occupied_rooms():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  r.roomNumber,
                c.firstName || ' ' || c.lastName AS guest,
                ra.actualCheckIn,
                w.wingDesignation,
                b.buildingName
        FROM    room_assignment ra
                JOIN room     r ON ra.roomId   = r.roomId
                JOIN wing     w ON r.wingId    = w.wingId
                JOIN building b ON w.buildingId = b.buildingId
                JOIN customer c ON ra.guestId  = c.customerId
        WHERE   ra.isActive = 1
        ORDER BY w.wingSequenceNumber, r.roomNumber
    """).fetchall()
    conn.close()
    columns = [
        {"key": "roomNumber",       "header": "Room"},
        {"key": "guest",            "header": "Guest"},
        {"key": "actualCheckIn",    "header": "Checked In"},
        {"key": "wingDesignation",  "header": "Wing"},
        {"key": "buildingName",     "header": "Building"},
    ]
    return render_template(
        "report.html",
        title="Currently Occupied Rooms",
        description="All rooms with an active guest assignment, "
                    "ordered by wing sequence and room number.",
        columns=columns,
        rows=rows,
    )

# Q2: Rooms available right now
@app.route("/available-rooms")
def available_rooms():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  w.wingDesignation,
                r.roomType,
                r.roomNumber,
                r.baseRentalRate
        FROM    room r
                JOIN wing w ON r.wingId = w.wingId
        WHERE   r.status = 'AVAILABLE'
          AND   r.roomId NOT IN (
                  SELECT roomId FROM room_assignment WHERE isActive = 1
                )
        ORDER BY w.wingSequenceNumber, r.roomNumber
    """).fetchall()
    conn.close()
    columns = [
        {"key": "wingDesignation", "header": "Wing"},
        {"key": "roomType",        "header": "Type"},
        {"key": "roomNumber",      "header": "Room"},
        {"key": "baseRentalRate",  "header": "Base Rate ($)"},
    ]
    return render_template(
        "report.html",
        title="Rooms Available Right Now",
        description="Rooms with status AVAILABLE and no active assignment.",
        columns=columns,
        rows=rows,
    )


# Q3: Total charges per customer, sorted by highest spend
@app.route("/customer-totals")
def customer_totals():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  c.customerId,
                c.firstName || ' ' || c.lastName AS name,
                COUNT(ch.chargeId)               AS numCharges,
                COALESCE(SUM(ch.amount), 0)      AS totalSpend
        FROM    customer c
                LEFT JOIN charge ch ON c.customerId = ch.billedPartyId
        GROUP BY c.customerId
        ORDER BY totalSpend DESC, name
    """).fetchall()
    conn.close()
    columns = [
        {"key": "customerId", "header": "ID"},
        {"key": "name",       "header": "Customer"},
        {"key": "numCharges", "header": "# of Charges"},
        {"key": "totalSpend", "header": "Total Spend ($)"},
    ]
    return render_template(
        "report.html",
        title="Total Charges per Customer",
        description="Every customer with the count and sum of their charges, "
                    "sorted by highest total spend.",
        columns=columns,
        rows=rows,
    )


# Q4: Unpaid / pending charges per customer
@app.route("/pending-charges")
def pending_charges():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  c.firstName || ' ' || c.lastName AS name,
                ch.chargeType,
                ch.chargeDescription,
                ch.amount,
                ch.chargeStatus,
                ch.chargeDatetime
        FROM    charge ch
                JOIN customer c ON ch.billedPartyId = c.customerId
        WHERE   ch.chargeStatus IN ('ACTUAL', 'ORDERED', 'AUTHORIZED')
        ORDER BY c.lastName, ch.chargeDatetime
    """).fetchall()
    conn.close()
    columns = [
        {"key": "name",              "header": "Customer"},
        {"key": "chargeType",        "header": "Type"},
        {"key": "chargeDescription", "header": "Description"},
        {"key": "amount",            "header": "Amount ($)"},
        {"key": "chargeStatus",      "header": "Status"},
        {"key": "chargeDatetime",    "header": "Date"},
    ]
    return render_template(
        "report.html",
        title="Unpaid / Pending Charges",
        description="Charges in ACTUAL, ORDERED, or AUTHORIZED status — "
                    "anything not yet billed and paid.",
        columns=columns,
        rows=rows,
    )


# Q5: Upcoming events with host name and estimated attendance
@app.route("/upcoming-events")
def upcoming_events():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  e.eventName,
                c.firstName || ' ' || c.lastName AS host,
                e.startDatetime,
                e.estimatedAttendance,
                e.estimatedHotelGuests,
                e.eventStatus
        FROM    event e
                JOIN customer c ON e.hostCustomerId = c.customerId
        WHERE   e.startDatetime > datetime('now')
        ORDER BY e.startDatetime
    """).fetchall()
    conn.close()
    columns = [
        {"key": "eventName",            "header": "Event"},
        {"key": "host",                 "header": "Host"},
        {"key": "startDatetime",        "header": "Starts"},
        {"key": "estimatedAttendance",  "header": "Est. Attendance"},
        {"key": "estimatedHotelGuests", "header": "Est. Hotel Guests"},
        {"key": "eventStatus",          "header": "Status"},
    ]
    return render_template(
        "report.html",
        title="Upcoming Events",
        description="Events scheduled to start in the future, with host and "
                    "estimated guest counts.",
        columns=columns,
        rows=rows,
    )


# Q6: Rooms booked per event
@app.route("/event-rooms")
def event_rooms():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  e.eventName,
                COUNT(DISTINCT er.roomId)   AS roomsUsed,
                COUNT(er.eventRoomId)       AS totalSlotBookings,
                COALESCE(SUM(er.chargeRate), 0) AS totalCharges
        FROM    event e
                LEFT JOIN event_room er ON e.eventId = er.eventId
        GROUP BY e.eventId, e.eventName
        ORDER BY totalCharges DESC
    """).fetchall()
    conn.close()
    columns = [
        {"key": "eventName",         "header": "Event"},
        {"key": "roomsUsed",         "header": "Rooms Used"},
        {"key": "totalSlotBookings", "header": "Time-Slot Bookings"},
        {"key": "totalCharges",      "header": "Total Charges ($)"},
    ]
    return render_template(
        "report.html",
        title="Rooms Booked per Event",
        description="Each event with the number of distinct rooms used, "
                    "total time-slot bookings, and total room charges.",
        columns=columns,
        rows=rows,
    )


# Q7: Reservations missing required deposits
@app.route("/missing-deposits")
def missing_deposits():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  r.reservationId,
                c.firstName || ' ' || c.lastName AS name,
                r.checkInDate,
                r.advanceDepositAmount,
                r.reservationStatus
        FROM    reservation r
                JOIN customer c ON r.customerId = c.customerId
        WHERE   r.advanceDepositRequired = 1
          AND   (r.depositPaid = 0 OR r.depositPaid IS NULL)
        ORDER BY r.checkInDate
    """).fetchall()
    conn.close()
    columns = [
        {"key": "reservationId",        "header": "Res #"},
        {"key": "name",                 "header": "Customer"},
        {"key": "checkInDate",          "header": "Check-In"},
        {"key": "advanceDepositAmount", "header": "Deposit Owed ($)"},
        {"key": "reservationStatus",    "header": "Status"},
    ]
    return render_template(
        "report.html",
        title="Reservations Missing Required Deposits",
        description="Reservations that require an advance deposit but where "
                    "the deposit has not yet been paid.",
        columns=columns,
        rows=rows,
    )


# Q8: Smoking rooms near pool, sorted by rate
@app.route("/smoking-pool-rooms")
def smoking_pool_rooms():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  r.roomNumber,
                r.roomType,
                r.baseRentalRate,
                w.wingDesignation
        FROM    room r
                JOIN wing w ON r.wingId = w.wingId
        WHERE   r.isSmoking = 1
          AND   w.poolProximity = 1
        ORDER BY r.baseRentalRate
    """).fetchall()
    conn.close()
    columns = [
        {"key": "roomNumber",      "header": "Room"},
        {"key": "roomType",        "header": "Type"},
        {"key": "baseRentalRate",  "header": "Base Rate ($)"},
        {"key": "wingDesignation", "header": "Wing"},
    ]
    return render_template(
        "report.html",
        title="Smoking Rooms Near the Pool",
        description="Smoking rooms located in pool-adjacent wings, "
                    "sorted by base rental rate.",
        columns=columns,
        rows=rows,
    )


# Q9: Available sleeping rooms with amenities for a given date range
@app.route("/rooms-by-dates")
def rooms_by_dates():
    start_date = request.args.get("start_date", "").strip()
    end_date   = request.args.get("end_date",   "").strip()

    rows = []
    if start_date and end_date:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT  r.roomNumber,
                    r.roomType,
                    r.baseRentalRate,
                    r.hasTelevision,
                    r.hasTelephone,
                    r.isSmoking,
                    w.handicappedAccess,
                    w.wingDesignation
            FROM    room r
                    JOIN wing w ON r.wingId = w.wingId
            WHERE   r.status = 'AVAILABLE'
              AND   r.roomType = 'SLEEPING'
              AND   r.roomId NOT IN (
                      SELECT ra.roomId
                      FROM   room_assignment ra
                             JOIN reservation res
                               ON ra.reservationId = res.reservationId
                      WHERE  res.checkInDate  < ?
                        AND  res.checkOutDate > ?
                    )
            ORDER BY r.baseRentalRate
        """, (end_date, start_date)).fetchall()
        conn.close()

    columns = [
        {"key": "roomNumber",        "header": "Room"},
        {"key": "roomType",          "header": "Type"},
        {"key": "baseRentalRate",    "header": "Rate ($)"},
        {"key": "hasTelevision",     "header": "TV"},
        {"key": "hasTelephone",      "header": "Phone"},
        {"key": "isSmoking",         "header": "Smoking"},
        {"key": "handicappedAccess", "header": "Handicapped"},
        {"key": "wingDesignation",   "header": "Wing"},
    ]
    return render_template(
        "report.html",
        title="Available Rooms by Date Range",
        description="Sleeping rooms that are AVAILABLE and not blocked by any "
                    "reservation overlapping the chosen date range, sorted by rate.",
        columns=columns,
        rows=rows,
        form_kind="dates",
        form_values={"start_date": start_date, "end_date": end_date},
    )


# Q10: Rooms that can sleep at least N guests
@app.route("/rooms-by-capacity")
def rooms_by_capacity():
    capacity = request.args.get("capacity", type=int)

    rows = []
    if capacity is not None:
        conn = get_db_connection()
        rows = conn.execute("""
            SELECT  r.roomNumber,
                    r.roomType,
                    r.maxSleepingGuests,
                    r.baseRentalRate,
                    w.wingDesignation
            FROM    room r
                    JOIN wing w ON r.wingId = w.wingId
            WHERE   r.maxSleepingGuests >= ?
              AND   r.roomType IN ('SLEEPING', 'SUITE')
            ORDER BY r.maxSleepingGuests, r.baseRentalRate
        """, (capacity,)).fetchall()
        conn.close()

    columns = [
        {"key": "roomNumber",        "header": "Room"},
        {"key": "roomType",          "header": "Type"},
        {"key": "maxSleepingGuests", "header": "Sleeps"},
        {"key": "baseRentalRate",    "header": "Rate ($)"},
        {"key": "wingDesignation",   "header": "Wing"},
    ]
    return render_template(
        "report.html",
        title="Rooms by Sleeping Capacity",
        description="Sleeping rooms and suites able to accommodate at least "
                    "the requested number of guests.",
        columns=columns,
        rows=rows,
        form_kind="capacity",
        form_values={"capacity": capacity if capacity is not None else ""},
    )


# Q11: Bed types available per room
@app.route("/bed-types")
def bed_types():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  r.roomNumber,
                r.roomType,
                rb.bedType,
                rb.bedSize,
                r.baseRentalRate
        FROM    room r
                JOIN room_bed rb ON r.roomId = rb.roomId
        ORDER BY r.roomNumber, rb.bedSize
    """).fetchall()
    conn.close()
    columns = [
        {"key": "roomNumber",     "header": "Room"},
        {"key": "roomType",       "header": "Type"},
        {"key": "bedType",        "header": "Bed Type"},
        {"key": "bedSize",        "header": "Bed Size"},
        {"key": "baseRentalRate", "header": "Rate ($)"},
    ]
    return render_template(
        "report.html",
        title="Bed Types per Room",
        description="Every bed in every room — useful when guests filter on "
                    "bed type or size.",
        columns=columns,
        rows=rows,
    )


# Q12: A guest's full stay history
@app.route("/guest-history")
def guest_history():
    customer_id = request.args.get("customer_id", type=int)

    conn = get_db_connection()
    customers = conn.execute("""
        SELECT customerId, firstName || ' ' || lastName AS name
        FROM   customer
        ORDER BY lastName, firstName
    """).fetchall()

    rows = []
    selected_name = None
    if customer_id is not None:
        selected = conn.execute(
            "SELECT firstName || ' ' || lastName AS name "
            "FROM customer WHERE customerId = ?",
            (customer_id,),
        ).fetchone()
        selected_name = selected["name"] if selected else None
        rows = conn.execute("""
            SELECT  r.roomNumber,
                    r.roomType,
                    ra.actualCheckIn,
                    ra.actualCheckOut,
                    res.reservationStatus,
                    COALESCE(SUM(ch.amount), 0) AS totalCharged
            FROM    room_assignment ra
                    JOIN room        r   ON ra.roomId        = r.roomId
                    JOIN reservation res ON ra.reservationId = res.reservationId
                    LEFT JOIN charge ch  ON ch.roomAssignmentId = ra.assignmentId
            WHERE   ra.guestId = ?
            GROUP BY ra.assignmentId
            ORDER BY ra.actualCheckIn DESC
        """, (customer_id,)).fetchall()
    conn.close()

    columns = [
        {"key": "roomNumber",        "header": "Room"},
        {"key": "roomType",          "header": "Type"},
        {"key": "actualCheckIn",     "header": "Check-In"},
        {"key": "actualCheckOut",    "header": "Check-Out"},
        {"key": "reservationStatus", "header": "Status"},
        {"key": "totalCharged",      "header": "Total Charged ($)"},
    ]

    description = "Pick a guest to see every room they have been assigned to."
    if selected_name:
        description = f"Stay history for {selected_name}."

    return render_template(
        "report.html",
        title="Guest Stay History",
        description=description,
        columns=columns,
        rows=rows,
        form_kind="customer",
        form_values={"customer_id": customer_id if customer_id is not None else ""},
        customers=customers,
    )


# Q13: All facilities at the complex
@app.route("/facilities")
def facilities():
    conn = get_db_connection()
    rows = conn.execute("""
        SELECT  f.facilityName,
                f.facilityType,
                f.locationDescription,
                hc.complexName
        FROM    facility f
                JOIN hotel_complex hc ON f.complexId = hc.complexId
        ORDER BY f.facilityType, f.facilityName
    """).fetchall()
    conn.close()
    columns = [
        {"key": "facilityName",        "header": "Facility"},
        {"key": "facilityType",        "header": "Type"},
        {"key": "locationDescription", "header": "Location"},
        {"key": "complexName",         "header": "Complex"},
    ]
    return render_template(
        "report.html",
        title="Facilities at the Complex",
        description="Every facility (restaurants, gyms, business centers, "
                    "spas, etc.) registered against a hotel complex.",
        columns=columns,
        rows=rows,
    )


# Search
@app.route("/search", methods=["POST"])
def search():
    term = request.form.get("search", "").strip()
    conn = get_db_connection()

    customers = conn.execute("""
        SELECT customerId, firstName || ' ' || lastName AS name, email, phone
        FROM   customer
        WHERE  lower(firstName || ' ' || lastName) LIKE lower(?)
            OR lower(email) LIKE lower(?)
        ORDER BY lastName, firstName
    """, (f"%{term}%", f"%{term}%")).fetchall()

    rooms = conn.execute("""
        SELECT r.roomNumber, r.roomType, r.status,
               r.baseRentalRate, w.wingDesignation
        FROM   room r
               JOIN wing w ON r.wingId = w.wingId
        WHERE  CAST(r.roomNumber AS TEXT) LIKE ?
            OR lower(r.roomType) LIKE lower(?)
        ORDER BY w.wingSequenceNumber, r.roomNumber
    """, (f"%{term}%", f"%{term}%")).fetchall()

    conn.close()
    return render_template(
        "search.html",
        term=term,
        customers=customers,
        rooms=rooms,
    )


# Add Reservation
@app.route("/add-reservation", methods=["GET", "POST"])
def add_reservation():
    conn = get_db_connection()

    if request.method == "POST":
        customer_id            = request.form.get("customerId", type=int)
        event_id               = request.form.get("eventId",    type=int)
        check_in               = request.form.get("checkInDate",  "").strip()
        check_out              = request.form.get("checkOutDate", "").strip()
        num_guests             = request.form.get("numGuests", type=int) or 1
        deposit_required       = 1 if request.form.get("advanceDepositRequired") == "on" else 0
        deposit_amount         = request.form.get("advanceDepositAmount", type=int)
        deposit_paid           = 1 if request.form.get("depositPaid") == "on" else 0
        reservation_status     = request.form.get("reservationStatus") or "PENDING"
        reservation_date       = datetime.now().strftime("%Y-%m-%d")

        conn.execute("""
            INSERT INTO reservation
                (customerId, eventId, reservationDate, checkInDate, checkOutDate,
                 numGuests, reservationStatus,
                 advanceDepositRequired, advanceDepositAmount, depositPaid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_id, event_id, reservation_date, check_in, check_out,
              num_guests, reservation_status,
              deposit_required, deposit_amount, deposit_paid))
        conn.commit()
        conn.close()
        flash("Reservation created.", "success")
        return redirect(url_for("missing_deposits"))

    customers = conn.execute("""
        SELECT customerId, firstName || ' ' || lastName AS name
        FROM   customer ORDER BY lastName, firstName
    """).fetchall()
    events = conn.execute("""
        SELECT eventId, eventName FROM event ORDER BY eventName
    """).fetchall()
    conn.close()

    return render_template(
        "add_reservation.html",
        customers=customers,
        events=events,
    )


# Add Customer
@app.route("/add-customer", methods=["GET", "POST"])
def add_customer():
    conn = get_db_connection()

    if request.method == "POST":
        first_name             = request.form.get("firstName", "").strip()
        last_name              = request.form.get("lastName", "").strip()
        email                  = request.form.get("email", "").strip()
        phone                  = request.form.get("phone", "").strip()
        address                = request.form.get("address", "").strip()
        organization_id        = request.form.get("organizationId", type=int)
        qualification_rating   = request.form.get("qualificationRating") or "NEW"
        payment_promptness     = request.form.get("paymentPromptness") or "FAIR"
        confidential_location  = 1 if request.form.get("confidentialLocation") == "on" else 0

        conn.execute("""
            INSERT INTO customer
                (firstName, lastName, email, phone, address,
                 organizationId, qualificationRating, paymentPromptness,
                 confidentialLocation)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, address,
              organization_id, qualification_rating, payment_promptness,
              confidential_location))
        conn.commit()
        conn.close()
        flash(f"{first_name} {last_name} added to guest records.", "success")
        return redirect(url_for("guests"))

    organizations = conn.execute("""
        SELECT organizationId, orgName FROM organization ORDER BY orgName
    """).fetchall()
    conn.close()

    return render_template(
        "add_customer.html",
        organizations=organizations,
    )


# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    return render_template("error.html", error=e), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
