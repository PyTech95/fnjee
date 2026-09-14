import AppShell from "@/pages/AppShell";
import { LayoutDashboard, BookOpen, Upload, Plus, ListChecks, Users, BarChart3, Award, Video, ShieldCheck, Activity, ScanEye } from "lucide-react";

const NAV = [
  { to: "/admin", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/admin/questions", label: "Question Bank", icon: BookOpen },
  { to: "/admin/import", label: "Import Wizard", icon: Upload },
  { to: "/admin/questions/new", label: "New Question", icon: Plus },
  { to: "/admin/tests", label: "Tests", icon: ListChecks },
  { to: "/admin/live-classes", label: "Live Classes", icon: Video },
  { to: "/admin/grading", label: "Grading", icon: Award },
  { to: "/admin/students", label: "Users", icon: Users },
  { to: "/admin/teachers", label: "Teacher Access", icon: ShieldCheck },
  { to: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/admin/proctoring", label: "Exam Integrity", icon: ScanEye },
  { to: "/admin/system", label: "System Health", icon: Activity },
];

export default function AdminLayout() {
  return <AppShell nav={NAV} brandLabel="FNJEE.com" accent="Admin" />;
}
