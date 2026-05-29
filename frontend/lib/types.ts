export interface TriggerResult { id: string; sop_name: string; severity: "critical"|"warning"|"info"; summary: string; source: string; sla_hours: number; assignee: string; extra: Record<string,unknown>; }
export interface WidgetMeta { updated_at: string; ttl_seconds: number; age_seconds: number; is_stale: boolean; }
export interface WidgetEnvelope<T> { data: T; meta: WidgetMeta; }
export interface CryptoData { btc_price: number; btc_change_24h: number; eth_price: number; eth_change_24h: number; sol_price: number; sol_change_24h: number; }
export interface FxData { usd_inr: number; usd_inr_change_wow: number; usd_eur: number; usd_gbp: number; date: string; }
export interface MacroData { cpi_latest: number|null; cpi_prior: number|null; cpi_mom: number|null; cpi_date: string|null; unemployment: number|null; fed_funds: number|null; }
export interface AqiCity { city: string; aqi: number|null; temp_c: number|null; humidity: number|null; weather_code: number|null; }
export interface HrMember { id: string; name: string; hours_this_week: number; utilization_pct: number; }
export interface SopItem { id: string; title: string; status: "Draft"|"Review"|"Published"|"Retired"; last_reviewed: string|null; notion_url?: string; }
export interface WorldBankBar { country: string; country_name: string; year: number|null; gdp: number|null; }
export interface RedditPost { title: string; score: number; comments: number; url: string; }
export interface WhoCell { country: string; value: number; year: number|null; }
export interface RandomUserEmployee { avatar: string|null; name: string; country: string; age: number|null; gender: string; }
export interface WikipediaSeriesPoint { week: string; views: number; }
export interface RemoteOkJob { title: string; company: string; posted_at: string|null; salary_min: number|null; salary_max: number|null; salary_mid: number|null; tag_count: number; tags: string[]; }
export interface AlphaCandle { date: string; open: number; high: number; low: number; close: number; volume: number; }
export interface UsaJob { title: string; agency: string; location: string; published: string|null; url: string|null; }
export interface NewsHeadline { title: string; source: string; url: string|null; published_at: string|null; description: string|null; }
export interface ScraperStatusRow { name: string; enabled: boolean; rate_limit_seconds: number|null; last_run: string|null; last_status: string|null; sop_trigger: string|null; notes?: string|null; fallback?: string|null; }
export interface ScraperStatusResponse { generated_at: string; rows: ScraperStatusRow[]; }
export interface DashboardSnapshot {
	triggers: TriggerResult[];
	snapshot: {
		crypto: WidgetEnvelope<CryptoData>;
		fx: WidgetEnvelope<FxData>;
		macro: WidgetEnvelope<MacroData>;
		aqi: WidgetEnvelope<{ cities: AqiCity[] }>;
		hr: WidgetEnvelope<{ members: HrMember[] }>;
		sop: WidgetEnvelope<{ sops: SopItem[]; stale_sops: SopItem[] }>;
		news: WidgetEnvelope<{ hn_stories: { id: number; title: string; url: string; score: number }[]; sec_filings: { company: string; form: string; filed_at: string; url: string }[] }>;
		world_bank: WidgetEnvelope<{ bars: WorldBankBar[]; trigger_hint: string; source: string }>;
		reddit: WidgetEnvelope<{ posts: RedditPost[]; trigger_hint: string; source: string }>;
		who: WidgetEnvelope<{ cells: WhoCell[]; trigger_hint: string; source: string }>;
		random_user: WidgetEnvelope<{ employees: RandomUserEmployee[]; gender_distribution: Record<string, number>; country_distribution: Record<string, number>; trigger_hint: string; source: string }>;
		wikipedia: WidgetEnvelope<{ series: { article: string; points: WikipediaSeriesPoint[] }[]; trigger_hint: string; source: string }>;
		remoteok: WidgetEnvelope<{ jobs: RemoteOkJob[]; trigger_hint: string; source: string }>;
		alpha_vantage: WidgetEnvelope<{ symbol: string; daily_change_pct: number; candles: AlphaCandle[]; trigger_hint: string; source: string }>;
		usajobs: WidgetEnvelope<{ jobs: UsaJob[]; trigger_hint: string; source: string }>;
		newsapi: WidgetEnvelope<{ articles: NewsHeadline[]; trigger_hint: string; source: string }>;
	};
	evaluated_at: string;
}
