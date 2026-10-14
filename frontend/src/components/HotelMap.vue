<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue';
import L from 'leaflet';

const props = defineProps({
  searchCenter: {
    type: Object,
    default: null,
  },
  hotels: {
    type: Array,
    default: () => [],
  },
  selectedHotelId: {
    type: String,
    default: null,
  },
  shortlistedIds: {
    type: Object,
    default: () => new Set(),
  },
});

const emit = defineEmits(['select-hotel', 'toggle-shortlist']);

const mapContainer = ref(null);
let map = null;
let centerMarker = null;
let radiusCircle = null;
let hotelMarkersLayer = null;
const markerMap = new Map(); // place_id -> L.marker

// Custom icons using Leaflet DivIcon
const centerIcon = L.divIcon({
  className: 'custom-center-marker',
  html: `<div style="
    width: 20px;
    height: 20px;
    background: #2563eb;
    border: 3px solid #ffffff;
    border-radius: 50%;
    box-shadow: 0 0 10px rgba(37,99,235,0.8);
  "></div>`,
  iconSize: [20, 20],
  iconAnchor: [10, 10],
});

function createHotelIcon(isSelected = false, isShortlisted = false) {
  const bg = isSelected ? '#1d4ed8' : (isShortlisted ? '#dc2626' : '#0284c7');
  const scale = isSelected ? 'scale(1.2)' : 'scale(1.0)';
  const shadow = isSelected ? '0 0 10px rgba(29, 78, 216, 0.9)' : '0 2px 5px rgba(0,0,0,0.3)';

  return L.divIcon({
    className: 'custom-hotel-pin',
    html: `<div style="
      transform: ${scale};
      background: ${bg};
      color: white;
      width: 28px;
      height: 28px;
      border-radius: 50% 50% 50% 0;
      transform-origin: bottom left;
      rotate: -45deg;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid white;
      box-shadow: ${shadow};
      transition: all 0.2s ease;
    ">
      <span style="rotate: 45deg; font-size: 13px;">${isShortlisted ? '★' : '🏨'}</span>
    </div>`,
    iconSize: [28, 28],
    iconAnchor: [14, 28],
    popupAnchor: [0, -28],
  });
}

function initMap() {
  if (!mapContainer.value || map) return;

  // Initialize Leaflet map. Initial default center: USA centroid
  map = L.map(mapContainer.value, {
    center: [39.8283, -98.5795],
    zoom: 4,
    zoomControl: true,
  });

  // OpenStreetMap Tile Layer (no secret keys needed; client-appropriate public attribution)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OpenStreetMap</a> contributors',
    maxZoom: 19,
  }).addTo(map);

  hotelMarkersLayer = L.layerGroup().addTo(map);

  // Resize fix
  setTimeout(() => {
    map?.invalidateSize();
  }, 200);
}

