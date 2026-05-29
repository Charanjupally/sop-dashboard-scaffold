"use client";

import type { ReactNode } from "react";
import { formatDistanceToNow } from "date-fns";
import type { WidgetMeta } from "@/lib/types";

interface Props {
  title: string;
  meta: WidgetMeta;
  subtitle?: string;
  className?: string;
  children: ReactNode;
}

export function WidgetShell({ title, subtitle, meta, className = "", children }: Props) {
  const ago = formatDistanceToNow(new Date(meta.updated_at), { addSuffix: true });

  return (
    <div className={`relative flex h-full flex-col rounded-xl border border-white/[0.08] bg-[#161922] p-4 shadow-soft ${className}`}>
      {meta.is_stale && (
        <div className="absolute right-3 top-3 rounded-full border border-amber-400/40 bg-amber-500/15 px-2 py-0.5 text-[10px] font-semibold tracking-wide text-amber-300">
          STALE
        </div>
      )}
      <div className="mb-3 pr-14">
        <div className="text-[11px] uppercase tracking-wide text-gray-500">{title}</div>
        {subtitle && <div className="mt-1 text-xs text-gray-400">{subtitle}</div>}
      </div>
      <div className="flex-1">{children}</div>
      <div className="mt-3 text-[10px] text-gray-500">Last updated: {ago}</div>
    </div>
  );
}
