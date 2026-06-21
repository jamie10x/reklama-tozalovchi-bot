import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "../api/client";

interface MeResponse {
  id: string;
  telegram_id: number;
  role: string;
  display_name: string | null;
  is_active: boolean;
}

export function useMe() {
  return useQuery<MeResponse>({
    queryKey: ["me"],
    queryFn: () => apiFetch("/api/v1/auth/me"),
    retry: false,
  });
}
