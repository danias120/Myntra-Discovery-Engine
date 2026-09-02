/**
 * Curated Research Data & Shopper Segment Definitions for Myntra Discovery Engine
 */

export interface ShopperSegment {
  type: string;
  brief_description: string;
  purchase_intent: string;
  intent_level: "very_high" | "high" | "medium_high" | "low_medium";
  share_pct: number;
  estimated_users: number;
  strengths: string;
  weaknesses: string;
  wishlist_habit: string;
  recommended_intervention: string;
  is_primary_target: boolean;
}

export const SHOPPER_SEGMENTS: ShopperSegment[] = [
  {
    type: "Bargain Hunter",
    brief_description: "Looks for the best price/deal before committing.",
    purchase_intent: "Medium–High",
    intent_level: "medium_high",
    share_pct: 44.9,
    estimated_users: 928,
    strengths: "Value-conscious; strong response to price drops",
    weaknesses: "Delays purchase; may keep items wishlisted for long",
    wishlist_habit: "Uses wishlist as a passive price-tracker; accumulates 15–30 items waiting for EORS sales or 40%+ drops.",
    recommended_intervention: "Personalized Target Strike-Price Alerts ('Alert me under ₹1,499') & Flash Drop VIP Passes.",
    is_primary_target: true,
  },
  {
    type: "Well-Informed Scholar",
    brief_description: "Researches reviews, quality, alternatives and product details before buying.",
    purchase_intent: "High",
    intent_level: "high",
    share_pct: 35.5,
    estimated_users: 734,
    strengths: "Makes confident, informed decisions",
    weaknesses: "Longer decision cycle; analysis paralysis",
    wishlist_habit: "Shortlists 4–8 similar items and opens multiple browser tabs to compare fabric blend, sizing, and ratings.",
    recommended_intervention: "In-App Side-by-Side Spec Comparison Matrix (Fabric GSM, Neckline, Rating) & AI Proportion Normalizer.",
    is_primary_target: true,
  },
  {
    type: "Determined Shopper",
    brief_description: "Has a specific need/goal and actively looks for the right product.",
    purchase_intent: "Very High",
    intent_level: "very_high",
    share_pct: 18.0,
    estimated_users: 372,
    strengths: "Clear intent; focused; high conversion potential",
    weaknesses: "Purchase stalls when exact needs aren't met",
    wishlist_habit: "Uses wishlist strictly as a pre-cart holding ground for 24–48h before payday or immediate checkout.",
    recommended_intervention: "Guaranteed Event-Date Delivery Badges & 1-Click Doorstep Size Hold.",
    is_primary_target: false,
  },
  {
    type: "Social Shopper",
    brief_description: "Uses friends, influencers, reviews and social proof to guide decisions.",
    purchase_intent: "Medium–High",
    intent_level: "medium_high",
    share_pct: 21.8,
    estimated_users: 450,
    strengths: "Responsive to recommendations and trends",
    weaknesses: "Can remain uncertain without external validation",
    wishlist_habit: "Takes screenshots of wishlisted outfits to share in WhatsApp group chats for family/friend approval before buying.",
    recommended_intervention: "1-Click Interactive WhatsApp Group Voting Polls ('Buy' or 'Skip') & Daylight Customer Review Photos.",
    is_primary_target: true,
  },
  {
    type: "Impulse Buyer",
    brief_description: "Purchases spontaneously when something catches their attention.",
    purchase_intent: "High but situational",
    intent_level: "high",
    share_pct: 17.4,
    estimated_users: 360,
    strengths: "Fast conversion; responsive to trends/offers",
    weaknesses: "Less predictable; higher risk of regret",
    wishlist_habit: "Uses wishlist as an intentional 7–14 day cooling-off buffer to let emotional shopping impulses settle.",
    recommended_intervention: "Wishlist Cooling-Off Timer & Salary-Day Smart Reminders.",
    is_primary_target: false,
  },
  {
    type: "Reluctant Shopper",
    brief_description: "Needs substantial reassurance before committing to a purchase.",
    purchase_intent: "Low–Medium",
    intent_level: "low_medium",
    share_pct: 13.0,
    estimated_users: 269,
    strengths: "Careful; minimizes perceived risk",
    weaknesses: "High hesitation; greater drop-off",
    wishlist_habit: "Fears return hassles, doorstep QC rejection, or poor fabric feel, causing items to sit indefinitely.",
    recommended_intervention: "Zero-Friction 1-Click Doorstep Exchange & Instant UPI Refund Guarantee.",
    is_primary_target: false,
  },
];

export interface ReviewRecord {
  id: string;
  source: string;
  platform_tag: string;
  date: string;
  text: string;
  theme: string;
  purchase_intent: "High" | "Medium" | "Low";
  sentiment: "Positive" | "Negative" | "Neutral" | "Mixed";
  sentiment_score: number;
  confidence: number;
  url: string;
}

