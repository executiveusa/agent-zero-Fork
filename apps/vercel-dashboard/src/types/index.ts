// Agent Zero API Response Types (grounded to python/api/*.py)

export interface PollResponse {
  deselect_chat: boolean;
  context: string;
  contexts: AgentContext[];
  tasks: SchedulerTask[];
  logs: LogItem[];
  log_guid: string;
  log_version: number;
  log_progress: string;
  log_progress_active: boolean;
  paused: boolean;
  notifications: Notification[];
  notifications_guid: string;
  notifications_version: number;
}

export interface AgentContext {
  id: string;
  name?: string;
  created_at: string;
  paused: boolean;
  project_name?: string;
  project_color?: string;
  type?: string;
}

export interface SchedulerTask {
  uuid: string;
  task_name: string;
  state: 'idle' | 'running' | 'disabled' | 'error';
  type: 'adhoc' | 'scheduled' | 'planned';
  system_prompt: string;
  prompt: string;
  last_run?: string;
  last_result?: string;
  attachments: string[];
  context_id?: string;
  project_name?: string;
  project_color?: string;
  schedule?: CronSchedule;
  plan?: PlanSchedule;
  token?: string;
  created_at: string;
}

export interface CronSchedule {
  minute: string;
  hour: string;
  day: string;
  month: string;
  weekday: string;
  timezone: string;
}

export interface PlanSchedule {
  todo: string[];
  in_progress: string | null;
  done: string[];
}

export interface LogItem {
  no: number;
  id: string | null;
  type: LogType;
  heading: string;
  content: string;
  temp: boolean;
  kvps: Record<string, any>;
}

export type LogType =
  | 'agent'
  | 'browser'
  | 'code_exe'
  | 'error'
  | 'hint'
  | 'info'
  | 'progress'
  | 'response'
  | 'tool'
  | 'input'
  | 'user'
  | 'util'
  | 'warning';

export interface Notification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  created_at: string;
  read: boolean;
}

export interface HealthResponse {
  status: string;
  [key: string]: any;
}

export interface Project {
  name: string;
  color: string;
  description?: string;
}

export interface FileInfo {
  name: string;
  path: string;
  size: number;
  modified: string;
  type: string;
  is_directory: boolean;
}

export interface McpServer {
  name: string;
  status: 'running' | 'stopped' | 'error';
  config: Record<string, any>;
  logs: string[];
}

export interface BackupInfo {
  filename: string;
  created_at: string;
  size: number;
  components: string[];
}

export interface SettingsData {
  [key: string]: any;
}

// Dashboard State Types

export type OperationalState =
  | 'idle'
  | 'planning'
  | 'running'
  | 'waiting'
  | 'paused'
  | 'error'
  | 'offline';

export interface DashboardState {
  connected: boolean;
  activeContext: string | null;
  contexts: AgentContext[];
  tasks: SchedulerTask[];
  logs: LogItem[];
  notifications: Notification[];
  logProgress: string;
  logProgressActive: boolean;
  paused: boolean;
  autonomyLevel: number;
  lastUpdate: Date | null;
}

// API Request/Response Types

export interface ApiError {
  error: string;
  details?: string;
  status: number;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: ApiError;
}

// Authentication Types

export interface DashboardUser {
  id: string;
  email: string;
  name?: string;
}

export interface AuthSession {
  user: DashboardUser;
  expires: string;
}
