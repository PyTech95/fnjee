import AppShell from "@/pages/AppShell";
import { LayoutDashboard, BookOpen, FilePlus2, BarChart3, Video } from "lucide-react";

const NAV = [
  { to: "/teacher", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/teacher/question-bank", label: "Question Bank", icon: BookOpen },
  { to: "/teacher/papers", label: "My Papers", icon: FilePlus2 },
  { to: "/teacher/live-classes", label: "Live Classes", icon: Video },
  { to: "/teacher/results", label: "Results", icon: BarChart3 },
];

export default function TeacherLayout() {
  return <AppShell nav={NAV} brandLabel="FNJEE.com" accent="Teacher" />;
}
