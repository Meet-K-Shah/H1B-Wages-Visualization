# H1B Wage Intelligence Dashboard

Interactive web dashboard to explore H1B prevailing wage levels (L1–L4) by state, county, and occupation, and compare them against a user-entered salary.

Built with **Next.js (App Router) + React**, **TypeScript**, **Firebase Firestore**, **react-select**, and **react-plotly.js**. Deployed on **Vercel** with an optional custom domain.

---

## Features

- **Filter panel**
  - Searchable dropdowns for:
    - State
    - County (filtered by state)
    - Occupation (SOC code + job title)
  - Salary input (annual or hourly mode)
  - Analysis runs **automatically** (debounced) when all inputs are valid.

- **Wage comparison table**
  - Shows for levels **L1–L4**:
    - Hourly wage
    - Annual wage
    - PW Ratio (user salary ÷ prevailing wage, as a percentage)
    - Status badge:
      - `exceeds` (green dot)
      - `meets` (yellow dot)
      - `below` (red dot)
    - **To reach**: extra annual salary needed to reach that level; `---` if the user already meets or exceeds it.

- **Bar chart**
  - Plotly bar chart of annual wages for L1–L4.
  - Per-level colors:
    - L1 – bluish
    - L2 – greenish
    - L3 – yellow–orange
    - L4 – orange–red
  - Dashed horizontal line for the user’s annual salary.

- **Architecture**
  - Frontend + API routes in a single Next.js app.
  - Backend logic implemented as serverless API routes on Vercel.
  - Firestore used as a read-only data store for H1B wage data.

---

## Tech Stack

- **Frontend & Backend**
  - Next.js (App Router, TypeScript)
  - React
  - Tailwind CSS (utility classes for layout and styling)
  - react-select (searchable dropdowns)
  - react-plotly.js + plotly.js (charts, client-only via dynamic import)

- **Data Layer**
  - Firebase Cloud Firestore
  - Single collection (current implementation): `h1bwages_data`
    - Example fields per document:
      - `area_code: string`
      - `state: string` (e.g. `"Texas (TX)"`)
      - `county: string`
      - `soc_code: string`
      - `job_title: string`
      - `l1_wage: number` (annual)
      - `l2_wage: number`
      - `l3_wage: number`
      - `l4_wage: number`

- **Hosting**
  - Vercel for app hosting (Next.js project).
  - Optional custom domain pointing to the Vercel project.

---

## Project Structure

```text
app/
  page.tsx                # Main dashboard UI (filters, table, chart)
  api/
    filters/route.ts      # GET: states, counties, occupations
    analyze/route.ts      # POST: wage comparison logic (L1–L4 vs salary)
lib/
  firebaseClient.ts       # Firebase Web SDK client (Firestore)
public/
  # Static assets (if any)
react-plotly-js.d.ts      # Type shim for react-plotly.js
.env.local                # Firebase config (local only, not committed)


API Routes
GET /api/filters
Returns filter data from Firestore.

GET /api/filters?type=states

Response:

json
{ "ok": true, "states": ["Texas (TX)", "California (CA)", "..."] }
GET /api/filters?type=counties&state=STATE_LABEL

Response:

json
{
  "ok": true,
  "state": "Texas (TX)",
  "counties": ["Randall County", "..."]
}
GET /api/filters?type=occupations

Response:

json
{
  "ok": true,
  "occupations": [
    { "soc_code": "15-1252", "job_title": "Software Developers" }
  ]
}
POST /api/analyze
Compares a user-entered salary against the prevailing wages for a specific location + SOC.

Request body:

json
{
  "state": "Texas (TX)",
  "county": "Randall County",
  "soc_code": "13-2071",
  "salary_value": 90000,
  "mode": "annual"
}


Core logic:

Convert salary to annual if mode is "hourly" (using 2080 hours/year).

Query Firestore for the matching document: (state, county, soc_code).

For each level L1–L4:

Compute ratio = userAnnual / levelAnnual.

Determine status:

below if ratio < 1

meets if 1 ≤ ratio < 1.1

exceeds if ratio ≥ 1.1

Compute toReachAnnual = levelAnnual - userAnnual if status === "below", else 0.

Response (simplified):

json
{
  "ok": true,
  "input": {
    "state": "...",
    "county": "...",
    "soc_code": "...",
    "job_title": "...",
    "salary_value": 90000,
    "mode": "annual",
    "salary_annual": 90000,
    "salary_hourly": 43.27
  },
  "wages": { "l1": 60000, "l2": 80000, "l3": 100000, "l4": 120000 },
  "chart": {
    "levels": ["L1", "L2", "L3", "L4"],
    "wagesAnnual": ,
    "userSalaryAnnual": 90000
  },
  "table": [
    {
      "level": "L1",
      "annual_wage": 60000,
      "hourly_wage": 28.85,
      "ratio": 1.5,
      "status": "exceeds",
      "toReachAnnual": 0
    }
  ]
}
Firebase Setup
Create a Firebase project and Firestore database.

Create collection: h1bwages_data with the fields shown above.

Set Firestore security rules (public read, no writes):

js
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /h1bwages_data/{doc} {
      allow read: if true;
      allow write: if false;
    }

    match /{document=**} {
      allow read, write: if false;
    }
  }
}
In .env.local (not committed):

bash
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=...
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=...
NEXT_PUBLIC_FIREBASE_APP_ID=...
Local Development
Install dependencies:

bash
npm install
Run the dev server:

bash
npm run dev
Open the app:

http://localhost:3000

