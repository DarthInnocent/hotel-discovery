<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  loading: {
    type: Boolean,
    default: false,
  },
  initialZip: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['search']);

const zipInput = ref(props.initialZip || '');
const touched = ref(false);

const isValidZipFormat = computed(() => {
  return /^\d{5}$/.test(zipInput.value.trim());
});

const validationError = computed(() => {
  if (!touched.value && !zipInput.value) return null;
  const val = zipInput.value.trim();
  if (!val) return 'ZIP code cannot be empty.';
  if (!/^\d+$/.test(val)) return 'ZIP code must only contain numeric digits.';
  if (val.length !== 5) return `ZIP code must be exactly 5 digits (currently ${val.length}).`;
  return null;
});

function handleInput(e) {
  touched.value = true;
  // Restrict to max 5 digits and numeric characters
  const raw = e.target.value;
  zipInput.value = raw.replace(/\D/g, '').slice(0, 5);
}

function submitSearch() {
  touched.value = true;
  const cleaned = zipInput.value.trim();
  if (!isValidZipFormat.value) {
    return;
  }
  emit('search', cleaned);
}

function selectSample(sampleZip) {
  zipInput.value = sampleZip;
  touched.value = true;
  emit('search', sampleZip);
}

function clearInput() {
  zipInput.value = '';
  touched.value = false;
}
</script>

<template>
  <div class="zip-search-box">
    <form @submit.prevent="submitSearch" class="search-form">
      <div class="input-wrapper" :class="{ 'has-error': touched && validationError }">
        <span class="input-icon">📍</span>
        <input
          type="text"
          inputmode="numeric"
          pattern="[0-9]*"
          maxlength="5"
          placeholder="Enter 5-digit U.S. ZIP (e.g. 90210, 02138)"
          :value="zipInput"
          @input="handleInput"
          class="zip-input"
          :disabled="loading"
          aria-label="U.S. ZIP Code"
        />
        <button
          v-if="zipInput"
          type="button"
          @click="clearInput"
          class="clear-btn"
          title="Clear input"
          :disabled="loading"
        >
          ✕
        </button>
      </div>

      <button
        type="submit"
        class="search-submit-btn"
        :disabled="loading || (!isValidZipFormat && touched)"
      >
        <span v-if="loading" class="spinner-small"></span>
        <span v-else>🔍 Search Hotels</span>
      </button>
    </form>

    <!-- Client-side real-time validation hint -->
    <div v-if="touched && validationError" class="input-validation-msg">
      ⚠️ {{ validationError }}
    </div>

    <!-- Quick Sample ZIP shortcuts for easy testing -->
    <div class="samples-row">
      <span class="samples-label">Try sample:</span>
      <button
        type="button"
        class="sample-chip"
        @click="selectSample('90210')"
        :disabled="loading"
      >
        90210 (Beverly Hills)
      </button>
      <button
        type="button"
        class="sample-chip"
        @click="selectSample('02138')"
        :disabled="loading"
        title="Tests leading zero retention"
      >
        02138 (Cambridge, MA)
      </button>
      <button
        type="button"
        class="sample-chip"
        @click="selectSample('10001')"
        :disabled="loading"
      >
        10001 (New York, NY)
      </button>
      <button
        type="button"
        class="sample-chip"
        @click="selectSample('01001')"
        :disabled="loading"
        title="Tests leading zero retention"
      >
        01001 (Agawam, MA)
      </button>
      <button
        type="button"
        class="sample-chip sample-chip-unresolved"
        @click="selectSample('00000')"
        :disabled="loading"
        title="Tests unresolved ZIP handling"
      >
        00000 (Unresolved test)
      </button>
    </div>
  </div>
</template>

<style scoped>
.zip-search-box {
  background: var(--bg-card);
  padding: 1.25rem 1.5rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  margin-bottom: 1.25rem;
}

.search-form {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  flex-wrap: wrap;
}

.input-wrapper {
  position: relative;
  flex: 1;
  min-width: 260px;
  display: flex;
  align-items: center;
  background: #ffffff;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: var(--border-focus);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
}

.input-wrapper.has-error {
  border-color: var(--danger);
  box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.15);
}

.input-icon {
  padding-left: 0.85rem;
  font-size: 1.1rem;
}

.zip-input {
  width: 100%;
  padding: 0.75rem 0.85rem;
  font-size: 1rem;
  border: none;
  outline: none;
  background: transparent;
  color: var(--text-main);
  letter-spacing: 0.05em;
  font-weight: 500;
}

.zip-input::placeholder {
  color: var(--text-subtle);
  font-weight: 400;
  letter-spacing: normal;
}

.clear-btn {
  padding: 0 0.85rem;
  color: var(--text-muted);
  font-size: 0.9rem;
}

.clear-btn:hover {
  color: var(--text-main);
}

.search-submit-btn {
  background: var(--primary);
  color: #ffffff;
  padding: 0.75rem 1.5rem;
  border-radius: var(--radius-md);
  font-size: 0.95rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, transform 0.1s ease;
  min-width: 150px;
}

.search-submit-btn:hover:not(:disabled) {
  background: var(--primary-hover);
}

.search-submit-btn:active:not(:disabled) {
  transform: translateY(1px);
}

.search-submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.input-validation-msg {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--danger);
  font-weight: 500;
}

.samples-row {
  margin-top: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.samples-label {
  font-size: 0.8rem;
  font-weight: 500;
  color: var(--text-muted);
}

.sample-chip {
  font-size: 0.78rem;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  background: var(--primary-light);
  color: var(--primary);
  border: 1px solid var(--primary-border);
  font-weight: 500;
  transition: all 0.15s ease;
}

.sample-chip:hover:not(:disabled) {
  background: var(--primary);
  color: #ffffff;
}

.sample-chip-unresolved {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fecaca;
}

.sample-chip-unresolved:hover:not(:disabled) {
  background: #b91c1c;
  color: #ffffff;
}

.spinner-small {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-top-color: #ffffff;
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
