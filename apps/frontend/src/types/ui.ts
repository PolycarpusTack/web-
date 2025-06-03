// UI Component Types for Web+ Application

import { ReactNode, ComponentPropsWithoutRef } from 'react';

// Base component props
export interface BaseComponentProps {
  className?: string;
  children?: ReactNode;
  id?: string;
  'data-testid'?: string;
}

// Button variants and sizes
export type ButtonVariant = 
  | 'default' 
  | 'destructive' 
  | 'outline' 
  | 'secondary' 
  | 'ghost' 
  | 'link';

export type ButtonSize = 'default' | 'sm' | 'lg' | 'icon';

export interface ButtonProps extends ComponentPropsWithoutRef<'button'> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  asChild?: boolean;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

// Input component types
export type InputVariant = 'default' | 'destructive';
export type InputSize = 'default' | 'sm' | 'lg';

export interface InputProps extends ComponentPropsWithoutRef<'input'> {
  variant?: InputVariant;
  inputSize?: InputSize;
  error?: string;
  helperText?: string;
  label?: string;
  leftAddon?: ReactNode;
  rightAddon?: ReactNode;
}

// Dialog/Modal types
export interface DialogProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  children: ReactNode;
}

export interface DialogContentProps extends BaseComponentProps {
  children: ReactNode;
  onEscapeKeyDown?: (event: KeyboardEvent) => void;
  onPointerDownOutside?: (event: PointerEvent) => void;
}

// Toast types
export type ToastVariant = 'default' | 'destructive' | 'success' | 'warning';

export interface ToastProps {
  id?: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  action?: ReactNode;
  duration?: number;
  onDismiss?: () => void;
}

export interface ToastContextType {
  toast: (props: Omit<ToastProps, 'id'>) => void;
  dismiss: (id: string) => void;
  toasts: ToastProps[];
}

// Card component types
export interface CardProps extends BaseComponentProps {
  children: ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  shadow?: 'none' | 'sm' | 'md' | 'lg';
  border?: boolean;
}

// Badge component types
export type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';

export interface BadgeProps extends BaseComponentProps {
  variant?: BadgeVariant;
  children: ReactNode;
}

// Avatar component types
export interface AvatarProps extends BaseComponentProps {
  src?: string;
  alt?: string;
  fallback?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

// Progress component types
export interface ProgressProps extends BaseComponentProps {
  value?: number;
  max?: number;
  variant?: 'default' | 'success' | 'warning' | 'destructive';
  size?: 'sm' | 'md' | 'lg';
}

// Skeleton component types
export interface SkeletonProps extends BaseComponentProps {
  width?: string | number;
  height?: string | number;
  circle?: boolean;
  count?: number;
}

// Loading spinner types
export interface SpinnerProps extends BaseComponentProps {
  size?: 'sm' | 'md' | 'lg';
  color?: 'primary' | 'secondary' | 'white';
}

// Dropdown/Select types
export interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
  icon?: ReactNode;
}

export interface SelectProps {
  options: SelectOption[];
  value?: string;
  onValueChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  className?: string;
}

// Table types
export interface TableColumn<T = any> {
  key: string;
  header: string;
  accessor?: string | ((item: T) => any);
  render?: (value: any, item: T, index: number) => ReactNode;
  sortable?: boolean;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

export interface TableProps<T = any> {
  data: T[];
  columns: TableColumn<T>[];
  loading?: boolean;
  error?: string;
  onRowClick?: (item: T, index: number) => void;
  onSort?: (key: string, direction: 'asc' | 'desc') => void;
  sortKey?: string;
  sortDirection?: 'asc' | 'desc';
  className?: string;
}

// Pagination types
export interface PaginationProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
  showFirstLast?: boolean;
  showPrevNext?: boolean;
  maxVisiblePages?: number;
  className?: string;
}

// Search/Filter types
export interface SearchProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  debounceMs?: number;
  onSearch?: (value: string) => void;
  className?: string;
}

export interface FilterOption {
  key: string;
  label: string;
  value: string;
  count?: number;
}

export interface FilterProps {
  title: string;
  options: FilterOption[];
  selectedValues: string[];
  onSelectionChange: (values: string[]) => void;
  multiSelect?: boolean;
  searchable?: boolean;
  className?: string;
}

