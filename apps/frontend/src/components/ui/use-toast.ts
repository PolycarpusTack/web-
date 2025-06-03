/**
 * Minimal, self-contained toast hook.
 * � Works in any React app (no extra deps).
 * � Prints to the DevTools console **and** shows a browser `alert()` so you
 *   always see feedback while you�re wiring things up.
 *
 * Replace this file with the real shadcn �toast� + �sonner� code whenever
 * you�re ready for production UI polish.
 */

export type ToastVariant = "default" | "destructive"

export interface ToastOptions {
  title: string
  description?: string
  variant?: ToastVariant
}

export function useToast() {
  const toast = ({ title, description, variant = "default" }: ToastOptions) => {
    const msg = description ? `${title} � ${description}` : title

    if (variant === "destructive") {
      console.error(`[toast] ${msg}`)
      alert(`? ${msg}`)
    } else {
      console.log(`[toast] ${msg}`)
      alert(`? ${msg}`)
    }
  }

  return { toast }
}

// Export toast function directly for components that import it
export const toast = ({ title, description, variant = "default" }: ToastOptions) => {
  const msg = description ? `${title} � ${description}` : title

  if (variant === "destructive") {
    console.error(`[toast] ${msg}`)
    alert(`? ${msg}`)
  } else {
    console.log(`[toast] ${msg}`)
    alert(`? ${msg}`)
  }
}
