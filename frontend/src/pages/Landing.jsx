import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion"; // eslint-disable-line no-unused-vars
import {
  ShieldCheck,
  Database,
  Zap,
  Brain,
  Users,
  Activity,
  ArrowRight,
  Check,
  Lock,
  Sparkles,
  FileText,
  Clock,
  Crosshair
} from "lucide-react";
import { getCurrentSubdomain } from "../lib/subdomain";
import { getTenantBySubdomain } from "../api/tenants";
import { useAuth } from "../context/AuthContext";

export default function Landing() {
  const [tenantName, setTenantName] = useState("");
  const { isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (loading) return;
    
    const sub = getCurrentSubdomain();
    if (sub) {
      if (isAuthenticated) {
        navigate("/dashboard", { replace: true });
      } else {
        navigate("/login", { replace: true });
      }
      return;
    }

    if (isAuthenticated) {
      navigate("/dashboard", { replace: true });
    }
  }, [isAuthenticated, loading, navigate]);

  useEffect(() => {
    const sub = getCurrentSubdomain();
    if (sub) {
      getTenantBySubdomain(sub)
        .then(t => {
          if (t && t.name) setTenantName(t.name);
        })
        .catch(err => console.error(err));
    }
  }, []);

  return (
    <div className="min-h-screen bg-surface-soft flex flex-col animate-fade-in">
      <TopNav tenantName={tenantName} />
      <main className="flex-1">
        <Hero tenantName={tenantName} />
        <TrustBar />
        <HowItWorks />
        <FeaturesSection />
        <CtaStrip />
      </main>
      <SiteFooter />
    </div>
  );
}

function TopNav({ tenantName }) {
  return (
    <nav className="sticky top-0 z-50 w-full bg-canvas border-b border-hairline h-16 flex items-center justify-between">
      <div className="max-w-[1280px] w-full mx-auto px-6 h-full flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <span className="w-8 h-8 rounded-md bg-primary flex items-center justify-center">
            <svg viewBox="0 0 24 24" className="w-[18px] h-[18px] text-white" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5z" />
              <circle cx="12" cy="18" r="2" />
            </svg>
          </span>
          <span className="text-[16px] font-bold text-ink tracking-tight font-sans">
            {tenantName ? `${tenantName} Portal` : "AI X-Ray Analyzer"}
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-6 text-[13px] font-bold text-mute">
          <a href="#features" className="hover:text-ink transition-colors">Features</a>
          <a href="#how" className="hover:text-ink transition-colors">How it works</a>
          <a href="#security" className="hover:text-ink transition-colors">Security</a>
        </div>

        <div className="flex items-center gap-2">
          <Link
            to="/login"
            className="px-4 h-10 inline-flex items-center text-[12px] font-bold text-ink bg-transparent hover:bg-surface-card rounded-md transition-colors"
          >
            Log in
          </Link>
          <Link
            to="/register"
            className="px-4 h-10 inline-flex items-center text-[12px] font-bold text-white bg-primary hover:bg-primary-pressed rounded-md transition-colors"
          >
            Sign up
          </Link>
        </div>
      </div>
    </nav>
  );
}

