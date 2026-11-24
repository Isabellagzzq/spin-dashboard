import os
import numpy as np, pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="Spin | Who to nudge next", page_icon="🟣", layout="wide")
HERE = os.path.dirname(os.path.abspath(__file__)); D = os.path.join(HERE, "data")

# ---------- palette (Spin purple + one highlight color; meaning stays the same on every chart) ----------
PUR, DEEP, LAV, MUTE = "#5B2EFF", "#2A0F6B", "#B9A8F5", "#C9C3DD"
ORA = "#FF8A1F"          # highlight = people who flip / the thing to act on
TEAL, PINK = "#12B5A6", "#E0459B"
PCOL = {}                 # persona -> color, filled below
DECISION = ("This dashboard helps the Marketing team at Spin decide which users to nudge first with a "
            "non-OXXO purchase incentive, given that Marketing can only reach a limited share of the base each month.")

st.markdown(f"""<style>
.stApp {{background: radial-gradient(1200px 700px at 10% -10%, #6A3DF0 0%, #3B1491 38%, {DEEP} 100%); background-attachment: fixed;}}
header[data-testid="stHeader"] {{background: transparent;}}
.block-container {{padding-top: 1.4rem; max-width: 1350px;}}
.hero h1 {{font-size: 2.2rem; margin-bottom:.1rem; color:#fff !important}}
.hero p {{opacity:.9; font-size:1.02rem; max-width: 980px; color:#fff !important}}
[class*="st-key-card"] {{background:#fff; border-radius:18px; padding:1rem 1.2rem; box-shadow:0 8px 30px rgba(10,0,50,.35); margin-bottom:.4rem}}
[class*="st-key-card"] p, [class*="st-key-card"] li, [class*="st-key-card"] h4, [class*="st-key-card"] label, [class*="st-key-card"] td, [class*="st-key-card"] th, [class*="st-key-card"] span {{color:#1B1340}}
[class*="st-key-card"] [data-testid="stMetricLabel"] p {{color:#6B5FA5 !important; font-size:.85rem}}
[class*="st-key-card"] [data-testid="stMetricValue"] {{font-size:2rem; color:{PUR} !important; font-weight:800}}
[class*="st-key-card"] [data-testid="stMetricValue"] div {{color:{PUR} !important}}
[class*="st-key-card"] .note {{color:#6B5FA5 !important}}
[class*="st-key-card"] .tag {{color:#fff !important}}
[class*="st-key-card"] [data-baseweb="tab"] p {{color:#6B5FA5 !important}}
[class*="st-key-card"] [aria-selected="true"] {{background:#EFEAFF !important}}
[class*="st-key-card"] [aria-selected="true"] p {{color:{PUR} !important; font-weight:700}}
[role="tablist"] [role="tab"], [role="tablist"] [role="tab"] *, [data-baseweb="tab-list"] [data-baseweb="tab"], [data-baseweb="tab-list"] [data-baseweb="tab"] * {{color:#fff !important; font-weight:600}}
[role="tablist"] [role="tab"] {{background:rgba(255,255,255,.14); border-radius:12px 12px 0 0; padding:8px 18px}}
[role="tablist"] [aria-selected="true"], [role="tablist"] [aria-selected="true"] * {{color:{PUR} !important}}
[role="tablist"] [aria-selected="true"] {{background:#fff}}
[class*="st-key-card"] [role="tablist"] [role="tab"], [class*="st-key-card"] [role="tablist"] [role="tab"] * {{color:#6B5FA5 !important; background:transparent}}
[class*="st-key-card"] [role="tablist"] [aria-selected="true"], [class*="st-key-card"] [role="tablist"] [aria-selected="true"] * {{color:{PUR} !important}}
[class*="st-key-card"] [role="tablist"] [aria-selected="true"] {{background:#EFEAFF}}
[role="tablist"] {{gap:6px}}
.tag {{display:inline-block; padding:2px 10px; border-radius:20px; font-size:.78rem; font-weight:700; color:#fff}}
.note {{font-size:.9rem; color:#D6CCFF}}
.stApp > div label p, [data-testid="stWidgetLabel"] p {{color:#fff}}
[class*="st-key-card"] [data-testid="stWidgetLabel"] p {{color:#1B1340}}
[data-testid="stRadio"] label p {{color:#fff !important}}
[class*="st-key-card"] [data-testid="stRadio"] label p {{color:#1B1340 !important}}
.stTabs [data-baseweb="tab-highlight"] {{display:none}}
</style>""", unsafe_allow_html=True)
_n = [0]
def nk():
    _n[0] += 1
    return f"card{_n[0]}"
