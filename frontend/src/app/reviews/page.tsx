"use client";

import { useState, useEffect, useCallback } from "react";
import { 
  Sparkles, 
  MessageSquare, 
  Search, 
  Download, 
  ExternalLink, 
  ChevronLeft, 
  ChevronRight,
  TrendingUp,
  Loader2,
  Filter,
  ArrowUpDown,
  FileText
} from "lucide-react";
import { fetchReviews, fetchReviewsIntelligence, ReviewItem, ReviewsIntelligence } from "@/lib/api";
import EvidenceModal from "@/components/EvidenceModal";

export default function ReviewsPage() {
  const [selectedSource, setSelectedSource] = useState<string>("All Sources");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedTheme, setSelectedTheme] = useState<string>("All");
  const [selectedSentiment, setSelectedSentiment] = useState<string>("All");
  const [selectedSort, setSelectedSort] = useState<string>("most_recent");
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  const [reviewsData, setReviewsData] = useState<{
    records: ReviewItem[];
    total: number;
    total_pages: number;
  }>({
    records: [],
    total: 0,
    total_pages: 1,
  });

  const [intelligence, setIntelligence] = useState<ReviewsIntelligence | null>(null);
  const [modalEvidence, setModalEvidence] = useState<any | null>(null);
  const [isModalOpen, setIsModalOpen] = useState<boolean>(false);

  const sourcesList = ["All Sources", "Reddit", "Quora", "App Store", "Google Play", "Other"];
  const themeList = [
    "All",
    "Price Drop Sensitivity & EORS Triggers",
    "Cross-Brand Sizing Uncertainty & Fit Anxiety",
    "Social Validation & Unedited Photo Proof",
    "Competitor Price Arbitrage & Cross-App Switching",
    "Pre-Cart Staging & Emotional Impulse Buffer",
    "Multi-Product Comparison Friction & Choice Overload",
    "Event Planning & Stockout Vulnerability",
    "Wishlist Clutter & 1,000-Item Cap Paralysis",
    "Desire Decay & Extended Holding Stagnation",
    "Social Reassurance Delays & Peer Polling"
  ];
  const itemsPerPage = 10; // Exactly 10 records per page

  const loadData = useCallback(async () => {
    setIsLoading(true);
    const [revs, intel] = await Promise.all([
      fetchReviews({
        source: selectedSource,
        search: searchQuery,
        theme: selectedTheme !== "All" ? selectedTheme : undefined,
        sentiment: selectedSentiment !== "All" ? selectedSentiment : undefined,
        sort: selectedSort,
        page: currentPage,
        limit: itemsPerPage,
      }),
      fetchReviewsIntelligence(selectedSource),
    ]);

    if (revs) {
      setReviewsData({
        records: revs.records,
        total: revs.total,
        total_pages: revs.total_pages,
      });
    }

    if (intel) {
      setIntelligence(intel);
    }
    setIsLoading(false);
  }, [selectedSource, searchQuery, selectedTheme, selectedSentiment, selectedSort, currentPage]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleSourceChange = (src: string) => {
    setSelectedSource(src);
    setCurrentPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  const handleExportCSV = () => {
    if (!reviewsData.records.length) return;
    const headers = ["ID", "Source", "Date", "Cleaned Text", "Theme", "Purchase Intent", "Sentiment", "URL"];
    const rows = reviewsData.records.map((r) => [
      r.id,
      r.source_display,
      r.date,
      `"${r.text.replace(/"/g, '""')}"`,
      r.theme,
      r.purchase_intent,
      r.sentiment,
      r.source_url,
    ]);
    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `myntra_corpus_${selectedSource.toLowerCase().replace(" ", "_")}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getSourceBadgeColor = (source: string) => {
    const s = source.toLowerCase();
    if (s.includes("reddit")) return "text-orange-400 bg-orange-500/10 border-orange-500/30";
    if (s.includes("app store") || s.includes("appstore")) return "text-purple-400 bg-purple-500/10 border-purple-500/30";
    if (s.includes("google") || s.includes("play")) return "text-emerald-400 bg-emerald-500/10 border-emerald-500/30";
    if (s.includes("quora")) return "text-red-400 bg-red-500/10 border-red-500/30";
    return "text-blue-400 bg-blue-500/10 border-blue-500/30";
  };

  const getSentimentBadge = (sentiment: string) => {
    switch (sentiment) {
      case "Positive":
        return <span className="text-xs font-semibold text-tertiary">Positive</span>;
      case "Negative":
        return <span className="text-xs font-semibold text-error-red">Negative</span>;
      case "Mixed":
        return <span className="text-xs font-semibold text-yellow-400">Mixed</span>;
      default:
        return <span className="text-xs font-semibold text-[#B8B8B8]">Neutral</span>;
    }
  };

  // Purchase Intent color coding: High = Green, Medium = Yellow, Low = Red
  const getIntentBadge = (intent: string) => {
    if (intent === "High") {
      return (
        <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-tertiary/15 text-tertiary border border-tertiary/30">
          High
        </span>
      );
    }
    if (intent === "Medium") {
      return (
        <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-yellow-500/15 text-yellow-400 border border-yellow-500/30">
          Medium
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-red-500/15 text-red-400 border border-red-500/30">
        Low
      </span>
    );
  };

  return (
    <main className="w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col gap-8 animate-fadeIn">
      {/* Page Header & Source Filters (Single Horizontal Line for Pills) */}
      <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-4">
        <div className="max-w-xl">
          <h1 className="font-heading text-3xl sm:text-4xl font-bold text-white tracking-tight">
            Reviews Intelligence
          </h1>
          <p className="text-sm text-[#B8B8B8] leading-relaxed mt-1">
            Deep-dive qualitative research analyzing why wishlisted items do or do not convert to purchases across 2,065 customer records.
          </p>
        </div>

        {/* Source Filter Pills: Strictly Single Horizontal Line */}
        <div className="flex items-center flex-nowrap gap-1.5 sm:gap-2 bg-[#1F1F1F] p-1.5 rounded-full border border-white/10 overflow-x-auto max-w-full flex-shrink-0">
          {sourcesList.map((src) => (
            <button
              key={src}
              onClick={() => handleSourceChange(src)}
              className={`px-3.5 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all flex-shrink-0 ${
                selectedSource === src
                  ? "bg-white text-black font-bold shadow-md"
                  : "text-[#B8B8B8] hover:text-white hover:bg-white/5"
              }`}
            >
              {src}
            </button>
          ))}
        </div>
      </div>

      {/* Bento Grid Analytics Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Card 1: AI Synthesis (Single strongest driver & single strongest blocker) */}
        <div className={`col-span-1 ${intelligence?.show_source_breakdown ? "lg:col-span-8" : "lg:col-span-8"} bento-card p-6 flex flex-col justify-between`}>
          <div>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center text-white">
                <Sparkles className="h-4 w-4 text-secondary" />
              </div>
              <h2 className="font-heading text-lg font-bold text-white">
                AI Synthesis: {intelligence?.source_display || selectedSource}
              </h2>
            </div>
            <p className="text-sm text-[#B8B8B8] leading-relaxed mb-6">
              {intelligence?.ai_synthesis || "Analyzing customer discourse..."}
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-white/5">
            <div className="bg-[#1F1F1F] p-3 rounded-lg border border-white/5">
              <span className="text-[10px] uppercase tracking-wider text-[#B8B8B8] block mb-1">Top Conversion Driver</span>
              <div className="font-bold text-xs text-white mb-1 leading-snug">{intelligence?.top_positive_keyword || '"Deep EORS Discount Triggers"'}</div>
              <div className="text-tertiary text-[11px] flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> Accelerates Checkout
              </div>
            </div>

            <div className="bg-[#1F1F1F] p-3 rounded-lg border border-white/5">
              <span className="text-[10px] uppercase tracking-wider text-[#B8B8B8] block mb-1">Top Conversion Blocker</span>
              <div className="font-bold text-xs text-white mb-1 leading-snug">{intelligence?.top_negative_keyword || '"Cross-Brand Sizing Uncertainty"'}</div>
              <div className="text-error-red text-[11px] flex items-center gap-1">
                <TrendingUp className="h-3 w-3" /> Delays Purchase
              </div>
            </div>

            <div className="bg-[#1F1F1F] p-3 rounded-lg border border-white/5">
              <span className="text-[10px] uppercase tracking-wider text-[#B8B8B8] block mb-1">Purchase Intent</span>
              <div className="font-bold text-sm text-white mb-1.5">{intelligence?.overall_purchase_intent_pct || 74}% High</div>
              <div className="w-full h-1.5 bg-[#3A3A3A] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-secondary rounded-full" 
                  style={{ width: `${intelligence?.overall_purchase_intent_pct || 74}%` }} 
                />
              </div>
            </div>
          </div>
        </div>

        {/* Card 2: Top Recurring Topics (5 topics for All Sources, 4 for individual sources) */}
        <div className="col-span-1 lg:col-span-4 bento-card p-6 flex flex-col justify-between">
          <h3 className="text-xs font-semibold text-[#B8B8B8] uppercase tracking-wider mb-4 border-b border-white/10 pb-2">
            Top Recurring Topics ({selectedSource})
          </h3>
          <div className="space-y-3.5">
            {intelligence?.recurring_topics && intelligence.recurring_topics.length > 0 ? (
              intelligence.recurring_topics.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-white font-medium truncate pr-2">{item.topic}</span>
                    <span className="text-[#B8B8B8] font-mono whitespace-nowrap text-[11px]">{item.mentions}</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#3A3A3A] rounded-full overflow-hidden">
                    <div className="h-full bg-secondary rounded-full" style={{ width: item.width }} />
                  </div>
                </div>
              ))
            ) : (
              <div className="text-xs text-[#B8B8B8] py-4">Loading topics...</div>
            )}
          </div>
        </div>

        {/* Card 3: Summary Box (Why Wishlist Saves Do Not Convert) */}
        <div className={`col-span-1 ${intelligence?.show_source_breakdown ? "lg:col-span-8" : "lg:col-span-12"} bento-card p-6 flex flex-col justify-between`}>
          <div className="flex items-center gap-3 mb-4 pb-3 border-b border-white/5">
            <div className="w-8 h-8 rounded-lg bg-white/10 border border-white/20 flex items-center justify-center text-white">
              <MessageSquare className="h-4 w-4 text-blue-400" />
            </div>
            <h2 className="font-heading text-lg font-bold text-white">
              {intelligence?.summary_title || `What ${selectedSource} users are saying?`}
            </h2>
          </div>

          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
            <p className={`text-sm text-[#B8B8B8] leading-relaxed ${intelligence?.show_source_breakdown ? "max-w-2xl" : "flex-1 max-w-4xl"}`}>
              {intelligence?.what_users_say_text}
            </p>

            <div className="bg-[#1F1F1F] p-4 rounded-xl border border-white/10 flex flex-col justify-center min-w-[180px] flex-shrink-0">
              <span className="text-[10px] text-[#B8B8B8] uppercase tracking-wider block mb-1">Filtered Records</span>
              <div className="text-2xl font-bold text-white">{intelligence?.total_records?.toLocaleString() || reviewsData.total.toLocaleString()}</div>
              <span className="text-[10px] text-tertiary">100% PII-Cleaned Signals</span>
            </div>
          </div>
        </div>

        {/* Card 4: Source Breakdown (Shown ONLY when All Sources is active) */}
        {intelligence?.show_source_breakdown && (
          <div className="col-span-1 lg:col-span-4 bento-card p-6 flex flex-col justify-between animate-fadeIn">
            <h3 className="text-xs font-semibold text-[#B8B8B8] uppercase tracking-wider mb-4 border-b border-white/10 pb-2">
              Source Breakdown (Actual Corpus)
            </h3>
            <div className="space-y-3.5">
              {intelligence.source_breakdown.slice(0, 5).map((s, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="text-white">{s.source}</span>
                    <span className="text-[#B8B8B8] font-mono text-[11px]">{s.count.toLocaleString()} ({s.pct}%)</span>
                  </div>
                  <div className="w-full h-1.5 bg-[#3A3A3A] rounded-full overflow-hidden">
                    <div className="h-full bg-secondary rounded-full" style={{ width: s.width }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>

      {/* Review Explorer Table Section (10 Records Per Page) */}
      <section className="flex flex-col gap-4">
        {/* Controls Bar */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div className="flex items-center gap-3">
            <h2 className="font-heading text-xl font-bold text-white">Review Explorer</h2>
            <span className="text-xs font-mono text-[#B8B8B8] bg-[#1F1F1F] px-2.5 py-1 rounded-full border border-white/10">
              {reviewsData.total.toLocaleString()} Records
            </span>
          </div>
          
          <div className="flex items-center flex-wrap gap-2.5 w-full md:w-auto">
            {/* Search input */}
            <div className="relative w-full sm:w-60">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#B8B8B8]" />
              <input
                type="text"
                value={searchQuery}
                onChange={handleSearchChange}
                placeholder="Search comments..."
                className="w-full bg-[#1F1F1F] border border-white/10 focus:border-white focus:ring-1 focus:ring-white/30 text-white text-xs rounded-lg pl-8 pr-3 py-2 transition-all outline-none"
              />
            </div>

            {/* Filter by Theme */}
            <div className="flex items-center gap-1.5 bg-[#1F1F1F] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-[#B8B8B8]">
              <Filter className="h-3.5 w-3.5 text-[#B8B8B8]" />
              <select
                value={selectedTheme}
                onChange={(e) => { setSelectedTheme(e.target.value); setCurrentPage(1); }}
                className="bg-transparent text-white text-xs focus:outline-none cursor-pointer max-w-[160px] truncate"
              >
                <option value="All" className="bg-[#1F1F1F]">All Themes</option>
                {themeList.slice(1).map((t) => (
                  <option key={t} value={t} className="bg-[#1F1F1F]">{t}</option>
                ))}
              </select>
            </div>

            {/* Sort Dropdown: Including Low Intent First */}
            <div className="flex items-center gap-1.5 bg-[#1F1F1F] border border-white/10 rounded-lg px-2.5 py-1.5 text-xs text-[#B8B8B8]">
              <ArrowUpDown className="h-3.5 w-3.5 text-[#B8B8B8]" />
              <select
                value={selectedSort}
                onChange={(e) => { setSelectedSort(e.target.value); setCurrentPage(1); }}
                className="bg-transparent text-white text-xs focus:outline-none cursor-pointer"
              >
                <option value="most_recent" className="bg-[#1F1F1F]">Most Recent</option>
                <option value="oldest" className="bg-[#1F1F1F]">Oldest</option>
                <option value="high_intent" className="bg-[#1F1F1F]">High Intent First</option>
                <option value="low_intent" className="bg-[#1F1F1F]">Low Intent First</option>
                <option value="detailed" className="bg-[#1F1F1F]">Most Detailed</option>
              </select>
            </div>

            {/* Export CSV Button */}
            <button
              onClick={handleExportCSV}
              className="px-3 py-2 rounded-lg bg-[#2B2B2B] hover:bg-[#333333] border border-white/10 text-xs font-medium text-white flex items-center gap-1.5 transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Export CSV</span>
            </button>
          </div>
        </div>

        {/* Data Grid Table */}
        <div className="bento-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse min-w-[900px]">
              <thead className="bg-[#1F1F1F] border-b border-white/10 text-[10px] text-[#B8B8B8] font-semibold uppercase tracking-wider">
                <tr>
                  {selectedSource === "All Sources" && (
                    <th className="py-3 px-4 w-28">Source</th>
                  )}
                  <th className="py-3 px-4 w-28">Date</th>
                  <th className="py-3 px-4">Cleaned Customer Evidence</th>
                  <th className="py-3 px-4 w-40">Theme</th>
                  <th className="py-3 px-4 w-28">Purchase Intent</th>
                  <th className="py-3 px-4 w-28">Sentiment</th>
                  <th className="py-3 px-4 w-16 text-center">URL</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-xs">
                {isLoading ? (
                  <tr>
                    <td colSpan={selectedSource === "All Sources" ? 7 : 6} className="py-12 text-center text-[#B8B8B8]">
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin text-white" />
                        <span>Loading real corpus chunks from database...</span>
                      </div>
                    </td>
                  </tr>
                ) : reviewsData.records.length > 0 ? (
                  reviewsData.records.map((rev) => (
                    <tr 
                      key={rev.id}
                      onClick={() => {
                        setModalEvidence({
                          quote: rev.text,
                          chunk_id: rev.id,
                          platform: rev.source_display,
                          theme: rev.theme,
                          url: rev.source_url,
                          is_internal: rev.is_internal,
                          source_label: rev.source_label,
                        });
                        setIsModalOpen(true);
                      }}
                      className="hover:bg-[#2B2B2B]/50 transition-colors cursor-pointer group"
                    >
                      {selectedSource === "All Sources" && (
                        <td className="py-3.5 px-4">
                          <span className={`px-2 py-0.5 rounded text-[11px] font-medium border ${getSourceBadgeColor(rev.source_platform)}`}>
                            {rev.source_display}
                          </span>
                        </td>
                      )}
                      <td className="py-3.5 px-4 text-[#B8B8B8] whitespace-nowrap">{rev.date}</td>
                      <td className="py-3.5 px-4 text-gray-200 group-hover:text-white line-clamp-2 max-w-lg">
                        {rev.text}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className="px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-[#B8B8B8] whitespace-nowrap">
                          {rev.theme}
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        {getIntentBadge(rev.purchase_intent)}
                      </td>
                      <td className="py-3.5 px-4">
                        {getSentimentBadge(rev.sentiment)}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        {rev.is_internal || !rev.source_url ? (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setModalEvidence({
                                quote: rev.text,
                                chunk_id: rev.id,
                                platform: rev.source_display,
                                theme: rev.theme,
                                url: null,
                                is_internal: true,
                                source_label: rev.source_label || "Internal Research",
                              });
                              setIsModalOpen(true);
                            }}
                            className="inline-flex items-center justify-center p-1.5 rounded hover:bg-white/10 text-[#B8B8B8] hover:text-white transition-colors"
                            title="View Internal Primary Research Transcript"
                          >
                            <FileText className="h-4 w-4" />
                          </button>
                        ) : (
                          <a
                            href={rev.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="inline-flex items-center justify-center p-1.5 rounded hover:bg-white/10 text-white hover:text-gray-300 transition-colors"
                            title={rev.source_label ? `Open ${rev.source_label}` : "Open Verified Source Link"}
                          >
                            <ExternalLink className="h-4 w-4 text-white" />
                          </a>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={selectedSource === "All Sources" ? 7 : 6} className="py-12 text-center text-[#B8B8B8]">
                      No customer feedback found matching the current search criteria in {selectedSource}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Footer: 10 Records Per Page */}
          <div className="flex items-center justify-between p-4 border-t border-white/10 bg-[#1A1A1A] text-xs text-[#B8B8B8]">
            <div>
              Showing {reviewsData.records.length > 0 ? (currentPage - 1) * itemsPerPage + 1 : 0}–{Math.min(currentPage * itemsPerPage, reviewsData.total)} of {reviewsData.total.toLocaleString()} records
            </div>
            
            <div className="flex items-center gap-1.5">
              <button
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                className="p-1.5 rounded bg-[#2B2B2B] text-white hover:bg-[#333333] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>

              {Array.from({ length: Math.min(5, reviewsData.total_pages) }).map((_, i) => {
                let pageNum = i + 1;
                if (reviewsData.total_pages > 5 && currentPage > 3) {
                  pageNum = currentPage - 2 + i;
                  if (pageNum > reviewsData.total_pages) {
                    pageNum = reviewsData.total_pages - 4 + i;
                  }
                }
                return (
                  <button
                    key={pageNum}
                    onClick={() => setCurrentPage(pageNum)}
                    className={`w-7 h-7 rounded flex items-center justify-center text-xs font-semibold transition-colors ${
                      currentPage === pageNum
                        ? "bg-white text-black font-bold shadow"
                        : "bg-[#2B2B2B] text-gray-300 hover:bg-[#383838] hover:text-white"
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}

              <button
                disabled={currentPage >= reviewsData.total_pages}
                onClick={() => setCurrentPage((p) => Math.min(reviewsData.total_pages, p + 1))}
                className="p-1.5 rounded bg-[#2B2B2B] text-white hover:bg-[#333333] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Verbatim Evidence Modal */}
      <EvidenceModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        evidence={modalEvidence}
      />
    </main>
  );
}
