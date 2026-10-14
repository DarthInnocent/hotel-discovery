# Hotel Discovery: U.S. ZIP Code Explorer & Persistent Shortlist

A pair-programmed web application that allows travelers to enter any five-digit U.S. ZIP code, discover nearby hotel accommodations within 5 km on a synchronized list and Leaflet map, and save selected places to a persistent SQLite shortlist.

---

## 🎯 Architecture & MVC Responsibilities

The application maintains clear **Model–View–Controller (MVC)** separation across frontend and backend:

### Backend (FastAPI + SQLite + Pydantic)
- **Model** (`backend/app/models/db_models.py`, `backend/app/schemas/hotel.py`):
  - Defines the SQLite relational schema and indexes for the persistent `shortlist` table.
  - Pydantic models for validated search center, hotel places, shortlist requests, and responses.
  - Strict honest data contract: no invented prices, star ratings, room availability, or simulated bookings.
- **Service** (`backend/app/services/geoapify_service.py`):
  - Validates five-digit U.S. ZIP codes preserving leading zeros (e.g. `02138`, `01001`).
  - Calls Geoapify Geocoding API (`/v1/geocode/search`) to resolve the U.S. postcode location.
  - **Integrity Guarantee**: Verifies that the resolved country is the United States and the returned postcode establishes the requested ZIP code. Lookups that do not establish the requested code fail explicitly and never silently become a different-location search.
  - Calls Geoapify Places API v2 (`/v2/places`) with `circle:{lon},{lat},5000` to find hotel accommodations within 5 km of the returned point.
  - Distinguishes service failures (401/403/500/network timeout) from empty results, returning HTTP 502/503 rather than empty 200s.
- **Controller** (`backend/app/controllers/shortlist_controller.py`, `backend/app/api/endpoints.py`):
  - Manages SQLite persistence and transactions with clean context management.
  - HTTP controller routing `/api/hotels/search`, `/api/shortlist`, and `/api/health`.

### Frontend (Vue 3 + Leaflet)
- **View / Presentation Layer** (`frontend/src/`):
  - `ZipSearchInput.vue`: User entry with real-time numeric 5-digit validation, leading zeros preservation, and test sample chips (`90210`, `02138`, `10001`, `01001`, `00000`).
  - `StatusBanner.vue`: Clearly distinguishes all 6 interface states (**loading**, **results**, **invalid input**, **unresolved ZIP code**, **no nearby results**, and **failed request**). Never presents a service failure as an empty search.
  - `HotelList.vue` & `HotelCard.vue`: Scrollable list with distance sorting, honest property labeling ("Name not provided", "Address not provided"), coordinates, and shortlist toggle.
  - `HotelMap.vue`: Leaflet map using OpenStreetMap imagery tiles (requiring no client secret key). Renders the exact search center marker, a 5 km perimeter circle, and interactive pins for all returned hotels.
  - `ShortlistDrawer.vue`: Traveler's saved places drawer; persists permanently in SQLite across browser reloads.
  - `App.vue`: Coordinates bidirectional synchronization—clicking a hotel in the list highlights and centers it on the map; clicking a marker on the map highlights and scrolls to the card in the list.

---

## 🔒 Security & Credentials Policy

1. **Backend Credentials**:
   - The Geoapify API key is configured in `backend/.env` as `GEOAPIFY_API_KEY=...`.
   - `.env` and `*.db` are strictly listed in `.gitignore` and are **never** committed to version control.
2. **Frontend Safety**:
   - The backend geocoding and Places API key is **never** copied into the frontend bundle or configuration.
   - All external Geoapify requests pass through the FastAPI backend.
   - Leaflet map imagery is provided via OpenStreetMap tiles with standard public attribution (`&copy; OpenStreetMap contributors`), completely free of leaked credentials.

---

## 🚦 Interface States Overview

| State | Trigger | Interface Behavior |
| --- | --- | --- |
| **Loading** | User initiates search | Pulsing blue spinner; status message explaining postcode resolution and 5 km radius search. |
| **Results** | ZIP resolves & hotels returned | Synchronized list and map; 5 km boundary circle; search center coordinates; total count. |
| **Invalid Input** | Input is not exactly 5 numeric digits | Warning banner explaining 5-digit numeric requirement with leading zeros. |
| **Unresolved ZIP** | ZIP not found in U.S. / mismatch | Amber alert; guarantees lookup does not silently redirect to another location. |
| **No Nearby Results** | ZIP resolved, 0 hotels in 5 km | Neutral banner showing resolved city/state with clear explanation of 0 accommodations in 5 km. |
| **Failed Request** | Geoapify error / 401 / offline | Destructive red error; troubleshoots API key in `.env`; never described as 0 results. |

---

## 🚀 Running the Project

### Prerequisites
- Python 3.13 (or 3.10+)
- Node.js (v18+)

### 1. Backend Setup & Run

```bash
cd backend

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# (Optional) Verify or install dependencies
pip install -r requirements.txt

# Configure your Geoapify API key in backend/.env
# Copy example if not present:
cp .env.example .env
# Edit .env and set GEOAPIFY_API_KEY=your_key_here

# Start the FastAPI server
uvicorn main:app --reload --port 8000
```
Backend API will be accessible at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### 2. Frontend Setup & Run

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Frontend application will be accessible at `http://localhost:5173`.

---

## 🧪 Repeatable Verification

To run the complete automated test suite and verification checks:

```bash
# From project root:
.\backend\venv\Scripts\python.exe verify_project.py
```

This verification script runs:
1. Python interpreter and `sqlite3` capability check.
2. Five-digit U.S. ZIP code validation (testing leading zeros like `02138` and `01001`, plus invalid string rejection).
3. Honest interface data contract check (confirming no invented prices, ratings, or room counts).
4. SQLite persistent shortlist CRUD and cross-session restart verification.
5. Pytest automated test suite (18 unit and integration tests covering geocoding, places, mock API responses, mismatch protection, and HTTP endpoints).
