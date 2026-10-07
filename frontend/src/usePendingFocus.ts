import { useEffect, useRef } from 'react'

// Disabling a focused control during a request sends focus to the document body.
// Restore it after React enables the controls, unless the user has moved elsewhere.
export function usePendingFocus(pending: boolean) {
  const origin = useRef<HTMLElement | null>(null)
  useEffect(() => {
    if (pending) return
    if (document.activeElement === document.body && origin.current?.isConnected)
      origin.current.focus()
    origin.current = null
  }, [pending])
  return () => {
    origin.current = document.activeElement instanceof HTMLElement ? document.activeElement : null
  }
}
