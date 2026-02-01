# H1B Wage Dashboard - Complete Specification

## Project Overview
Interactive dashboard for analyzing H1B prevailing wages by location, occupation, and salary input. Users can compare their salary against prevailing wage levels (L1-L4) across the United States.

---

## 1. INPUT CONTROLS (Top Section)

### 1.1 State Dropdown
- **Label:** "State"
- **Type:** Dropdown (cascading)
- **Data Source:** Distinct states from Geography.csv
- **Behavior:** 
  - Load all distinct states alphabetically
  - On selection â†’ filter County dropdown

### 1.2 County Dropdown (Dependent)
- **Label:** "County"
- **Type:** Dropdown (cascading, dependent on State)
- **Data Source:** Counties from selected state
- **Behavior:**
  - Initially disabled until State selected
  - On State change â†’ repopulate with counties
  - Show only counties in selected state

### 1.3 Occupation Dropdown (Independent)
- **Label:** "Occupation"
- **Type:** Dropdown (independent of location)
- **Data Source:** Distinct SOC codes from oes_soc_occs.csv
- **Display Format:** "SOC Code - Job Title" (e.g., "15-1252 - Software Developers")
- **Behavior:** Can select any occupation regardless of State/County

### 1.4 Salary Input (Independent)
- **Label:** "Target Salary"
- **Type:** Number input with toggle for Annual/Hourly
- **Default Mode:** Annual
- **Toggle Options:**
  - ◉ Annual (default)
  - ○ Hourly
- **Behavior:**
  - If user switches Annual â†” Hourly â†’ auto-convert current value
  - Formula: Annual = Hourly Ã— 2080 (standard working hours/year)
  - Conversion: Hourly = Annual Ã· 2080
  - Format display: $X,XXX for Annual | $XX.XX/hr for Hourly
  - Optional input (can leave blank)

### 1.5 Analyze Button
- **Label:** "Analyze"
- **Type:** Primary button
- **Behavior:**
  - Validate that State, County, Occupation are selected
  - Trigger all output sections to update
  - If salary is blank â†’ show outputs without salary line/map coloring
  - If salary entered â†’ show all visualizations with salary comparison

### 1.6 Clear Button
- **Label:** "Clear"
- **Type:** Secondary button
- **Behavior:**
  - Reset all dropdowns to default
  - Clear salary input
  - Reset all output visualizations

---

## 2. OUTPUT SECTIONS

### 2.1 Annual Wage Levels Chart

**Location:** Below input controls (left side or full width)

**Chart Type:** Bar chart with horizontal line overlay

