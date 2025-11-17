"use client"

import * as React from 'react'
import { cn } from '@/lib/utils'

export interface SwitchProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  checked?: boolean
  onCheckedChange?: (checked: boolean) => void
}

export const Switch = React.forwardRef<HTMLButtonElement, SwitchProps>(
  ({ checked = false, onCheckedChange, className, disabled, ...props }, ref) => (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-disabled={disabled}
      onClick={() => !disabled && onCheckedChange?.(!checked)}
      data-state={checked ? 'checked' : 'unchecked'}
      className={cn(
        'relative inline-flex h-6 w-11 items-center rounded-full border border-input bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:opacity-50 data-[state=checked]:bg-primary',
        className,
      )}
      ref={ref}
      disabled={disabled}
      {...props}
    >
      <span
        data-state={checked ? 'checked' : 'unchecked'}
        className={cn(
          'pointer-events-none inline-block size-4 transform rounded-full bg-background shadow transition-transform',
          checked ? 'translate-x-5' : 'translate-x-1',
        )}
      />
    </button>
  ),
)

Switch.displayName = 'Switch'
