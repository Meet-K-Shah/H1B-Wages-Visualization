"use client";

import { useEffect, useMemo, useState } from "react";
import Select, { SingleValue } from "react-select";
import { WageBarChart } from "./components/WageBarChart";

type Option = { value: string; label: string };

type Occupation = {
  soc_code: string;
  job_title: string;
};

type TableRow = {
  level: string;
  annual_wage: number;
  hourly_wage: number;
  toReachAnnual: number;
  ratio: number;
  status: "below" | "meets" | "exceeds";
};

export default function Home() {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    setIsClient(true);
  }, []);

  const [states, setStates] = useState<Option[]>([]);
  const [counties, setCounties] = useState<Option[]>([]);
  const [occupations, setOccupations] = useState<Option[]>([]);

  const [selectedState, setSelectedState] = useState<Option | null>(null);
  const [selectedCounty, setSelectedCounty] = useState<Option | null>(null);
  const [selectedOccupation, setSelectedOccupation] =
    useState<Option | null>(null);

  const [loadingStates, setLoadingStates] = useState(false);
  const [loadingCounties, setLoadingCounties] = useState(false);
  const [loadingOccupations, setLoadingOccupations] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [salaryValue, setSalaryValue] = useState<string>("");
  const [salaryMode, setSalaryMode] = useState<"annual" | "hourly">("annual");
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);

  const [resultsTable, setResultsTable] = useState<TableRow[] | null>(null);
  const [chartLevels, setChartLevels] = useState<string[] | null>(null);
  const [chartWagesAnnual, setChartWagesAnnual] = useState<number[] | null>(
    null
  );
  const [chartUserSalaryAnnual, setChartUserSalaryAnnual] = useState<
    number | null
  >(null);

  // Fetch states and occupations on mount
  useEffect(() => {
    const fetchStates = async () => {
      try {
        setLoadingStates(true);
        const res = await fetch("/api/filters?type=states");
        const data = await res.json();
        if (!data.ok) throw new Error(data.error || "Failed to load states");
        const opts: Option[] = data.states.map((s: string) => ({
          value: s,
          label: s,
        }));
        setStates(opts);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoadingStates(false);
      }
    };

    const fetchOccupations = async () => {
      try {
        setLoadingOccupations(true);
        const res = await fetch("/api/filters?type=occupations");
        const data = await res.json();
        if (!data.ok) {
          throw new Error(data.error || "Failed to load occupations");
        }
        const opts: Option[] = data.occupations.map((o: Occupation) => ({
          value: o.soc_code,
          label: `${o.job_title} (${o.soc_code})`,
        }));
        setOccupations(opts);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoadingOccupations(false);
      }
    };

    fetchStates();
    fetchOccupations();
  }, []);

  // Fetch counties when state changes
  useEffect(() => {
    const fetchCounties = async () => {
      if (!selectedState) {
        setCounties([]);
        setSelectedCounty(null);
        return;
      }

      try {
        setLoadingCounties(true);
        const params = new URLSearchParams({
          type: "counties",
          state: selectedState.value,
        });
        const res = await fetch(`/api/filters?${params.toString()}`);
        const data = await res.json();
        if (!data.ok) {
          throw new Error(data.error || "Failed to load counties");
        }
        const opts: Option[] = data.counties.map((c: string) => ({
          value: c,
          label: c,
        }));
        setCounties(opts);
        setSelectedCounty(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoadingCounties(false);
      }
    };

    fetchCounties();
  }, [selectedState]);

  const handleAnalyze = async () => {
    setAnalyzeError(null);
    setResultsTable(null);
    setChartLevels(null);
    setChartWagesAnnual(null);
    setChartUserSalaryAnnual(null);

    if (!selectedState || !selectedCounty || !selectedOccupation) {
      setAnalyzeError("Please select state, county, and occupation.");
      return;
    }

    const numericSalary = Number(salaryValue);
    if (!numericSalary || Number.isNaN(numericSalary) || numericSalary <= 0) {
      setAnalyzeError("Please enter a valid salary value.");
      return;
    }

    try {
      setAnalyzeLoading(true);
      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          state: selectedState.value,
          county: selectedCounty.value,
          soc_code: selectedOccupation.value,
          salary_value: numericSalary,
          mode: salaryMode,
        }),
      });

      const data = await res.json();

      if (!res.ok || !data.ok) {
        throw new Error(data.error || "Analyze request failed");
      }

      setResultsTable(data.table as TableRow[]);
      setChartLevels(data.chart.levels as string[]);
      setChartWagesAnnual(data.chart.wagesAnnual as number[]);
      setChartUserSalaryAnnual(data.chart.userSalaryAnnual as number);
    } catch (err: any) {
      setAnalyzeError(err.message);
    } finally {
      setAnalyzeLoading(false);
    }
  };

  // Auto-analyze when filters + salary are valid (debounced)
  useEffect(() => {
    setAnalyzeError(null);

    const numericSalary = Number(salaryValue);
    const hasValidSalary =
      !!numericSalary && !Number.isNaN(numericSalary) && numericSalary > 0;

    const canAnalyze =
      selectedState && selectedCounty && selectedOccupation && hasValidSalary;

    if (!canAnalyze) {
      setResultsTable(null);
      setChartLevels(null);
      setChartWagesAnnual(null);
      setChartUserSalaryAnnual(null);
      return;
    }

    const timeout = setTimeout(() => {
      handleAnalyze();
    }, 400); // 400ms debounce

    return () => clearTimeout(timeout);
  }, [
    selectedState,
    selectedCounty,
    selectedOccupation,
    salaryValue,
    salaryMode,
  ]);

  const stateValue = useMemo(() => selectedState, [selectedState]);
  const countyValue = useMemo(() => selectedCounty, [selectedCounty]);
  const occupationValue = useMemo(
    () => selectedOccupation,
    [selectedOccupation]
  );

  const isCountyDisabled = !selectedState || loadingCounties;

  if (!isClient) {
    return (
      <main className="min-h-screen bg-white text-black">
        <div className="max-w-6xl mx-auto py-10 px-4">
          <h1 className="text-2xl font-semibold mb-6">H1B Wage Dashboard</h1>
          <p className="text-sm text-gray-500">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white text-black">
      <div className="max-w-6xl mx-auto py-10 px-4">
        <h1 className="text-2xl font-semibold mb-6">H1B Wage Dashboard</h1>

        {error && (
          <div className="mb-4 rounded bg-red-50 border border-red-400 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        {/* Filters row */}
        <div className="grid gap-4 md:grid-cols-4">
          {/* State */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-800">State</label>
            <Select
              className="text-black"
              classNamePrefix="react-select"
              options={states}
              value={stateValue}
              onChange={(option: SingleValue<Option>) =>
                setSelectedState(option ?? null)
              }
              isSearchable
              isLoading={loadingStates}
              placeholder="Select or search state..."
            />
          </div>

          {/* County */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-800">County</label>
            <Select
              className="text-black"
              classNamePrefix="react-select"
              options={counties}
              value={countyValue}
              onChange={(option: SingleValue<Option>) =>
                setSelectedCounty(option ?? null)
              }
              isSearchable
              isLoading={loadingCounties}
              isDisabled={isCountyDisabled}
              placeholder={
                selectedState
                  ? "Select or search county..."
                  : "Select state first"
              }
            />
          </div>

          {/* Occupation */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-800">
              Occupation
            </label>
            <Select
              className="text-black"
              classNamePrefix="react-select"
              options={occupations}
              value={occupationValue}
              onChange={(option: SingleValue<Option>) =>
                setSelectedOccupation(option ?? null)
              }
              isSearchable
              isLoading={loadingOccupations}
              placeholder="Search occupation..."
            />
          </div>

          {/* Salary */}
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-gray-800">Salary</label>
            <input
              type="number"
              className="rounded border border-gray-300 bg-white px-2 py-2 text-sm text-black"
              placeholder="Enter salary"
              value={salaryValue}
              onChange={(e) => setSalaryValue(e.target.value)}
            />
          </div>
        </div>

        {/* Mode + status */}
        <div className="mt-4 flex flex-col gap-3 md:flex-row md:items-end">
          <div className="flex flex-col gap-1 md:w-40">
            <label className="text-sm font-medium text-gray-800">Mode</label>
            <select
              className="rounded border border-gray-300 bg-white px-2 py-2 text-sm text-black"
              value={salaryMode}
              onChange={(e) =>
                setSalaryMode(
                  e.target.value === "hourly" ? "hourly" : "annual"
                )
              }
            >
              <option value="annual">Annual</option>
              <option value="hourly">Hourly</option>
            </select>
          </div>

          {analyzeLoading && (
            <div className="text-sm text-gray-500 md:ml-4">
              Updating comparison…
            </div>
          )}
        </div>

        {/* Analyze error */}
        {analyzeError && (
          <div className="mt-4 rounded bg-red-50 border border-red-400 px-3 py-2 text-sm text-red-700">
            {analyzeError}
          </div>
        )}

        {/* Summary + chart */}
        {resultsTable &&
          chartLevels &&
          chartWagesAnnual &&
          chartUserSalaryAnnual !== null && (
            <div className="mt-6 space-y-4">
              {/* Summary + table */}
              <div className="rounded border border-gray-200 bg-white p-4 shadow-sm">
                <h2 className="text-base font-semibold mb-2">
                  Selected Location &amp; Occupation
                </h2>
                <p className="mb-4 text-sm text-gray-700">
                  {selectedState?.label} / {selectedCounty?.label}{" "}
                  {selectedOccupation
                    ? `| ${selectedOccupation.label}`
                    : ""}
                </p>

                <div className="overflow-x-auto rounded border border-gray-200 bg-white">
                  <table className="min-w-full border-collapse text-sm">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          Level
                        </th>
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          Hourly
                        </th>
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          Annual
                        </th>
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          PW Ratio
                        </th>
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          To reach
                        </th>
                        <th className="px-3 py-2 text-left border-b border-gray-200">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {resultsTable.map((row) => {
                        const ratioPct = row.ratio * 100;
                        const isMeets = row.status === "meets";
                        const isExceeds = row.status === "exceeds";

                        const dotColor = isExceeds
                          ? "bg-emerald-500"
                          : isMeets
                          ? "bg-amber-400"
                          : "bg-red-500";

                        const needsExtra = row.status === "below";

                        return (
                          <tr key={row.level} className="odd:bg-gray-50">
                            <td className="px-3 py-2 border-b border-gray-200">
                              {row.level}
                            </td>
                            <td className="px-3 py-2 text-left border-b border-gray-200">
                              ${row.hourly_wage.toFixed(2)}
                            </td>
                            <td className="px-3 py-2 text-left border-b border-gray-200">
                              {row.annual_wage.toLocaleString(undefined, {
                                maximumFractionDigits: 0,
                              })}
                            </td>
                            <td className="px-3 py-2 text-left border-b border-gray-200">
                              {ratioPct.toFixed(1)}%
                            </td>
                            <td className="px-3 py-2 text-left border-b border-gray-200">
                              {needsExtra
                                ? `+$${row.toReachAnnual.toLocaleString(undefined, {
                                    maximumFractionDigits: 0,
                                  })}`
                                : "---"}
                            </td>
                            <td className="px-3 py-2 text-left border-b border-gray-200">
                              <span className="inline-flex items-center gap-2">
                                <span
                                  className={`inline-block h-3 w-3 rounded-full ${dotColor}`}
                                />
                                <span className="capitalize">
                                  {row.status}
                                </span>
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Bar chart */}
              <div className="rounded border border-gray-200 bg-white p-4 shadow-sm">
                <WageBarChart
                  levels={chartLevels}
                  wagesAnnual={chartWagesAnnual}
                  userSalaryAnnual={chartUserSalaryAnnual}
                />
              </div>
            </div>
          )}
      </div>
    </main>
  );
}