def card():
    _n[0] += 1
    return st.container(key=f"card{_n[0]}")

@st.cache_data
def load():
    r = lambda f: pd.read_csv(os.path.join(D, f))
    out = {k: r(f"{k}.csv") for k in ["monthly", "personas", "flip_profile", "descriptives", "pca", "models",
                                       "tree_rules", "drivers", "scores_out", "scores_in", "meta", "clustering"]}
    out["experiments"] = r("experiments.csv") if os.path.exists(os.path.join(D, "experiments.csv")) else None
    return out
L = load(); MON, PER, FP, DS, PCA, MOD, TREE, DRV, META, CLU = (L[k] for k in
    ["monthly", "personas", "flip_profile", "descriptives", "pca", "models", "tree_rules", "drivers", "meta", "clustering"])
meta = dict(zip(META["key"], META["value"]))
PERSONAS = list(PER.sort_values("users", ascending=False)["persona"])
for p, c in zip(PERSONAS, [PUR, TEAL, PINK]): PCOL[p] = c
MONTHS = sorted(MON["month"].unique())

NICE = {"oxxo_tx_ratio_m": "Share of purchases at OXXO", "ecommerce_tx_ratio_m": "Share of purchases online",
        "decline_ratio_m": "Share of declined payments", "tx_count_m": "Purchases per month",
        "merchant_entropy_m": "Variety of merchants", "oxxo_diff1": "Change in OXXO share vs last month",
        "tx_count_delta_m": "Change in purchases vs last month", "cash_funding_ratio_m": "Share of top-ups made in cash",
        "tx_log": "Purchase volume (log scale)", "oxxo_roll3": "OXXO share, 3-month average",
        "tx_roll3": "Purchases, 3-month average", "tenure_months": "Months since first purchase", "active_3m": "Active months in last 3",
        "oxxo_lag1": "OXXO share last month", "oxxo_ratio_delta_m": "Change in OXXO share vs last month", "active_3m_": ""}
PCT = {"oxxo_tx_ratio_m", "ecommerce_tx_ratio_m", "decline_ratio_m", "cash_funding_ratio_m", "oxxo_roll3", "oxxo_diff1", "oxxo_lag1"}
def nice(c): return NICE.get(c, c.replace("_", " ").replace(" m", "").capitalize())
def fmt(c, v): return f"{v*100:.1f}%" if c in PCT else f"{v:,.2f}"

def action_for(p):
    p = p.lower()
    if "oxxo" in p: return "Reward the first purchase outside OXXO"
    if "commerce" in p or "single" in p: return "Fix payment declines, then offer cashback online"
    return "Offer a loyalty program to keep them diverse"
def style(fig, h=340, title=None):
    fig.update_layout(template="plotly_white", height=h, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=10, r=10, t=10, b=10), font=dict(color="#1B1340", size=13), legend=dict(orientation="h", y=-0.2))
    fig.update_xaxes(showgrid=False, linecolor="#D9D3F0"); fig.update_yaxes(gridcolor="#EEEAFB", zeroline=False)
    return fig
def title(t, sub=None):
    st.markdown(f"#### {t}")
    if sub: st.markdown(f'<span class="note">{sub}</span>', unsafe_allow_html=True)

# ---------- hero + global filters (every chart below reacts to these) ----------
st.markdown(f'<div class="hero"><h1>Who should Marketing nudge next?</h1><p>{DECISION}</p></div>', unsafe_allow_html=True)
f1, f2, f3 = st.columns([1.1, 1.6, 1.3])
beh = f1.radio("Behavior to watch", ["Flip-Out", "Flip-In"], horizontal=True, key="beh",
               help="Flip-Out: a user who leaves OXXO as the main place to pay. Flip-In: a user who moves toward OXXO.")
