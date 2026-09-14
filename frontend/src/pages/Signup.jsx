import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { toast } from "sonner";

export default function Signup() {
  const [role, setRole] = useState("student");
  const [form, setForm] = useState({ name: "", email: "", password: "", referral_code: "", child_email: "", exam_target: "JEE" });
  const [busy, setBusy] = useState(false);
  const { signup } = useAuth();
  const nav = useNavigate();
  const upd = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault(); setBusy(true);
    try {
      const u = await signup({ ...form, role });
      toast.success(`Account created! Welcome ${u.name}`);
      nav(u.role === "admin" ? "/admin" : u.role === "parent" ? "/parent" : "/student");
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Signup failed");
    } finally { setBusy(false); }
  };

  return (
    <div data-testid="signup-page" className="min-h-screen flex items-center justify-center p-8 bg-muted/30">
      <Card className="w-full max-w-lg p-8 rounded-3xl border-border">
        <Link to="/" className="flex items-center gap-2 mb-6">
          <div className="h-9 w-9 rounded-xl bg-white grid place-items-center shadow-sm border border-border"><img src="/icon-192.png" alt="FNJEE.com" className="h-7 w-7" /></div>
          <span className="font-display font-bold text-xl tracking-tight">FNJEE.com</span>
        </Link>
        <h1 className="font-display font-bold text-3xl tracking-tight">Create your account</h1>
        <p className="text-sm text-muted-foreground mt-1 mb-6">Pick your role and get started in seconds.</p>

        <Tabs value={role} onValueChange={setRole}>
          <TabsList data-testid="signup-role-tabs" className="grid grid-cols-3 rounded-full h-auto p-1">
            <TabsTrigger value="student" className="rounded-full">Student</TabsTrigger>
            <TabsTrigger value="parent" className="rounded-full">Parent</TabsTrigger>
            <TabsTrigger value="admin" className="rounded-full">Admin</TabsTrigger>
          </TabsList>
          <TabsContent value={role} className="mt-6">
            <form onSubmit={submit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Full name</Label>
                  <Input data-testid="signup-name" required value={form.name} onChange={(e) => upd("name", e.target.value)} />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input data-testid="signup-email" type="email" required value={form.email} onChange={(e) => upd("email", e.target.value)} />
                </div>
              </div>
              <div>
                <Label>Password</Label>
                <Input data-testid="signup-password" type="password" required value={form.password} onChange={(e) => upd("password", e.target.value)} />
              </div>
              {role === "student" && (
                <>
                  <div>
                    <Label>Exam target</Label>
                    <Input value={form.exam_target} onChange={(e) => upd("exam_target", e.target.value)} placeholder="JEE / NEET / …" />
                  </div>
                  <div>
                    <Label>Referral code (optional)</Label>
                    <Input value={form.referral_code} onChange={(e) => upd("referral_code", e.target.value)} placeholder="EXN…" />
                  </div>
                </>
              )}
              {role === "parent" && (
                <div>
                  <Label>Your child's email (student account)</Label>
                  <Input data-testid="signup-child-email" type="email" value={form.child_email} onChange={(e) => upd("child_email", e.target.value)} />
                </div>
              )}
              <Button data-testid="signup-submit" disabled={busy} className="w-full rounded-full">{busy ? "Creating…" : "Create account"}</Button>
            </form>
          </TabsContent>
        </Tabs>
        <div className="mt-6 text-sm text-muted-foreground">
          Already have an account? <Link to="/login" className="text-primary font-medium hover:underline">Sign in</Link>
        </div>
      </Card>
    </div>
  );
}
