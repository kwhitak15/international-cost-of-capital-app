 """International Cost of Capital — Streamlit application."""

from datetime import datetime, timezone
from html import escape
from io import BytesIO, StringIO
import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="International Cost of Capital",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

BETAS_XLS = (
    "https://pages.stern.nyu.edu/"
    "~adamodar/pc/datasets/betas.xls"
)

BETAS_HTML = (
    "https://pages.stern.nyu.edu/"
    "~adamodar/New_Home_Page/datafile/Betas.html"
)

BBB_URL = (
    "https://pages.stern.nyu.edu/"
    "adamodar/New_Home_Page/datafile/ratings.html"
)

OECD_URL = (
    "https://www.oecd.org/en/publications/"
    "corporate-tax-statistics-2026_73af6222-en/"
    "full-report/"
    "statutory-corporate-income-tax-rates_ce84abb9.html"
)

OECD_API = (
    "https://sdmx.oecd.org/public/rest/data/"
    "OECD.CTP.TPS,DSD_TAX_CIT@DF_CIT,2.0/"
)

BONDS_URL = "https://tradingeconomics.com/bonds"

DEFAULT_INDUSTRY = "Software (System & Application)"


# ============================================================
# COUNTRIES
# ============================================================

# ISO-3 country code, currency, Trading Economics URL identifier.

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


# ============================================================
# VISUAL DESIGN
# ============================================================

