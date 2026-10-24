# Hotel Management System V1 — GitHub Copilot Instructions

## 1. Project Vision

Build a complete, reliable, beginner-friendly Hotel Management System using Python, Object-Oriented Programming (OOP), Streamlit, JSON, and TXT file handling.

This is strictly **Version 1 (V1)** of a student project. The goal is to demonstrate Python fundamentals, OOP concepts, file handling, practical problem-solving, modular programming, and thoughtful user-interface design.

The application should be functional enough for an end-to-end demonstration and polished enough to showcase in a public GitHub portfolio.

The UI should look professionally designed without making the code unnecessarily complex. Every feature must be understandable, maintainable, and appropriate for the project's learning objectives.

**Do not expand the agreed V1 scope.**

## 2. Fixed Technology Stack and Scope

Use only the following application technologies:

- **Python:** Business logic and application development.
- **Object-Oriented Programming:** Classes, objects, encapsulation, inheritance, polymorphism, and method overriding.
- **Streamlit:** Interactive web-based user interface.
- **JSON:** Persistent structured application data.
- **TXT:** Simple stay-history records.
- **Python standard library:** Dates, file operations, calculations, and other required basic utilities.

Use Streamlit's built-in capabilities wherever practical. Maintain a simple `requirements.txt` containing only the necessary dependencies.

### Explicitly excluded from V1

Do not introduce:

- APIs or FastAPI.
- Databases or database connectors.
- Pydantic.
- Logging frameworks.
- Pytest or additional testing frameworks.
- Authentication or user-account systems.
- Online payment gateways.
- AI features or machine learning.
- Cloud infrastructure, microservices, or deployment complexity.
- Unnecessary third-party libraries or advanced architectural patterns.

Do not add a technology merely to make the project appear more advanced.

## 3. Functional Requirements

### 3.1 Dashboard

Create an attractive, useful hotel operations dashboard displaying information calculated from the application's saved data.

Include:
- Total rooms.
- Available rooms.
- Reserved rooms.
- Occupied rooms.
- Rooms under maintenance.
- Active bookings.
- Today's check-ins and check-outs.
- Recent reservations or relevant hotel activity.
- Useful billing or revenue summaries where the saved records support them.

Metrics must be derived from actual application data. Never hardcode statistics or present fabricated activity as real information.

When data is unavailable, show a useful empty state or clearly identified fictional demonstration data.

### 3.2 Guest Management

Create a `Guest` class and a `GuestManager` class.

Support:
- Registering guests.
- Viewing guest details.
- Searching and listing guests.
- Updating guest information.
- Deleting guests when deletion is permitted.

Guest attributes:
- `guest_id`
- `name`
- `phone`
- `email`
- `address`
- `id_proof`

Expected methods include:
- `update_details()`
- `display_details()`
- `to_dict()`
- `from_dict()`
- `add_guest()`
- `find_guest()`
- `get_guest()`
- `update_guest()`
- `delete_guest()`
- `list_guests()`

Use unique guest identifiers, validate required information, handle unknown IDs, and prevent deletion of guests with active bookings.

For a student demonstration, use fictional guest information only.

### 3.3 Room Management

Create a `Room` base class and the following subclasses:

- `StandardRoom`
- `DeluxeRoom`
- `SuiteRoom`

Create a `RoomManager` class for managing room inventory.

Room attributes should include:
- `room_no`
- `floor`
- `capacity`
- `base_price`
- `status`

Implement appropriate methods for:
- Checking availability.
- Changing room status.
- Calculating room prices.
- Adding and finding rooms.
- Listing available rooms.
- Updating room details or status.
- Converting objects to dictionaries and reconstructing them from dictionaries.

Demonstrate inheritance, encapsulation, method overriding, and polymorphism naturally through room-specific pricing or behavior.

Use the project's agreed example room types and prices where needed.

#### Room status and availability rules

Use consistent statuses such as:
- Available.
- Reserved.
- Occupied.
- Maintenance.

Keep operational room status distinct from date-specific reservation availability.

Before accepting a booking, check the requested dates against existing active reservations and the room's operational status. Never determine availability from a stored status field alone.

Update room status consistently when reservations are confirmed, cancelled, checked in, or checked out. Do not make a room available after checkout when maintenance is required or another applicable booking prevents it.

A future reservation must not incorrectly block a different, non-overlapping stay.

### 3.4 Booking and Reservation Management

Create a `Booking` class and a `BookingManager` class.

