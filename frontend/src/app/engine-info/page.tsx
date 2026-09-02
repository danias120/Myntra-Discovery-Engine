"use client";

import { 
  CloudDownload, 
  ShieldCheck, 
  Copy, 
  Filter, 
  Smile, 
  Tags, 
  Bot, 
  Layers, 
  Database, 
  Info,
  CheckCircle2,
  Cpu,
  Workflow
} from "lucide-react";

export default function EngineInfoPage() {
  const pipelineSteps = [
    { label: "Collection", stat: "100%", icon: CloudDownload, color: "text-blue-400" },
    { label: "Cleaning", stat: "92.8%", icon: Filter, color: "text-orange-400" },
    { label: "PII Strip", stat: "100%", icon: ShieldCheck, color: "text-red-400" },
    { label: "Deduplication", stat: "77.8%", icon: Copy, color: "text-purple-400" },
    { label: "Relevance", stat: "37.3%", icon: Filter, color: "text-cyan-400" },
    { label: "Sentiment", stat: "Annotated", icon: Smile, color: "text-emerald-400" },
    { label: "Themes", stat: "10 Curated", icon: Tags, color: "text-amber-400" },
    { label: "ChromaDB", stat: "Indexed", icon: Database, color: "text-primary" },
  ];

  const coreCapabilities = [
    {
      title: "Sentiment Intelligence",
      description: "Fine-grained emotion analysis at the aspect level (sizing, fabric, pricing, delivery).",
      icon: Smile,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/20",
    },
    {
      title: "Theme Detection & Hierarchy",
      description: "Automated 2-pass clustering into 10 Curated Primary Themes and 30 Sub-Themes.",
      icon: Tags,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/20",
    },
    {
      title: "Purchase Intent Quantification",
      description: "0–100 Opportunity scoring calibrating frequency, platform spread, and purchase delay.",
      icon: Layers,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      border: "border-blue-500/20",
    },
    {
      title: "Behavioral Shopper Segments",
      description: "Classifies wishlisters across 6 archetypes (Bargain Hunter, Scholar, Determined, etc.).",
      icon: Layers,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
      border: "border-orange-500/20",
    },
    {
      title: "Hypothesis Testing Engine",
      description: "Structured evaluation of product assumptions with Verdict, Evidence, and Strategic Roadmap.",
      icon: Cpu,
      color: "text-primary",
      bg: "bg-primary/10",
      border: "border-primary/20",
    },
    {
      title: "Grounded AI Analyst",
      description: "Dense BGE vector retrieval + Cross-Encoder reranking with strict citation grounding.",
      icon: Bot,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      border: "border-cyan-500/20",
    },
  ];

  // Exact 8 Ingestion Source Platforms from 2,065-record corpus
  const ingestionSources = [
    { name: "Reddit", count: "982 (47.6%)", badge: "R", badgeColor: "text-[#FF4500]", desc: "r/IndianFashionAddicts, r/TwoXIndia, r/delhi community discourse." },
    { name: "Quora", count: "486 (23.5%)", badge: "Q", badgeColor: "text-[#B92B27]", desc: "Consumer inquiries & cross-app comparison threads." },
    { name: "Apple App Store", count: "185 (9.0%)", badge: "A", badgeColor: "text-purple-400", desc: "iOS feature feedback, 1,000-item cap & app review logs." },
    { name: "User Surveys", count: "174 (8.4%)", badge: "S", badgeColor: "text-blue-400", desc: "Structured consumer responses on holding duration & price triggers." },
    { name: "Google Play Store", count: "133 (6.4%)", badge: "P", badgeColor: "text-emerald-400", desc: "Android UX feedback, return policy & customer photo logs." },
    { name: "1-on-1 Interviews", count: "96 (4.6%)", badge: "I", badgeColor: "text-cyan-400", desc: "Qualitative transcripts on mental models & cooling-off buffers." },
    { name: "Catalog Feedback", count: "7 (0.3%)", badge: "M", badgeColor: "text-pink-400", desc: "Customer review entries on product sizing & fabric quality." },
    { name: "YouTube Hauls", count: "2 (0.1%)", badge: "Y", badgeColor: "text-red-500", desc: "Creator try-on video reviews evaluating daylight drape." },
  ];

  return (
    <main className="w-full max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-8 py-10 flex flex-col gap-10 animate-fadeIn">
      {/* Header Section */}
      <div className="flex flex-col items-center text-center">
        <div className="inline-flex items-center gap-2 bg-[#2B2B2B] px-4 py-1.5 rounded-full mb-4 border border-white/10">
          <Info className="h-4 w-4 text-white" />
          <span className="text-xs font-semibold text-white">About the Discovery Platform</span>
        </div>
        <h1 className="font-heading text-3xl sm:text-5xl font-bold gradient-text mb-4 tracking-tight">
          Myntra Discovery Engine
        </h1>
        <p className="text-base text-[#B8B8B8] max-w-3xl leading-relaxed">
          An AI-powered qualitative customer intelligence system that transforms thousands of fragmented customer conversations into structured, evidence-backed insights for product and growth teams.
        </p>
      </div>

      {/* Quote Banner */}
      <div className="relative rounded-2xl bg-[#242424] p-6 sm:p-8 border border-white/10 text-center overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-gradient-to-r from-primary to-secondary" />
        <p className="font-heading text-base sm:text-xl font-bold text-white relative z-10 leading-snug">
          &ldquo;From customer voices <span className="text-[#B8B8B8] mx-1">→</span> structured evidence <span className="text-[#B8B8B8] mx-1">→</span> behavioral understanding <span className="text-[#B8B8B8] mx-1">→</span> actionable insight.&rdquo;
        </p>
      </div>

      {/* Funnel Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: "Total Records Ingested", value: "5,538", sub: "100% Raw Discourse" },
          { label: "Cleaned & PII Stripped", value: "5,142", sub: "92.8% Retained" },
          { label: "Deduplicated", value: "4,310", sub: "77.8% Retained" },
          { label: "Relevant Clean Chunks", value: "2,065", sub: "37.3% Curated Corpus" },
          { label: "Spam / Bots Filtered", value: "3,473", sub: "62.7% Excluded Noise" },
        ].map((stat, sIdx) => (
          <div key={sIdx} className="bento-card p-4 flex flex-col justify-between">
            <span className="text-[11px] font-semibold text-[#B8B8B8] uppercase tracking-wider mb-1">{stat.label}</span>
            <span className="font-heading text-2xl font-bold text-white mb-1">{stat.value}</span>
            <span className="text-[11px] text-tertiary font-medium">{stat.sub}</span>
          </div>
        ))}
      </div>

      {/* Visual Connected Processing Pipeline */}
      <section className="bento-card p-6 sm:p-8 flex flex-col gap-6">
        <div className="flex items-center gap-2">
          <Workflow className="h-5 w-5 text-secondary" />
          <h2 className="font-heading text-lg font-bold text-white">Data Processing Pipeline</h2>
        </div>

        <div className="relative flex flex-wrap sm:flex-nowrap justify-between items-center gap-4 py-4 px-2">
          {/* Connecting line on desktop */}
          <div className="hidden sm:block absolute top-1/2 left-8 right-8 h-[2px] -translate-y-1/2 bg-gradient-to-r from-primary to-secondary opacity-30 z-0" />

          {pipelineSteps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div key={idx} className="relative z-10 flex flex-col items-center gap-2 flex-1 min-w-[80px]">
                <div className="w-12 h-12 rounded-xl bg-[#2B2B2B] border border-white/15 flex items-center justify-center shadow-lg group hover:border-primary transition-colors">
                  <Icon className={`h-5 w-5 ${step.color}`} />
                </div>
                <div className="text-center">
                  <div className="text-xs font-bold text-white">{step.label}</div>
                  <div className="text-[11px] text-[#B8B8B8] font-mono">{step.stat}</div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Two Column Grid: Core Capabilities (2 cols x 3 rows) & Ingestion Sources (All 8) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Core Capabilities: 2 columns x 3 rows (7 cols) */}
        <section className="col-span-1 lg:col-span-7 bento-card p-6 flex flex-col gap-6">
          <div className="flex items-center gap-2">
            <Cpu className="h-5 w-5 text-primary" />
            <h2 className="font-heading text-lg font-bold text-white">Core Qualitative Capabilities</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {coreCapabilities.map((cap, idx) => {
              const Icon = cap.icon;
              return (
                <div
                  key={idx}
                  className="rounded-xl border border-white/10 bg-[#1F1F1F] p-5 hover:bg-[#2B2B2B] hover:border-primary/40 transition-all flex flex-col gap-3 group"
                >
                  <div className={`w-10 h-10 rounded-lg ${cap.bg} border ${cap.border} flex items-center justify-center ${cap.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <h3 className="font-heading text-sm font-bold text-white mb-1">{cap.title}</h3>
                    <p className="text-xs text-[#B8B8B8] leading-relaxed">{cap.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Ingestion Sources: All 8 Ingestion Platforms (5 cols) */}
        <section className="col-span-1 lg:col-span-5 bento-card p-6 flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-white/10 pb-3">
            <div className="flex items-center gap-2">
              <Database className="h-5 w-5 text-secondary" />
              <h2 className="font-heading text-lg font-bold text-white">8 Ingestion Sources</h2>
            </div>
            <span className="text-xs font-mono text-[#B8B8B8]">2,065 Clean Chunks</span>
          </div>

          <div className="space-y-2.5 overflow-y-auto max-h-[460px] pr-1">
            {ingestionSources.map((src, idx) => (
              <div key={idx} className="rounded-xl border border-white/10 bg-[#1F1F1F] p-3 flex items-start justify-between gap-3 hover:bg-[#2B2B2B] transition-colors">
                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-[#2B2B2B] border border-white/10 flex items-center justify-center font-heading font-bold text-xs flex-shrink-0 mt-0.5">
                    <span className={src.badgeColor}>{src.badge}</span>
                  </div>
                  <div>
                    <h3 className="font-heading text-xs font-bold text-white">{src.name}</h3>
                    <p className="text-[10px] text-[#B8B8B8] leading-tight mt-0.5">{src.desc}</p>
                  </div>
                </div>
                <span className="text-[10px] font-mono text-[#B8B8B8] whitespace-nowrap bg-white/5 px-2 py-0.5 rounded border border-white/5">
                  {src.count}
                </span>
              </div>
            ))}
          </div>
        </section>

      </div>

      {/* Detailed Architecture & Operational Methodology (Factually Verified) */}
      <section className="bento-card p-6 sm:p-8 flex flex-col gap-6">
        <div className="flex items-center gap-2 border-b border-white/10 pb-4">
          <Layers className="h-5 w-5 text-tertiary" />
          <h2 className="font-heading text-xl font-bold text-white">Engine Architecture &amp; Methodology</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-xs sm:text-sm text-gray-300 leading-relaxed">
          {/* Column 1 */}
          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" /> 1. Multi-Channel Data Ingestion
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                Ingests 5,538 raw customer discussions across 8 source platforms: Reddit (r/IndianFashionAddicts, r/TwoXIndia, r/delhi), Quora Q&amp;A threads, App Store and Google Play feedback, structured user surveys, 1-on-1 interviews, catalog feedback, and YouTube try-on hauls.
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" /> 2. PII Sanitization &amp; Data Quality Guardrails
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                Regex and heuristic pipelines sanitize customer handles, phone numbers, email addresses, and order tracking numbers. MinHash deduplication and spam scrubbers eliminate bot promotions to yield 2,065 clean qualitative evidence chunks (78,519 words).
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-primary" /> 3. Qualitative Taxonomy &amp; Thematic Engine
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                A 2-pass qualitative engine clusters micro-friction points into 10 Curated Primary Themes and 30 Sub-Themes with verified verbatim quotes. Triangulates findings across platforms with a 0.90 mean confidence rating.
              </p>
            </div>
          </div>

          {/* Column 2 */}
          <div className="space-y-6">
            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-secondary" /> 4. Opportunity Quantification Algorithm
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                Scores each theme on a 0–100 scale using the calibrated weighted formula (0.40 × Frequency + 0.30 × Spread + 0.30 × Purchase Delay) and ranks opportunities primarily by customer comment volume (e.g. Price Drop: 928 comments / 44.9%).
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-secondary" /> 5. Dense BGE Embeddings &amp; Cross-Encoder Reranker
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                Vectorizes the entire clean corpus into ChromaDB using <code className="text-secondary">BAAI/bge-small-en-v1.5</code> (384-dimensional dense vectors). Retrieval executes a two-stage pipeline: ChromaDB Top 20 candidate fetch → <code className="text-secondary">ms-marco-MiniLM-L-6-v2</code> cross-attention reranking.
              </p>
            </div>

            <div className="space-y-2">
              <h3 className="font-heading text-sm font-bold text-white flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-secondary" /> 6. Grounded Qualitative Synthesis Guardrails
              </h3>
              <p className="text-[#B8B8B8] leading-relaxed">
                Uses citation validation and grounded-generation guardrails to reduce unsupported claims, preserve source traceability, and link findings back to original evidence.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
