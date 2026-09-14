import AppShell from "@/pages/AppShell";
import { LayoutDashboard, BookOpen, Bell, Mail } from "lucide-react";

const NAV = [
  { to: "/parent", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/parent/digest", label: "Weekly Digest", icon: Mail },
  { to: "/parent/assign", label: "Assign Test", icon: BookOpen },
  { to: "/parent/notifications", label: "Notifications", icon: Bell },
];

export default function ParentLayout() {
  return <AppShell nav={NAV} brandLabel="Abhyash Mantra" accent="Parent" />;
}
