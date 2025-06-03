# Missing Dependencies Analysis

## Critical Missing Dependencies:

### Radix UI Components (Most TypeScript errors)
- @radix-ui/react-accordion
- @radix-ui/react-alert-dialog
- @radix-ui/react-aspect-ratio
- @radix-ui/react-breadcrumb
- @radix-ui/react-calendar
- @radix-ui/react-card
- @radix-ui/react-collapsible
- @radix-ui/react-command
- @radix-ui/react-context-menu
- @radix-ui/react-form
- @radix-ui/react-hover-card
- @radix-ui/react-input-otp
- @radix-ui/react-menubar
- @radix-ui/react-navigation-menu
- @radix-ui/react-radio-group
- @radix-ui/react-resizable
- @radix-ui/react-sheet
- @radix-ui/react-sidebar
- @radix-ui/react-table
- @radix-ui/react-textarea
- @radix-ui/react-toggle
- @radix-ui/react-toggle-group

### Other Dependencies
- @vercel/analytics
- react-resizable-panels
- zod
- sonner (toast notifications)
- katex (math rendering)

### Custom/Local Modules Missing
- shadcn/registry
- @/lib/highlight-code
- @/lib/registry
- @/components/block-viewer

## Lucide React Icon Issues
The following icons don't exist in lucide-react and need replacements:
- Smile -> SmilePlus or Smile
- BrainCircuit -> Brain or CircuitBoard
- ArrowRightCircle -> ArrowRight + Circle combination
- CornerDownRight -> ArrowDownRight
- MoreVertical -> MoreVertical (should exist)
- PlusCircle -> Plus + Circle combination
- ArrowRight -> ArrowRight (should exist)

## Action Plan
1. Install missing Radix UI components
2. Install other missing dependencies  
3. Fix lucide-react icon imports
4. Remove/fix custom shadcn components that don't belong in this project
5. Run TypeScript check to verify fixes