// Layout types
export interface SidebarProps extends BaseComponentProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  side?: 'left' | 'right';
  overlay?: boolean;
  children: ReactNode;
}

export interface HeaderProps extends BaseComponentProps {
  title?: string;
  subtitle?: string;
  actions?: ReactNode;
  breadcrumbs?: BreadcrumbItem[];
  children?: ReactNode;
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
  current?: boolean;
}

// Form types
export interface FormFieldProps {
  name: string;
  label?: string;
  required?: boolean;
  error?: string;
  helperText?: string;
  children: ReactNode;
  className?: string;
}

export interface FormProps extends ComponentPropsWithoutRef<'form'> {
  onSubmit: (data: any) => void | Promise<void>;
  loading?: boolean;
  error?: string;
  children: ReactNode;
}

// Theme types
export type ThemeMode = 'light' | 'dark' | 'system';

export interface ThemeContextType {
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  isDark: boolean;
  toggleMode: () => void;
}

// Navigation types
export interface NavItem {
  label: string;
  href?: string;
  icon?: ReactNode;
  children?: NavItem[];
  active?: boolean;
  disabled?: boolean;
  badge?: string | number;
}

export interface NavigationProps {
  items: NavItem[];
  orientation?: 'horizontal' | 'vertical';
  variant?: 'default' | 'pills' | 'underline';
  className?: string;
}

// Modal/Sheet types
export interface SheetProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
  side?: 'top' | 'right' | 'bottom' | 'left';
  children: ReactNode;
}

// Tooltip types
export interface TooltipProps {
  content: ReactNode;
  children: ReactNode;
  placement?: 'top' | 'right' | 'bottom' | 'left';
  delay?: number;
  className?: string;
}

// Accordion types
export interface AccordionItem {
  id: string;
  trigger: ReactNode;
  content: ReactNode;
  disabled?: boolean;
}

export interface AccordionProps {
  items: AccordionItem[];
  type?: 'single' | 'multiple';
  defaultValue?: string | string[];
  value?: string | string[];
  onValueChange?: (value: string | string[]) => void;
  collapsible?: boolean;
  className?: string;
}

// Tabs types
export interface TabItem {
  id: string;
  label: string;
  content: ReactNode;
  disabled?: boolean;
  icon?: ReactNode;
}

export interface TabsProps {
  items: TabItem[];
  defaultValue?: string;
  value?: string;
  onValueChange?: (value: string) => void;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

// Command/CommandPalette types
export interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  shortcut?: string[];
  onSelect?: () => void;
  disabled?: boolean;
}

export interface CommandGroup {
  heading?: string;
  items: CommandItem[];
}

export interface CommandProps {
  groups: CommandGroup[];
  placeholder?: string;
  emptyMessage?: string;
  loading?: boolean;
  onSearch?: (search: string) => void;
  className?: string;
}

// Date picker types
export interface DatePickerProps {
  value?: Date;
  onChange?: (date: Date | undefined) => void;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
  className?: string;
}

// Color picker types
export interface ColorPickerProps {
  value?: string;
  onChange?: (color: string) => void;
  presets?: string[];
  disabled?: boolean;
  className?: string;
}

// File upload types
export interface FileUploadProps {
  accept?: string;
  multiple?: boolean;
  maxSize?: number;
  onUpload?: (files: File[]) => void;
  loading?: boolean;
  error?: string;
  className?: string;
}

// Generic component props
export type Size = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type Color = 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info';
export type Placement = 'top' | 'right' | 'bottom' | 'left';
export type Variant = 'solid' | 'outline' | 'ghost' | 'link';

// Responsive types
export type ResponsiveValue<T> = T | {
  xs?: T;
  sm?: T;
  md?: T;
  lg?: T;
  xl?: T;
};

// Animation types
export type AnimationDuration = 'fast' | 'normal' | 'slow';
export type AnimationEasing = 'ease' | 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';

export interface AnimationProps {
  duration?: AnimationDuration;
  easing?: AnimationEasing;
  delay?: number;
}

// Accessibility types
export interface AccessibilityProps {
  'aria-label'?: string;
  'aria-labelledby'?: string;
  'aria-describedby'?: string;
  'aria-expanded'?: boolean;
  'aria-hidden'?: boolean;
  role?: string;
  tabIndex?: number;
}