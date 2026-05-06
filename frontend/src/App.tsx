import {
  Activity,
  Check,
  Download,
  Eye,
  ExternalLink,
  FileMusic,
  Loader2,
  Pencil,
  Plus,
  RefreshCw,
  Server,
  Trash2,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  createPlaylist,
  createSession,
  deletePlaylist,
  deletePlaylistItem,
  exportPlaylist,
  getHealth,
  getPlaylist,
  getPlaylistStats,
  getSession,
  listPlaylists,
  parseAndMatch,
  renamePlaylist,
  reviewPlaylistItem,
  touchSession,
} from "./api/client";
import type {
  HealthResult,
  ParseAndMatchResult,
  PersistedPlaylistItemResult,
  PersistedPlaylistResult,
  PlaylistExportFormat,
  PlaylistExportResult,
  PlaylistStatsResult,
  UserSessionResult,
} from "./api/types";

const SESSION_STORAGE_KEY = "playlist-parser-session-id";

const DEMO_INPUT = [
  "Daft Punk - Around the World",
  "Radiohead - Nude",
  "Bonobo - Kerala",
  "Кино - Группа крови",
].join("\n");

type LoadState = "idle" | "loading";

type Notice = {
  tone: "success" | "error";
  text: string;
};

export function App() {
  const [health, setHealth] = useState<HealthResult | null>(null);
  const [session, setSession] = useState<UserSessionResult | null>(null);
  const [playlists, setPlaylists] = useState<PersistedPlaylistResult[]>([]);
  const [activePlaylist, setActivePlaylist] =
    useState<PersistedPlaylistResult | null>(null);
  const [preview, setPreview] = useState<ParseAndMatchResult | null>(null);
  const [stats, setStats] = useState<PlaylistStatsResult | null>(null);
  const [exportResult, setExportResult] = useState<PlaylistExportResult | null>(null);
  const [rawInput, setRawInput] = useState(DEMO_INPUT);
  const [playlistName, setPlaylistName] = useState("Demo Playlist");
  const [renameValue, setRenameValue] = useState("");
  const [matchLimit, setMatchLimit] = useState(3);
  const [manualTrackIds, setManualTrackIds] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState<Notice | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");

  const rawLines = useMemo(
    () =>
      rawInput
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean),
    [rawInput],
  );

  useEffect(() => {
    void initializeApp();
  }, []);

  useEffect(() => {
    if (session !== null) {
      void refreshPlaylists(session.session_id);
    }
  }, [session]);

  async function runTask(task: () => Promise<void>, successText?: string) {
    setLoadState("loading");
    setNotice(null);
    try {
      await task();
      if (successText !== undefined) {
        setNotice({ tone: "success", text: successText });
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : "Неизвестная ошибка";
      setNotice({ tone: "error", text: message });
    } finally {
      setLoadState("idle");
    }
  }

  async function initializeApp() {
    await runTask(async () => {
      setHealth(await getHealth());
      await initializeSession();
    });
  }

  async function initializeSession() {
    const storedSessionId = localStorage.getItem(SESSION_STORAGE_KEY);
    if (storedSessionId !== null) {
      const existingSession = await getSession(storedSessionId);
      const touchedSession = await touchSession(existingSession.session_id);
      setSession(touchedSession);
      return;
    }

    const createdSession = await createSession("Frontend Session");
    localStorage.setItem(SESSION_STORAGE_KEY, createdSession.session_id);
    setSession(createdSession);
  }

  async function refreshPlaylists(sessionId = session?.session_id) {
    if (sessionId === undefined) {
      return;
    }

    const nextPlaylists = await listPlaylists(sessionId);
    setPlaylists(nextPlaylists);

    if (activePlaylist !== null) {
      const updatedActive = nextPlaylists.find(
        (playlist) => playlist.playlist_id === activePlaylist.playlist_id,
      );
      if (updatedActive !== undefined) {
        setActivePlaylist(updatedActive);
      }
    }
  }

  async function handlePreview() {
    if (rawLines.length === 0) {
      setNotice({ tone: "error", text: "Добавь хотя бы одну строку." });
      return;
    }

    await runTask(async () => {
      const result = await parseAndMatch({ rawLines, matchLimit });
      setPreview(result);
      setExportResult(null);
    }, "Предпросмотр готов.");
  }

  async function handleCreatePlaylist() {
    if (session === null || rawLines.length === 0) {
      setNotice({ tone: "error", text: "Нет session или строк для обработки." });
      return;
    }

    await runTask(async () => {
      const playlist = await createPlaylist({
        sessionId: session.session_id,
        name: playlistName.trim() || "Untitled Playlist",
        rawLines,
        matchLimit,
      });
      setActivePlaylist(playlist);
      setRenameValue(playlist.name ?? "");
      setStats(await getPlaylistStats(playlist.playlist_id));
      setExportResult(null);
      await refreshPlaylists(session.session_id);
    }, "Плейлист создан.");
  }

  async function handleSelectPlaylist(playlistId: string) {
    await runTask(async () => {
      const playlist = await getPlaylist(playlistId);
      setActivePlaylist(playlist);
      setRenameValue(playlist.name ?? "");
      setStats(await getPlaylistStats(playlist.playlist_id));
      setExportResult(null);
    });
  }

  async function handleRenamePlaylist() {
    if (activePlaylist === null) {
      return;
    }

    await runTask(async () => {
      const playlist = await renamePlaylist(activePlaylist.playlist_id, renameValue);
      setActivePlaylist(playlist);
      await refreshPlaylists();
    }, "Название обновлено.");
  }

  async function handleDeletePlaylist() {
    if (activePlaylist === null) {
      return;
    }

    await runTask(async () => {
      await deletePlaylist(activePlaylist.playlist_id);
      setActivePlaylist(null);
      setStats(null);
      setExportResult(null);
      await refreshPlaylists();
    }, "Плейлист удалён.");
  }

  async function handleReviewItem(item: PersistedPlaylistItemResult) {
    if (activePlaylist === null) {
      return;
    }

    const manualTrackId = manualTrackIds[item.item_id]?.trim();
    const matchTrackId =
      manualTrackId || item.match_track_id || `manual:${item.item_id}`;

    await runTask(async () => {
      await reviewPlaylistItem({
        playlistId: activePlaylist.playlist_id,
        itemId: item.item_id,
        matchTrackId,
        matchScore: item.match_score ?? 0.99,
      });
      const playlist = await getPlaylist(activePlaylist.playlist_id);
      setActivePlaylist(playlist);
      setStats(await getPlaylistStats(playlist.playlist_id));
      await refreshPlaylists();
    }, "Item подтверждён.");
  }

  async function handleDeleteItem(itemId: string) {
    if (activePlaylist === null) {
      return;
    }

    await runTask(async () => {
      const playlist = await deletePlaylistItem(activePlaylist.playlist_id, itemId);
      setActivePlaylist(playlist);
      setStats(await getPlaylistStats(playlist.playlist_id));
      await refreshPlaylists();
    }, "Item удалён.");
  }

  async function handleExport(format: PlaylistExportFormat) {
    if (activePlaylist === null) {
      return;
    }

    await runTask(async () => {
      setExportResult(await exportPlaylist(activePlaylist.playlist_id, format));
    }, `Экспорт ${format.toUpperCase()} готов.`);
  }

  function handleManualTrackIdChange(
    itemId: string,
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    setManualTrackIds((current) => ({
      ...current,
      [itemId]: event.target.value,
    }));
  }

  const isLoading = loadState === "loading";
  const backendStatus = health === null ? "offline" : `${health.status} ${health.version}`;
  const resultPanelTitle = activePlaylist?.name ?? "Предпросмотр";
  const resultPanelCount = activePlaylist?.total_items ?? preview?.total ?? 0;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <FileMusic aria-hidden="true" />
          <div>
            <strong>Playlist Parser</strong>
            <span>Research MVP</span>
          </div>
        </div>

        <section className="session-block">
          <div className="section-title">Backend</div>
          <div className={health === null ? "backend-badge offline" : "backend-badge"}>
            <Server aria-hidden="true" />
            {backendStatus}
          </div>
        </section>

        <section className="session-block">
          <div className="section-title">Session</div>
          <code>{session?.session_id ?? "..."}</code>
          <button
            className="icon-text-button"
            type="button"
            onClick={() => void initializeApp()}
            disabled={isLoading}
          >
            <RefreshCw aria-hidden="true" />
            Обновить
          </button>
        </section>

        <section className="playlist-list">
          <div className="section-title">Плейлисты</div>
          {playlists.length === 0 ? (
            <p className="muted">Пока пусто</p>
          ) : (
            playlists.map((playlist) => (
              <button
                key={playlist.playlist_id}
                className={
                  playlist.playlist_id === activePlaylist?.playlist_id
                    ? "playlist-button active"
                    : "playlist-button"
                }
                type="button"
                onClick={() => void handleSelectPlaylist(playlist.playlist_id)}
              >
                <span>{playlist.name ?? "Untitled Playlist"}</span>
                <small>{playlist.total_items} tracks</small>
              </button>
            ))
          )}
        </section>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <h1>Рабочий стол</h1>
            <p>{rawLines.length} строк готово к обработке</p>
          </div>
          <div className="status-pill">
            {isLoading ? <Loader2 className="spin" aria-hidden="true" /> : null}
            {isLoading ? "Выполняется" : "Готово"}
          </div>
        </header>

        {notice !== null ? (
          <div className={`notice ${notice.tone}`}>{notice.text}</div>
        ) : null}

        <div className="workspace-grid">
          <section className="input-panel">
            <div className="panel-heading">
              <h2>Ввод</h2>
              <span>{rawLines.length} lines</span>
            </div>

            <label className="field">
              <span>Название</span>
              <input
                value={playlistName}
                onChange={(event) => setPlaylistName(event.target.value)}
                placeholder="Playlist name"
              />
            </label>

            <label className="field">
              <span>Список треков</span>
              <textarea
                value={rawInput}
                onChange={(event) => setRawInput(event.target.value)}
                spellCheck={false}
              />
            </label>

            <label className="field compact-field">
              <span>Match limit</span>
              <input
                type="number"
                min={1}
                max={20}
                value={matchLimit}
                onChange={(event) => setMatchLimit(Number(event.target.value))}
              />
            </label>

            <div className="input-actions">
              <button
                className="secondary-button"
                type="button"
                onClick={() => void handlePreview()}
                disabled={isLoading || rawLines.length === 0}
              >
                <Eye aria-hidden="true" />
                Предпросмотр
              </button>
              <button
                className="primary-button"
                type="button"
                onClick={() => void handleCreatePlaylist()}
                disabled={isLoading || session === null || rawLines.length === 0}
              >
                <Plus aria-hidden="true" />
                Создать
              </button>
            </div>
          </section>

          <section className="result-panel">
            <div className="panel-heading">
              <h2>{resultPanelTitle}</h2>
              <span>{resultPanelCount} tracks</span>
            </div>

            {activePlaylist === null ? (
              <PreviewPanel preview={preview} />
            ) : (
              <>
                <div className="rename-row">
                  <input
                    value={renameValue}
                    onChange={(event) => setRenameValue(event.target.value)}
                    placeholder="Playlist name"
                  />
                  <button
                    className="icon-button"
                    type="button"
                    title="Переименовать"
                    onClick={() => void handleRenamePlaylist()}
                    disabled={isLoading}
                  >
                    <Pencil aria-hidden="true" />
                  </button>
                  <button
                    className="icon-button danger"
                    type="button"
                    title="Удалить плейлист"
                    onClick={() => void handleDeletePlaylist()}
                    disabled={isLoading}
                  >
                    <Trash2 aria-hidden="true" />
                  </button>
                </div>

                <div className="items-list">
                  {activePlaylist.items.map((item) => (
                    <article key={item.item_id} className="track-row">
                      <div className="track-main">
                        <div className="track-title">
                          {formatTrackTitle(item)}
                          {item.is_uncertain ? (
                            <span className="uncertain">uncertain</span>
                          ) : (
                            <span className="confirmed">confirmed</span>
                          )}
                        </div>
                        <div className="track-meta">
                          <span>{item.match_track_id ?? "no match"}</span>
                          <span>{formatScore(item.match_score)}</span>
                          <span>{item.source ?? "unknown"}</span>
                          <SourceLink href={item.match_external_url} />
                        </div>
                      </div>

                      <input
                        className="manual-input"
                        value={manualTrackIds[item.item_id] ?? ""}
                        onChange={(event) =>
                          handleManualTrackIdChange(item.item_id, event)
                        }
                        placeholder="manual:track-id"
                      />

                      <button
                        className="icon-button"
                        type="button"
                        title="Подтвердить"
                        onClick={() => void handleReviewItem(item)}
                        disabled={isLoading}
                      >
                        <Check aria-hidden="true" />
                      </button>
                      <button
                        className="icon-button danger"
                        type="button"
                        title="Удалить item"
                        onClick={() => void handleDeleteItem(item.item_id)}
                        disabled={isLoading}
                      >
                        <Trash2 aria-hidden="true" />
                      </button>
                    </article>
                  ))}
                </div>
              </>
            )}
          </section>

          <section className="insight-panel">
            <div className="panel-heading">
              <h2>Метрики и экспорт</h2>
              <Activity aria-hidden="true" />
            </div>

            <div className="metric-grid">
              <Metric label="Items" value={stats?.total_items ?? preview?.total ?? 0} />
              <Metric
                label="Uncertain"
                value={stats?.uncertain_count ?? preview?.uncertain_count ?? 0}
              />
              <Metric
                label="Avg score"
                value={formatScore(stats?.average_match_score ?? null)}
              />
              <Metric
                label="Parser"
                value={formatScore(stats?.average_parser_confidence ?? null)}
              />
            </div>

            <div className="export-actions">
              {(["json", "csv", "m3u"] as const).map((format) => (
                <button
                  key={format}
                  className="secondary-button"
                  type="button"
                  onClick={() => void handleExport(format)}
                  disabled={isLoading || activePlaylist === null}
                >
                  <Download aria-hidden="true" />
                  {format.toUpperCase()}
                </button>
              ))}
            </div>

            {exportResult !== null ? (
              <div className="export-box">
                <div className="export-header">
                  <strong>{exportResult.filename}</strong>
                  <span>{exportResult.media_type}</span>
                </div>
                <pre>{exportResult.content}</pre>
              </div>
            ) : null}
          </section>
        </div>
      </section>
    </main>
  );
}

