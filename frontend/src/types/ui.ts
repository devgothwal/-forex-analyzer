// UI-specific types and interfaces

export interface ThemeConfig {
  mode: 'light' | 'dark';
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: string;
}

export interface LoadingState {
  isLoading: boolean;
  message?: string;
  progress?: number;
}

export interface ErrorState {
  hasError: boolean;
  message?: string;
  details?: string;
  code?: string | number;
}

export interface NotificationState {
  message: string;
  type: 'success' | 'error' | 'warning' | 'info';
  duration?: number;
  id: string;
}

export interface ModalState {
  isOpen: boolean;
  title?: string;
  content?: React.ReactNode;
  onClose?: () => void;
  size?: 'small' | 'medium' | 'large' | 'fullscreen';
}

export interface TableColumn<T = any> {
  id: string;
  label: string;
  accessor: keyof T | ((item: T) => any);
  sortable?: boolean;
  filterable?: boolean;
  width?: number;
  align?: 'left' | 'center' | 'right';
  format?: (value: any) => string;
  render?: (value: any, item: T) => React.ReactNode;
}

export interface FilterConfig {
  field: string;
  operator: 'equals' | 'contains' | 'greater' | 'less' | 'between' | 'in';
  value: any;
  label?: string;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

export interface PaginationConfig {
  page: number;
  pageSize: number;
  total: number;
}

// Component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
  'data-testid'?: string;
}

export interface ResponsiveProps {
  xs?: boolean | number;
  sm?: boolean | number;
  md?: boolean | number;
  lg?: boolean | number;
  xl?: boolean | number;
}

// Layout types
export interface LayoutConfig {
  sidebar: {
    open: boolean;
    width: number;
    variant: 'permanent' | 'temporary' | 'persistent';
  };
  header: {
    height: number;
    variant: 'fixed' | 'static' | 'sticky';
  };
  footer: {
    height: number;
    visible: boolean;
  };
}

// Navigation types
export interface NavigationItem {
  id: string;
  label: string;
  path?: string;
  icon?: React.ComponentType;
  children?: NavigationItem[];
  permissions?: string[];
  badge?: string | number;
  disabled?: boolean;
}

export interface BreadcrumbItem {
  label: string;
  path?: string;
  icon?: React.ComponentType;
}

// Form types
export interface FormFieldConfig {
  name: string;
  label: string;
  type: 'text' | 'number' | 'email' | 'password' | 'select' | 'checkbox' | 'radio' | 'textarea' | 'file' | 'date';
  placeholder?: string;
  required?: boolean;
  validation?: {
    min?: number;
    max?: number;
    pattern?: RegExp;
    custom?: (value: any) => string | null;
  };
  options?: Array<{ value: any; label: string }>;
  multiple?: boolean;
  disabled?: boolean;
  description?: string;
}

export interface FormState {
  values: Record<string, any>;
  errors: Record<string, string>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}

// Chart types
export interface ChartTheme {
  background: string;
  grid: string;
  text: string;
  primary: string;
  secondary: string;
  accent: string;
  success: string;
  warning: string;
  error: string;
}

export interface ChartTooltipConfig {
  enabled: boolean;
  format?: (point: any) => string;
  backgroundColor?: string;
  borderColor?: string;
  textColor?: string;
}

export interface ChartLegendConfig {
  enabled: boolean;
  position: 'top' | 'bottom' | 'left' | 'right';
  align: 'start' | 'center' | 'end';
}

export interface ChartAxisConfig {
  title?: string;
  min?: number;
  max?: number;
  type?: 'linear' | 'log' | 'category' | 'time';
  format?: string;
  grid?: boolean;
}

// Mobile-specific types
export interface TouchGesture {
  type: 'tap' | 'swipe' | 'pinch' | 'pan';
  direction?: 'up' | 'down' | 'left' | 'right';
  distance?: number;
  scale?: number;
}

export interface ViewportConfig {
  width: number;
  height: number;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  orientation: 'portrait' | 'landscape';
}

// Plugin UI types
export interface PluginComponent {
  component: React.ComponentType<any>;
  props?: Record<string, any>;
  slots?: Record<string, React.ReactNode>;
}

export interface PluginRoute {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  permissions?: string[];
}

export interface PluginMenuItem {
  label: string;
  path?: string;
  icon?: React.ComponentType;
  children?: PluginMenuItem[];
  permissions?: string[];
}