# International Cost of Capital

An interactive Streamlit application that compares a project's cost of equity, cost of debt, and weighted average cost of capital (WACC) in U.S. dollars and a selected country's currency.

The application combines industry risk, corporate tax rates, government bond yields, and borrowing spreads to estimate financing costs across currencies.

## Features

- Select an industry and target country.
- Retrieve U.S. industry unlevered betas from Aswath Damodaran.
- Retrieve corporate tax rates from OECD data.
- Retrieve the USD BBB borrowing spread from Aswath Damodaran.
- Retrieve 10-year government bond yields from Trading Economics.
- Adjust the equity risk premium and target debt share.
- Switch between the U.S. and selected-country corporate tax rates.
- Manually override retrieved financial inputs.
- Automatically calculate the foreign-currency BBB borrowing spread or enter a manual override.
- Compare cost of equity, pretax cost of debt, after-tax cost of debt, and WACC side by side.
- View an all-industry comparison.
- Download results as CSV files.
- Review calculation formulas, assumptions, data sources, and dates.
- Refresh retrieved data.

## Default Settings

| Parameter | Default |
|---|---|
| Industry | Software (System & Application) |
| Target Country | United States |
| Corporate Tax Rate | U.S. |
| Equity Risk Premium | 6.5% |
| Target Debt Share | 30% |

Market data are retrieved from their respective sources when available.

## Calculation Methodology

The application uses consistent financing assumptions across both currencies.

### Levered Beta

`D/E = d / (1 - d)`

`Levered Beta = Unlevered Beta × [1 + (1 - Tax Rate) × D/E]`

### USD Cost of Capital

`Cost of Equity = U.S. Government Yield + Levered Beta × Equity Risk Premium`

`Cost of Debt = U.S. Government Yield + USD BBB Borrowing Spread`

`WACC = (1 - Debt Share) × Cost of Equity + Debt Share × Cost of Debt × (1 - Tax Rate)`

### Foreign-Currency Cost of Capital

The currency conversion factor is:

`F = (1 + Foreign Government Yield) / (1 + U.S. Government Yield)`

The foreign-currency cost of equity is:

`Foreign Cost of Equity = (1 + USD Cost of Equity) × F - 1`

The automatic foreign-currency borrowing spread is:

`Foreign BBB Spread = USD BBB Spread × F`

The foreign-currency borrowing cost is:

`Foreign Cost of Debt = Foreign Government Yield + Foreign BBB Spread`

The foreign-currency WACC is:

`Foreign WACC = (1 - Debt Share) × Foreign Cost of Equity + Debt Share × Foreign Cost of Debt × (1 - Tax Rate)`

All calculations retain full precision. Displayed percentages are rounded.

## Data Sources

**Aswath Damodaran**

U.S. industry unlevered betas:

https://pages.stern.nyu.edu/~adamodar/pc/datasets/betas.xls

BBB borrowing spreads:

https://pages.stern.nyu.edu/adamodar/New_Home_Page/datafile/ratings.html

**OECD**

Corporate Tax Statistics:

https://www.oecd.org/en/topics/sub-issues/corporate-taxation/corporate-tax-statistics.html

**Trading Economics**

10-year government bond yields:

https://tradingeconomics.com/bonds

## Assumptions

The model uses U.S. industry betas as proxies for project risk relative to the U.S. stock market.

Government bond yields serve as currency-specific risk-free rate proxies, although these yields can contain additional risk premia.

No separate country equity risk premium is included.

Debt beta is assumed to be zero, and interest tax deductions are assumed to be fully usable.

The same corporate tax rate, equity risk premium, and target debt share apply to both currencies.

Currency conversion relies on relative purchasing power parity and equal-real-interest-rate approximations.

## Data Availability

External data availability depends on the published datasets and accessibility of their websites.

If automatic retrieval fails, users can enter verified values using Manual Overrides.

The application identifies unavailable data rather than silently replacing them with assumed market values.

Some countries may not have corporate tax or government bond yield data available from the specified sources.

## Calculation Verification

The application includes automated checks for:

- A fixed illustrative financing scenario.
- Equality of results when government yields are identical.
- WACC equaling the cost of equity when the debt share is zero.
- Independence of USD calculations from manual foreign-currency borrowing spread overrides.

## Running the Application

Install the required Python packages:

`pip install -r requirements.txt`

Run the Streamlit application:

`streamlit run app.py`

## Project Files

- `app.py` — Application interface, data retrieval, and financial calculations.
- `requirements.txt` — Python dependencies.
- `README.md` — Application documentation.
