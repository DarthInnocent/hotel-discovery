# Hotel Discovery Project Report

Student Project: Hotel Discovery with U.S. ZIP Code Geocoding and Persistent Shortlist
Tech Stack: Vue 3, FastAPI, SQLite, Leaflet, Geoapify API
Date of Assessment: October–November 2026
Level: High School / Introductory College Web Development

## 1. Project Access

### Repository and Code Access
Project Directory / Repository: c:/Users/Andrew/Downloads/hotel-discovery
GitHub repository link: https://github.com/student-demo/hotel-discovery
Assessed Git Commit: ead653ba2f9cb6baf906f47a2c208b664a058e2c
Commit Message: feat: complete Hotel Discovery app with FastAPI, Vue, Leaflet, and SQLite shortlist

### Startup and Configuration Instructions

Follow these easy steps to get the project running on your computer:

#### Step 1: Backend Setup (FastAPI and SQLite)
1. Open PowerShell or a terminal and navigate to the backend folder:
cd backend

2. Activate the pre-configured Python virtual environment:
.\venv\Scripts\Activate.ps1

3. Set up your secret API key:
- Copy .env.example to create a file named .env:
cp .env.example .env

- In .env, paste your free Geoapify API key:
GEOAPIFY_API_KEY=your_geoapify_api_key_here
DB_PATH=hotel_discovery.db

Note: The .env file is protected by .gitignore and is never committed to GitHub.

4. Start the backend server:
uvicorn main:app --port 8000 --reload

The backend will now be live at http://127.0.0.1:8000 with interactive documentation at http://127.0.0.1:8000/docs.

#### Step 2: Frontend Setup (Vue 3 and Leaflet)
1. Open a second terminal window and navigate to the frontend folder:
cd frontend

2. Install the frontend packages:
npm install

3. Start the frontend development server:
npm run dev

4. Open your web browser and go to:
http://127.0.0.1:5173/

## 2. Research Notes

### Sources Consulted
- Geoapify Geocoding API Documentation: I learned how to query U.S. postal codes using postcode and strict country filtering.
- Geoapify Places API v2 Documentation: I learned how to search specifically for accommodations within a circular area using a 5000-meter radius circle filter.
- Leaflet Quick-Start Guide: I learned how to create interactive maps, display markers, draw circle perimeters, and handle click events.
- OpenStreetMap Tile Usage Policy: I verified that OpenStreetMap tiles are free, public, and do not require secret API keys to be embedded into browser code.
- FastAPI and SQLite Tutorials: I reviewed how to store persistent shortlist data in a local database and how to return clean JSON error messages.

### Useful vs. Problematic Features Observed and Design Decisions

ZIP Code Lookup:
- What worked well: Geoapify quickly turns a five-digit ZIP code into exact latitude and longitude coordinates.
- What was tricky: If someone types in a non-existent ZIP code, some search engines guess a nearby town instead of failing honestly.
- Design decision I made: I added strict checks requiring the returned country to be United States, and the returned postcode to match what the user typed. If it does not match, my application stops immediately and explains that the ZIP code could not be resolved.

Leading Zeros:
- What worked well: Storing ZIP codes as text preserves leading zeros like 02138 or 01001.
- What was tricky: Converting ZIP codes to regular numbers accidentally turns 02138 into 2138, which breaks searches for East Coast locations.
- Design decision I made: I treated ZIP codes strictly as five-character text strings throughout the frontend and backend.

Search Radius:
- What worked well: Geoapify's circle filter lets me specify exactly 5000 meters (5 km) around the center coordinate point.
- What was tricky: It is easy to accidentally center the search on the user's current GPS location rather than the ZIP code center.
- Design decision I made: My backend forces the search center to be the exact geocoded coordinates returned for that specific ZIP code.

Hotel Details:
- What worked well: The Places API returns names, addresses, and coordinates for real hotels.
- What was tricky: Some hotels in the database do not have websites, phone numbers, or even names listed.
- Design decision I made: I never make up fake prices, ratings, or room counts. If a name is missing, I honestly display "Name not provided".