Booking attributes should include:
- `booking_id`
- `guest_id`
- `room_no`
- `check_in`
- `check_out`
- `guests_count`
- `status`

Expected methods include:
- `calculate_nights()`
- `confirm()`
- `cancel()`
- `check_in_guest()`
- `checkout()`
- `create_booking()`
- `is_room_available()`
- `detect_conflict()`
- `find_booking()`
- `get_booking()`
- `cancel_booking()`

Validate all booking operations using centralized business rules.

#### Essential booking rules

1. The check-out date must be later than the check-in date.
2. The guest count must be positive and must not exceed room capacity.
3. The referenced guest and room must exist.
4. Rooms must not have overlapping active reservations.
5. Consecutive stays must be allowed when the first booking's checkout date equals the next booking's check-in date.
6. Cancelled bookings must not block room availability.
7. Checked-out and cancelled bookings must not be reactivated accidentally.
8. Invalid state transitions must be rejected with clear messages.
9. A confirmed booking may be checked in.
10. A confirmed booking may be cancelled before check-in.
11. A checked-in booking may be checked out.
12. Checkout before check-in and repeated checkout operations must be rejected.

Keep date comparisons and conflict detection in the booking business logic, not duplicated across UI pages.

For example, a booking from October 10 to October 13 conflicts with another booking for the same room from October 12 to October 14. A booking beginning October 13 is allowed, assuming no other conflict or operational restriction exists.

### 3.5 Hotel Services

Create a `Service` class for additional hotel services such as:
- Room service.
- Laundry.
- Additional amenities.

Service attributes should include:
- `service_id`
- `name`
- `category`
- `price`

Support listing available services and adding service quantities to a guest's stay.

Validate service prices and quantities. Quantities must be positive, and invalid values must be rejected before billing.

### 3.6 Billing and Checkout

Create a `Bill` class and a `BillingManager` class.

The bill should represent:
- `bill_id`
- `booking_id`
- `room_charge`
- `service_charges`
- `tax`
- `discount`
- `total`
- `payment_status`

Provide appropriate methods for:
- Adding services to a bill.
- Calculating room charges.
- Calculating service charges.
- Calculating tax.
- Applying valid discounts.
- Calculating the final total.
- Generating a bill.
- Finding and saving bills.
- Performing valid checkout operations.

#### Billing formula

- Room charge = number of nights × applicable nightly room price.
- Service charges = sum of service price × quantity.
- Subtotal = room charge + service charges.
- Tax = subtotal × configured tax rate.
- Final total = subtotal + tax − valid discount.

Centralize all calculations so that the UI does not duplicate billing logic.

Use one documented, fixed tax-rate configuration appropriate for this demonstration. Do not build a tax-compliance system.

Checkout must save the final bill, update the booking and room states consistently, and preserve completed stay history. A failed operation must not leave the application in an obviously inconsistent state.

Payment status is for recording the demonstration workflow only. Do not implement or claim real payment processing.

### 3.7 Stay History

Preserve completed and relevant cancelled booking records as required by the agreed blueprint.

Support useful history viewing and searching. Maintain references to the related guests, rooms, bookings, and bills.

Append appropriate completed-stay records to `history.txt` without silently replacing earlier history.

## 4. Architecture and Module Responsibilities

Use the following project structure as the architectural guide:

```text
Hotel-Management-System/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── guest/
│   ├── guest.py
│   └── guest_manager.py
│
├── room/
│   ├── room.py
│   └── room_manager.py
│
├── booking/
│   ├── booking.py
│   └── booking_manager.py
│
├── billing/
│   ├── service.py
│   ├── bill.py
│   └── billing_manager.py
│
├── storage/
│   └── file_manager.py
│
└── data/
    ├── guests.json
    ├── rooms.json
    ├── bookings.json
    ├── services.json
    ├── bills.json
    └── history.txt
```

Add small supporting files only when they serve a clear purpose. Do not create unnecessary empty folders or files.

### Module boundaries

- `guest/` owns guest information and guest-management rules.
- `room/` owns room entities, room types, pricing behavior, and room management.
- `booking/` owns reservations, date validation, availability, and booking-state transitions.
- `billing/` owns hotel services, bills, calculations, and checkout coordination.
- `storage/` owns reading and writing JSON/TXT files.
- `data/` holds the runtime data files.
- `app.py` connects the modules to the Streamlit interface.

### Inter-module consistency

