"""
Custom CSS styles for the Manufacturing Investigation Copilot.
Provides a modern, enterprise-grade UI matching the React reference design.
Supports both light and dark Streamlit themes.
"""

CUSTOM_CSS = """    
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ============================================
   CSS Custom Properties (Theme-Aware)
   Streamlit uses [data-testid="stAppViewContainer"]
   with background color to indicate theme
   ============================================ */

/* Light theme (default) */
.stApp, [data-testid="stAppViewContainer"] {
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --text-faint: #94a3b8;
    --border-color: #e2e8f0;
    --border-light: #f1f5f9;
    --shadow-color: rgba(0,0,0,0.05);
    --shadow-medium: rgba(0,0,0,0.1);

    /* Brand colors (same in both themes) */
    --primary-blue: #2563eb;
    --primary-blue-hover: #1d4ed8;
    --primary-indigo: #4f46e5;
    --success-green: #22c55e;
    --priority-critical: #ef4444;
    --priority-high: #f97316;
    --priority-medium: #fbbf24;
    --priority-low: #22c55e;

    /* NLP badge */
    --nlp-bg: #dbeafe;
    --nlp-text: #1d4ed8;
}

/* Dark theme - detect via Streamlit's dark background colors */
[data-testid="stAppViewContainer"][style*="background-color: rgb(14"],
[data-testid="stAppViewContainer"][style*="background-color: rgb(17"],
[data-testid="stAppViewContainer"][style*="background-color: rgb(38"],
[data-testid="stAppViewContainer"][style*="background-color: rgb(49"],
.stApp[data-theme="dark"],
[data-theme="dark"] {
    --bg-primary: #1e293b !important;
    --bg-secondary: #0f172a !important;
    --bg-tertiary: #334155 !important;
    --text-primary: #f1f5f9 !important;
    --text-secondary: #cbd5e1 !important;
    --text-muted: #94a3b8 !important;
    --text-faint: #64748b !important;
    --border-color: #334155 !important;
    --border-light: #475569 !important;
    --shadow-color: rgba(0,0,0,0.3) !important;
    --shadow-medium: rgba(0,0,0,0.4) !important;
    --nlp-bg: #1e3a5f !important;
    --nlp-text: #60a5fa !important;
}

/* Fallback: Use prefers-color-scheme */
@media (prefers-color-scheme: dark) {
    .stApp, [data-testid="stAppViewContainer"] {
        --bg-primary: #1e293b;
        --bg-secondary: #0f172a;
        --bg-tertiary: #334155;
        --text-primary: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #94a3b8;
        --text-faint: #64748b;
        --border-color: #334155;
        --border-light: #475569;
        --shadow-color: rgba(0,0,0,0.3);
        --shadow-medium: rgba(0,0,0,0.4);
        --nlp-bg: #1e3a5f;
        --nlp-text: #60a5fa;
    }
}

/* ============================================
   Global Styles
   ============================================ */

.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide default Streamlit header */
header[data-testid="stHeader"] {
    background: transparent;
}

/* ============================================
   Custom Header
   ============================================ */

.custom-header {
    background-color: var(--bg-primary) !important;
    border-bottom: 1px solid var(--border-color) !important;
    padding: 0.75rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem;
    box-shadow: 0 1px 3px var(--shadow-color);
}

.header-logo {
    background: var(--primary-blue);
    padding: 0.5rem;
    border-radius: 0.5rem;
    display: inline-flex;
}

.header-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
    line-height: 1.2;
}

.header-subtitle {
    font-size: 0.65rem;
    color: var(--text-muted);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.header-user {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.header-user-info {
    text-align: right;
}

.header-user-name {
    font-size: 0.875rem;
    font-weight: 600;
    margin: 0;
    color: var(--text-primary);
}

.header-user-site {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin: 0;
}

.header-avatar {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    background: var(--bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    color: var(--text-muted);
}

/* ============================================
   Card Styles
   ============================================ */

.custom-card {
    background-color: var(--bg-primary) !important;
    border-radius: 0.75rem;
    border: 1px solid var(--border-color) !important;
    box-shadow: 0 1px 3px var(--shadow-color);
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.card-header {
    background-color: var(--bg-secondary) !important;
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid var(--border-color) !important;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-header svg {
    color: var(--text-muted) !important;
}

.card-header svg[stroke="currentColor"] {
    stroke: var(--text-muted) !important;
}

.card-header-text {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary) !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.card-body {
    padding: 1.5rem;
    background-color: var(--bg-primary) !important;
}

/* ============================================
   Section Titles
   ============================================ */

.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
}

.section-subtitle {
    color: var(--text-muted);
    margin-bottom: 1.5rem;
}

/* ============================================
   Severity Toggle
   ============================================ */

.severity-toggle {
    display: flex;
    background: var(--bg-tertiary);
    padding: 0.25rem;
    border-radius: 0.5rem;
    gap: 0.25rem;
}

.severity-btn {
    flex: 1;
    padding: 0.375rem 0.75rem;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
}

.severity-btn-active {
    background: var(--bg-primary);
    color: var(--text-primary);
    box-shadow: 0 1px 2px var(--shadow-color);
}

.severity-btn-high {
    background: #dc2626;
    color: white;
}

/* ============================================
   Results Header Card (Gradient - same in both themes)
   ============================================ */

.results-header {
    background: linear-gradient(135deg, var(--primary-blue) 0%, var(--primary-indigo) 100%);
    border-radius: 0.75rem 0.75rem 0 0;
    padding: 1.5rem 2rem;
    color: white;
}

.diagnosis-badge {
    background: rgba(255,255,255,0.2);
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    display: inline-block;
    margin-bottom: 1rem;
}

.priority-badge {
    background: var(--priority-medium);
    color: #78350f;
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.priority-critical { background: var(--priority-critical); color: white; }
.priority-high { background: var(--priority-high); color: white; }
.priority-medium { background: var(--priority-medium); color: #78350f; }
.priority-low { background: var(--priority-low); color: white; }

.diagnosis-title {
    font-size: 1.875rem;
    font-weight: 800;
    margin: 0.5rem 0 0.25rem 0;
    color: white;
}

.diagnosis-subtitle {
    color: rgba(255,255,255,0.8);
    font-size: 1.125rem;
}

/* ============================================
   Confidence Score
   ============================================ */

.confidence-section {
    padding: 2rem;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-light);
}

.confidence-label {
    font-size: 0.65rem;
    font-weight: 700;
    color: var(--text-faint);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

.confidence-value {
    font-size: 2.5rem;
    font-weight: 900;
    color: var(--text-primary);
    letter-spacing: -0.025em;
}

.confidence-bar {
    width: 8rem;
    height: 0.75rem;
    background: var(--bg-tertiary);
    border-radius: 9999px;
    overflow: hidden;
}

.confidence-fill {
    height: 100%;
    background: var(--success-green);
    border-radius: 9999px;
}

/* ============================================
   Action Steps
   ============================================ */

.action-step {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-light);
    border-radius: 0.5rem;
    margin-bottom: 0.75rem;
    transition: border-color 0.2s;
}

.action-step:hover {
    border-color: #60a5fa;
}

.step-number {
    width: 2rem;
    height: 2rem;
    background: var(--primary-blue);
    color: white;
    border-radius: 9999px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.875rem;
    flex-shrink: 0;
}

.step-content h4 {
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.25rem 0;
}

.step-content p {
    font-size: 0.875rem;
    color: var(--text-muted);
    margin: 0;
}

/* ============================================
   Sidebar Card
   ============================================ */

.sidebar-card {
    background: var(--bg-primary);
    border-radius: 0.75rem;
    border: 1px solid var(--border-color);
    padding: 1.5rem;
    margin-bottom: 1rem;
}

.sidebar-dark {
    background: #1e293b;
    color: white;
    border: none;
}

.sidebar-title {
    font-size: 0.75rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 1rem;
    color: var(--text-faint);
}

/* ============================================
   Meta Info
   ============================================ */

.meta-row {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-light);
    font-size: 0.875rem;
}

.meta-label {
    color: var(--text-faint);
}

.meta-value {
    font-family: 'Monaco', 'Consolas', monospace;
    color: var(--text-primary);
}

/* ============================================
   Loading Overlay
   ============================================ */

.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: var(--bg-primary);
    opacity: 0.95;
    backdrop-filter: blur(8px);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 9999;
}

.loading-spinner {
    width: 6rem;
    height: 6rem;
    border: 4px solid var(--bg-tertiary);
    border-top-color: var(--primary-blue);
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

.loading-text {
    margin-top: 2rem;
    text-align: center;
}

.loading-text h3 {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 0.5rem 0;
}

.loading-text p {
    color: var(--text-muted);
}

/* ============================================
   Button Styles
   ============================================ */

.primary-btn {
    background: var(--primary-blue);
    color: white;
    padding: 0.625rem 2.5rem;
    border-radius: 0.5rem;
    font-weight: 700;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
    transition: all 0.2s;
}

.primary-btn:hover {
    background: var(--primary-blue-hover);
}

/* ============================================
   Form Label
   ============================================ */

.form-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}

/* ============================================
   NLP Badge
   ============================================ */

.nlp-badge {
    background: var(--nlp-bg);
    color: var(--nlp-text);
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    letter-spacing: 0.025em;
}

/* ============================================
   Footer
   ============================================ */

.custom-footer {
    background-color: var(--bg-primary) !important;
    border-top: 1px solid var(--border-color) !important;
    padding: 1rem 2rem;
    text-align: center;
    margin: 2rem -1rem -1rem -1rem;
}

.footer-text {
    font-size: 0.625rem;
    color: var(--text-faint) !important;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* ============================================
   Streamlit Widget Overrides
   ============================================ */

.stSelectbox > div > div {
    border-radius: 0.5rem;
}

.stTextArea > div > div > textarea {
    border-radius: 0.5rem;
}

.stNumberInput > div > div > input {
    border-radius: 0.5rem;
}

div[data-testid="stForm"] {
    border: none;
    padding: 0;
}

/* Hide form border */
section[data-testid="stForm"] > div {
    border: none !important;
    padding: 0 !important;
}

/* ============================================
   Additional Theme-Aware Helpers
   ============================================ */

.text-primary { color: var(--text-primary); }
.text-secondary { color: var(--text-secondary); }
.text-muted { color: var(--text-muted); }
.bg-primary { background: var(--bg-primary); }
.bg-secondary { background: var(--bg-secondary); }
</style>
"""


