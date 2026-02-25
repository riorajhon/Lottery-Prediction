# Lottery Prediction System — Web App Spec

Define stack, main pages, and wireframes so the **UI can be built first** with no backend logic. Backend and functions come later.

---

## 1. Stack

| Layer | Choice | Notes |
|-------|--------|--------|
| **Backend API** | **FastAPI** | Async, OpenAPI docs, good for scrapers + ML jobs; lighter than Django for API-only. |
| **Frontend** | **React** | Matches requirement; rich ecosystem for dashboards, FullCalendar, charts. |
| **Database** | PostgreSQL or MongoDB | Per requirement; decide when implementing. |
| **Hosting** | Cloud (e.g. Vercel/Netlify for React + separate API host) | Remote access as required. |

**UI phase:** React app only (static or dev server). API endpoints can be mocked or return empty/placeholder JSON so the UI can be wired to “shapes” of data.

---

## 2. Main Pages & Routes

| # | Route | Page | Purpose |
|---|--------|------|--------|
| 1 | `/` or `/dashboard` | Dashboard | Agenda/calendar, next draws, quick stats, shortcuts. |
| 2 | `/draws` | Draw results | List/filter draws by lottery and date; view numbers and jackpots. |
| 3 | `/predictions` | Predictions | Choose lottery, model, options → view “recommended numbers” (UI only for now). |
| 4 | `/wheeling` | Wheeling | Input numbers + wheel type → generated lines (UI only). |
| 5 | `/backtesting` | Backtesting | Select date range, model, wheel → run report → results (UI only). |
| 6 | `/betting` | Betting | Pending bets, balance, confirm screen, place bet flow (UI only). |
| 7 | `/betting/history` | Betting history | Past bets, receipts, filters. |
| 8 | `/data` | Data status | Scraper status, last update per lottery, logs (UI only). |
| 9 | `/settings` | Settings | User prefs, optional integrations (no credentials stored in UI). |

**Navigation:** Global sidebar or top nav with these sections: Dashboard, Draws, Predictions, Wheeling, Backtesting, Betting (+ History), Data, Settings.

---

## 3. Wireframes (Layout & Key Elements)

### 3.1 Dashboard (`/` or `/dashboard`)

```
+------------------------------------------------------------------+
| [Logo]  Lottery Prediction    Dashboard | Draws | Predictions | … |
+------------------------------------------------------------------+
|                                                                  |
|  +-------------------+  +-------------------+  +----------------+ |
|  | Next draws        |  | Data status       |  | Quick actions  | |
|  | Euromillones Fri  |  | Euromillones ✓    |  | [New predict]  | |
|  | La Primitiva Sat  |  | La Primitiva ✓    |  | [Open wheel]   | |
|  | El Gordo …        |  | El Gordo ✓        |  | [Backtest]     | |
|  +-------------------+  +-------------------+  +----------------+ |
|                                                                  |
|  +--------------------------------------------------------------+|
|  | AGENDA (FullCalendar-style)                                   ||
|  |        Mon    Tue    Wed    Thu    Fri    Sat    Sun          ||
|  | Week 8  [Euromillones] [La Primitiva] ...                     ||
|  | Week 9  [El Gordo] [Euromillones] ...                         ||
|  | (Click day → draw detail or “Add prediction”)                 ||
|  +--------------------------------------------------------------+|
|                                                                  |
|  +------------------+  +----------------------------------------+|
|  | Recent results   |  | Last predictions / Last backtest summary||
|  | (last 3 draws)   |  | (placeholder cards)                     ||
|  +------------------+  +----------------------------------------+|
+------------------------------------------------------------------+
```

**Elements:** App bar with nav, “Next draws” card, “Data status” card, “Quick actions” buttons, agenda (month/week view, draw badges), “Recent results” and “Last predictions/backtest” placeholder sections.

---

### 3.2 Draw results (`/draws`)

```
+------------------------------------------------------------------+
| [Nav]  Draw results                                              |
+------------------------------------------------------------------+
| Lottery [Euromillones v]  From [date] To [date]  [Apply] [Export] |
+------------------------------------------------------------------+
| Date         | Lottery      | Main numbers      | Stars/Bonus | Jackpot  |
|--------------|--------------|-------------------|-------------|----------|
| 21 Feb 2025  | Euromillones | 12 18 23 31 42    | 2 7         | €45M     |
| 18 Feb 2025  | La Primitiva | 3 9 15 22 28 41   | 8           | €2.1M    |
| ...          | ...          | ...               | ...         | ...      |
+------------------------------------------------------------------+
| Pagination: [<] 1 2 3 ... 10 [>]                                 |
+------------------------------------------------------------------+
```