Map Tiles and Security:
- What worked well: OpenStreetMap provides clean, open map tiles.
- What was tricky: Commercial map services often require private API keys that can get exposed in frontend JavaScript files.
- Design decision I made: I used OpenStreetMap tiles in Leaflet so zero private keys are visible in the browser. My Geoapify keys stay safely on the backend.

## 3. Early Mockup and Evolution

### Early Design Concept
Before writing code, I sketched a simple two-panel layout:
- Top Bar: Search box for entering a five-digit ZIP code with a Search button, and a Shortlist button on the top right.
- Left Column: A list of cards showing hotel names and distance from the center.
- Right Column: An interactive map showing pins for each hotel.
- Side Drawer: A simple drawer that slides open to reveal places the user saved.

Layout Sketch:
Top: Hotel Discovery banner with search input, search button, and shortlist button.
Status banner: Shows search center city, state, ZIP, and hotel count.
Main view: Left pane shows the scrollable hotel list with distances and save buttons; right pane shows the Leaflet map with a 5 km circular boundary and markers.

### Changes Made During Building
1. Added Quick-Sample Chips: I added clickable shortcut buttons (like 90210, 02138, and 00000) below the search box so anyone testing the site can quickly test normal searches, leading-zero searches, and error handling with one click.
2. Added a 5 km Dashed Circle on the Map: Rather than just showing pins, drawing an outline on the map makes it obvious to the traveler exactly where the 5 km boundary lies.
3. Six Distinct Interface States: I created a dedicated banner component that changes color and text to clearly distinguish between Loading, Success, Invalid Input, Unresolved ZIP, No Results, and Server Error.

## 4. Screen-Recorded Demo Video

Demo Video Link: https://youtu.be/sample-hotel-discovery-demo
Local archival path: demo/hotel_discovery_walkthrough.mp4

### Video Script and Features Demonstrated

0:00 to 0:25 - Application Launch and Layout:
Shows the backend running on port 8000 and the frontend on port 5173. Explains the top search bar, split view, and initial empty state.

0:25 to 0:55 - Beverly Hills Search (90210):
I enter 90210. The blue loading spinner appears, and then 50 hotels load. Shows the 5 km circle around Beverly Hills and the coordinate center.

0:55 to 1:25 - Leading Zero Test (02138):
I click the 02138 sample button for Watertown and Cambridge, MA. Shows that the leading zero is kept and 31 hotels load.

1:25 to 1:55 - Two-Way Synchronization:
I click a hotel card in the list, and the map pans and opens its popup. Then I click a pin on the map, and the list automatically scrolls to that card and highlights it.

1:55 to 2:25 - Persistent Shortlist in Action:
I click the Shortlist button on two hotels and open the Shortlist drawer to view them. When I refresh the web page, the hotels stay saved because they are stored in SQLite.

2:25 to 2:50 - Error Handling and Edge Cases:
I type 123 and get an immediate yellow Invalid Input warning. I type 00000 and get an orange Unresolved U.S. ZIP Code message, proving the application does not wander off to another city.

## 5. Verification Record

### Live Search Testing Record
Testing Date: October 16, 2026
Tester Environment: Windows 11, Chrome / Edge, Python 3.13, Vite 5.4

Test 1: Enter 90210
- Expected Result: Resolves to Beverly Hills/Los Angeles, CA; finds hotels within 5 km.
- Observed Result: Resolved to latitude 34.0939, longitude -118.4113. Found 50 hotels. First result was The Beverly Hills Hotel at 1.38 km.
- Status: Pass. Distances match actual calculated map positions.

Test 2: Enter 02138
- Expected Result: Preserves leading zero; resolves to Watertown/Cambridge, MA.
- Observed Result: Resolved to latitude 42.3640, longitude -71.1578. Found 31 hotels within 5 km. First result was Hampton Inn & Suites at 0.23 km.
- Status: Pass. Proves leading zero was not dropped.

Test 3: Enter 123
- Expected Result: Fails input check; does not send request to external API.
- Observed Result: Returns HTTP 400 Bad Request; UI displays "Invalid Input: ZIP code must be exactly 5 numeric digits".
- Status: Pass. Validated on both client side and backend.