def inject_custom_css():
    """Inject custom CSS with JavaScript-based theme detection that follows Streamlit's UI theme."""
    import streamlit as st

    # JavaScript that detects theme by watching Streamlit's background and injects appropriate styles
    theme_script = """
    <script>
    (function() {
        const lightColors = {
            bg: '#ffffff', bgSecondary: '#f8fafc', bgTertiary: '#f1f5f9',
            text: '#1e293b', textSecondary: '#475569', textMuted: '#64748b', textFaint: '#94a3b8',
            border: '#e2e8f0', borderLight: '#f1f5f9', nlpBg: '#dbeafe', nlpText: '#1d4ed8'
        };
        const darkColors = {
            bg: '#0e1117', bgSecondary: '#262730', bgTertiary: '#31333F',
            text: '#fafafa', textSecondary: '#c2c5ce', textMuted: '#a3a8b8', textFaint: '#6b7280',
            border: '#31333F', borderLight: '#3d4051', nlpBg: '#1e3a5f', nlpText: '#60a5fa'
        };

        function applyThemeColors(isDark) {
            const c = isDark ? darkColors : lightColors;
            const styleId = 'custom-theme-styles';
            let styleEl = document.getElementById(styleId);
            if (!styleEl) {
                styleEl = document.createElement('style');
                styleEl.id = styleId;
                document.head.appendChild(styleEl);
            }
            styleEl.textContent = `
                .custom-header { background-color: ${c.bg} !important; border-bottom: 1px solid ${c.border} !important; }
                .header-title { color: ${c.text} !important; }
                .header-subtitle { color: ${c.textMuted} !important; }
                .header-user-name { color: ${c.text} !important; }
                .header-user-site { color: ${c.textMuted} !important; }
                .header-avatar { background-color: ${c.bgTertiary} !important; color: ${c.textMuted} !important; }
                .custom-card { background-color: ${c.bg} !important; border-color: ${c.border} !important; }
                .card-header { background-color: ${c.bgSecondary} !important; border-bottom-color: ${c.border} !important; }
                .card-header-text { color: ${c.textSecondary} !important; }
                .card-header svg { stroke: ${c.textMuted} !important; }
                .section-title { color: ${c.text} !important; }
                .section-subtitle { color: ${c.textMuted} !important; }
                .form-label { color: ${c.textSecondary} !important; }
                .nlp-badge { background-color: ${c.nlpBg} !important; color: ${c.nlpText} !important; }
                .custom-footer { background-color: ${c.bg} !important; border-top: 1px solid ${c.border} !important; }
                .footer-text { color: ${c.textFaint} !important; }
                .confidence-section { background-color: ${c.bg} !important; border-bottom: 1px solid ${c.borderLight} !important; }
                .confidence-label { color: ${c.textFaint} !important; }
                .confidence-value { color: ${c.text} !important; }
                .confidence-bar { background-color: ${c.bgTertiary} !important; }
                .action-step { background-color: ${c.bgSecondary} !important; border-color: ${c.borderLight} !important; }
                .step-content h4 { color: ${c.text} !important; }
                .step-content p { color: ${c.textMuted} !important; }
            `;
        }

        function detectTheme() {
            const stApp = document.querySelector('[data-testid="stAppViewContainer"]');
            if (!stApp) return null;
            const bg = window.getComputedStyle(stApp).backgroundColor;
            const match = bg.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
            if (match) {
                const brightness = (parseInt(match[1]) * 299 + parseInt(match[2]) * 587 + parseInt(match[3]) * 114) / 1000;
                return brightness < 128;
            }
            return false;
        }

        function checkAndApply() {
            const isDark = detectTheme();
            if (isDark !== null) {
                applyThemeColors(isDark);
            }
        }

        // Run on load and periodically to catch theme changes
        checkAndApply();
        setInterval(checkAndApply, 500);

        // Also observe DOM changes
        const observer = new MutationObserver(checkAndApply);
        observer.observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['style', 'class'] });
    })();
    </script>
    """

    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown(theme_script, unsafe_allow_html=True)


def render_header():
    """Render the header using native Streamlit components."""
    import streamlit as st

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### ⚡ Diagnostic AI")
        st.caption("MANUFACTURING ENGINEERING PORTAL")
    with col2:
        st.markdown("**Engineer A. Chen**")
        st.caption("Site: Austin-TX-01")

    st.divider()


def render_footer():
    """Render the footer using native Streamlit components."""
    import streamlit as st

    st.divider()
    st.caption("Secured Enterprise Fusion App • Connected to FASTAPI-AI-BACKEND • Version 1.2.0")


def card_start(title: str, icon: str = ""):
    """Start a styled card section."""
    import streamlit as st
    icon_svg = ""
    if icon == "layout":
        icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
    elif icon == "alert":
        icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
    
    st.markdown(f"""
    <div class="custom-card">
        <div class="card-header">
            {icon_svg}
            <p class="card-header-text">{title}</p>
        </div>
        <div class="card-body">
    """, unsafe_allow_html=True)


def card_end():
    """End a styled card section."""
    import streamlit as st
    st.markdown("</div></div>", unsafe_allow_html=True)
