import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "./client";

interface DashboardStats {
  open_events: number;
  critical_events: number;
  pending_observations: number;
  total_indicators: number;
  active_groups: number;
  active_officers: number;
}

export function useDashboard() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch("/api/v1/dashboard"),
  });
}

interface EventListParams {
  limit?: number;
  offset?: number;
  status?: string;
  severity?: string;
  event_type?: string;
  chat_id?: number;
}

interface Event {
  id: string;
  event_number: number;
  chat_id: number;
  message_id: number | null;
  sender_id: number | null;
  event_type: string;
  severity: string;
  score: number;
  title: string | null;
  status: string;
  assigned_officer_id: number | null;
  created_at: string;
  updated_at: string;
}

interface EventListResponse {
  items: Event[];
  total: number;
}

export function useEvents(params: EventListParams = {}) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  if (params.status) search.set("status", params.status);
  if (params.severity) search.set("severity", params.severity);
  if (params.event_type) search.set("event_type", params.event_type);
  if (params.chat_id) search.set("chat_id", String(params.chat_id));
  const qs = search.toString();

  return useQuery<EventListResponse>({
    queryKey: ["events", params],
    queryFn: () => apiFetch(`/api/v1/events${qs ? `?${qs}` : ""}`),
  });
}

export function useEvent(id: string) {
  return useQuery<Event>({
    queryKey: ["event", id],
    queryFn: () => apiFetch(`/api/v1/events/${id}`),
    enabled: !!id,
  });
}

interface Indicator {
  id: string;
  indicator_type: string;
  indicator_value: string;
  status: string;
  first_seen_at: string | null;
  last_seen_at: string | null;
  seen_count: number;
  event_count: number;
  notes: string | null;
  created_at: string;
}

interface IndicatorListResponse {
  items: Indicator[];
  total: number;
}

export function useIndicators(params: {
  limit?: number;
  offset?: number;
  indicator_type?: string;
  status?: string;
}) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.offset) search.set("offset", String(params.offset));
  if (params.indicator_type) search.set("indicator_type", params.indicator_type);
  if (params.status) search.set("status", params.status);
  const qs = search.toString();

  return useQuery<IndicatorListResponse>({
    queryKey: ["indicators", params],
    queryFn: () => apiFetch(`/api/v1/indicators${qs ? `?${qs}` : ""}`),
  });
}

interface Group {
  telegram_chat_id: number;
  title: string | null;
  username: string | null;
  enabled: boolean;
  mode: string;
  bot_can_delete_messages: boolean;
  created_at: string;
}

interface GroupListResponse {
  items: Group[];
  total: number;
}

export function useGroups() {
  return useQuery<GroupListResponse>({
    queryKey: ["groups"],
    queryFn: () => apiFetch("/api/v1/groups"),
  });
}

interface Officer {
  id: string;
  telegram_id: number;
  role: string;
  display_name: string | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

interface OfficerListResponse {
  items: Officer[];
  total: number;
}

export function useOfficers() {
  return useQuery<OfficerListResponse>({
    queryKey: ["officers"],
    queryFn: () => apiFetch("/api/v1/officers"),
  });
}

interface AuditLogEntry {
  id: string;
  officer_id: string | null;
  action_type: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown> | null;
  created_at: string;
}

interface AuditLogResponse {
  items: AuditLogEntry[];
  total: number;
}

export function useAuditLogs(params: { limit?: number; action_type?: string }) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.action_type) search.set("action_type", params.action_type);
  const qs = search.toString();

  return useQuery<AuditLogResponse>({
    queryKey: ["audit", params],
    queryFn: () => apiFetch(`/api/v1/audit${qs ? `?${qs}` : ""}`),
  });
}

interface User {
  telegram_id: number;
  current_username: string | null;
  current_first_name: string | null;
  current_last_name: string | null;
  is_bot: boolean;
  language_code: string | null;
  risk_score: number;
  first_seen_at: string | null;
  last_seen_at: string | null;
}

interface UserListResponse {
  items: User[];
  total: number;
}

export function useUsers(query: string) {
  const search = new URLSearchParams();
  if (query) search.set("query", query);
  const qs = search.toString();

  return useQuery<UserListResponse>({
    queryKey: ["users", query],
    queryFn: () => apiFetch(`/api/v1/users${qs ? `?${qs}` : ""}`),
    enabled: query.length >= 0,
  });
}

interface CaseItem {
  id: string;
  case_number: number;
  title: string;
  severity: string;
  status: string;
  assigned_officer_id: number | null;
  description: string | null;
  resolution: string | null;
  created_at: string;
  updated_at: string;
}

interface CaseListResponse {
  items: CaseItem[];
  total: number;
}

export function useCases(params: { limit?: number; status?: string; severity?: string }) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.status) search.set("status", params.status);
  if (params.severity) search.set("severity", params.severity);
  const qs = search.toString();

  return useQuery<CaseListResponse>({
    queryKey: ["cases", params],
    queryFn: () => apiFetch(`/api/v1/cases${qs ? `?${qs}` : ""}`),
  });
}

interface HealthResponse {
  status: string;
  database: string;
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: () => apiFetch("/api/v1/health"),
    refetchInterval: 30_000,
  });
}