st.markdown(
    """
<style>

@import url(
'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;600;700;800&display=swap'
);

html,
body,
[data-testid="stApp"] {
    font-family: 'DM Sans', sans-serif;
}

[data-testid="stApp"] {
    background:
        radial-gradient(
            ellipse at 85% -10%,
            #1c3353,
            transparent 39%
        ),
        #09101d;

    color: #eef4ff;
}

[data-testid="stSidebar"] {
    background: #0e182a;
    border-right: 1px solid #2b3e57;
}

.block-container {
    max-width: 1480px;
    padding-top: 1.4rem;
    padding-bottom: 3rem;
}

h1,
h2,
h3 {
    font-family: 'Manrope', sans-serif;
    letter-spacing: -.035em;
}


/* HEADER */

.hero {
    position: relative;
    overflow: hidden;

    padding: 34px 38px;
    margin-bottom: 18px;

    background:
        linear-gradient(
            115deg,
            #182f4e,
            #111c32 65%,
            #172039
        );

    border: 1px solid #35506d;
    border-radius: 24px;

    box-shadow: 0 22px 60px #0004;
}

.hero:before {
    content: '';

    position: absolute;

    right: -110px;
    top: -170px;

    width: 460px;
    height: 460px;

    border-radius: 50%;

    background:
        radial-gradient(
            circle,
            #43ddcd40,
            transparent 65%
        );

    animation:
        glow 9s ease-in-out infinite alternate;

    pointer-events: none;
}

@keyframes glow {
    to {
        transform: translate(-65px, 55px);
    }
}

.hero h1 {
    color: #fff;

    font-size: clamp(30px, 4.2vw, 56px);
    font-weight: 800;

    margin: 0 0 12px;
}

.hero p {
    color: #b7c9e2;

    font-size: 15px;
    line-height: 1.65;

    margin: 0;
    max-width: 790px;
}


/* SECTION LABELS */

.section-label {
    font-size: 11px;
    font-weight: 800;

    letter-spacing: .16em;

    color: #a1b7d3;

    text-transform: uppercase;

    margin: 18px 0 11px;
}


/* RESULTS CARDS */

.rate-card {
    background:
        linear-gradient(
            150deg,
            #162b46,
            #101b30
        );

    border: 1px solid #31536e;
    border-radius: 21px;

    padding: 25px 27px;

    min-height: 232px;

    box-shadow: 0 15px 35px #0003;

    transition:
        transform .22s,
        border-color .22s;
}

.rate-card:hover {
    transform: translateY(-4px);
    border-color: #5bd3c9;
}

.rate-card.local {
    background:
        linear-gradient(
            150deg,
            #292244,
            #141c32
        );

    border-color: #57477d;
}

.rate-card.local:hover {
    border-color: #ad9af2;
}

.rate-card .country {
    font-size: 12px;

    letter-spacing: .12em;
    text-transform: uppercase;

    font-weight: 700;
    color: #aec4df;
}

.rate-card .big {
    font:
        800 clamp(39px, 4.7vw, 66px)/1.3
        'Manrope', sans-serif;

    letter-spacing: -.06em;
    color: #62e5d4;

    margin: 11px 0 3px;
}

.rate-card.local .big {
    color: #c4aaff;
}

.rate-card .caption {
    font-size: 11px;

    letter-spacing: .1em;

    color: #9eb3ce;

    margin-bottom: 21px;
}

.rate-card .details {
    border-top: 1px solid #35506c;

    padding-top: 16px;

    display: grid;
    grid-template-columns: 1fr 1fr;

    gap: 15px;
}

.rate-card .details small {
    display: block;

    font-size: 11px;
    color: #99acc9;

    margin-bottom: 4px;
}

.rate-card .details strong {
    font:
        700 16px 'Manrope', sans-serif;

    color: #f5f8ff;
}


/* SUMMARY INDICATORS */

.chips {
    display: flex;
    flex-wrap: wrap;

    gap: 10px;

    margin: 16px 0;
}

.chip {
    background: #13243a;

    border: 1px solid #304764;
    border-radius: 12px;

    padding: 11px 15px;

    font-size: 12px;
    color: #a4b9d4;
}

.chip b {
    color: #f1f7ff;

    margin-left: 8px;

    font-size: 14px;
}


/* BUTTON INTERACTIONS */

[data-testid="stButton"] button,
[data-testid="stDownloadButton"] button {
    border-radius: 11px !important;

    border: 1px solid #4b8797 !important;

    background:
        linear-gradient(
            110deg,
            #164051,
            #213754
        ) !important;

    color: #e9fbff !important;

    font-weight: 700 !important;

    transition:
        transform .18s,
        box-shadow .18s,
        filter .18s !important;
}

[data-testid="stButton"] button:hover,
[data-testid="stDownloadButton"] button:hover {
    transform: translateY(-2px);

    filter: brightness(1.15);

    box-shadow:
        0 8px 25px #32d4c633;
}

[data-testid="stButton"] button:active,
[data-testid="stDownloadButton"] button:active {
    transform: scale(.975);
}


/* TABLES AND NAVIGATION */

[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

[data-testid="stTabs"] [data-baseweb="tab"] {
    font-weight: 700;
}


/* MOBILE */

@media(max-width:640px) {

    .hero {
        padding: 23px 20px;
    }

    .rate-card {
        padding: 20px;
    }

    .rate-card .big {
        font-size: 40px;
    }
}


/* ACCESSIBILITY */

@media(prefers-reduced-motion:reduce) {

    *,
    *:before,
    *:after {
        animation: none !important;
        transition: none !important;
    }
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# DATA RETRIEVAL
# ============================================================

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 "
        "(X11; Linux x86_64) "
        "AppleWebKit/537.36 "
        "Chrome/124.0 Safari/537.36"
    )
}


def downloaded_at():

    return datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def get(url, timeout=25, headers=None):

    response = requests.get(
        url,
        headers=headers or HEADERS,
        timeout=(7, timeout),
    )

    response.raise_for_status()

    return response


def source(
    value,
    url,
    date="Date unavailable",
    error=None,
):

    return {
        "value": value,
        "url": url,
        "date": date,
        "retrieved": downloaded_at(),
        "error": error,
    }


def analysis_date(html):

    text = BeautifulSoup(
        html,
        "html.parser",
    ).get_text(
        " ",
        strip=True,
    )

    match = re.search(
        r"Date of Analysis:\s*"
        r"Data used is as of\s*"
        r"([A-Za-z]+\s+\d{4})",
        text,
        re.I,
    )

    return (
        match.group(1)
        if match
        else "Date unavailable"
    )


# ============================================================
# INDUSTRY UNLEVERED BETAS
# ============================================================

def read_beta_table(frame):

    frame = frame.copy()

    frame.columns = [
        " ".join(str(c).split())
        for c in frame.columns
    ]

    names = {
        c.casefold(): c
        for c in frame.columns
    }

    if (
        "industry name" not in names
        or "unlevered beta" not in names
    ):

        raise ValueError(
            "Industry or unlevered beta "
            "column not found"
        )

    betas = {}

    for label, raw in zip(
        frame[names["industry name"]],
        frame[names["unlevered beta"]],
    ):

        label = " ".join(
            str(label).split()
        )

        value = pd.to_numeric(
            raw,
            errors="coerce",
        )

        if (
            label
            and label.lower()
            not in {
                "nan",
                "total market",
            }
            and not label.lower().startswith(
                "total market"
            )
            and pd.notna(value)
            and -5 < float(value) < 10
        ):

            betas[label] = float(value)

    if len(betas) < 25:

        raise ValueError(
            "Incomplete industry beta table"
        )

    return dict(
        sorted(betas.items())
    )


@st.cache_data(
    ttl=21600,
    show_spinner=False,
)
def fetch_betas():

    errors = []

    try:

        raw = pd.read_excel(
            BytesIO(
                get(BETAS_XLS).content
            ),
            header=None,
            engine="xlrd",
        )

        for row in range(
            min(50, len(raw))
        ):

            header = [
                " ".join(str(x).split())
                for x in raw.iloc[row]
            ]

            if {
                "industry name",
                "unlevered beta",
            }.issubset(
                {
                    x.casefold()
                    for x in header
                }
            ):

                table = raw.iloc[
                    row + 1:
                ].copy()

                table.columns = header

                betas = read_beta_table(
                    table
                )

                try:

                    date = analysis_date(
                        get(BETAS_HTML).text
                    )

                except requests.RequestException:

                    date = (
                        "Date unavailable"
                    )

                return source(
                    betas,
                    BETAS_XLS,
                    date,
                )

        raise ValueError(
            "Expected Excel headers missing"
        )

    except Exception as exc:

        errors.append(
            f"Excel: {exc}"
        )

    try:

        html = get(
            BETAS_HTML
        ).text

        for table in pd.read_html(
            StringIO(html)
        ):

            try:

                return source(
                    read_beta_table(table),
                    BETAS_HTML,
                    analysis_date(html),
                )

            except ValueError:

                continue

        raise ValueError(
            "Expected HTML table missing"
        )

    except Exception as exc:

        errors.append(
            f"HTML: {exc}"
        )

    return source(
        {},
        BETAS_XLS,
        "Unavailable",
        " | ".join(errors),
    )


# ============================================================
# BBB BORROWING SPREAD
# ============================================================

@st.cache_data(
    ttl=21600,
    show_spinner=False,
)
def fetch_bbb():

    try:

        html = get(
            BBB_URL
        ).text

        text = BeautifulSoup(
            html,
            "html.parser",
        ).get_text(
            " ",
            strip=True,
        )

        match = re.search(
            r"Baa2\s*/\s*BBB\s+"
            r"(\d+(?:\.\d+)?)\s*%",
            text,
            re.I,
        )

        if not match:

            raise ValueError(
                "Baa2/BBB large nonfinancial "
                "spread missing"
            )

        value = float(
            match.group(1)
        )

        if not 0 <= value <= 30:

            raise ValueError(
                "Unexpected spread"
            )

        return source(
            value,
            BBB_URL,
            analysis_date(html),
        )

    except Exception as exc:

        return source(
            None,
            BBB_URL,
            "Unavailable",
            str(exc),
        )


# ============================================================
# OECD CORPORATE TAX RATES
# ============================================================

@st.cache_data(
    ttl=43200,
    show_spinner=False,
)
def fetch_taxes():

    # Combined statutory corporate tax rate,
    # general government.

    url = (
        OECD_API
        + ".A.CIT_C.ST..S13..."
        + "?startPeriod=2024"
        + "&dimensionAtObservation=AllDimensions"
        + "&format=csvfilewithlabels"
    )

    try:

        response = get(
            url,
            timeout=40,
        )

        df = pd.read_csv(
            BytesIO(
                response.content
            ),
            low_memory=False,
        )

        df.columns = [
            str(c).strip()
            for c in df.columns
        ]

        required = {
            "REF_AREA",
            "TIME_PERIOD",
            "OBS_VALUE",
        }

        if not required.issubset(
            df.columns
        ):

            raise ValueError(
                "Unexpected OECD data columns"
            )

        for col, code in (
            ("MEASURE", "CIT_C"),
            ("TARGETING", "ST"),
            ("INSTITUTIONAL_SECTOR", "S13"),
        ):

            if col in df.columns:

                df = df.loc[
                    df[col]
                    .astype(str)
                    .str.strip()
                    == code
                ]

        df = df.copy()

        df["rate"] = pd.to_numeric(
            df["OBS_VALUE"],
            errors="coerce",
        )

        df["year"] = pd.to_numeric(
            df["TIME_PERIOD"],
            errors="coerce",
        )

        df = df.loc[
            df["rate"].between(0, 100)
            & df["year"].between(
                2024,
                2100,
            )
        ]

        valid_codes = {
            v[0]
            for v in COUNTRIES.values()
        }

        rates = {}

        for code, group in df.groupby(
            "REF_AREA"
        ):

            code = str(
                code
            ).strip().upper()

            if code not in valid_codes:

                continue

            newest = group.loc[
                group["year"]
                == group["year"].max()
            ]

            distinct = (
                newest["rate"]
                .round(8)
                .unique()
            )

            if len(distinct) == 1:

                rates[code] = (
                    float(distinct[0]),
                    str(
                        int(
                            newest["year"].iloc[0]
                        )
                    ),
                )

        if (
            "USA" not in rates
            or len(rates) < 15
        ):

            raise ValueError(
                f"Only {len(rates)} tax rates verified; "
                "check OECD response"
            )

        return source(
            rates,
            url,
            "Latest year for each country",
        )

    except Exception as exc:

        return source(
            {},
            url,
            "Unavailable",
            str(exc),
        )


# ============================================================
# GOVERNMENT BOND YIELDS
# ============================================================

@st.cache_data(
    ttl=900,
    show_spinner=False,
)
def fetch_yield(slug):

    url = (
        "https://tradingeconomics.com/"
        f"{slug}/government-bond-yield"
    )

    try:

        soup = BeautifulSoup(
            get(url).text,
            "html.parser",
        )

        h1 = soup.find(
            "h1"
        )

        if (
            not h1
            or not re.search(
                r"10\s*[- ]?\s*Year",
                h1.get_text(
                    " ",
                    strip=True,
                ),
                re.I,
            )
        ):

            raise ValueError(
                "10-year bond title missing"
            )

        text = soup.get_text(
            " ",
            strip=True,
        )

        pos = text.find(
            h1.get_text(
                " ",
                strip=True,
            )
        )

        match = re.search(
            r"\bActual\s+"
            r"(-?\d+(?:\.\d+)?)\b",
            text[pos:pos + 450],
            re.I,
        )

        if not match:

            raise ValueError(
                "Actual yield not found "
                "(forecasts are not used)"
            )

        yield_pct = float(
            match.group(1)
        )

        if not -25 < yield_pct < 100:

            raise ValueError(
                "Yield outside supported range"
            )

        stamp = re.search(
            r"last updated on\s+"
            r"([A-Za-z]+\s+\d{1,2}"
            r"(?:\s+of)?\s+\d{4})",
            text,
            re.I,
        )

        date = (
            stamp.group(1)
            if stamp
            else "Observation date unavailable"
        )

        return source(
            yield_pct,
            url,
            date,
        )

    except Exception as exc:

        return source(
            None,
            url,
            "Unavailable",
            str(exc),
        )


# ============================================================
# FINANCIAL CALCULATIONS
# ============================================================

def calculate(
    beta_u,
    tax,
    erp,
    debt,
    usd_rf,
    local_rf,
    usd_spread,
    local_spread=None,
):
    """
    Return financing costs in USD and
    the selected country's currency.

    All rates are decimals.
    """

    if not (
        0 <= debt < 1
        and 0 <= tax <= 1
        and usd_rf > -1
        and local_rf > -1
    ):

        raise ValueError(
            "Invalid tax, debt share, "
            "or government yield"
        )

    # Debt-to-equity ratio.

    de = debt / (1 - debt)

    # Levered beta.

    beta_e = beta_u * (
        1 + (1 - tax) * de
    )

    # USD cost of equity.

    re_usd = (
        usd_rf
        + beta_e * erp
    )

    # USD cost of debt.

    rd_usd = (
        usd_rf
        + usd_spread
    )

    # USD WACC.

    wacc_usd = (
        (1 - debt) * re_usd
        + debt * rd_usd * (1 - tax)
    )

    # Currency conversion factor.

    factor = (
        (1 + local_rf)
        / (1 + usd_rf)
    )

    # Foreign-currency cost of equity.

    re_local = (
        (1 + re_usd) * factor
        - 1
    )

    # Foreign-currency borrowing spread.

    spread_auto = (
        usd_spread * factor
    )

    spread_used = (
        spread_auto
        if local_spread is None
        else local_spread
    )

    # Foreign-currency cost of debt.

    rd_local = (
        local_rf
        + spread_used
    )

    # Foreign-currency WACC.

    wacc_local = (
        (1 - debt) * re_local
        + debt * rd_local * (1 - tax)
    )

    return {
        "de": de,
        "beta_e": beta_e,
        "factor": factor,

        "re_usd": re_usd,
        "rd_usd": rd_usd,
        "after_usd": rd_usd * (1 - tax),
        "wacc_usd": wacc_usd,

        "re_local": re_local,
        "rd_local": rd_local,
        "after_local": rd_local * (1 - tax),
        "wacc_local": wacc_local,

        "spread_auto": spread_auto,
        "spread_used": spread_used,
    }


# ============================================================
# CALCULATION VERIFICATION
# ============================================================

def verification():

    base = calculate(
        .8, .35, .065, .3,
        .04, .12, .015,
    )

    same = calculate(
        .8, .35, .065, .3,
        .04, .04, .015,
    )

    zero = calculate(
        .8, .35, .065, 0,
        .04, .12, .015,
    )

    override = calculate(
        .8, .35, .065, .3,
        .04, .12, .015, .03,
    )

    def close(a, b):

        return abs(a - b) < 1e-12

    return {

        "USD cost of equity — 10.6486%":
            close(
                base["re_usd"],
                .1064857142857143,
            ),

        "USD WACC — 8.5265%":
            close(
                base["wacc_usd"],
                .085265,
            ),

        "COP cost of equity — 19.1600%":
            close(
                base["re_local"],
                .1916,
            ),

        "COP WACC — 16.0670%":
            close(
                base["wacc_local"],
                .16067,
            ),

        "Equal yields produce equal costs":
            all(
                close(
                    same[a],
                    same[b],
                )
                for a, b in (
                    ("re_usd", "re_local"),
                    ("rd_usd", "rd_local"),
                    ("wacc_usd", "wacc_local"),
                )
            ),

        "Zero debt makes WACC equal cost of equity":
            (
                close(
                    zero["wacc_usd"],
                    zero["re_usd"],
                )
                and close(
                    zero["wacc_local"],
                    zero["re_local"],
                )
            ),

        "Foreign spread override leaves USD unchanged":
            all(
                close(
                    base[k],
                    override[k],
                )
                for k in (
                    "re_usd",
                    "rd_usd",
                    "wacc_usd",
                )
            ),
    }


# ============================================================
# DISPLAY FUNCTIONS
# ============================================================

def percent(x):

    return f"{100 * x:,.4f}%"


def input_field(
    label,
    auto,
    key,
    minimum=0.0,
    maximum=100.0,
    step=0.1,
):

    override = st.toggle(
        "Override " + label,
        key="override_" + key,
    )

    if override or auto is None:

        if auto is None:

            st.caption(
                "Source unavailable — "
                "enter a verified value."
            )

        value = st.number_input(
            label,
            min_value=float(minimum),
            max_value=float(maximum),

            value=(
                float(auto)
                if auto is not None
                else None
            ),

            step=float(step),
            format="%.4f",
            key="manual_" + key,
        )

        return (
            value,
            (
                "Manual"
                if value is not None
                else "Missing"
            ),
        )

    st.caption(
        f"{label}: **{auto:.4f}** · Automatic"
    )

    return auto, "Automatic"


def result_card(
    country,
    currency,
    values,
    local=False,
):

    p = (
        "local"
        if local
        else "usd"
    )

    cls = (
        " local"
        if local
        else ""
    )

    st.markdown(
        f"""
<div class="rate-card{cls}">

    <div class="country">
        {escape(country)} · {escape(currency)}
    </div>

    <div class="big">
        {percent(values['wacc_' + p])}
    </div>

    <div class="caption">
        WEIGHTED AVERAGE COST OF CAPITAL
    </div>

    <div class="details">

        <div>
            <small>Cost of Equity</small>
            <strong>
                {percent(values['re_' + p])}
            </strong>
        </div>

        <div>
            <small>Pretax Cost of Debt</small>
            <strong>
                {percent(values['rd_' + p])}
            </strong>
        </div>

        <div>
            <small>After-Tax Cost of Debt</small>
            <strong>
                {percent(values['after_' + p])}
            </strong>
        </div>

        <div>
            <small>WACC</small>
            <strong>
                {percent(values['wacc_' + p])}
            </strong>
        </div>

    </div>

</div>
""",
        unsafe_allow_html=True,
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
<div class="hero">

    <h1>
        International Cost of Capital
    </h1>

    <p>
        Compare a project's cost of equity,
        debt, and WACC in USD and the selected
        country's currency.
    </p>

</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# REFRESH DATA
# ============================================================

refresh_col, caption_col = st.columns(
    [1, 4],
    vertical_alignment="center",
)

with refresh_col:

    if st.button(
        "↻ Refresh Data",
        use_container_width=True,
    ):

        fetch_betas.clear()
        fetch_bbb.clear()
        fetch_taxes.clear()
        fetch_yield.clear()

        st.session_state[
            "refreshed"
        ] = True

        st.rerun()


with caption_col:

    st.caption(
        "Inputs recalculate automatically. "
        "Refresh Data requests updated "
        "values from the sources."
    )


if st.session_state.pop(
    "refreshed",
    False,
):

    st.toast(
        "Data sources requested again."
    )


# ============================================================
# INITIAL DATA RETRIEVAL
# ============================================================

with st.spinner(
    "Retrieving industry betas, "
    "corporate taxes, and borrowing spreads…"
):

    betas_data = fetch_betas()
    bbb_data = fetch_bbb()
    tax_data = fetch_taxes()


beta_map = betas_data[
    "value"
]

industries = sorted(
    set(beta_map)
    | {DEFAULT_INDUSTRY}
)


# ============================================================
# PROJECT SETTINGS
# ============================================================

with st.sidebar:

    st.header(
        "Project Settings"
    )

    industry = st.selectbox(
        "Industry",
        industries,

        index=industries.index(
            DEFAULT_INDUSTRY
        ),
    )

    country = st.selectbox(
        "Target Country",
        list(COUNTRIES),
    )

    country_code, currency, bond_slug = (
        COUNTRIES[country]
    )

    tax_mode = st.segmented_control(
        "Corporate Tax Rate",
        [
            "U.S.",
            "Selected Country",
        ],
        default="U.S.",
    )

    erp_pct = st.number_input(
        "Equity Risk Premium (%)",

        min_value=0.0,
        max_value=50.0,

        value=6.5,
        step=.1,

        format="%.2f",
    )

    debt_pct = st.slider(
        "Target Debt Share (%)",

        min_value=0,
        max_value=99,

        value=30,
    )

    st.caption(
        "One corporate tax rate, equity risk "
        "premium, and debt share apply "
        "to both currencies."
    )


# ============================================================
# GOVERNMENT YIELD RETRIEVAL
# ============================================================

with st.spinner(
    "Retrieving 10-year government bond yields…"
):

    usd_bond = fetch_yield(
        "united-states"
    )

    local_bond = (
        usd_bond
        if country_code == "USA"
        else fetch_yield(bond_slug)
    )


# ============================================================
# MANUAL OVERRIDES
# ============================================================

with st.sidebar:

    with st.expander(
        "Manual Overrides",
        expanded=True,
    ):

        st.caption(
            "Enter rates in percent: "
            "4.25 means 4.25%."
        )

        beta, beta_status = input_field(
            "Unlevered Beta",

            beta_map.get(industry),

            "beta_" + industry,

            -5,
            10,
            .05,
        )

        tax_us, tax_us_status = input_field(
            "U.S. Corporate Tax Rate (%)",

            tax_data["value"].get(
                "USA",
                (None, None),
            )[0],

            "tax_USA",
        )

        if country_code == "USA":

            tax_local = tax_us

            tax_local_status = (
                "Same as U.S."
            )

        else:

            tax_local, tax_local_status = (
                input_field(
                    f"{country} Corporate Tax Rate (%)",

                    tax_data["value"].get(
                        country_code,
                        (None, None),
                    )[0],

                    "tax_" + country_code,
                )
            )

        spread, spread_status = input_field(
            "USD BBB Borrowing Spread (pp)",

            bbb_data["value"],

            "spread_usd",
        )

        rf_us, rf_us_status = input_field(
            "U.S. 10-Year Government Yield (%)",

            usd_bond["value"],

            "yield_USA",

            -25,
        )

        if country_code == "USA":

            rf_local = rf_us

            rf_local_status = (
                "Same as U.S."
            )

        else:

            rf_local, rf_local_status = (
                input_field(
                    f"{country} 10-Year Government Yield (%)",

                    local_bond["value"],

                    "yield_" + country_code,

                    -25,
                )
            )

        st.divider()

        manual_foreign_spread = st.toggle(
            "Override Foreign-Currency BBB Spread"
        )

        if (
            all(
                v is not None
                for v in (
                    spread,
                    rf_us,
                    rf_local,
                )
            )
            and float(rf_us) > -100
        ):

            calculated_spread = (
                float(spread)
                * (100 + float(rf_local))
                / (100 + float(rf_us))
            )

        else:

            calculated_spread = None

        if manual_foreign_spread:

            foreign_spread = st.number_input(
                "Foreign-Currency BBB Spread (pp)",

                min_value=0.0,
                max_value=100.0,

                value=calculated_spread,

                step=.1,
                format="%.4f",
            )

        else:

            foreign_spread = None

            if calculated_spread is not None:

                st.caption(
                    "Automatically calculated: "
                    f"**{calculated_spread:.4f} pp**"
                )

            else:

                st.caption(
                    "Awaiting yields and USD spread."
                )


# ============================================================
# INPUT VALIDATION
# ============================================================

tax = (
    tax_us
    if tax_mode == "U.S."
    else tax_local
)

inputs = {
    "Unlevered Beta": beta,

    "Corporate Tax Rate": tax,

    "USD BBB Borrowing Spread": spread,

    "U.S. 10-Year Government Yield": rf_us,

    "Selected-Country 10-Year Government Yield":
        rf_local,

    "Foreign-Currency BBB Spread": (
        foreign_spread
        if manual_foreign_spread
        else 0.0
    ),
}

missing = [
    name
    for name, value in inputs.items()
    if value is None
]


# ============================================================
# MISSING DATA
# ============================================================

if missing:

    st.warning(
        "Missing data: "
        + ", ".join(missing)
        + ". Enter the missing values "
        "in Manual Overrides."
    )

    with st.expander(
        "Data Source Errors",
        expanded=True,
    ):

        for name, item in (
            ("Industry betas", betas_data),
            ("BBB spread", bbb_data),
            ("Corporate tax rates", tax_data),
            ("U.S. government yield", usd_bond),
            (
                "Selected-country government yield",
                local_bond,
            ),
        ):

            st.write(
                f"**{name}:** "
                f"{item['error'] or 'Retrieved successfully'}"
            )

            st.caption(
                item["url"]
            )


# ============================================================
# MAIN RESULTS
# ============================================================

else:

    parameters = {
        "tax": float(tax) / 100,

        "erp": erp_pct / 100,

        "debt": debt_pct / 100,

        "usd_rf": float(rf_us) / 100,

        "local_rf": float(rf_local) / 100,

        "usd_spread": float(spread) / 100,

        "local_spread": (
            float(foreign_spread) / 100
            if manual_foreign_spread
            else None
        ),
    }

    result = calculate(
        beta_u=float(beta),
        **parameters,
    )

    st.markdown(
        '<div class="section-label">'
        'Cost of Capital Comparison'
        '</div>',

        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(
        2,
        gap="medium",
    )

    with c1:

        result_card(
            "United States",
            "USD",
            result,
        )

    with c2:

        result_card(
            country,
            currency,
            result,
            local=True,
        )

    st.markdown(
        f"""
<div class="chips">

    <div class="chip">
        Levered Beta
        <b>{result['beta_e']:.4f}</b>
    </div>

    <div class="chip">
        Debt / Equity
        <b>{result['de']:.4f}</b>
    </div>

    <div class="chip">
        Corporate Tax Rate
        <b>{float(tax):.2f}%</b>
    </div>

    <div class="chip">
        WACC Difference
        <b>
            {100 * (result['wacc_local'] - result['wacc_usd']):+.4f} pp
        </b>
    </div>

</div>
""",
        unsafe_allow_html=True,
    )

    st.caption(
        "Foreign-currency BBB borrowing spread: "
        f"{100 * result['spread_used']:.4f} pp "
        f"({'Manual' if manual_foreign_spread else 'Automatically calculated'})."
    )


    # ========================================================
    # NAVIGATION
    # ========================================================

    overview, industries_tab, methods, sources_tab = (
        st.tabs(
            [
                "Overview",
                "All-Industry Comparison",
                "Calculations and Assumptions",
                "Data Sources",
            ]
        )
    )


    # ========================================================
    # OVERVIEW
    # ========================================================

    with overview:

        st.subheader(
            "Cost of Equity, Debt, and WACC"
        )

        labels = [
            "Cost of Equity",
            "Pretax Cost of Debt",
            "After-Tax Cost of Debt",
            "WACC",
        ]

        fig = go.Figure()

        for title, keys, color in (

            (
                "USD",

                (
                    "re_usd",
                    "rd_usd",
                    "after_usd",
                    "wacc_usd",
                ),

                "#5de0d0",
            ),

            (
                currency + " · Selected Country",

                (
                    "re_local",
                    "rd_local",
                    "after_local",
                    "wacc_local",
                ),

                "#b49df6",
            ),
        ):

            fig.add_bar(
                name=title,

                x=labels,

                y=[
                    100 * result[k]
                    for k in keys
                ],

                marker_color=color,

                hovertemplate=(
                    "%{x}: %{y:.4f}%"
                    "<extra></extra>"
                ),
            )

        fig.update_layout(
            barmode="group",

            height=420,

            margin=dict(
                l=10,
                r=8,
                t=28,
                b=6,
            ),

            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",

            font=dict(
                color="#d5e3f4",
                family="DM Sans",
            ),

            yaxis=dict(
                title="Rate (%)",
                gridcolor="#2a3b53",
            ),

            xaxis=dict(
                showgrid=False,
            ),

            legend=dict(
                orientation="h",
                y=1.13,
                x=0,
            ),

            hovermode="x unified",
        )

        st.plotly_chart(
            fig,

            use_container_width=True,

            config={
                "displayModeBar": False,
            },
        )


        # ====================================================
        # RESULTS DOWNLOAD
        # ====================================================

        export = {
            "Industry": industry,

            "Target Country": country,

            "Currency": currency,

            "Unlevered Beta": beta,

            "Levered Beta": result["beta_e"],

            "Tax Jurisdiction": tax_mode,

            "Corporate Tax Rate (%)": tax,

            "Equity Risk Premium (%)": erp_pct,

            "Target Debt Share (%)": debt_pct,

            "U.S. 10-Year Yield (%)": rf_us,

            "Selected-Country 10-Year Yield (%)":
                rf_local,

            "USD BBB Spread (pp)": spread,

            "Foreign BBB Spread (pp)":
                100 * result["spread_used"],

            "Foreign Spread Source": (
                "Manual"
                if manual_foreign_spread
                else "Automatic"
            ),

            "USD Cost of Equity (%)":
                100 * result["re_usd"],

            "Foreign Cost of Equity (%)":
                100 * result["re_local"],

            "USD Pretax Cost of Debt (%)":
                100 * result["rd_usd"],

            "Foreign Pretax Cost of Debt (%)":
                100 * result["rd_local"],

            "USD After-Tax Cost of Debt (%)":
                100 * result["after_usd"],

            "Foreign After-Tax Cost of Debt (%)":
                100 * result["after_local"],

            "USD WACC (%)":
                100 * result["wacc_usd"],

            "Foreign WACC (%)":
                100 * result["wacc_local"],
        }

        st.download_button(
            "↓ Download Results",

            pd.DataFrame(
                [export]
            ).to_csv(
                index=False
            ),

            "international_cost_of_capital.csv",

            "text/csv",
        )


    # ========================================================
    # ALL-INDUSTRY COMPARISON
    # ========================================================

    with industries_tab:

        st.subheader(
            "All-Industry Comparison"
        )

        st.caption(
            "The same tax rate, equity risk premium, "
            "debt share, borrowing spread, and yields "
            "apply to every industry."
        )

        if not beta_map:

            st.info(
                "Industry data unavailable. "
                "Refresh Data to retry."
            )

        else:

            rows = []

            for name, original_beta in beta_map.items():

                row_beta = (
                    float(beta)
                    if (
                        name == industry
                        and beta_status == "Manual"
                    )
                    else original_beta
                )

                value = calculate(
                    beta_u=row_beta,
                    **parameters,
                )

                rows.append(
                    {
                        "Industry": name,

                        "Unlevered Beta": row_beta,

                        "Levered Beta":
                            value["beta_e"],

                        "USD Cost of Equity (%)":
                            100 * value["re_usd"],

                        "Foreign Cost of Equity (%)":
                            100 * value["re_local"],

                        "USD Cost of Debt (%)":
                            100 * value["rd_usd"],

                        "Foreign Cost of Debt (%)":
                            100 * value["rd_local"],

                        "USD WACC (%)":
                            100 * value["wacc_usd"],

                        "Foreign WACC (%)":
                            100 * value["wacc_local"],
                    }
                )

            table = pd.DataFrame(
                rows
            ).sort_values(
                "USD WACC (%)",
                ascending=False,
            )

            st.dataframe(
                table,

                hide_index=True,
                use_container_width=True,

                height=490,
            )

            st.download_button(
                "↓ Download Industry Comparison",

                table.to_csv(
                    index=False
                ),

                "international_cost_of_capital_industries.csv",

                "text/csv",
            )


    # ========================================================
    # CALCULATIONS AND ASSUMPTIONS
    # ========================================================

    with methods:

        st.subheader(
            "Calculations and Assumptions"
        )

        st.markdown(
            r"""

All interest rates, borrowing spreads, and the equity
risk premium in these formulas are decimals.

### Levered Beta

$$
\frac{D}{E}=\frac{d}{1-d}
$$

$$
\beta_E
=
\beta_U
\left[
1+(1-\tau)\frac{D}{E}
\right]
$$

### USD Cost of Equity, Cost of Debt, and WACC

$$
R_e=R_f+\beta_E\times ERP
$$

$$
R_d=R_f+s
$$

$$
WACC=(1-d)R_e+dR_d(1-\tau)
$$

### Selected-Country Currency

$$
F=\frac{1+R_f^*}{1+R_f}
$$

$$
R_e^*=(1+R_e)F-1
$$

$$
s^*=sF
$$

$$
R_d^*=R_f^*+s^*
$$

$$
WACC^*=(1-d)R_e^*+dR_d^*(1-\tau)
$$

If the foreign-currency BBB spread is manually
overridden, the entered value replaces the
automatically calculated spread in the foreign-currency
cost of debt and WACC only.

### Main Assumptions

- U.S. industry unlevered betas proxy for project risk
  relative to the U.S. stock market.
- Government bond yields proxy for currency-specific
  risk-free rates; they can also contain term, liquidity,
  and sovereign risk premia.
- No separate country equity risk premium is added.
- Debt beta is zero, and interest deductions
  are fully usable.
- The same corporate tax rate, equity risk premium,
  and target debt share apply to both currencies.
- Currency conversion uses relative purchasing power
  parity and equal-real-interest-rate approximations.

"""
        )

        st.subheader(
            "Calculation Verification"
        )

        if st.button(
            "Run Calculation Checks"
        ):

            checks = verification()

            for name, passed in checks.items():

                st.write(
                    ("✓ " if passed else "✕ ")
                    + name
                )

            if all(
                checks.values()
            ):

                st.success(
                    "All calculation checks passed."
                )

            else:

                st.error(
                    "A calculation check failed."
                )


    # ========================================================
    # DATA SOURCES
    # ========================================================

    with sources_tab:

        st.subheader(
            "Data Sources and Dates"
        )

        st.caption(
            "Publisher dates describe the data vintage. "
            "Retrieval timestamps indicate when this "
            "application accessed each source."
        )

        entries = [

            (
                "Unlevered Beta",
                "Damodaran",
                betas_data,
                betas_data["date"],
                beta_status,
            ),

            (
                "USD BBB Borrowing Spread",
                "Damodaran",
                bbb_data,
                bbb_data["date"],
                spread_status,
            ),

            (
                "U.S. Corporate Tax Rate",
                "OECD",
                tax_data,

                tax_data["value"].get(
                    "USA",
                    (None, "Unavailable"),
                )[1],

                tax_us_status,
            ),

            (
                f"{country} Corporate Tax Rate",
                "OECD",
                tax_data,

                tax_data["value"].get(
                    country_code,
                    (None, "Unavailable"),
                )[1],

                tax_local_status,
            ),

            (
                "U.S. 10-Year Government Yield",
                "Trading Economics",
                usd_bond,
                usd_bond["date"],
                rf_us_status,
            ),

            (
                f"{country} 10-Year Government Yield",
                "Trading Economics",
                local_bond,
                local_bond["date"],
                rf_local_status,
            ),
        ]

        sources_table = pd.DataFrame(
            [
                {
                    "Input": name,

                    "Source": provider,

                    "Source Date": vintage,

                    "Input Mode": status,

                    "Retrieved (UTC)":
                        item["retrieved"],

                    "URL": item["url"],
                }

                for (
                    name,
                    provider,
                    item,
                    vintage,
                    status,
                ) in entries
            ]
        )

        st.dataframe(
            sources_table,

            use_container_width=True,
            hide_index=True,
        )

        st.caption(
            "Foreign BBB spread: "
            + (
                "Manual override"
                if manual_foreign_spread
                else (
                    "Calculated from the two "
                    "government yields and USD BBB spread"
                )
            )
        )

        st.markdown(
            f"[Industry Betas]({BETAS_XLS})"
            " · "
            f"[BBB Borrowing Spread]({BBB_URL})"
            " · "
            f"[OECD Corporate Tax Rates]({OECD_URL})"
            " · "
            f"[Government Bond Yields]({BONDS_URL})"
        )

        for name, item in (
            ("Industry betas", betas_data),
            ("BBB spread", bbb_data),
            ("Corporate tax rates", tax_data),
            ("U.S. government yield", usd_bond),
            (
                "Selected-country government yield",
                local_bond,
            ),
        ):

            if item["error"]:

                st.warning(
                    f"{name}: {item['error']}"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
<div style="
    margin-top:35px;
    padding-top:17px;

    border-top:1px solid #2c415a;

    color:#8fa6c3;
    font-size:12px;
">

International Cost of Capital

&nbsp; · &nbsp;

Full-precision calculations;
displayed rates are rounded.

</div>
""",
    unsafe_allow_html=True,
)
