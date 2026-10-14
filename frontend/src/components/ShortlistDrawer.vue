<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  shortlist: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(['close', 'remove-item', 'select-item']);
</script>

<template>
  <div v-if="isOpen" class="drawer-backdrop" @click="emit('close')">
    <div class="drawer-panel" @click.stop>
      <div class="drawer-header">
        <div class="title-group">
          <h2 class="drawer-title">⭐ Traveler's Shortlist</h2>
          <span class="count-badge">{{ shortlist.length }} Saved</span>
        </div>
        <button
          type="button"
          class="close-btn"
          @click="emit('close')"
          aria-label="Close Shortlist"
        >
          ✕
        </button>
      </div>

      <div class="drawer-body">
        <div v-if="loading" class="drawer-loading">
          <span class="spinner"></span>
          <p>Loading your saved places...</p>
        </div>

        <div v-else-if="shortlist.length === 0" class="drawer-empty">
          <span class="empty-icon">📂</span>
          <h3>Your shortlist is empty</h3>
          <p>
            When you explore hotels around any U.S. ZIP code, click the
            <strong>🤍 Shortlist</strong> button on any card or map pin to save it here.
          </p>
          <p class="persistence-hint">
            💡 Places in your shortlist are securely saved to your local SQLite database and persist across browser reloads.
          </p>
        </div>

        <div v-else class="shortlist-items">
          <p class="persistence-notice">
            💾 Stored permanently in SQLite database.
          </p>

          <div
            v-for="item in shortlist"
            :key="item.place_id"
            class="shortlist-card"
          >
            <div class="item-header">
              <h4 class="item-name">{{ item.name || 'Hotel name not provided' }}</h4>
              <button
                type="button"
                class="remove-btn"
                @click="emit('remove-item', item.place_id)"
                title="Remove from shortlist"
              >
                🗑️ Remove
              </button>
            </div>

            <p class="item-address">
              📍 {{ item.formatted_address || item.street || `${item.city || ''}, ${item.state || ''} ${item.postcode || ''}` || 'Address not provided' }}
            </p>

            <div class="item-meta">
              <span class="item-cat">{{ item.category || 'Hotel' }}</span>
              <span v-if="item.distance_meters != null" class="item-dist">
                📏 {{ (item.distance_meters / 1000).toFixed(2) }} km away
              </span>
              <span class="item-coords">
                ({{ item.latitude.toFixed(4) }}, {{ item.longitude.toFixed(4) }})
              </span>
            </div>

            <div class="item-actions">
              <button
                type="button"
                class="view-on-map-btn"
                @click="emit('select-item', item)"
              >
                🗺️ Focus on Map
              </button>
              <a
                v-if="item.website"
                :href="item.website"
                target="_blank"
                rel="noopener noreferrer"
                class="item-link"
              >
                🌐 Website
              </a>
              <a
                v-if="item.phone"
                :href="`tel:${item.phone}`"
                class="item-link"
              >
                📞 {{ item.phone }}
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
  z-index: 1000;
  display: flex;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease;
}

.drawer-panel {
  width: 100%;
  max-width: 440px;
  background: #ffffff;
  height: 100%;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.25s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateX(100%); }
  to { transform: translateX(0); }
}

.drawer-header {
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.drawer-title {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-main);
}

.count-badge {
  font-size: 0.75rem;
  font-weight: 700;
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid var(--primary-border);
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
}

.close-btn {
  font-size: 1.2rem;
  color: var(--text-muted);
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  transition: all 0.15s ease;
}

.close-btn:hover {
  background: #f1f5f9;
  color: var(--text-main);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
}

.drawer-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--secondary);
}

.empty-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
}

.drawer-empty h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-main);
  margin-bottom: 0.5rem;
}

.drawer-empty p {
  font-size: 0.88rem;
  line-height: 1.5;
  color: var(--text-muted);
  margin-bottom: 1rem;
}

.persistence-hint {
  font-size: 0.82rem;
  background: #f8fafc;
  padding: 0.75rem;
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border-color);
}

.persistence-notice {
  font-size: 0.78rem;
  color: #15803d;
  background: #f0fdf4;
  padding: 0.35rem 0.65rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  font-weight: 500;
}

.shortlist-items {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.shortlist-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 1rem;
  box-shadow: var(--shadow-sm);
  transition: all 0.15s ease;
}

.shortlist-card:hover {
  border-color: #cbd5e1;
  box-shadow: var(--shadow-md);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.item-name {
  font-size: 0.98rem;
  font-weight: 600;
  color: var(--text-main);
  line-height: 1.3;
}

.remove-btn {
  font-size: 0.75rem;
  color: #ef4444;
  background: #fef2f2;
  border: 1px solid #fecaca;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-weight: 600;
  transition: all 0.15s ease;
  white-space: nowrap;
}

.remove-btn:hover {
  background: #dc2626;
  color: #ffffff;
}

.item-address {
  font-size: 0.82rem;
  color: var(--secondary);
  margin-bottom: 0.4rem;
}

.item-meta {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  font-size: 0.75rem;
  margin-bottom: 0.6rem;
}

.item-cat {
  background: #f1f5f9;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  color: var(--secondary);
}

.item-dist {
  color: #1e40af;
  font-weight: 500;
}

.item-coords {
  font-family: ui-monospace, monospace;
  color: var(--text-subtle);
}

.item-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
  padding-top: 0.5rem;
  border-top: 1px dashed var(--border-color);
}

.view-on-map-btn {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-light);
  border: 1px solid var(--primary-border);
  padding: 0.25rem 0.6rem;
  border-radius: 4px;
  transition: all 0.15s ease;
}

.view-on-map-btn:hover {
  background: var(--primary);
  color: #ffffff;
}

.item-link {
  font-size: 0.78rem;
  color: var(--text-muted);
  text-decoration: none;
}

.item-link:hover {
  color: var(--primary);
  text-decoration: underline;
}

.drawer-loading {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--text-muted);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(37, 99, 235, 0.2);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
  margin-bottom: 0.75rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
