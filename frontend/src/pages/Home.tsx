import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Database, MessageSquare, Shield, Brain, Send, Layers, Search, Cpu, Upload, SlidersHorizontal } from 'lucide-react';
import './Home.css';

// ── 3D tilt card component ──────────────────────────────────────
const TiltCard = ({ children, className = '' }: { children: React.ReactNode; className?: string }) => {
  const ref = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const card = ref.current;
    if (!card) return;
    const { left, top, width, height } = card.getBoundingClientRect();
    const x = (e.clientX - left) / width;
    const y = (e.clientY - top)  / height;
    const rotX = (y - 0.5) * -16;
    const rotY = (x - 0.5) *  16;
    card.style.setProperty('--rx', `${rotX}deg`);
    card.style.setProperty('--ry', `${rotY}deg`);
    card.style.setProperty('--mx', `${x * 100}%`);
    card.style.setProperty('--my', `${y * 100}%`);
  };

  const handleMouseLeave = () => {
    const card = ref.current;
    if (!card) return;
    card.style.setProperty('--rx', '0deg');
    card.style.setProperty('--ry', '0deg');
  };

  return (
    <div
      ref={ref}
      className={`tilt-card ${className}`}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <div className="tilt-spotlight" />
      {children}
    </div>
  );
};

// ── Animated counter hook ──────────────────────────────────────
const useCounter = (target: number, duration: number, trigger: boolean) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!trigger) return;
    let startTime: number | null = null;
    const step = (ts: number) => {
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      const eased    = 1 - Math.pow(1 - progress, 3); // ease-out cubic
      setCount(Math.floor(eased * target));
      if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [trigger, target, duration]);
  return count;
};

// ── Stats Section Component ────────────────────────────────────
const StatsSection = () => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setInView(true); obs.disconnect(); } },
      { threshold: 0.25 }
    );
    if (sectionRef.current) obs.observe(sectionRef.current);
    return () => obs.disconnect();
  }, []);

  const c7   = useCounter(7,   1400, inView);
  const c3   = useCounter(3,   1200, inView);
  const c100 = useCounter(100, 1800, inView);

  return (
    <section className="stats-section" ref={sectionRef}>
      <div className="stats-bg" />

      {/* Top separator */}
      <div className="stats-separator" />

      <div className="stats-inner">
        <div className="section-header">
          <span className="section-label">By the numbers</span>
          <h2 className="section-title">Everything configured, nothing hidden</h2>
          <p className="section-subtitle">
            Each number represents a real capability you can tune — not a marketing promise.
          </p>
        </div>

        <div className="stats-grid">

          <div className={`stat-card ${inView ? 'stat-card-visible' : ''}`} style={{ animationDelay: '0ms' }}>
            <div className="stat-number">
              <span className="stat-digits">{c7}</span>
            </div>
            <div className="stat-label">Chunking Strategies</div>
            <p className="stat-desc">
              Fixed Size, Sliding Window, Sentence, Semantic, Token, Recursive, and Hybrid —
              pick the one that matches your document structure.
            </p>
            <div className="stat-bar stat-bar-indigo" style={{ width: `${(c7 / 7) * 100}%` }} />
          </div>

          <div className={`stat-card ${inView ? 'stat-card-visible' : ''}`} style={{ animationDelay: '120ms' }}>
            <div className="stat-number">
              <span className="stat-digits">{c3}</span>
            </div>
            <div className="stat-label">Vector Search Modes</div>
            <p className="stat-desc">
              Dense, Sparse, and Hybrid retrieval — each mode supports multiple swappable
              embedding models (FastEmbed, SPLADE, ColBERT) so you're never locked in.
            </p>
            <div className="stat-bar stat-bar-violet" style={{ width: `${(c3 / 3) * 100}%` }} />
          </div>

          <div className={`stat-card ${inView ? 'stat-card-visible' : ''}`} style={{ animationDelay: '240ms' }}>
            <div className="stat-number">
              <span className="stat-digits">{c100}</span>
              <span className="stat-suffix">%</span>
            </div>
            <div className="stat-label">Configurable LLM Backend</div>
            <p className="stat-desc">
              Groq is the default LLM provider for fast cloud inference, but you can swap in
              any compatible API or self-hosted model at any time.
            </p>
            <div className="stat-bar stat-bar-emerald" style={{ width: inView ? '100%' : '0%' }} />
          </div>

          <div className={`stat-card ${inView ? 'stat-card-visible' : ''}`} style={{ animationDelay: '360ms' }}>
            <div className="stat-number">
              <span className="stat-digits stat-inf">∞</span>
            </div>
            <div className="stat-label">Documents per KB</div>
            <p className="stat-desc">
              No artificial caps on your library size. Store, index, and query as many documents
              as your storage and compute allow.
            </p>
            <div className="stat-bar stat-bar-cyan" style={{ width: inView ? '100%' : '0%' }} />
          </div>

        </div>
      </div>
    </section>
  );
};

