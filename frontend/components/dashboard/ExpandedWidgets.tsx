"use client";

import type { CSSProperties } from "react";
import React from "react";
import { format } from "date-fns";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Customized,
  Line,
  LineChart,
  LabelList,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";
import type {
  AlphaCandle,
  RandomUserEmployee,
  RedditPost,
  RemoteOkJob,
  WidgetEnvelope,
  WhoCell,
  WikipediaSeriesPoint,
  WorldBankBar,
  NewsHeadline,
  UsaJob,
} from "@/lib/types";
import { WidgetShell } from "@/components/dashboard/WidgetShell";

function compactNumber(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(value);
}

function usd(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `$${new Intl.NumberFormat("en", { maximumFractionDigits: 0 }).format(value)}`;
}

function dateLabel(value: string | null | undefined) {
  if (!value) return "—";
  return value.slice(0, 10);
}

function salaryTick(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `$${Math.round(value / 1000)}k`;
}

function moneyLabel(value: number | null | undefined) {
  if (value == null || Number.isNaN(value)) return "—";
  return `$${value.toFixed(2)}`;
}

class ChartErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: Error | null }> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  override render() {
    if (this.state.hasError) {
      return <div style={{ color: "red", fontSize: 12, padding: 12 }}>Chart error: {this.state.error?.message}</div>;
    }

    return this.props.children;
  }
}

const CandleShape = (props: {
  x: number;
  y: number;
  width: number;
  height: number;
  open: number;
  close: number;
  high: number;
  low: number;
  fill?: string;
}) => {
  const { x, y, width, height, open, close } = props;
  const isUp = close >= open;
  const color = isUp ? "#22c55e" : "#ef4444";
  const bodyTop = Math.min(open, close);
  const bodyHeight = Math.max(Math.abs(close - open), 2);
  return (
    <g>
      <line x1={x + width / 2} y1={y} x2={x + width / 2} y2={y + height} stroke={color} strokeWidth={1} />
      <rect x={x + 2} y={bodyTop} width={Math.max(width - 4, 2)} height={bodyHeight} fill={color} />
    </g>
  );
};

