"""International Cost of Capital — interactive financing comparison."""

from datetime import datetime, timezone
from html import escape
from io import BytesIO, StringIO
import math
import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from bs4 import BeautifulSoup


st.set_page_config(
    page_title="International Cost of Capital",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BETA_XLS = "https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls"
BETA_HTML = "https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/Betas.html"
BBB_URL = "https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ratings.html"
OECD_URL = (
    "https://www.oecd.org/en/publications/corporate-tax-statistics-2026_73af6222-en/"
    "full-report/statutory-corporate-income-tax-rates_ce84abb9.html"
)
OECD_API = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0/"
)
BONDS_URL = "https://tradingeconomics.com/bonds"
DEFAULT_INDUSTRY = "Software (System & Application)"

# Country code, currency, Trading Economics page identifier.
COUNTRIES = {
    "United States": ("USA", "USD", "united-states"),
    "Australia": ("AUS", "AUD", "australia"),
    "Austria": ("AUT", "EUR", "austria"),
    "Belgium": ("BEL", "EUR", "belgium"),
    "Brazil": ("BRA", "BRL", "brazil"),
    "Canada": ("CAN", "CAD", "canada"),
    "Chile": ("CHL", "CLP", "chile"),
    "China": ("CHN", "CNY", "china"),
    "Colombia": ("COL", "COP", "colombia"),
    "Costa Rica": ("CRI", "CRC", "costa-rica"),
    "Croatia": ("HRV", "EUR", "croatia"),
    "Czechia": ("CZE", "CZK", "czech-republic"),
    "Denmark": ("DNK", "DKK", "denmark"),
    "Egypt": ("EGY", "EGP", "egypt"),
    "Finland": ("FIN", "EUR", "finland"),
    "France": ("FRA", "EUR", "france"),
    "Germany": ("DEU", "EUR", "germany"),
    "Greece": ("GRC", "EUR", "greece"),
    "Hungary": ("HUN", "HUF", "hungary"),
    "Iceland": ("ISL", "ISK", "iceland"),
    "India": ("IND", "INR", "india"),
    "Indonesia": ("IDN", "IDR", "indonesia"),
    "Ireland": ("IRL", "EUR", "ireland"),
    "Israel": ("ISR", "ILS", "israel"),
    "Italy": ("ITA", "EUR", "italy"),
    "Japan": ("JPN", "JPY", "japan"),
    "Malaysia": ("MYS", "MYR", "malaysia"),
    "Mexico": ("MEX", "MXN", "mexico"),
    "Netherlands": ("NLD", "EUR", "netherlands"),
    "New Zealand": ("NZL", "NZD", "new-zealand"),
    "Nigeria": ("NGA", "NGN", "nigeria"),
    "Norway": ("NOR", "NOK", "norway"),
    "Pakistan": ("PAK", "PKR", "pakistan"),
    "Peru": ("PER", "PEN", "peru"),
    "Philippines": ("PHL", "PHP", "philippines"),
    "Poland": ("POL", "PLN", "poland"),
    "Portugal": ("PRT", "EUR", "portugal"),
    "Romania": ("ROU", "RON", "romania"),
    "Singapore": ("SGP", "SGD", "singapore"),
    "Slovakia": ("SVK", "EUR", "slovakia"),
    "Slovenia": ("SVN", "EUR", "slovenia"),
    "South Africa": ("ZAF", "ZAR", "south-africa"),
    "South Korea": ("KOR", "KRW", "south-korea"),
    "Spain": ("ESP", "EUR", "spain"),
    "Sweden": ("SWE", "SEK", "sweden"),
    "Switzerland": ("CHE", "CHF", "switzerland"),
    "Thailand": ("THA", "THB", "thailand"),
    "Turkey": ("TUR", "TRY", "turkey"),
    "United Kingdom": ("GBR", "GBP", "united-kingdom"),
    "Vietnam": ("VNM", "VND", "vietnam"),
}