function Hero({ tenantName }) {
  return (
    <section className="px-6 py-12 lg:py-20">
      <div className="max-w-[1280px] mx-auto grid lg:grid-cols-[1.1fr_1fr] gap-12 lg:gap-16 items-center">
        {/* Copy */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-surface-card rounded-full mb-6 border border-hairline-soft">
            <Sparkles className="w-3.5 h-3.5 text-primary" />
            <span className="text-[11px] font-bold text-ink-soft uppercase tracking-wider">Clinical Grade Diagnostics</span>
          </div>

          <h1 className="text-[32px] sm:text-[44px] md:text-[50px] lg:text-[56px] font-bold text-ink leading-[1.15] mb-6 tracking-[-1px]">
            {tenantName ? `AI-powered diagnostics for ${tenantName}.` : "AI-powered diagnostics for modern radiology."}
          </h1>

          <p className="text-[15px] text-body max-w-xl leading-[1.5] mb-8 font-medium">
            Instantly upload chest X-rays, calculate predictions, and display Grad-CAM visual overlays. Complete multi-tenant hospital isolation with passwordless security.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 mb-8">
            <Link
              to="/register"
              className="h-10 px-5 inline-flex items-center justify-center gap-2 text-[12px] font-bold text-white bg-primary hover:bg-primary-pressed rounded-md transition-colors shadow-sm"
            >
              Get started free
              <ArrowRight className="w-3.5 h-3.5" strokeWidth={2.5} />
            </Link>
            <Link
              to="/login"
              className="h-10 px-5 inline-flex items-center justify-center text-[12px] font-bold text-ink bg-secondary-bg hover:bg-secondary-pressed rounded-md transition-colors"
            >
              Enter portal
            </Link>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 text-[12px] text-mute font-bold">
            <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-600" strokeWidth={3} /> No credit card</span>
            <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-600" strokeWidth={3} /> HIPAA-ready</span>
            <span className="flex items-center gap-1.5"><Check className="w-3.5 h-3.5 text-emerald-600" strokeWidth={3} /> Multi-tenant</span>
          </div>
        </motion.div>

        {/* Visual Mockup - Simple & Professional PACS Style */}
        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.1 }}
        >
          <div className="bg-[#0c0c0e] border border-hairline rounded-md overflow-hidden relative aspect-[4/3] w-full max-w-lg mx-auto flex items-center justify-center shadow-md">
            <XrayMockup />
            
            {/* DICOM Style HUD */}
            <div className="absolute inset-0 bg-gradient-to-b from-black/60 via-transparent to-black/60 pointer-events-none p-3.5 flex flex-col justify-between text-[10px] font-mono text-white/70 select-none">
              <div className="flex justify-between items-start">
                <div>
                  <p className="font-bold text-white tracking-wider">PATIENT #9822A</p>
                  <p className="text-[8px] opacity-75">ID: fd818a6c</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-primary tracking-wider">CHEST AP</p>
                  <p className="text-[8px] opacity-75">2026-05-23</p>
                </div>
              </div>
              
              {/* Target overlay */}
              <div className="absolute inset-0 flex items-center justify-center opacity-20">
                <div className="w-8 h-[1px] bg-white"></div>
                <div className="h-8 w-[1px] bg-white absolute"></div>
                <div className="w-16 h-16 border border-dashed border-white rounded-full absolute"></div>
              </div>

              {/* Heatmap overlay simulation */}
              <div
                className="absolute top-[30%] right-[32%] w-[35%] aspect-square rounded-full opacity-60 mix-blend-screen"
                style={{
                  background:
                    "radial-gradient(circle, rgba(230,0,35,0.95) 0%, rgba(255,140,0,0.5) 40%, transparent 75%)",
                }}
              />

              <div className="flex justify-between items-end">
                <div>
                  <p className="opacity-75">W: 420 L: 180</p>
                  <p className="opacity-75">ZOOM: COMPACT</p>
                </div>
                <div className="text-right">
                  <p className="opacity-75 font-bold text-emerald-400">AI PROCESSED</p>
                </div>
              </div>
            </div>

            {/* Float badge */}
            <div className="absolute bottom-10 right-4 px-2.5 py-1.5 bg-canvas border border-hairline rounded-md shadow-sm pointer-events-none">
              <div className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-primary" />
                <span className="text-[11px] font-bold text-ink">98.2% Accuracy</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}

function XrayMockup() {
  return (
    <svg viewBox="0 0 300 400" className="w-full h-full opacity-65" preserveAspectRatio="xMidYMid slice">
      <defs>
        <radialGradient id="lungGradLanding" cx="0.5" cy="0.5" r="0.6">
          <stop offset="0%" stopColor="#2a2a26" />
          <stop offset="100%" stopColor="#0a0a08" />
        </radialGradient>
      </defs>
      <path
        d="M60 80 Q60 60 90 55 L120 60 L150 50 L180 60 L210 55 Q240 60 240 80 L250 200 Q250 260 230 310 L220 360 L80 360 L70 310 Q50 260 50 200 Z"
        fill="url(#lungGradLanding)"
        stroke="rgba(255,255,255,0.08)"
        strokeWidth="1"
      />
      <rect x="148" y="70" width="4" height="290" fill="rgba(255,255,255,0.12)" />
      {[110, 140, 170, 200, 230, 260].map((y, i) => (
        <g key={i} opacity={0.15}>
          <path
            d={`M70 ${y} Q150 ${y + 15} 230 ${y}`}
            stroke="white"
            strokeWidth="1.2"
            fill="none"
          />
        </g>
      ))}
      <path d="M70 95 Q110 85 145 95" stroke="rgba(255,255,255,0.25)" strokeWidth="2" fill="none" />
      <path d="M155 95 Q190 85 230 95" stroke="rgba(255,255,255,0.25)" strokeWidth="2" fill="none" />
      <ellipse cx="130" cy="220" rx="38" ry="55" fill="rgba(255,255,255,0.06)" />
    </svg>
  );
}