m_lo, m_hi = f2.select_slider("Months", options=MONTHS, value=(MONTHS[0], MONTHS[-1]), key="months")
focus = f3.selectbox("Focus on a persona", ["All personas"] + PERSONAS, key="focus")
sel_m = [m for m in MONTHS if m_lo <= m <= m_hi]
inP = PERSONAS if focus == "All personas" else [focus]
col = "flip_out" if beh == "Flip-Out" else "flip_in"
mon = MON[MON["month"].isin(sel_m) & MON["persona"].isin(inP)]
def wmean(df, c, w="user_months"): return float((df[c] * df[w]).sum() / df[w].sum())

t1, t2, t3, t4, t5 = st.tabs(["1 · Who our users are", "2 · Who flips", "3 · Personas", "4 · Target list", "5 · The model"])

# ================= 1. OVERVIEW =================
with t1:
    users = int(MON.groupby("month")["users"].sum().max()) if False else int(PER["users"].sum())
    k1, k2, k3, k4 = st.columns(4)
    with k1.container(key=nk()): st.metric("Users in the sample", f"{int(mon['users'].sum() / max(len(sel_m),1)):,}", help="Average active users per month in the selection")
    with k2.container(key=nk()): st.metric("Purchases made at OXXO", f"{wmean(mon, 'oxxo')*100:.0f}%")
    with k3.container(key=nk()): st.metric(f"{beh} rate (per month)", f"{wmean(mon, col)*100:.1f}%")
    with k4.container(key=nk()): st.metric("Personas found", f"{len(PERSONAS)}")

    a, b = st.columns([1, 1.15])
    with a.container(key=nk()):
        sh = mon.groupby("persona")["users"].sum().reindex(PERSONAS).dropna().sort_values(ascending=False)
        lead = sh.idxmax(); title(f"{lead.replace(' Users','')} users are the largest group ({sh.max()/sh.sum()*100:.0f}% of users)",
                                  "Click a bar to focus the whole dashboard on that persona.")
        fig = go.Figure(go.Bar(y=sh.index, x=sh.values / sh.sum() * 100, orientation="h", marker_color=[PCOL[p] for p in sh.index],
                               text=[f"{v/sh.sum()*100:.0f}%" for v in sh.values], textposition="outside", customdata=sh.index,
                               hovertemplate="%{y}: %{x:.1f}% of users<extra></extra>"))
        fig.update_xaxes(visible=False, range=[0, 100]); fig.update_yaxes(autorange="reversed")
        ev = st.plotly_chart(style(fig, 230), width="stretch", on_select="rerun", selection_mode="points", key="share_chart")
        try:
            pts = ev.selection["points"] if ev and ev.get("selection") else []
            if pts:
                st.session_state["focus"] = pts[0]["y"]; st.rerun()
        except Exception: pass
    with b.container(key=nk()):
        g = mon.groupby("month").apply(lambda d: pd.Series({"oxxo": wmean(d, "oxxo"), "rate": wmean(d, col)}), include_groups=False).reset_index()
        title(f"OXXO usage {'fell' if g['oxxo'].iloc[-1] < g['oxxo'].iloc[0] else 'rose'} while {beh} stayed near {g['rate'].mean()*100:.0f}% a month",
              "Orange = the behavior we want to predict. Purple = how much of the spend is at OXXO.")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=g["month"], y=g["oxxo"] * 100, name="Purchases at OXXO (%)", line=dict(color=PUR, width=3)), secondary_y=False)
        fig.add_trace(go.Scatter(x=g["month"], y=g["rate"] * 100, name=f"{beh} rate (%)", line=dict(color=ORA, width=3), mode="lines+markers"), secondary_y=True)
        fig.update_yaxes(title_text="OXXO share (%)", secondary_y=False); fig.update_yaxes(title_text=f"{beh} (%)", secondary_y=True, showgrid=False)
        st.plotly_chart(style(fig, 230), width="stretch")

    with card():
        title("How we found the personas", "Three steps: compress the data (PCA), group similar users (K-Means), check the groups hold together.")
        s1, s2, s3 = st.tabs(["Descriptive statistics", "PCA", "Clustering quality"])
        with s1:
            d = DS.copy(); d["Variable"] = d["variable"].map(nice)
            fm = lambda r, c: fmt(r["variable"], r[c])
            for c in ["mean", "median", "std", "min", "max"]: d[c] = d.apply(lambda r, c=c: fm(r, c), axis=1)
            st.table(d[["Variable", "mean", "median", "std", "min", "max"]].rename(columns=str.capitalize))
            with st.expander("What each variable means (definitions)"):
                st.markdown("""
- **Share of purchases at OXXO / online**: part of a user's monthly purchases made in that channel.
- **Share of declined payments**: part of payment attempts that were refused (friction).
- **Purchases per month**: number of purchases in the month.
- **Variety of merchants**: how spread the purchases are across different merchants (higher = more variety).
- **Change vs last month**: this month minus last month.
- **Share of top-ups in cash**: part of the money added to the account that came as cash.
- **Flip-Out / Flip-In**: see tab 2.""")
        with s2:
            n80 = int((PCA["cumulative"] < 0.8).sum() + 1)
            title(f"{n80} components keep 80% of the information of all features")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Bar(x=PCA["component"], y=PCA["explained"] * 100, marker_color=LAV, name="Each component (%)"), secondary_y=False)
            fig.add_trace(go.Scatter(x=PCA["component"], y=PCA["cumulative"] * 100, line=dict(color=PUR, width=3), name="Accumulated (%)"), secondary_y=True)
            fig.update_yaxes(title_text="Information explained (%)", secondary_y=False); fig.update_yaxes(range=[0, 105], showgrid=False, secondary_y=True)
            st.plotly_chart(style(fig, 300), width="stretch")
        with s3:
            c = CLU.copy(); best = c.loc[c["Silhouette"].idxmax(), "Method"]
            title("Three groups is the simplest split that stays stable", f"Best separation score: {best}. Higher silhouette = clearer groups; lower Davies-Bouldin = clearer groups.")
            st.table(c.round(3))
            st.markdown('<span class="note">Groups are moderately stable: user boundaries can shift a little between runs, so use personas as a guide, not a label for life.</span>', unsafe_allow_html=True)