// ── Main page ───────────────────────────────────────────────────
const Home = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div className="home-container">

      {/* ── Glassmorphic Navbar ── */}
      <nav className={`navbar ${scrolled ? 'scrolled' : ''}`}>
        <div className="logo">
          <div className="logo-icon">
            <Brain size={18} color="#fff" />
          </div>
          <div className="logo-text">
            Personal&nbsp;<span>RAG</span>
          </div>
        </div>
        <div className="nav-links">
          <Link to="/login" className="nav-btn-ghost">Login</Link>
          <Link to="/signup" className="nav-btn-primary">
            <span>Get Started</span>
          </Link>
        </div>
      </nav>

      <div className="navbar-spacer" />

      {/* ── Hero Section ── */}
      <header className="hero">
        <div className="hero-bg">
          <div className="orb orb-1" />
          <div className="orb orb-2" />
          <div className="orb orb-3" />
          <div className="hero-grid-overlay" />
        </div>

        <div className="hero-inner">
          <div className="hero-left">
            <div className="hero-badge">
              <span className="badge-dot" />
              Powered by Advanced RAG Technology
            </div>

            <h1 className="hero-title">
              <span className="hero-title-line">Your Personal</span>
              <span className="hero-title-gradient">Knowledge&nbsp;Assistant</span>
            </h1>

            <p className="hero-subtitle">
              Transform any document collection into a living knowledge base.
              Ask questions in plain language and get precise, cited answers — powered by state-of-the-art
              language models and semantic retrieval.
            </p>

            <ul className="hero-highlights">
              <li><span className="check">✦</span> 7 intelligent chunking strategies</li>
              <li><span className="check">✦</span> Multiple LLM backends supported</li>
              <li><span className="check">✦</span> Dense, sparse &amp; hybrid vector search</li>
            </ul>

            <div className="hero-actions">
              <Link to="/signup" className="btn-hero-primary">
                Start for Free
                <span className="btn-arrow">→</span>
              </Link>
              <Link to="/login" className="btn-hero-outline">Sign In</Link>
            </div>
          </div>

          <div className="hero-right">
            <div className="card-scene">
              <div className="card-glow" />
              <div className="hero-card">
                <div className="card-header">
                  <div className="card-dots">
                    <span className="dot-red" />
                    <span className="dot-yellow" />
                    <span className="dot-green" />
                  </div>
                  <span className="card-title-label">AI Assistant — Research KB</span>
                </div>

                <div className="card-messages">
                  <div className="msg-row msg-row-user">
                    <div className="msg msg-user">
                      What is semantic chunking and when should I use it?
                    </div>
                  </div>
                  <div className="msg-row msg-row-ai">
                    <div className="msg-avatar"><Brain size={14} /></div>
                    <div className="msg msg-ai">
                      <strong>Semantic chunking</strong> splits documents based on meaning rather than fixed character counts.
                      Use it when your documents contain varied paragraph lengths or topic shifts —
                      it ensures each chunk represents a complete idea, improving retrieval accuracy. ✨
                    </div>
                  </div>
                  <div className="msg-row msg-row-user">
                    <div className="msg msg-user">Which embedding model gives the best results?</div>
                  </div>
                  <div className="msg-row msg-row-ai">
                    <div className="msg-avatar"><Brain size={14} /></div>
                    <div className="msg msg-ai typing-indicator">
                      <span /><span /><span />
                    </div>
                  </div>
                </div>

                <div className="card-input-row">
                  <input className="card-input" placeholder="Ask your knowledge base anything…" readOnly />
                  <button className="card-send-btn" aria-label="Send"><Send size={14} /></button>
                </div>
              </div>

              <div className="stat-chip chip-top-right">
                <span className="chip-dot chip-green" />
                <span>3 sources retrieved</span>
              </div>
              <div className="stat-chip chip-bottom-left">
                <span className="chip-dot chip-indigo" />
                <span>dense + sparse hybrid</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* ── STEP 4: Feature Cards ── */}
      <section className="features-section">
        <div className="section-header">
          <span className="section-label">What's inside</span>
          <h2 className="section-title">The full stack, exposed and configurable</h2>
          <p className="section-subtitle">
            FastAPI · Qdrant · PostgreSQL · MinIO · Celery · Redis · FastEmbed · Groq —
            every layer is open, tuneable, and production-ready.
          </p>
        </div>

        <div className="features-grid">

          <TiltCard>
            <div className="fc-icon fc-icon-indigo"><Database size={26} /></div>
            <h3 className="fc-title">Knowledge Bases</h3>
            <p className="fc-desc">
              Organise any number of document collections into isolated knowledge bases.
              Each KB has its own ingestion pipeline, embedding space, and access controls.
            </p>
            <ul className="fc-bullets">
              <li>Unlimited KBs per user</li>
              <li>PDF, TXT, MD, DOCX &amp; more</li>
              <li>Per-KB embedding &amp; chunking config</li>
            </ul>
          </TiltCard>

          <TiltCard>
            <div className="fc-icon fc-icon-violet"><Layers size={26} /></div>
            <h3 className="fc-title">7 Chunking Strategies</h3>
            <p className="fc-desc">
              Choose exactly how your documents are split — from simple fixed-size windows
              to meaning-aware semantic chunkers that preserve context across boundaries.
            </p>
            <ul className="fc-bullets">
              <li>Fixed Size &amp; Sliding Window</li>
              <li>Semantic &amp; Sentence-based</li>
              <li>Token, Recursive &amp; Hybrid</li>
            </ul>
          </TiltCard>

          <TiltCard>
            <div className="fc-icon fc-icon-cyan"><Search size={26} /></div>
            <h3 className="fc-title">Hybrid Vector Search</h3>
            <p className="fc-desc">
              Combine dense, sparse (SPLADE), and multi-vector (ColBERT) retrieval methods
              to maximise recall and precision across all query types.
            </p>
            <ul className="fc-bullets">
              <li>Dense embeddings via FastEmbed</li>
              <li>SPLADE sparse retrieval</li>
              <li>ColBERT multi-vector reranking</li>
            </ul>
          </TiltCard>

          <TiltCard>
            <div className="fc-icon fc-icon-emerald"><MessageSquare size={26} /></div>
            <h3 className="fc-title">AI Assistants</h3>
            <p className="fc-desc">
              Build custom chat assistants backed by your knowledge base. Configure the system
              prompt, search depth, and LLM model independently per assistant.
            </p>
            <ul className="fc-bullets">
              <li>Per-assistant instructions</li>
              <li>Multiple LLM backends</li>
              <li>Linked to any Knowledge Base</li>
            </ul>
          </TiltCard>

          <TiltCard>
            <div className="fc-icon fc-icon-orange"><Cpu size={26} /></div>
            <h3 className="fc-title">Async Processing</h3>
            <p className="fc-desc">
              Documents are ingested, chunked, and embedded in the background via Celery workers
              — uploads return instantly and the UI stays responsive for large files.
            </p>
            <ul className="fc-bullets">
              <li>Celery + Redis task queue</li>
              <li>Real-time processing status</li>
              <li>Re-process on config changes</li>
            </ul>
          </TiltCard>

          <TiltCard>
            <div className="fc-icon fc-icon-rose"><Shield size={26} /></div>
            <h3 className="fc-title">Secure &amp; Private</h3>
            <p className="fc-desc">
              JWT-authenticated API with strict per-user data isolation. Files are stored
              in MinIO object storage — your data never leaves your own infrastructure.
            </p>
            <ul className="fc-bullets">
              <li>JWT access tokens</li>
              <li>User-isolated data stores</li>
              <li>Groq API (cloud) or local LLM</li>
            </ul>
          </TiltCard>

        </div>
      </section>

      {/* ── STEP 5: How It Works ── */}
      <section className="how-section">
        {/* background band */}
        <div className="how-bg" />

        <div className="how-inner">
          <div className="section-header">
            <span className="section-label">Simple by design</span>
            <h2 className="section-title">From documents to answers in minutes</h2>
            <p className="section-subtitle">
              Three steps. No ML expertise required. Upload your documents,
              tune your pipeline, and start getting precise answers.
            </p>
          </div>

          <div className="how-steps">

            {/* Step 1 */}
            <div className="how-step">
              <div className="step-num step-num-1">01</div>
              <div className="step-icon-wrap step-iw-indigo">
                <Upload size={28} />
              </div>
              <div className="step-body">
                <h3 className="step-title">Upload Your Documents</h3>
                <p className="step-desc">
                  Drop in PDFs, plain text, Markdown, or Word files.
                  The system extracts, cleans, and queues them for processing
                  automatically — no preprocessing needed on your end.
                </p>
                <ul className="step-bullets">
                  <li>PDF, TXT, MD, DOCX supported</li>
                  <li>Multiple files at once</li>
                  <li>Real-time processing status</li>
                </ul>
              </div>
            </div>

            {/* Animated connector */}
            <div className="how-connector" aria-hidden="true">
              <div className="connector-track">
                <div className="connector-fill" />
              </div>
              <div className="connector-arrow">›</div>
            </div>

            {/* Step 2 */}
            <div className="how-step">
              <div className="step-num step-num-2">02</div>
              <div className="step-icon-wrap step-iw-violet">
                <SlidersHorizontal size={28} />
              </div>
              <div className="step-body">
                <h3 className="step-title">Configure Your Pipeline</h3>
                <p className="step-desc">
                  Choose a chunking strategy, pick an embedding model, and tune
                  retrieval parameters. Every knob is exposed — or leave it all
                  at sensible defaults for immediate results.
                </p>
                <ul className="step-bullets">
                  <li>7 chunking strategies</li>
                  <li>Dense, sparse &amp; hybrid search</li>
                  <li>Re-process instantly on changes</li>
                </ul>
              </div>
            </div>

            {/* Animated connector */}
            <div className="how-connector" aria-hidden="true">
              <div className="connector-track">
                <div className="connector-fill connector-fill-delay" />
              </div>
              <div className="connector-arrow">›</div>
            </div>

            {/* Step 3 */}
            <div className="how-step">
              <div className="step-num step-num-3">03</div>
              <div className="step-icon-wrap step-iw-emerald">
                <MessageSquare size={28} />
              </div>
              <div className="step-body">
                <h3 className="step-title">Chat &amp; Get Answers</h3>
                <p className="step-desc">
                  Ask questions in natural language. The assistant retrieves
                  the most relevant chunks, constructs a grounded response,
                  and tells you exactly where each answer came from.
                </p>
                <ul className="step-bullets">
                  <li>Source-cited answers</li>
                  <li>Multiple LLM backends</li>
                  <li>Persistent chat history</li>
                </ul>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── STEP 6: Use Cases ── */}
      <section className="usecases-section">
        <div className="usecases-inner">
          <div className="section-header">
            <span className="section-label">Real-world applications</span>
            <h2 className="section-title">Built for every use case</h2>
            <p className="section-subtitle">
              Whether you're a researcher, a business team, or an individual — Personal RAG
              adapts to your domain and your documents.
            </p>
          </div>

          <div className="usecases-grid">

            {/* Card 1 — Research */}
            <div className="uc-card">
              <div className="uc-top-bar uc-bar-indigo" />
              <div className="uc-head">
                <span className="uc-emoji">🔬</span>
                <span className="uc-industry">Academia &amp; Research</span>
              </div>
              <h3 className="uc-title">Research Paper Assistant</h3>
              <p className="uc-desc">
                Upload hundreds of academic papers and instantly query findings, methodologies,
                and citations across your entire library. No more Ctrl+F through 80-page PDFs.
              </p>
              <div className="uc-demo">
                <div className="uc-q">
                  <span className="uc-q-label">You</span>
                  What did the 2023 studies conclude about transformer attention scaling?
                </div>
                <div className="uc-a">
                  <span className="uc-a-label">Assistant</span>
                  Three papers in your KB converge on the finding that attention head count scales
                  sub-linearly with model capacity after 32 heads…
                  <span className="uc-cite">— Source: scaling_laws_2023.pdf, p.7</span>
                </div>
              </div>
              <div className="uc-tags">
                <span className="uc-tag uc-tag-indigo">Semantic Chunking</span>
                <span className="uc-tag uc-tag-indigo">Dense Search</span>
                <span className="uc-tag uc-tag-indigo">GPT-4</span>
              </div>
            </div>

            {/* Card 2 — Corporate */}
            <div className="uc-card">
              <div className="uc-top-bar uc-bar-violet" />
              <div className="uc-head">
                <span className="uc-emoji">🏢</span>
                <span className="uc-industry">Corporate &amp; HR</span>
              </div>
              <h3 className="uc-title">Company Knowledge Bot</h3>
              <p className="uc-desc">
                Give your team instant answers from internal wikis, policy documents, SOPs,
                and onboarding materials — without ever leaving their workflow.
              </p>
              <div className="uc-demo">
                <div className="uc-q">
                  <span className="uc-q-label">You</span>
                  What's the remote work policy for contractors in the EU?
                </div>
                <div className="uc-a">
                  <span className="uc-a-label">Assistant</span>
                  Per the 2024 Remote Work Policy (Section 4.2), EU contractors may work remotely
                  up to 180 days per year, provided they comply with local tax obligations…
                  <span className="uc-cite">— Source: hr_policy_2024.pdf, p.12</span>
                </div>
              </div>
              <div className="uc-tags">
                <span className="uc-tag uc-tag-violet">Fixed-size Chunking</span>
                <span className="uc-tag uc-tag-violet">Hybrid Search</span>
                <span className="uc-tag uc-tag-violet">GPT-3.5 Turbo</span>
              </div>
            </div>

            {/* Card 3 — Legal */}
            <div className="uc-card">
              <div className="uc-top-bar uc-bar-emerald" />
              <div className="uc-head">
                <span className="uc-emoji">⚖️</span>
                <span className="uc-industry">Legal &amp; Compliance</span>
              </div>
              <h3 className="uc-title">Contract Analyzer</h3>
              <p className="uc-desc">
                Upload contracts, NDAs, and compliance documents. Extract key clauses,
                identify obligations, and surface critical deadlines before they sneak up on you.
              </p>
              <div className="uc-demo">
                <div className="uc-q">
                  <span className="uc-q-label">You</span>
                  Does any vendor contract include an auto-renewal clause?
                </div>
                <div className="uc-a">
                  <span className="uc-a-label">Assistant</span>
                  Yes — 3 of your 14 vendor contracts contain auto-renewal clauses.
                  Acme Corp (Clause 8.3) renews annually unless cancelled 60 days prior…
                  <span className="uc-cite">— Sources: acme_contract.pdf, techvend_msa.pdf</span>
                </div>
              </div>
              <div className="uc-tags">
                <span className="uc-tag uc-tag-emerald">Recursive Chunking</span>
                <span className="uc-tag uc-tag-emerald">Sparse (SPLADE)</span>
                <span className="uc-tag uc-tag-emerald">GPT-4</span>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* ── STEP 7: Stats / Social Proof ── */}
      <StatsSection />

      {/* ── Closing CTA Banner ── */}
      <section className="cta-section">
        <div className="cta-glow" />
        <div className="cta-inner">
          <h2 className="cta-title">Ready to build your knowledge base?</h2>
          <p className="cta-subtitle">
            Start for free. No credit card required. Your data stays on your infrastructure.
          </p>
          <div className="cta-actions">
            <Link to="/signup" className="btn-hero-primary">
              Create Your First KB
              <span className="btn-arrow">→</span>
            </Link>
            <Link to="/login" className="btn-hero-outline">Already have an account?</Link>
          </div>
        </div>
      </section>

    </div>
  );
};

export default Home;
