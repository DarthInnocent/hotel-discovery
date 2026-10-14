<script setup>
import { ref, onMounted, computed } from 'vue';
import ZipSearchInput from './components/ZipSearchInput.vue';
import StatusBanner from './components/StatusBanner.vue';
import HotelList from './components/HotelList.vue';
import HotelMap from './components/HotelMap.vue';
import ShortlistDrawer from './components/ShortlistDrawer.vue';
import {
  searchHotels,
  getShortlist,
  addToShortlist,
  removeFromShortlist,
  checkBackendHealth,
} from './services/api';

// Search and results state
// UI State: 'idle' | 'loading' | 'results' | 'invalid_input' | 'unresolved_zip' | 'no_results' | 'failed_request'
const uiState = ref('idle');
const statusMessage = ref('');
const currentZip = ref('');
const searchCenter = ref(null);
const hotels = ref([]);
const selectedHotelId = ref(null);

// Shortlist state (persistent in SQLite)
const shortlist = ref([]);
const isShortlistOpen = ref(false);
const shortlistLoading = ref(false);

// Backend health check state
const backendHealth = ref({ checked: false, ok: false, geoapifyConfigured: false });

// Toast notification
const toast = ref({ show: false, message: '', type: 'info' });
let toastTimer = null;

function showToast(message, type = 'info') {
  if (toastTimer) clearTimeout(toastTimer);
  toast.value = { show: true, message, type };
  toastTimer = setTimeout(() => {
    toast.value.show = false;
  }, 3500);
}

// Compute set of shortlisted place IDs for quick lookup
const shortlistedIdsSet = computed(() => {
  return new Set(shortlist.value.map((item) => item.place_id));
});

// Load persistent shortlist from SQLite backend
async function fetchShortlist() {
  shortlistLoading.value = true;
  try {
    const data = await getShortlist();
    shortlist.value = data.shortlist || [];
  } catch (err) {
    console.error('Failed to fetch shortlist:', err);
  } finally {
    shortlistLoading.value = false;
  }
}

// Check backend connectivity on mount
async function checkHealth() {
  const result = await checkBackendHealth();
  if (result.ok) {
    backendHealth.value = {
      checked: true,
      ok: true,
      geoapifyConfigured: !!result.data?.geoapify_configured,
    };
  } else {
    backendHealth.value = { checked: true, ok: false, geoapifyConfigured: false };
  }
}

// Perform ZIP Code search
async function handleSearch(zipCode) {
  currentZip.value = zipCode;
  uiState.value = 'loading';
  statusMessage.value = '';
  selectedHotelId.value = null;

  const res = await searchHotels(zipCode);

  if (res.status === 'results') {
    uiState.value = 'results';
    searchCenter.value = res.data.search_center;
    hotels.value = res.data.results || [];
    if (hotels.value.length > 0) {
      selectedHotelId.value = hotels.value[0].place_id;
    }
  } else if (res.status === 'no_results') {
    uiState.value = 'no_results';
    searchCenter.value = res.data?.search_center || null;
    hotels.value = [];
    statusMessage.value = res.message;
  } else if (res.status === 'invalid_input') {
    uiState.value = 'invalid_input';
    hotels.value = [];
    searchCenter.value = null;
    statusMessage.value = res.message;
  } else if (res.status === 'unresolved_zip') {
    uiState.value = 'unresolved_zip';
    hotels.value = [];
    searchCenter.value = null;
    statusMessage.value = res.message;
  } else {
    // failed_request (Distinguished from empty search)
    uiState.value = 'failed_request';
    hotels.value = [];
    searchCenter.value = null;
    statusMessage.value = res.message;
  }
}

// Select a hotel (synchronized between list and map)
function handleSelectHotel(hotel) {
  selectedHotelId.value = hotel.place_id;
}

// Toggle persistent shortlist
async function handleToggleShortlist(hotel) {
  const isAlreadySaved = shortlistedIdsSet.value.has(hotel.place_id);

  if (isAlreadySaved) {
    try {
      await removeFromShortlist(hotel.place_id);
      shortlist.value = shortlist.value.filter((h) => h.place_id !== hotel.place_id);
      showToast(`Removed "${hotel.name || 'hotel'}" from shortlist.`, 'info');
    } catch (err) {
      showToast(`Error removing from shortlist: ${err.message}`, 'error');
    }
  } else {
    try {
      const saved = await addToShortlist(hotel, currentZip.value);
      shortlist.value = [saved, ...shortlist.value];
      showToast(`Saved "${hotel.name || 'hotel'}" to shortlist!`, 'success');
    } catch (err) {
      showToast(`Error saving to shortlist: ${err.message}`, 'error');
    }
  }
}