**Data Display:**
- 4 vertical bars for Level 1, Level 2, Level 3, Level 4
- X-axis: Level 1, Level 2, Level 3, Level 4
- Y-axis: Annual salary in thousands ($0 - $150k or higher if needed)
- Bar colors (gradient): 
  - Level 1: Green (#22c55e)
  - Level 2: Yellow/Gold (#eab308)
  - Level 3: Orange (#f97316)
  - Level 4: Red (#ef4444)

**Salary Line (Optional):**
- Horizontal dashed line at user salary amount
- Color: Red (#ef4444)
- Label: "Your Offer: $X,XXX" or "Your Offer: $XX.XX/hr"
- Only appears if salary entered
- If salary exceeds chart range â†’ extend Y-axis automatically

**Toggle Control:**
- Above chart: Annual/Hourly radio buttons
- Dynamically update chart values when toggled
- Auto-convert salary line if salary entered

**Interaction:**
- Hover over bars â†’ show exact values
- Hover over salary line â†’ show "Your Offer: $X,XXX"

**Responsive:**
- Full width on desktop
- Stack vertically on mobile

---

### 2.2 Geographic Heatmap (USA County-level Map)

**Location:** Right side of wage levels chart (or below on mobile)

**Map Type:** Interactive USA map with county-level coloring

**Data Logic:**
- Uses only: Selected Occupation + User Salary
- Ignores: Selected State/County (shows ALL counties)
- For each county in USA:
  - Look up prevailing wage levels for selected occupation
  - Determine which level user salary meets (Option A: Highest level met)
  - Assign color based on level

**Color Mapping (Discrete Levels):**
- 🟪 Level 0 (Gray #9ca3af): User salary BELOW Level 1 (not competitive)
- 🟢 Level 1 (Green #22c55e): User salary MEETS Level 1
- 🟡 Level 2 (Yellow #eab308): User salary MEETS Level 2
- 🟠 Level 3 (Orange #f97316): User salary MEETS Level 3
- 🔴 Level 4 (Red #ef4444): User salary MEETS Level 4

**Interactivity:**
- **Hover over county:** Show tooltip with:
  - County name, State
  - User salary: $X,XXX
  - L1 prevailing wage for occupation: $X,XXX
  - Your level: Level 0-4
  - Match percentage: XX%
  - Status: "Meets Level X" or "Below Level 1"

- **Click on county:** 
  - Show detailed view with all occupations available in that county
  - Display wage ranges for each occupation
  - Allow drill-down analysis

**Update Behavior:**
- Real-time updates (Option A: Instant)
- Map colors change immediately when user adjusts salary
- No need to click "Analyze" button for map updates
- If salary blank â†’ map shows all counties in Level 0 (gray)

**Technical Details:**
- Use Plotly Choropleth or similar mapping library
- Geospatial data: County FIPS codes or lat/long boundaries
- Performance: Pre-calculate levels for all county-occupation combinations

---

### 2.3 Wage Details Table

**Location:** Below charts (full width)

**Table Structure:**

| Column | Description | Format |
|--------|-------------|--------|
| Level | Prevailing wage level | "L1", "L2", "L3", "L4" |
| Hourly | Hourly wage rate | "$XX.XX/hr" or "$XX.XX" |
| Annual | Annual salary equivalent | "$XXX,XXX" or "~$XXX,XXX" |
| PW Ratio | Prevailing wage ratio | "XX.XX%" |
| Status | Visual status + interpretation | "🟢 Meets" / "🟡 Close" / "🔴 Below" |

**Data Logic:**
- Fetch L1, L2, L3, L4 wages for selected: State, County, Occupation
- Calculate PW Ratio: (User Salary / Level Wage) × 100
- Assign status emoji:
  - 🟢 Green: User salary >= Level wage (100%+)
  - 🟡 Yellow: User salary between 95-99% of Level wage
  - 🔴 Red: User salary < 95% of Level wage

**Example:**
```
Level | Hourly  | Annual    | PW Ratio | Status
------|---------|-----------|----------|------------------
L1    | $42.81  | $89,045   | 95.46%   | 🟡 Below (Gap: $4k)
L2    | $51.43  | $106,974  | 79.46%   | 🔴 Below (Gap: $22k)
L3    | $60.06  | $124,925  | 68.04%   | 🔴 Below (Gap: $40k)
L4    | $68.68  | $142,854  | 59.50%   | 🔴 Below (Gap: $58k)
```

**Dynamic Updates:**
- Toggle Annual â†” Hourly â†’ table updates values automatically
- Change salary â†’ PW Ratio and Status columns update in real-time
- If no salary â†’ show gray rows or disable

**Sorting:** Fixed order (L1, L2, L3, L4)

**Mobile Responsiveness:** Horizontal scroll or card layout on small screens

---

## 3. LAYOUT STRUCTURE

### Desktop (1200px+)
```
┌─────────────────────────────────────────────────────────────┐
│ INPUT CONTROLS (State | County | Occupation | Salary)      │
│ [Analyze] [Clear]                                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────┬──────────────────────────────────┐
│ ANNUAL WAGE LEVELS       │ GEOGRAPHIC HEATMAP               │
│ (Bar Chart with line)    │ (USA County-level Map)           │
│                          │                                  │
│ [Annual/Hourly Toggle]   │ Interactive coloring             │
└──────────────────────────┴──────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ WAGE DETAILS TABLE                                          │
│ Level | Hourly | Annual | PW Ratio | Status                │
│ L1    | ...    | ...    | ...      | ...                   │
│ L2    | ...    | ...    | ...      | ...                   │
│ L3    | ...    | ...    | ...      | ...                   │
│ L4    | ...    | ...    | ...      | ...                   │
└─────────────────────────────────────────────────────────────┘
```

### Tablet (768px - 1199px)
```
Stack charts vertically
Map below wage chart
Table full width below
```

### Mobile (< 768px)
```
Single column layout
All sections stack vertically
Smaller fonts, touch-friendly buttons
Map uses mobile-friendly rendering
```

---

## 4. DATA SOURCES & PROCESSING

### Files Used:
1. **ALC_Export.csv** - Wage levels by Area, SOC code, and Level (1-4)
2. **Geography.csv** - Area codes mapped to State and County
3. **oes_soc_occs.csv** - SOC codes mapped to job titles/descriptions

### Data Merging:
- Merge Geography with ALC using Area code
- Merge with oes_soc_occs using SOC code
- Result: Complete dataset with State, County, Occupation, L1-L4 wages

### Calculations:
- PW Ratio = (User Salary / Level Wage) Ã— 100
- Hourly = Annual Ã· 2080
- Annual = Hourly Ã— 2080
- Level Assignment (Option A): User meets highest level where salary >= level wage

---

## 5. USER INTERACTIONS & FLOWS

### Flow 1: Basic Analysis
1. User selects State, County, Occupation
2. Enters salary ($85,000 annual)
3. Clicks "Analyze"
4. âœ… Chart shows bars + salary line
5. âœ… Map colors update based on occupation + salary
6. âœ… Table shows L1-L4 comparisons

### Flow 2: Real-time Map Updates
1. User changes salary from $85k â†’ $100k
2. âœ… Map colors update IMMEDIATELY (no button needed)
3. Wage chart line moves
4. Table updates PW Ratios

### Flow 3: Annual â†” Hourly Toggle
1. User has $85,000 annual entered
2. Clicks "Hourly" radio button
3. âœ… Input auto-converts to $40.87/hr
4. âœ… Chart updates to hourly scale
5. âœ… Table updates hourly column
6. User can edit hourly value
7. Clicks "Annual" â†’ converts back

### Flow 4: Blank Salary
1. User selects State, County, Occupation
2. Leaves salary blank
3. Clicks "Analyze"
4. âœ… Chart shows 4 bars (no salary line)
5. âœ… Map shows all counties in gray (Level 0)
6. âœ… Table shows standard L1-L4 rates (no PW Ratio)

### Flow 5: Clear All
1. User clicks "Clear" button
2. âœ… All dropdowns reset
3. âœ… Salary field clears
4. âœ… All visualizations reset to default/empty state

---

## 6. TECHNICAL STACK (Recommendations)

### Framework: **Dash + Plotly** (Python)
- **Why:** 
  - Excellent for interactive dashboards
  - Built-in callbacks for real-time updates
  - Great map support via Plotly Choropleth
  - Professional UI out of box

### Libraries:
- `dash` - Web framework
- `plotly` - Charting & maps
- `pandas` - Data processing
- `numpy` - Calculations

### Deployment Options:
- Heroku (free tier)
- Vercel
- AWS
- Streamlit Cloud (simpler alternative)

---

## 7. EDGE CASES & ERROR HANDLING

### Missing Data:
- If State has no counties â†’ show error message
- If Occupation has no data for county â†’ show "No data available"
- If salary calculation fails â†’ show placeholder

### User Inputs:
- Negative salary â†’ reject with error message
- Zero salary â†’ treat as blank
- Very large salary (>$1M) â†’ extend chart axis

### Map Rendering:
- County not found â†’ skip (gray background)
- No wage data for occupation-county pair â†’ Level 0 (gray)

---

## 8. Performance Considerations

- Pre-compute all Level assignments for all county-occupation combos
- Cache map GeoJSON data
- Lazy-load county details on click (not on hover)
- Debounce real-time map updates on slider (optional)
- Compress CSV files or use Parquet for faster loading

---

## 9. Future Enhancements

1. Historical trend analysis (wage changes over time)
2. Job market comparison (salary vs. market rates)
3. Export data to PDF/CSV
4. Save favorite locations for comparison
5. H1B approval prediction model
6. Mobile app version
7. Integration with job boards (LinkedIn, Indeed)