function updateMapState() {
  if (!map) return;

  // Clear existing hotel markers
  hotelMarkersLayer.clearLayers();
  markerMap.clear();

  // Handle Search Center
  if (props.searchCenter && props.searchCenter.latitude && props.searchCenter.longitude) {
    const centerLatLng = [props.searchCenter.latitude, props.searchCenter.longitude];

    if (centerMarker) {
      centerMarker.setLatLng(centerLatLng);
    } else {
      centerMarker = L.marker(centerLatLng, { icon: centerIcon }).addTo(map);
    }

    centerMarker.bindPopup(`
      <div style="font-family: inherit; font-size: 13px;">
        <strong style="color: #2563eb;">📍 Search Center</strong><br/>
        <strong>ZIP ${props.searchCenter.postcode}</strong> — ${props.searchCenter.city || ''}, ${props.searchCenter.state || ''}<br/>
        <span style="color: #64748b; font-size: 11px;">Lat: ${props.searchCenter.latitude.toFixed(4)}, Lon: ${props.searchCenter.longitude.toFixed(4)}</span><br/>
        <span style="color: #475569; font-size: 11px;">Search perimeter: 5 km radius</span>
      </div>
    `);

    // 5 km (5000m) Radius Circle
    if (radiusCircle) {
      radiusCircle.setLatLng(centerLatLng);
    } else {
      radiusCircle = L.circle(centerLatLng, {
        radius: 5000,
        color: '#2563eb',
        fillColor: '#3b82f6',
        fillOpacity: 0.1,
        weight: 1.5,
        dashArray: '4, 6',
      }).addTo(map);
    }
  } else {
    if (centerMarker) {
      map.removeLayer(centerMarker);
      centerMarker = null;
    }
    if (radiusCircle) {
      map.removeLayer(radiusCircle);
      radiusCircle = null;
    }
  }

  // Add markers for all returned hotels
  const bounds = L.latLngBounds([]);

  if (props.searchCenter) {
    bounds.extend([props.searchCenter.latitude, props.searchCenter.longitude]);
  }

  props.hotels.forEach((hotel) => {
    if (!hotel.latitude || !hotel.longitude) return;

    const latLng = [hotel.latitude, hotel.longitude];
    bounds.extend(latLng);

    const isSelected = props.selectedHotelId === hotel.place_id;
    const isShortlisted = props.shortlistedIds instanceof Set
      ? props.shortlistedIds.has(hotel.place_id)
      : !!props.shortlistedIds[hotel.place_id];

    const marker = L.marker(latLng, {
      icon: createHotelIcon(isSelected, isShortlisted),
      zIndexOffset: isSelected ? 1000 : 100,
    });

    const distKm = hotel.distance_meters != null ? (hotel.distance_meters / 1000).toFixed(2) : null;

    marker.bindPopup(`
      <div style="min-width: 180px; font-family: inherit;">
        <h4 style="margin: 0 0 4px 0; font-size: 14px; font-weight: 600; color: #0f172a;">
          ${hotel.name || 'Hotel name not provided'}
        </h4>
        <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">
          ${hotel.formatted_address || hotel.street || ''}
        </div>
        ${distKm ? `<div style="font-size: 12px; color: #2563eb; font-weight: 500; margin-bottom: 6px;">📏 ${distKm} km from center</div>` : ''}
        <div style="display: flex; gap: 6px; margin-top: 6px;">
          <button id="popup-btn-${hotel.place_id}" style="
            background: ${isShortlisted ? '#fef2f2' : '#f0fdf4'};
            color: ${isShortlisted ? '#dc2626' : '#16a34a'};
            border: 1px solid ${isShortlisted ? '#fecaca' : '#bbf7d0'};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
          ">
            ${isShortlisted ? '❤️ Shortlisted' : '🤍 Add to Shortlist'}
          </button>
        </div>
      </div>
    `);

    // Handle marker click -> select in list
    marker.on('click', () => {
      emit('select-hotel', hotel);
    });

    marker.on('popupopen', () => {
      const btn = document.getElementById(`popup-btn-${hotel.place_id}`);
      if (btn) {
        btn.onclick = (e) => {
          e.stopPropagation();
          emit('toggle-shortlist', hotel);
        };
      }
    });

    marker.addTo(hotelMarkersLayer);
    markerMap.set(hotel.place_id, marker);
  });

  // Fit bounds if we have points
  if (bounds.isValid()) {
    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }

  // Open popup for selected hotel if any
  if (props.selectedHotelId && markerMap.has(props.selectedHotelId)) {
    const selectedMarker = markerMap.get(props.selectedHotelId);
    selectedMarker.openPopup();
  }
}

// Watchers for reactive synchronization
watch(
  () => [props.hotels, props.searchCenter, props.shortlistedIds],
  () => {
    updateMapState();
  },
  { deep: true }
);

watch(
  () => props.selectedHotelId,
  (newId) => {
    if (!map) return;

    // Update icons for all markers to highlight selected
    props.hotels.forEach((hotel) => {
      const marker = markerMap.get(hotel.place_id);
      if (marker) {
        const isSelected = hotel.place_id === newId;
        const isShortlisted = props.shortlistedIds instanceof Set
          ? props.shortlistedIds.has(hotel.place_id)
          : !!props.shortlistedIds[hotel.place_id];
        marker.setIcon(createHotelIcon(isSelected, isShortlisted));
        marker.setZIndexOffset(isSelected ? 1000 : 100);

        if (isSelected) {
          map.panTo(marker.getLatLng(), { animate: true, duration: 0.5 });
          marker.openPopup();
        }
      }
    });
  }
);

onMounted(() => {
  initMap();
  updateMapState();
});

onBeforeUnmount(() => {
  if (map) {
    map.remove();
    map = null;
  }
});
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapContainer" class="hotel-map-container"></div>
    <div class="map-legend">
      <div class="legend-item">
        <span class="legend-dot center-dot"></span>
        <span>ZIP Search Center</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot hotel-dot"></span>
        <span>Hotel Place</span>
      </div>
      <div class="legend-item">
        <span class="legend-dot saved-dot"></span>
        <span>Shortlisted</span>
      </div>
      <div class="legend-item">
        <span class="legend-line"></span>
        <span>5 km Perimeter</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.map-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 480px;
  border-radius: var(--radius-md);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.hotel-map-container {
  width: 100%;
  height: 100%;
  min-height: 480px;
}

.map-legend {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(4px);
  padding: 0.5rem 0.75rem;
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-md);
  font-size: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  z-index: 800;
  border: 1px solid var(--border-color);
  pointer-events: none;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--text-main);
  font-weight: 500;
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.center-dot {
  background: #2563eb;
  border: 2px solid #ffffff;
  box-shadow: 0 0 4px rgba(37, 99, 235, 0.6);
}

.hotel-dot {
  background: #0284c7;
}

.saved-dot {
  background: #dc2626;
}

.legend-line {
  width: 14px;
  height: 2px;
  background: #2563eb;
  display: inline-block;
  border-top: 1px dashed #2563eb;
}
</style>
