import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/AuthContext";
import { User, Lock, Loader2, Keyboard } from "lucide-react";
import { toast } from "sonner";

const DEMO_TEST_ID = "demo-cbt-jee-advanced";
const DEMO_EMAIL = "student1@examnest.io";
const DEMO_PASSWORD = "Student@123";

export default function DemoExam() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState(DEMO_EMAIL);
  const [password, setPassword] = useState(DEMO_PASSWORD);
  const [busy, setBusy] = useState(false);

  const signIn = async (e) => {
    e?.preventDefault();
    if (busy) return;
    setBusy(true);
    try {
      await login({ email: email.trim(), password, role: "student" });
      nav(`/student/cbt/${DEMO_TEST_ID}`);
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Login failed. Use the pre-filled demo candidate.");
      setBusy(false);
    }
  };

  return (
    <div data-testid="demo-exam-login" className="min-h-screen bg-white flex flex-col">
      {/* ---- Official-style exam banner ---- */}
      <div className="w-full border-b border-slate-300">
        <div className="flex items-stretch">
          <div className="flex items-center gap-4 px-4 sm:px-6 py-3 bg-gradient-to-r from-[#0b2e59] to-[#17457e] text-white flex-1">
            <div className="h-14 w-14 rounded-md bg-white/15 grid place-items-center font-display font-extrabold text-xl tracking-tight shrink-0">
              JEE
            </div>
            <div className="min-w-0">
              <div className="text-[11px] uppercase tracking-[0.25em] text-blue-200">Joint Entrance Examination (Advanced) 2026</div>
              <div className="font-display font-bold text-lg sm:text-2xl leading-tight">FNJEE Computer Based Test — Demo</div>
            </div>
          </div>
        </div>
        <div className="bg-[#f4b840] text-[#0b2e59]">
          <div className="px-4 sm:px-6 py-2 flex flex-wrap items-center gap-x-6 gap-y-1 text-sm">
            <div><span className="font-semibold">System Name :</span> <span className="font-display font-extrabold tracking-wide">C001</span></div>
            <div className="text-[#0b2e59]/80">Kindly contact the invigilator if there is any discrepancy on your screen.</div>
            <div className="ml-auto"><span className="font-semibold">Subject :</span> Mock Exam</div>
          </div>
        </div>
      </div>

      {/* ---- Login card ---- */}
      <div className="flex-1 grid place-items-center px-4 py-10 bg-slate-50">
        <motion.div
          initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45, ease: "easeOut" }}
          className="w-full max-w-md rounded-xl overflow-hidden border border-slate-200 shadow-xl bg-white">
          <div className="bg-gradient-to-r from-slate-100 to-slate-200 px-5 py-3 border-b border-slate-200">
            <h1 className="font-display font-bold text-xl text-slate-800">Login</h1>
          </div>
          <form onSubmit={signIn} className="p-6 space-y-4">
            <div className="flex items-stretch rounded-lg overflow-hidden border border-slate-300 focus-within:border-[#0b2e59] focus-within:ring-2 focus-within:ring-[#0b2e59]/20 transition">
              <span className="w-12 grid place-items-center bg-slate-100 text-slate-500 border-r border-slate-300"><User className="h-5 w-5" /></span>
              <input data-testid="demo-login-email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="flex-1 px-3 py-3 text-sm outline-none" placeholder="Candidate ID" autoComplete="username" />
              <span className="w-10 grid place-items-center text-slate-400"><Keyboard className="h-4 w-4" /></span>
            </div>
            <div className="flex items-stretch rounded-lg overflow-hidden border border-slate-300 focus-within:border-[#0b2e59] focus-within:ring-2 focus-within:ring-[#0b2e59]/20 transition">
              <span className="w-12 grid place-items-center bg-slate-100 text-slate-500 border-r border-slate-300"><Lock className="h-5 w-5" /></span>
              <input data-testid="demo-login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="flex-1 px-3 py-3 text-sm outline-none" placeholder="Password" autoComplete="current-password" />
              <span className="w-10 grid place-items-center text-slate-400"><Keyboard className="h-4 w-4" /></span>
            </div>

            <motion.button whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.98 }}
              data-testid="demo-login-submit" type="submit" disabled={busy}
              className="w-full rounded-lg bg-gradient-to-r from-[#1f8fe0] to-[#1673c0] text-white font-semibold py-3 text-base shadow-md hover:shadow-lg transition disabled:opacity-60 inline-flex items-center justify-center gap-2">
              {busy ? <><Loader2 className="h-5 w-5 animate-spin" /> Signing in…</> : "Sign In"}
            </motion.button>

            <div className="rounded-lg bg-blue-50 border border-blue-100 px-3 py-2 text-xs text-slate-600">
              Demo candidate is pre-filled for you — just press <b>Sign In</b> to experience the full CBT interface.
            </div>
            <div className="text-center">
              <Link to="/" className="text-xs text-slate-400 hover:text-slate-600">← Back to FNJEE.com</Link>
            </div>
          </form>
        </motion.div>
      </div>
      <div className="bg-[#0b2e59] text-center text-white/80 text-xs py-2">Version 17.07.00 · Demo</div>
    </div>
  );
}
