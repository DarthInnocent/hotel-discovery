const API_BASE = '/api';

/**
 * Searches hotels by 5-digit U.S. ZIP code.
 * Distinguishes results, invalid input, unresolved ZIP, no nearby results, and failed request.
 */
export async function searchHotels(zipCode) {
  try {
    const trimmed = String(zipCode || '').trim();
    const res = await fetch(`${API_BASE}/hotels/search?zip_code=${encodeURIComponent(trimmed)}`);
    const data = await res.json().catch(() => ({}));

    if (res.status === 200) {
      if (!data.results || data.results.length === 0) {
        return {
          status: 'no_results',
          data,
          message: `No hotels found within 5 km of ${data.search_center?.city || 'the area'} (${data.zip_code}).`,
        };
      }
      return {
        status: 'results',
        data,
      };
    } else if (res.status === 400) {
      return {
        status: 'invalid_input',
        message: data.detail?.message || 'Please enter a valid 5-digit U.S. ZIP code.',
      };
    } else if (res.status === 404) {
      return {
        status: 'unresolved_zip',
        message: data.detail?.message || `ZIP code '${trimmed}' could not be resolved to a valid U.S. postcode location.`,
      };
    } else {
      // 500, 502, 503 or other service failure
      return {
        status: 'failed_request',
        statusCode: res.status,
        message: data.detail?.message || `Hotel service request failed with HTTP status ${res.status}.`,
      };
    }
  } catch (err) {
    return {
      status: 'failed_request',
      message: `Network communication error: ${err.message || 'Unable to reach backend service.'}`,
    };
  }
}

/**
 * Fetches persistent shortlist from SQLite backend.
 */
export async function getShortlist() {
  const res = await fetch(`${API_BASE}/shortlist`);
  if (!res.ok) {
    throw new Error(`Failed to fetch shortlist: HTTP ${res.status}`);
  }
  return await res.json();
}

/**
 * Saves a hotel to persistent shortlist.
 */
export async function addToShortlist(hotel, searchZip = null) {
  const payload = {
    place_id: hotel.place_id,
    name: hotel.name,
    formatted_address: hotel.formatted_address,
    street: hotel.street,
    city: hotel.city,
    state: hotel.state,
    postcode: hotel.postcode,
    latitude: hotel.latitude,
    longitude: hotel.longitude,
    distance_meters: hotel.distance_meters,
    category: hotel.category,
    website: hotel.website,
    phone: hotel.phone,
    search_zip: searchZip,
  };

  const res = await fetch(`${API_BASE}/shortlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to save to shortlist: HTTP ${res.status}`);
  }

  return await res.json();
}

/**
 * Removes a hotel from persistent shortlist.
 */
export async function removeFromShortlist(placeId) {
  const res = await fetch(`${API_BASE}/shortlist/${encodeURIComponent(placeId)}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete from shortlist: HTTP ${res.status}`);
  }

  return await res.json();
}

/**
 * Health check endpoint to verify backend service and configuration.
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) return { ok: false, status: res.status };
    return { ok: true, data: await res.json() };
  } catch (err) {
    return { ok: false, error: err.message };
  }
}
