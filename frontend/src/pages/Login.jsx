import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";

const DEMO = {
  admin: { email: "admin@examnest.io", password: "Admin@123" },
  teacher: { email: "teacher1@examnest.io", password: "Teacher@123" },
  student: { email: "student1@examnest.io", password: "Student@123" },
  parent: { email: "parent1@examnest.io", password: "Parent@123" },
};

export default function Login() {
  const [role, setRole] = useState("student");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const { login } = useAuth();
  const nav = useNavigate();

  const submit = async (e) => {
    e?.preventDefault();
    setBusy(true);
    try {
      const u = await login({ email, password, role });
      toast.success(`Welcome back, ${u.name}!`);
      nav(u.role === "admin" ? "/admin" : u.role === "parent" ? "/parent" : u.role === "teacher" ? "/teacher" : "/student");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed");
    } finally { setBusy(false); }
  };

  const useDemo = () => { setEmail(DEMO[role].email); setPassword(DEMO[role].password); };

  return (
    <div data-testid="login-page" className="min-h-screen grid lg:grid-cols-2">
      <div className="hidden lg:flex flex-col justify-between p-10 bg-primary text-primary-foreground relative overflow-hidden">
        <div className="absolute inset-0 en-grid-bg opacity-10" aria-hidden="true" />
        <Link to="/" className="relative flex items-center gap-2">
          <div className="h-9 w-9 rounded-xl bg-primary-foreground text-primary grid place-items-center font-display font-bold">M</div>
          <span className="font-display font-bold text-xl tracking-tight">Abhyash Mantra</span>
        </Link>
        <div className="relative">
          <h2 className="font-display font-bold text-4xl leading-tight tracking-tight">Three portals.<br/>One serious edge<br/>for JEE / NEET prep.</h2>
          <p className="mt-4 text-primary-foreground/80 max-w-md">Admin runs the show. Students train hard. Parents stay in the loop. Everyone wins.</p>
        </div>
        <div className="relative text-sm text-primary-foreground/70">Trusted by coaching institutes preparing India's next rankers.</div>
      </div>

      <div className="flex items-center justify-center p-8">
        <Card className="w-full max-w-md p-8 rounded-3xl border-border">
          <div className="mb-6">
            <h1 className="font-display font-bold text-3xl tracking-tight">Welcome back</h1>
            <p className="text-sm text-muted-foreground mt-1">Choose your role to sign in.</p>
          </div>
          <Tabs value={role} onValueChange={setRole}>
            <TabsList data-testid="login-role-tabs" className="grid grid-cols-4 rounded-full h-auto p-1">
              <TabsTrigger data-testid="tab-student" value="student" className="rounded-full">Student</TabsTrigger>
              <TabsTrigger data-testid="tab-teacher" value="teacher" className="rounded-full">Teacher</TabsTrigger>
              <TabsTrigger data-testid="tab-parent" value="parent" className="rounded-full">Parent</TabsTrigger>
              <TabsTrigger data-testid="tab-admin" value="admin" className="rounded-full">Admin</TabsTrigger>
            </TabsList>
            <TabsContent value={role} className="mt-6">
              <form onSubmit={submit} className="space-y-4">
                <div>
                  <Label htmlFor="email">Email</Label>
                  <Input data-testid="login-email" id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@examnest.io" />
                </div>
                <div>
                  <Label htmlFor="password">Password</Label>
                  <Input data-testid="login-password" id="password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} />
                </div>
                <div className="flex gap-2">
                  <Button data-testid="login-submit" type="submit" disabled={busy} className="rounded-full flex-1">{busy ? "Signing in…" : "Sign in"}</Button>
                  <Button data-testid="use-demo-btn" type="button" variant="outline" className="rounded-full" onClick={useDemo}>Use demo</Button>
                </div>
              </form>
            </TabsContent>
          </Tabs>
          <div className="mt-6 text-sm text-muted-foreground">
            New here? <Link to="/signup" className="text-primary font-medium hover:underline">Create an account</Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
