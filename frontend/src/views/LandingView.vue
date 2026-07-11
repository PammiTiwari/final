<template>
  <div class="landing">
    <!-- Navbar -->
    <nav class="land-nav">
      <div class="land-brand">
        <div class="brand-icon">CP</div>
        <span class="brand-name">Cyber Panchayat</span>
      </div>
      <div class="nav-links">
        <a href="#home">Home</a>
        <a href="#services">Services</a>
        <a href="#about">About Us</a>
        <a href="#contact">Contact</a>
      </div>
      <div class="nav-actions">
        <router-link to="/login" class="btn-nav-login">Login</router-link>
        <router-link to="/register" class="btn-nav-register">Register</router-link>
      </div>
    </nav>

    <!-- Hero -->
    <section class="hero" id="home">
      <div class="hero-content">
        <div class="hero-left">
          <div class="hero-tag"><span class="hero-tag-dot"></span>Smart City Portal</div>
          <h1 class="hero-title">Together, We<br>Make Our City<br><span class="hero-accent gradient-text">Better</span></h1>
          <p class="hero-subtitle">Report civic issues, track resolutions, and connect with your community. Cyber Panchayat makes it easy to collaborate with local authorities.</p>
          <div class="hero-btns">
            <router-link to="/register" class="btn-hero-primary">Submit a Complaint</router-link>
            <router-link to="/track" class="btn-hero-outline">Track Complaint</router-link>
          </div>
        </div>
        <div class="hero-right">
          <svg viewBox="0 0 500 380" xmlns="http://www.w3.org/2000/svg" class="hero-svg">
            <!-- Sky gradient -->
            <defs>
              <linearGradient id="skyGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#E8EFFF"/>
                <stop offset="100%" stop-color="#FAFAFA"/>
              </linearGradient>
            </defs>
            <rect width="500" height="380" fill="url(#skyGrad)" rx="16"/>
            <!-- Sun -->
            <circle cx="400" cy="70" r="40" fill="#4D7CFF" opacity="0.18"/>
            <!-- Mountains -->
            <polygon points="0,280 120,140 240,280" fill="#94B2FF" opacity="0.4"/>
            <polygon points="100,280 220,120 340,280" fill="#6E94F2" opacity="0.45"/>
            <polygon points="250,280 370,150 490,280" fill="#3D63D6" opacity="0.5"/>
            <!-- Ground -->
            <rect x="0" y="280" width="500" height="100" fill="#E2E8F0" opacity="0.6"/>
            <!-- Buildings -->
            <rect x="30" y="190" width="50" height="90" fill="#0F172A" rx="2"/>
            <rect x="90" y="210" width="40" height="70" fill="#1E3A8A" rx="2"/>
            <rect x="140" y="200" width="35" height="80" fill="#0F172A" rx="2"/>
            <!-- Windows -->
            <rect x="38" y="198" width="8" height="8" fill="#4D7CFF" opacity="0.8"/>
            <rect x="50" y="198" width="8" height="8" fill="#4D7CFF" opacity="0.8"/>
            <rect x="62" y="198" width="8" height="8" fill="#4D7CFF" opacity="0.5"/>
            <rect x="38" y="215" width="8" height="8" fill="#4D7CFF" opacity="0.8"/>
            <rect x="50" y="215" width="8" height="8" fill="#4D7CFF" opacity="0.3"/>
            <rect x="62" y="215" width="8" height="8" fill="#4D7CFF" opacity="0.8"/>
            <!-- Road -->
            <rect x="0" y="310" width="500" height="20" fill="#CBD5E1" opacity="0.5"/>
            <rect x="60" y="317" width="30" height="4" fill="#fff" opacity="0.8" rx="2"/>
            <rect x="130" y="317" width="30" height="4" fill="#fff" opacity="0.8" rx="2"/>
            <rect x="200" y="317" width="30" height="4" fill="#fff" opacity="0.8" rx="2"/>
            <!-- City Hall -->
            <rect x="310" y="170" width="100" height="110" fill="#0F172A" rx="2"/>
            <polygon points="310,170 360,140 410,170" fill="#0F172A"/>
            <rect x="340" y="220" width="40" height="60" fill="#1E3A8A"/>
            <!-- Flag -->
            <line x1="360" y1="140" x2="360" y2="110" stroke="#94B2FF" stroke-width="2"/>
            <polygon points="360,110 385,120 360,130" fill="#0052FF" opacity="0.9"/>
            <!-- Windows city hall -->
            <rect x="320" y="180" width="16" height="14" fill="#4D7CFF" opacity="0.7" rx="1"/>
            <rect x="345" y="180" width="16" height="14" fill="#4D7CFF" opacity="0.7" rx="1"/>
            <rect x="370" y="180" width="16" height="14" fill="#4D7CFF" opacity="0.4" rx="1"/>
            <rect x="395" y="180" width="12" height="14" fill="#4D7CFF" opacity="0.7" rx="1"/>
            <!-- Tree -->
            <rect x="260" y="265" width="6" height="25" fill="#64748B" opacity="0.6"/>
            <circle cx="263" cy="255" r="18" fill="#0052FF" opacity="0.45"/>
            <rect x="460" y="265" width="6" height="25" fill="#64748B" opacity="0.6"/>
            <circle cx="463" cy="255" r="16" fill="#0052FF" opacity="0.4"/>
          </svg>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="how-it-works" id="services">
      <div class="section-container">
        <h2 class="section-title-lg">How It Works</h2>
        <p class="section-sub">Simple steps to resolve civic issues in your city</p>
        <div class="steps-grid">
          <div class="step-card">
            <div class="step-num">1</div>
            <h3>Submit</h3>
            <p>Report an issue with details and photos from anywhere, anytime</p>
          </div>
          <div class="step-card">
            <div class="step-num">2</div>
            <h3>Assign</h3>
            <p>We assign it to the right department for quick action</p>
          </div>
          <div class="step-card">
            <div class="step-num">3</div>
            <h3>Action</h3>
            <p>Officers take action and update status regularly</p>
          </div>
          <div class="step-card">
            <div class="step-num">4</div>
            <h3>Resolve</h3>
            <p>Issue resolved and you get notified instantly</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Contact -->
    <section class="land-contact" id="contact">
      <div class="section-container">
        <h2 class="section-title-lg">Contact Us</h2>
        <p class="section-sub">Have a question or need help? Reach out to the admin office.</p>
        <div class="contact-grid">
          <a v-if="stats.admin_email" :href="`mailto:${stats.admin_email}`" class="contact-card">
            <span class="contact-icon">✉️</span>
            <div>
              <div class="contact-label">Email</div>
              <div class="contact-value">{{ stats.admin_email }}</div>
            </div>
          </a>
          <a v-if="stats.admin_phone" :href="`tel:+91${stats.admin_phone}`" class="contact-card">
            <span class="contact-icon">📞</span>
            <div>
              <div class="contact-label">Phone</div>
              <div class="contact-value">{{ fmtPhone(stats.admin_phone) }}</div>
            </div>
          </a>
        </div>
      </div>
    </section>

    <!-- Stats -->
    <section class="land-stats">
      <div class="stats-container">
        <div class="stat-item">
          <div class="stat-big">{{ fmtNum(stats.total_complaints) }}</div>
          <div class="stat-lbl">Complaints</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-big">{{ fmtNum(stats.resolved) }}</div>
          <div class="stat-lbl">Resolved</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-big">{{ fmtNum(stats.in_progress) }}</div>
          <div class="stat-lbl">In Progress</div>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <div class="stat-big">{{ fmtNum(stats.departments) }}</div>
          <div class="stat-lbl">Departments</div>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="land-footer">
      <p>&copy; 2026 Cyber Panchayat. Making cities better together.</p>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import api from '../api'

