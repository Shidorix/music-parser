export type ApiMeta = {
  total: number;
  page: number;
};

export type ApiError = {
  code: string;
  message: string;
};

export type ApiResponse<T> = {
  data: T | null;
  meta: ApiMeta | null;
  error: ApiError | null;
};

export type HealthResult = {
  status: string;
  version: string;
};

export type UserSessionResult = {
  session_id: string;
  display_name: string | null;
  created_at: string;
  last_seen_at: string;
  explanation: string;
};

export type ParsedTrack = {
  raw_input: string;
  normalized_input: string;
  artist: string | null;
  title: string | null;
  confidence: number;
  pattern: string;
  explanation: string;
  language: string;
  language_confidence: number;
  language_explanation: string;
  normalization_steps: string[];
  transliteration_candidates: unknown[];
  transliteration_explanation: string;
};

export type TrackCandidate = {
  track_id: string;
  artist: string | null;
  title: string;
  source: string;
  external_url: string | null;
};

export type MatchResult = {
  track_id: string;
  query: string;
  candidate: TrackCandidate;
  score: number;
  algorithm: string;
  source: string;
  distance: number;
  normalized_query: string;
  normalized_candidate: string;
  explanation: string;
  query_variant_source: string;
  query_variant_confidence: number;
};

export type ParsedTrackMatchResult = {
  parsed_track_raw_input: string;
  query_variants: {
    text: string;
    source: string;
    confidence: number;
    explanation: string;
  }[];
  matches: MatchResult[];
  explanation: string;
};

export type ParseAndMatchItemResult = {
  parsed_track: ParsedTrack;
  match_result: ParsedTrackMatchResult;
  source_reports: {
    source: string;
    status: string;
    candidate_count: number;
    error_code: string | null;
    error_message: string | null;
  }[];
  best_score: number;
  is_uncertain: boolean;
  explanation: string;
};

export type ParseAndMatchResult = {
  items: ParseAndMatchItemResult[];
  total: number;
  uncertain_count: number;
  confidence_threshold: number;
  explanation: string;
};

export type PersistedPlaylistItemResult = {
  item_id: string;
  position: number;
  raw_input: string;
  parsed_artist: string | null;
  parsed_title: string | null;
  parser_confidence: number;
  match_track_id: string | null;
  match_external_url: string | null;
  match_score: number | null;
  match_algorithm: string | null;
  source: string | null;
  is_uncertain: boolean;
};

export type PersistedPlaylistResult = {
  playlist_id: string;
  session_id: string;
  name: string | null;
  created_at: string;
  total_items: number;
  uncertain_count: number;
  items: PersistedPlaylistItemResult[];
  explanation: string;
};

export type PlaylistStatsResult = {
  playlist_id: string;
  total_items: number;
  uncertain_count: number;
  confirmed_count: number;
  average_match_score: number | null;
  average_parser_confidence: number | null;
  source_counts: Record<string, number>;
  algorithm_counts: Record<string, number>;
  uncertain_positions: number[];
  explanation: string;
};

export type PlaylistExportFormat = "json" | "csv" | "m3u";

export type PlaylistExportResult = {
  filename: string;
  format: PlaylistExportFormat;
  media_type: string;
  content: string;
  total_items: number;
  explanation: string;
};

export type DeletedResourceResult = {
  resource_id: string;
  resource_type: string;
  deleted: boolean;
  explanation: string;
};