- `GuestManager.get_guest(guest_id)` should return the relevant guest or handle an unknown ID consistently.
- `RoomManager` provides room lookups and static room candidates filtered by room type, capacity, and operational status. `BookingManager.get_available_rooms(check_in, check_out, room_type, guests_count)` applies date-specific availability and booking-conflict rules using those candidates and its own booking records.

- `BookingManager.get_booking(booking_id)` should return the relevant booking or handle an unknown ID consistently.
- Billing should use the correct booking, room, stay duration, and selected services.
- All modules should use a consistent serialization approach, including `to_dict()` and `from_dict()` where appropriate.
- The UI should call management classes rather than duplicating business rules.

Keep the business logic understandable for beginner-level Python developers.

## 5. JSON/TXT File Handling and Data Integrity

Create a `FileManager` class for persistence.

Expected responsibilities include:
- Saving JSON data.
- Loading JSON data.
- Appending TXT records.
- Checking whether a file exists.
- Handling missing or malformed files safely.

Use the following filenames:
- `guests.json`
- `rooms.json`
- `bookings.json`
- `services.json`
- `bills.json`
- `history.txt`

### Persistence rules

1. Initialize missing files safely on first run.
2. Never overwrite all existing records simply because the application starts or reruns.
3. Save relevant changes after successful operations.
4. Preserve records when updating individual guests, rooms, bookings, or bills.
5. Handle malformed JSON and file-operation failures with helpful messages.
6. Keep JSON serialization consistent.
7. Avoid duplicating records during reruns or repeated UI actions.
8. Use fictional, clearly identifiable sample data when examples are needed.

Do not add a database or replace file-based persistence with another storage technology.

## 6. Professional UI and User Experience

**A polished interface is a major project priority, but it must look purposeful rather than like a generic AI-generated admin template.**

Design the application as a practical hotel front-desk system that real staff could understand.

### Visual direction

Use a refined boutique-hotel aesthetic:
- Deep navy or charcoal for structure and emphasis.
- Warm white or ivory for backgrounds and content surfaces.
- Restrained champagne-gold or muted teal accents.
- Consistent typography and readable font sizes.
- Clear alignment, generous but efficient spacing, and meaningful visual hierarchy.
- Subtle borders and restrained shadows where appropriate.

Maintain consistency across navigation, page titles, cards, forms, tables, status indicators, and buttons.

Avoid excessive gradients, random accent colors, decorative clutter, excessive animations, oversized headings, excessive emoji, and unnecessary rounded-card layouts.

### Navigation

Provide clear navigation for:
- Dashboard.
- Guest Management.
- Room Management.
- Booking Management.
- Services.
- Billing and Checkout.
- Stay History.

Use a well-organized Streamlit sidebar or another simple, appropriate navigation approach.

### Dashboard design

Prefer a small number of meaningful metrics and useful operational sections over a screen full of decorative widgets.

Where supported by actual saved records, show:
- Room availability and status.
- Upcoming arrivals and departures.
- Recent bookings.
- Billing summaries.
- Relevant charts or operational alerts.

Charts must communicate real information. Do not add charts merely to fill empty space.

### Interaction quality

- Every visible button and control must perform its advertised action.
- Forms must validate inputs before committing changes.
- Destructive operations require confirmation.
- Show useful success, warning, and error messages.
- Provide helpful empty states and clear next actions.
- Preserve relevant user selections during ordinary Streamlit reruns where appropriate.
- Make tables, filters, forms, and status labels readable and consistent.
- Ensure the layout remains usable across common desktop and smaller-window sizes.

Use reusable Streamlit UI functions and centralized, maintainable custom CSS when practical.

### Authenticity and maintainability

The UI must reflect actual application capabilities and saved data. Do not show fake live indicators, fabricated occupancy rates, invented revenue, or nonfunctional interface elements.

Prefer purposeful design and correct workflows over flashy visual effects. Keep styling simple enough for the project team to understand and maintain.

## 7. Error Handling and Input Validation

Use clear, appropriate validation for:
- Required guest fields.
- Unique identifiers.
- Valid room numbers and capacities.
- Valid booking dates.
- Booking conflicts.
- Unknown IDs.
- Invalid booking-state transitions.
- Non-positive service quantities.
- Invalid prices or discounts.
- Billing calculations.
- Missing or malformed files.

Handle expected errors gracefully and provide useful messages to the user.

Avoid silently ignoring exceptions, displaying raw internal errors in the UI, or creating unnecessary layers of exception-handling code.

