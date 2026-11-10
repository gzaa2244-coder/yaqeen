import asyncio
import base64
import json
import re
import time
import urllib.request

import streamlit as st
import streamlit.components.v1 as components

# =====================================================
# 1) إعداد الصفحة (لازم يكون أول أمر Streamlit)
# =====================================================
st.set_page_config(
    page_title="منصة اليقين",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PAGES = ["🏠 الرئيسية", "💬 اسأل نور", "🤝 قاعة الحوار", "📖 القرآن الكريم", "🕌 الصلاة والمساجد"]
PAGE_KEYS = {PAGES[0]: "home", PAGES[1]: "qa", PAGES[2]: "dialogue", PAGES[3]: "quran", PAGES[4]: "prayer"}

# =====================================================
# 2) التصميم — نهاري (مريمي وكريمي) وليلي (فحمي وذهبي)
# =====================================================
def make_pattern(color: str, opacity: str) -> str:
    return (
        "url(\"data:image/svg+xml,"
        "%3Csvg xmlns='http://www.w3.org/2000/svg' width='96' height='96' viewBox='0 0 96 96'%3E"
        f"%3Cg fill='none' stroke='%23{color}' stroke-opacity='{opacity}' stroke-width='1'%3E"
        "%3Crect x='28' y='28' width='40' height='40'/%3E"
        "%3Crect x='28' y='28' width='40' height='40' transform='rotate(45 48 48)'/%3E"
        "%3Ccircle cx='48' cy='48' r='10'/%3E"
        "%3Cpath d='M0 0L20 20M96 0L76 20M0 96L20 76M96 96L76 76M48 0V8M48 96V88M0 48H8M96 48H88'/%3E"
        "%3Crect x='-12' y='-12' width='24' height='24' transform='rotate(45 0 0)'/%3E"
        "%3Crect x='84' y='-12' width='24' height='24' transform='rotate(45 96 0)'/%3E"
        "%3Crect x='-12' y='84' width='24' height='24' transform='rotate(45 0 96)'/%3E"
        "%3Crect x='84' y='84' width='24' height='24' transform='rotate(45 96 96)'/%3E"
        "%3C/g%3E%3C/svg%3E\")"
    )


PATTERN_DARK = make_pattern("c9a45c", "0.10")
PATTERN_LIGHT = make_pattern("7f9c88", "0.22")
PATTERN_PANEL_DARK = make_pattern("c9a45c", "0.22")
PATTERN_PANEL_LIGHT = make_pattern("ffffff", "0.95")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap');

/* ===== الألوان: الليلي هو الأساس ===== */
:root{
  --bg:#0f1116; --bg-2:#161922;
  --surface:rgba(26,29,38,.72); --surface-solid:#1a1d26; --surface-2:#1f2330;
  --border:rgba(201,164,92,.22); --border-strong:rgba(201,164,92,.55);
  --text:#f2ecdf; --muted:#a9a293;
  --gold:#c9a45c; --gold-light:#e9cd8f; --gold-dark:#8d6e33; --gold-shine:#fff3c4;
  --gold-soft:rgba(201,164,92,.12);
  --accent:#3f9d7a; --accent-soft:rgba(63,157,122,.16);
  --glow1:rgba(201,164,92,.18); --glow2:rgba(40,110,90,.22);
  --shadow:0 18px 40px rgba(0,0,0,.45);
  --input-bg:#151821; --on-gold:#14110a;
  --pattern:PAT_DARK; --panel:PANEL_DARK;
}
:root[data-yq-theme="light"]{
  --bg:#edf0e9; --bg-2:#f6f5ee;
  --surface:rgba(255,255,255,.62); --surface-solid:#fbfaf5; --surface-2:#ffffff;
  --border:rgba(120,145,128,.30); --border-strong:rgba(176,141,74,.55);
  --text:#2b3830; --muted:#68776d;
  --gold:#b08d4a; --gold-light:#8c6b2a; --gold-dark:#6f5420; --gold-shine:#d9b86a;
  --gold-soft:rgba(176,141,74,.12);
  --accent:#5f8a72; --accent-soft:rgba(95,138,114,.14);
  --glow1:rgba(255,255,255,.95); --glow2:rgba(150,180,160,.35);
  --shadow:0 18px 40px rgba(60,80,65,.14);
  --input-bg:#ffffff; --on-gold:#ffffff;
  --pattern:PAT_LIGHT; --panel:PANEL_LIGHT;
}

/* ===== الخطوط (مع حماية أيقونات Streamlit) ===== */
.stApp, .stApp *{ font-family:'Noto Kufi Arabic', sans-serif; }
[data-testid="stIconMaterial"], .material-symbols-rounded, .material-icons{
  font-family:'Material Symbols Rounded' !important;
}
.stMarkdown p, .stMarkdown li{ font-size:1.05rem; font-weight:500; line-height:2.1; color:var(--text); }
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4{ color:var(--gold-light); }
.stMarkdown strong{ color:var(--gold-light); }
.stApp, .stApp p, .stApp label, .stApp span{ color:var(--text); }

/* ===== الخلفية الحية ===== */
.stApp{ isolation:isolate; background:var(--bg); color:var(--text); transition:background .6s ease; }
.stApp::before{
  content:""; position:fixed; inset:-25%; z-index:-1; pointer-events:none;
  background:
    radial-gradient(circle at 30% 18%, var(--glow1) 0%, transparent 36%),
    radial-gradient(circle at 75% 82%, var(--glow2) 0%, transparent 38%),
    radial-gradient(circle at 82% 12%, var(--gold-soft) 0%, transparent 30%);
  animation:aurora 22s ease-in-out infinite alternate;
}
@keyframes aurora{
  0%  { transform:translate(0,0) rotate(0deg) scale(1); }
  50% { transform:translate(4%,-3%) rotate(8deg) scale(1.08); }
  100%{ transform:translate(-4%,3%) rotate(-6deg) scale(1.02); }
}
.stApp::after{
  content:""; position:fixed; inset:-96px; z-index:-1; pointer-events:none;
  background-image:var(--pattern); background-size:96px 96px;
  animation:drift 45s linear infinite;
  -webkit-mask-image:radial-gradient(ellipse 85% 75% at 50% 45%, #000 30%, transparent 100%);
          mask-image:radial-gradient(ellipse 85% 75% at 50% 45%, #000 30%, transparent 100%);
}
@keyframes drift{ to{ transform:translate(96px,96px); } }

[data-testid="stMainBlockContainer"], .main .block-container{
  direction:rtl; text-align:right; max-width:1120px; padding-top:1.2rem; padding-bottom:7rem;
}

/* إخفاء أدوات Streamlit العلوية */
[data-testid="stHeader"]{ background:transparent; }
[data-testid="stDecoration"], [data-testid="stAppDeployButton"], .stDeployButton, [data-testid="stMainMenu"], #MainMenu, footer{ display:none !important; }
[data-testid="stExpandSidebarButton"], [data-testid="stSidebarCollapsedControl"]{ color:var(--gold) !important; }

/* ===== شريط التنقل العلوي ===== */
.st-key-topnav{
  background:var(--surface); border:1px solid var(--border); border-radius:20px;
  padding:.55rem 1rem; backdrop-filter:blur(14px); box-shadow:var(--shadow);
  margin-bottom:1.4rem; animation:rise .6s ease both;
}
.st-key-topnav [data-testid="stHorizontalBlock"]{ align-items:center; }
.brand{ display:flex; align-items:center; gap:.55rem; white-space:nowrap; }
.brand .lamp{ font-size:1.6rem; display:inline-block; animation:float 4s ease-in-out infinite; }
.brand .name{ font-family:'Amiri', serif !important; font-size:1.7rem; font-weight:700; color:var(--gold-light); line-height:1.2; }
/* تبويبات قسم القرآن */
.st-key-qtabs{ display:flex; justify-content:center; margin:-.6rem 0 .8rem; }
.st-key-qtabs [role="radiogroup"]{ gap:.4rem; justify-content:center; background:var(--surface); border:1px solid var(--border);
  border-radius:999px; padding:.3rem; backdrop-filter:blur(10px); }
.st-key-qtabs [role="radiogroup"] label{ border-radius:999px; padding:.35rem 1.1rem; margin:0 !important; cursor:pointer; transition:all .25s; }
.st-key-qtabs [role="radiogroup"] label > div:first-child{ display:none; }
.st-key-qtabs [role="radiogroup"] label p{ font-weight:700; color:var(--muted); margin:0; }
.st-key-qtabs [role="radiogroup"] label:has(input:checked){ background:var(--gold); }
.st-key-qtabs [role="radiogroup"] label:has(input:checked) p{ color:var(--on-gold); }
.st-key-topnav [role="radiogroup"]{ gap:.35rem; flex-wrap:wrap; justify-content:flex-start; direction:rtl; }
.st-key-topnav [role="radiogroup"] label{
  border:1px solid transparent; border-radius:999px; padding:.35rem .9rem; margin:0 !important;
  cursor:pointer; transition:all .25s ease; background:transparent;
}
.st-key-topnav [role="radiogroup"] label > div:first-child{ display:none; }
.st-key-topnav [role="radiogroup"] label p{ font-size:.92rem; font-weight:600; color:var(--muted); margin:0; }
.st-key-topnav [role="radiogroup"] label:hover{ background:var(--gold-soft); }
.st-key-topnav [role="radiogroup"] label:hover p{ color:var(--text); }
.st-key-topnav [role="radiogroup"] label:has(input:checked){
  background:var(--gold-soft); border-color:var(--border-strong);
}
.st-key-topnav [role="radiogroup"] label:has(input:checked) p{ color:var(--gold-light); }

/* ===== الشريط الجانبي ===== */
[data-testid="stSidebar"]{ background:var(--bg-2); border-left:1px solid var(--border); }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{ direction:rtl; text-align:right; }
.side-brand{ text-align:center; padding:.4rem 0 1.1rem; margin-bottom:1.1rem; border-bottom:1px solid var(--border); }
.side-brand .logo{ font-size:2.4rem; display:inline-block; animation:float 4s ease-in-out infinite; }
.side-brand .name{ font-family:'Amiri', serif !important; font-size:2.1rem; font-weight:700; color:var(--gold-light); }
.side-brand .tag{ color:var(--muted); font-size:.85rem; }
.note, .tip{ border-radius:14px; padding:1rem; margin:1.1rem 0; font-size:.9rem; line-height:2; color:var(--text); }
.note{ background:var(--gold-soft); border:1px solid var(--border-strong); }
.note b, .tip b{ color:var(--gold-light); }
.tip{ background:var(--accent-soft); border:1px dashed var(--border); }
[data-testid="stSidebar"] .stButton > button{
  width:100%; background:transparent; color:var(--gold-light); border:1px solid var(--gold); border-radius:12px;
}
[data-testid="stSidebar"] .stButton > button:hover{ background:var(--gold); color:var(--on-gold); }

/* ===== حركات عامة ===== */
@keyframes rise{ from{opacity:0; transform:translateY(18px);} to{opacity:1; transform:none;} }
@keyframes shimmer{ to{ background-position:200% center; } }
@keyframes float{ 0%,100%{ transform:translateY(0) rotate(-3deg); } 50%{ transform:translateY(-7px) rotate(3deg); } }
@keyframes breathe{
  0%,100%{ text-shadow:0 0 6px var(--gold-soft); }
  50%    { text-shadow:0 0 22px var(--gold-soft), 0 0 30px var(--gold-soft); }
}

/* ===== القوس الرئيسي (الصفحة الرئيسية) ===== */
.hero-wrap{ display:grid; grid-template-columns:1fr 1.5fr 1fr; gap:1.2rem; align-items:end; margin:.4rem 0 1.4rem; }
.hero-side{
  height:230px; border-radius:22px; border:1px solid var(--border);
  background:var(--panel), linear-gradient(160deg, var(--surface), transparent);
  background-size:72px 72px, auto; box-shadow:var(--shadow); opacity:.9;
  animation:rise .9s ease .15s both;
}
.arch{
  position:relative; text-align:center; padding:3.2rem 1.6rem 2rem; min-height:300px;
  border-radius:50% 50% 24px 24px / 34% 34% 24px 24px;
  background:linear-gradient(180deg, var(--surface-2) 0%, var(--surface) 100%);
  border:1px solid var(--border-strong); box-shadow:var(--shadow), inset 0 0 60px var(--gold-soft);
  overflow:hidden; animation:rise .8s ease both;
}
.arch::before{
  content:"نور"; position:absolute; left:50%; top:52%; transform:translate(-50%,-50%);
  font-family:'Amiri', serif; font-size:11rem; font-weight:700; color:var(--gold); opacity:.07; pointer-events:none;
}
.arch .bismillah{ font-family:'Amiri', serif !important; color:var(--gold-light); font-size:1.3rem; animation:breathe 4s ease-in-out infinite; }
.arch .verse{
  font-family:'Amiri', serif !important; font-weight:700; font-size:2.6rem; line-height:1.7; margin:.6rem 0 .2rem;
  background:linear-gradient(90deg, var(--gold-dark), var(--gold), var(--gold-shine), var(--gold), var(--gold-dark));
  background-size:200% auto; -webkit-background-clip:text; background-clip:text; color:transparent;
  animation:shimmer 6s linear infinite;
}
.arch .ref{ color:var(--muted); font-size:.8rem; }
.arch .sub{ color:var(--text); font-size:1.05rem; font-weight:600; margin-top:.8rem; }

/* ===== كروت الصفحة الرئيسية ===== */
[class*="st-key-card_"]{
  background:var(--surface); border:1px solid var(--border); border-radius:22px; padding:1.2rem 1.2rem .6rem;
  backdrop-filter:blur(12px); box-shadow:var(--shadow); transition:transform .3s ease, border-color .3s ease, box-shadow .3s ease;
  animation:rise .8s ease both; height:100%;
}
[class*="st-key-card_"]:hover{ transform:translateY(-5px); border-color:var(--border-strong); box-shadow:var(--shadow), 0 0 0 4px var(--gold-soft); }
[class*="st-key-card_"] [data-testid="stVerticalBlock"]{ gap:.2rem; }
.hc .ic{ width:52px; height:52px; border-radius:16px; display:flex; align-items:center; justify-content:center; font-size:1.6rem;
  background:var(--accent-soft); border:1px solid var(--border); margin-bottom:.6rem; transition:transform .4s ease; }
[class*="st-key-card_"]:hover .hc .ic{ transform:rotate(-8deg) scale(1.08); }
.hc h3{ font-size:1.15rem !important; font-weight:700; color:var(--text) !important; margin:0 0 .25rem; padding:0; }
.hc p{ font-size:.9rem !important; color:var(--muted) !important; line-height:1.9 !important; margin:0; min-height:3.4em; }
[class*="st-key-card_"] .stButton > button{
  background:transparent !important; border:none !important; color:var(--gold-light) !important;
  padding:.2rem 0 !important; min-height:auto !important; font-weight:700; box-shadow:none !important; width:auto !important;
}
[class*="st-key-card_"] .stButton > button:hover{ color:var(--accent) !important; transform:translateX(-4px); }
.st-key-card_1{ animation-delay:.1s; } .st-key-card_2{ animation-delay:.2s; } .st-key-card_3{ animation-delay:.3s; }
.st-key-card_4{ animation-delay:.4s; } .st-key-card_5{ animation-delay:.5s; }

.section-title{ display:flex; align-items:center; gap:.8rem; color:var(--gold-light); font-weight:700; font-size:1.1rem; margin:1.6rem 0 .8rem; }
.section-title::after{ content:""; flex:1; height:1px; background:linear-gradient(90deg, var(--border), transparent); }

/* ===== عنوان صفحات المحادثة ===== */
.hero{ text-align:center; margin:.6rem 0 1.8rem; animation:rise .8s ease both; }
.hero h1{
  font-family:'Amiri', serif !important; font-weight:700; font-size:3rem; line-height:1.4; margin:.4rem 0; text-align:center; padding:0;
  background:linear-gradient(90deg, var(--gold-dark), var(--gold), var(--gold-shine), var(--gold), var(--gold-dark));
  background-size:200% auto; -webkit-background-clip:text; background-clip:text; color:transparent;
  animation:shimmer 6s linear infinite;
}
.hero .ornament{ display:flex; align-items:center; justify-content:center; gap:.8rem; color:var(--gold); font-size:1.3rem; margin:.3rem 0 .8rem; }
.hero .ornament::before, .hero .ornament::after{ content:""; width:120px; height:1px; background:linear-gradient(90deg, transparent, var(--gold), transparent); }
.hero p{ color:var(--muted) !important; font-size:1.1rem; font-weight:500; line-height:2; }
.badge{ display:inline-block; color:var(--gold-light); border:1px solid var(--border-strong); border-radius:999px;
  padding:.3rem 1.1rem; font-size:.9rem; font-weight:600; background:var(--gold-soft); }
.suggest-title{ color:var(--muted); font-size:.95rem; margin:.5rem 0 .8rem; text-align:center; }

/* أزرار الأسئلة المقترحة */
.st-key-suggest .stButton > button{
  width:100%; min-height:68px; white-space:normal; position:relative; overflow:hidden;
  background:var(--surface); color:var(--text); border:1px solid var(--border); border-radius:16px;
  direction:rtl; text-align:right; justify-content:flex-start; font-size:1rem; font-weight:600;
  backdrop-filter:blur(8px); transition:all .25s ease; animation:rise 1s ease both;
}
.st-key-suggest .stButton > button p{ color:var(--text); }
.st-key-suggest .stButton > button::after{
  content:""; position:absolute; top:0; bottom:0; width:45%; left:-60%; pointer-events:none;
  background:linear-gradient(100deg, transparent, var(--gold-soft), transparent); transform:skewX(-20deg); transition:left .7s ease;
}
.st-key-suggest .stButton > button:hover::after{ left:120%; }
.st-key-suggest .stButton > button:hover{ border-color:var(--gold); background:var(--gold-soft); transform:translateY(-3px); box-shadow:var(--shadow); }

.st-key-clearchat .stButton > button{
  background:transparent; border:1px solid var(--border); color:var(--muted); border-radius:999px; font-size:.85rem; padding:.2rem 1rem;
}
.st-key-clearchat .stButton > button:hover{ border-color:var(--gold); color:var(--gold-light); }

/* ===== المحادثة ===== */
[data-testid="stChatMessage"]{
  direction:rtl; text-align:right; background:var(--surface); border:1px solid var(--border);
  border-radius:18px; padding:1.1rem 1.2rem; margin-bottom:.9rem; backdrop-filter:blur(10px);
  animation:rise .5s ease both; transition:border-color .3s, box-shadow .3s;
}
[data-testid="stChatMessage"]:hover{ border-color:var(--border-strong); box-shadow:var(--shadow); }
[data-testid="stChatMessage"]:has([aria-label="Chat message from assistant"]){
  border-right:3px solid var(--gold);
  background:linear-gradient(135deg, var(--gold-soft), var(--surface) 45%);
}
[data-testid="stChatMessage"]:has([aria-label="Chat message from user"]){
  border-right:3px solid var(--accent);
  background:linear-gradient(135deg, var(--accent-soft), var(--surface) 45%);
}

/* ===== مربع الكتابة ===== */
[data-testid="stBottom"], [data-testid="stBottom"] > div, [data-testid="stBottomBlockContainer"]{ background:transparent !important; }
[data-testid="stChatInput"]{
  direction:rtl; background:var(--input-bg) !important; border:1px solid var(--gold) !important; border-radius:18px !important;
  animation:inputGlow 3.5s ease-in-out infinite;
}
@keyframes inputGlow{
  0%,100%{ box-shadow:0 0 0 4px var(--gold-soft), var(--shadow); }
  50%    { box-shadow:0 0 0 6px var(--gold-soft), 0 0 26px var(--gold-soft), var(--shadow); }
}
[data-testid="stChatInput"] textarea{ direction:rtl; text-align:right; font-size:1.05rem; font-weight:500; color:var(--text) !important; }
[data-testid="stChatInput"] textarea::placeholder{ color:var(--muted); opacity:1; }
[data-testid="stChatInputSubmitButton"]{ background:var(--gold) !important; border-radius:12px !important; transition:transform .2s; }
[data-testid="stChatInputSubmitButton"]:hover{ transform:scale(1.08) rotate(-8deg); }
[data-testid="stChatInputSubmitButton"] svg{ fill:var(--on-gold) !important; color:var(--on-gold) !important; }
[data-testid="stSpinner"] *{ color:var(--gold-light) !important; }

/* إطارات الأدوات (الصلاة والقرآن) شفافة */
iframe{ background:transparent !important; color-scheme:normal; }

/* ===== مساحة محجوزة لنور حتى لا يغطي الكلام ===== */
@media (max-width:1500px){
  [data-testid="stMainBlockContainer"], .main .block-container{ padding-right:125px !important; }
}
@media (max-width:760px){
  [data-testid="stMainBlockContainer"], .main .block-container{ padding-right:70px !important; padding-left:12px !important; }
  .hero-wrap{ grid-template-columns:1fr; }
  .hero-side{ display:none; }
  .arch .verse{ font-size:1.9rem; }
  .arch::before{ font-size:7rem; }
  .hero h1{ font-size:2.1rem; }
  .brand .name{ font-size:1.4rem; }
}

::-webkit-scrollbar{ width:8px; height:8px; }
::-webkit-scrollbar-thumb{ background:var(--border); border-radius:8px; }

@media (prefers-reduced-motion: reduce){
  *, *::before, *::after{ animation:none !important; transition:none !important; }
}
</style>
"""
CSS = (
    CSS.replace("PAT_DARK", PATTERN_DARK)
    .replace("PAT_LIGHT", PATTERN_LIGHT)
    .replace("PANEL_DARK", PATTERN_PANEL_DARK)
    .replace("PANEL_LIGHT", PATTERN_PANEL_LIGHT)
)

st.markdown(CSS, unsafe_allow_html=True)

# =====================================================
# 3) نور + زر الوضع الليلي/النهاري + النجوم
#    الكود يُحقن في الصفحة مرة واحدة، وبعدها نرسل له الأحداث
# =====================================================
MASCOT_JS = r"""
(function () {
  if (window.__yaqeenV4) return;
  const D = document, H = D.documentElement;
  ['yq-mascot', 'yq-glow', 'yq-stars', 'yq-theme', 'yq-ask'].forEach(id => { const o = D.getElementById(id); if (o) o.remove(); });

  const css = `
  #yq-glow{position:fixed;left:0;top:0;width:420px;height:420px;margin:-210px 0 0 -210px;border-radius:50%;
    pointer-events:none;z-index:1;background:radial-gradient(circle,var(--gold-soft) 0%,transparent 65%)}
  #yq-theme{position:fixed;top:12px;right:16px;z-index:999991;width:42px;height:42px;border-radius:50%;
    border:1px solid var(--border-strong);background:var(--surface-solid);color:var(--gold-light);font-size:19px;cursor:pointer;
    display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow);transition:transform .4s ease}
  #yq-theme:hover{transform:rotate(25deg) scale(1.08)}
  #yq-mascot{position:fixed;left:0;top:0;width:92px;z-index:999990;user-select:none;cursor:pointer;
    font-family:'Noto Kufi Arabic',sans-serif}
  #yq-mascot .yq-body{transform-origin:50% 90%;filter:drop-shadow(0 6px 18px rgba(212,175,55,.45))}
  #yq-mascot .yq-eyes{transform-box:fill-box;transform-origin:center;transition:transform .08s}
  #yq-mascot.blink .yq-eyes{transform:scaleY(.1)}
  #yq-mascot .yq-open{opacity:0;transform-box:fill-box;transform-origin:center}
  #yq-mascot.talking .yq-open{opacity:1;animation:yqTalk .22s ease-in-out infinite alternate}
  #yq-mascot.talking .yq-smile{opacity:0}
  @keyframes yqTalk{from{transform:scaleY(.25)}to{transform:scaleY(1.15)}}
  #yq-mascot .yq-light{animation:yqGlow 2.4s ease-in-out infinite alternate}
  @keyframes yqGlow{from{opacity:.75}to{opacity:1}}
  .yq-bubble{position:absolute;bottom:100%;right:0;margin-bottom:10px;width:220px;padding:.7rem .85rem;
    background:var(--surface-solid);color:var(--text);border:1px solid var(--gold);border-radius:14px;direction:rtl;text-align:right;
    font-size:.88rem;line-height:1.9;box-shadow:var(--shadow);opacity:0;transform:translateY(8px) scale(.96);
    transition:opacity .25s,transform .25s;pointer-events:none}
  .yq-bubble::after{content:"";position:absolute;top:100%;right:30px;border:8px solid transparent;border-top-color:var(--gold)}
  #yq-mascot.show .yq-bubble{opacity:1;transform:none}
  .yq-name{color:var(--gold-light);font-weight:700;margin-left:.3rem}
  .yq-voice{position:absolute;top:-10px;left:-12px;width:36px;height:36px;border-radius:50%;border:2px solid var(--gold);
    background:var(--surface-solid);color:var(--gold-light);font-size:16px;cursor:pointer;display:flex;align-items:center;justify-content:center;
    padding:0;z-index:2;box-shadow:var(--shadow)}
  .yq-voice:hover,.yq-voice.on{background:var(--gold);color:var(--on-gold)}
  #yq-ask{position:fixed;right:16px;bottom:270px;z-index:999992;width:300px;max-width:calc(100vw - 32px);
    background:var(--surface-solid);color:var(--text);border:1px solid var(--gold);border-radius:18px;padding:14px 16px;
    box-shadow:var(--shadow);direction:rtl;text-align:right;font-family:'Noto Kufi Arabic',sans-serif;
    opacity:0;transform:translateY(12px) scale(.97);pointer-events:none;transition:opacity .3s,transform .3s}
  #yq-ask.show{opacity:1;transform:none;pointer-events:auto}
  #yq-ask .q{font-weight:700;line-height:1.9;margin-bottom:10px;font-size:.95rem}
  #yq-ask .q b{color:var(--gold-light)}
  #yq-ask .row{display:flex;gap:8px;flex-wrap:wrap}
  #yq-ask button{font-family:inherit;border-radius:999px;padding:7px 14px;font-weight:700;cursor:pointer;border:1px solid var(--gold);font-size:.85rem}
  #yq-ask .yes{background:var(--gold);color:var(--on-gold)}
  #yq-ask .no{background:transparent;color:var(--gold-light)}
  @media (max-width:760px){#yq-ask{bottom:200px;right:12px}}
  @media (max-width:760px){#yq-glow{display:none}#yq-mascot{width:56px}.yq-bubble{width:180px;font-size:.8rem}
    .yq-voice{width:30px;height:30px;font-size:13px}#yq-theme{width:36px;height:36px;font-size:16px}}
  `;
  const style = D.createElement('style'); style.textContent = css; D.head.appendChild(style);

  // ===== الوضع الليلي/النهاري =====
  const themeBtn = D.createElement('button'); themeBtn.id = 'yq-theme'; D.body.appendChild(themeBtn);
  function savedTheme() {
    try { const s = localStorage.getItem('yq-theme'); if (s) return s; } catch (e) {}
    const h = new Date().getHours();
    return (h >= 6 && h < 18) ? 'light' : 'dark';   // تلقائي حسب وقت اليوم
  }
  function applyTheme(t) {
    H.setAttribute('data-yq-theme', t);
    themeBtn.textContent = t === 'light' ? '🌙' : '☀️';
    themeBtn.title = t === 'light' ? 'الوضع الليلي' : 'الوضع النهاري';
  }
  applyTheme(savedTheme());

  const glow = D.createElement('div'); glow.id = 'yq-glow'; D.body.appendChild(glow);

  // ===== نجوم تطلع ببطء + شهاب بين فترة وفترة =====
  (function stars() {
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const app = D.querySelector('.stApp');
    const cv = D.createElement('canvas'); cv.id = 'yq-stars';
    cv.style.cssText = 'position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:-1';
    if (app) app.prepend(cv); else { cv.style.zIndex = '0'; D.body.appendChild(cv); }
    const ctx = cv.getContext('2d');
    let W = 0, Hh = 0;
    function resize() {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      W = innerWidth; Hh = innerHeight;
      cv.width = W * dpr; cv.height = Hh * dpr; ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize(); addEventListener('resize', resize);
    const N = innerWidth < 760 ? 28 : 55;
    const rnd = (a, b) => a + Math.random() * (b - a);
    const mk = (y) => ({ x: rnd(0, W), y: (y === undefined ? rnd(0, Hh) : y), r: rnd(.6, 2.1), vy: rnd(.08, .35), vx: rnd(-.08, .08),
                         tw: rnd(0, Math.PI * 2), ts: rnd(.01, .035), em: Math.random() < .18 });
    const ps = Array.from({ length: N }, () => mk());
    let meteor = null, nextMeteor = performance.now() + rnd(3000, 7000);
    function draw(t) {
      if (!D.hidden) {
        const light = H.getAttribute('data-yq-theme') === 'light';
        ctx.clearRect(0, 0, W, Hh);
        for (const p of ps) {
          p.y -= p.vy; p.x += p.vx + Math.sin(t / 2000 + p.tw) * .05; p.tw += p.ts;
          if (p.y < -10) Object.assign(p, mk(Hh + 10));
          const a = (.25 + .55 * (0.5 + 0.5 * Math.sin(p.tw))) * (light ? .7 : 1);
          const c = p.em ? (light ? `rgba(95,138,114,${a})` : `rgba(80,200,150,${a * .8})`)
                         : (light ? `rgba(176,141,74,${a})` : `rgba(245,220,138,${a})`);
          ctx.beginPath(); ctx.fillStyle = c; ctx.shadowColor = c; ctx.shadowBlur = p.r * 6;
          ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2); ctx.fill();
        }
        ctx.shadowBlur = 0;
        if (!meteor && t > nextMeteor) meteor = { x: rnd(W * .3, W), y: rnd(0, Hh * .35), vx: -rnd(7, 11), vy: rnd(2.5, 4), life: 1 };
        if (meteor) {
          const m = meteor, len = 14;
          const g = ctx.createLinearGradient(m.x, m.y, m.x - m.vx * len, m.y - m.vy * len);
          g.addColorStop(0, light ? `rgba(176,141,74,${m.life})` : `rgba(255,243,196,${m.life})`); g.addColorStop(1, 'rgba(212,175,55,0)');
          ctx.strokeStyle = g; ctx.lineWidth = 2; ctx.lineCap = 'round';
          ctx.beginPath(); ctx.moveTo(m.x, m.y); ctx.lineTo(m.x - m.vx * len, m.y - m.vy * len); ctx.stroke();
          m.x += m.vx; m.y += m.vy; m.life -= .012;
          if (m.life <= 0 || m.x < -50 || m.y > Hh + 50) { meteor = null; nextMeteor = t + rnd(6000, 12000); }
        }
      }
      requestAnimationFrame(draw);
    }
    requestAnimationFrame(draw);
  })();

  // ===== نور =====
  const root = D.createElement('div');
  root.id = 'yq-mascot';
  root.title = 'نور — انقر لأتكلم، وانقر أثناء كلامي لأسكت';
  root.innerHTML = `
  <div class="yq-bubble"><span class="yq-name">نور:</span><span class="yq-text"></span></div>
  <button class="yq-voice" title="تشغيل/إيقاف الصوت">🔇</button>
  <svg class="yq-body" viewBox="0 0 100 140" width="100%">
    <defs>
      <linearGradient id="yqGold" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#fbe7a1"/><stop offset=".45" stop-color="#d4af37"/><stop offset="1" stop-color="#8f6d1c"/>
      </linearGradient>
      <radialGradient id="yqLight" cx=".5" cy=".45" r=".65">
        <stop offset="0" stop-color="#fffbe8"/><stop offset=".6" stop-color="#ffe08a"/><stop offset="1" stop-color="#e9b440"/>
      </radialGradient>
    </defs>
    <path d="M50 1 a7 7 0 1 0 7 9 a5.2 5.2 0 1 1 -7 -9z" fill="#f5dc8a"/>
    <rect x="47" y="12" width="6" height="8" rx="2" fill="url(#yqGold)"/>
    <path d="M28 36 Q50 10 72 36 Z" fill="url(#yqGold)"/>
    <rect x="24" y="35" width="52" height="7" rx="3.5" fill="#8f6d1c"/>
    <rect x="21" y="41" width="58" height="70" rx="17" fill="url(#yqGold)"/>
    <rect class="yq-light" x="29" y="48" width="42" height="55" rx="13" fill="url(#yqLight)"/>
    <g class="yq-eyes">
      <ellipse cx="41" cy="69" rx="6.5" ry="7.5" fill="#fff"/>
      <ellipse cx="59" cy="69" rx="6.5" ry="7.5" fill="#fff"/>
      <g class="yq-pupils">
        <circle cx="41" cy="69" r="3.6" fill="#1b1308"/><circle cx="59" cy="69" r="3.6" fill="#1b1308"/>
        <circle cx="42.3" cy="67.5" r="1.1" fill="#fff"/><circle cx="60.3" cy="67.5" r="1.1" fill="#fff"/>
      </g>
    </g>
    <circle cx="34" cy="81" r="3.4" fill="#e8846b" opacity=".55"/>
    <circle cx="66" cy="81" r="3.4" fill="#e8846b" opacity=".55"/>
    <path class="yq-smile" d="M44 83 Q50 89 56 83" stroke="#5a3b0a" stroke-width="2.6" fill="none" stroke-linecap="round"/>
    <ellipse class="yq-open" cx="50" cy="86" rx="4.6" ry="4" fill="#5a3b0a"/>
    <rect x="28" y="110" width="44" height="8" rx="4" fill="#8f6d1c"/>
    <rect x="33" y="118" width="9" height="9" rx="3" fill="url(#yqGold)"/>
    <rect x="58" y="118" width="9" height="9" rx="3" fill="url(#yqGold)"/>
  </svg>`;
  D.body.appendChild(root);

  const body = root.querySelector('.yq-body');
  const pupils = root.querySelector('.yq-pupils');
  const textEl = root.querySelector('.yq-text');
  const voiceBtn = root.querySelector('.yq-voice');

  let voiceOn = false;
  try { voiceOn = localStorage.getItem('yq-voice') === '1'; } catch (e) {}
  function paintVoice() { voiceBtn.textContent = voiceOn ? '🔊' : '🔇'; voiceBtn.classList.toggle('on', voiceOn); }
  paintVoice();

  // نور ثابت في الزاوية تحت يمين، فوق مربع الكتابة
  const mouse = { x: innerWidth / 2, y: innerHeight / 2 };
  const size = () => { const r = body.getBoundingClientRect(); return { w: r.width || 92, h: r.height || 130 }; };
  const home = () => { const s = size(); return { x: innerWidth - s.w - 18, y: innerHeight - s.h - 115 }; };
  const pos = home();
  let tilt = 0;

  D.addEventListener('mousemove', (e) => {
    mouse.x = e.clientX; mouse.y = e.clientY;
    glow.style.transform = `translate(${e.clientX}px,${e.clientY}px)`;
  }, { passive: true });

  function frame(t) {
    const target = home();
    const dx = target.x - pos.x;
    pos.x += dx * 0.08; pos.y += (target.y - pos.y) * 0.08;
    tilt += (Math.max(-16, Math.min(16, dx * 0.06)) - tilt) * 0.1;
    const bob = Math.sin(t / 450) * 4;
    root.style.transform = `translate(${pos.x}px,${pos.y}px)`;
    body.style.transform = `translateY(${bob}px) rotate(${tilt}deg)`;
    const r = body.getBoundingClientRect();
    const ex = r.left + r.width / 2, ey = r.top + r.height * 0.49;
    const ang = Math.atan2(mouse.y - ey, mouse.x - ex);
    const dist = Math.min(3, Math.hypot(mouse.x - ex, mouse.y - ey) / 40);
    pupils.setAttribute('transform', `translate(${Math.cos(ang) * dist} ${Math.sin(ang) * dist})`);
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);

  (function blink() {
    root.classList.add('blink');
    setTimeout(() => root.classList.remove('blink'), 140);
    setTimeout(blink, 2500 + Math.random() * 3000);
  })();

  let typeTimer = null, hideTimer = null, talkTimer = null;
  function talking(on) { root.classList.toggle('talking', on); }

  // ===== الصوت: ملف صوتي واضح من السيرفر (edge-tts) =====
  let audio = null, pendingAudio = '';
  function stopAudio() { if (audio) { try { audio.pause(); } catch (e) {} audio = null; } talking(false); }
  function playAudio(b64) {
    if (!voiceOn || !b64) return false;
    stopAudio();
    try {
      const a = new Audio('data:audio/mpeg;base64,' + b64);
      audio = a;
      a.onplay = () => talking(true);
      a.onended = () => { talking(false); if (audio === a) audio = null; };
      a.onerror = () => talking(false);
      const p = a.play();
      if (p && p.catch) p.catch(() => { talking(false); audio = null; pendingAudio = b64; say('اضغط عليّ لأقرأ لك الإجابة 🔊'); });
      pendingAudio = '';
      return true;
    } catch (e) { return false; }
  }

  function say(text, b64) {
    clearInterval(typeTimer); clearTimeout(hideTimer); clearTimeout(talkTimer);
    textEl.textContent = '';
    root.classList.add('show');
    const usingVoice = playAudio(b64);
    if (!usingVoice) talking(true);
    let i = 0;
    typeTimer = setInterval(() => {
      textEl.textContent = text.slice(0, ++i);
      if (i >= text.length) { clearInterval(typeTimer); if (!usingVoice) talkTimer = setTimeout(() => talking(false), 300); }
    }, 28);
    hideTimer = setTimeout(() => root.classList.remove('show'), Math.max(4000, text.length * 80));
  }

  themeBtn.addEventListener('click', () => {
    const t = H.getAttribute('data-yq-theme') === 'light' ? 'dark' : 'light';
    try { localStorage.setItem('yq-theme', t); } catch (e) {}
    applyTheme(t);
    say(t === 'light' ? 'صباح النور ☀️' : 'مساء الخير 🌙');
  });

  const tips = [
    'مرحبًا! أنا نور، مرشدك في منصة اليقين 🌙',
    'اضغط زر السماعة فوق رأسي لأقرأ لك الإجابات بصوتي 🔊',
    'جرّب قسم القرآن الكريم واستمع لقارئك المفضّل 📖',
    'تقدر تشوف مواقيت الصلاة وأقرب مسجد لك من قسم الصلاة 🕌',
    'زر ☀️/🌙 فوق يغيّر بين الوضع النهاري والليلي.',
    '«وقل رب زدني علمًا» — العلم نور.'
  ];
  let tipIdx = 0;
  root.addEventListener('click', (e) => {
    if (e.target.closest('.yq-voice')) return;
    if (audio) { stopAudio(); say('تمام، سكتّ 🤫'); return; }
    if (pendingAudio && voiceOn) { const b = pendingAudio; pendingAudio = ''; say('تفضّل 🔊', b); return; }
    say(tips[tipIdx++ % tips.length]);
  });

  function setVoice(on) {
    voiceOn = on; paintVoice();
    try { localStorage.setItem('yq-voice', voiceOn ? '1' : '0'); } catch (e) {}
    if (voiceOn) say('تم تشغيل الصوت 🔊 سأقرأ لك الإجابات.');
    else { stopAudio(); say('تم إيقاف الصوت 🔇'); }
  }
  voiceBtn.addEventListener('click', (e) => { e.stopPropagation(); e.preventDefault(); setVoice(!voiceOn); });

  D.addEventListener('focusin', (e) => {
    if (audio) return;
    if (e.target.closest && e.target.closest('[data-testid="stChatInput"]')) say('أنا أسمعك... اكتب سؤالك براحتك ✍️');
  });


  // ===== تذكير الصلاة: بعد كل صلاة بـ ١٥–٢٠ دقيقة يسأل نور: هل صليت؟ =====
  (function prayerReminder() {
    const NAMES = { Fajr: 'الفجر', Dhuhr: 'الظهر', Asr: 'العصر', Maghrib: 'المغرب', Isha: 'العشاء' };
    const ORDER = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'];
    const UNTIL = { Fajr: 'Sunrise', Dhuhr: 'Asr', Asr: 'Maghrib', Maghrib: 'Isha', Isha: null };
    const S = { get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
                set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} } };
    const p2 = n => String(n).padStart(2, '0');
    const dkey = d => `${d.getFullYear()}-${p2(d.getMonth() + 1)}-${p2(d.getDate())}`;
    const at = (t) => { const [h, m] = t.slice(0, 5).split(':').map(Number); const d = new Date(); d.setHours(h, m, 0, 0); return d; };

    const card = D.createElement('div'); card.id = 'yq-ask'; D.body.appendChild(card);
    let showing = null;

    async function timesToday() {
      const loc = S.get('yq-loc'); if (!loc) return null;
      const method = S.get('yq-method') || 4, d = new Date();
      const ds = `${p2(d.getDate())}-${p2(d.getMonth() + 1)}-${d.getFullYear()}`;
      const key = `yq-pt-${ds}-${loc.lat.toFixed(2)}-${loc.lon.toFixed(2)}-${method}`;
      let data = S.get(key);
      if (!data) {
        try {
          const j = await (await fetch(`https://api.aladhan.com/v1/timings/${ds}?latitude=${loc.lat}&longitude=${loc.lon}&method=${method}`)).json();
          data = j.data; if (data) S.set(key, data);
        } catch (e) { return null; }
      }
      return data ? data.timings : null;
    }

    function hide() { card.classList.remove('show'); showing = null; }

    function ask(p, sk) {
      if (showing === sk) return;
      showing = sk;
      const snooze = S.get('yq-ask') || {}; snooze[sk] = Date.now() + 10 * 60000; S.set('yq-ask', snooze);
      root.classList.remove('show');
      card.innerHTML = `<div class="q">🕌 من فضلك أخبرني، هل صليت صلاة <b>${NAMES[p]}</b>؟</div>
        <div class="row"><button class="yes">✅ نعم صليت</button><button class="no">⏰ ليس بعد، ذكّرني بعد ١٠ دقائق</button></div>`;
      card.classList.add('show');
      talking(true); setTimeout(() => talking(false), 900);
      card.querySelector('.yes').onclick = () => {
        const log = S.get('yq-log') || {}, k = dkey(new Date());
        log[k] = log[k] || {}; log[k][p] = true; S.set('yq-log', log);
        hide(); say('تقبّل الله منك 🤲 سجّلتها لك ✓');
      };
      card.querySelector('.no').onclick = () => {
        const sn = S.get('yq-ask') || {}; sn[sk] = Date.now() + 10 * 60000; S.set('yq-ask', sn);
        hide(); say('تمام، بذكّرك بعد ١٠ دقائق. الصلاة على وقتها من أحب الأعمال إلى الله 🌿');
      };
      if (D.hidden && 'Notification' in window && Notification.permission === 'granted') {
        try {
          const n = new Notification('منصة اليقين 🕌', { body: `من فضلك أخبرني، هل صليت صلاة ${NAMES[p]}؟`, tag: 'yq-' + sk });
          n.onclick = () => { window.focus(); n.close(); };
        } catch (e) {}
      }
    }

    async function check() {
      if (S.get('yq-remind') === false) { if (showing) hide(); return; }
      const T = await timesToday(); if (!T) return;
      const now = new Date(), k = dkey(now), day = (S.get('yq-log') || {})[k] || {}, sn = S.get('yq-ask') || {};
      for (let i = 0; i < ORDER.length; i++) {
        const p = ORDER[i], sk = k + '-' + p;
        if (day[p]) { if (showing === sk) hide(); continue; }
        const delay = 15 + ((now.getDate() * 7 + i * 3) % 6);          // بين ١٥ و٢٠ دقيقة
        const askAt = new Date(at(T[p]).getTime() + delay * 60000);
        const end = UNTIL[p] ? at(T[UNTIL[p]]) : (() => { const d = new Date(); d.setHours(23, 59, 59, 0); return d; })();
        if (now >= askAt && now < end) {
          if (showing === sk) return;
          if (sn[sk] && Date.now() < sn[sk]) continue;
          ask(p, sk); return;
        }
        if (showing === sk && now >= end) hide();
      }
    }
    // تنظيف التذكيرات القديمة
    try { const sn = S.get('yq-ask') || {}; const k = dkey(new Date()); Object.keys(sn).forEach(x => { if (!x.startsWith(k)) delete sn[x]; }); S.set('yq-ask', sn); } catch (e) {}
    setTimeout(check, 5000);
    setInterval(check, 30000);
  })();

  let last = { id: -1, section: null };
  window.__yaqeenV4 = {
    update(state) {
      if (!state) return;
      if (state.section !== last.section) {
        const first = last.section === null;
        last.section = state.section;
        if (state.greeting) setTimeout(() => say(state.greeting), first ? 900 : 100);
      }
      if (state.id !== last.id) {
        const prev = last.id; last.id = state.id;
        if (prev === -1) return;
        if (state.kind === 'thinking') { stopAudio(); say('لحظة... أبحث لك في الأدلة 📚'); }
        if (state.kind === 'answer') say('تفضّل، هذه الإجابة ✨', state.audio);
      }
    }
  };
})();
"""


# =====================================================
# 4) صوت نور — صوت سعودي واضح من مكتبة edge-tts (مجانية)
# =====================================================
VOICE = "ar-SA-HamedNeural"  # للصوت النسائي: "ar-SA-ZariyahNeural"


def clean_for_speech(text: str) -> str:
    t = re.sub(r"`[^`]*`", " ", text or "")
    t = re.sub(r"https?://\S+", " ", t)
    t = re.sub(r"[#*_>~|\[\]{}]", " ", t)
    t = re.sub(r"[^\w\s.,،؛:!?؟()«»\"'\-]", " ", t)  # يشيل الإيموجي والرموز
    t = re.sub(r"\s+", " ", t).strip()
    return t[:1500]


@st.cache_data(show_spinner=False, max_entries=200)
def tts_base64(text: str, voice: str = VOICE) -> str:
    """يحوّل النص لملف صوت mp3 ويرجعه base64. لو فشل يرجع نص فاضي."""
    if not text:
        return ""
    try:
        import edge_tts
    except ImportError:
        print("edge-tts غير مثبتة: python -m pip install edge-tts")
        return ""

    async def run():
        data = b""
        async for chunk in edge_tts.Communicate(text, voice, rate="-5%").stream():
            if chunk["type"] == "audio":
                data += chunk["data"]
        return data

    try:
        audio = asyncio.run(run())
    except Exception as e:
        print("TTS error:", e)
        return ""
    return base64.b64encode(audio).decode() if audio else ""


def mascot(state_id: str, kind: str, section: str, greeting: str = "", text: str = ""):
    state = {"id": state_id, "kind": kind, "section": section, "greeting": greeting, "audio": ""}
    if kind == "answer" and text and not text.startswith("⚠️"):
        state["audio"] = tts_base64(clean_for_speech(text))

    loader = """
<script>
(function () {
  var P = (window.parent && window.parent !== window) ? window.parent : window;
  try {
    if (!P.__yaqeenV4) {
      var s = P.document.createElement('script');
      s.textContent = CODE;
      P.document.head.appendChild(s);
    }
    P.__yaqeenV4 && P.__yaqeenV4.update(STATE);
  } catch (e) { console.error('Yaqeen mascot:', e); }
})();
</script>
""".replace("CODE", json.dumps(MASCOT_JS)).replace("STATE", json.dumps(state))
    components.html(loader, height=0)


def js_data(obj) -> str:
    """تحويل بيانات بايثون لـ JSON آمن داخل <script>"""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


# =====================================================
# 5) أداة مشتركة للإطارات: الخطوط + مزامنة الوضع الليلي/النهاري
# =====================================================
FRAME_HEAD = r"""
<meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Kufi+Arabic:wght@400;500;600;700&family=Amiri:wght@400;700&family=Amiri+Quran&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
:root{--text:#f2ecdf;--muted:#a9a293;--gold:#c9a45c;--gold-l:#e9cd8f;--gold-dark:#8d6e33;--surface:rgba(26,29,38,.72);--surface-2:rgba(255,255,255,.04);
  --border:rgba(201,164,92,.22);--border-s:rgba(201,164,92,.55);--accent:#3f9d7a;--accent-soft:rgba(63,157,122,.16);
  --gold-soft:rgba(201,164,92,.12);--shadow:0 18px 40px rgba(0,0,0,.45);--on-gold:#14110a;color-scheme:dark}
[data-theme="light"]{--text:#2b3830;--muted:#68776d;--gold:#b08d4a;--gold-l:#8c6b2a;--gold-dark:#7a5c22;--surface:rgba(255,255,255,.62);--surface-2:rgba(95,138,114,.07);
  --border:rgba(120,145,128,.30);--border-s:rgba(176,141,74,.55);--accent:#5f8a72;--accent-soft:rgba(95,138,114,.14);
  --gold-soft:rgba(176,141,74,.12);--shadow:0 18px 40px rgba(60,80,65,.14);--on-gold:#fff;color-scheme:light}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:var(--text);font-family:'Noto Kufi Arabic',sans-serif;direction:rtl}
.card{background:var(--surface);border:1px solid var(--border);border-radius:22px;padding:16px 18px;
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);box-shadow:var(--shadow);animation:rise .6s ease both}
@keyframes rise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
button{font-family:inherit;cursor:pointer}
.btn{border:1px solid var(--border-s);background:var(--gold-soft);color:var(--gold-l);border-radius:999px;padding:6px 14px;font-size:.85rem;font-weight:600;transition:all .2s}
.btn:hover,.btn.on{background:var(--gold);color:var(--on-gold)}
.muted{color:var(--muted)}
::-webkit-scrollbar{width:7px;height:7px}::-webkit-scrollbar-thumb{background:var(--border);border-radius:8px}
@media (prefers-reduced-motion: reduce){*{animation:none!important;transition:none!important}}
</style>
<script>
(function(){
  function sync(){ var t='dark'; try{ t = parent.document.documentElement.getAttribute('data-yq-theme') || 'dark'; }catch(e){}
    document.documentElement.setAttribute('data-theme', t); }
  sync();
  try{ new MutationObserver(sync).observe(parent.document.documentElement, {attributes:true, attributeFilter:['data-yq-theme']}); }catch(e){}
  // الإطار يكبر ويصغر حسب محتواه (مهم للجوال)
  addEventListener('DOMContentLoaded', function(){
    function fit(){ try{ if (frameElement) { var h = (document.body.scrollHeight + 8) + 'px';
      frameElement.style.height = h; frameElement.setAttribute('height', parseInt(h));
      if (frameElement.parentElement) frameElement.parentElement.style.height = h; } }catch(e){} }
    try{ new ResizeObserver(fit).observe(document.body); }catch(e){}
    fit();
  });
})();
</script>
"""

# =====================================================
# 6) مواقيت الصلاة + القبلة + أقرب المساجد (يشتغل في متصفح الزائر)
# =====================================================
PRAYER_HTML = r"""<!doctype html><html dir="rtl"><head>__HEAD__
<style>
.top{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap}
.loc{text-align:center}
.badge{display:inline-flex;align-items:center;gap:8px;background:var(--gold-soft);color:var(--gold-l);padding:7px 16px;border-radius:999px;
  font-weight:700;font-size:.9rem;border:1px solid var(--border-s)}
.badge .date{color:var(--muted);font-weight:600}
.badge i{color:var(--gold)}
/* شريط الصلاة القادمة */
.nextb{position:relative;overflow:hidden;margin-top:14px;border-radius:18px;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;
  background:linear-gradient(135deg,var(--gold-dark),var(--gold));color:#fff;box-shadow:0 10px 28px var(--gold-soft)}
.nextb::after{content:"";position:absolute;top:0;bottom:0;width:40%;left:-50%;background:linear-gradient(100deg,transparent,rgba(255,255,255,.22),transparent);
  transform:skewX(-20deg);animation:sweep 5s ease-in-out infinite}
@keyframes sweep{0%,60%{left:-50%}100%{left:130%}}
.nextb .lbl{font-size:.9rem;opacity:.9;font-weight:600}
.nextb .nname{font-family:'Amiri',serif;font-size:2rem;font-weight:700;line-height:1.3;display:flex;align-items:center;gap:10px}
.nextb .cd{font-size:1.5rem;font-weight:700;letter-spacing:1px;background:rgba(0,0,0,.2);padding:8px 18px;border-radius:14px;font-variant-numeric:tabular-nums}
/* كروت الصلوات */
.chips{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;margin-top:14px}
.chip{background:var(--surface-2);border:1px solid var(--border);border-radius:16px;padding:14px 6px;text-align:center;transition:transform .3s,border-color .3s,background .3s}
.chip:hover{transform:translateY(-4px);border-color:var(--gold)}
.chip .ic{font-size:1.5rem;color:var(--gold);margin-bottom:6px}
.chip .n{font-size:.85rem;color:var(--muted);font-weight:600}.chip .t{font-weight:700;font-size:1.05rem}
.chip.on{background:linear-gradient(160deg,var(--gold-soft),var(--accent-soft));border-color:var(--gold);transform:translateY(-4px);
  box-shadow:0 0 0 3px var(--gold-soft);animation:pulse 2.4s ease-in-out infinite}
.chip.on .n{color:var(--gold-l)}
@keyframes pulse{0%,100%{box-shadow:0 0 0 3px var(--gold-soft)}50%{box-shadow:0 0 0 7px var(--gold-soft)}}
.chip.past{opacity:.55}
.compact .chip{padding:9px 4px}.compact .chip .ic{font-size:1.15rem;margin-bottom:3px}.compact .nextb{padding:10px 18px}
.compact .nextb .nname{font-size:1.5rem}.compact .nextb .cd{font-size:1.15rem;padding:5px 14px}
.bar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px}
select{font-family:inherit;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:999px;padding:6px 12px;font-size:.85rem}
.grid2{display:grid;grid-template-columns:280px 1fr;gap:14px;margin-top:14px}
h3{margin:0 0 10px;font-size:1.05rem;color:var(--gold-l)}
.compass{position:relative;width:190px;height:190px;margin:8px auto;border-radius:50%;
  background:radial-gradient(circle,var(--surface-2) 0 55%,transparent 56%),conic-gradient(from 0deg,var(--gold-soft),var(--accent-soft),var(--gold-soft));
  border:1px solid var(--border-s)}
.compass .nn{position:absolute;top:6px;left:50%;transform:translateX(-50%);font-weight:700;color:var(--muted);font-size:.8rem}
.needle{position:absolute;left:50%;width:4px;height:78px;margin-left:-2px;transform-origin:50% 100%;
  background:linear-gradient(var(--gold),transparent);border-radius:4px;transition:transform 1.2s cubic-bezier(.2,.8,.2,1);top:calc(50% - 78px)}
.needle::before{content:"🕋";position:absolute;top:-26px;left:50%;transform:translateX(-50%);font-size:1.4rem}
.deg{text-align:center;font-weight:700;font-size:1.1rem;color:var(--gold-l)}
.mlist{max-height:440px;overflow:auto;display:flex;flex-direction:column;gap:8px;padding-left:4px}
.m{display:flex;align-items:center;gap:12px;background:var(--surface-2);border:1px solid var(--border);border-radius:16px;padding:10px 12px;
  transition:all .25s;animation:rise .5s ease both}
.m:hover{border-color:var(--border-s);transform:translateX(-3px)}
.m .ic{width:40px;height:40px;border-radius:12px;background:var(--accent-soft);display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex:none}
.m .info{flex:1;min-width:0}.m .nm{font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.m .ds{color:var(--muted);font-size:.8rem}
.m a{flex:none;text-decoration:none}
.msg{color:var(--muted);font-size:.9rem;padding:8px 0;line-height:1.9}
.tk{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:12px}
.tp{background:var(--surface-2);border:1px solid var(--border);border-radius:16px;padding:10px 4px;color:var(--text);display:flex;flex-direction:column;
  align-items:center;gap:6px;font-weight:700;font-size:.9rem;transition:all .25s}
.tp:hover{border-color:var(--border-s);transform:translateY(-2px)}
.tp .ck{width:30px;height:30px;border-radius:50%;border:2px solid var(--border-s);display:flex;align-items:center;justify-content:center;font-size:1rem;color:#fff}
.tp.done{background:var(--accent-soft);border-color:var(--accent)}
.tp.done .ck{background:var(--accent);border-color:var(--accent);animation:pop .45s ease}
.tp.later{opacity:.45}
@keyframes pop{0%{transform:scale(.3)}70%{transform:scale(1.25)}100%{transform:scale(1)}}
.week{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;margin-top:14px}
.wd{text-align:center}.wn{font-size:.72rem;color:var(--muted)}
.wc{margin-top:4px;border-radius:10px;padding:4px 0;font-size:.78rem;font-weight:700;background:var(--surface-2);border:1px solid var(--border)}
.wc.c5{background:var(--accent);color:#fff;border-color:var(--accent)}.wc.c3,.wc.c4{background:var(--accent-soft)}
.spin{display:inline-block;animation:sp 1s linear infinite}@keyframes sp{to{transform:rotate(360deg)}}
@media (max-width:720px){.chips{grid-template-columns:repeat(3,1fr)}.grid2{grid-template-columns:1fr}.nextb{justify-content:center;text-align:center}.nextb .nname{justify-content:center}}
</style></head><body>
<div class="card" id="main">
  <div class="loc"><span class="badge"><i class="fa-solid fa-location-dot"></i><span id="city">جاري تحديد موقعك <span class="spin">⏳</span></span><span class="date" id="date"></span></span></div>
  <div class="nextb"><div><div class="lbl">الصلاة القادمة</div><div class="nname"><i class="fa-solid fa-mosque" style="font-size:1.3rem;opacity:.85"></i><span id="nname">—</span></div></div><div class="cd" id="cd"></div></div>
  <div class="chips" id="chips"></div>
  <div class="bar" id="bar"></div>
</div>
<div class="grid2" id="extra" style="display:none">
  <div class="card"><h3>🧭 اتجاه القبلة</h3><div class="compass"><span class="nn">ش</span><div class="needle" id="needle"></div></div>
    <div class="deg" id="deg"></div><div class="msg" style="text-align:center">الزاوية من جهة الشمال باتجاه عقارب الساعة</div></div>
  <div class="card"><h3>🕌 أقرب المساجد لك</h3><div id="mosques" class="msg">جاري البحث <span class="spin">⏳</span></div></div>
</div>
<div class="card" id="track" style="display:none;margin-top:14px">
  <div class="top"><div><h3 style="margin:0">✅ سجل صلواتي</h3><div class="date" id="tsum"></div></div><div class="bar" id="rbar" style="margin:0"></div></div>
  <div class="tk" id="tk"></div>
  <div class="week" id="week"></div>
  <div class="msg" id="nmsg"></div>
</div>
<script>
const MODE = "__MODE__";
const $ = s => document.querySelector(s);
const PR = [["Fajr","الفجر","fa-star-and-crescent"],["Sunrise","الشروق","fa-mountain-sun"],["Dhuhr","الظهر","fa-sun"],["Asr","العصر","fa-cloud-sun"],["Maghrib","المغرب","fa-cloud-moon"],["Isha","العشاء","fa-moon"]];
if (MODE !== 'full') document.getElementById('main').classList.add('compact');
const METHODS = [[4,"أم القرى"],[3,"رابطة العالم الإسلامي"],[5,"الهيئة المصرية"],[8,"منطقة الخليج"],[9,"الكويت"],[10,"قطر"],[16,"دبي"],[2,"أمريكا الشمالية"],[1,"كراتشي"],[13,"تركيا"],[12,"فرنسا"]];
const KAABA = {lat:21.4225, lon:39.8262};
const store = {get(k){try{return JSON.parse(localStorage.getItem(k))}catch(e){return null}}, set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const toAr = s => String(s).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const pad = n => String(n).padStart(2,'0');
function fmt12(t){ let [h,m] = t.slice(0,5).split(':').map(Number); const s = h < 12 ? 'ص' : 'م'; h = h % 12 || 12; return toAr(h + ':' + pad(m)) + ' ' + s; }
function withTimeout(p, ms){ return Promise.race([p, new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout')), ms))]); }

let loc = null, data = null, method = store.get('yq-method') || 4, timer = null;

async function getLocation(force){
  const saved = store.get('yq-loc');
  if (saved && !force && Date.now() - saved.ts < 6*3600e3) return saved;
  let L = null;
  try {
    const p = await withTimeout(new Promise((res, rej) => navigator.geolocation
      ? navigator.geolocation.getCurrentPosition(res, rej, {enableHighAccuracy:false, timeout:12000, maximumAge:600000}) : rej()), 15000);
    L = {lat:p.coords.latitude, lon:p.coords.longitude, precise:true};
  } catch(e) {}
  if (!L) {
    try { const j = await withTimeout(fetch('https://get.geojs.io/v1/ip/geo.json').then(r=>r.json()), 8000);
          L = {lat:+j.latitude, lon:+j.longitude, city:j.city, precise:false}; } catch(e) {}
  }
  if (!L) L = saved || {lat:KAABA.lat, lon:KAABA.lon, city:'مكة المكرمة', precise:false, fallback:true};
  try {
    const j = await withTimeout(fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${L.lat}&longitude=${L.lon}&localityLanguage=ar`).then(r=>r.json()), 8000);
    L.city = j.city || j.locality || j.principalSubdivision || L.city; L.country = j.countryName || '';
  } catch(e) {}
  L.ts = Date.now(); store.set('yq-loc', L); return L;
}

async function getTimes(){
  const d = new Date(), ds = `${pad(d.getDate())}-${pad(d.getMonth()+1)}-${d.getFullYear()}`;
  const key = `yq-pt-${ds}-${loc.lat.toFixed(2)}-${loc.lon.toFixed(2)}-${method}`;
  const c = store.get(key); if (c) return c;
  const j = await withTimeout(fetch(`https://api.aladhan.com/v1/timings/${ds}?latitude=${loc.lat}&longitude=${loc.lon}&method=${method}`).then(r=>r.json()), 12000);
  if (!j || !j.data) throw new Error('no data');
  store.set(key, j.data); return j.data;
}

function toDate(t, addDay){ const [h,m] = t.slice(0,5).split(':').map(Number); const d = new Date(); d.setHours(h, m, 0, 0); if (addDay) d.setDate(d.getDate()+1); return d; }

function nextPrayer(){
  const now = new Date();
  for (const [k, n] of PR) { if (k === 'Sunrise') continue; const d = toDate(data.timings[k]); if (d > now) return {k, n, d}; }
  return {k:'Fajr', n:'الفجر', d: toDate(data.timings.Fajr, true)};
}

function render(){
  const T = data.timings, h = data.date && data.date.hijri;
  $('#city').textContent = (loc.city || 'موقعك') + (loc.country ? '، ' + loc.country : '');
  $('#date').textContent = h ? `| ${toAr(h.day)} ${h.month.ar} ${toAr(h.year)} هـ` : '';
  tick();
  clearInterval(timer); timer = setInterval(tick, 1000);
  const bar = $('#bar'); bar.innerHTML = '';
  if (!loc.precise) { const s = document.createElement('span'); s.className = 'muted'; s.style.fontSize = '.8rem';
    s.textContent = 'الموقع تقريبي — '; bar.appendChild(s); }
  const b = document.createElement('button'); b.className = 'btn'; b.textContent = '📍 حدّد موقعي بدقة';
  b.onclick = () => start(true); bar.appendChild(b);
  if (MODE === 'full') {
    const sel = document.createElement('select');
    METHODS.forEach(([v, n]) => { const o = document.createElement('option'); o.value = v; o.textContent = 'طريقة الحساب: ' + n; if (v == method) o.selected = true; sel.appendChild(o); });
    sel.onchange = () => { method = +sel.value; store.set('yq-method', method); start(false); };
    bar.appendChild(sel);
  }
}

function tick(){
  const nx = nextPrayer(), now = new Date();
  if (now.getSeconds() === 0) renderTrack();
  let s = Math.max(0, Math.floor((nx.d - now) / 1000));
  $('#nname').textContent = nx.n;
  $('#cd').textContent = 'بعد ' + toAr(`${pad(Math.floor(s/3600))}:${pad(Math.floor(s%3600/60))}:${pad(s%60)}`);
  const chips = $('#chips');
  chips.innerHTML = PR.map(([k, n, ic]) => {
    const past = toDate(data.timings[k]) < now && !(nx.k === k);
    return `<div class="chip ${nx.k === k ? 'on' : ''} ${past && k !== 'Sunrise' ? 'past' : ''}"><div class="ic"><i class="fa-solid ${ic}"></i></div><div class="n">${n}</div><div class="t">${fmt12(data.timings[k])}</div></div>`;
  }).join('');
  if (now.getHours() === 0 && now.getMinutes() === 0 && now.getSeconds() < 2) start(false);
}

function rad(x){ return x * Math.PI / 180; }
function distM(a, b){ const R = 6371000, dLa = rad(b.lat-a.lat), dLo = rad(b.lon-a.lon);
  const x = Math.sin(dLa/2)**2 + Math.cos(rad(a.lat))*Math.cos(rad(b.lat))*Math.sin(dLo/2)**2; return 2*R*Math.asin(Math.sqrt(x)); }
function qibla(lat, lon){ const p1 = rad(lat), p2 = rad(KAABA.lat), dl = rad(KAABA.lon - lon);
  const y = Math.sin(dl)*Math.cos(p2), x = Math.cos(p1)*Math.sin(p2) - Math.sin(p1)*Math.cos(p2)*Math.cos(dl);
  return (Math.atan2(y, x)*180/Math.PI + 360) % 360; }

async function mosques(){
  const box = $('#mosques');
  box.innerHTML = 'جاري البحث عن المساجد القريبة <span class="spin">⏳</span>';
  const gmaps = `https://www.google.com/maps/search/%D9%85%D8%B3%D8%AC%D8%AF/@${loc.lat},${loc.lon},15z`;
  try {
    // نحفظ النتيجة يوم كامل عشان ما نطلبها كل مرة
    const ck = `yq-mosq-${loc.lat.toFixed(3)}-${loc.lon.toFixed(3)}`;
    let list = (store.get(ck) || {}).ts > Date.now() - 86400e3 ? store.get(ck).list : null;
    if (!list) {
      list = [];
      const seen = new Set();
      const add = (name, lat, lon, id) => {
        lat = +lat; lon = +lon; if (!isFinite(lat) || !isFinite(lon)) return;
        const key = id || (lat.toFixed(4) + ',' + lon.toFixed(4)); if (seen.has(key)) return; seen.add(key);
        if (!name || /^mosque$/i.test(name)) name = 'مسجد';
        list.push({name, lat, lon});
      };
      // ١) Nominatim (الأسرع والأثبت) — نوسّع البحث إذا ما لقينا كفاية
      for (const d of [0.02, 0.06, 0.15]) {
        const vb = `${loc.lon-d},${loc.lat+d},${loc.lon+d},${loc.lat-d}`;
        const rs = await Promise.all(['مسجد', 'جامع', 'mosque'].map(w =>
          withTimeout(fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&q=${encodeURIComponent(w)}&viewbox=${vb}&bounded=1&limit=40&accept-language=ar`)
            .then(x => x.json()), 12000).catch(() => [])));
        rs.flat().filter(e => e.type === 'place_of_worship' || /مسجد|جامع|mosque|masjid/i.test(e.name || ''))
          .forEach(e => add(e.name || (e.display_name || '').split('،')[0].split(',')[0], e.lat, e.lon, e.osm_type + e.osm_id));
        if (list.length >= 5) break;
      }
      // ٢) احتياطي: Photon
      if (list.length < 3) {
        try {
          const j = await withTimeout(fetch(`https://photon.komoot.io/api/?q=mosque&lat=${loc.lat}&lon=${loc.lon}&limit=20&osm_tag=amenity:place_of_worship`).then(x=>x.json()), 10000);
          (j.features || []).forEach(f => add(f.properties && f.properties.name, f.geometry.coordinates[1], f.geometry.coordinates[0], 'p' + (f.properties && f.properties.osm_id)));
        } catch(e) {}
      }
      if (list.length) store.set(ck, {ts: Date.now(), list});
    }
    list.forEach(m => m.d = distM(loc, m)); list.sort((a,b) => a.d - b.d);
    if (!list.length) { box.innerHTML = `ما لقيت مساجد مسجّلة قريبة منك. <a class="btn" target="_blank" href="${gmaps}">ابحث في خرائط Google</a>`; return; }
    box.className = 'mlist';
    box.innerHTML = list.slice(0, 10).map((m, i) => {
      const dd = m.d < 1000 ? toAr(Math.round(m.d/10)*10) + ' م' : toAr((m.d/1000).toFixed(1)) + ' كم';
      const walk = Math.max(1, Math.round(m.d / 80));
      const url = `https://www.google.com/maps/dir/?api=1&destination=${m.lat},${m.lon}&travelmode=walking`;
      return `<div class="m" style="animation-delay:${i*0.05}s"><div class="ic">🕌</div><div class="info"><div class="nm"></div>
        <div class="ds">${dd} · ${toAr(walk)} دقيقة مشي تقريبًا</div></div><a class="btn" target="_blank" rel="noopener" href="${url}">الاتجاهات ↗</a></div>`;
    }).join('') + `<div class="msg">${loc.precise ? '' : 'الموقع تقريبي، اضغط «حدّد موقعي بدقة» لنتائج أدق. '}<a class="btn" target="_blank" rel="noopener" href="${gmaps}">عرض الكل في الخريطة</a></div>`;
    box.querySelectorAll('.nm').forEach((el, i) => el.textContent = list[i].name);
  } catch(e) {
    box.className = 'msg';
    box.innerHTML = `تعذّر جلب المساجد الآن. <a class="btn" target="_blank" rel="noopener" href="${gmaps}">ابحث في خرائط Google</a>`;
  }
}

// ===== سجل صلواتي + تفعيل التذكير =====
const PORDER = [["Fajr","الفجر"],["Dhuhr","الظهر"],["Asr","العصر"],["Maghrib","المغرب"],["Isha","العشاء"]];
const dkey = d => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
function renderTrack(){
  if (MODE !== 'full' || !data) return;
  $('#track').style.display = 'block';
  const log = store.get('yq-log') || {}, k = dkey(new Date()), day = log[k] || {}, now = new Date();
  $('#tk').innerHTML = PORDER.map(([p, n]) => {
    const done = !!day[p], due = toDate(data.timings[p]) <= now;
    return `<button class="tp ${done ? 'done' : ''} ${!due && !done ? 'later' : ''}" data-p="${p}" title="اضغط للتسجيل أو الإلغاء"><span class="ck">${done ? '✓' : ''}</span><span>${n}</span></button>`;
  }).join('');
  $('#tk').querySelectorAll('.tp').forEach(b => b.onclick = () => {
    const L = store.get('yq-log') || {}; L[k] = L[k] || {}; L[k][b.dataset.p] = !L[k][b.dataset.p]; store.set('yq-log', L); renderTrack();
  });
  let w = '';
  for (let i = 6; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const dd = log[dkey(d)] || {}, c = PORDER.filter(([p]) => dd[p]).length;
    w += `<div class="wd"><div class="wn">${i === 0 ? 'اليوم' : d.toLocaleDateString('ar', {weekday:'short'})}</div><div class="wc c${c}">${toAr(c)}/٥</div></div>`;
  }
  $('#week').innerHTML = w;
  const cnt = PORDER.filter(([p]) => day[p]).length;
  $('#tsum').textContent = cnt === 5 ? 'ما شاء الله، أتممت صلوات اليوم 🌟' : `صليت ${toAr(cnt)} من ٥ صلوات اليوم — اضغط على الصلاة لتسجيلها`;
  renderRBar();
}
function renderRBar(){
  const on = store.get('yq-remind') !== false;
  let N = null; try { N = parent.Notification || window.Notification; } catch(e) { N = window.Notification; }
  let h = `<button class="btn ${on ? 'on' : ''}" id="rt">${on ? '🔔 التذكير مفعّل' : '🔕 التذكير متوقف'}</button>`;
  if (N && on && N.permission !== 'granted') h += `<button class="btn" id="np">📲 فعّل إشعارات المتصفح</button>`;
  $('#rbar').innerHTML = h;
  $('#rt').onclick = () => { store.set('yq-remind', !on); renderRBar(); };
  const np = $('#np');
  if (np) np.onclick = async () => {
    $('#nmsg').dataset.set = '1';
    try { const r = await N.requestPermission(); $('#nmsg').textContent = r === 'granted' ? 'تم تفعيل الإشعارات ✅' : 'ما تم السماح بالإشعارات من المتصفح.'; }
    catch(e) { $('#nmsg').textContent = 'متصفحك ما يدعم الإشعارات.'; }
    renderRBar();
  };
  if (!$('#nmsg').dataset.set) $('#nmsg').textContent = on ? 'بعد كل صلاة بـ ١٥ إلى ٢٠ دقيقة يسألك نور إذا صليت، والموقع مفتوح.' : '';
}
addEventListener('storage', e => { if (e.key === 'yq-log' || e.key === 'yq-remind') renderTrack(); });

async function start(force){
  try {
    if (force || !loc) { $('#city').innerHTML = 'جاري تحديد موقعك <span class="spin">⏳</span>'; loc = await getLocation(force); }
    data = await getTimes();
    render();
    if (MODE === 'full') {
      $('#extra').style.display = 'grid';
      const q = qibla(loc.lat, loc.lon);
      $('#needle').style.transform = `rotate(${q}deg)`;
      $('#deg').textContent = toAr(q.toFixed(1)) + '°';
      mosques();
      renderTrack();
    }
  } catch(e) {
    $('#city').textContent = 'تعذّر جلب المواقيت، تأكد من الإنترنت';
    const bar = $('#bar'); bar.innerHTML = ''; const b = document.createElement('button'); b.className = 'btn'; b.textContent = '🔄 أعد المحاولة';
    b.onclick = () => start(true); bar.appendChild(b);
  }
}
start(false);
</script></body></html>"""


def prayer_widget(mode: str, height: int):
    html = PRAYER_HTML.replace("__HEAD__", FRAME_HEAD).replace("__MODE__", mode)
    components.html(html, height=height, scrolling=False)


# =====================================================
# 7) القرآن الكريم — كل القرّاء من mp3quran.net وكل السور
# =====================================================
SURAS = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل", "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس",
]

# احتياطي لو ما قدرنا نجيب القائمة الكاملة من الإنترنت
FALLBACK_RECITERS = [
    {"n": "مشاري راشد العفاسي", "s": "https://server8.mp3quran.net/afs/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "ماهر المعيقلي", "s": "https://server12.mp3quran.net/maher/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "عبدالرحمن السديس", "s": "https://server11.mp3quran.net/sds/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "سعود الشريم", "s": "https://server7.mp3quran.net/shur/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "سعد الغامدي", "s": "https://server7.mp3quran.net/s_gmd/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "ياسر الدوسري", "s": "https://server11.mp3quran.net/yasser/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "عبدالباسط عبدالصمد", "s": "https://server7.mp3quran.net/basit/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "محمد صديق المنشاوي", "s": "https://server10.mp3quran.net/minsh/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "محمود خليل الحصري", "s": "https://server13.mp3quran.net/husr/", "l": "", "r": "حفص عن عاصم - مرتل"},
    {"n": "ناصر القطامي", "s": "https://server6.mp3quran.net/qtm/", "l": "", "r": "حفص عن عاصم - مرتل"},
]

POPULAR = ["العفاسي", "المعيقلي", "السديس", "الشريم", "الغامدي", "الدوسري", "عبدالباسط", "عبد الباسط",
           "المنشاوي", "الحصري", "القطامي", "العجمي", "فارس عباد", "أبكر", "بليلة", "الجهني", "اللحيدان",
           "الطبلاوي", "الحذيفي", "البنا", "الكلباني", "هزاع البلوشي", "إسلام صبحي"]


@st.cache_data(ttl=86400, show_spinner=False)
def load_reciters():
    try:
        req = urllib.request.Request(
            "https://mp3quran.net/api/v3/reciters?language=ar", headers={"User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
        out = []
        for rc in data.get("reciters", []):
            ms = [m for m in (rc.get("moshaf") or []) if m.get("server")]
            if not ms:
                continue

            def score(m):
                name = m.get("name", "")
                return (("حفص" in name) * 2 + ("مرتل" in name), int(m.get("surah_total") or 0))

            m = max(ms, key=score)
            server = m["server"] if m["server"].endswith("/") else m["server"] + "/"
            total = int(m.get("surah_total") or 0)
            out.append({
                "n": (rc.get("name") or "").strip(),
                "s": server,
                "l": "" if total >= 114 else (m.get("surah_list") or ""),
                "r": m.get("name", ""),
            })

        def rank(x):
            for i, k in enumerate(POPULAR):
                if k in x["n"]:
                    return (0, i)
            return (1, 0)

        out.sort(key=rank)
        if out:
            return out
    except Exception as e:
        print("Reciters API error:", e)
    return FALLBACK_RECITERS


QURAN_HTML = r"""<!doctype html><html dir="rtl"><head>__HEAD__
<style>
.now{display:grid;grid-template-columns:auto 1fr;gap:18px;align-items:center}
.disc{width:96px;height:96px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:2.4rem;
  background:conic-gradient(from 0deg,var(--gold-soft),var(--accent-soft),var(--gold-soft));border:1px solid var(--border-s);
  box-shadow:0 0 0 6px var(--gold-soft)}
.playing .disc{animation:rot 8s linear infinite}@keyframes rot{to{transform:rotate(360deg)}}
.sname{font-family:'Amiri',serif;font-size:2rem;font-weight:700;color:var(--gold-l);line-height:1.4}
.rname{color:var(--muted);font-size:.92rem}
.eq{display:inline-flex;gap:3px;align-items:flex-end;height:16px;margin-right:8px;vertical-align:middle;opacity:0;transition:opacity .3s}
.playing .eq{opacity:1}.eq i{width:3px;background:var(--accent);border-radius:2px;animation:eq 1s ease-in-out infinite}
.eq i:nth-child(2){animation-delay:.2s}.eq i:nth-child(3){animation-delay:.4s}.eq i:nth-child(4){animation-delay:.1s}
@keyframes eq{0%,100%{height:4px}50%{height:16px}}
audio{width:100%;margin-top:10px;height:40px}
.ctrl{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}
.btn.on{background:var(--gold);color:var(--on-gold)}
.cols{display:grid;grid-template-columns:300px 1fr;gap:14px;margin-top:14px}
.col{display:flex;flex-direction:column;min-height:0}
.col h3{margin:0 0 8px;font-size:1rem;color:var(--gold-l);display:flex;justify-content:space-between;align-items:center}
.col h3 small{color:var(--muted);font-weight:500;font-size:.78rem}
input.search{width:100%;font-family:inherit;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:999px;
  padding:8px 14px;font-size:.9rem;outline:none;margin-bottom:10px}
input.search:focus{border-color:var(--border-s);box-shadow:0 0 0 3px var(--gold-soft)}
.list{overflow:auto;height:430px;padding-left:4px}
.rc{display:block;width:100%;text-align:right;background:transparent;border:1px solid transparent;border-radius:14px;padding:8px 10px;
  color:var(--text);margin-bottom:4px;transition:all .2s}
.rc:hover{background:var(--surface-2);border-color:var(--border)}
.rc.on{background:linear-gradient(135deg,var(--gold-soft),var(--accent-soft));border-color:var(--border-s)}
.rc .a{font-weight:700;font-size:.92rem}.rc .b{color:var(--muted);font-size:.72rem}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(128px,1fr));gap:8px;align-content:start}
.su{background:var(--surface-2);border:1px solid var(--border);border-radius:14px;padding:9px 10px;color:var(--text);
  display:flex;align-items:center;gap:8px;transition:all .2s;text-align:right}
.su:hover{border-color:var(--border-s);transform:translateY(-2px)}
.su .no{width:30px;height:30px;flex:none;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:.78rem;font-weight:700;
  background:var(--accent-soft);color:var(--accent)}
.su .nm{font-family:'Amiri',serif;font-size:1.08rem;font-weight:700}
.su.on{background:linear-gradient(135deg,var(--gold-soft),var(--accent-soft));border-color:var(--gold)}
.su.on .no{background:var(--gold);color:var(--on-gold)}
.su[disabled]{opacity:.3;cursor:not-allowed;transform:none}
.tabs{display:none;gap:8px;margin-top:12px}
@media (max-width:760px){
  .cols{grid-template-columns:1fr}.tabs{display:flex}.col.hide{display:none}
  .list{height:360px}.disc{width:70px;height:70px;font-size:1.8rem}.sname{font-size:1.6rem}
}
</style></head><body>
<div class="card" id="nowcard">
  <div class="now">
    <div class="disc">📖</div>
    <div>
      <div class="sname"><span id="sname">اختر سورة</span><span class="eq"><i></i><i></i><i></i><i></i></span></div>
      <div class="rname" id="rname"></div>
    </div>
  </div>
  <audio id="audio" controls preload="none"></audio>
  <div class="ctrl">
    <button class="btn" id="prev">⏮ السابقة</button>
    <button class="btn" id="next">التالية ⏭</button>
    <button class="btn" id="auto">🔁 تشغيل تلقائي للتالية</button>
  </div>
</div>
<div class="tabs"><button class="btn on" data-t="r">🎙️ القرّاء</button><button class="btn" data-t="s">📜 السور</button></div>
<div class="cols">
  <div class="card col" id="colR"><h3>🎙️ القرّاء <small id="rcount"></small></h3>
    <input class="search" id="rq" placeholder="ابحث عن قارئ..."><div class="list" id="rlist"></div></div>
  <div class="card col" id="colS"><h3>📜 السور <small>١١٤ سورة</small></h3>
    <input class="search" id="sq" placeholder="ابحث عن سورة أو رقمها..."><div class="list sgrid" id="slist"></div></div>
</div>
<script>
const R = __RECITERS__, S = __SURAS__;
const $ = s => document.querySelector(s);
const store = {get(k){try{return JSON.parse(localStorage.getItem(k))}catch(e){return null}}, set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const toAr = s => String(s).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const norm = s => (s||'').replace(/[أإآ]/g,'ا').replace(/ة/g,'ه').replace(/ى/g,'ي').replace(/\s+/g,'');
const audio = $('#audio');
let ri = 0, si = 0, auto = store.get('yq-q-auto') !== false;
const saved = store.get('yq-q');
if (saved) { const i = R.findIndex(r => r.s === saved.s); if (i >= 0) ri = i; si = saved.si || 0; }
R.forEach(r => r.set = r.l ? new Set(r.l.split(',').map(Number)) : null);
const has = (r, n) => !r.set || r.set.has(n);
$('#rcount').textContent = toAr(R.length) + ' قارئ';

function paintAuto(){ $('#auto').classList.toggle('on', auto); }
paintAuto();

function renderR(){
  const q = norm($('#rq').value);
  $('#rlist').innerHTML = R.map((r, i) => (!q || norm(r.n).includes(q))
    ? `<button class="rc ${i === ri ? 'on' : ''}" data-i="${i}"><div class="a"></div><div class="b"></div></button>` : '').join('');
  $('#rlist').querySelectorAll('.rc').forEach(b => { const r = R[+b.dataset.i]; b.querySelector('.a').textContent = r.n; b.querySelector('.b').textContent = r.r || '';
    b.onclick = () => pickR(+b.dataset.i); });
}
function renderS(){
  const q = norm($('#sq').value), r = R[ri];
  $('#slist').innerHTML = S.map((n, i) => {
    const no = i + 1;
    if (q && !norm(n).includes(q) && String(no) !== q) return '';
    return `<button class="su ${no === si ? 'on' : ''}" data-n="${no}" ${has(r, no) ? '' : 'disabled'}><span class="no">${toAr(no)}</span><span class="nm">${n}</span></button>`;
  }).join('');
  $('#slist').querySelectorAll('.su').forEach(b => b.onclick = () => play(+b.dataset.n));
}
function header(){
  $('#sname').textContent = si ? 'سورة ' + S[si-1] : 'اختر سورة';
  $('#rname').textContent = 'بصوت القارئ: ' + R[ri].n;
}
function pickR(i){
  ri = i; renderR(); renderS(); header();
  if (si && has(R[ri], si)) play(si, !audio.paused);
  if (matchMedia('(max-width:760px)').matches) showTab('s');
}
function play(n, keep){
  si = n; const r = R[ri];
  audio.src = r.s + String(n).padStart(3, '0') + '.mp3';
  store.set('yq-q', {s:r.s, si:n});
  header(); renderS();
  if (keep !== false) audio.play().catch(()=>{});
}
function step(d){
  const r = R[ri]; let n = si || 0;
  for (let k = 0; k < 114; k++) { n += d; if (n < 1 || n > 114) return; if (has(r, n)) return play(n); }
}
audio.addEventListener('play', () => $('#nowcard').classList.add('playing'));
audio.addEventListener('pause', () => $('#nowcard').classList.remove('playing'));
audio.addEventListener('ended', () => { $('#nowcard').classList.remove('playing'); if (auto) step(1); });
$('#prev').onclick = () => step(-1);
$('#next').onclick = () => step(1);
$('#auto').onclick = () => { auto = !auto; store.set('yq-q-auto', auto); paintAuto(); };
$('#rq').oninput = renderR; $('#sq').oninput = renderS;

function showTab(t){
  document.querySelectorAll('.tabs .btn').forEach(b => b.classList.toggle('on', b.dataset.t === t));
  $('#colR').classList.toggle('hide', t !== 'r'); $('#colS').classList.toggle('hide', t !== 's');
}
document.querySelectorAll('.tabs .btn').forEach(b => b.onclick = () => showTab(b.dataset.t));
if (matchMedia('(max-width:760px)').matches) showTab('r');

renderR(); renderS(); header();
if (si && has(R[ri], si)) { audio.src = R[ri].s + String(si).padStart(3, '0') + '.mp3'; }
const on = $('#rlist .rc.on'); if (on) on.scrollIntoView({block:'center'});
</script></body></html>"""


MUSHAF_HTML = r"""<!doctype html><html dir="rtl"><head>__HEAD__
<style>
:root{--paper:rgba(14,16,22,.55)}
[data-theme="light"]{--paper:#fffdf6}
h3{margin:0 0 10px;font-size:1.05rem;color:var(--gold-l)}
.msg{color:var(--muted);font-size:.9rem;line-height:1.9}
.spin{display:inline-block;animation:sp 1s linear infinite}@keyframes sp{to{transform:rotate(360deg)}}
/* ===== الخطة ===== */
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
.lbl{font-weight:700;font-size:.9rem;margin:12px 0 6px}
.chip{border:1px solid var(--border);background:var(--surface-2);color:var(--text);border-radius:999px;padding:6px 14px;font-size:.85rem;font-weight:600;transition:all .2s}
.chip:hover{border-color:var(--border-s)}
.chip.on{background:var(--gold);color:var(--on-gold);border-color:var(--gold)}
select,input[type=number]{font-family:inherit;background:var(--surface-2);color:var(--text);border:1px solid var(--border);border-radius:999px;padding:6px 12px;font-size:.88rem;outline:none}
input[type=number]{width:90px;text-align:center}
.preview{margin-top:14px;padding:12px 14px;border-radius:16px;background:linear-gradient(135deg,var(--gold-soft),var(--accent-soft));border:1px solid var(--border-s);font-weight:600;line-height:2}
.preview b{color:var(--gold-l);font-size:1.1rem}
.big{font-size:1rem;padding:9px 22px}
.pl{display:grid;grid-template-columns:150px 1fr;gap:18px;align-items:center}
.ring{width:140px;height:140px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  background:conic-gradient(var(--accent) calc(var(--p)*1%), var(--surface-2) 0);transition:all .6s;position:relative}
.ring::before{content:"";position:absolute;inset:12px;border-radius:50%;background:var(--surface)}
.ring span{position:relative;font-weight:700;font-size:1.4rem;color:var(--gold-l)}
.ring small{display:block;font-size:.7rem;color:var(--muted);text-align:center}
.today{font-size:1.05rem;font-weight:700;line-height:2}
.today b{color:var(--gold-l)}
.stat{display:flex;gap:8px;flex-wrap:wrap;margin:8px 0}
.st{background:var(--surface-2);border:1px solid var(--border);border-radius:12px;padding:5px 10px;font-size:.8rem}
.st.ok{border-color:var(--accent);color:var(--accent)}.st.bad{border-color:#c46a4a;color:#c46a4a}
.hint{font-size:.82rem;color:var(--muted);margin-top:6px}
.celebrate{text-align:center;font-size:1.2rem;font-weight:700;color:var(--gold-l);line-height:2;animation:rise .6s ease both}
/* ===== القارئ ===== */
.reader{margin-top:14px}
.rtop{display:flex;gap:8px;flex-wrap:wrap;align-items:center;justify-content:space-between;margin-bottom:12px}
.pg{display:flex;gap:6px;align-items:center;font-size:.88rem}
.banner{margin-bottom:10px;padding:8px 12px;border-radius:12px;background:var(--accent-soft);border:1px dashed var(--accent);font-size:.85rem;display:none}
.page{background:var(--paper);border:1px solid var(--border-s);border-radius:20px;padding:22px 26px;min-height:440px;
  box-shadow:inset 0 0 50px var(--gold-soft);position:relative;transition:opacity .25s}
.page::before,.page::after{content:"۞";position:absolute;top:8px;color:var(--gold);opacity:.5;font-size:1rem}
.page::before{right:12px}.page::after{left:12px}
.ptext{font-family:'Amiri Quran','Amiri',serif;font-size:var(--fs,1.75rem);line-height:2.35;text-align:justify;text-align-last:center;margin:0;color:var(--text)}
.an{display:inline-flex;align-items:center;justify-content:center;min-width:1.55em;height:1.55em;padding:0 .2em;border-radius:50%;
  border:1.5px solid var(--gold);color:var(--gold-l);font-size:.5em;font-family:'Noto Kufi Arabic',sans-serif;font-weight:700;vertical-align:middle;margin:0 .2em;line-height:1}
.shead{margin:16px 0 6px;text-align:center;border:1px solid var(--border-s);border-radius:14px;padding:6px;
  background:linear-gradient(90deg,transparent,var(--gold-soft),transparent);font-family:'Amiri',serif;font-weight:700;color:var(--gold-l);font-size:1.3rem}
.basm{text-align:center;font-family:'Amiri Quran','Amiri',serif;font-size:calc(var(--fs,1.75rem)*.9);color:var(--gold-l);margin:4px 0 8px}
.pfoot{text-align:center;color:var(--muted);font-size:.85rem;margin-top:10px}
.mark{display:flex;justify-content:center;margin-top:12px}
@media (max-width:720px){.pl{grid-template-columns:1fr;justify-items:center;text-align:center}.page{padding:16px 14px}.stat{justify-content:center}}
</style></head><body>
<div class="card" id="plan"></div>
<div class="card reader" id="reader">
  <div class="rtop">
    <select id="sura"></select>
    <div class="pg">
      <button class="btn" id="pprev" title="الصفحة السابقة">→</button>
      <span>صفحة</span><input type="number" id="pin" min="1" max="604"><span>من ٦٠٤</span>
      <button class="btn" id="pnext" title="الصفحة التالية">←</button>
    </div>
    <div class="row"><button class="btn" id="fminus">أ−</button><button class="btn" id="fplus">أ+</button></div>
  </div>
  <div class="banner" id="banner"></div>
  <div class="page" id="page"></div>
  <div class="pfoot" id="pfoot"></div>
</div>
<script>
const S = __SURAS__;
const $ = s => document.querySelector(s);
const store = {get(k){try{return JSON.parse(localStorage.getItem(k))}catch(e){return null}}, set(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
const toAr = s => String(s).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const pad = n => String(n).padStart(2,'0');
const dkey = d => `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;
const esc = t => t.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));
function withTimeout(p, ms){ return Promise.race([p, new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout')), ms))]); }

// ===================== خطة الختمة / الحفظ =====================
const SCOPES = {
  all:  {n:'القرآن كاملًا', a:1, b:604},
  j30:  {n:'جزء عمّ', a:582, b:604},
  j29:  {n:'جزء تبارك', a:562, b:581},
  j2930:{n:'جزء تبارك وجزء عمّ', a:562, b:604},
  j2630:{n:'آخر خمسة أجزاء', a:502, b:604},
  baq:  {n:'سورة البقرة', a:2, b:49},
};
const DURS = [[7,'أسبوع'],[15,'أسبوعين'],[30,'شهر'],[60,'شهرين'],[90,'٣ أشهر'],[180,'٦ أشهر'],[365,'سنة']];
let draft = {type:'khatma', scope:'all', days:30};

function daysBetween(a, b){ const A = new Date(a + 'T00:00:00'), B = new Date(b + 'T00:00:00'); return Math.round((B - A) / 86400000); }

function renderSetup(){
  const sc = SCOPES[draft.scope], total = sc.b - sc.a + 1, per = total / draft.days;
  const isH = draft.type === 'hifz';
  $('#plan').innerHTML = `
    <h3>🎯 ابدأ خطتك مع القرآن</h3>
    <div class="lbl">نوع الخطة</div>
    <div class="row">
      <button class="chip ${!isH ? 'on' : ''}" data-t="khatma">📖 ختمة قراءة</button>
      <button class="chip ${isH ? 'on' : ''}" data-t="hifz">🧠 حفظ</button>
    </div>
    <div class="lbl">النطاق</div>
    <select id="scope">${Object.entries(SCOPES).map(([k, v]) => `<option value="${k}" ${k === draft.scope ? 'selected' : ''}>${v.n} (${toAr(v.b - v.a + 1)} صفحة)</option>`).join('')}</select>
    <div class="lbl">المدة</div>
    <div class="row">${DURS.map(([d, n]) => `<button class="chip ${d === draft.days ? 'on' : ''}" data-d="${d}">${n}</button>`).join('')}
      <span class="muted" style="font-size:.85rem">أو</span><input type="number" id="cdays" min="1" max="2000" value="${draft.days}"><span class="muted" style="font-size:.85rem">يوم</span></div>
    <div class="preview">${isH ? 'حفظك اليومي' : 'وردك اليومي'}: <b>${per >= 1 ? toAr(Math.ceil(per * 10) / 10) + ' صفحة' : 'صفحة كل ' + toAr(Math.ceil(1 / per)) + ' أيام تقريبًا'}</b>
      ${!isH ? `<br><span class="muted" style="font-size:.85rem">≈ ${toAr(Math.max(1, Math.round(per * 2)))} دقيقة قراءة يوميًا</span>` : ''}
      <br><span class="muted" style="font-size:.85rem">تنتهي بإذن الله: ${new Date(Date.now() + (draft.days - 1) * 86400000).toLocaleDateString('ar', {day:'numeric', month:'long', year:'numeric'})}</span></div>
    <div class="row" style="margin-top:14px"><button class="btn big on" id="go">ابدأ على بركة الله ✨</button></div>`;
  $('#plan').querySelectorAll('[data-t]').forEach(b => b.onclick = () => { draft.type = b.dataset.t; if (draft.type === 'hifz' && draft.days < 60 && draft.scope === 'all') draft.days = 365; renderSetup(); });
  $('#plan').querySelectorAll('[data-d]').forEach(b => b.onclick = () => { draft.days = +b.dataset.d; renderSetup(); });
  $('#scope').onchange = e => { draft.scope = e.target.value; renderSetup(); };
  $('#cdays').onchange = e => { const v = Math.max(1, Math.min(2000, parseInt(e.target.value) || 30)); draft.days = v; renderSetup(); };
  $('#go').onclick = () => {
    const sc = SCOPES[draft.scope];
    store.set('yq-plan', {type: draft.type, scope: draft.scope, a: sc.a, b: sc.b, days: draft.days, start: dkey(new Date()), done: 0, log: {}});
    renderPlan(); goPage(sc.a);
  };
}

function planMath(P){
  const total = P.b - P.a + 1, per = total / P.days;
  const dayIdx = Math.min(P.days, Math.max(1, daysBetween(P.start, dkey(new Date())) + 1));
  const expected = Math.min(total, Math.ceil(per * dayIdx - 1e-9));
  const expectedPrev = Math.min(total, Math.ceil(per * (dayIdx - 1) - 1e-9));
  const need = Math.max(0, expected - P.done);
  const from = P.a + P.done, to = Math.min(P.b, from + Math.max(need, 1) - 1);
  return {total, per, dayIdx, expected, expectedPrev, need, from, to};
}

let cancelArm = false;
function renderPlan(){
  const P = store.get('yq-plan');
  if (!P) { renderSetup(); $('#banner').style.display = 'none'; return; }
  const M = planMath(P), isH = P.type === 'hifz', pct = Math.round(P.done / M.total * 100);
  const word = isH ? 'حفظ' : 'ورد';
  if (P.done >= M.total) {
    $('#plan').innerHTML = `<div class="celebrate">🎉 مبارك! أتممت ${isH ? 'حفظ' : 'ختمة'} ${SCOPES[P.scope].n}<br>
      <span class="muted" style="font-size:.9rem">«خيركم من تعلّم القرآن وعلّمه» — تقبّل الله منك</span></div>
      <div class="row" style="justify-content:center;margin-top:12px"><button class="btn big on" id="again">ابدأ خطة جديدة</button></div>`;
    $('#again').onclick = () => { store.set('yq-plan', null); renderPlan(); };
    $('#banner').style.display = 'none';
    return;
  }
  let status;
  if (P.done < M.expectedPrev) status = `<span class="st bad">متأخر ${toAr(M.expectedPrev - P.done)} صفحة — عوّضها اليوم 💪</span>`;
  else if (P.done > M.expected) status = `<span class="st ok">متقدّم ${toAr(P.done - M.expected)} صفحة 🌟</span>`;
  else status = `<span class="st ok">على الخطة ✓</span>`;
  const todayDone = M.need === 0;
  $('#plan').innerHTML = `
    <div class="pl">
      <div class="ring" style="--p:${pct}"><div><span>${toAr(pct)}٪</span><small>${toAr(P.done)} / ${toAr(M.total)}</small></div></div>
      <div>
        <h3>${isH ? '🧠 خطة الحفظ' : '📖 خطة الختمة'}: ${SCOPES[P.scope].n}</h3>
        <div class="today">${todayDone
          ? `أنهيت ${word} اليوم ✅ <span class="muted" style="font-size:.85rem">تقدر تكمل وتتقدّم</span>`
          : `${word} اليوم: <b>${M.from === M.to ? 'صفحة ' + toAr(M.from) : 'من صفحة ' + toAr(M.from) + ' إلى ' + toAr(M.to)}</b>`}</div>
        <div class="stat"><span class="st">اليوم ${toAr(M.dayIdx)} من ${toAr(P.days)}</span><span class="st">المتبقي ${toAr(M.total - P.done)} صفحة</span>${status}</div>
        <div class="row">
          <button class="btn big on" id="read">${todayDone ? 'اقرأ زيادة' : isH ? 'ابدأ حفظ اليوم' : 'اقرأ وردك'} 📖</button>
          <button class="btn" id="mark">✅ ${todayDone ? 'أنهيت صفحات زيادة' : 'أنهيت ' + word + ' اليوم'}</button>
          <button class="btn" id="cancel">${cancelArm ? 'متأكد؟ اضغط مرة ثانية للحذف' : 'إلغاء الخطة'}</button>
        </div>
        ${isH ? '<div class="hint">💡 كرّر الصفحة حتى تحفظها، وراجع حفظ أمس قبل الجديد، وسمّع لأحد إذا تقدر.</div>' : ''}
      </div>
    </div>`;
  $('#read').onclick = () => { goPage(M.from); $('#reader').scrollIntoView({behavior:'smooth'}); };
  $('#mark').onclick = () => {
    const P2 = store.get('yq-plan'), M2 = planMath(P2);
    const add = M2.need > 0 ? M2.need : Math.max(1, Math.ceil(M2.per));
    P2.done = Math.min(M2.total, P2.done + add);
    const k = dkey(new Date()); P2.log[k] = (P2.log[k] || 0) + add;
    store.set('yq-plan', P2); renderPlan();
  };
  $('#cancel').onclick = () => {
    if (!cancelArm) { cancelArm = true; renderPlan(); setTimeout(() => { cancelArm = false; if (store.get('yq-plan')) renderPlan(); }, 4000); return; }
    cancelArm = false; store.set('yq-plan', null); renderPlan();
  };
  const bn = $('#banner');
  bn.style.display = todayDone ? 'none' : 'block';
  bn.textContent = `🎯 ${word} اليوم: ${M.from === M.to ? 'صفحة ' + toAr(M.from) : 'من صفحة ' + toAr(M.from) + ' إلى ' + toAr(M.to)}`;
}

// ===================== المصحف =====================
const cache = {};
let cur = store.get('yq-mp') || 1, fs = store.get('yq-fs') || 1.75;
document.documentElement.style.setProperty('--fs', fs + 'rem');
$('#sura').innerHTML = S.map((n, i) => `<option value="${i + 1}">${toAr(i + 1)}. سورة ${n}</option>`).join('');

async function fetchPage(p){
  if (cache[p]) return cache[p];
  const j = await withTimeout(fetch(`https://api.alquran.cloud/v1/page/${p}/quran-uthmani`).then(r => r.json()), 15000);
  if (!j || !j.data) throw new Error('bad');
  cache[p] = j.data; return j.data;
}

async function goPage(p){
  p = Math.min(604, Math.max(1, parseInt(p) || 1)); cur = p; store.set('yq-mp', p); $('#pin').value = p;
  const box = $('#page');
  if (!cache[p]) box.innerHTML = '<div class="msg" style="text-align:center;padding-top:40px">جاري تحميل الصفحة <span class="spin">⏳</span></div>';
  try {
    const d = await fetchPage(p);
    if (cur !== p) return;
    let html = '', para = '';
    const flush = () => { if (para) { html += `<p class="ptext">${para}</p>`; para = ''; } };
    for (const a of d.ayahs) {
      let t = a.text.replace(/﻿/g, '');
      const s = a.surah.number;
      if (a.numberInSurah === 1) {
        flush();
        html += `<div class="shead">سورة ${S[s - 1]}</div>`;
        if (s !== 1 && s !== 9) {
          const w = t.split(' ');
          if (w.length > 4 && w[0].startsWith('بِس')) { html += `<div class="basm">${esc(w.slice(0, 4).join(' '))}</div>`; t = w.slice(4).join(' '); }
        }
      }
      para += `${esc(t)} <span class="an">${toAr(a.numberInSurah)}</span> `;
    }
    flush();
    box.innerHTML = html;
    const f = d.ayahs[0];
    $('#pfoot').textContent = `الجزء ${toAr(f.juz)} · صفحة ${toAr(p)}`;
    $('#sura').value = f.surah.number;
    if (p < 604) fetchPage(p + 1).catch(() => {});
  } catch(e) {
    box.innerHTML = '<div class="msg" style="text-align:center;padding-top:40px">تعذّر تحميل الصفحة، تأكد من الإنترنت. <button class="btn" id="retry">🔄 أعد المحاولة</button></div>';
    $('#retry').onclick = () => goPage(p);
  }
}

$('#pprev').onclick = () => goPage(cur - 1);
$('#pnext').onclick = () => goPage(cur + 1);
$('#pin').onchange = e => goPage(e.target.value);
$('#fplus').onclick = () => { fs = Math.min(3, fs + .15); store.set('yq-fs', fs); document.documentElement.style.setProperty('--fs', fs + 'rem'); };
$('#fminus').onclick = () => { fs = Math.max(1.1, fs - .15); store.set('yq-fs', fs); document.documentElement.style.setProperty('--fs', fs + 'rem'); };
$('#sura').onchange = async e => {
  const n = +e.target.value;
  try { const j = await withTimeout(fetch(`https://api.alquran.cloud/v1/ayah/${n}:1`).then(r => r.json()), 12000); goPage(j.data.page); }
  catch(err) { $('#page').innerHTML = '<div class="msg" style="text-align:center;padding-top:40px">تعذّر فتح السورة، حاول مرة ثانية.</div>'; }
};
document.addEventListener('keydown', e => {
  if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;
  if (e.key === 'ArrowLeft') goPage(cur + 1);
  if (e.key === 'ArrowRight') goPage(cur - 1);
});
let tx = null;
$('#page').addEventListener('touchstart', e => { tx = e.touches[0].clientX; }, {passive:true});
$('#page').addEventListener('touchend', e => {
  if (tx === null) return; const dx = e.changedTouches[0].clientX - tx; tx = null;
  if (Math.abs(dx) > 60) goPage(dx > 0 ? cur + 1 : cur - 1);   // السحب لليمين = الصفحة التالية مثل المصحف
}, {passive:true});

renderPlan();
goPage(cur);
</script></body></html>"""


def mushaf_reader():
    html = MUSHAF_HTML.replace("__HEAD__", FRAME_HEAD).replace("__SURAS__", js_data(SURAS))
    components.html(html, height=1300, scrolling=False)


def quran_player():
    html = (
        QURAN_HTML.replace("__HEAD__", FRAME_HEAD)
        .replace("__RECITERS__", js_data(load_reciters()))
        .replace("__SURAS__", js_data(SURAS))
    )
    components.html(html, height=860, scrolling=False)


# =====================================================
# 8) الذكاء الاصطناعي (Gemini)
# =====================================================
# إذا كان نموذج مزدحمًا ننتقل تلقائيًا للي بعده
MODELS = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash",
          "gemini-flash-latest", "gemini-2.5-flash-lite"]

SYSTEM_PROMPTS = {
    "qa": """أنت "المساعد الشرعي" في منصة اليقين، تجيب عن الأسئلة الشرعية وترد على الشبهات وفق منهج أهل السنة والجماعة.
- اكتب بالعربية الفصحى الواضحة، بأسلوب علمي هادئ ومنظّم (عناوين قصيرة ونقاط عند الحاجة).
- استدل بالقرآن مع ذكر اسم السورة ورقم الآية، وبالأحاديث الصحيحة مع ذكر من أخرجها، وانقل أقوال أهل العلم المعتبرين.
- لا تخترع آية أو حديثًا أو قولًا أو مرجعًا أبدًا؛ إن لم تكن متأكدًا من النص أو تخريجه فقل ذلك صراحة.
- في الرد على الشبهة: اعرضها بإنصاف، ثم فنّدها بالدليل النقلي والعقلي، ثم لخّص الجواب.
- في المسائل الخلافية اذكر الأقوال المعتبرة وأدلتها باختصار ولا تتعصب لقول.
- في المسائل الشخصية الدقيقة (طلاق، مواريث معقدة، وقائع خاصة) أعطِ الحكم العام وانصح بمراجعة عالم أو جهة إفتاء رسمية.
- إن كان السؤال خارج نطاق الدين فوجّه السائل بلطف إلى موضوع المنصة.""",
    "dialogue": """أنت محاور هادئ في "قاعة الحوار" بمنصة اليقين، تتحدث مع غير المسلمين ومن لديهم تساؤلات عن الإسلام.
- خاطب السائل باحترام ولطف، ولا تسخر من أي دين أو معتقد ولا تهاجم أصحابه.
- ابدأ بالحجة العقلية والمنطقية والأدلة التاريخية، ثم ادعمها بالنصوص من القرآن والسنة مع ذكر مراجعها.
- اشرح المصطلحات الإسلامية ببساطة لمن لا يعرفها.
- لا تخترع نصوصًا أو إحصاءات أو مراجع؛ وإن لم تكن متأكدًا فقل ذلك.
- اعترف بالأسئلة الصعبة بإنصاف وأجب عنها بصدق، فالهدف الإقناع بالحق لا الغلبة في الجدال.
- اكتب بلغة السائل نفسها (عربية أو إنجليزية أو غيرها).""",
}


@st.cache_resource
def get_client():
    from google import genai
    from google.genai import types

    try:
        key = str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        return None
    # المفتاح الصحيح حروف إنجليزية وأرقام فقط (يبدأ عادة بـ AIza)
    if not key or not key.isascii() or " " in key:
        return None
    # مهلة 40 ثانية لكل طلب بدل الانتظار بلا نهاية
    return genai.Client(api_key=key, http_options=types.HttpOptions(timeout=40_000))


def _make_configs(types, system_prompt):
    """إعداد بتفكير قليل (أسرع)، وإعداد عادي احتياطي لو النموذج ما يدعمه"""
    base = dict(system_instruction=system_prompt, max_output_tokens=2500)
    configs = []
    try:
        configs.append(types.GenerateContentConfig(**base, thinking_config=types.ThinkingConfig(thinking_level="low")))
    except Exception:
        pass
    configs.append(types.GenerateContentConfig(**base))
    return configs


def stream_answer(mode: str, messages: list):
    """يرجّع الإجابة قطعة قطعة أول ما تبدأ توصل، عشان المستخدم ما ينتظر"""
    try:
        client = get_client()
        from google.genai import types
    except ImportError:
        yield "⚠️ مكتبة Gemini غير مثبتة. شغّل في الترمنال: `python -m pip install google-genai`"
        return
    if client is None:
        yield ("⚠️ مفتاح API غير موجود أو مكتوب غلط. افتح الملف `.streamlit/secrets.toml` وحط مفتاحك الحقيقي "
               "(يبدأ بـ AIza) مكان `ضع_مفتاحك_هنا`، ثم أعد تشغيل التطبيق.")
        return

    recent = messages[-12:]
    while recent and recent[0]["role"] != "user":
        recent = recent[1:]
    contents = [
        types.Content(role="user" if m["role"] == "user" else "model", parts=[types.Part(text=m["content"])])
        for m in recent
    ]
    configs = _make_configs(types, SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["qa"]))

    last_error = None
    # إعادة تلقائية: يجرب كل النماذج، وإذا كلها مزدحمة (503) ينتظر ويعيد المحاولة
    for attempt in range(3):
        if attempt:
            # نعيد المحاولة فقط إذا كانت المشكلة ضغط مؤقت (503)، مو خطأ في المفتاح أو الحد
            if not last_error or not ("503" in last_error or "UNAVAILABLE" in last_error or "overloaded" in last_error.lower()):
                break
            time.sleep(3 * attempt)  # ينتظر 3 ثواني ثم 6
        for model in MODELS:
            for config in configs:
                got_text = False
                try:
                    for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
                        if chunk.text:
                            got_text = True
                            yield chunk.text
                    if got_text:
                        return
                    break  # رد فاضي: جرّب النموذج التالي
                except Exception as e:
                    if got_text:  # انقطع في النص: نكتفي بما وصل
                        yield "\n\n⚠️ انقطع الاتصال قبل اكتمال الإجابة، أعد السؤال لإكمالها."
                        return
                    last_error = str(e)
                    if "401" in last_error or "UNAUTHENTICATED" in last_error or "API key" in last_error:
                        yield "⚠️ مفتاح API غير صالح. أنشئ مفتاحًا جديدًا من Google AI Studio وضعه في `.streamlit/secrets.toml`."
                        return
                    if "INVALID_ARGUMENT" in last_error or "400" in last_error:
                        continue  # غالبًا إعداد التفكير غير مدعوم: جرّب الإعداد العادي
                    break  # مزدحم أو غير موجود أو انتهت المهلة: النموذج التالي

    print("Gemini error:", last_error)  # يظهر في الترمنال
    err = last_error or ""
    if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
        msg = ("⚠️ انتهى الحد المجاني لمفتاح Gemini مؤقتًا (كثرة طلبات). "
               "انتظر دقيقة، وإذا استمر انتظر لين بكرة أو أنشئ مفتاحًا جديدًا من Google AI Studio.")
    elif "403" in err or "PERMISSION_DENIED" in err:
        msg = "⚠️ المفتاح ما عنده صلاحية. أنشئ مفتاحًا جديدًا من Google AI Studio وضعه في `.streamlit/secrets.toml`."
    elif "404" in err or "NOT_FOUND" in err:
        msg = "⚠️ أسماء النماذج في القائمة `MODELS` غير موجودة. غيّرها لأسماء صحيحة مثل `gemini-2.5-flash`."
    elif "503" in err or "UNAVAILABLE" in err:
        msg = "⚠️ خوادم الذكاء الاصطناعي مزدحمة الآن، انتظر دقيقة وأعد إرسال سؤالك."
    else:
        msg = "⚠️ تعذّر الاتصال بالذكاء الاصطناعي. تأكد من الإنترنت ثم أعد المحاولة."
    yield msg + "\n\nتفاصيل الخطأ: `" + err[:300].replace("`", "'") + "`"


def strip_icon(s: str) -> str:
    return s.split("  ", 1)[-1]


# =====================================================
# 9) الحالة
# =====================================================
if "chats" not in st.session_state:
    st.session_state.chats = {"qa": [], "dialogue": []}
if "page" not in st.session_state:
    st.session_state.page = PAGES[0]


def go(page_label: str):
    st.session_state.page = page_label


def clear_chat(mode: str):
    st.session_state.chats[mode] = []


# =====================================================
# 10) شريط التنقل العلوي + الشريط الجانبي
# =====================================================
with st.container(key="topnav"):
    c_brand, c_nav = st.columns([1.1, 4], vertical_alignment="center")
    with c_brand:
        st.markdown('<div class="brand"><span class="lamp">🏮</span><span class="name">منصة اليقين</span></div>',
                    unsafe_allow_html=True)
    with c_nav:
        page_label = st.radio("التنقل", PAGES, horizontal=True, key="page", label_visibility="collapsed")

page = PAGE_KEYS[page_label]

with st.sidebar:
    st.markdown(
        """
<div class="side-brand">
  <div class="logo">📖</div>
  <div class="name">منصة اليقين</div>
  <div class="tag">الحوار الشرعي والرد على الشبهات</div>
</div>
<div class="note">
  💡 <b>ملاحظة توجيهية:</b> جميع الإجابات مبنية على أصول أهل السنة والجماعة،
  وتعتمد على الأدلة الشرعية والمنطق العقلي السليم.
</div>
<div class="tip">
  🏮 <b>تعرّف على نور:</b> اضغط زر السماعة 🔇 فوق رأسه ليقرأ لك الإجابات بصوته،
  وانقر عليه أثناء الكلام ليسكت. وزر ☀️/🌙 فوق يبدّل بين الوضع النهاري والليلي.
</div>
""",
        unsafe_allow_html=True,
    )

GREETINGS = {
    "home": "السلام عليكم! أنا نور 🌙 أهلًا بك في منصة اليقين.",
    "qa": "اطرح سؤالك أو الشبهة اللي تواجهك وسأساعدك 📚",
    "dialogue": "أهلًا بك في قاعة الحوار! اسأل عن أي شيء يخص الإسلام بكل حرية 🤝",
    "quran": "اختر قارئك المفضّل والسورة، واستمع بخشوع 🎧",
    "prayer": "هنا مواقيت الصلاة في مدينتك، واتجاه القبلة، وأقرب المساجد لك 🕌",
}

# =====================================================
# 11) الصفحة الرئيسية
# =====================================================
if page == "home":
    st.markdown(
        """
<div class="hero-wrap">
  <div class="hero-side"></div>
  <div class="arch">
    <div class="bismillah">بسم الله الرحمن الرحيم</div>
    <div class="verse">سَلَامٌ قَوْلًا مِّن رَّبٍّ رَّحِيمٍ</div>
    <div class="ref">سورة يس — آية ٥٨</div>
    <div class="sub">واحة علمٍ ونورٍ وطمأنينة</div>
  </div>
  <div class="hero-side"></div>
</div>
""",
        unsafe_allow_html=True,
    )

    prayer_widget("compact", 300)

    st.markdown('<div class="section-title">✨ استكشف المنصة</div>', unsafe_allow_html=True)
    cards = [
        ("💬", "اسأل نور", "اطرح سؤالك الشرعي أو الشبهة، وخذ إجابة موثّقة بالدليل.", PAGES[1]),
        ("🤝", "قاعة الحوار", "حوار هادئ ومحترم لغير المسلمين ومن لديهم تساؤلات.", PAGES[2]),
        ("📖", "القرآن الكريم", "المصحف كامل، وخطة ختمة أو حفظ، والاستماع لكبار القرّاء.", PAGES[3]),
        ("🕰️", "مواقيت الصلاة", "مواقيت مدينتك، وسجل صلواتك، وتذكير بعد كل صلاة.", PAGES[4]),
        ("🕌", "أقرب مسجد", "المساجد القريبة منك مع المسافة والاتجاهات.", PAGES[4]),
        ("🧭", "اتجاه القبلة", "اعرف اتجاه القبلة من موقعك الحالي.", PAGES[4]),
    ]
    for row in range(2):
        cols = st.columns(3)
        for j in range(3):
            i = row * 3 + j
            icon, title, desc, target = cards[i]
            with cols[j]:
                with st.container(key=f"card_{i}"):
                    st.markdown(f'<div class="hc"><div class="ic">{icon}</div><h3>{title}</h3><p>{desc}</p></div>',
                                unsafe_allow_html=True)
                    st.button("ادخل ←", key=f"go_{i}", on_click=go, args=(target,))

    mascot("home-idle", "idle", "home", GREETINGS["home"])

# =====================================================
# 12) القرآن الكريم
# =====================================================
elif page == "quran":
    st.markdown(
        """
<div class="hero">
  <span class="badge">القرآن الكريم</span>
  <h1>استمع لكتاب الله</h1>
  <div class="ornament">۞</div>
  <p>اقرأ المصحف وابدأ خطة ختمة أو حفظ، أو استمع لجميع السور بأصوات كبار القرّاء.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    with st.container(key="qtabs"):
        qtab = st.radio("قسم القرآن", ["📖 المصحف والختمة", "🎧 الاستماع للقرّاء"], horizontal=True,
                        key="qtab", label_visibility="collapsed")
    if qtab.startswith("📖"):
        mushaf_reader()
    else:
        quran_player()
    mascot("quran-idle", "idle", "quran", GREETINGS["quran"])

# =====================================================
# 13) الصلاة والمساجد
# =====================================================
elif page == "prayer":
    st.markdown(
        """
<div class="hero">
  <span class="badge">الصلاة والمساجد</span>
  <h1>مواقيت الصلاة</h1>
  <div class="ornament">۞</div>
  <p>نحدد مدينتك تلقائيًا، ونعرض لك المواقيت واتجاه القبلة وأقرب المساجد.</p>
</div>
""",
        unsafe_allow_html=True,
    )
    prayer_widget("full", 820)
    mascot("prayer-idle", "idle", "prayer", GREETINGS["prayer"])

# =====================================================
# 14) صفحات المحادثة (اسأل نور / قاعة الحوار)
# =====================================================
else:
    mode = page
    messages = st.session_state.chats[mode]

    if mode == "dialogue":
        badge, title = "قاعة الحوار", "حوار هادئ حول الإسلام"
        subtitle = "اسأل بحرية عن الإسلام، وستجد إجابة بالحجة والدليل وبأسلوب محترم."
        placeholder = "اكتب سؤالك عن الإسلام هنا..."
        suggestions = [
            "🌌  ما الدليل العقلي على وجود الخالق؟",
            "📜  كيف نعرف أن القرآن من عند الله؟",
            "🕌  لماذا يؤمن المسلمون بنبوة محمد ﷺ؟",
            "🕊️  ما نظرة الإسلام لعيسى عليه السلام؟",
        ]
    else:
        badge, title = "الأسئلة وتصحيح الشبهات", "المساعد الشرعي وتفنيد الشبهات"
        subtitle = "اطرح سؤالك الشرعي أو الشبهة التي تواجهك لتجد إجابة علمية موثّقة وموضوعية."
        placeholder = "اكتب سؤالك أو الشبهة هنا..."
        suggestions = [
            "⚔️  شبهة: الإسلام انتشر بالسيف",
            "🧳  ما حكم الجمع بين الصلاتين للمسافر؟",
            "🔬  الرد على شبهة تعارض العلم والدين",
            "📖  كيف أثبت حجية السنة النبوية؟",
        ]

    if not messages:
        st.markdown(
            f"""
<div class="hero">
  <span class="badge">{badge}</span>
  <h1>{title}</h1>
  <div class="ornament">۞</div>
  <p>{subtitle}</p>
</div>
<div class="suggest-title">أو ابدأ بأحد هذه الأسئلة</div>
""",
            unsafe_allow_html=True,
        )
        with st.container(key="suggest"):
            cols = st.columns(2)
            for i, s in enumerate(suggestions):
                if cols[i % 2].button(s, key=f"s_{mode}_{i}"):
                    messages.append({"role": "user", "content": strip_icon(s)})
                    st.rerun()
    else:
        with st.container(key="clearchat"):
            st.button("🗑️ محادثة جديدة", key=f"clear_{mode}", on_click=clear_chat, args=(mode,))

    for m in messages:
        with st.chat_message(m["role"], avatar="🧑" if m["role"] == "user" else "🏮"):
            st.markdown(m["content"])

    if prompt := st.chat_input(placeholder):
        messages.append({"role": "user", "content": prompt})
        st.rerun()

    # توليد الإجابة إذا كانت آخر رسالة من المستخدم
    if messages and messages[-1]["role"] == "user":
        mascot(f"{mode}-{len(messages)}-thinking", "thinking", mode, GREETINGS[mode])
        with st.chat_message("assistant", avatar="🏮"):
            answer = st.write_stream(stream_answer(mode, messages))
        messages.append({"role": "assistant", "content": answer})
        mascot(f"{mode}-{len(messages)}-answer", "answer", mode, GREETINGS[mode], text=answer)
    else:
        mascot(f"{mode}-{len(messages)}-idle", "idle", mode, GREETINGS[mode])
