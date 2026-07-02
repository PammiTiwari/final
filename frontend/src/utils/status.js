const LABELS = {
  on_hold_weather: 'on hold - weather restrictions',
}

// Badge text shown next to a complaint status. CSS applies text-transform:
// capitalize, so each word (but not "-") gets capitalized automatically.
export function fmtStatus(status) {
  if (!status) return ''
  return LABELS[status] || status.replace(/_/g, ' ')
}
