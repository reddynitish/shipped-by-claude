import { useCallback, useEffect, useState } from "react";

const API = "";

function timeAgo(iso) {
  if (!iso) return "";
  const s = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 3600) return `${Math.max(1, Math.floor(s / 60))}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

const SOURCE_LABELS = {
  claude_md: "CLAUDE.md",
  topic: "#claude-code",
  commit_trailer: "co-authored",
};

function Node() {
  return (
    <div className="relative flex w-8 shrink-0 justify-center">
      <div className="absolute inset-y-0 w-px bg-edge" />
      <div className="relative mt-6 h-3 w-3 rounded-full border-2 border-ship bg-ink" />
    </div>
  );
}

function PostCard({ post }) {
  return (
    <article className="flex">
      <Node />
      <div className="mb-4 min-w-0 flex-1 rounded-lg border border-edge bg-panel p-4 transition-colors hover:border-ship/40">
        <div className="flex items-center gap-3">
          <img
            src={post.owner_avatar_url}
            alt=""
            className="h-9 w-9 rounded-full border border-edge"
            loading="lazy"
          />
          <div className="min-w-0">
            <div className="truncate font-semibold">{post.owner_login}</div>
            <div className="font-mono text-xs text-dim">
              pushed {timeAgo(post.pushed_at)}
            </div>
          </div>
          <div className="ml-auto flex gap-1">
            {post.signal_source?.split(",").map((s) => (
              <span
                key={s}
                className="rounded border border-edge px-1.5 py-0.5 font-mono text-[10px] text-dim"
              >
                {SOURCE_LABELS[s] ?? s}
              </span>
            ))}
          </div>
        </div>

        <p className="mt-3 leading-snug">{post.caption}</p>
        {post.description && (
          <p className="mt-1 text-sm text-dim">{post.description}</p>
        )}

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-xs text-dim">
          <span>⭐ {post.stars}</span>
          {post.language && (
            <span className="rounded bg-edge px-1.5 py-0.5">{post.language}</span>
          )}
          <a
            href={post.repo_url}
            target="_blank"
            rel="noreferrer"
            className="ml-auto text-ship hover:underline"
          >
            View on GitHub →
          </a>
        </div>
      </div>
    </article>
  );
}

function Skeleton() {
  return (
    <div className="flex">
      <Node />
      <div className="mb-4 flex-1 animate-pulse rounded-lg border border-edge bg-panel p-4">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-edge" />
          <div className="h-4 w-32 rounded bg-edge" />
        </div>
        <div className="mt-4 h-4 w-3/4 rounded bg-edge" />
        <div className="mt-2 h-3 w-1/2 rounded bg-edge" />
      </div>
    </div>
  );
}

const STAR_FILTERS = [
  { label: "All", value: 0 },
  { label: "10+", value: 10 },
  { label: "50+", value: 50 },
  { label: "100+", value: 100 },
];

export default function App() {
  const [posts, setPosts] = useState(null); // null = loading
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [sort, setSort] = useState("top");
  const [minStars, setMinStars] = useState(0);

  const load = useCallback(async () => {
    try {
      const res = await fetch(
        `${API}/posts?page=1&page_size=50&sort=${sort}&min_stars=${minStars}`
      );
      const data = await res.json();
      setPosts(data.posts);
      setError(null);
    } catch {
      setError("Can't reach the backend — is uvicorn running on :8000?");
      setPosts([]);
    }
  }, [sort, minStars]);

  useEffect(() => {
    load();
  }, [load]);

  const refresh = async () => {
    setRefreshing(true);
    try {
      await fetch(`${API}/refresh`, { method: "POST" });
      await load();
    } catch {
      setError("Refresh failed — check the backend logs.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 pb-20">
      <header className="sticky top-0 z-10 -mx-4 border-b border-edge bg-ink/90 px-4 py-3 backdrop-blur">
        <div className="flex items-center gap-3">
          <h1 className="font-mono text-lg font-bold">
            <span className="text-ship">$</span> shipped_by_claude
          </h1>
          <button
            onClick={refresh}
            disabled={refreshing}
            className="ml-auto rounded-md border border-ship/50 px-3 py-1.5 font-mono text-sm text-ship transition hover:bg-ship/10 disabled:opacity-50"
          >
            {refreshing ? "fetching…" : "↻ Refresh Feed"}
          </button>
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2 font-mono text-xs">
          <div className="flex overflow-hidden rounded-md border border-edge" role="group" aria-label="sort">
            {["top", "latest"].map((s) => (
              <button
                key={s}
                onClick={() => setSort(s)}
                className={
                  sort === s
                    ? "bg-ship px-3 py-1 font-semibold text-ink"
                    : "px-3 py-1 text-dim hover:text-ship"
                }
              >
                {s === "top" ? "Top" : "Latest"}
              </button>
            ))}
          </div>
          <div className="ml-2 flex gap-1" role="group" aria-label="minimum stars">
            {STAR_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => setMinStars(f.value)}
                className={
                  minStars === f.value
                    ? "rounded-full border border-ship bg-ship/15 px-2.5 py-1 font-semibold text-ship"
                    : "rounded-full border border-edge px-2.5 py-1 text-dim hover:border-ship/40 hover:text-ship"
                }
              >
                {f.value === 0 ? "All" : `⭐ ${f.label}`}
              </button>
            ))}
          </div>
        </div>
      </header>

      <p className="mt-4 mb-6 font-mono text-xs text-dim">
        real repos shipped with Claude Code, fresh off the GitHub API
      </p>

      {error && (
        <div className="mb-4 rounded-lg border border-red-900 bg-red-950/40 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {posts === null && (
        <>
          <Skeleton />
          <Skeleton />
          <Skeleton />
        </>
      )}

      {posts !== null && posts.length === 0 && !error && (
        <div className="rounded-lg border border-dashed border-edge p-10 text-center">
          <p className="font-mono text-dim">feed is empty.</p>
          <button
            onClick={refresh}
            disabled={refreshing}
            className="mt-4 rounded-md bg-ship px-4 py-2 font-mono text-sm font-semibold text-ink hover:opacity-90 disabled:opacity-50"
          >
            {refreshing ? "fetching…" : "Pull the first posts →"}
          </button>
        </div>
      )}

      {posts?.map((p) => (
        <PostCard key={p.id} post={p} />
      ))}
    </div>
  );
}
