# =============================================================
# Thème CSS — Injection de styles premium
# =============================================================

import streamlit as st

PREMIUM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap');
    
    .reportview-container { font-family: 'Inter', sans-serif; }
    
    .main-header {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800; font-size: 3rem; margin-bottom: 0.2rem;
    }
    .sub-header {
        font-family: 'Inter', sans-serif;
        color: #94a3b8; font-size: 1.15rem; margin-bottom: 2rem; font-weight: 400;
    }
    
    .glass-card {
        background: rgba(255,255,255,0.03); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
        padding: 24px; margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    }
    .glass-card:hover {
        border-color: rgba(99,102,241,0.4);
        box-shadow: 0 10px 30px -10px rgba(99,102,241,0.2);
        transform: translateY(-2px);
    }
    
    .metric-container { display: flex; gap: 15px; margin-bottom: 20px; }
    .metric-badge {
        flex: 1;
        background: linear-gradient(135deg, rgba(99,102,241,0.1) 0%, rgba(168,85,247,0.1) 100%);
        border: 1px solid rgba(99,102,241,0.2); border-radius: 12px;
        padding: 16px; text-align: center;
    }
    .metric-badge.emerald {
        background: linear-gradient(135deg, rgba(16,185,129,0.1) 0%, rgba(5,150,105,0.1) 100%);
        border: 1px solid rgba(16,185,129,0.2);
    }
    .metric-badge.violet {
        background: linear-gradient(135deg, rgba(139,92,246,0.1) 0%, rgba(109,40,217,0.1) 100%);
        border: 1px solid rgba(139,92,246,0.2);
    }
    .metric-value {
        font-family: 'Outfit', sans-serif; font-size: 2.2rem; font-weight: 800; margin: 0;
        background: linear-gradient(135deg, #ffffff 0%, #cbd5e1 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 0.05em; font-weight: 600; margin-top: 4px;
    }
    
    .prescription-row {
        background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px; padding: 15px; margin-bottom: 12px;
        display: flex; align-items: center; gap: 15px;
    }
    .index-bubble {
        background: #6366f1; color: white;
        font-family: 'Outfit', sans-serif; font-weight: 800;
        border-radius: 50%; width: 36px; height: 36px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1rem; flex-shrink: 0;
    }
    
    .score-badge {
        font-size: 0.8rem; font-weight: 700; padding: 4px 10px;
        border-radius: 20px; text-transform: uppercase; display: inline-block;
    }
    .score-badge.high {
        background: rgba(16,185,129,0.15); color: #10b981;
        border: 1px solid rgba(16,185,129,0.3);
    }
    .score-badge.med {
        background: rgba(245,158,11,0.15); color: #f59e0b;
        border: 1px solid rgba(245,158,11,0.3);
    }
    .score-badge.low {
        background: rgba(239,68,68,0.15); color: #ef4444;
        border: 1px solid rgba(239,68,68,0.3);
    }
    
    .stCodeBlock { border-radius: 12px !important; border: 1px solid rgba(255,255,255,0.05) !important; }

    /* === Quality Gate === */
    .quality-card {
        background: rgba(255,255,255,0.03); backdrop-filter: blur(10px);
        border: 1px solid rgba(255,255,255,0.08); border-radius: 16px;
        padding: 24px; margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    }
    .quality-card.accepted {
        border-color: rgba(16,185,129,0.4);
        box-shadow: 0 4px 20px -5px rgba(16,185,129,0.15);
    }
    .quality-card.rejected {
        border-color: rgba(239,68,68,0.4);
        box-shadow: 0 4px 20px -5px rgba(239,68,68,0.15);
    }
    .quality-gauge {
        display: flex; align-items: center; justify-content: center;
        flex-direction: column; gap: 4px;
    }
    .quality-score {
        font-family: 'Outfit', sans-serif; font-size: 3rem; font-weight: 800;
        line-height: 1; margin: 0;
    }
    .quality-score.pass {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .quality-score.fail {
        background: linear-gradient(135deg, #ef4444 0%, #f87171 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .quality-label {
        font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;
        letter-spacing: 0.08em; font-weight: 600;
    }
    .quality-verdict {
        font-family: 'Outfit', sans-serif; font-weight: 700;
        font-size: 1.1rem; padding: 6px 16px; border-radius: 30px;
        display: inline-block; margin-top: 6px;
    }
    .quality-verdict.pass {
        background: rgba(16,185,129,0.12); color: #10b981;
        border: 1px solid rgba(16,185,129,0.3);
    }
    .quality-verdict.fail {
        background: rgba(239,68,68,0.12); color: #ef4444;
        border: 1px solid rgba(239,68,68,0.3);
    }
    .metric-bar-track {
        background: rgba(255,255,255,0.06); border-radius: 6px;
        height: 8px; width: 100%; overflow: hidden;
    }
    .metric-bar-fill {
        height: 100%; border-radius: 6px;
        transition: width 0.6s ease;
    }
    .metric-bar-fill.good { background: linear-gradient(90deg, #10b981, #34d399); }
    .metric-bar-fill.warn { background: linear-gradient(90deg, #f59e0b, #fbbf24); }
    .metric-bar-fill.bad  { background: linear-gradient(90deg, #ef4444, #f87171); }
    .metric-icon { font-size: 1.3rem; }
</style>
"""


def inject():
    """Injecte le thème CSS premium dans la page Streamlit."""
    st.markdown(PREMIUM_CSS, unsafe_allow_html=True)