// Handle remove from shortlist drawer
async function handleRemoveShortlistItem(placeId) {
  try {
    await removeFromShortlist(placeId);
    shortlist.value = shortlist.value.filter((h) => h.place_id !== placeId);
    showToast('Hotel removed from shortlist.', 'info');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

// Handle select item from shortlist drawer to focus on map
function handleSelectShortlistItem(item) {
  // If item is not in current search results, add it so the map can render it
  const existsInCurrent = hotels.value.some((h) => h.place_id === item.place_id);
  if (!existsInCurrent) {
    hotels.value = [item, ...hotels.value];
    searchCenter.value = {
      latitude: item.latitude,
      longitude: item.longitude,
      city: item.city,
      state: item.state,
      postcode: item.postcode || 'Saved',
      formatted: item.formatted_address,
    };
    uiState.value = 'results';
  }
  selectedHotelId.value = item.place_id;
  isShortlistOpen.value = false;
  showToast(`Focused map on "${item.name}".`, 'info');
}

onMounted(() => {
  checkHealth();
  fetchShortlist();
});
</script>

<template>
  <div class="app-layout">
    <!-- Application Header -->
    <header class="app-header">
      <div class="header-container">
        <div class="brand-group">
          <span class="brand-icon">🏨</span>
          <div>
            <h1 class="brand-title">Hotel Discovery</h1>
            <p class="brand-subtitle">
              U.S. ZIP Search & Synchronized Map within 5 km
            </p>
          </div>
        </div>

        <div class="header-actions">
          <!-- Backend Status Pill -->
          <div
            class="status-pill"
            :class="{ 'pill-online': backendHealth.ok, 'pill-offline': backendHealth.checked && !backendHealth.ok }"
            :title="backendHealth.ok ? 'Backend API online' : 'Backend API unreachable'"
          >
            <span class="status-dot"></span>
            <span class="status-label">
              {{ backendHealth.ok ? 'API Online' : 'Connecting...' }}
            </span>
          </div>

          <!-- Shortlist Drawer Toggle -->
          <button
            type="button"
            class="shortlist-toggle-btn"
            @click="isShortlistOpen = true"
            title="Open persistent shortlist"
          >
            <span class="shortlist-btn-icon">⭐</span>
            <span class="shortlist-btn-label">Shortlist</span>
            <span class="shortlist-badge">{{ shortlist.length }}</span>
          </button>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <main class="main-content">
      <div class="content-container">
        <!-- Search Input Bar -->
        <ZipSearchInput
          :loading="uiState === 'loading'"
          :initial-zip="currentZip"
          @search="handleSearch"
        />

        <!-- Status & Feedback Banner -->
        <StatusBanner
          :state="uiState"
          :message="statusMessage"
          :search-center="searchCenter"
          :total-results="hotels.length"
          :searched-zip="currentZip"
        />

        <!-- Initial Welcome State (when idle) -->
        <div v-if="uiState === 'idle'" class="welcome-card">
          <div class="welcome-icon">🗺️</div>
          <h2>Explore Hotels by U.S. ZIP Code</h2>
          <p>
            Enter any five-digit U.S. ZIP code (such as <strong>90210</strong> or <strong>02138</strong>).
            FastAPI resolves the location using Geoapify and plots all hotels within exactly <strong>5 km</strong> on a synchronized Leaflet map and list.
          </p>
          <div class="features-grid">
            <div class="feature-box">
              <span class="feature-icon">🎯</span>
              <h4>Exact Search Center</h4>
              <p>Search center is the returned ZIP location point, not traveler location or random address.</p>
            </div>
            <div class="feature-box">
              <span class="feature-icon">🔄</span>
              <h4>Synchronized Selection</h4>
              <p>Selecting any hotel in the list highlights and centers it on the Leaflet map, and vice versa.</p>
            </div>
            <div class="feature-box">
              <span class="feature-icon">🛡️</span>
              <h4>Honest Representation</h4>
              <p>Strictly displays actual Geoapify fields without inventing fake prices, reviews, or booking counts.</p>
            </div>
            <div class="feature-box">
              <span class="feature-icon">💾</span>
              <h4>Persistent Shortlist</h4>
              <p>Save favorite hotels directly to SQLite database; persists permanently across page reloads.</p>
            </div>
          </div>
        </div>

        <!-- Synchronized Split View: List & Map -->
        <div
          v-else-if="uiState === 'results' || (uiState === 'no_results' && searchCenter)"
          class="discovery-split-view"
        >
          <!-- Left Column: Hotel List -->
          <div class="list-column">
            <HotelList
              :hotels="hotels"
              :selected-hotel-id="selectedHotelId"
              :shortlisted-ids="shortlistedIdsSet"
              @select-hotel="handleSelectHotel"
              @toggle-shortlist="handleToggleShortlist"
            />
          </div>

          <!-- Right Column: Leaflet Map -->
          <div class="map-column">
            <HotelMap
              :search-center="searchCenter"
              :hotels="hotels"
              :selected-hotel-id="selectedHotelId"
              :shortlisted-ids="shortlistedIdsSet"
              @select-hotel="handleSelectHotel"
              @toggle-shortlist="handleToggleShortlist"
            />
          </div>
        </div>
      </div>
    </main>

    <!-- Shortlist Drawer Modal -->
    <ShortlistDrawer
      :is-open="isShortlistOpen"
      :shortlist="shortlist"
      :loading="shortlistLoading"
      @close="isShortlistOpen = false"
      @remove-item="handleRemoveShortlistItem"
      @select-item="handleSelectShortlistItem"
    />

    <!-- Toast Notification -->
    <div
      v-if="toast.show"
      class="toast-notification"
      :class="`toast-${toast.type}`"
    >
      {{ toast.message }}
    </div>
  </div>
</template>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: #ffffff;
  border-bottom: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 0;
  z-index: 50;
}

.header-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.85rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.brand-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.brand-icon {
  font-size: 1.8rem;
}

.brand-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-main);
  letter-spacing: -0.01em;
}

