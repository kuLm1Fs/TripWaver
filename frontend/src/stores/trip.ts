import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ItineraryResponse } from '@/types/itinerary'

export const useTripStore = defineStore('trip', () => {
  const currentTrip = ref<ItineraryResponse | null>(null)

  function setTrip(trip: ItineraryResponse) {
    currentTrip.value = trip
  }

  function clearTrip() {
    currentTrip.value = null
  }

  return { currentTrip, setTrip, clearTrip }
})
