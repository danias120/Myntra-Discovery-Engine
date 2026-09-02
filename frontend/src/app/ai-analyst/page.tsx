"use client";

import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { 
  Sparkles, 
  Send, 
  HelpCircle, 
  Users, 
  TrendingUp, 
  FlaskConical, 
  RotateCcw,
  Loader2
} from "lucide-react";
import { askAIAnalyst, QueryResponse } from "@/lib/api";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  isHypothesis?: boolean;
  verdict?: string;
}

export default function AIAnalystPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const chatContainerRef = useRef<HTMLDivElement>(null);
  const latestQuestionRef = useRef<HTMLDivElement>(null);

  const suggestionCards = [
    {
      title: "Why are wishlist items not converting to cart?",
      icon: HelpCircle,
      query: "Why are wishlist items not converting to cart on Myntra?",
    },
    {
      title: "Who are the target shopper segments?",
      icon: Users,
      query: "Who are the target shopper segments and what are their intent levels?",
    },
    {
      title: "Is waiting for discounts a major reason users don't buy from their wishlist?",
      icon: FlaskConical,
      query: "Is waiting for discounts a major reason users don't buy from their wishlist?",
    },
    {
      title: "List all our hypotheses with their validation status.",
      icon: TrendingUp,
      query: "List all our hypotheses with their validation status.",
    },
  ];

  // Intelligent auto-scroll: when a new question is submitted or active generation finishes,
  // ensure the latest question and its response are automatically brought into view.
  useEffect(() => {
    if (messages.length === 0) return;

    const timer = setTimeout(() => {
      if (latestQuestionRef.current) {
        latestQuestionRef.current.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }
    }, 60);

    return () => clearTimeout(timer);
  }, [messages.length, isLoading]);

  const handleSend = async (queryText: string) => {
    if (!queryText.trim() || isLoading) return;

    const userMessage: ChatMessage = { role: "user", content: queryText };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue("");
    setIsLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const response: QueryResponse = await askAIAnalyst(queryText, history);

      const qLower = queryText.toLowerCase();
      const isHypo = response.generation_metadata?.is_hypothesis_test || qLower.includes("hypothesis") || qLower.includes("hypotheses") || qLower.includes("supported") || qLower.includes("bookmark") || qLower.includes("discount");

      const finalContent = response.answer && response.answer.trim()
        ? response.answer
        : "Unable to generate an answer right now. Please try again.";

      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: finalContent,
        isHypothesis: isHypo,
        verdict: response.generation_metadata?.verdict,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      console.warn("Backend query error:", err);
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: "Unable to generate an answer right now. Please try again.",
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setInputValue("");
  };

  const lastUserIndex = messages.map((m) => m.role).lastIndexOf("user");

  return (
    <main className="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col items-center gap-6 animate-fadeIn">
      {/* Header Section */}
      <div className="text-center space-y-2 w-full max-w-2xl">
        <h1 className="font-heading text-3xl sm:text-4xl font-bold gradient-text tracking-tight">
          Ask the Discovery Engine
        </h1>
        <p className="text-sm sm:text-base text-[#B8B8B8]">
          Explore customer conversations, uncover deep qualitative insights, and test product hypotheses with our grounded AI analyst.
        </p>
      </div>

      {/* Main Chat Container */}
      <div className="w-full bento-card flex flex-col h-[650px] overflow-hidden relative shadow-2xl">
        {/* Chat History Canvas with Ref */}
        <div 
          ref={chatContainerRef}
          className="flex-grow overflow-y-auto p-6 space-y-6 flex flex-col scroll-smooth"
        >
          {/* Initial State (Suggestions with Vertically Centered Text) */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center space-y-6 my-auto">
              <div className="w-14 h-14 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-white">
                <Sparkles className="h-7 w-7 text-secondary" />
              </div>
              
              <div className="space-y-1">
                <h2 className="font-heading text-xl font-bold text-white">
                  How can I help you analyze the qualitative data today?
                </h2>
                <p className="text-xs text-[#B8B8B8]">
                  Select an inquiry below or type any custom research question or hypothesis.
                </p>
              </div>

              {/* 4 Suggestion Cards: All with Vertically Centered Text */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 w-full max-w-2xl mt-4">
                {suggestionCards.map((card, idx) => {
                  const Icon = card.icon;
                  return (
                    <button
                      key={idx}
                      onClick={() => handleSend(card.query)}
                      className="p-4 rounded-xl border border-white/10 bg-[#1F1F1F] hover:bg-[#2B2B2B] hover:border-white/30 text-left transition-all group flex items-center gap-3.5 shadow-sm min-h-[72px]"
                    >
                      <div className="p-2 rounded-lg bg-white/5 group-hover:bg-white/15 text-[#B8B8B8] group-hover:text-white transition-colors flex-shrink-0">
                        <Icon className="h-4 w-4" />
                      </div>
                      <span className="text-xs font-medium text-[#B8B8B8] group-hover:text-white leading-relaxed flex-1">
                        {card.title}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Active Conversation Messages */}
          {messages.map((msg, idx) => {
            const isLatestUser = idx === lastUserIndex;

            return (
              <div 
                key={idx} 
                ref={isLatestUser ? latestQuestionRef : undefined}
                className="space-y-3 scroll-mt-4"
              >
                {msg.role === "user" ? (
                  /* User Bubble */
                  <div className="flex justify-end">
                    <div className="bg-[#2B2B2B] border border-white/10 px-4 py-3 rounded-2xl rounded-tr-none max-w-[80%] text-sm text-white shadow-md">
                      {msg.content}
                    </div>
                  </div>
                ) : (
                  /* Assistant Bubble */
                  <div className="flex flex-col gap-2.5 animate-fadeIn">
                    {/* Assistant Header */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-white/10 border border-white/20 flex items-center justify-center text-white">
                          <Sparkles className="h-3.5 w-3.5 text-secondary" />
                        </div>
                        <span className="font-heading text-sm font-bold text-white">AI Grounded Analysis</span>
                      </div>

                      {msg.verdict && (
                        <span className="px-2.5 py-0.5 rounded bg-tertiary/20 text-tertiary border border-tertiary/30 text-xs font-bold font-mono">
                          {msg.verdict}
                        </span>
                      )}
                    </div>

                    {/* Structured Markdown Content with Tables & Lists */}
                    <div className="prose prose-invert max-w-none text-xs sm:text-sm text-gray-200 leading-relaxed bg-[#1F1F1F] p-4 rounded-xl border border-white/5 space-y-2">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                          h1: ({ children }) => <h1 className="text-base font-bold text-white mt-1 mb-1">{children}</h1>,
                          h2: ({ children }) => <h2 className="text-sm font-bold text-white mt-1 mb-1">{children}</h2>,
                          h3: ({ children }) => <h3 className="text-xs font-bold text-white mt-1 mb-1">{children}</h3>,
                          p: ({ children }) => <p className="mb-2 leading-relaxed text-gray-200">{children}</p>,
                          strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
                          ul: ({ children }) => <ul className="list-disc pl-4 space-y-1 mb-2">{children}</ul>,
                          ol: ({ children }) => <ol className="list-decimal pl-4 space-y-1 mb-2">{children}</ol>,
                          li: ({ children }) => <li className="text-gray-300">{children}</li>,
                          table: ({ children }) => (
                            <div className="overflow-x-auto my-3">
                              <table className="w-full text-left border-collapse text-xs border border-white/10 rounded-lg overflow-hidden">
                                {children}
                              </table>
                            </div>
                          ),
                          thead: ({ children }) => <thead className="bg-[#2B2B2B] text-white border-b border-white/10 font-semibold">{children}</thead>,
                          tbody: ({ children }) => <tbody className="divide-y divide-white/5">{children}</tbody>,
                          tr: ({ children }) => <tr className="hover:bg-white/5 transition-colors">{children}</tr>,
                          th: ({ children }) => <th className="py-2.5 px-3 font-semibold text-white">{children}</th>,
                          td: ({ children }) => <td className="py-2.5 px-3 text-gray-200">{children}</td>,
                        }}
                      >
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Loading Indicator */}
          {isLoading && (
            <div className="flex items-center gap-3 p-4 rounded-xl bg-[#1F1F1F] border border-white/5 animate-pulse">
              <Loader2 className="h-5 w-5 text-white animate-spin" />
              <span className="text-xs text-[#B8B8B8]">
                Synthesizing grounded research evidence across 2,065 customer records...
              </span>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-white/10 bg-[#1F1F1F]/90 backdrop-blur-md">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend(inputValue);
            }}
            className="relative flex items-center"
          >
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question or test a hypothesis (e.g. 'List all our hypotheses with their validation status')..."
              className="w-full bg-[#2B2B2B] border border-white/10 rounded-full py-3 pl-5 pr-20 text-xs sm:text-sm text-white placeholder:text-[#B8B8B8] focus:outline-none focus:border-white focus:ring-1 focus:ring-white/30 transition-all shadow-inner"
            />
            
            <div className="absolute right-2 flex items-center gap-1.5">
              {messages.length > 0 && (
                <button
                  type="button"
                  onClick={handleReset}
                  title="Reset conversation"
                  className="p-1.5 rounded-full hover:bg-white/10 text-[#B8B8B8] hover:text-white transition-colors"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              )}
              <button
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                className="p-2 rounded-full bg-white text-black disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-200 transition-colors shadow-md"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </main>
  );
}