const stats = ref({})

function fmtNum(n) {
  return typeof n === 'number' ? n.toLocaleString('en-IN') : '—'
}

function fmtPhone(p) {
  return p && p.length === 10 ? `+91 ${p.slice(0, 5)} ${p.slice(5)}` : p
}

onMounted(() => {
  api.get('/public-stats').then(res => { stats.value = res.data }).catch(() => {})
})
</script>

<style scoped>
.landing { min-height: 100vh; background: var(--bg); font-family: var(--font-body); }

/* Navbar */
.land-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 3rem;
  background: rgba(255,255,255,0.85);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 100;
}
.land-brand { display: flex; align-items: center; gap: 0.65rem; }
.brand-icon {
  width: 30px; height: 30px; background: var(--gradient-accent); color: #fff;
  border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.62rem; box-shadow: var(--shadow-accent);
}
.brand-name { font-family: var(--font-heading); font-weight: 400; font-size: 1.05rem; color: var(--text); }
.nav-links { display: flex; gap: 2rem; }
.nav-links a { font-size: 0.875rem; font-weight: 500; color: var(--text-muted); transition: var(--transition); position: relative; }
.nav-links a::after {
  content: ''; position: absolute; left: 0; bottom: -6px; width: 0; height: 2px;
  background: var(--gradient-accent); transition: width var(--transition);
}
.nav-links a:hover { color: var(--text); }
.nav-links a:hover::after { width: 100%; }
.nav-actions { display: flex; gap: 0.6rem; align-items: center; }
.btn-nav-login {
  padding: 0.45rem 1.1rem; font-size: 0.875rem; font-weight: 600;
  border: 1px solid var(--border); border-radius: var(--radius-sm); color: var(--text);
  transition: var(--transition);
}
.btn-nav-login:hover { border-color: var(--primary); color: var(--primary); background: var(--accent); }
.btn-nav-register {
  padding: 0.45rem 1.1rem; font-size: 0.875rem; font-weight: 600;
  background: var(--gradient-accent); color: #fff; border-radius: var(--radius-sm);
  transition: var(--transition); box-shadow: var(--shadow-accent);
}
.btn-nav-register:hover { filter: brightness(1.08); transform: translateY(-1px); box-shadow: var(--shadow-accent-lg); }