function TrustBar() {
  return (
    <section className="px-6 py-10 border-y border-hairline bg-canvas">
      <div className="max-w-[1280px] mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="text-center">
            <p className="text-[28px] md:text-[34px] font-bold text-ink leading-none tracking-tight">99.2%</p>
            <p className="text-[12px] text-mute font-bold mt-1.5">Model Accuracy</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] md:text-[34px] font-bold text-ink leading-none tracking-tight">&lt; 3.0s</p>
            <p className="text-[12px] text-mute font-bold mt-1.5">Avg Inference Speed</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] md:text-[34px] font-bold text-ink leading-none tracking-tight">100%</p>
            <p className="text-[12px] text-mute font-bold mt-1.5">Tenant Isolation</p>
          </div>
          <div className="text-center">
            <p className="text-[28px] md:text-[34px] font-bold text-ink leading-none tracking-tight">24/7</p>
            <p className="text-[12px] text-mute font-bold mt-1.5">HIPAA Audit Trails</p>
          </div>
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    {
      step: "01",
      icon: <FileText className="w-5 h-5 text-ink" />,
      title: "Upload Scan",
      desc: "Instantly upload chest X-ray images (PNG, JPG, or DICOM) to a patient record.",
    },
    {
      step: "02",
      icon: <Brain className="w-5 h-5 text-ink" />,
      title: "Run AI Model",
      desc: "Neural network runs inference and computes multi-condition diagnostics in real time.",
    },
    {
      step: "03",
      icon: <Activity className="w-5 h-5 text-ink" />,
      title: "Verify Heatmap",
      desc: "Inspect localized Grad-CAM heatmaps showing exact regions of model attention.",
    },
  ];
  return (
    <section id="how" className="px-6 py-16 lg:py-20 bg-canvas">
      <div className="max-w-[1280px] mx-auto">
        <div className="text-center max-w-xl mx-auto mb-12">
          <p className="text-[11px] font-bold text-primary uppercase tracking-widest mb-2.5">Process Workflow</p>
          <h2 className="text-[24px] sm:text-[32px] font-bold text-ink tracking-tight">
            Clinical analysis in three steps
          </h2>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {steps.map((s, i) => (
            <div key={i} className="bg-surface-card rounded-md p-6 border border-hairline-soft">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[36px] font-bold text-ink/10 font-mono leading-none tracking-tight">{s.step}</span>
                <div className="w-9 h-9 rounded-full bg-canvas border border-hairline flex items-center justify-center">
                  {s.icon}
                </div>
              </div>
              <h3 className="text-[15px] font-bold text-ink mb-1.5 tracking-tight">{s.title}</h3>
              <p className="text-[13px] text-mute leading-relaxed font-semibold">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  const features = [
    {
      icon: <Database className="w-5 h-5 text-ink" />,
      title: "Isolated Databases",
      desc: "True database-per-hospital isolation ensuring patient security and HIPAA compliance."
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-ink" />,
      title: "Passwordless Passkeys",
      desc: "Log in quickly and securely using WebAuthn biometrics (Touch ID / Face ID)."
    },
    {
      icon: <Crosshair className="w-5 h-5 text-ink" />,
      title: "Explainable Heatmaps",
      desc: "Inspect specific visual interest zones highlighted by Grad-CAM attention maps."
    },
    {
      icon: <Users className="w-5 h-5 text-ink" />,
      title: "Role-Based Access",
      desc: "Differentiated workflows and permissions tailored for Doctors, Admins, and Superadmins."
    },
    {
      icon: <Clock className="w-5 h-5 text-ink" />,
      title: "Immediate Reporting",
      desc: "AI report summaries generated in bulleted, concise format for clinical speed."
    },
    {
      icon: <Lock className="w-5 h-5 text-ink" />,
      title: "HIPAA Compliant Uptime",
      desc: "Robust audit logs, complete backups, and automated secure patient roster invite onboarding."
    }
  ];

  return (
    <section id="features" className="px-6 py-16 lg:py-20 bg-surface-soft">
      <div className="max-w-[1280px] mx-auto">
        <div className="text-center max-w-xl mx-auto mb-12">
          <p className="text-[11px] font-bold text-primary uppercase tracking-widest mb-2.5">Capabilities</p>
          <h2 className="text-[24px] sm:text-[32px] font-bold text-ink tracking-tight">
            Designed for clinical standards
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <div key={i} className="bg-canvas border border-hairline rounded-md p-6 hover:bg-surface-card transition-colors duration-200">
              <div className="w-9 h-9 bg-surface-card rounded-md border border-hairline-soft flex items-center justify-center mb-4">
                {f.icon}
              </div>
              <h3 className="text-[15px] font-bold text-ink mb-1.5 tracking-tight">{f.title}</h3>
              <p className="text-[13px] text-mute leading-relaxed font-semibold">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CtaStrip() {
  return (
    <section className="px-6 py-12 bg-canvas">
      <div className="max-w-[1280px] mx-auto">
        <div className="bg-surface-dark rounded-md p-10 lg:p-14 text-center relative overflow-hidden">
          <div
            className="absolute -top-16 -right-16 w-56 h-56 rounded-full opacity-20"
            style={{ background: "radial-gradient(circle, var(--primary) 0%, transparent 70%)" }}
          />
          <div className="relative z-10">
            <h2 className="text-[22px] sm:text-[30px] font-bold text-white leading-tight mb-3 tracking-tight">
              Ready to modernize your radiology workflow?
            </h2>
            <p className="text-[13px] sm:text-[14px] text-white/70 mb-6 max-w-md mx-auto font-medium">
              Free plan includes up to 5 doctors and 100 scans per month. No credit card required.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                to="/register"
                className="h-10 px-5 inline-flex items-center justify-center gap-2 text-[12px] font-bold text-white bg-primary hover:bg-primary-pressed rounded-md transition-colors"
              >
                Start free trial
                <ArrowRight className="w-3.5 h-3.5" strokeWidth={2.5} />
              </Link>
              <Link
                to="/login"
                className="h-10 px-5 inline-flex items-center justify-center text-[12px] font-bold text-white bg-white/10 hover:bg-white/15 rounded-md transition-colors"
              >
                Sign in instead
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function SiteFooter() {
  return (
    <footer className="bg-canvas border-t border-hairline">
      <div className="max-w-[1280px] mx-auto px-6 py-10">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="w-7 h-7 rounded-md bg-primary flex items-center justify-center">
                <svg viewBox="0 0 24 24" className="w-[14px] h-[14px] text-white" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2l1.5 4.5L18 8l-4.5 1.5L12 14l-1.5-4.5L6 8l4.5-1.5z" />
                  <circle cx="12" cy="18" r="2" />
                </svg>
              </span>
              <span className="text-[14px] font-bold text-ink">AI X-Ray</span>
            </div>
            <p className="text-[12px] text-mute leading-relaxed font-semibold max-w-xs">
              AI-powered diagnostics with database-per-tenant architecture.
            </p>
          </div>
          <FooterCol title="Product" links={[["Features", "#features"], ["How it works", "#how"]]} />
          <FooterCol title="Portal" links={[["Sign in", "/login"], ["Create account", "/register"]]} />
          <FooterCol title="Policy" links={[["Privacy", "#"], ["Terms of service", "#"]]} />
        </div>
        <div className="pt-6 border-t border-hairline flex flex-col sm:flex-row justify-between items-center gap-3">
          <span className="text-[11px] text-mute font-semibold">© 2026 AI X-Ray Analyzer. All rights reserved.</span>
          <div className="flex gap-4 text-[11px] text-mute font-semibold">
            <a href="#" className="hover:text-ink">Status</a>
            <a href="#" className="hover:text-ink">HIPAA Audit Ready</a>
          </div>
        </div>
      </div>
    </footer>
  );
}

function FooterCol({ title, links }) {
  return (
    <div>
      <h4 className="text-[12px] font-bold text-ink mb-2.5">{title}</h4>
      <ul className="space-y-1.5">
        {links.map(([label, href]) => (
          <li key={label}>
            <a href={href} className="text-[12px] text-mute hover:text-ink font-semibold transition-colors">
              {label}
            </a>
          </li>
        ))}
      </ul>
    </div>
  );
}
