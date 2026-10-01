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
    gradient: "from-primary/10 to-transparent",
    bgTone: "bg-primary/10",
    borderTone: "border-primary/30",
    textTone: "text-primary",
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
    gradient: "from-primary/10 to-transparent",
    bgTone: "bg-primary/10",
    borderTone: "border-primary/30",
    textTone: "text-primary",
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
    gradient: "from-primary/10 to-transparent",
    bgTone: "bg-primary/10",
    borderTone: "border-primary/30",
    textTone: "text-primary",
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
    gradient: "from-primary/10 to-transparent",
    bgTone: "bg-primary/10",
    borderTone: "border-primary/30",
    textTone: "text-primary",
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
    gradient: "from-primary/10 to-transparent",
    bgTone: "bg-primary/10",
    borderTone: "border-primary/30",
    textTone: "text-primary",
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
