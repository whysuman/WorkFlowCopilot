"""
Custom CSS styles for the Manufacturing Investigation Copilot.
Provides a modern, enterprise-grade UI matching the React reference design.
Supports both light and dark Streamlit themes via JavaScript detection.
"""

# ============================================
# Base CSS (layout, fonts, animations - theme-independent)
# ============================================
BASE_CSS = """
<style>
/* Import Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Global Styles */
.stApp {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hide default Streamlit header */
header[data-testid="stHeader"] {
    background: transparent;
}

/* Custom Header Layout */
.custom-header {
    padding: 0.75rem 1.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: -1rem -1rem 1.5rem -1rem;
    border-bottom-width: 1px;
    border-bottom-style: solid;
}

.header-logo {
    background: #2563eb;
    padding: 0.5rem;
    border-radius: 0.5rem;
    display: inline-flex;
}

.header-title {
    font-size: 1.125rem;
    font-weight: 700;
    margin: 0;
    line-height: 1.2;
}

.header-subtitle {
    font-size: 0.65rem;
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
}

.header-user-site {
    font-size: 0.75rem;
    margin: 0;
}

.header-avatar {
    width: 2.5rem;
    height: 2.5rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
}

/* Custom Card Layout */
.custom-card {
    border-radius: 0.75rem;
    border-width: 1px;
    border-style: solid;
    overflow: hidden;
    margin-bottom: 1.5rem;
}

.card-header {
    padding: 0.75rem 1.5rem;
    border-bottom-width: 1px;
    border-bottom-style: solid;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-header-text {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0;
}

.card-body {
    padding: 1.5rem;
}

/* Section Titles */
.section-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 0.25rem;
}

.section-subtitle {
    margin-bottom: 1.5rem;
}

/* Results Header (Gradient - same in both themes) */
.results-header {
    background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
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
    padding: 0.25rem 0.75rem;
    border-radius: 0.25rem;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
}

.priority-critical { background: #ef4444; color: white; }
.priority-high { background: #f97316; color: white; }
.priority-medium { background: #fbbf24; color: #78350f; }
.priority-low { background: #22c55e; color: white; }

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

/* Confidence Score */
.confidence-section {
    padding: 2rem;
    border-bottom-width: 1px;
    border-bottom-style: solid;
}

.confidence-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 0.5rem;
}

.confidence-value {
    font-size: 2.5rem;
    font-weight: 900;
    letter-spacing: -0.025em;
}

.confidence-bar {
    width: 8rem;
    height: 0.75rem;
    border-radius: 9999px;
    overflow: hidden;
}

.confidence-fill {
    height: 100%;
    background: #22c55e;
    border-radius: 9999px;
}

/* Action Steps */
.action-step {
    display: flex;
    gap: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 0.75rem;
    border-width: 1px;
    border-style: solid;
    transition: border-color 0.2s;
}

.action-step:hover {
    border-color: #60a5fa;
}

.step-number {
    width: 2rem;
    height: 2rem;
    background: #2563eb;
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
    margin: 0 0 0.25rem 0;
}

.step-content p {
    font-size: 0.875rem;
    margin: 0;
}

/* NLP Badge */
.nlp-badge {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    padding: 0.25rem 0.5rem;
    border-radius: 0.25rem;
    letter-spacing: 0.025em;
}

/* Footer */
.custom-footer {
    padding: 1rem 2rem;
    text-align: center;
    margin: 2rem -1rem -1rem -1rem;
    border-top-width: 1px;
    border-top-style: solid;
}

.footer-text {
    font-size: 0.625rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}

/* Form overrides */
div[data-testid="stForm"] {
    border: none;
    padding: 0;
}

section[data-testid="stForm"] > div {
    border: none !important;
    padding: 0 !important;
}

/* Native segmented control: intentionally no custom severity overrides. */

/* Temporary debug badge */
.theme-debug-badge {
    position: fixed;
    right: 12px;
    bottom: 12px;
    z-index: 999999;
    padding: 8px 10px;
    border-radius: 8px;
    font-size: 11px;
    font-weight: 700;
    font-family: "Inter", sans-serif;
    background: var(--secondary-background-color);
    color: var(--text-color);
    border: 1px solid rgba(128, 128, 128, 0.35);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>
"""

