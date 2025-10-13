// API Response types
export interface ApiResponse<T> {
  data?: T;
  message?: string;
  error?: string;
}

// Authentication types
export interface User {
  id: number;
  username: string;
  email?: string;
  role: 'admin' | 'user' | 'super_admin';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Document types
export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  user_id: number;
  status: 'not processed' | 'extracted' | 'chunked' | 'processed';
  created_at: string;
  processed_at?: string;
}

// Chat types
export interface ChatMessage {
  id?: number;
  message: string;
  document_ids?: number[];
  response?: string;
  context_docs?: number[];
  model_used?: string;
  created_at?: string;
  isUser: boolean;
}

// Form types
export interface LoginForm {
  username: string;
  password: string;
}

export interface RegisterForm {
  username: string;
  email?: string;
  password: string;
  confirmPassword: string;
}

// UI State types
export interface LoadingState {
  isLoading: boolean;
  message?: string;
}

export interface NotificationState {
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  description?: string;
}

// API Error types
export interface ApiError {
  detail: string;
  status_code?: number;
}

// Component Props types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}