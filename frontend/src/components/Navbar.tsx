"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import Image from "next/image";

export default function Navbar() {
  const pathname = usePathname();
  const isEngineInfo = pathname === "/engine-info";

  const navLinks = [
    { name: "Overview", href: "/" },
    { name: "Reviews", href: "/reviews" },
    { name: "AI Analyst", href: "/ai-analyst" },
    { name: "FAQs", href: "/faqs" },
    { name: "Engine Info", href: "/engine-info" },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/10 bg-[#24181F]/95 backdrop-blur-md">
      <div className="w-full max-w-[1440px] mx-auto flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* LEFT: Fixed-width branding slot so navigation on right never moves */}
        <div className="flex items-center min-w-[280px] sm:min-w-[320px] flex-shrink-0">
          <Link href="/" className="flex items-center gap-3 group flex-shrink-0">
            <div className="relative h-10 w-auto flex-shrink-0 transition-transform group-hover:scale-105 flex items-center">
              <Image
                src="/myntra-logo.png"
                alt="Myntra Logo"
                width={100}
                height={38}
                className="h-10 w-auto object-contain"
                priority
              />
            </div>
            {/* Show title on all pages EXCEPT Engine Info */}
            {!isEngineInfo && (
              <span className="font-heading text-lg sm:text-xl font-bold tracking-tight bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent whitespace-nowrap">
                Myntra Discovery Engine
              </span>
            )}
          </Link>
        </div>

        {/* RIGHT: Fixed Position Navigation Menu anchored identically across all 5 pages */}
        <nav className="flex items-center gap-6 md:gap-8 h-full flex-shrink-0">
          {navLinks.map((link) => {
            const isActive =
              pathname === link.href ||
              (link.href !== "/" && pathname.startsWith(link.href));

            return (
              <Link
                key={link.name}
                href={link.href}
                className={`relative flex h-full items-center text-sm font-medium transition-colors duration-150 ${
                  isActive
                    ? "text-white font-semibold"
                    : "text-[#B8B8B8] hover:text-white"
                }`}
              >
                {link.name}
                {isActive && (
                  <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-white rounded-full" />
                )}
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