# HTML is rendered with st.html, not Markdown, so nested tags are never
# interpreted as indented code blocks.
st.html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap');
:root{color-scheme:dark}
html,body,[data-testid="stApp"]{font-family:'DM Sans',sans-serif}
[data-testid="stApp"]{background:radial-gradient(ellipse at 80% -12%,#1d3556,transparent 40%),#090f1d;color:#ecf4ff}
[data-testid="stSidebar"]{background:#0d182a;border-right:1px solid #2b405c}
.block-container{max-width:1480px;padding-top:1.5rem;padding-bottom:2.5rem}
h1,h2,h3{font-family:'Manrope',sans-serif;letter-spacing:-.035em}
.hero{position:relative;overflow:hidden;border-radius:24px;padding:34px 38px;margin-bottom:18px;background:linear-gradient(113deg,#19304d,#111c32 65%,#172039);border:1px solid #39526d;box-shadow:0 22px 60px #0005}
.hero:before{content:'';position:absolute;right:-95px;top:-195px;width:440px;height:440px;border-radius:50%;background:radial-gradient(circle,#40d6c94b,transparent 66%);pointer-events:none;animation:floatglow 9s ease-in-out infinite alternate}
@keyframes floatglow{to{transform:translate(-55px,65px)}}
.hero h1{position:relative;color:#fff;font-weight:800;font-size:clamp(31px,4.1vw,55px);line-height:1.15;margin:0 0 13px}
.hero p{position:relative;color:#bed0e6;max-width:760px;font-size:15px;line-height:1.7;margin:0}
.section-label{color:#a4b9d4;font-size:11px;letter-spacing:.15em;font-weight:800;text-transform:uppercase;margin:21px 0 12px}
.rate-card{border-radius:21px;padding:25px 27px;min-height:225px;background:linear-gradient(145deg,#152b47,#101c30);border:1px solid #31516e;box-shadow:0 14px 35px #0003;transition:transform .2s,border-color .2s}
.rate-card:hover{transform:translateY(-4px);border-color:#63dbcf}
.rate-card.local{background:linear-gradient(145deg,#2a2348,#151c32);border-color:#5a467d}
.rate-card.local:hover{border-color:#baa0fa}
.card-label{font-size:12px;letter-spacing:.13em;text-transform:uppercase;font-weight:800;color:#b1c5df}
.card-number{font:800 clamp(40px,4.5vw,65px)/1.3 'Manrope',sans-serif;letter-spacing:-.06em;color:#65e7d6;margin:9px 0 4px}
.local .card-number{color:#c6aaff}
.card-caption{color:#96acc8;font-size:11px;letter-spacing:.09em;margin-bottom:20px}
.card-grid{border-top:1px solid #33506a;display:grid;grid-template-columns:1fr 1fr;gap:15px;padding-top:16px}
.card-grid small{display:block;font-size:11px;color:#a1b5d1;margin-bottom:5px}
.card-grid strong{color:#f4f7ff;font:700 16px 'Manrope',sans-serif}
.chips{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}
.chip{background:#13243b;border:1px solid #304863;border-radius:12px;padding:10px 14px;font-size:12px;color:#abc1d9}
.chip strong{font-size:14px;color:#f3f8ff;margin-left:7px}
[data-testid="stButton"] button,[data-testid="stDownloadButton"] button{border-radius:11px!important;background:linear-gradient(110deg,#164153,#233955)!important;border:1px solid #498d9b!important;color:#edfcff!important;font-weight:700!important;transition:transform .17s,box-shadow .18s,filter .18s!important}
[data-testid="stButton"] button:hover,[data-testid="stDownloadButton"] button:hover{transform:translateY(-2px);filter:brightness(1.2);box-shadow:0 8px 25px #27e0c52e}
[data-testid="stButton"] button:active,[data-testid="stDownloadButton"] button:active{transform:scale(.975)}
[data-testid="stTabs"] [data-baseweb="tab"]{font-weight:700}
[data-testid="stDataFrame"]{border-radius:12px;overflow:hidden}
.footer{margin-top:34px;padding-top:17px;border-top:1px solid #2c415a;color:#97abc5;font-size:12px}
@media(max-width:640px){.hero{padding:24px 21px}.rate-card{padding:21px}.card-number{font-size:38px}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation:none!important;transition:none!important}}
</style>
""")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"
}


def fetched_at():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def request(url, timeout=25):
    r = requests.get(url, headers=HEADERS, timeout=(7, timeout))
    r.raise_for_status()
    return r


def record(value, url, date="Unavailable", error=None):
    return dict(value=value, url=url, date=date, fetched=fetched_at(), error=error)


def analysis_date(html):
    text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
    m = re.search(r"Date of Analysis:\s*Data used is as of\s*([A-Za-z]+\s+\d{4})", text, re.I)
    return m.group(1) if m else "Publisher date not specified"


def normalize(value):
    return re.sub(r"\s+", " ", str(value).replace("\xa0", " ")).strip().casefold()


def extract_beta_rows(rows):
    """Locate exact unlevered-beta column despite irregular XLS/HTML headers."""
    for i, row in enumerate(rows):
        header = [normalize(x) for x in row]
        try:
            name_idx = header.index("industry name")
            beta_idx = header.index("unlevered beta")
        except ValueError:
            continue
        output = {}
        for values in rows[i + 1:]:
            if max(name_idx, beta_idx) >= len(values):
                continue
            name = " ".join(str(values[name_idx]).split())
            value = pd.to_numeric(values[beta_idx], errors="coerce")
            if (name and normalize(name) not in {"nan", "none"}
                    and not normalize(name).startswith("total market")
                    and pd.notna(value) and -5 < float(value) < 10):
                output[name] = float(value)
        if len(output) >= 35 and DEFAULT_INDUSTRY in output:
            return dict(sorted(output.items()))
    raise ValueError("The industry name and unlevered beta columns were not found together")


def extract_betas_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # Direct table-cell parsing handles HTML headers that pandas reads as a MultiIndex.
    for table in soup.find_all("table"):
        rows = [
            [c.get_text(" ", strip=True) for c in tr.find_all(["th", "td"], recursive=False)]
            for tr in table.find_all("tr")
        ]
        try:
            return extract_beta_rows(rows)
        except ValueError:
            continue
    # Independent fallback for imperfect table markup.
    for frame in pd.read_html(StringIO(html), header=None):
        try:
            return extract_beta_rows(frame.fillna("").values.tolist())
        except ValueError:
            continue
    raise ValueError("U.S. industry unlevered beta table not found")


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_betas():
    failures = []
    try:
        response = request(BETA_XLS)
        sheets = pd.read_excel(BytesIO(response.content), header=None,
                               sheet_name=None, engine="xlrd")
        for frame in sheets.values():
            try:
                data = extract_beta_rows(frame.fillna("").values.tolist())
                try:
                    date = analysis_date(request(BETA_HTML).text)
                except Exception:
                    date = "Publisher date not available"
                return record(data, BETA_XLS, date)
            except ValueError:
                continue
        failures.append("Excel: industry table not found")
    except Exception as exc:
        failures.append(f"Excel: {exc}")
    try:
        html = request(BETA_HTML).text
        return record(extract_betas_html(html), BETA_HTML, analysis_date(html))
    except Exception as exc:
        failures.append(f"HTML: {exc}")
    return record({}, BETA_HTML, error=" | ".join(failures))


@st.cache_data(ttl=21600, show_spinner=False)
def fetch_bbb():
    try:
        html = request(BBB_URL).text
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        # First matching rating is in the large nonfinancial services table.
        match = re.search(r"Baa2\s*/\s*BBB\s+(\d+(?:\.\d+)?)\s*%", text, re.I)
        if not match:
            raise ValueError("Baa2/BBB spread not found")
        spread = float(match.group(1))
        if not 0 <= spread <= 30:
            raise ValueError("BBB borrowing spread outside supported range")
        return record(spread, BBB_URL, analysis_date(html))
    except Exception as exc:
        return record(None, BBB_URL, error=str(exc))


@st.cache_data(ttl=43200, show_spinner=False)
def fetch_taxes():
    url = (OECD_API + ".A.CIT_C.ST..S13...?startPeriod=2024"
           "&dimensionAtObservation=AllDimensions&format=csvfilewithlabels")
    try:
        df = pd.read_csv(BytesIO(request(url, timeout=40).content), low_memory=False)
        df.columns = [str(c).strip() for c in df.columns]
        if not {"REF_AREA", "TIME_PERIOD", "OBS_VALUE"}.issubset(df.columns):
            raise ValueError("OECD response does not contain the expected data columns")
        for column, code in (("MEASURE", "CIT_C"), ("TARGETING", "ST"),
                             ("INSTITUTIONAL_SECTOR", "S13")):
            if column in df.columns:
                df = df.loc[df[column].astype(str).str.strip() == code]
        if "UNIT_MEASURE" in df.columns and df["UNIT_MEASURE"].eq("PT_INC_TAX").any():
            df = df.loc[df["UNIT_MEASURE"] == "PT_INC_TAX"]
        df = df.copy()
        df["rate"] = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
        df["year"] = pd.to_numeric(df["TIME_PERIOD"], errors="coerce")
        df = df.loc[df["rate"].between(0, 100) & df["year"].between(2024, 2100)]
        allowed = {item[0] for item in COUNTRIES.values()}
        rates = {}
        for code, group in df.groupby("REF_AREA"):
            code = str(code).strip().upper()
            if code not in allowed:
                continue
            latest = group.loc[group["year"] == group["year"].max()]
            unique = latest["rate"].round(8).unique()
            if len(unique) == 1:
                rates[code] = (float(unique[0]), str(int(latest["year"].iloc[0])))
        if "USA" not in rates or len(rates) < 15:
            raise ValueError(f"Only {len(rates)} unambiguous corporate tax rates returned")
        return record(rates, url, "Latest available year by country")
    except Exception as exc:
        return record({}, url, error=str(exc))


@st.cache_data(ttl=900, show_spinner=False)
def fetch_yield(slug):
    url = f"https://tradingeconomics.com/{slug}/government-bond-yield"
    try:
        soup = BeautifulSoup(request(url).text, "html.parser")
        h1 = soup.find("h1")
        if not h1 or not re.search(r"10\s*[- ]?\s*Year", h1.get_text(" ", strip=True), re.I):
            raise ValueError("10-year government bond heading not found")
        text = soup.get_text(" ", strip=True)
        pos = text.find(h1.get_text(" ", strip=True))
        if pos < 0:
            raise ValueError("10-year quote location not found")
        match = re.search(r"\bActual\s+(-?\d+(?:\.\d+)?)\b", text[pos:pos + 500], re.I)
        if not match:
            raise ValueError("Observed 10-year yield not available (forecast excluded)")
        value = float(match.group(1))
        if not -25 < value < 100:
            raise ValueError("Government yield outside supported range")
        stamp = re.search(r"last updated on\s+([A-Za-z]+\s+\d{1,2}(?:\s+of)?\s+\d{4})",
                          text, re.I)
        return record(value, url, stamp.group(1) if stamp else "Date not stated")
    except Exception as exc:
        return record(None, url, error=str(exc))


def calculate(beta_u, tax, erp, debt, usd_rf, local_rf, usd_spread, local_spread=None):
    """Costs of equity/debt and WACC. All inputs are decimal rates."""
    vals = [beta_u, tax, erp, debt, usd_rf, local_rf, usd_spread]
    if not all(math.isfinite(float(x)) for x in vals):
        raise ValueError("All inputs must be finite")
    if not (0 <= tax <= 1 and 0 <= debt < 1 and usd_rf > -1 and local_rf > -1):
        raise ValueError("Invalid tax, debt share, or government yield")
    if local_spread is not None and not math.isfinite(float(local_spread)):
        raise ValueError("Invalid foreign borrowing spread")
    debt_equity = debt / (1 - debt)
    beta_e = beta_u * (1 + (1 - tax) * debt_equity)
    re_usd = usd_rf + beta_e * erp
    rd_usd = usd_rf + usd_spread
    wacc_usd = (1 - debt) * re_usd + debt * rd_usd * (1 - tax)
    factor = (1 + local_rf) / (1 + usd_rf)
    re_local = (1 + re_usd) * factor - 1
    spread_auto = usd_spread * factor
    spread_used = spread_auto if local_spread is None else local_spread
    rd_local = local_rf + spread_used
    wacc_local = (1 - debt) * re_local + debt * rd_local * (1 - tax)
    return dict(beta_e=beta_e, debt_equity=debt_equity, factor=factor,
                re_usd=re_usd, rd_usd=rd_usd, after_usd=rd_usd * (1 - tax),
                wacc_usd=wacc_usd, re_local=re_local, rd_local=rd_local,
                after_local=rd_local * (1 - tax), wacc_local=wacc_local,
                spread_auto=spread_auto, spread_used=spread_used)


def calculation_checks():
    base = calculate(.8, .35, .065, .3, .04, .12, .015)
    same = calculate(.8, .35, .065, .3, .04, .04, .015)
    zero = calculate(.8, .35, .065, 0, .04, .12, .015)
    override = calculate(.8, .35, .065, .3, .04, .12, .015, .03)
    close = lambda a, b: math.isclose(a, b, abs_tol=1e-11, rel_tol=0)
    return {
        "Illustrative USD cost of equity: 10.6486%": close(base["re_usd"], .1064857142857143),
        "Illustrative USD WACC: 8.5265%": close(base["wacc_usd"], .085265),
        "Illustrative COP cost of equity: 19.1600%": close(base["re_local"], .1916),
        "Illustrative COP WACC: 16.0670%": close(base["wacc_local"], .16067),
        "Equal government yields give equal financing costs": all(
            close(same[a], same[b]) for a, b in
            (("re_usd", "re_local"), ("rd_usd", "rd_local"), ("wacc_usd", "wacc_local"))),
        "Zero debt makes WACC equal cost of equity": (
            close(zero["wacc_usd"], zero["re_usd"]) and
            close(zero["wacc_local"], zero["re_local"])),
        "Foreign borrowing-spread override leaves USD unchanged": all(
            close(base[k], override[k]) for k in ("re_usd", "rd_usd", "wacc_usd")),
    }


def pct(x):
    return f"{100 * x:,.4f}%"


def input_field(label, automatic, key, min_value=0.0, max_value=100.0, step=0.1):
    enabled = st.toggle(f"Override {label}", key="override_" + key)
    if enabled or automatic is None:
        if automatic is None:
            st.caption("Source unavailable — enter a verified value.")
        value = st.number_input(label, min_value=float(min_value), max_value=float(max_value),
                                value=float(automatic) if automatic is not None else None,
                                step=float(step), format="%.4f", key="manual_" + key)
        return value, "Manual" if value is not None else "Missing"
    st.caption(f"{label}: **{automatic:,.4f}** · Automatic")
    return automatic, "Automatic"


def result_card(name, currency, values, local=False):
    prefix = "local" if local else "usd"
    css_class = " local" if local else ""
    html = f"""
    <div class="rate-card{css_class}">
      <div class="card-label">{escape(name)} · {escape(currency)}</div>
      <div class="card-number">{pct(values['wacc_' + prefix])}</div>
      <div class="card-caption">WEIGHTED AVERAGE COST OF CAPITAL</div>
      <div class="card-grid">
        <div><small>Cost of Equity</small><strong>{pct(values['re_' + prefix])}</strong></div>
        <div><small>Pretax Cost of Debt</small><strong>{pct(values['rd_' + prefix])}</strong></div>
        <div><small>After-Tax Cost of Debt</small><strong>{pct(values['after_' + prefix])}</strong></div>
        <div><small>WACC</small><strong>{pct(values['wacc_' + prefix])}</strong></div>
      </div>
    </div>"""
    st.html(html)


# ------------------------------------------------------------
# APPLICATION
# ------------------------------------------------------------

st.html("""
<div class="hero">
  <h1>International Cost of Capital</h1>
  <p>Compare a project's cost of equity, debt, and WACC in USD and the selected country's currency.</p>
</div>
""")

control_col, note_col = st.columns([1, 3], vertical_alignment="center")
with control_col:
    if st.button("↻ Refresh Data", use_container_width=True):
        fetch_betas.clear()
        fetch_bbb.clear()
        fetch_taxes.clear()
        fetch_yield.clear()
        st.session_state["refresh_notice"] = True
        st.rerun()
with note_col:
    st.caption("Inputs recalculate automatically. Refresh Data requests updated source values.")
if st.session_state.pop("refresh_notice", False):
    st.toast("Source data requested again.")

with st.spinner("Retrieving industry betas, tax rates, and borrowing spread…"):
    betas_data = fetch_betas()
    bbb_data = fetch_bbb()
    taxes_data = fetch_taxes()

beta_map = betas_data["value"]
industries = sorted(set(beta_map) | {DEFAULT_INDUSTRY})

with st.sidebar:
    st.header("Project Settings")
    industry = st.selectbox("Industry", industries, index=industries.index(DEFAULT_INDUSTRY))
    country = st.selectbox("Target Country", list(COUNTRIES))
    code, currency, slug = COUNTRIES[country]
    tax_mode = st.segmented_control("Corporate Tax Rate", ["U.S.", "Selected Country"],
                                    default="U.S.")
    erp_pct = st.number_input("Equity Risk Premium (%)", min_value=0.0,
                              max_value=50.0, value=6.5, step=0.1, format="%.2f")
    debt_pct = st.slider("Target Debt Share (%)", min_value=0, max_value=99, value=30)
    st.caption("The same corporate tax rate, equity risk premium, and debt share apply to both currencies.")

with st.spinner("Retrieving 10-year government bond yields…"):
    us_bond = fetch_yield("united-states")
    local_bond = us_bond if code == "USA" else fetch_yield(slug)

with st.sidebar:
    with st.expander("Manual Overrides", expanded=True):
        st.caption("Rates are entered in percent; for example, 4.25 means 4.25%.")
        beta, beta_mode = input_field("Unlevered Beta", beta_map.get(industry),
                                      "beta_" + industry, -5, 10, .05)
        tax_us, tax_us_mode = input_field(
            "U.S. Corporate Tax Rate (%)", taxes_data["value"].get("USA", (None, None))[0], "tax_USA")
        if code == "USA":
            tax_local, tax_local_mode = tax_us, "Same as U.S."
        else:
            tax_local, tax_local_mode = input_field(
                f"{country} Corporate Tax Rate (%)",
                taxes_data["value"].get(code, (None, None))[0], "tax_" + code)
        spread, spread_mode = input_field("USD BBB Borrowing Spread (pp)",
                                          bbb_data["value"], "spread_USD")
        rf_us, us_yield_mode = input_field("U.S. 10-Year Government Yield (%)",
                                           us_bond["value"], "yield_USA", -25)
        if code == "USA":
            rf_local, local_yield_mode = rf_us, "Same as U.S."
        else:
            rf_local, local_yield_mode = input_field(
                f"{country} 10-Year Government Yield (%)",
                local_bond["value"], "yield_" + code, -25)
        st.divider()
        use_manual_spread = st.toggle("Override Foreign-Currency BBB Spread")
        if all(v is not None for v in (spread, rf_us, rf_local)) and rf_us > -100:
            auto_spread_pct = float(spread) * (100 + float(rf_local)) / (100 + float(rf_us))
        else:
            auto_spread_pct = None
        if use_manual_spread:
            foreign_spread_pct = st.number_input(
                "Foreign-Currency BBB Spread (pp)", min_value=0.0, max_value=100.0,
                value=auto_spread_pct, step=0.1, format="%.4f")
        else:
            foreign_spread_pct = None
            st.caption("Automatically calculated spread: " +
                       (f"**{auto_spread_pct:.4f} pp**" if auto_spread_pct is not None
                        else "Awaiting source inputs"))

chosen_tax = tax_us if tax_mode == "U.S." else tax_local
needed = {
    "Unlevered Beta": beta,
    "Corporate Tax Rate": chosen_tax,
    "USD BBB Borrowing Spread": spread,
    "U.S. 10-Year Government Yield": rf_us,
    "Selected-Country 10-Year Government Yield": rf_local,
    "Foreign-Currency BBB Spread": foreign_spread_pct if use_manual_spread else 0.0,
}
missing = [label for label, value in needed.items() if value is None]

if missing:
    st.warning("Missing data: " + ", ".join(missing) + ". Enter verified values in Manual Overrides.")
else:
    params = dict(tax=float(chosen_tax) / 100, erp=erp_pct / 100,
                  debt=debt_pct / 100, usd_rf=float(rf_us) / 100,
                  local_rf=float(rf_local) / 100, usd_spread=float(spread) / 100,
                  local_spread=(float(foreign_spread_pct) / 100 if use_manual_spread else None))
    result = calculate(beta_u=float(beta), **params)
    st.html('<div class="section-label">Cost of Capital Comparison</div>')
    left, right = st.columns(2, gap="medium")
    with left:
        result_card("United States", "USD", result)
    with right:
        result_card(country, currency, result, local=True)
    st.html(f"""
    <div class="chips">
      <div class="chip">Levered Beta <strong>{result['beta_e']:.4f}</strong></div>
      <div class="chip">Debt / Equity <strong>{result['debt_equity']:.4f}</strong></div>
      <div class="chip">Corporate Tax Rate <strong>{float(chosen_tax):.2f}%</strong></div>
      <div class="chip">WACC Difference <strong>{100 * (result['wacc_local'] - result['wacc_usd']):+.4f} pp</strong></div>
    </div>""")
    st.caption(f"Foreign-currency BBB borrowing spread: {100 * result['spread_used']:.4f} pp "
               f"({'Manual override' if use_manual_spread else 'Automatic calculation'}).")

# Keep methodology, checks and source diagnostics available even without a beta.
overview, industries_tab, methods, sources_tab = st.tabs([
    "Overview", "All-Industry Comparison", "Calculations and Assumptions", "Data Sources"
])

with overview:
    if not missing:
        st.subheader("Cost of Equity, Debt, and WACC")
        labels = ["Cost of Equity", "Pretax Cost of Debt", "After-Tax Cost of Debt", "WACC"]
        fig = go.Figure()
        for name, keys, color in (
            ("USD", ("re_usd", "rd_usd", "after_usd", "wacc_usd"), "#62e3d4"),
            (f"{currency} · {country}", ("re_local", "rd_local", "after_local", "wacc_local"), "#b79df9"),
        ):
            fig.add_bar(name=name, x=labels, y=[100 * result[k] for k in keys],
                        marker_color=color, hovertemplate="%{x}<br>%{y:.4f}%<extra></extra>")
        fig.update_layout(
            barmode="group", height=420, margin=dict(l=6, r=8, t=32, b=6),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#d3e3f4", family="DM Sans"),
            yaxis=dict(title="Annual rate (%)", gridcolor="#2a3c54"),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", y=1.13, x=0), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        export = {
            "Industry": industry, "Target Country": country, "Currency": currency,
            "Unlevered Beta": beta, "Levered Beta": result["beta_e"],
            "Tax Jurisdiction": tax_mode, "Corporate Tax Rate (%)": chosen_tax,
            "Equity Risk Premium (%)": erp_pct, "Target Debt Share (%)": debt_pct,
            "U.S. 10-Year Government Yield (%)": rf_us,
            "Selected-Country 10-Year Government Yield (%)": rf_local,
            "USD BBB Borrowing Spread (pp)": spread,
            "Foreign-Currency BBB Borrowing Spread (pp)": 100 * result["spread_used"],
            "Foreign Spread Input Mode": "Manual" if use_manual_spread else "Automatic",
            "USD Cost of Equity (%)": 100 * result["re_usd"],
            "Foreign-Currency Cost of Equity (%)": 100 * result["re_local"],
            "USD Pretax Cost of Debt (%)": 100 * result["rd_usd"],
            "Foreign-Currency Pretax Cost of Debt (%)": 100 * result["rd_local"],
            "USD After-Tax Cost of Debt (%)": 100 * result["after_usd"],
            "Foreign-Currency After-Tax Cost of Debt (%)": 100 * result["after_local"],
            "USD WACC (%)": 100 * result["wacc_usd"],
            "Foreign-Currency WACC (%)": 100 * result["wacc_local"],
        }
        st.download_button("↓ Download Results", pd.DataFrame([export]).to_csv(index=False),
                           file_name="international_cost_of_capital.csv", mime="text/csv")
    else:
        st.info("Results will appear when the required inputs are available.")

with industries_tab:
    st.subheader("All-Industry Comparison")
    st.caption("All industries use the same corporate tax rate, equity risk premium, debt share, borrowing spread, and yields.")
    if missing:
        st.info("Complete the required inputs to see the industry comparison.")
    elif not beta_map:
        st.info("Industry data is unavailable. Use Refresh Data to retry.")
    else:
        rows = []
        for name, source_beta in beta_map.items():
            industry_beta = float(beta) if name == industry and beta_mode == "Manual" else source_beta
            r = calculate(beta_u=industry_beta, **params)
            rows.append({
                "Industry": name, "Unlevered Beta": industry_beta,
                "Levered Beta": r["beta_e"],
                "USD Cost of Equity (%)": 100 * r["re_usd"],
                "Foreign-Currency Cost of Equity (%)": 100 * r["re_local"],
                "USD Pretax Cost of Debt (%)": 100 * r["rd_usd"],
                "Foreign-Currency Pretax Cost of Debt (%)": 100 * r["rd_local"],
                "USD WACC (%)": 100 * r["wacc_usd"],
                "Foreign-Currency WACC (%)": 100 * r["wacc_local"],
            })
        industry_table = pd.DataFrame(rows).sort_values("USD WACC (%)", ascending=False)
        st.dataframe(industry_table, use_container_width=True, hide_index=True, height=480)
        st.download_button("↓ Download Industry Comparison", industry_table.to_csv(index=False),
                           file_name="international_cost_of_capital_industries.csv", mime="text/csv")

with methods:
    st.subheader("Calculations and Assumptions")
    st.markdown(r"""
All rates are decimals. The same corporate tax rate, equity risk premium, and target debt share
apply in both currencies.

**Levered Beta**

$$\frac{D}{E}=\frac{d}{1-d}$$

$$\beta_E=\beta_U\left[1+(1-\tau)\frac{D}{E}\right]$$

**USD Cost of Equity, Cost of Debt, and WACC**

$$R_e=R_f+\beta_E\times ERP$$

$$R_d=R_f+s$$

$$WACC=(1-d)R_e+dR_d(1-\tau)$$

**Selected-Country Currency**

$$F=\frac{1+R_f^*}{1+R_f}$$

$$R_e^*=(1+R_e)F-1$$

$$s^*=sF$$

$$R_d^*=R_f^*+s^*$$

$$WACC^*=(1-d)R_e^*+dR_d^*(1-\tau)$$

A manual foreign-currency BBB spread replaces the calculated $s^*$ in the foreign-currency
cost of debt and WACC only.

**Main Assumptions**

- U.S. industry unlevered betas proxy for project risk relative to the U.S. stock market.
- Government bond yields proxy for currency-specific risk-free rates, but may include term,
  liquidity, and sovereign risk premia.
- No separate country equity risk premium is included.
- Debt beta is zero and interest tax deductions are fully usable.
- Target debt share is constant.
- Currency conversion uses relative PPP and equal-real-interest-rate approximations.
""")
    st.subheader("Calculation Verification")
    if st.button("Run Calculation Checks"):
        checks = calculation_checks()
        for description, passed in checks.items():
            st.write(("✓ " if passed else "✕ ") + description)
        if all(checks.values()):
            st.success("All calculation checks passed.")
        else:
            st.error("A calculation check failed.")

with sources_tab:
    st.subheader("Data Sources and Dates")
    st.caption("Data dates reflect the publisher's latest stated observations; retrieval times reflect when the app fetched the pages.")
    rows = [
        ("Unlevered Beta", "Damodaran", betas_data, betas_data["date"], beta_mode),
        ("USD BBB Borrowing Spread", "Damodaran", bbb_data, bbb_data["date"], spread_mode),
        ("U.S. Corporate Tax Rate", "OECD", taxes_data,
         taxes_data["value"].get("USA", (None, "Unavailable"))[1], tax_us_mode),
        (f"{country} Corporate Tax Rate", "OECD", taxes_data,
         taxes_data["value"].get(code, (None, "Unavailable"))[1], tax_local_mode),
        ("U.S. 10-Year Government Yield", "Trading Economics", us_bond,
         us_bond["date"], us_yield_mode),
        (f"{country} 10-Year Government Yield", "Trading Economics", local_bond,
         local_bond["date"], local_yield_mode),
    ]
    st.dataframe(pd.DataFrame([
        {"Input": label, "Provider": provider, "Source Date": date,
         "Input Mode": mode, "Retrieved (UTC)": item["fetched"], "URL": item["url"]}
        for label, provider, item, date, mode in rows
    ]), hide_index=True, use_container_width=True)
    st.caption("Foreign-currency BBB spread: " +
               ("Manual override" if use_manual_spread else "Calculated from the U.S. BBB spread and both government yields"))
    st.markdown(f"[Industry Betas]({BETA_XLS}) · [BBB Borrowing Spread]({BBB_URL}) · "
                f"[OECD Corporate Tax Rates]({OECD_URL}) · [Government Bond Yields]({BONDS_URL})")
    for label, data in (("Industry betas", betas_data), ("BBB spread", bbb_data),
                        ("Corporate tax rates", taxes_data), ("U.S. yield", us_bond),
                        ("Selected-country yield", local_bond)):
        if data["error"]:
            st.warning(f"{label}: {data['error']}")

st.html("""
<div class="footer">
International Cost of Capital · Full-precision calculations; displayed rates are rounded.
</div>
""")