/* Hero */
.hero { background: var(--bg); padding: 5rem 3rem; position: relative; overflow: hidden; }
.hero::before {
  content: ''; position: absolute; top: -120px; right: -120px; width: 380px; height: 380px;
  border-radius: 50%; background: var(--accent-secondary); opacity: 0.12; filter: blur(80px);
}
.hero-content {
  max-width: 1120px; margin: 0 auto; position: relative; z-index: 1;
  display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 3rem; align-items: center;
}
.hero-tag {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: var(--accent); color: var(--primary); border: 1px solid rgba(0,82,255,0.25);
  padding: 0.3rem 0.85rem; border-radius: 100px;
  font-family: var(--font-mono); font-size: 0.68rem; font-weight: 600;
  letter-spacing: 0.13em; text-transform: uppercase;
  margin-bottom: 1.25rem;
}
.hero-tag-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--primary); animation: pulse-dot 2s infinite; flex-shrink: 0; }
.hero-title { font-family: var(--font-heading); font-size: 3.1rem; font-weight: 400; line-height: 1.12; letter-spacing: -0.01em; color: var(--text); margin-bottom: 1.1rem; }
.hero-subtitle { font-size: 1.02rem; color: var(--text-muted); line-height: 1.7; margin-bottom: 1.85rem; max-width: 420px; }
.hero-btns { display: flex; gap: 0.85rem; flex-wrap: wrap; }
.btn-hero-primary {
  padding: 0.75rem 1.6rem; background: var(--gradient-accent); color: #fff;
  border-radius: var(--radius); font-size: 0.9rem; font-weight: 700; transition: var(--transition);
  box-shadow: var(--shadow-accent);
}
.btn-hero-primary:hover { filter: brightness(1.08); transform: translateY(-1px); box-shadow: var(--shadow-accent-lg); }
.btn-hero-outline {
  padding: 0.75rem 1.6rem;
  border: 1px solid var(--border); color: var(--text);
  border-radius: var(--radius); font-size: 0.9rem; font-weight: 700; transition: var(--transition);
}
.btn-hero-outline:hover { border-color: var(--primary); color: var(--primary); background: var(--accent); }
.hero-svg { width: 100%; border-radius: var(--radius-lg); box-shadow: var(--shadow-float); }

