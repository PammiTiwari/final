<template>
  <div class="loc-picker">
    <div v-if="!readonly" class="loc-toolbar">
      <button type="button" class="btn btn-sm btn-outline" @click="useMyLocation" :disabled="locating">
        {{ locating ? 'Locating…' : '📍 Use my current location' }}
      </button>
      <span class="loc-hint">or click / drag the marker on the map</span>
    </div>
    <div ref="mapEl" class="loc-map" :class="{ readonly }"></div>
    <p v-if="status" class="loc-status">{{ status }}</p>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

// Fix Leaflet's default marker icon paths under Vite bundling
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({ iconRetinaUrl: markerIcon2x, iconUrl: markerIcon, shadowUrl: markerShadow })

const props = defineProps({
  lat: { type: Number, default: null },
  lng: { type: Number, default: null },
  readonly: { type: Boolean, default: false },
})
const emit = defineEmits(['located'])

const mapEl = ref(null)
const status = ref('')
const locating = ref(false)
let map = null
let marker = null

const DEFAULT_CENTER = [20.5937, 78.9629]  // India
const DEFAULT_ZOOM = 5

let resizeObserver = null

onMounted(() => {
  const hasCoords = props.lat != null && props.lng != null
  map = L.map(mapEl.value, { zoomControl: !props.readonly, scrollWheelZoom: false })
    .setView(hasCoords ? [props.lat, props.lng] : DEFAULT_CENTER, hasCoords ? 16 : DEFAULT_ZOOM)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors', maxZoom: 19,
  }).addTo(map)

  if (hasCoords) setMarker(props.lat, props.lng, false)
  if (!props.readonly) map.on('click', (e) => setMarker(e.latlng.lat, e.latlng.lng))

  // Keep the map's internal pixel grid in sync with its actual container size —
  // a one-shot invalidateSize() isn't enough if the layout settles later
  // (web fonts, surrounding content shifting), which otherwise leaves the
  // tiles misaligned and makes the map appear to jump/drift on interaction.
  resizeObserver = new ResizeObserver(() => map && map.invalidateSize())
  resizeObserver.observe(mapEl.value)
})

onBeforeUnmount(() => {
  if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
  if (map) { map.remove(); map = null }
})

function setMarker(lat, lng, geocode = true) {
  if (!marker) {
    marker = L.marker([lat, lng], { draggable: !props.readonly }).addTo(map)
    if (!props.readonly) marker.on('dragend', () => {
      const p = marker.getLatLng(); commit(p.lat, p.lng)
    })
  } else {
    marker.setLatLng([lat, lng])
  }
  if (geocode) commit(lat, lng)
}

async function commit(lat, lng) {
  const rlat = Math.round(lat * 1e6) / 1e6
  const rlng = Math.round(lng * 1e6) / 1e6
  status.value = `Selected: ${rlat}, ${rlng}`
  let address = ''
  try {
    const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${rlat}&lon=${rlng}`)
    address = (await res.json()).display_name || ''
  } catch { /* offline / rate-limited — coords still usable */ }
  emit('located', { lat: rlat, lng: rlng, address })
}

function useMyLocation() {
  if (!navigator.geolocation) { status.value = 'Geolocation not supported by this browser.'; return }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const { latitude, longitude } = pos.coords
      map.setView([latitude, longitude], 17)
      setMarker(latitude, longitude)
      locating.value = false
    },
    () => { status.value = 'Could not get your location (permission denied or unavailable).'; locating.value = false },
    { enableHighAccuracy: true, timeout: 10000 },
  )
}
</script>

<style scoped>
.loc-toolbar { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.loc-hint { font-size: 0.78rem; color: var(--text-muted); }
.loc-map { height: 260px; width: 100%; border: 1px solid var(--border); border-radius: var(--radius-sm); }
.loc-map.readonly { height: 200px; }
.loc-status { font-size: 0.78rem; color: var(--text-muted); margin-top: 0.4rem; }
</style>
