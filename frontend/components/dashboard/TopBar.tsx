"use client";
import type { TriggerResult } from "@/lib/types";
import { formatDistanceToNow } from "date-fns";

interface Props {
  triggers: TriggerResult[];
  evaluatedAt: string;
}

const sev = (t: TriggerResult[], s: string) => t.filter(x => x.severity === s).length;

export function TopBar({ triggers, evaluatedAt }: Props) {
  const critical = sev(triggers, "critical");
  const warning  = sev(triggers, "warning");
  const ago      = formatDistanceToNow(new Date(evaluatedAt), { addSuffix: true });

  return (
    <header className="bg-[#161922] border-b border-white/[0.08] px-5 py-3 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-blue-500 flex items-center justify-center text-white text-sm">⚡</div>
        <div>
          <div className="text-sm font-medium text-white">SOP Operations Dashboard</div>
          <div className="text-xs text-gray-500">ElevateBox · Founder&apos;s Office</div>
        </div>
      </div>
      <div className="flex items-center gap-3 text-xs">
        {critical > 0 && (
          <span className="px-2 py-1 rounded-full bg-red-500/15 text-red-400 font-medium">
            {critical} critical
          </span>
        )}
        {warning > 0 && (
          <span className="px-2 py-1 rounded-full bg-amber-500/15 text-amber-400 font-medium">
            {warning} warnings
          </span>
        )}
        <span className="text-gray-500">Updated {ago}</span>
      </div>
    </header>
  );
}
