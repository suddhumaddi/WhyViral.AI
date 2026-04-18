# Required installations:
# pip install streamlit moviepy openai-whisper torch

import os
import time
import tempfile
import streamlit as st
import base64

def get_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# Load background image
bg_image = get_base64("assets/bg.jpeg")  # <-- make sure name matches

st.markdown(f"""
<style>

/* MAIN BACKGROUND */
div[data-testid="stAppViewContainer"] {{
    background:
        linear-gradient(rgba(10,10,15,0.88), rgba(10,10,15,0.95)),
        url("data:image/jpeg;base64,{bg_image}");
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}}

/* REMOVE DEFAULT WHITE BACKGROUND */
div[data-testid="stApp"] {{
    background: transparent !important;
}}

/* MAIN CONTENT AREA */
.main {{
    background: transparent !important;
}}

</style>
""", unsafe_allow_html=True)

# ── Page config (must be first Streamlit call) ────────────────────────────
st.set_page_config(
    page_title="WhyViral AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Global ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e8e8f0;
  }

  .main { background-color: #0a0a0f; }
  .block-container { padding: 2rem 3rem 4rem 3rem; max-width: 1200px; }

  /* ── Hero ── */
  .hero-wrap {
    text-align: center;
    padding: 3.5rem 1rem 2rem 1rem;
  }
  .hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, #3b82f622, #38bdf822);
    border: 1px solid #3b82f655;
    color: #60a5fa;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 0.35rem 1rem;
    border-radius: 999px;
    margin-bottom: 1.2rem;
  }
  .hero-title {
    font-size: 3.8rem;
    font-weight: 800;
    line-height: 1.1;
    background: linear-gradient(135deg, #ffffff 0%, #60a5fa 50%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.8rem;
  }
  .hero-sub {
    font-size: 1.1rem;
    color: #94a3b8;
    font-weight: 400;
    max-width: 520px;
    margin: 0 auto 2.5rem auto;
    line-height: 1.6;
  }

  /* ── Upload zone ── */
  .upload-card {
    background: linear-gradient(135deg, #13131f 0%, #1a1a2e 100%);
    border: 1.5px dashed #2d2d4e;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    text-align: center;
    transition: border-color 0.3s;
    margin-bottom: 2rem;
  }
  .upload-card:hover { border-color: #3b82f6; }

  /* ── Divider ── */
  .section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #2d2d4e, transparent);
    margin: 2.5rem 0;
  }

  /* ── Clip card ── */
  .clip-card {
    background: linear-gradient(145deg, #13131f, #1c1c2e);
    border: 1px solid #2d2d4e;
    border-radius: 20px;
    padding: 1.8rem 2rem;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
  }
  .clip-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #3b82f6, #38bdf8, #f59e0b);
  }

  /* ── Score badge ── */
  .score-wrap { text-align: center; padding: 0.5rem 0; }
  .score-ring {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    width: 110px; height: 110px;
    border-radius: 50%;
    border: 3px solid;
    margin-bottom: 0.4rem;
  }
  .score-ring.green  { border-color: #22c55e; background: #22c55e12; }
  .score-ring.yellow { border-color: #f59e0b; background: #f59e0b12; }
  .score-ring.red    { border-color: #ef4444; background: #ef444412; }
  .score-number { font-size: 2rem; font-weight: 800; line-height: 1; }
  .score-label  { font-size: 0.65rem; letter-spacing: 0.1em; text-transform: uppercase; color: #64748b; margin-top: 2px; }
  .score-green  { color: #22c55e; }
  .score-yellow { color: #f59e0b; }
  .score-red    { color: #ef4444; }

  /* ── Section labels ── */
  .section-label {
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.6rem;
  }

  /* ── Hook box ── */
  .hook-box {
    background: linear-gradient(135deg, #3b82f618, #38bdf818);
    border-left: 3px solid #60a5fa;
    border-radius: 0 12px 12px 0;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0 1.2rem 0;
  }
  .hook-text {
    font-size: 1.05rem;
    font-weight: 700;
    color: #e2e8f0;
    line-height: 1.4;
  }

  /* ── Caption box ── */
  .caption-box {
    background: #1e1e30;
    border: 1px solid #2d2d4e;
    border-radius: 12px;
    padding: 0.9rem 1.2rem;
    margin: 0.4rem 0 1.2rem 0;
    font-style: italic;
    color: #cbd5e1;
    font-size: 0.95rem;
  }

  /* ── Reason pills ── */
  .pill-wrap { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.4rem 0 1.2rem 0; }
  .pill {
    background: #1e1e30;
    border: 1px solid #3d3d5e;
    border-radius: 999px;
    padding: 0.3rem 0.9rem;
    font-size: 0.78rem;
    color: #60a5fa;
    font-weight: 500;
  }

  /* ── Tip items ── */
  .tip-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid #1e1e30;
    font-size: 0.88rem;
    color: #94a3b8;
  }
  .tip-item:last-child { border-bottom: none; }
  .tip-dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    background: #3b82f6;
    margin-top: 6px;
    flex-shrink: 0;
  }

  /* ── Progress steps ── */
  .step-row { display: flex; align-items: center; gap: 0.8rem; padding: 0.6rem 0; }
  .step-icon { font-size: 1.1rem; width: 28px; text-align: center; }
  .step-text { font-size: 0.9rem; color: #94a3b8; }
  .step-text.active { color: #60a5fa; font-weight: 600; }
  .step-text.done   { color: #22c55e; }

  /* ── Clip header ── */
  .clip-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1.2rem;
  }
  .clip-number {
    background: linear-gradient(135deg, #3b82f6, #38bdf8);
    color: white;
    font-weight: 800;
    font-size: 0.85rem;
    width: 34px; height: 34px;
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
  }
  .clip-title { font-size: 1.1rem; font-weight: 700; color: #e2e8f0; }
  .clip-duration { font-size: 0.8rem; color: #64748b; margin-top: 2px; }

  /* ── Results header ── */
  .results-header {
    text-align: center;
    padding: 1rem 0 2rem 0;
  }
  .results-title {
    font-size: 1.8rem;
    font-weight: 800;
    color: #e2e8f0;
    margin-bottom: 0.3rem;
  }
  .results-sub { font-size: 0.9rem; color: #64748b; }

  /* ── Background glow enhancement (Fix 7) ── */
  .main::before {
    content: '';
    position: fixed;
    top: -200px; left: 50%;
    transform: translateX(-50%);
    width: 800px; height: 500px;
    background: radial-gradient(ellipse at center, #3b82f618 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
  }
  body {
  background: 
    radial-gradient(circle at 20% 0%, #1a103d 0%, #0a0a0f 40%),
    radial-gradient(circle at 80% 20%, #2a0f2e 0%, transparent 40%),
    #0a0a0f !important;
}

  /* ── Hover effect on clip cards (Fix 8) ── */
  .clip-card {
    transition: transform 0.25s ease, box-shadow 0.25s ease;
  }
  .clip-card:hover {
    transform: translateY(-3px) scale(1.005);
    box-shadow: 0 12px 40px #3b82f622, 0 4px 16px #00000055;
  }

  /* ── Empty state (Fix 9) ── */
  .empty-state {
    text-align: center;
    padding: 2.5rem 1rem 1rem 1rem;
    color: #475569;
    font-size: 1rem;
    font-weight: 500;
    letter-spacing: 0.02em;
  }
  .stFileUploader > div { background: transparent !important; }
  div[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: none !important;
  }
  .stButton > button {
    background: linear-gradient(135deg, #3b82f6, #38bdf8) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.7rem 2.5rem !important;
    transition: opacity 0.2s !important;
    width: 100%;
  }
  .stButton > button:hover { opacity: 0.85 !important; }
  video { border-radius: 12px; }
  .stExpander {
    background: #13131f !important;
    border: 1px solid #2d2d4e !important;
    border-radius: 12px !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────

def score_color(score: float) -> str:
    if score >= 8.0:
        return "green"
    if score >= 5.0:
        return "yellow"
    return "red"


def format_seconds(s: float) -> str:
    m, sec = divmod(int(s), 60)
    return f"{m}:{sec:02d}"


def render_score(score: float):
    color = score_color(score)
    st.markdown(f"""
    <div class="score-wrap">
      <div class="score-ring {color}">
        <span class="score-number score-{color}">{score}</span>
        <span class="score-label">Viral Score</span>
      </div>
    </div>
    """, unsafe_allow_html=True)


def render_clip_card(idx: int, clip_path: str, segment: dict, insights: dict, is_top: bool = False):
    duration = segment["end"] - segment["start"]

    # ── Most Viral badge (first clip only) ───────────────────────────
    if is_top:
        st.markdown("""
        <div style="display:flex;justify-content:flex-start;margin-bottom:0.6rem;">
          <div style="background:linear-gradient(135deg,#f59e0b,#ef4444);
                      color:white;font-weight:800;font-size:0.78rem;
                      letter-spacing:0.08em;text-transform:uppercase;
                      padding:0.35rem 1rem;border-radius:999px;
                      display:inline-flex;align-items:center;gap:0.4rem;">
            🏆 Most Viral Clip
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Card header ──────────────────────────────────────────────────
    st.markdown(f"""
    <div class="clip-card">
      <div class="clip-header">
        <div class="clip-number">#{idx}</div>
        <div>
          <div class="clip-title">Viral Clip #{idx}</div>
          <div class="clip-duration">
            ⏱ {format_seconds(segment['start'])} → {format_seconds(segment['end'])}
            &nbsp;·&nbsp; {duration:.1f}s
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Video player (full width) ────────────────────────────────────
    if os.path.exists(clip_path):
        with open(clip_path, "rb") as f:
            st.video(f.read())
    else:
        st.warning("Clip file not found.")

    # ── Score (centered, full width) ─────────────────────────────────
    render_score(insights["score"])

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

    # ── Why It Works ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">🧠 Why It Works</div>', unsafe_allow_html=True)
    pills_html = "".join(f'<span class="pill">{r}</span>' for r in insights["reason"])
    st.markdown(f'<div class="pill-wrap">{pills_html}</div>', unsafe_allow_html=True)

    # ── Hook ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">🚀 Hook</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="hook-box">
      <div class="hook-text">"{insights['hook']}"</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Caption ──────────────────────────────────────────────────────
    st.markdown('<div class="section-label">✍️ Caption</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="caption-box">{insights["caption"]}</div>', unsafe_allow_html=True)

    # ── Tips ─────────────────────────────────────────────────────────
    st.markdown('<div class="section-label">📈 Editing Tips</div>', unsafe_allow_html=True)
    tips_html = "".join(
        f'<div class="tip-item"><div class="tip-dot"></div><span>{tip}</span></div>'
        for tip in insights["tips"]
    )
    st.markdown(tips_html, unsafe_allow_html=True)

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)


# ── Pipeline runner ───────────────────────────────────────────────────────

def run_pipeline(video_path: str):
    """Run full pipeline and display results."""

    from modules.transcribe import transcribe_video
    from modules.analyzer   import analyze_transcript
    from modules.clipper    import clip_video
    from modules.enhancer   import enhance_clip

    status_area = st.empty()

    STEPS = [
        ("🎙️", "Transcribing audio"),
        ("🧠", "Analyzing viral potential"),
        ("✂️", "Cutting clips"),
        ("✨", "Generating viral insights"),
    ]

    def render_steps(current: int):
        """Render all steps; steps before current are ✅ done, current is active."""
        rows = ""
        for i, (icon, label) in enumerate(STEPS):
            if i < current:
                state = "done"
                bullet = "✅"
                text_label = f"{label} — done"
            elif i == current:
                state = "active"
                bullet = icon
                text_label = f"{label}..."
            else:
                state = ""
                bullet = "○"
                text_label = label
            rows += f"""
            <div class="step-row">
              <span class="step-icon">{bullet}</span>
              <span class="step-text {state}">{text_label}</span>
            </div>"""
        status_area.markdown(f"""
        <div style="background:#13131f;border:1px solid #2d2d4e;border-radius:16px;
                    padding:1.5rem 2rem;max-width:520px;margin:0 auto;">
          <div style="font-size:0.7rem;letter-spacing:0.12em;text-transform:uppercase;
                      color:#64748b;margin-bottom:1rem;">⚙️ &nbsp;Processing Pipeline</div>
          {rows}
        </div>
        """, unsafe_allow_html=True)

    # ── Step 1: Transcribe ────────────────────────────────────────────
    render_steps(0)
    try:
        transcript = transcribe_video(video_path)
    except Exception as e:
        st.error(f"Transcription failed: {e}")
        return

    # ── Step 2: Analyze ───────────────────────────────────────────────
    render_steps(1)
    try:
        segments = analyze_transcript(transcript)
    except Exception as e:
        st.error(f"Analysis failed: {e}")
        return

    if not segments:
        st.warning("No strong viral segments detected. Try a longer or more expressive video.")
        return

    # ── Step 3: Clip ──────────────────────────────────────────────────
    render_steps(2)
    try:
        clip_paths = clip_video(video_path, segments)
    except Exception as e:
        st.error(f"Clipping failed: {e}")
        return

    # ── Step 4: Enhance ───────────────────────────────────────────────
    render_steps(3)
    insights_list = []
    for seg in segments:
        clip_text = " ".join(
            s["text"] for s in transcript
            if s["start"] >= seg["start"] - 0.5 and s["end"] <= seg["end"] + 0.5
        )
        try:
            insights_list.append(enhance_clip(clip_text))
        except Exception as e:
            insights_list.append({
                "score": 0.0, "reason": ["Enhancement error"],
                "hook": "—", "caption": "—", "tips": [str(e)],
            })

    status_area.empty()

    # ── Fix 4: Total clips found counter ─────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;margin-bottom:0.5rem;">
      <span style="background:linear-gradient(135deg,#3b82f622,#38bdf822);
                   border:1px solid #3b82f655;color:#60a5fa;
                   font-size:0.85rem;font-weight:700;letter-spacing:0.06em;
                   padding:0.45rem 1.4rem;border-radius:999px;display:inline-block;">
        🔥 Found {len(segments)} viral clip{"s" if len(segments) != 1 else ""}
      </span>
    </div>
    """, unsafe_allow_html=True)

    # ── Results header ────────────────────────────────────────────────
    st.markdown("""
    <div class="results-header">
      <div class="results-title">⚡ Your Viral Clips Are Ready</div>
      <div class="results-sub">Ranked and explained by WhyViral AI</div>
    </div>
    """, unsafe_allow_html=True)

    for idx, (seg, clip_path, insights) in enumerate(
        zip(segments, clip_paths, insights_list), start=1
    ):
        render_clip_card(idx, clip_path, seg, insights, is_top=(idx == 1))


# ── Main layout ───────────────────────────────────────────────────────────

def main():
    # ── Hero ─────────────────────────────────────────────────────────
    st.markdown("""
    <div class="hero-wrap">
      <div class="hero-badge">⚡ AI-Powered Clip Intelligence</div>
      <div class="hero-title">WhyViral AI</div>
      <div class="hero-sub">
        Turn long videos into viral short clips — with AI that explains
        exactly why each moment will perform.
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Upload ────────────────────────────────────────────────────────
    # NOTE: The upload-card styling is applied via the inner container div
    # to avoid Streamlit's HTML fragment isolation creating an empty box.
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        uploaded = st.file_uploader(
            label="Upload video",
            type=["mp4"],
            label_visibility="collapsed",
        )

        if uploaded:
            st.markdown(f"""
            <div style="background:#1e1e30;border-radius:10px;padding:0.7rem 1rem;
                        margin:0.8rem 0;font-size:0.85rem;color:#94a3b8;
                        display:flex;align-items:center;gap:0.5rem;">
              ✅ &nbsp;<strong style="color:#e2e8f0;">{uploaded.name}</strong>
              &nbsp;·&nbsp; {uploaded.size / (1024*1024):.1f} MB
            </div>
            """, unsafe_allow_html=True)

            process_btn = st.button("⚡  Analyze & Extract Viral Clips", use_container_width=True)
        else:
            process_btn = False

    # ── Feature pills ─────────────────────────────────────────────────
    if not uploaded:
        st.markdown("""
        <div style="display:flex;justify-content:center;gap:1rem;flex-wrap:wrap;
                    margin-top:1rem;margin-bottom:1.5rem;">
          <span class="pill">🎙️ Auto-transcription</span>
          <span class="pill">🧠 Viral scoring</span>
          <span class="pill">✂️ Smart clipping</span>
          <span class="pill">🚀 Hook generation</span>
          <span class="pill">📈 Editing tips</span>
        </div>
        <div class="empty-state">
          Upload a video to discover viral moments ✨
        </div>
        """, unsafe_allow_html=True)

    # ── Process ───────────────────────────────────────────────────────
    if process_btn and uploaded:
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            tmp.write(uploaded.read())
            tmp_path = tmp.name

        try:
            run_pipeline(tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


if __name__ == "__main__":
    main()