**Elements:** Filters (lottery dropdown, date range), table with columns as above, pagination. Row click → optional detail drawer/modal (same info + optional “Use for prediction”).

---

### 3.3 Predictions (`/predictions`)

```
+------------------------------------------------------------------+
| [Nav]  Predictions                                               |
+------------------------------------------------------------------+
| Lottery [Euromillones v]                                         |
| Model  [Random Forest v]  [LSTM] [Genetic] [Bayesian]            |
| Options: [x] Hot/cold filter  [ ] Use last N draws: [52]          |
+------------------------------------------------------------------+
| [Generate prediction]  (disabled or loading state for now)       |
+------------------------------------------------------------------+
| Result (placeholder):                                             |
| +----------------------------------------------------------------+|
| | Recommended numbers:  --  --  --  --  --  (stars: -- --)       ||
| | Or: "Select lottery and model, then generate (backend later)"  ||
| +----------------------------------------------------------------+|
| [Copy] [Send to Wheeling]                                         |
+------------------------------------------------------------------+
```

**Elements:** Lottery and model selectors, optional checkboxes/inputs (hot-cold, last N draws), “Generate” button, result area (placeholder text/empty state), “Copy” and “Send to Wheeling” actions.

---

### 3.4 Wheeling (`/wheeling`)

```
+------------------------------------------------------------------+
| [Nav]  Wheeling                                                  |
+------------------------------------------------------------------+
| Lottery [Euromillones v]                                         |
| Wheel type [Abbreviated wheel v]  (Full / Abbreviated / Balanced /|
|                                    Key number / Random / Guarantee)|
| Numbers source: ( ) Manual  (•) From last prediction             |
| Manual input: [ 1 5 12 18 23 31 42 7 9 ]  (if Manual)            |
| Key numbers (if Key number wheel): [ 7 9 ]                       |
+------------------------------------------------------------------+
| [Generate lines]                                                 |
+------------------------------------------------------------------+
| Generated lines (placeholder):                                    |
| Line 1:  -- -- -- -- --  (-- --)                                 |
| Line 2:  -- -- -- -- --  (-- --)                                 |
| ... (or table)                                                   |
| Summary: X lines, estimated cost €Y                               |
| [Copy all] [Export CSV] [Send to Betting]                         |
+------------------------------------------------------------------+
```

**Elements:** Lottery, wheel-type dropdown, numbers source (manual vs from prediction), key numbers if applicable, “Generate lines” button, list/table of lines, summary, actions (Copy, Export, Send to Betting).

---

### 3.5 Backtesting (`/backtesting`)

```
+------------------------------------------------------------------+
| [Nav]  Backtesting                                              |
+------------------------------------------------------------------+
| Lottery [Euromillones v]                                         |
| Model [Random Forest v]   Wheel [Abbreviated v]                  |
| From [date] To [date]                                            |
| [Run backtest]  (long-running; show “Simulation” state later)     |
+------------------------------------------------------------------+
| Report (placeholder):                                             |
| +----------------------------------------------------------------+|
| | Summary: X draws, Y tickets total, Z wins, ROI %                ||
| | Hit rate: 5+2: n%, 5+1: n%, ...                                 ||
| | Chart: (placeholder for P&L over time or hit distribution)     ||
| | Table: per-draw results (optional, collapsible)                 ||
| +----------------------------------------------------------------+|
| [Export report]                                                   |
+------------------------------------------------------------------+
```

**Elements:** Lottery, model, wheel, date range, “Run backtest” button, report area (summary, hit rate, chart placeholder, optional table), “Export report”.

---

### 3.6 Betting (`/betting`)