function PreviewPanel({ preview }: { preview: ParseAndMatchResult | null }) {
  if (preview === null) {
    return <div className="empty-state">Сделай предпросмотр или создай плейлист</div>;
  }

  return (
    <div className="preview-list">
      {preview.items.map((item) => {
        const bestMatch = item.match_result.matches[0];
        return (
          <article key={item.parsed_track.raw_input} className="preview-row">
            <div className="track-title">
              {formatParsedTitle(item.parsed_track.artist, item.parsed_track.title)}
              {item.is_uncertain ? (
                <span className="uncertain">uncertain</span>
              ) : (
                <span className="confirmed">match</span>
              )}
            </div>
            <div className="track-meta">
              <span>{bestMatch?.track_id ?? "no match"}</span>
              <span>{formatScore(item.best_score)}</span>
              <span>{bestMatch?.algorithm ?? "n/a"}</span>
              <span>{bestMatch?.source ?? "unknown"}</span>
              <SourceLink href={bestMatch?.candidate.external_url ?? null} />
            </div>
            <p>{item.explanation}</p>
          </article>
        );
      })}
    </div>
  );
}

function SourceLink({ href }: { href: string | null }) {
  if (href === null) {
    return null;
  }

  return (
    <a
      className="source-link"
      href={href}
      target="_blank"
      rel="noreferrer"
      title="Open source"
    >
      <ExternalLink aria-hidden="true" />
      open
    </a>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function formatTrackTitle(item: PersistedPlaylistItemResult): string {
  return formatParsedTitle(item.parsed_artist, item.parsed_title, item.raw_input);
}

function formatParsedTitle(
  artist: string | null,
  title: string | null,
  fallback = "Untitled",
): string {
  if (artist !== null && title !== null) {
    return `${artist} - ${title}`;
  }
  return title ?? fallback;
}

function formatScore(score: number | null): string {
  if (score === null) {
    return "n/a";
  }
  return score.toFixed(2);
}
