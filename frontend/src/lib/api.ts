/**
 * API Client for Myntra Discovery Engine FastAPI Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Theme {
  theme_id: string;
  name: string;
  theme_name?: string;
  description: string;
  comment_count?: number;
  comment_share_pct?: number;
  comment_summary?: string;
  opportunity_score?: number;
  frequency_score?: number;
  platform_spread_score?: number;
  purchase_delay_score?: number;
  evidence_count?: number;
  platforms?: string[];
  affected_shopping_stages?: string[];
  purchase_delay_reasoning?: string;
  sentiment_distribution?: {
    positive: number;
    negative: number;
    neutral: number;
    mixed?: number;
  };
  sub_themes?: {
    sub_theme_id: string;
    name: string;
    description: string;
    category: string;
    frequency_count: number;
    sentiment_distribution: Record<string, number>;
    representative_quotes: {
      quote: string;
      chunk_id: string;
      platform: string;
    }[];
  }[];
}

export interface ResearchQuestion {
  question_id: string;
  question_title?: string;
  question_text: string;
  focus_area?: string;
  synthesized_answer: string;
  triangulation_confidence: number;
  primary_themes_involved: string[];
  supporting_quotes: {
    quote: string;
    chunk_id: string;
    platform: string;
  }[];
}

export interface QueryResponse {
  query: string;
  answer: string;
  relevant_signals_count?: number;
  is_insufficient_evidence?: boolean;
  citations: {
    citation_id: number;
    chunk_id: string;
    source_platform: string;
    source_url?: string;
    relevance_score?: number;
    verbatim_quote?: string;
    text_preview?: string;
  }[];
  generation_metadata: {
    retrieved_count: number;
    model_name: string;
    is_hypothesis_test?: boolean;
    verdict?: string;
    execution_time_sec?: number;
  };
}

export interface OverviewStats {
  collected_records: number;
  usable_clean_records: number;
  usable_percentage: number;
  source_count: number;
  sources: string[];
  median_time_to_purchase_days: number;
  median_time_to_purchase_label: string;
  sentiment_breakdown: {
    positive_pct: number;
    neutral_pct: number;
    negative_pct: number;
  };
  source_breakdown_list?: {
    id: string;
    name: string;
    count: number;
    percentage: number;
  }[];
  conversion_drivers?: {
    name: string;
    impact?: string;
    signals?: number;
  }[];
  conversion_detractors?: {
    name: string;
    impact?: string;
    signals?: number;
  }[];
  actionable_insights?: {
    theme_id: string;
    name: string;
    opportunity_score: number;
    comment_count: number;
    comment_share_pct: number;
    rank: number;
  }[];
  high_intent_signals: {
    waiting_for_sale: number;
    sizing_questions: number;
    comparing_alternatives: number;
    upcoming_event: number;
    social_validation: number;
  };
}

export interface ReviewItem {
  id: string;
  source_platform: string;
  source_display: string;
  source_url: string;
  date: string;
  text: string;
  theme: string;
  purchase_intent: "High" | "Medium" | "Low";
  sentiment: "Positive" | "Negative" | "Neutral" | "Mixed";
  word_count: number;
}

export interface ReviewsResponse {
  total: number;
  page: number;
  limit: number;
  total_pages: number;
  source_filter: string;
  records: ReviewItem[];
}

export interface ReviewsIntelligence {
  source: string;
  source_display: string;
  total_records: number;
  summary_title: string;
  ai_synthesis: string;
  what_users_say_text: string;
  top_positive_keyword: string;
  top_negative_keyword: string;
  overall_purchase_intent_pct: number;
  recurring_topics: {
    topic: string;
    mentions: string;
    count: number;
    width: string;
  }[];
  source_breakdown: {
    source: string;
    count: number;
    pct: number;
    width: string;
  }[];
  show_source_breakdown: boolean;
}

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback data:", err);
    return null;
  }
}

export async function fetchOverviewStats(): Promise<OverviewStats | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/overview/stats`);
    if (!res.ok) throw new Error("Failed to fetch overview stats");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback stats:", err);
    return null;
  }
}

export async function fetchThemes(): Promise<{ primary_themes: Theme[] } | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/themes`);
    if (!res.ok) throw new Error("Failed to fetch themes");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback themes:", err);
    return null;
  }
}

export async function fetchResearchQuestions(): Promise<{ research_questions: ResearchQuestion[] } | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/research-questions`);
    if (!res.ok) throw new Error("Failed to fetch research questions");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback research questions:", err);
    return null;
  }
}

export async function fetchReviews(params: {
  source?: string;
  search?: string;
  theme?: string;
  sort?: string;
  sentiment?: string;
  page?: number;
  limit?: number;
}): Promise<ReviewsResponse | null> {
  try {
    const q = new URLSearchParams();
    if (params.source) q.set("source", params.source);
    if (params.search) q.set("search", params.search);
    if (params.theme) q.set("theme", params.theme);
    if (params.sort) q.set("sort", params.sort);
    if (params.sentiment) q.set("sentiment", params.sentiment);
    if (params.page) q.set("page", params.page.toString());
    if (params.limit) q.set("limit", params.limit.toString());

    const res = await fetch(`${API_BASE_URL}/api/reviews?${q.toString()}`);
    if (!res.ok) throw new Error("Failed to fetch reviews");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback reviews:", err);
    return null;
  }
}

export async function fetchReviewsIntelligence(source: string = "all"): Promise<ReviewsIntelligence | null> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/reviews/intelligence?source=${encodeURIComponent(source)}`);
    if (!res.ok) throw new Error("Failed to fetch reviews intelligence");
    return await res.json();
  } catch (err) {
    console.warn("Backend offline, using fallback intelligence:", err);
    return null;
  }
}

export async function askAIAnalyst(
  query: string,
  conversationHistory: { role: string; content: string }[] = [],
  filterPlatform?: string
): Promise<QueryResponse> {
  const payload: any = {
    query,
    top_k: 8,
    stream: false,
    conversation_history: conversationHistory,
  };
  if (filterPlatform && filterPlatform !== "All Sources") {
    payload.filter_platform = filterPlatform.toLowerCase();
  }

  const res = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    throw new Error(`API Query Error: ${res.statusText}`);
  }

  return await res.json();
}