```
+------------------------------------------------------------------+
| [Nav]  Betting                                                  |
+------------------------------------------------------------------+
| Balance: €---  (placeholder)   [Refresh]   [Login to official]   |
+------------------------------------------------------------------+
| Pending bets (from Wheeling or manual):                           |
| +----------------------------------------------------------------+|
| | [ ] Euromillones  Fri 28 Feb  Line 1: 1 5 12 18 23 (2 7)  €2.50 ||
| | [ ] Euromillones  Fri 28 Feb  Line 2: ...                      ||
| | [Select all] [Remove selected]                                   ||
| +----------------------------------------------------------------+|
| [Place selected bets]  → opens confirmation screen               |
+------------------------------------------------------------------+
| Confirmation (modal/drawer):                                      |
| "You are about to place 5 bets for €12.50. Confirm?"             |
| [Cancel] [Confirm and place]                                      |
+------------------------------------------------------------------+
| Recent: link to [Betting history]                                 |
+------------------------------------------------------------------+
```

**Elements:** Balance (placeholder), “Refresh” and “Login” buttons, list of pending bets with checkboxes, “Place selected bets”, confirmation modal (mandatory before submit), link to history.

---

### 3.7 Betting history (`/betting/history`)

```
+------------------------------------------------------------------+
| [Nav]  Betting history                                           |
+------------------------------------------------------------------+
| From [date] To [date]  Lottery [All v]  [Apply]                   |
+------------------------------------------------------------------+
| Date       | Lottery      | Numbers           | Amount | Receipt  |
|------------|--------------|-------------------|--------|----------|
| 21 Feb 25  | Euromillones | 12 18 23 31 42…   | €2.50  | [View]   |
| ...        | ...          | ...               | ...    | ...      |
+------------------------------------------------------------------+
| Pagination                                                       |
+------------------------------------------------------------------+
```

**Elements:** Date and lottery filters, table (date, lottery, numbers, amount, receipt link), pagination.

---

### 3.8 Data status (`/data`)

```
+------------------------------------------------------------------+
| [Nav]  Data status                                               |
+------------------------------------------------------------------+
| Last run: 2025-02-24 00:02  [Run now] (disabled in UI-only phase) |
+------------------------------------------------------------------+
| Lottery      | Last update  | Status   | Draws in DB | Actions   |
|--------------|--------------|----------|-------------|-----------|
| Euromillones | 24 Feb 00:05 | ✓ OK     | 1,234       | [Details] |
| La Primitiva | 24 Feb 00:06 | ✓ OK     | 2,100       | [Details] |
| El Gordo     | 23 Feb 00:04 | ✓ OK     | 890         | [Details] |
+------------------------------------------------------------------+
| Log (last 20 lines, placeholder):                                 |
| [2025-02-24 00:02] Job started                                   |
| [2025-02-24 00:05] Euromillones: 1 new draw saved                 |
| ...                                                               |
+------------------------------------------------------------------+
```

**Elements:** Last run time, “Run now” button, table (lottery, last update, status, count), optional log area.

---

### 3.9 Settings (`/settings`)

```
+------------------------------------------------------------------+
| [Nav]  Settings                                                  |
+------------------------------------------------------------------+
| Preferences                                                       |
| - Default lottery: [Euromillones v]                               |
| - Default wheel: [Abbreviated v]                                  |
| - Agenda view: [Month v]  Week | Month                            |
| - Language: [English v]                                           |
| [Save]                                                            |
|                                                                   |
| Integrations (placeholders; no credentials in UI)                 |
| - Official lottery login: "Configure in secure backend"           |
| - CAPTCHA handling: "Manual / External service" (info only)        |
+------------------------------------------------------------------+
```

**Elements:** Default lottery/wheel, agenda view, language, Save; integration placeholders with short explanatory text.

---

## 4. UI Conventions (For Build)

- **No backend calls yet:** Use mock data or empty states; buttons can be disabled or show “Coming soon” where needed.
- **Responsive:** Sidebar collapses to hamburger on small screens; tables scroll or cardify.
- **Accessibility:** Semantic HTML, labels, keyboard nav, focus states.
- **Theming:** Decide light/dark or system; use CSS variables for colors and spacing so theming is easy later.
- **Agenda:** Use a calendar component (e.g. FullCalendar) with events for “Euromillones”, “La Primitiva”, “El Gordo” so the dashboard matches the requirement.

---

## 5. Next Step

Implement the **React app** with the above routes and wireframes (static/mock). Add backend (FastAPI) and real logic in a later phase.
