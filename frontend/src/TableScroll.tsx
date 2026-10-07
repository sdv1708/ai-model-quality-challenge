import type { ReactNode } from 'react'

export default function TableScroll({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="table-scroll" role="region" aria-label={`${label} scroll area`} tabIndex={0}>
      {children}
    </div>
  )
}
