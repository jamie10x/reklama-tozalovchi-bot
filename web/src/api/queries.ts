import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export interface Event {
  id: string;
  event_number: number;
  chat_id: number;
  message_id: number | null;
  sender_id: number | null;
  event_type: string;
  severity: string;
  score: number;
  confidence: number | null;
  title: string | null;
  message_excerpt: string | null;
  detection_reasons: Record<string, unknown> | null;
  detected_indicators: Record<string, unknown> | null;
  ad_score: number | null;
  security_score: number | null;
  ai_score: number | null;
  ai_analysis: Record<string, unknown> | null;
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

export function useUpdateEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiFetch<Event>(`/api/v1/events/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: (event) => {
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["event", event.id] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
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

export interface Group {
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

export function useGroup(chatId?: number) {
  return useQuery<Group>({
    queryKey: ["group", chatId],
    queryFn: () => apiFetch(`/api/v1/groups/${chatId}`),
    enabled: !!chatId,
  });
}

export interface CaptureSettings {
  chat_id: number;
  enabled: boolean;
  capture_mode: "metadata_only" | "flagged_only" | "full_text";
  metadata_retention_days: number;
  flagged_retention_days: number;
  updated_by_officer_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface ObservedMessage {
  id: string;
  chat_id: number;
  message_id: number;
  sender_id: number | null;
  sender_username: string | null;
  sender_first_name: string | null;
  sender_last_name: string | null;
  sender_is_bot: boolean;
  sender_chat_id: number | null;
  message_type: string;
  text: string | null;
  text_stored: boolean;
  has_text: boolean;
  is_edited: boolean;
  is_forwarded: boolean;
  forward_from_chat_id: number | null;
  reply_to_message_id: number | null;
  detection_status: string;
  risk_score: number;
  ad_score: number | null;
  security_score: number | null;
  ai_score: number | null;
  detection_result: Record<string, unknown> | null;
  event_id: string | null;
  message_date: string | null;
  created_at: string;
  updated_at: string;
}

interface ObservedMessageListResponse {
  items: ObservedMessage[];
  total: number;
}

export function useActivityMessages(params: {
  limit?: number;
  chat_id?: number;
  sender_id?: number;
  flagged_only?: boolean;
} = {}) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.chat_id) search.set("chat_id", String(params.chat_id));
  if (params.sender_id) search.set("sender_id", String(params.sender_id));
  if (params.flagged_only) search.set("flagged_only", "true");
  const qs = search.toString();

  return useQuery<ObservedMessageListResponse>({
    queryKey: ["activity", params],
    queryFn: () => apiFetch(`/api/v1/activity/messages${qs ? `?${qs}` : ""}`),
    refetchInterval: params.flagged_only ? 5_000 : false,
  });
}

export function useLiveActivity(chatId?: number) {
  const search = new URLSearchParams();
  search.set("limit", "50");
  if (chatId) search.set("chat_id", String(chatId));
  return useQuery<ObservedMessageListResponse>({
    queryKey: ["activity-live", chatId],
    queryFn: () => apiFetch(`/api/v1/activity/live?${search.toString()}`),
    refetchInterval: 5_000,
  });
}

export function useCaptureSettings(chatId?: number) {
  return useQuery<CaptureSettings>({
    queryKey: ["capture-settings", chatId],
    queryFn: () => apiFetch(`/api/v1/activity/groups/${chatId}/settings`),
    enabled: !!chatId,
  });
}

export function useUpdateCaptureSettings(chatId?: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: Partial<Pick<CaptureSettings, "enabled" | "capture_mode">>) =>
      apiFetch<CaptureSettings>(`/api/v1/activity/groups/${chatId}/settings`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["capture-settings", chatId] });
      queryClient.invalidateQueries({ queryKey: ["groups"] });
    },
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

export function useUserIntel(telegramId?: number) {
  return useQuery({
    queryKey: ["user-intel", telegramId],
    queryFn: () => apiFetch(`/api/v1/users/${telegramId}/intel`),
    enabled: !!telegramId,
  });
}

export interface CaseItem {
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

export interface CaseCreateRequest {
  title: string;
  severity?: string;
  description?: string | null;
  assigned_officer_id?: number | null;
}

export function useCreateCase() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: CaseCreateRequest) =>
      apiFetch<CaseItem>("/api/v1/cases", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cases"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
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

export type EnforcementActionType =
  | "delete_message"
  | "trust_sender"
  | "block_indicator"
  | "allow_indicator"
  | "refresh_member"
  | "refresh_group_permissions"
  | "restrict_member"
  | "mute_member"
  | "ban_member"
  | "get_chat_info"
  | "get_chat_administrators"
  | "get_chat_member_count"
  | "get_user_profile_photos"
  | "save_observed_state"
  | "send_recent_messages";

export interface EnforcementAction {
  id: string;
  action_type: EnforcementActionType;
  target_chat_id: number | null;
  target_message_id: number | null;
  target_user_id: number | null;
  target_indicator_id: string | null;
  status: string;
  result: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
}

export interface EnforcementActionRequest {
  action_type: EnforcementActionType;
  target_chat_id?: number | null;
  target_message_id?: number | null;
  target_user_id?: number | null;
  target_indicator_id?: string | null;
}

export function useCreateEnforcementAction() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: EnforcementActionRequest) =>
      apiFetch<EnforcementAction>("/api/v1/enforcement/actions", {
        method: "POST",
        body: JSON.stringify(body),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["enforcement"] });
      queryClient.invalidateQueries({ queryKey: ["events"] });
      queryClient.invalidateQueries({ queryKey: ["groups"] });
      queryClient.invalidateQueries({ queryKey: ["activity"] });
      queryClient.invalidateQueries({ queryKey: ["activity-live"] });
    },
  });
}

export function useEnforcement(params: {
  limit?: number;
  status?: string;
  action_type?: EnforcementActionType;
  chat_id?: number;
} = {}) {
  const search = new URLSearchParams();
  if (params.limit) search.set("limit", String(params.limit));
  if (params.status) search.set("status", params.status);
  if (params.action_type) search.set("action_type", params.action_type);
  if (params.chat_id) search.set("chat_id", String(params.chat_id));
  const qs = search.toString();

  return useQuery<{ items: EnforcementAction[]; total: number }>({
    queryKey: ["enforcement", params],
    queryFn: () => apiFetch(`/api/v1/enforcement${qs ? `?${qs}` : ""}`),
  });
}