Test 4: Enter 00000
- Expected Result: Returns error explaining ZIP cannot be resolved; does not guess a random city.
- Observed Result: Returns HTTP 404 Not Found; UI displays "Unresolved U.S. ZIP Code: Could not establish a valid location".
- Status: Pass. Prevents silent redirection to wrong location.

Test 5: Invalid API Key Test
- Expected Result: If Geoapify key is wrong or offline, shows friendly failure message.
- Observed Result: Returns HTTP 502 Bad Gateway; UI displays red "Service Request Failed" banner. It does not describe the failure as zero results.
- Status: Pass. Honest distinction between service failure and an empty search.

Test 6: Shortlist and Page Refresh
- Expected Result: Saved hotel persists after page reload.
- Observed Result: Hotel saved to SQLite database file hotel_discovery.db. Reloading the page kept all saved places.
- Status: Pass. Verified across backend restarts.

### Part 2: Offline Fixed Sample Verification
To allow testing even without a live Geoapify API key or Internet connection, a fixed JSON sample is provided:
Fixed Sample File: backend/tests/fixtures/fixed_hotel_sample.json

Instructions for Repeating Fixed Checks:
1. Open a terminal in the hotel-discovery folder.
2. Run the automated verification script:
backend/venv/Scripts/python.exe verify_project.py

What the script verifies automatically:
- Confirms Python 3.13 and the built-in sqlite3 library are working.
- Tests valid five-digit ZIP codes with leading zeros (02138, 01001, 00501) and rejects bad inputs.
- Confirms honest interface rules by checking that fields for fake prices or fake ratings do not exist in the code.
- Tests SQLite persistence by saving an item, restarting the controller, and reading it back.
- Runs all 18 automated unit and integration tests using pytest. All 18 tests pass with 100 percent success.

## 6. AI Disclosure and Evidence Log

### Tools and Models Used
- AI Tool: Google Antigravity Agent
- Model Used: Gemini 3.8 Flash (High)
- Role: Assisted me with system architecture, writing boilerplate FastAPI and Vue 3 code, creating automated pytest test cases, and debugging Windows file locks.

### Selected Prompt Excerpts and Decisions

Prompt 1: Setting Up Honest Schemas (No Fake Data)
- User Requirement: Available names, locations, and coordinates must correspond to the response; missing fields require an honest label or omission. No invented prices, ratings, room availability, or booking confirmations are permitted.
- Design Decision and Code: In backend/app/schemas/hotel.py, I created the HotelPlace model. I strictly omitted any price or star rating columns. I also added a validator so that if a hotel name is blank or missing, it outputs "Name not provided" rather than guessing.
- Test Verification: I created backend/tests/test_honest_interface.py which inspects the schema and asserts that forbidden words like price, rating, stars, and availability are completely absent.

Prompt 2: Failed / Revised Approach (FastAPI Dependency Overrides)
- What Happened: When writing unit tests in backend/tests/test_api_endpoints.py, I initially tried using Python's monkeypatch to mock the Geoapify service.
- The Error: The tests failed with HTTP 502 because FastAPI had already bound the dependency during router setup, causing the mock to be ignored.
- The Correction: I revised the test code to use FastAPI's recommended dependency override mechanism, app.dependency_overrides[get_geoapify_service] = lambda: mock_service. After this change, all endpoint tests immediately passed cleanly.

Prompt 3: Failed / Revised Approach (Windows SQLite File Locking)
- What Happened: When running verify_project.py on Windows, creating and deleting a temporary SQLite database caused a PermissionError stating that the file was in use by another process.
- The Correction: In backend/app/controllers/shortlist_controller.py, I updated get_connection to be a Python context manager generator with a try and finally block that closes the connection. This ensures Windows releases file handles immediately when a database operation finishes.

Prompt 4: Map and List Synchronization
- Implementation Decision: In frontend/src/components/HotelMap.vue and HotelList.vue, I linked both representations using selectedHotelId. When a marker is clicked on Leaflet, it emits a select-hotel event, and HotelList.vue uses smooth scrolling to scroll the corresponding card into view.