/* How it works */
.how-it-works { padding: 5rem 3rem; background: var(--card); }
.section-container { max-width: 1120px; margin: 0 auto; }
.section-title-lg { font-family: var(--font-heading); font-size: 2rem; font-weight: 400; color: var(--text); text-align: center; margin-bottom: 0.5rem; }
.section-sub { text-align: center; color: var(--text-muted); font-size: 0.95rem; margin-bottom: 3rem; }
.steps-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
.step-card {
  text-align: center; padding: 1.85rem 1.25rem;
  border: 1px solid var(--border); border-radius: var(--radius-lg); transition: var(--transition);
  background: var(--bg);
}
.step-card:hover { box-shadow: var(--shadow-hover); transform: translateY(-3px); border-color: rgba(0,82,255,0.25); }
.step-num {
  width: 44px; height: 44px;
  background: var(--gradient-accent); color: #fff;
  border-radius: var(--radius-sm); display: flex; align-items: center; justify-content: center;
  font-family: var(--font-mono); font-size: 1.1rem; font-weight: 700; margin: 0 auto 0.9rem;
  box-shadow: var(--shadow-accent);
}
.step-card h3 { font-family: var(--font-heading); font-size: 1.05rem; font-weight: 400; color: var(--text); margin-bottom: 0.5rem; }
.step-card p { font-size: 0.85rem; color: var(--text-muted); line-height: 1.6; }

/* Stats — inverted contrast section */
.land-stats {
  background: var(--surface-dark);
  background-image: radial-gradient(circle, rgba(255,255,255,0.06) 1px, transparent 1px);
  background-size: 28px 28px;
  padding: 3rem 3rem;
}
.stats-container { max-width: 920px; margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: 0; }
.stat-item { text-align: center; flex: 1; padding: 0.5rem 1.5rem; }
.stat-big { font-family: var(--font-heading); font-size: 2.2rem; font-weight: 400; color: #fff; }
.stat-lbl { font-family: var(--font-mono); font-size: 0.7rem; letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent-secondary); font-weight: 500; margin-top: 0.35rem; }
.stat-divider { width: 1px; height: 50px; background: rgba(255,255,255,0.12); flex-shrink: 0; }

/* Contact */
.land-contact { padding: 5rem 3rem; background: var(--bg); }
.contact-grid { display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap; }
.contact-card {
  display: flex; align-items: center; gap: 0.9rem;
  padding: 1.25rem 1.75rem; min-width: 260px;
  background: var(--card); border: 1px solid var(--border); border-radius: var(--radius-lg);
  transition: var(--transition);
}
.contact-card:hover { border-color: rgba(0,82,255,0.25); box-shadow: var(--shadow-hover); transform: translateY(-2px); }
.contact-icon {
  width: 42px; height: 42px; flex-shrink: 0;
  background: var(--accent); border-radius: var(--radius-sm);
  display: flex; align-items: center; justify-content: center; font-size: 1.2rem;
}
.contact-label { font-size: 0.72rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.06em; color: var(--text-muted); }
.contact-value { font-size: 0.95rem; font-weight: 600; color: var(--text); margin-top: 0.15rem; }

/* Footer */
.land-footer { padding: 1.5rem 3rem; background: var(--card); text-align: center; color: var(--text-muted); font-size: 0.85rem; border-top: 1px solid var(--border); }

@media (max-width: 900px) {
  .hero-content { grid-template-columns: 1fr; }
  .hero-right { display: none; }
  .steps-grid { grid-template-columns: repeat(2, 1fr); }
  .stats-container { flex-wrap: wrap; }
}
@media (max-width: 480px) {
  .land-nav { padding: 0.85rem 1.25rem; }
  .nav-links { display: none; }
  .hero { padding: 3rem 1.25rem; }
  .hero-title { font-size: 2.1rem; }
  .how-it-works, .land-stats, .land-footer { padding-left: 1.25rem; padding-right: 1.25rem; }
  .steps-grid { grid-template-columns: 1fr; }
  .stat-divider { display: none; }
}
</style>
