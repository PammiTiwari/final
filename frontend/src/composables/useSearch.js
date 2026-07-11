import { ref, computed } from 'vue'

export function useSearch(items, searchFields = ['title', 'description'], debounceMs = 300) {
  const searchQuery = ref('')
  const filters = ref({})
  let debounceTimer = null

  const debouncedSearch = computed(() => {
    return searchQuery.value
  })

  const filtered = computed(() => {
    let result = items.value || []

    // Apply search filter
    if (debouncedSearch.value) {
      const q = debouncedSearch.value.toLowerCase()
      result = result.filter(item =>
        searchFields.some(field => {
          const value = getNestedValue(item, field)
          return value && value.toString().toLowerCase().includes(q)
        })
      )
    }

    // Apply custom filters
    Object.entries(filters.value).forEach(([key, value]) => {
      if (value && value !== '' && value !== null) {
        result = result.filter(item => {
          const itemValue = getNestedValue(item, key)
          if (Array.isArray(value)) {
            return value.includes(itemValue)
          }
          if (typeof value === 'object' && value.min !== undefined) {
            return itemValue >= value.min && itemValue <= value.max
          }
          return itemValue === value || itemValue?.toString().toLowerCase() === value.toString().toLowerCase()
        })
      }
    })

    return result
  })

  const setSearch = (query) => {
    searchQuery.value = query
  }

  const setFilter = (key, value) => {
    filters.value[key] = value
  }

  const setFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
  }

  const clearFilters = () => {
    filters.value = {}
  }

  const clearSearch = () => {
    searchQuery.value = ''
  }

  const clearAll = () => {
    clearSearch()
    clearFilters()
  }

  const getNestedValue = (obj, path) => {
    return path.split('.').reduce((current, prop) => current?.[prop], obj)
  }

  return {
    searchQuery,
    filters,
    filtered,
    setSearch,
    setFilter,
    setFilters,
    clearFilters,
    clearSearch,
    clearAll,
    hasActiveFilters: computed(() => Object.values(filters.value).some(v => v && v !== '' && v !== null)),
    resultCount: computed(() => filtered.value.length)
  }
}