# ================= 2. FLIPPERS =================
with t2:
    with card():
        title("How we spot a flip", "We compare each user's OXXO share this month with the next month.")
        x1, x2 = st.columns(2)
        x1.markdown(f'<span class="tag" style="background:{ORA}">Flip-Out</span>  A user whose main way of paying was OXXO and who moves to other channels next month.', unsafe_allow_html=True)
        x2.markdown(f'<span class="tag" style="background:{PUR}">Flip-In</span>  A user who was not tied to OXXO and who starts paying mostly there next month.', unsafe_allow_html=True)
        st.markdown('<span class="note">The exact thresholds come from the notebook definition used to build the labels.</span>', unsafe_allow_html=True)

    fpd = FP[(FP["behavior"] == beh) & FP["month"].isin(sel_m) & FP["persona"].isin(inP)]
    feats = [c for c in NICE if c in FP.columns]
    with card():
        c1, c2 = st.columns([2, 1])
        pick = c2.selectbox("Compare on", feats, format_func=nice, index=0, key="feat")
        mm = c1.multiselect("Months to compare (side by side)", sel_m, default=sel_m[-3:], key="mm")
        mm = mm or sel_m[-3:]
        def agg(flag):
            d = fpd[(fpd["flipper"] == flag) & fpd["month"].isin(mm)]
            return d.groupby("month").apply(lambda x: float((x[pick] * x["n"]).sum() / x["n"].sum()), include_groups=False).reindex(mm)
        fl, nf = agg(1), agg(0)
        scale = 100 if pick in PCT else 1
        gap = (fl.mean() - nf.mean()) * scale
        word = "higher" if gap > 0 else "lower"
        title(f"{beh} users show {abs(gap):.1f}{'pp' if pick in PCT else ''} {word} '{nice(pick)}' than users who stay",
              "Same scale on both sides so the bars can be compared at a glance.")
        top = max(fl.max(), nf.max()) * scale * 1.18
        L_, R_ = st.columns(2)
        for colx, ser, nm, clr in [(L_, fl, f"Users who {beh.lower()}", ORA), (R_, nf, "Users who did not", MUTE)]:
            with colx:
                st.markdown(f"**{nm}**")
                fig = go.Figure(go.Bar(x=ser.index, y=ser.values * scale, marker_color=clr, text=[f"{v*scale:.1f}" for v in ser.values], textposition="outside"))
                fig.update_yaxes(range=[min(0, ser.min()*scale*1.2 if ser.min() < 0 else 0), top]); st.plotly_chart(style(fig, 280), width="stretch")
    with card():
        fa = fpd[fpd["month"].isin(mm)]
        rows = []
        for c in feats:
            a_ = fa[fa["flipper"] == 1]; b_ = fa[fa["flipper"] == 0]
            if len(a_) and len(b_):
                va = (a_[c] * a_["n"]).sum() / a_["n"].sum(); vb = (b_[c] * b_["n"]).sum() / b_["n"].sum()
                rows.append((nice(c), va, vb, c))
        if rows:
            r = pd.DataFrame(rows, columns=["name", "fl", "nf", "c"]); sd = r.apply(lambda x: abs(x.fl - x.nf), axis=1)
            sc = DS.set_index("variable")["std"] if "std" in DS else None
            r["z"] = [(row.fl - row.nf) / (sc[row.c] if sc is not None and row.c in sc.index and sc[row.c] > 0 else 1) for row in r.itertuples()]
            r = r.reindex(r["z"].abs().sort_values().index)
            title("What makes a flipper different: the biggest gaps come first", "Bars show the gap in standard deviations. Right of 0: flippers have more; left: less.")
            fig = go.Figure(go.Bar(y=r["name"], x=r["z"], orientation="h", marker_color=[ORA if z > 0 else PUR for z in r["z"]],
                                   hovertemplate="%{y}: %{x:.2f} std. dev.<extra></extra>"))
            fig.add_vline(x=0, line_color="#1B1340"); st.plotly_chart(style(fig, 330), width="stretch")
    with card():
        g = mon.groupby(["month", "persona"]).apply(lambda d: wmean(d, col), include_groups=False).reset_index(name="rate")
        title(f"{beh} peaks for {g.loc[g['rate'].idxmax(), 'persona']} users", "Each line is a persona: who to target changes with the month.")
        fig = go.Figure()
        for p in inP:
            d = g[g["persona"] == p]; fig.add_trace(go.Scatter(x=d["month"], y=d["rate"] * 100, name=p, line=dict(color=PCOL[p], width=3), mode="lines+markers"))
        fig.update_yaxes(title_text=f"{beh} rate (%)"); st.plotly_chart(style(fig, 300), width="stretch")

