"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import type { ScraperStatusResponse } from "@/lib/types";
import { WidgetShell } from "@/components/dashboard/WidgetShell";

function statusMark(enabled: boolean) {
  return enabled ? "✓" : "✕";
}

function statusColor(enabled: boolean) {
  return enabled ? "text-emerald-400" : "text-rose-400";
}

export function ScraperHealth() {
  const { data, error } = useSWR<ScraperStatusResponse>("/api/scrapers/status", fetcher, { refreshInterval: 60_000 });

  return (
    <WidgetShell title="Scraper Health" subtitle="YAML-configured scraper controls" meta={data ? { updated_at: data.generated_at, ttl_seconds: 60, age_seconds: 0, is_stale: false } : { updated_at: new Date().toISOString(), ttl_seconds: 60, age_seconds: 0, is_stale: false }}>
      {error ? (
        <div className="text-sm text-rose-300">Failed to load scraper status.</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[11px]">
            <thead className="text-gray-500">
              <tr>
                <th className="py-1 pr-3 font-normal">Scraper Name</th>
                <th className="py-1 pr-3 font-normal">Enabled</th>
                <th className="py-1 pr-3 font-normal">Rate Limit</th>
                <th className="py-1 pr-3 font-normal">Last Run</th>
                <th className="py-1 pr-3 font-normal">Last Status</th>
                <th className="py-1 pr-3 font-normal">SOP Trigger</th>
              </tr>
            </thead>
            <tbody>
              {(data?.rows ?? []).map((row) => (
                <tr key={row.name} className="border-t border-white/[0.06]">
                  <td className="py-2 pr-3 text-white">{row.name}</td>
                  <td className={`py-2 pr-3 ${statusColor(row.enabled)}`}>{statusMark(row.enabled)}</td>
                  <td className="py-2 pr-3 text-gray-300">{row.rate_limit_seconds ?? "—"}s</td>
                  <td className="py-2 pr-3 text-gray-300">{row.last_run ?? "—"}</td>
                  <td className="py-2 pr-3 text-gray-300">{row.last_status ?? "—"}</td>
                  <td className="py-2 pr-3 text-gray-300">{row.sop_trigger}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </WidgetShell>
  );
}