export const SAMPLE_REVIEWS: ReviewRecord[] = [
  {
    id: "chunk_001",
    source: "Reddit",
    platform_tag: "r/IndianFashionAddicts",
    date: "Aug 28, 2026",
    text: "Saved 4 floral midi dresses for an upcoming wedding in Goa. I'm waiting for the EORS sale because ₹3,499 feels steep for polyester blend. If it drops below ₹2k I'll buy immediately.",
    theme: "Price Drop Sensitivity",
    purchase_intent: "High",
    sentiment: "Mixed",
    sentiment_score: 0.55,
    confidence: 0.94,
    url: "https://reddit.com/r/IndianFashionAddicts/comments/myntra_wishlist_prices",
  },
  {
    id: "chunk_002",
    source: "Reddit",
    platform_tag: "r/TwoXIndia",
    date: "Aug 28, 2026",
    text: "Myntra sizing is completely unpredictable across brands. In Mango I am Medium, but in Tokyo Talkies Medium fits like an XS. I have 6 tops saved in wishlist but too scared to checkout and deal with return hassle.",
    theme: "Sizing & Fit Anxiety",
    purchase_intent: "High",
    sentiment: "Negative",
    sentiment_score: 0.15,
    confidence: 0.96,
    url: "https://reddit.com/r/TwoXIndia/comments/sizing_issues_online_shopping",
  },
  {
    id: "chunk_003",
    source: "App Store",
    platform_tag: "iOS Review",
    date: "Aug 29, 2026",
    text: "Wishlist is so cluttered with out of stock items! I hit the 1,000 item limit and now I can't save anything new. Why can't we create custom folders like 'Workwear' or 'Festive'?",
    theme: "Wishlist Maintenance & Clutter",
    purchase_intent: "Medium",
    sentiment: "Negative",
    sentiment_score: 0.20,
    confidence: 0.92,
    url: "https://apps.apple.com/app/myntra-fashion-shopping/id907394059",
  },
  {
    id: "chunk_004",
    source: "Quora",
    platform_tag: "Quora Q&A",
    date: "Aug 29, 2026",
    text: "I always shortlist kurtas on Myntra because the search and catalog are great, but then I copy the brand name to AJIO or Nykaa Fashion to check if there is a ₹300 coupon code before buying.",
    theme: "Competitor Price Arbitrage",
    purchase_intent: "High",
    sentiment: "Neutral",
    sentiment_score: 0.50,
    confidence: 0.91,
    url: "https://quora.com/Why-do-people-wishlist-items-on-Myntra-and-buy-on-AJIO",
  },
  {
    id: "chunk_005",
    source: "Google Play",
    platform_tag: "Android Review",
    date: "Aug 30, 2026",
    text: "Loved the unedited customer photos on reviews! It saved me from buying a kurta that looked maroon in studio lighting but was actually bright red in daylight.",
    theme: "Social Validation & Photos",
    purchase_intent: "High",
    sentiment: "Positive",
    sentiment_score: 0.88,
    confidence: 0.95,
    url: "https://play.google.com/store/apps/details?id=com.myntra.android",
  },
  {
    id: "chunk_006",
    source: "Reddit",
    platform_tag: "r/delhi",
    date: "Aug 30, 2026",
    text: "I use my wishlist as a salary day bucket. I keep adding cool oversized streetwear tees throughout the month, and when salary credits on the 31st, I buy the top 2 items and keep the rest.",
    theme: "Pre-Cart & Impulse Buffer",
    purchase_intent: "High",
    sentiment: "Positive",
    sentiment_score: 0.82,
    confidence: 0.93,
    url: "https://reddit.com/r/delhi/comments/payday_shopping_haul",
  },
  {
    id: "chunk_007",
    source: "Survey",
    platform_tag: "User Survey #24",
    date: "Aug 31, 2026",
    text: "I take screenshots of 3 dresses from my wishlist and send them to my WhatsApp group with my college friends. I only buy the one that gets the most votes.",
    theme: "Social Reassurance Delays",
    purchase_intent: "Medium",
    sentiment: "Mixed",
    sentiment_score: 0.60,
    confidence: 0.89,
    url: "https://myntra.com/research/survey/2026_wishlist_study",
  },
  {
    id: "chunk_008",
    source: "Interview",
    platform_tag: "1-on-1 Interview P03",
    date: "Aug 31, 2026",
    text: "When I open my wishlist, there are items from 6 months ago that I completely forgot about. The impulse is dead now, so I just delete them. A gentle reminder after 14 days would have converted me.",
    theme: "Desire Decay & Forgetting",
    purchase_intent: "Low",
    sentiment: "Negative",
    sentiment_score: 0.30,
    confidence: 0.90,
    url: "https://myntra.com/research/interviews/transcript_p03",
  },
];
