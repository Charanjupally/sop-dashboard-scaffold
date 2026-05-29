"use client";

import useSWR from "swr";
import { fetcher } from "@/lib/fetcher";
import type { DashboardSnapshot, WidgetMeta } from "@/lib/types";
import { ActionQueue } from "@/components/dashboard/ActionQueue";
import { KpiStrip } from "@/components/dashboard/KpiStrip";
import { AqiPanel, HrPanel, NewsPanel, SopKanban } from "@/components/dashboard/Panels";
import { TopBar } from "@/components/dashboard/TopBar";
import {
  AlphaVantageWidget,
  NewsApiWidget,
  RandomUserWidget,
  RedditWidget,
  RemoteOkWidget,
  UsaJobsWidget,
  WikipediaWidget,
  WhoWidget,
  WorldBankWidget,
} from "@/components/dashboard/ExpandedWidgets";
import { ScraperHealth } from "@/components/dashboard/ScraperHealth";

export default function Dashboard() {
  const { data, error, isLoading } = useSWR<DashboardSnapshot>(
    "/api/sop/triggers",
    fetcher,
    { refreshInterval: 60_000 }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-500 text-sm">
        Running morning scan across 25 sources…
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center h-screen text-red-400 text-sm">
        Failed to load dashboard. Check that the backend is running on port 8000.
      </div>
    );
  }

  const { triggers, snapshot, evaluated_at } = data;
  const queueMeta: WidgetMeta = {
    updated_at: evaluated_at,
    ttl_seconds: 60,
    age_seconds: 0,
    is_stale: false,
  };

  return (
    <div className="min-h-screen bg-[#0f1117]">
      <TopBar triggers={triggers} evaluatedAt={evaluated_at} />
      <div className="p-4 space-y-4 max-w-[1600px] mx-auto">
        <KpiStrip crypto={snapshot.crypto} fx={snapshot.fx} macro={snapshot.macro} />
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <div className="xl:col-span-2">
            <ActionQueue triggers={triggers} meta={queueMeta} />
          </div>
          <WorldBankWidget widget={snapshot.world_bank} />
          <AqiPanel widget={snapshot.aqi} />
          <HrPanel widget={snapshot.hr} />
          <NewsPanel widget={snapshot.news} />
          <SopKanban widget={snapshot.sop} />
          <RedditWidget widget={snapshot.reddit} />
          <WhoWidget widget={snapshot.who} />
          <RandomUserWidget widget={snapshot.random_user} />
          <WikipediaWidget widget={snapshot.wikipedia} />
          <RemoteOkWidget widget={snapshot.remoteok} />
          <AlphaVantageWidget widget={snapshot.alpha_vantage} />
          <UsaJobsWidget widget={snapshot.usajobs} />
          <NewsApiWidget widget={snapshot.newsapi} />
        </div>
        <div className="pt-2">
          <ScraperHealth />
        </div>
      </div>
    </div>
  );
}
