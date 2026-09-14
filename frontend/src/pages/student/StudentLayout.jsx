import AppShell from "@/pages/AppShell";
import { LayoutDashboard, BookOpen, Trophy, User, Headphones, Zap, Layers, Network, Target, PlayCircle, Sparkles, Video, Radio, Bot, Wand2, RotateCcw, Gauge, Swords } from "lucide-react";

const NAV = [
  { to: "/student", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/student/tests", label: "My Tests", icon: BookOpen },
  { to: "/student/ai-tutor", label: "AI Tutor", icon: Bot },
  { to: "/student/battles", label: "Quiz Battles", icon: Swords },
  { to: "/student/coach", label: "Weakness Coach", icon: Target },
  { to: "/student/adaptive", label: "Adaptive CAT", icon: Gauge },
  { to: "/student/revision", label: "Smart Revision", icon: RotateCcw },
  { to: "/student/notes-quiz", label: "Notes → Quiz", icon: Wand2 },
  { to: "/student/leaderboard", label: "Leaderboard", icon: Radio },
  { to: "/student/live", label: "Live Classes", icon: Video },
  { to: "/student/practice", label: "Practice", icon: Sparkles },
  { to: "/student/dpp", label: "Today's DPP", icon: Zap },
  { to: "/student/playlist", label: "Chapter Playlist", icon: PlayCircle },
  { to: "/student/flashcards", label: "Flashcards", icon: Layers },
  { to: "/student/mindmaps", label: "Mindmaps", icon: Network },
  { to: "/student/rank", label: "Rank Predictor", icon: Target },
  { to: "/student/podcasts", label: "Podcasts", icon: Headphones },
  { to: "/student/rewards", label: "Rewards", icon: Trophy },
  { to: "/student/profile", label: "Profile", icon: User },
];

export default function StudentLayout() {
  return <AppShell nav={NAV} brandLabel="Abhyash Mantra" accent="Student" />;
}