# ================= 3. PERSONAS =================
with t3:
    cols = st.columns(len(PERSONAS))
    for cx, p in zip(cols, PERSONAS):
        r = PER[PER["persona"] == p].iloc[0]
        with cx.container(key=nk()):
            st.markdown(f'<span class="tag" style="background:{PCOL[p]}">{p}</span>', unsafe_allow_html=True)
            st.metric("Share of users", f"{r['users']/PER['users'].sum()*100:.0f}%")
            st.markdown(f"**{beh} rate:** {r[col]*100:.1f}%  \n**OXXO share:** {r['oxxo']*100:.0f}%  \n**Online share:** {r['ecom']*100:.0f}%")
            st.markdown(f"**Suggested action:** {action_for(p)}")
    cA, cB = st.columns(2)
    with cA.container(key=nk()):
        metrics = ["oxxo", "ecom", "decl", "entropy", "tx"]; lab = ["OXXO share", "Online share", "Declines", "Merchant variety", "Purchases"]
        rel = PER.set_index("persona")[metrics]; rel = (rel - rel.min()) / (rel.max() - rel.min()).replace(0, 1)
        title("Each persona has a clear fingerprint", "Farther from the center = higher (relative to the other personas).")
        fig = go.Figure()
        for p in inP:
            v = rel.loc[p].tolist(); fig.add_trace(go.Scatterpolar(r=v + v[:1], theta=lab + lab[:1], name=p, fill="toself", line=dict(color=PCOL[p], width=3), opacity=.65))
        fig.update_layout(polar=dict(radialaxis=dict(visible=False)))
        st.plotly_chart(style(fig, 380), width="stretch")
    with cB.container(key=nk()):
        title("Personas side by side", "Same scale for all, so differences are real.")
        h = PER.set_index("persona")[metrics].copy(); h.columns = lab
        z = (h - h.mean()) / h.std().replace(0, 1)
        fig = go.Figure(go.Heatmap(z=z.values, x=lab, y=[p for p in h.index], colorscale=[[0, "#EDE8FF"], [.5, "#B9A8F5"], [1, DEEP]],
                                   text=[[(f"{v*100:.0f}%" if i < 3 else f"{v:,.2f}") for i, v in enumerate(row)] for row in h.values],
                                   texttemplate="%{text}", showscale=False))
        st.plotly_chart(style(fig, 380), width="stretch")

