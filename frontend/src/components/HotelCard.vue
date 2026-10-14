<script setup>
const props = defineProps({
  hotel: {
    type: Object,
    required: true,
  },
  isSelected: {
    type: Boolean,
    default: false,
  },
  isShortlisted: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['select', 'toggle-shortlist']);

function onCardClick() {
  emit('select', props.hotel);
}

function onToggleShortlist(e) {
  e.stopPropagation();
  emit('toggle-shortlist', props.hotel);
}
</script>

<template>
  <div
    class="hotel-card"
    :class="{ 'card-selected': isSelected, 'card-shortlisted': isShortlisted }"
    @click="onCardClick"
    tabindex="0"
    role="button"
    :aria-pressed="isSelected"
  >
    <div class="card-header">
      <div class="header-main">
        <h3 class="hotel-name">
          {{ hotel.name || 'Hotel name not provided' }}
        </h3>
        <span class="category-pill">{{ hotel.category || 'Lodging' }}</span>
      </div>

      <!-- Persistent Shortlist Action -->
      <button
        type="button"
        class="shortlist-btn"
        :class="{ 'is-saved': isShortlisted }"
        @click="onToggleShortlist"
        :title="isShortlisted ? 'Remove from Shortlist' : 'Save to Shortlist'"
        aria-label="Toggle Shortlist"
      >
        <span class="heart-icon">{{ isShortlisted ? '❤️' : '🤍' }}</span>
        <span class="shortlist-text">{{ isShortlisted ? 'Saved' : 'Shortlist' }}</span>
      </button>
    </div>

    <!-- Distance from search center -->
    <div class="distance-badge" v-if="hotel.distance_meters !== null && hotel.distance_meters !== undefined">
      📏 <strong>{{ (hotel.distance_meters / 1000).toFixed(2) }} km</strong> from ZIP center
    </div>

    <!-- Address (Honest reporting: if missing, honest label) -->
    <p class="hotel-address">
      📍 {{ hotel.formatted_address || hotel.street || (hotel.city ? `${hotel.city}, ${hotel.state || ''}` : 'Address not provided') }}
    </p>

    <!-- Coordinates -->
    <div class="coordinates-row">
      <span class="coord-label">Coordinates:</span>
      <span class="coord-value">{{ hotel.latitude.toFixed(5) }}, {{ hotel.longitude.toFixed(5) }}</span>
    </div>

    <!-- Optional Contact Info if returned by Geoapify (Honest: no dummy data) -->
    <div class="contact-links" v-if="hotel.website || hotel.phone">
      <a
        v-if="hotel.website"
        :href="hotel.website"
        target="_blank"
        rel="noopener noreferrer"
        class="contact-link"
        @click.stop
      >
        🌐 Official Website
      </a>
      <a
        v-if="hotel.phone"
        :href="`tel:${hotel.phone}`"
        class="contact-link"
        @click.stop
      >
        📞 {{ hotel.phone }}
      </a>
    </div>

    <!-- Selection indicator footer -->
    <div class="card-footer" v-if="isSelected">
      <span class="active-badge">✓ Active on Map</span>
    </div>
  </div>
</template>

<style scoped>
.hotel-card {
  background: var(--bg-card);
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1.1rem;
  margin-bottom: 0.85rem;
  transition: all 0.2s ease;
  cursor: pointer;
  position: relative;
}

.hotel-card:hover {
  border-color: #93c5fd;
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.hotel-card.card-selected {
  border-color: var(--primary);
  background: #f8faff;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2), var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.header-main {
  flex: 1;
}

.hotel-name {
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
}

.category-pill {
  display: inline-block;
  margin-top: 0.25rem;
  font-size: 0.72rem;
  padding: 0.15rem 0.5rem;
  background: #f1f5f9;
  color: var(--secondary);
  border-radius: 4px;
  font-weight: 500;
}

.shortlist-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.4rem 0.75rem;
  border-radius: var(--radius-sm);
  background: #f8fafc;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.shortlist-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: var(--text-main);
}

.shortlist-btn.is-saved {
  background: #fef2f2;
  border-color: #fecaca;
  color: #dc2626;
}

.distance-badge {
  display: inline-block;
  font-size: 0.82rem;
  color: #1e40af;
  background: var(--primary-light);
  padding: 0.2rem 0.55rem;
  border-radius: var(--radius-sm);
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.hotel-address {
  font-size: 0.88rem;
  color: var(--secondary);
  line-height: 1.4;
  margin-bottom: 0.5rem;
}

.coordinates-row {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.78rem;
  color: var(--text-subtle);
  margin-bottom: 0.5rem;
}

.coord-value {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  color: var(--text-muted);
}

.contact-links {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-top: 0.6rem;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border-color);
}

.contact-link {
  font-size: 0.8rem;
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

.contact-link:hover {
  text-decoration: underline;
}

.card-footer {
  margin-top: 0.6rem;
  padding-top: 0.4rem;
  border-top: 1px solid rgba(37, 99, 235, 0.15);
}

.active-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
}
</style>
