"use client";
import type { TriggerResult, WidgetMeta } from "@/lib/types";
import { WidgetShell } from "@/components/dashboard/WidgetShell";

const SEV_COLOR: Record<string, string> = {
  critical: "#f05252",
  warning:  "#f5a623",
  info:     "#4f9cf9",
};

const SEV_BG: Record<string, string> = {
  critical: "bg-red-500/10 text-red-400",
  warning:  "bg-amber-500/10 text-amber-400",
  info:     "bg-blue-500/10 text-blue-400",
};

function slaColor(hoursLeft: number, sla: number) {
  const ratio = hoursLeft / sla;
  if (ratio < 0.3) return "text-red-400";
  if (ratio < 0.6) return "text-amber-400";
  return "text-gray-400";
}

export function ActionQueue({ triggers, meta }: { triggers: TriggerResult[]; meta: WidgetMeta }) {
  if (triggers.length === 0) {
    return (
      <WidgetShell title={`Morning Action Queue — 0 triggered`} subtitle="All thresholds clear" meta={meta}>
        <div className="py-8 text-center text-sm text-gray-500">✅ No triggers fired — all thresholds clear</div>
      </WidgetShell>
    );
  }

  return (
    <WidgetShell
      title={`Morning Action Queue — ${triggers.length} triggered`}
      subtitle={`${triggers.filter((t) => t.severity === "critical").length} critical`}
      meta={meta}
    >
      <div className="space-y-2">
        {triggers.map((t) => {
          // Rough SLA remaining: assume triggered now, SLA is N hours
          const slaLeft = t.sla_hours; // in real app: sla_hours - elapsed
          return (
            <div
              key={t.id}
              className="bg-[#1e2230] border border-white/[0.06] rounded-lg px-4 py-3 flex items-center gap-3 hover:border-white/[0.14] transition-colors cursor-pointer"
            >
              <div
                className="w-2 h-2 rounded-full flex-shrink-0"
                style={{ background: SEV_COLOR[t.severity] }}
              />
              <div className="flex-1 min-w-0">
                <div className="text-[13px] font-medium text-white truncate">{t.sop_name}</div>
                <div className="text-[11px] text-gray-500 mt-0.5">{t.summary}</div>
                <div className="text-[10px] text-gray-600 mt-1">{t.source} · {t.assignee}</div>
              </div>
              <div className="text-right flex-shrink-0">
                <div className={`text-[12px] font-medium ${slaColor(slaLeft, t.sla_hours)}`}>
                  {slaLeft}h left
                </div>
                <div className="text-[10px] text-gray-600">SLA: {t.sla_hours}h</div>
              </div>
            </div>
          );
        })}
      </div>
    </WidgetShell>
  );
}
