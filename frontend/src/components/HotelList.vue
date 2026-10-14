<script setup>
import { ref, computed, watch, nextTick } from 'vue';
import HotelCard from './HotelCard.vue';

const props = defineProps({
  hotels: {
    type: Array,
    default: () => [],
  },
  selectedHotelId: {
    type: String,
    default: null,
  },
  shortlistedIds: {
    type: Object, // Set or Object of IDs
    default: () => new Set(),
  },
});

const emit = defineEmits(['select-hotel', 'toggle-shortlist']);

const sortBy = ref('distance'); // 'distance' | 'name'
const listContainerRef = ref(null);

const sortedHotels = computed(() => {
  const list = [...props.hotels];
  if (sortBy.value === 'distance') {
    list.sort((a, b) => (a.distance_meters || 0) - (b.distance_meters || 0));
  } else if (sortBy.value === 'name') {
    list.sort((a, b) => (a.name || '').localeCompare(b.name || ''));
  }
  return list;
});

// Auto-scroll the selected hotel into view if changed
watch(
  () => props.selectedHotelId,
  async (newId) => {
    if (!newId || !listContainerRef.value) return;
    await nextTick();
    const el = listContainerRef.value.querySelector(`[data-hotel-id="${newId}"]`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }
);

function isHotelShortlisted(hotel) {
  if (props.shortlistedIds instanceof Set) {
    return props.shortlistedIds.has(hotel.place_id);
  }
  return !!props.shortlistedIds[hotel.place_id];
}
</script>

<template>
  <div class="hotel-list-pane">
    <div class="list-controls-bar">
      <div class="count-label">
        <strong>{{ hotels.length }}</strong> place{{ hotels.length === 1 ? '' : 's' }} listed
      </div>
      <div class="sort-selector">
        <label for="sort-select" class="sort-label">Sort by:</label>
        <select id="sort-select" v-model="sortBy" class="sort-dropdown">
          <option value="distance">Distance (Closest)</option>
          <option value="name">Name (A-Z)</option>
        </select>
      </div>
    </div>

    <div ref="listContainerRef" class="hotel-cards-scroll">
      <div
        v-for="hotel in sortedHotels"
        :key="hotel.place_id"
        :data-hotel-id="hotel.place_id"
      >
        <HotelCard
          :hotel="hotel"
          :is-selected="selectedHotelId === hotel.place_id"
          :is-shortlisted="isHotelShortlisted(hotel)"
          @select="emit('select-hotel', $event)"
          @toggle-shortlist="emit('toggle-shortlist', $event)"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.hotel-list-pane {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.list-controls-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.6rem 0.5rem 0.75rem 0.5rem;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 0.75rem;
}

.count-label {
  font-size: 0.88rem;
  color: var(--secondary);
}

.sort-selector {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.sort-label {
  font-size: 0.8rem;
  color: var(--text-muted);
}

.sort-dropdown {
  font-size: 0.82rem;
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-color);
  background: #ffffff;
  color: var(--text-main);
  outline: none;
}

.sort-dropdown:focus {
  border-color: var(--primary);
}

.hotel-cards-scroll {
  flex: 1;
  overflow-y: auto;
  padding-right: 0.35rem;
}

/* Custom scrollbar */
.hotel-cards-scroll::-webkit-scrollbar {
  width: 6px;
}
.hotel-cards-scroll::-webkit-scrollbar-track {
  background: transparent;
}
.hotel-cards-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 9999px;
}
.hotel-cards-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>
