import * as React from "react"
import type { ToastActionElement, ToastProps } from "@/components/ui/toast"

const TOAST_LIMIT = 5
const TOAST_REMOVE_DELAY = 5000

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = typeof actionTypes

type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: string
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: string
    }

interface State {
  toasts: ToasterToast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

// Cleanup function to remove toast after delay
function cleanupToast(toastId: string) {
  if (toastTimeouts.has(toastId)) {
    clearTimeout(toastTimeouts.get(toastId))
    toastTimeouts.delete(toastId)
  }
}

const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case actionTypes.ADD_TOAST:
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case actionTypes.UPDATE_TOAST:
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case actionTypes.DISMISS_TOAST: {
      const { toastId } = action

      // Toast is no longer controlled, remove it from state
      if (toastId === undefined) {
        return {
          ...state,
          toasts: state.toasts.map((t) => ({
            ...t,
            open: false,
          })),
        }
      }

      // Remove toast from state
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case actionTypes.REMOVE_TOAST:
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

const listeners: Array<(state: State) => void> = []

let memoryState: State = { toasts: [] }

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

type Toast = Omit<ToasterToast, "id">

function toast({ ...props }: Toast) {
  const id = genId()

  const update = (props: Partial<ToasterToast>) =>
    dispatch({
      type: actionTypes.UPDATE_TOAST,
      toast: { ...props, id },
    })

  const dismiss = () => {
    dispatch({ type: actionTypes.DISMISS_TOAST, toastId: id })
    
    // Add auto-removal after dismiss
    if (toastTimeouts.has(id)) {
      clearTimeout(toastTimeouts.get(id))
    }
    
    const timeout = setTimeout(() => {
      dispatch({ type: actionTypes.REMOVE_TOAST, toastId: id })
      toastTimeouts.delete(id)
    }, TOAST_REMOVE_DELAY)
    
    toastTimeouts.set(id, timeout)
  }

  dispatch({
    type: actionTypes.ADD_TOAST,
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
        // Make sure we call the user's onOpenChange if they provided it
        props.onOpenChange?.(open)
      },
    },
  })

  return {
    id,
    dismiss,
    update,
  }
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
      
      // Clean up any remaining timeouts when component unmounts
      state.toasts.forEach(toast => {
        if (toastTimeouts.has(toast.id)) {
          clearTimeout(toastTimeouts.get(toast.id))
          toastTimeouts.delete(toast.id)
        }
      })
    }
  }, [state])

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => {
      dispatch({ type: actionTypes.DISMISS_TOAST, toastId })
      
      // Add auto-removal for all toasts or specific toast
      if (toastId === undefined) {
        // Remove all toasts after delay
        state.toasts.forEach(toast => {
          if (toastTimeouts.has(toast.id)) {
            clearTimeout(toastTimeouts.get(toast.id))
          }
          
          const timeout = setTimeout(() => {
            dispatch({ type: actionTypes.REMOVE_TOAST, toastId: toast.id })
            toastTimeouts.delete(toast.id)
          }, TOAST_REMOVE_DELAY)
          
          toastTimeouts.set(toast.id, timeout)
        })
      } else if (toastId) {
        // Remove specific toast after delay
        if (toastTimeouts.has(toastId)) {
          clearTimeout(toastTimeouts.get(toastId))
        }
        
        const timeout = setTimeout(() => {
          dispatch({ type: actionTypes.REMOVE_TOAST, toastId })
          toastTimeouts.delete(toastId)
        }, TOAST_REMOVE_DELAY)
        
        toastTimeouts.set(toastId, timeout)
      }
    },
  }
}

export { useToast, toast }