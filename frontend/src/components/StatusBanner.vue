<script setup>
defineProps({
  state: {
    type: String,
    required: true,
    // 'idle' | 'loading' | 'results' | 'invalid_input' | 'unresolved_zip' | 'no_results' | 'failed_request'
  },
  message: {
    type: String,
    default: '',
  },
  searchCenter: {
    type: Object,
    default: null,
  },
  totalResults: {
    type: Number,
    default: 0,
  },
  searchedZip: {
    type: String,
    default: '',
  },
});
</script>

<template>
  <div v-if="state !== 'idle'" class="status-container">
    <!-- State 1: Loading -->
    <div v-if="state === 'loading'" class="status-banner banner-loading">
      <div class="banner-icon-wrapper">
        <span class="pulsing-spinner"></span>
      </div>
      <div class="banner-content">
        <h4 class="banner-title">Locating Hotels...</h4>
        <p class="banner-desc">
          Resolving U.S. ZIP code <strong>{{ searchedZip }}</strong> with Geoapify and searching for hotel accommodations within 5 km of the returned point.
        </p>
      </div>
    </div>

    <!-- State 2: Results -->
    <div v-else-if="state === 'results'" class="status-banner banner-results">
      <div class="banner-icon-wrapper">
        <span class="banner-emoji">📍</span>
      </div>
      <div class="banner-content">
        <div class="results-header">
          <h4 class="banner-title">
            Found {{ totalResults }} hotel{{ totalResults === 1 ? '' : 's' }} within 5 km
          </h4>
          <span class="badge-success">Search Verified</span>
        </div>
        <p class="banner-desc" v-if="searchCenter">
          <strong>Search Center:</strong>
          {{ searchCenter.city ? searchCenter.city + ', ' : '' }}{{ searchCenter.state }} {{ searchCenter.postcode }}
          <span class="coords-tag">({{ searchCenter.latitude.toFixed(4) }}, {{ searchCenter.longitude.toFixed(4) }})</span>
          <span class="center-note">— radius fixed at 5.0 km</span>
        </p>
      </div>
    </div>

    <!-- State 3: Invalid Input -->
    <div v-else-if="state === 'invalid_input'" class="status-banner banner-invalid">
      <div class="banner-icon-wrapper">
        <span class="banner-emoji">⚠️</span>
      </div>
      <div class="banner-content">
        <h4 class="banner-title">Invalid Input</h4>
        <p class="banner-desc">
          {{ message || 'Please enter a valid five-digit U.S. ZIP code, including leading zeros (e.g. 90210, 02138).' }}
        </p>
      </div>
    </div>

    <!-- State 4: Unresolved ZIP Code -->
    <div v-else-if="state === 'unresolved_zip'" class="status-banner banner-unresolved">
      <div class="banner-icon-wrapper">
        <span class="banner-emoji">❓</span>
      </div>
      <div class="banner-content">
        <h4 class="banner-title">Unresolved U.S. ZIP Code</h4>
        <p class="banner-desc">
          {{ message || `ZIP code '${searchedZip}' could not be established as a valid U.S. postcode location.` }}
        </p>
        <p class="policy-note">
          Strict Location Integrity: A lookup that does not establish the requested U.S. ZIP code will never silently become a different-location search.
        </p>
      </div>
    </div>

    <!-- State 5: No Nearby Results -->
    <div v-else-if="state === 'no_results'" class="status-banner banner-no-results">
      <div class="banner-icon-wrapper">
        <span class="banner-emoji">🔍</span>
      </div>
      <div class="banner-content">
        <h4 class="banner-title">No Hotels Found Nearby</h4>
        <p class="banner-desc">
          {{ message || `The ZIP code was resolved, but no hotel accommodations were found within 5 km of the center.` }}
        </p>
        <p class="banner-desc" v-if="searchCenter">
          Search center resolved at <strong>{{ searchCenter.city }}, {{ searchCenter.state }} {{ searchCenter.postcode }}</strong>
          ({{ searchCenter.latitude.toFixed(4) }}, {{ searchCenter.longitude.toFixed(4) }}).
        </p>
      </div>
    </div>

    <!-- State 6: Failed Request -->
    <div v-else-if="state === 'failed_request'" class="status-banner banner-failed">
      <div class="banner-icon-wrapper">
        <span class="banner-emoji">🚫</span>
      </div>
      <div class="banner-content">
        <h4 class="banner-title">Service Request Failed</h4>
        <p class="banner-desc">
          {{ message || 'Failed to communicate with the Geoapify hotel discovery service.' }}
        </p>
        <div class="service-troubleshoot">
          <strong>Notice:</strong> This is a service error, not an empty search.
          Please ensure your Geoapify API key is set in <code>backend/.env</code> (e.g. <code>GEOAPIFY_API_KEY=your_key</code>) and that your backend server is running.
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.status-container {
  margin-bottom: 1.25rem;
}

.status-banner {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  border-width: 1.5px;
  border-style: solid;
  transition: all 0.2s ease;
}

.banner-icon-wrapper {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-emoji {
  font-size: 1.4rem;
  line-height: 1;
}

.banner-content {
  flex: 1;
}

.results-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.25rem;
}

.banner-title {
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.3;
}

.banner-desc {
  font-size: 0.9rem;
  margin-top: 0.25rem;
  line-height: 1.4;
}

.coords-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.center-note {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-left: 0.35rem;
}

.policy-note {
  font-size: 0.82rem;
  margin-top: 0.4rem;
  font-style: italic;
  opacity: 0.9;
}

.badge-success {
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 700;
  background: #10b981;
  color: #ffffff;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
}

/* Banner Theme Variants */
.banner-loading {
  background: var(--primary-light);
  border-color: var(--primary-border);
  color: #1e40af;
}

.banner-results {
  background: #f0fdf4;
  border-color: #bbf7d0;
  color: #166534;
}

.banner-invalid {
  background: var(--warning-bg);
  border-color: var(--warning-border);
  color: #92400e;
}

.banner-unresolved {
  background: #fff7ed;
  border-color: #ffedd5;
  color: #9a3412;
}

.banner-no-results {
  background: #f8fafc;
  border-color: #cbd5e1;
  color: #475569;
}

.banner-failed {
  background: var(--danger-bg);
  border-color: var(--danger-border);
  color: #991b1b;
}

.service-troubleshoot {
  margin-top: 0.5rem;
  font-size: 0.82rem;
  padding: 0.5rem 0.75rem;
  background: rgba(255, 255, 255, 0.7);
  border-radius: var(--radius-sm);
  border: 1px dashed rgba(239, 68, 68, 0.4);
}

.service-troubleshoot code {
  background: rgba(0, 0, 0, 0.06);
  padding: 0.15rem 0.35rem;
  border-radius: 3px;
  font-size: 0.85em;
}

.pulsing-spinner {
  width: 22px;
  height: 22px;
  border: 3px solid rgba(37, 99, 235, 0.25);
  border-top-color: #2563eb;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