# ================= 4. TARGET LIST =================
with t4:
    S = L["scores_out"] if beh == "Flip-Out" else L["scores_in"]
    S = S[S["month"].isin(sel_m) & S["persona"].isin(inP)].sort_values("score", ascending=False).reset_index(drop=True)
    with card():
        cap = st.slider("How much of the base can Marketing reach this month? (%)", 5, 30, 10, key="cap")
        k = max(1, int(len(S) * cap / 100)); got = int(S["actual_event"].head(k).sum()); tot = max(int(S["actual_event"].sum()), 1)
        rnd = tot * cap / 100
        m1, m2, m3 = st.columns(3)
        m1.metric("Users to contact", f"{k:,}"); m2.metric(f"{beh} users captured", f"{got/tot*100:.0f}%", f"{(got-rnd)/max(rnd,1e-9)*100:.0f}% more than random")
        m3.metric("Random contact would capture", f"{cap}%")
        x = np.arange(1, 101); ss = S["actual_event"].values
        cum = np.cumsum(ss) / tot; idx = (x / 100 * len(S)).astype(int).clip(1, len(S)) - 1
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=x, y=cum[idx] * 100, name="Ranked by score", line=dict(color=ORA, width=4)))
        fig.add_trace(go.Scatter(x=x, y=x, name="Random contact", line=dict(color=MUTE, width=3, dash="dash")))
        fig.add_vrect(x0=5, x1=cap, fillcolor=PUR, opacity=.12, line_width=0)
        fig.update_xaxes(title_text="% of users contacted"); fig.update_yaxes(title_text=f"% of {beh} users reached")
        title(f"Contacting {cap}% of users with the best score reaches {got/tot*100:.0f}% of the {beh} users", "Shaded area = your capacity. Move the slider to see the trade-off.")
        st.plotly_chart(style(fig, 320), width="stretch")
    with card():
        d1, d2 = st.columns([1, 2])
        dec = d1.multiselect("Score decile (1 = highest scores)", list(range(1, 11)), default=[1], key="dec")
        T = S.head(k)
        T = T[T["decile"].isin(dec)] if dec else T
        bp = T["persona"].value_counts().reindex(inP).fillna(0)
        with d2:
            title(f"{bp.idxmax() if bp.sum() else '—'} users make up most of the list")
            fig = go.Figure(go.Bar(x=bp.index, y=bp.values, marker_color=[PCOL[p] for p in bp.index], text=bp.values.astype(int), textposition="outside"))
            st.plotly_chart(style(fig, 220), width="stretch")
        out = T.head(500).copy(); out["Rank"] = np.arange(1, len(out) + 1)
        out["Score"] = (out["score"] * 100).round(1).astype(str) + "%"; out["Suggested action"] = out["persona"].map(action_for)
        st.dataframe(out[["Rank", "user_key", "month", "persona", "Score", "decile", "Suggested action"]].rename(columns={"user_key": "User (anonymous)", "month": "Month", "persona": "Persona", "decile": "Decile"}),
                     hide_index=True, width="stretch", height=300)
        st.download_button("Download this list (CSV)", out[["user_key", "month", "persona", "score", "decile"]].to_csv(index=False), "target_list.csv")

