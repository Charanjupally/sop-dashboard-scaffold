const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
export async function fetcher<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
