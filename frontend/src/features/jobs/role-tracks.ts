export type RoleTrackId = "all" | "frontend" | "backend" | "fullstack" | "ai";

export interface RoleTrack {
  id: RoleTrackId;
  label: string;
  shortLabel: string;
  badge: string;
  description: string;
  keywords: string[];
  gradient: string;
  bgTone: string;
  borderTone: string;
  textTone: string;
}

export const ROLE_TRACKS: Record<RoleTrackId, RoleTrack> = {
  all: {
    id: "all",
    label: "All Software & AI",
    shortLabel: "All Roles",
    badge: "✨ All Tracks",
    description: "Frontend, Backend, Full-Stack, and AI/ML Engineering positions",
    keywords: [
      "software engineer",
      "software developer",
      "frontend engineer",
      "frontend developer",
      "backend engineer",
      "backend developer",
      "full stack engineer",
      "full stack developer",
      "fullstack",
      "ai engineer",
      "ai developer",
      "machine learning engineer",
      "ml engineer",
      "artificial intelligence",
      "web developer",
      "python developer",
      "react developer",
      "distributed systems",
      "cloud engineer",
      "platform engineer",
    ],
    gradient: "from-indigo-500/20 via-violet-500/20 to-purple-500/20",
    bgTone: "bg-indigo-500/10 dark:bg-indigo-500/20",
    borderTone: "border-indigo-500/30 dark:border-indigo-500/40",
    textTone: "text-indigo-600 dark:text-indigo-400",
  },
  frontend: {
    id: "frontend",
    label: "Frontend Engineering",
    shortLabel: "Frontend",
    badge: "🎨 Frontend",
    description: "React, Next.js, TypeScript, UI/UX, Web & Interface Engineering",
    keywords: [
      "frontend engineer",
      "frontend developer",
      "front end",
      "react",
      "next.js",
      "typescript",
      "ui engineer",
      "web developer",
      "javascript engineer",
      "client engineer",
    ],
    gradient: "from-sky-500/20 via-blue-500/20 to-cyan-500/20",
    bgTone: "bg-sky-500/10 dark:bg-sky-500/20",
    borderTone: "border-sky-500/30 dark:border-sky-500/40",
    textTone: "text-sky-600 dark:text-sky-400",
  },
  backend: {
    id: "backend",
    label: "Backend Systems",
    shortLabel: "Backend",
    badge: "⚙️ Backend",
    description: "Python, Java, Distributed Systems, Microservices, APIs & Cloud",
    keywords: [
      "backend engineer",
      "backend developer",
      "back end",
      "systems engineer",
      "python developer",
      "java engineer",
      "distributed systems",
      "api engineer",
      "cloud engineer",
      "platform engineer",
      "golang",
      "database",
    ],
    gradient: "from-emerald-500/20 via-teal-500/20 to-green-500/20",
    bgTone: "bg-emerald-500/10 dark:bg-emerald-500/20",
    borderTone: "border-emerald-500/30 dark:border-emerald-500/40",
    textTone: "text-emerald-600 dark:text-emerald-400",
  },
  fullstack: {
    id: "fullstack",
    label: "Full-Stack Engineering",
    shortLabel: "Full-Stack",
    badge: "🌐 Full-Stack",
    description: "End-to-end product engineering across Frontend, Backend & Database",
    keywords: [
      "full stack engineer",
      "full stack developer",
      "fullstack",
      "full-stack",
      "software engineer",
      "web application developer",
      "product engineer",
    ],
    gradient: "from-amber-500/20 via-orange-500/20 to-yellow-500/20",
    bgTone: "bg-amber-500/10 dark:bg-amber-500/20",
    borderTone: "border-amber-500/30 dark:border-amber-500/40",
    textTone: "text-amber-600 dark:text-amber-400",
  },
  ai: {
    id: "ai",
    label: "AI & Machine Learning",
    shortLabel: "AI / ML",
    badge: "🤖 AI & ML",
    description: "LLMs, GenAI, Agentic Systems, Machine Learning & Intelligent Applications",
    keywords: [
      "ai engineer",
      "ai developer",
      "machine learning engineer",
      "ml engineer",
      "artificial intelligence",
      "llm engineer",
      "genai engineer",
      "deep learning",
      "nlp engineer",
      "applied ai",
    ],
    gradient: "from-fuchsia-500/20 via-purple-500/20 to-pink-500/20",
    bgTone: "bg-fuchsia-500/10 dark:bg-fuchsia-500/20",
    borderTone: "border-fuchsia-500/30 dark:border-fuchsia-500/40",
    textTone: "text-fuchsia-600 dark:text-fuchsia-400",
  },
};

export const TRACK_LIST = Object.values(ROLE_TRACKS);

/**
 * Determines whether a job matches a given role track.
 */
export function matchesTrack(
  job: { title: string; description_text?: string },
  trackId: RoleTrackId
): boolean {
  if (trackId === "all") return true;
  const track = ROLE_TRACKS[trackId];
  if (!track) return true;

  const haystack = `${job.title} ${job.description_text ?? ""}`.toLowerCase();
  return track.keywords.some((kw) => haystack.includes(kw.toLowerCase()));
}

/**
 * Detects which tracks a job matches.
 */
export function identifyJobTracks(
  job: { title: string; description_text?: string }
): RoleTrackId[] {
  const haystack = `${job.title} ${job.description_text ?? ""}`.toLowerCase();
  const matched: RoleTrackId[] = [];

  const specificTracks: RoleTrackId[] = ["frontend", "backend", "fullstack", "ai"];
  for (const trackId of specificTracks) {
    const track = ROLE_TRACKS[trackId];
    if (track.keywords.some((kw) => haystack.includes(kw.toLowerCase()))) {
      matched.push(trackId);
    }
  }

  // Fallback to fullstack or backend if general software engineer
  if (matched.length === 0 && (haystack.includes("software") || haystack.includes("engineer") || haystack.includes("developer"))) {
    matched.push("fullstack");
  }

  return matched;
}
