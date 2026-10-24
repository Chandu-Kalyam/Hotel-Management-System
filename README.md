# Hotel Management System

A beginner-friendly hotel front-desk application built with Python, OOP,
Streamlit, JSON, and TXT files.

## Features

- Dashboard with room, booking, arrival, departure, and billing summaries.
- Guest registration, search, update, validation, and deletion.
- Standard, Deluxe, and Suite room management with capacity, pricing, and
  operational status.
- Date-based reservations with room and guest conflict prevention.
- Check-in, cancellation, checkout, and booking-state validation.
- Hotel services, itemized bills, 5% demonstration tax, and discounts.
- TXT stay-history records saved after successful checkout.
- Clear validation and empty states for front-desk users.

## Technology stack

- Python 3.10+
- Streamlit 1.46.1
- Python standard library
- JSON and TXT file handling

No API, database, FastAPI, authentication, online payment, AI, cloud service,
Pydantic, logging framework, Pytest, or not used.

## Project structure

```text
app.py                  Streamlit interface and navigation
guest/                  Guest and GuestManager
room/                   Room types and RoomManager
booking/                Booking and BookingManager
billing/                Services, bills, and BillingManager
storage/                FileManager for JSON/TXT files
data/                   JSON records and history.txt
```

## Setup and run

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit, normally
`http://localhost:8501`.

Run the commands from the project root, the folder that contains
`app.py` and `requirements.txt`.

## Application navigation

The sidebar provides these pages:

- **Dashboard** - room availability, booking activity, arrivals, departures,
  and billing summaries.
- **Guest Management** - register, search, update, and delete guests when
  deletion is allowed.
- **Room Management** - view rooms, prices, capacities, and operational
  statuses.
- **Booking Management** - create reservations, check guests in, cancel
  bookings, and review booking states.
- **Services** - review the available hotel services.
- **Billing & Checkout** - create bills, add services, apply discounts, and
  complete checkout.
- **Stay History** - search completed-stay records saved in `history.txt`.

## Data and configuration

No environment variables are required. The application uses local files only:

- `guests.json` - guest records
- `rooms.json` - room inventory
- `bookings.json` - reservations
- `services.json` - sample hotel services
- `bills.json` - generated bills
- `history.txt` - completed-stay history

Sample rooms and services are initialized only when their files are missing.
On a completely new copy, guest, booking, bill, and history files begin
empty. This repository may already contain fictional demonstration records in
the `data/` folder; those records are preserved across application startup and
Streamlit reruns.

The application creates `data/history.txt` automatically if it is missing.
Successful checkout appends one completed-stay line to that file without
replacing earlier entries. The Stay History page reads this file directly.
You do not need to create it manually.

Use fictional demonstration data only. Do not add real guest information,
credentials, or secrets.

## Team contributions

1. **Chaitanaya - Guest Management**
   - Guest entity, GuestManager, registration, search, update, deletion, and
     guest validation.

2. **Chandu Reddy - Room Management**
   - Room hierarchy, room types, inventory, capacity, pricing, and room status.

3. **Venket Ram - Booking Management**
   - Booking entity, reservations, date validation, availability, conflict
     detection, check-in, cancellation, and checkout transitions.

4. **Naveen - Billing Management**
   - Service, Bill, BillingManager, service charges, tax, discounts, checkout,
     bill persistence, and stay history.
