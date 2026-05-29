"use client";
import type { AqiCity, HrMember, SopItem, WidgetEnvelope } from "@/lib/types";
import { WidgetShell } from "@/components/dashboard/WidgetShell";

// ── AQI Panel ─────────────────────────────────────────
function aqiColor(aqi: number | null) {
  if (aqi == null) return "text-gray-500";
  if (aqi >= 200) return "text-red-400";
  if (aqi >= 150) return "text-amber-400";
  if (aqi >= 100) return "text-yellow-400";
  return "text-emerald-400";
}

function aqiBarColor(aqi: number | null) {
  if (aqi == null) return "bg-gray-600";
  if (aqi >= 200) return "bg-red-500";
  if (aqi >= 150) return "bg-amber-500";
  if (aqi >= 100) return "bg-yellow-500";
  return "bg-emerald-500";
}

export function AqiPanel({ widget }: { widget: WidgetEnvelope<{ cities: AqiCity[] }> }) {
  return (
    <WidgetShell title="AQI · Office Cities" subtitle="AQI monitor" meta={widget.meta}>
      <div className="space-y-2.5">
        {widget.data.cities.map((c) => (
          <div key={c.city} className="flex items-center justify-between gap-3">
            <span className="text-[12px] text-white w-20 shrink-0">{c.city}</span>
            <div className="flex-1 h-1.5 bg-[#1e2230] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${aqiBarColor(c.aqi)}`}
                style={{ width: `${Math.min(((c.aqi ?? 0) / 300) * 100, 100)}%` }}
              />
            </div>
            <span className={`text-[12px] font-medium w-8 text-right ${aqiColor(c.aqi)}`}>
              {c.aqi ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}


// ── HR Panel ──────────────────────────────────────────
function utilColor(pct: number) {
  if (pct >= 90) return "bg-red-500";
  if (pct >= 75) return "bg-amber-500";
  return "bg-emerald-500";
}

export function HrPanel({ widget }: { widget: WidgetEnvelope<{ members: HrMember[] }> }) {
  return (
    <WidgetShell title="Team Utilization · Clockify" subtitle="HR utilization monitor" meta={widget.meta}>
      <div className="space-y-2.5">
        {widget.data.members.map((m) => (
          <div key={m.id}>
            <div className="flex items-center justify-between text-[11px] mb-1">
              <span className="text-white">{m.name}</span>
              <span className={m.utilization_pct >= 90 ? "text-red-400" : "text-gray-400"}>
                {m.utilization_pct}%
              </span>
            </div>
            <div className="h-1 bg-[#1e2230] rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${utilColor(m.utilization_pct)}`}
                style={{ width: `${m.utilization_pct}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}


// ── News Panel ────────────────────────────────────────
export function NewsPanel({ widget }: { widget: WidgetEnvelope<{ hn_stories: { id: number; title: string; url: string; score: number }[]; sec_filings: { company: string; form: string; filed_at: string; url: string }[] }> }) {
  return (
    <WidgetShell title="HackerNews · SEC 8-K Filings" subtitle="News watcher" meta={widget.meta}>
      <div className="space-y-2">
        {widget.data.hn_stories.slice(0, 4).map((s) => (
          <div key={s.id} className="flex gap-3 items-start py-1.5 border-b border-white/[0.05] last:border-0">
            <span className="text-[11px] font-medium text-blue-400 bg-blue-500/10 px-1.5 py-0.5 rounded min-w-[36px] text-center">
              {s.score}
            </span>
            <div>
              <div className="text-[12px] text-white leading-snug">{s.title}</div>
              {s.url && (
                <div className="text-[10px] text-gray-600 mt-0.5">
                  {new URL(s.url).hostname.replace("www.", "")}
                </div>
              )}
            </div>
          </div>
        ))}
        {widget.data.sec_filings.length > 0 && (
          <div className="pt-2 border-t border-white/[0.08] mt-2">
            <div className="text-[10px] text-gray-600 mb-1.5 uppercase tracking-wide">SEC 8-K Filings</div>
            {widget.data.sec_filings.slice(0, 2).map((f, i) => (
              <div key={i} className="text-[11px] text-amber-400 py-1 flex gap-2 items-center">
                <span className="text-gray-600">8-K</span>
                <span>{f.company}</span>
                <span className="text-gray-600">·</span>
                <span className="text-gray-500">{f.filed_at}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </WidgetShell>
  );
}


// ── SOP Kanban ────────────────────────────────────────
const STATUS_ORDER = ["Draft", "Review", "Published", "Retired"] as const;

const STATUS_STYLE: Record<string, { dot: string; header: string }> = {
  Draft:     { dot: "bg-gray-500",    header: "text-gray-400" },
  Review:    { dot: "bg-amber-500",   header: "text-amber-400" },
  Published: { dot: "bg-emerald-500", header: "text-emerald-400" },
  Retired:   { dot: "bg-gray-700",    header: "text-gray-600" },
};

export function SopKanban({ widget }: { widget: WidgetEnvelope<{ sops: SopItem[]; stale_sops: SopItem[] }> }) {
  const staleIds = new Set(widget.data.stale_sops.map(s => s.id));
  const grouped = Object.fromEntries(
    STATUS_ORDER.map(s => [s, widget.data.sops.filter(x => x.status === s)])
  );

  return (
    <WidgetShell title="SOP Registry · Notion" subtitle="Registry and review status" meta={widget.meta}>
      <div className="grid grid-cols-4 gap-3">
        {STATUS_ORDER.map((status) => {
          const style = STATUS_STYLE[status];
          const items = grouped[status] ?? [];
          return (
            <div key={status}>
              <div className={`flex items-center justify-between text-[10px] uppercase tracking-wide mb-2 ${style.header}`}>
                <span>{status}</span>
                <span className="bg-[#1e2230] px-1.5 py-0.5 rounded-full text-gray-500">{items.length}</span>
              </div>
              <div className="space-y-1.5">
                {items.map((sop) => (
                  <div
                    key={sop.id}
                    className={`bg-[#1e2230] border rounded-md px-3 py-2 ${staleIds.has(sop.id) ? "border-amber-500/30" : "border-white/[0.06]"}`}
                  >
                    <div className="text-[11px] text-white leading-snug">{sop.title}</div>
                    {staleIds.has(sop.id) && (
                      <div className="text-[10px] text-amber-500 mt-1">⚠ Needs review</div>
                    )}
                    {sop.last_reviewed && (
                      <div className="text-[10px] text-gray-600 mt-0.5">
                        {sop.last_reviewed.slice(0, 10)}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </WidgetShell>
  );
}
