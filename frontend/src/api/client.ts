import type {
  ApiResponse,
  DeletedResourceResult,
  HealthResult,
  ParseAndMatchResult,
  PersistedPlaylistItemResult,
  PersistedPlaylistResult,
  PlaylistExportFormat,
  PlaylistExportResult,
  PlaylistStatsResult,
  UserSessionResult,
} from "./types";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: object;
};

async function requestData<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const headers = new Headers();
  const init: RequestInit = {
    method: options.method ?? "GET",
    headers,
  };

  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
    init.body = JSON.stringify(options.body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);
  const payload = (await response.json()) as ApiResponse<T>;

  if (!response.ok || payload.error !== null || payload.data === null) {
    const message = payload.error?.message ?? `Request failed with ${response.status}`;
    throw new Error(message);
  }

  return payload.data;
}

export async function getHealth(): Promise<HealthResult> {
  return requestData<HealthResult>("/health");
}

export async function createSession(
  displayName: string,
): Promise<UserSessionResult> {
  return requestData<UserSessionResult>("/sessions", {
    method: "POST",
    body: { display_name: displayName },
  });
}

export async function getSession(
  sessionId: string,
): Promise<UserSessionResult> {
  return requestData<UserSessionResult>(`/sessions/${sessionId}`);
}

export async function touchSession(
  sessionId: string,
): Promise<UserSessionResult> {
  return requestData<UserSessionResult>(`/sessions/${sessionId}/touch`, {
    method: "POST",
  });
}

export async function parseAndMatch(input: {
  rawLines: string[];
  matchLimit: number;
}): Promise<ParseAndMatchResult> {
  return requestData<ParseAndMatchResult>("/parse-and-match", {
    method: "POST",
    body: {
      raw_lines: input.rawLines,
      match_limit: input.matchLimit,
    },
  });
}

export async function createPlaylist(input: {
  sessionId: string;
  name: string;
  rawLines: string[];
  matchLimit: number;
}): Promise<PersistedPlaylistResult> {
  return requestData<PersistedPlaylistResult>("/playlists", {
    method: "POST",
    body: {
      session_id: input.sessionId,
      name: input.name,
      raw_lines: input.rawLines,
      match_limit: input.matchLimit,
    },
  });
}

export async function listPlaylists(
  sessionId: string,
): Promise<PersistedPlaylistResult[]> {
  const params = new URLSearchParams({ session_id: sessionId });
  return requestData<PersistedPlaylistResult[]>(`/playlists?${params.toString()}`);
}

export async function getPlaylist(
  playlistId: string,
): Promise<PersistedPlaylistResult> {
  return requestData<PersistedPlaylistResult>(`/playlists/${playlistId}`);
}

export async function renamePlaylist(
  playlistId: string,
  name: string,
): Promise<PersistedPlaylistResult> {
  return requestData<PersistedPlaylistResult>(`/playlists/${playlistId}`, {
    method: "PATCH",
    body: { name },
  });
}

export async function deletePlaylist(
  playlistId: string,
): Promise<DeletedResourceResult> {
  return requestData<DeletedResourceResult>(`/playlists/${playlistId}`, {
    method: "DELETE",
  });
}

export async function reviewPlaylistItem(input: {
  playlistId: string;
  itemId: string;
  matchTrackId: string;
  matchScore: number;
}): Promise<PersistedPlaylistItemResult> {
  return requestData<PersistedPlaylistItemResult>(
    `/playlists/${input.playlistId}/items/${input.itemId}`,
    {
      method: "PATCH",
      body: {
        match_track_id: input.matchTrackId,
        match_score: input.matchScore,
        match_algorithm: "manual",
        source: "manual",
        is_uncertain: false,
      },
    },
  );
}

export async function deletePlaylistItem(
  playlistId: string,
  itemId: string,
): Promise<PersistedPlaylistResult> {
  return requestData<PersistedPlaylistResult>(
    `/playlists/${playlistId}/items/${itemId}`,
    { method: "DELETE" },
  );
}

export async function getPlaylistStats(
  playlistId: string,
): Promise<PlaylistStatsResult> {
  return requestData<PlaylistStatsResult>(`/playlists/${playlistId}/stats`);
}

export async function exportPlaylist(
  playlistId: string,
  format: PlaylistExportFormat,
): Promise<PlaylistExportResult> {
  const params = new URLSearchParams({ format });
  return requestData<PlaylistExportResult>(
    `/playlists/${playlistId}/export?${params.toString()}`,
  );
}