# ================= 5. MODEL =================
with t5:
    M = MOD[MOD["behavior"] == beh]; _s = M[M["selected"] == "yes"]; sel = _s.iloc[0] if len(_s) else M[M["selected"] != "explainer"].sort_values("test_pr_auc", ascending=False).iloc[0]
    v1, v2, v3, v4 = st.columns(4)
    with v1.container(key=nk()): st.metric("Model version", meta.get("model_version", "v1.0"), help="Saved on " + str(meta.get("date", "")))
    with v2.container(key=nk()): st.metric("Precision-recall quality (PR-AUC)", f"{sel['test_pr_auc']:.2f}")
    with v3.container(key=nk()): st.metric("Captured in top 10%", f"{sel['capture10']*100:.0f}%")
    with v4.container(key=nk()): st.metric("Times better than random", f"{sel['lift10']:.1f}×")
    a, b = st.columns(2)
    with a.container(key=nk()):
        best = M.sort_values("test_pr_auc", ascending=False).iloc[0]
        title(f"{best['model']} finds {beh} users best among the models we tried", "Higher is better. The decision tree is the simple one we use to explain.")
        fig = go.Figure(go.Bar(y=M["model"], x=M["test_pr_auc"], orientation="h", text=M["test_pr_auc"].round(2), textposition="outside",
                               marker_color=[ORA if m_ == sel["model"] else MUTE for m_ in M["model"]]))
        fig.update_yaxes(autorange="reversed"); fig.update_xaxes(title_text="PR-AUC on unseen months", range=[0, max(M["test_pr_auc"]) * 1.2])
        st.plotly_chart(style(fig, 280), width="stretch")
    with b.container(key=nk()):
        d = DRV[DRV["behavior"] == beh].sort_values("importance", ascending=False); d = d[d["importance"] > 0].head(8).iloc[::-1]
        title(f"'{nice(d.iloc[-1]['feature']) if len(d) else ''}' is what the model looks at first", "Orange: the higher the value, the more likely to flip. Purple: the opposite.")
        fig = go.Figure(go.Bar(y=[nice(c) for c in d["feature"]], x=d["importance"], orientation="h", marker_color=[ORA if v > 0 else PUR for v in d["direction"]]))
        st.plotly_chart(style(fig, 280), width="stretch")
    with card():
        T_ = TREE[TREE["behavior"] == beh].sort_values("rate", ascending=False).copy()
        title("A simple decision tree explains who flips", "Each row is a rule. Pick the rows with the highest flip rate first.")
        T_["Rule"] = T_["rule"].apply(lambda s: " AND ".join(f"{nice(p.split(' ')[0])} {p.split(' ')[1]} {float(p.split(' ')[2])*(100 if p.split(' ')[0] in PCT else 1):.1f}{'%' if p.split(' ')[0] in PCT else ''}" for p in s.split(" AND ")))
        T_["Flip rate"] = (T_["rate"] * 100).round(1).astype(str) + "%"; T_["Share of users"] = (T_["share"] * 100).round(1).astype(str) + "%"
        st.table(T_[["Rule", "Flip rate", "Share of users"]])
    with card():
        title("What changed since the last version")
        E = L["experiments"]
        if E is not None: st.table(E)
        else: st.markdown("This is the first saved version: Dashboard v1 was too dense and slow, so v2 simplified it and v3 (this one) follows the planned page structure.")
st.caption("Data: aggregated tables and anonymous user IDs from a sample of Spin users. No raw Spin data is included.")
