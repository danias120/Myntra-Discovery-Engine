"use client";

import { useEffect } from "react";
import { ExternalLink, X, Quote, ShieldCheck } from "lucide-react";

interface EvidenceModalProps {
  isOpen: boolean;
  onClose: () => void;
  evidence: {
    quote?: string;
    text?: string;
    chunk_id?: string;
    platform?: string;
    theme?: string;
    url?: string | null;
    is_internal?: boolean;
    source_label?: string;
    sentiment?: string;
  } | null;
}

export default function EvidenceModal({ isOpen, onClose, evidence }: EvidenceModalProps) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "auto";
    };
  }, [isOpen, onClose]);

  if (!isOpen || !evidence) return null;

  const quoteText = evidence.quote || evidence.text || "No quote text available.";
  const platform = evidence.platform || "Reddit";
  const isInternal =
    evidence.is_internal ||
    platform.toLowerCase().includes("interview") ||
    platform.toLowerCase().includes("survey") ||
    !evidence.url;

  const url = evidence.url;
  const isAppStore = platform.toLowerCase().includes("app") || platform.toLowerCase().includes("play");

  return (
    <div 
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 animate-fadeIn"
    >
      <div className="relative w-full max-w-xl rounded-xl border border-white/10 bg-[#242424] p-6 shadow-2xl">
        {/* Close Icon Button */}
        <button
          onClick={onClose}
          aria-label="Close"
          className="absolute right-4 top-4 rounded-lg p-1.5 text-[#B8B8B8] hover:bg-white/10 hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/20 text-primary border border-primary/30">
            <Quote className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-heading text-lg font-bold text-white">Verified Customer Evidence</h3>
          </div>
        </div>

        {/* Content */}
        <div className="rounded-lg border border-white/5 bg-[#1F1F1F] p-4 mb-5">
          <p className="text-sm italic leading-relaxed text-gray-200">
            &ldquo;{quoteText}&rdquo;
          </p>
        </div>

        {/* Metadata Chips: Source Platform + Theme Tag */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="rounded-lg border border-white/5 bg-[#2B2B2B] p-2.5">
            <span className="block text-[10px] uppercase tracking-wider text-[#B8B8B8] mb-1">Source Platform</span>
            <span className="text-xs font-semibold text-white">{platform}</span>
          </div>
          <div className="rounded-lg border border-white/5 bg-[#2B2B2B] p-2.5">
            <span className="block text-[10px] uppercase tracking-wider text-[#B8B8B8] mb-1">Theme Tag</span>
            <span className="text-xs font-semibold text-secondary truncate block">
              {evidence.theme || "Wishlist Friction"}
            </span>
          </div>
        </div>

        {/* Action / Source Info Footer */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-white/10 pt-4">
          {isInternal ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10 text-xs text-[#B8B8B8] w-full sm:w-auto">
              <ShieldCheck className="h-4 w-4 text-emerald-400 flex-shrink-0" />
              <span>Primary Research Asset (De-identified Participant)</span>
            </div>
          ) : isAppStore ? (
            <span className="text-[11px] text-[#888888] italic">
              App Store web pages open the catalog overview
            </span>
          ) : (
            <div />
          )}

          {!isInternal && url && (
            <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
              <a
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="rounded-lg bg-white px-4 py-2 text-xs font-semibold text-black hover:bg-gray-200 transition-colors flex items-center gap-1.5 shadow"
              >
                <span>{evidence.source_label || "Open Verified Source"}</span>
                <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