Use Python's standard capabilities. Do not introduce a logging framework, Pydantic, or other excluded technologies.

## 8. Public GitHub Repository and Privacy

This repository is public.

The local `docs/` directory contains the Hotel Management System V1 blueprint PDF and must remain on the local machine.

- Keep `docs/` listed in `.gitignore`.
- Never force-add, stage intentionally, commit, or push the `docs/` directory or its contents.
- Do not modify the ignore rules to expose the PDF.
- Do not copy the blueprint into tracked project documentation.
- Before suggesting a Git commit or push, verify that `docs/` remains ignored and is not included in staged changes.
- Never commit real guest details, identity documents, personal phone numbers, credentials, or secrets.
- Use fictional demonstration data only.

The application must not depend on the local blueprint PDF to run.

## 9. Development Workflow

Build incrementally. **Never generate the entire application in one massive change.**

Before a substantial implementation step:

1. Inspect the existing repository and its current files.
2. Explain the feature being addressed.
3. Identify which files need to be created or changed.
4. Check that the change agrees with the V1 scope and architecture.
5. Implement one coherent feature at a time.
6. Explain how to run and manually verify the feature.
7. Fix discovered problems before proceeding.

Preserve working code. Do not delete or overwrite existing work without a clear reason.

Use readable naming, appropriate type hints where helpful, simple methods, and explanatory comments only when they improve understanding.

Avoid unnecessary abstractions, duplicated logic, complicated design patterns, or code that a beginner cannot reasonably explain.

### Python Commenting and Docstring Standard

This standard applies to every existing and newly created Python module, class,
and method throughout V1:

- Add a short explanatory comment for each import, stating why that module,
  class, or type is used in that file. Keep the explanation specific to the
  implementation.
- Give every Python module and class a meaningful docstring. Give public
  methods and private methods with non-obvious logic useful docstrings that
  explain their purpose, parameters, return values, and relevant exceptions.
- Explain important constructors, parameters, return values, validation rules,
  loops, conditions, calculations, file operations, and exception handling
  near the logic they describe.
- Explain important OOP concepts and relationships between modules when that
  helps a beginner understand the design.
- Use straightforward, natural English that a Python beginner can understand
  and explain during a project viva.
- Comment generously on meaningful logic, but do not mechanically comment
  every line or repeat obvious statements.
- Review comments and docstrings for accuracy whenever code is created or
  modified. They must remain consistent with the actual implementation.
- Do not change working logic merely to add comments or docstrings.
- Do not add ordinary comments to JSON files. Keep explanations for JSON
  structure in Python docstrings, README documentation, or other appropriate
  text documentation.

Keep this commenting standard compatible with the fixed V1 technology scope:
Python, OOP, Streamlit, JSON, TXT, and the Python standard library only.

### Manual verification

Do not introduce Pytest or another test framework.

After implementing each important feature, provide a concise manual verification checklist covering relevant successful operations and failure cases.

Include checks for:
- Duplicate guest identifiers.
- Unknown guest, room, or booking IDs.
- Invalid or reversed booking dates.
- Overlapping reservations.
- Valid consecutive stays.
- Room-capacity violations.
- Missing JSON files.
- Existing data surviving application restarts.
- Invalid service quantities.
- Incorrect billing totals.
- Checkout before check-in.
- Duplicate checkout attempts.
- Room status after cancellation, check-in, and checkout.

Do not claim that a feature has been verified unless it has actually been checked.

## 10. Final Acceptance Criteria

V1 is complete when it supports the following end-to-end demonstration:

**Register a guest → select an available room → create a valid reservation → check in → add hotel services → generate an itemized bill → complete checkout → save the stay history.**

The completed application must:
- Use Python and OOP appropriately.
- Demonstrate inheritance, encapsulation, polymorphism, and method overriding naturally.
- Provide Guest, Room, Booking, Service, Billing, Storage, and Streamlit UI functionality.
- Prevent conflicting reservations.
- Validate inputs and important state transitions.
- Calculate bills correctly.
- Persist data in JSON/TXT files across application restarts.
- Display an attractive, functional, data-driven interface.
- Preserve historical records.
- Be understandable enough for the four-member student team to explain its modules and complete workflow.
- Include usable setup instructions and a clear README.

**Final scope rule: This is V1 only. Use Python, OOP, Streamlit, JSON, TXT, and the Python standard library. Do not add APIs, FastAPI, databases, Pydantic, logging frameworks, Pytest, authentication, AI features, or cloud infrastructure.**