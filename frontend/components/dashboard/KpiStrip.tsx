"use client";
import type { CryptoData, FxData, MacroData, WidgetEnvelope, WidgetMeta } from "@/lib/types";
import { WidgetShell } from "@/components/dashboard/WidgetShell";

interface Props {
  crypto: WidgetEnvelope<CryptoData>;
  fx: WidgetEnvelope<FxData>;
  macro: WidgetEnvelope<MacroData>;
}

function KpiCard({
  label, value, sub, change, triggered, triggerLabel, meta,
}: {
  label: string; value: string; sub: string;
  change?: { val: number; suffix?: string };
  triggered?: boolean; triggerLabel?: string;
  meta: WidgetMeta;
}) {
  const up = change && change.val > 0;
  const down = change && change.val < 0;
  return (
    <WidgetShell title={label} subtitle={sub} meta={meta}>
      <div className="text-xl font-medium text-white">{value}</div>
      {change !== undefined && (
        <div className={`mt-1 flex items-center gap-1 text-[11px] ${up ? "text-emerald-400" : down ? "text-red-400" : "text-gray-500"}`}>
          {up ? "▲" : down ? "▼" : "—"} {Math.abs(change.val).toFixed(2)}{change.suffix ?? "%"}
        </div>
      )}
      {triggered && triggerLabel && (
        <div className="mt-2 inline-block rounded bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-400">
          ⚠ {triggerLabel}
        </div>
      )}
    </WidgetShell>
  );
}

export function KpiStrip({ crypto, fx, macro }: Props) {
  return (
    <div className="grid grid-cols-5 gap-3">
      <KpiCard
        label="BTC / USD"
        value={`$${crypto.data.btc_price.toLocaleString()}`}
        sub="Bitcoin · CoinGecko"
        meta={crypto.meta}
        change={{ val: crypto.data.btc_change_24h }}
        triggered={crypto.data.btc_change_24h <= -5}
        triggerLabel="Treasury Review SOP"
      />
      <KpiCard
        label="ETH / USD"
        value={`$${crypto.data.eth_price.toLocaleString()}`}
        sub="Ethereum · CoinGecko"
        meta={crypto.meta}
        change={{ val: crypto.data.eth_change_24h }}
        triggered={crypto.data.eth_change_24h <= -8}
        triggerLabel="Treasury Review SOP"
      />
      <KpiCard
        label="USD → INR"
        value={`₹${fx.data.usd_inr.toFixed(2)}`}
        sub="Frankfurter FX"
        meta={fx.meta}
        change={{ val: fx.data.usd_inr_change_wow }}
        triggered={Math.abs(fx.data.usd_inr_change_wow) >= 2}
        triggerLabel="Invoicing SOP"
      />
      <KpiCard
        label="CPI MoM"
        value={macro.data.cpi_mom != null ? `+${macro.data.cpi_mom.toFixed(2)}%` : "—"}
        sub={`FRED · ${macro.data.cpi_date ?? ""}`}
        meta={macro.meta}
        change={macro.data.cpi_mom != null ? { val: macro.data.cpi_mom, suffix: "%" } : undefined}
        triggered={(macro.data.cpi_mom ?? 0) >= 0.3}
        triggerLabel="Pricing Review SOP"
      />
      <KpiCard
        label="Unemployment"
        value={macro.data.unemployment != null ? `${macro.data.unemployment}%` : "—"}
        sub="FRED · UNRATE"
        meta={macro.meta}
        change={macro.data.unemployment != null ? { val: 0 } : undefined}
      />
    </div>
  );
}