export function WorldBankWidget({ widget }: { widget: WidgetEnvelope<{ bars: WorldBankBar[]; trigger_hint: string; source: string }> }) {
  let chartData: Array<{ country: string; gdp: number }> = [];

  try {
    const rawData = widget.data.bars as Array<
      WorldBankBar & {
        countryiso3code?: string;
        value?: number | null;
        date?: string;
        country?: { value?: string; id?: string } | string;
      }
    >;

    const records = Array.isArray(rawData) && Array.isArray((rawData as unknown as unknown[])[1]) ? ((rawData as unknown as unknown[])[1] as Array<Record<string, unknown>>) : rawData;

    chartData = (records ?? [])
      .map((record: any) => {
        const rawValue = record?.value ?? record?.gdp;
        const numericValue = Number(rawValue);
        const gdp = Number.isFinite(numericValue) ? parseFloat((numericValue > 1e9 ? numericValue / 1e12 : numericValue).toFixed(2)) : 0;
        const country = record?.countryiso3code ?? (typeof record?.country === "string" ? record.country : record?.country?.id) ?? record?.country ?? "N/A";
        return { country, gdp };
      })
      .filter((record) => record.gdp > 0 && record.country);
  } catch (e) {
    console.error("WorldBank transform error:", e);
  }

  console.log("WorldBank chartData:", chartData);

  return (
    <WidgetShell title="World Bank GDP" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="h-56">
        {!chartData || chartData.length === 0 ? (
          <div style={{ color: "#888", fontSize: 12, padding: 12 }}>No GDP data available</div>
        ) : (
          <ChartErrorBoundary>
            <BarChart width={340} height={220} data={chartData} margin={{ top: 20, right: 20, bottom: 5, left: 40 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="country" tick={{ fill: "#888", fontSize: 11 }} />
              <YAxis tick={{ fill: "#888", fontSize: 11 }} label={{ value: "USD Trillion", angle: -90, position: "insideLeft", fill: "#888", fontSize: 11 }} />
              <Tooltip formatter={(v: number) => [`$${v}T`, "GDP"]} />
              <Bar dataKey="gdp" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                <LabelList dataKey="gdp" position="top" style={{ fill: "#888", fontSize: 11 }} formatter={(v: number) => `${v}T`} />
              </Bar>
            </BarChart>
          </ChartErrorBoundary>
        )}
      </div>
      <div className="mt-2 flex flex-wrap gap-2 text-[10px] text-gray-500">
        {chartData.map((bar) => (
          <span key={bar.country} className="rounded-full bg-white/[0.04] px-2 py-0.5">
            {bar.country}
          </span>
        ))}
      </div>
    </WidgetShell>
  );
}

export function RedditWidget({ widget }: { widget: WidgetEnvelope<{ posts: RedditPost[]; trigger_hint: string; source: string }> }) {
  return (
    <WidgetShell title="Reddit Sentiment" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="space-y-2">
        {widget.data.posts.map((post, index) => (
          <div key={`${post.title}-${index}`} className="rounded-lg border border-white/[0.06] bg-[#1e2230] px-3 py-2">
            <div className="max-h-10 overflow-hidden text-ellipsis text-[12px] text-white leading-snug">{post.title}</div>
            <div className="mt-1 flex items-center gap-3 text-[10px] text-gray-400">
              <span>Score {post.score}</span>
              <span>Comments {post.comments}</span>
            </div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}

function heatColor(value: number, min: number, max: number) {
  if (max <= min) return "rgba(245, 158, 11, 0.35)";
  const t = Math.max(0, Math.min(1, (value - min) / (max - min)));
  const red = Math.round(239 + (239 - 239) * t);
  const green = Math.round(68 + (68 - 68) * t);
  const blue = Math.round(68 + (68 - 68) * t);
  return `rgba(${red}, ${green}, ${blue}, ${0.18 + t * 0.62})`;
}

export function WhoWidget({ widget }: { widget: WidgetEnvelope<{ cells: WhoCell[]; trigger_hint: string; source: string }> }) {
  const values = widget.data.cells.map((cell) => cell.value);
  const min = Math.min(...values, 0);
  const max = Math.max(...values, 1);
  return (
    <WidgetShell title="WHO Health Indicators" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        {widget.data.cells.map((cell) => (
          <div key={cell.country} className="rounded-lg border border-white/[0.06] p-3" style={{ background: heatColor(cell.value, min, max) } as CSSProperties}>
            <div className="text-[11px] text-white">{cell.country}</div>
            <div className="mt-1 text-lg font-medium text-white">{cell.value.toFixed(1)}</div>
            <div className="text-[10px] text-gray-200/70">{cell.year ?? "—"}</div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}

function distributionBar(entries: [string, number][]) {
  const total = entries.reduce((sum, [, count]) => sum + count, 0) || 1;
  return (
    <div className="mt-3 space-y-2">
      {entries.map(([label, count], index) => (
        <div key={`${label}-${index}`}>
          <div className="mb-1 flex items-center justify-between text-[10px] text-gray-500">
            <span>{label}</span>
            <span>{count}</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-[#1e2230]">
            <div className="h-full rounded-full bg-sky-400" style={{ width: `${(count / total) * 100}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function RandomUserWidget({ widget }: { widget: WidgetEnvelope<{ employees: RandomUserEmployee[]; gender_distribution: Record<string, number>; country_distribution: Record<string, number>; trigger_hint: string; source: string }> }) {
  const genders = Object.entries(widget.data.gender_distribution);
  const countries = Object.entries(widget.data.country_distribution);
  return (
    <WidgetShell title="RandomUser HR" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="max-h-72 overflow-auto pr-1">
        <table className="w-full text-left text-[11px]">
          <thead className="sticky top-0 bg-[#161922] text-gray-500">
            <tr>
              <th className="py-1 pr-2 font-normal">Employee</th>
              <th className="py-1 pr-2 font-normal">Country</th>
              <th className="py-1 pr-2 font-normal">Age</th>
              <th className="py-1 pr-2 font-normal">Gender</th>
            </tr>
          </thead>
          <tbody>
            {widget.data.employees.map((employee, index) => (
              <tr key={`${employee.name}-${index}`} className="border-t border-white/[0.06]">
                <td className="py-2 pr-2 text-white">
                  <div className="flex items-center gap-2">
                    {employee.avatar ? <img src={employee.avatar} alt={employee.name} className="h-6 w-6 rounded-full" /> : <div className="h-6 w-6 rounded-full bg-white/[0.08]" />}
                    <span>{employee.name}</span>
                  </div>
                </td>
                <td className="py-2 pr-2 text-gray-300">{employee.country}</td>
                <td className="py-2 pr-2 text-gray-300">{employee.age ?? "—"}</td>
                <td className="py-2 pr-2 text-gray-300">{employee.gender}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {distributionBar(genders)}
      {distributionBar(countries)}
    </WidgetShell>
  );
}

export function WikipediaWidget({ widget }: { widget: WidgetEnvelope<{ series: { article: string; points: WikipediaSeriesPoint[] }[]; trigger_hint: string; source: string }> }) {
  return (
    <WidgetShell title="Wikipedia Pageviews" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart margin={{ top: 8, right: 8, left: 0, bottom: 0 }} data={widget.data.series[0]?.points.map((point, index) => ({ ...point, a: point.views, b: widget.data.series[1]?.points[index]?.views ?? null })) ?? []}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
            <XAxis dataKey="week" tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} interval={5} />
            <YAxis tickFormatter={compactNumber} tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} />
            <Tooltip />
            <Line type="monotone" dataKey="a" stroke="#38bdf8" strokeWidth={2} dot={false} name={widget.data.series[0]?.article ?? "Series A"} />
            <Line type="monotone" dataKey="b" stroke="#f59e0b" strokeWidth={2} dot={false} name={widget.data.series[1]?.article ?? "Series B"} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </WidgetShell>
  );
}

export function RemoteOkWidget({ widget }: { widget: WidgetEnvelope<{ jobs: RemoteOkJob[]; trigger_hint: string; source: string }> }) {
  const jobs = widget.data.jobs.filter((job) => Boolean(job.title && job.company));
  const scatterData = jobs.map((job, index) => {
    const salary = job.salary_min != null && job.salary_max != null ? (job.salary_min + job.salary_max) / 2 : 50000;
    return {
      x: new Date(job.posted_at ?? Date.now()).getTime(),
      y: salary,
      z: Math.max(job.tags?.length ?? job.tag_count ?? 1, 1),
      title: job.title,
      company: job.company,
      index,
    };
  });
  const hasEnoughData = scatterData.length >= 10;

  const tooltipContent = ({ active, payload }: { active?: boolean; payload?: Array<{ payload?: (typeof scatterData)[number] }> }) => {
    if (!active || !payload?.length) return null;
    const point = payload[0]?.payload;
    if (!point) return null;
    return (
      <div className="rounded-lg border border-white/[0.08] bg-[#0f1117] px-3 py-2 text-[11px] text-gray-200 shadow-xl">
        <div className="font-medium text-white">{point.title}</div>
        <div className="text-gray-400">{point.company}</div>
        <div className="mt-1 text-gray-300">{format(new Date(point.x), "MMM d")}</div>
        <div className="text-gray-300">{salaryTick(point.y)}</div>
        <div className="text-gray-400">{point.z} tags</div>
      </div>
    );
  };
  return (
    <WidgetShell title="RemoteOK Jobs" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="h-64">
        {hasEnoughData ? (
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 8, right: 16, bottom: 10, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis type="number" dataKey="x" domain={["dataMin", "dataMax"]} tickFormatter={(value) => format(new Date(value), "MMM d")} tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis type="number" dataKey="y" tickFormatter={salaryTick} tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} />
              <ZAxis dataKey="z" range={[40, 400]} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} content={tooltipContent} />
              <Scatter data={scatterData} fill="#38bdf8" />
            </ScatterChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-white/[0.08] bg-[#0f1117] text-[12px] text-gray-400">
            Not enough data
          </div>
        )}
      </div>
      <div className="mt-2 space-y-1 text-[11px] text-gray-400">
        {widget.data.jobs.slice(0, 3).map((job) => (
          <div key={`${job.title}-${job.company}`} className="flex items-center justify-between gap-2">
            <span className="truncate text-white">{job.title} · {job.company}</span>
            <span>{job.tag_count} tags</span>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}

function CandlestickSvg({ candles }: { candles: AlphaCandle[] }) {
  const points = candles.slice(-20).map((candle) => ({
    date: format(new Date(candle.date), "MMM d"),
    open: candle.open,
    high: candle.high,
    low: candle.low,
    close: candle.close,
  }));
  const minPrice = Math.min(...points.map((c) => c.low));
  const maxPrice = Math.max(...points.map((c) => c.high));
  const yDomain: [number, number] = [minPrice * 0.998, maxPrice * 1.002];

  const CandleLayer = ({ xAxisMap, yAxisMap }: any) => {
    const xAxis = Object.values(xAxisMap ?? {})[0] as { scale?: (value: string) => number; bandwidth?: () => number } | undefined;
    const yAxis = Object.values(yAxisMap ?? {})[0] as { scale?: (value: number) => number } | undefined;
    const xScale = xAxis?.scale;
    const yScale = yAxis?.scale;
    if (!xScale || !yScale) return null;

    const bandwidth = typeof xAxis.bandwidth === "function" ? xAxis.bandwidth() : 12;
    const candleWidth = Math.max(Math.min(bandwidth * 0.55, 14), 6);

    return (
      <g>
        {points.map((candle) => {
          const centerX = xScale(candle.date);
          const openY = yScale(candle.open);
          const closeY = yScale(candle.close);
          const highY = yScale(candle.high);
          const lowY = yScale(candle.low);
          const y = Math.min(highY, lowY);
          const height = Math.max(Math.abs(lowY - highY), 1);

          return <CandleShape key={candle.date} x={centerX - candleWidth / 2} y={y} width={candleWidth} height={height} open={openY} close={closeY} high={highY} low={lowY} />;
        })}
      </g>
    );
  };

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={points} margin={{ top: 8, right: 8, bottom: 10, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="date" tick={{ fill: "#9ca3af", fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis domain={yDomain} tickFormatter={usd} tick={{ fill: "#9ca3af", fontSize: 11 }} axisLine={false} tickLine={false} width={70} />
        <Customized component={CandleLayer} />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

export function AlphaVantageWidget({ widget }: { widget: WidgetEnvelope<{ symbol: string; daily_change_pct: number; candles: AlphaCandle[]; trigger_hint: string; source: string }> }) {
  return (
    <WidgetShell title="Alpha Vantage Candles" subtitle={`${widget.data.source} · ${widget.data.symbol} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="mb-3 flex items-end justify-between">
        <div>
          <div className="text-2xl font-medium text-white">{widget.data.daily_change_pct >= 0 ? "+" : ""}{widget.data.daily_change_pct.toFixed(2)}%</div>
          <div className="text-[11px] text-gray-500">Daily change</div>
        </div>
        <div className="text-[11px] text-gray-500">OHLC / Candlestick</div>
      </div>
      <div className="h-64 rounded-lg bg-[#0f1117] p-2">
        <CandlestickSvg candles={widget.data.candles} />
      </div>
    </WidgetShell>
  );
}

export function UsaJobsWidget({ widget }: { widget: WidgetEnvelope<{ jobs: UsaJob[]; trigger_hint: string; source: string }> }) {
  return (
    <WidgetShell title="USAJOBS Compliance" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="max-h-72 overflow-auto pr-1">
        <table className="w-full text-left text-[11px]">
          <thead className="sticky top-0 bg-[#161922] text-gray-500">
            <tr>
              <th className="py-1 pr-2 font-normal">Title</th>
              <th className="py-1 pr-2 font-normal">Agency</th>
              <th className="py-1 pr-2 font-normal">Location</th>
              <th className="py-1 pr-2 font-normal">Posted</th>
            </tr>
          </thead>
          <tbody>
            {widget.data.jobs.map((job, index) => (
              <tr key={`${job.title}-${index}`} className="border-t border-white/[0.06]">
                <td className="py-2 pr-2 text-white">{job.title}</td>
                <td className="py-2 pr-2 text-gray-300">{job.agency}</td>
                <td className="py-2 pr-2 text-gray-300">{job.location}</td>
                <td className="py-2 pr-2 text-gray-300">{dateLabel(job.published)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </WidgetShell>
  );
}

export function NewsApiWidget({ widget }: { widget: WidgetEnvelope<{ articles: NewsHeadline[]; trigger_hint: string; source: string }> }) {
  return (
    <WidgetShell title="NewsAPI Business India" subtitle={`${widget.data.source} · ${widget.data.trigger_hint}`} meta={widget.meta}>
      <div className="space-y-2 overflow-hidden">
        {widget.data.articles.map((article, index) => (
          <div key={`${article.title}-${index}`} className="rounded-lg border border-white/[0.06] bg-[#1e2230] px-3 py-2">
            <div className="max-h-10 overflow-hidden text-ellipsis text-[12px] text-white leading-snug">{article.title}</div>
            <div className="mt-1 flex items-center gap-2 text-[10px] text-gray-400">
              <span>{article.source}</span>
              <span>·</span>
              <span>{dateLabel(article.published_at)}</span>
            </div>
          </div>
        ))}
      </div>
    </WidgetShell>
  );
}