.brand-subtitle {
  font-size: 0.82rem;
  color: var(--text-muted);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  background: #f1f5f9;
  color: var(--text-muted);
  font-weight: 500;
}

.status-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #94a3b8;
}

.pill-online {
  background: #ecfdf5;
  color: #065f46;
}

.pill-online .status-dot {
  background: #10b981;
}

.pill-offline {
  background: #fef2f2;
  color: #991b1b;
}

.pill-offline .status-dot {
  background: #ef4444;
}

.shortlist-toggle-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: var(--primary);
  color: #ffffff;
  padding: 0.5rem 1rem;
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  font-weight: 600;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
}

.shortlist-toggle-btn:hover {
  background: var(--primary-hover);
  transform: translateY(-1px);
}

.shortlist-btn-icon {
  font-size: 1rem;
}

.shortlist-badge {
  background: #ffffff;
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.1rem 0.45rem;
  border-radius: 9999px;
}

.main-content {
  flex: 1;
  padding: 1.5rem 1.5rem 2.5rem 1.5rem;
}

.content-container {
  max-width: 1400px;
  margin: 0 auto;
}

/* Welcome Card */
.welcome-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 2.5rem 2rem;
  text-align: center;
  max-width: 900px;
  margin: 2rem auto;
  box-shadow: var(--shadow-sm);
}

.welcome-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
}

.welcome-card h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-main);
  margin-bottom: 0.75rem;
}

.welcome-card p {
  color: var(--secondary);
  font-size: 0.95rem;
  line-height: 1.6;
  max-width: 680px;
  margin: 0 auto 2rem auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.25rem;
  text-align: left;
}

.feature-box {
  background: var(--bg-main);
  padding: 1.25rem;
  border-radius: var(--radius-md);
  border: 1px solid var(--border-color);
}

.feature-icon {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.5rem;
}

.feature-box h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 0.35rem;
}

.feature-box p {
  font-size: 0.82rem;
  color: var(--text-muted);
  line-height: 1.4;
  margin: 0;
}

/* Split View */
.discovery-split-view {
  display: grid;
  grid-template-columns: 420px 1fr;
  gap: 1.5rem;
  height: calc(100vh - 220px);
  min-height: 550px;
}

@media (max-width: 960px) {
  .discovery-split-view {
    grid-template-columns: 1fr;
    height: auto;
  }

  .map-column {
    min-height: 400px;
    order: -1;
  }
}

.list-column {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 1rem;
  box-shadow: var(--shadow-sm);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.map-column {
  background: #ffffff;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  height: 100%;
}

/* Toast */
.toast-notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 0.75rem 1.25rem;
  border-radius: var(--radius-md);
  font-size: 0.88rem;
  font-weight: 500;
  box-shadow: var(--shadow-lg);
  z-index: 1200;
  animation: slideUp 0.2s ease;
}

.toast-success {
  background: #10b981;
  color: #ffffff;
}

.toast-info {
  background: #1e293b;
  color: #ffffff;
}

.toast-error {
  background: #ef4444;
  color: #ffffff;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
</style>