# ============================================
# Theme Observer JavaScript
# Detects Streamlit's theme and applies colors dynamically
# ============================================
THEME_OBSERVER_JS = """
<script>
(function() {
    // Color definitions
    const themes = {
        light: {
            bg: '#ffffff',
            bgSecondary: '#f8fafc',
            bgTertiary: '#f1f5f9',
            text: '#1e293b',
            textSecondary: '#475569',
            textMuted: '#64748b',
            textFaint: '#94a3b8',
            border: '#e2e8f0',
            borderLight: '#f1f5f9',
            nlpBg: '#dbeafe',
            nlpText: '#1d4ed8'
        },
        dark: {
            bg: '#0e1117',
            bgSecondary: '#262730',
            bgTertiary: '#31333F',
            text: '#fafafa',
            textSecondary: '#c2c5ce',
            textMuted: '#a3a8b8',
            textFaint: '#6b7280',
            border: '#31333F',
            borderLight: '#3d4051',
            nlpBg: '#1e3a5f',
            nlpText: '#60a5fa'
        }
    };

    function detectTheme() {
        const stApp = document.querySelector('[data-testid="stAppViewContainer"]');
        if (!stApp) return null;
        const bg = window.getComputedStyle(stApp).backgroundColor;
        const match = bg.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)/);
        if (match) {
            const r = parseInt(match[1], 10);
            const g = parseInt(match[2], 10);
            const b = parseInt(match[3], 10);
            const luminance = (0.299 * r + 0.587 * g + 0.114 * b);
            return luminance < 128 ? 'dark' : 'light';
        }
        return 'light';
    }

    function applyTheme(themeName) {
        const c = themes[themeName];
        if (!c) return;

        // Apply to custom shell elements only.
        // Severity controls are styled in CSS with Streamlit theme tokens.
        document.querySelectorAll('.custom-header').forEach(el => {
            el.style.backgroundColor = c.bg;
            el.style.borderBottomColor = c.border;
        });
        document.querySelectorAll('.header-title').forEach(el => {
            el.style.color = c.text;
        });
        document.querySelectorAll('.header-subtitle').forEach(el => {
            el.style.color = c.textMuted;
        });
        document.querySelectorAll('.header-user-name').forEach(el => {
            el.style.color = c.text;
        });
        document.querySelectorAll('.header-user-site').forEach(el => {
            el.style.color = c.textMuted;
        });
        document.querySelectorAll('.header-avatar').forEach(el => {
            el.style.backgroundColor = c.bgTertiary;
            el.style.color = c.textMuted;
        });
        document.querySelectorAll('.custom-card').forEach(el => {
            el.style.backgroundColor = c.bg;
            el.style.borderColor = c.border;
        });
        document.querySelectorAll('.card-header').forEach(el => {
            el.style.backgroundColor = c.bgSecondary;
            el.style.borderBottomColor = c.border;
        });
        document.querySelectorAll('.card-header-text').forEach(el => {
            el.style.color = c.textSecondary;
        });
        document.querySelectorAll('.card-header svg').forEach(el => {
            el.style.stroke = c.textMuted;
        });
        document.querySelectorAll('.section-title').forEach(el => {
            el.style.color = c.text;
        });
        document.querySelectorAll('.section-subtitle').forEach(el => {
            el.style.color = c.textMuted;
        });
        document.querySelectorAll('.form-label').forEach(el => {
            el.style.color = c.textSecondary;
        });
        document.querySelectorAll('.nlp-badge').forEach(el => {
            el.style.backgroundColor = c.nlpBg;
            el.style.color = c.nlpText;
        });
        document.querySelectorAll('.custom-footer').forEach(el => {
            el.style.backgroundColor = c.bg;
            el.style.borderTopColor = c.border;
        });
        document.querySelectorAll('.footer-text').forEach(el => {
            el.style.color = c.textFaint;
        });
        document.querySelectorAll('.confidence-section').forEach(el => {
            el.style.backgroundColor = c.bg;
            el.style.borderBottomColor = c.borderLight;
        });
        document.querySelectorAll('.confidence-label').forEach(el => {
            el.style.color = c.textFaint;
        });
        document.querySelectorAll('.confidence-value').forEach(el => {
            el.style.color = c.text;
        });
        document.querySelectorAll('.confidence-bar').forEach(el => {
            el.style.backgroundColor = c.bgTertiary;
        });
        document.querySelectorAll('.action-step').forEach(el => {
            el.style.backgroundColor = c.bgSecondary;
            el.style.borderColor = c.borderLight;
        });
        document.querySelectorAll('.step-content h4').forEach(el => {
            el.style.color = c.text;
        });
        document.querySelectorAll('.step-content p').forEach(el => {
            el.style.color = c.textMuted;
        });
    }

    function checkAndApply() {
        const theme = detectTheme();
        if (!theme) return;
        applyTheme(theme);
    }

    // Run immediately
    checkAndApply();

    // Poll for changes (catches theme switches)
    setInterval(checkAndApply, 250);

    // Also observe DOM mutations for new elements
    const observer = new MutationObserver(() => {
        checkAndApply();
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });
})();
</script>
"""


def inject_custom_css():
    """Inject base CSS and theme observer JavaScript."""
    import streamlit as st

    st.markdown(BASE_CSS, unsafe_allow_html=True)
    st.markdown(THEME_OBSERVER_JS, unsafe_allow_html=True)
    theme_base = st.get_option("theme.base") or "auto"
    st.markdown(
        f'<div class="theme-debug-badge">Theme(base): {theme_base} | Severity: native segmented</div>',
        unsafe_allow_html=True,
    )


def render_header():
    """Render the custom header with theme-aware styling."""
    import streamlit as st

    st.markdown("""
    <div class="custom-header">
        <div style="display: flex; align-items: center; gap: 1rem;">
            <div class="header-logo">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
                    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
                </svg>
            </div>
            <div>
                <p class="header-title">ACCEL MAN</p>
                <p class="header-subtitle">Manufacturing Investigation Portal</p>
            </div>
        </div>
        <div class="header-user">
            <div class="header-user-info">
                <p class="header-user-name">Engineer A. Chen</p>
                <p class="header-user-site">Site: Austin-TX-01</p>
            </div>
            <div class="header-avatar">AC</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the custom footer with theme-aware styling."""
    import streamlit as st

    st.markdown("""
    <div class="custom-footer">
        <p class="footer-text">
            Secured Enterprise Fusion App • Connected to FASTAPI-AI-BACKEND • Version 1.2.0
        </p>
    </div>
    """, unsafe_allow_html=True)


def card_start(title: str, icon: str = ""):
    """Start a styled card section."""
    import streamlit as st

    icon_svg = ""
    if icon == "layout":
        icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>'
    elif icon == "alert":
        icon_svg = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'

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
