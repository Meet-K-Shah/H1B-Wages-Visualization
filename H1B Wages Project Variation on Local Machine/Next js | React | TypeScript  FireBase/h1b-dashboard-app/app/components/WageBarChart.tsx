"use client";

import dynamic from "next/dynamic";
import type { ComponentType } from "react";

const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
}) as ComponentType<any>;


type WageBarChartProps = {
  levels: string[];
  wagesAnnual: number[];
  userSalaryAnnual: number;
};

export function WageBarChart({
  levels,
  wagesAnnual,
  userSalaryAnnual,
}: WageBarChartProps) {
  if (!levels.length || !wagesAnnual.length) return null;

  return (
    <div>
      <h2 className="mb-3 text-base font-semibold text-gray-900">
        Wage chart
      </h2>
      <div className="border border-gray-200 rounded bg-white">
        <Plot
          data={[
            {
              x: levels,
              y: wagesAnnual,
              type: "bar",
              name: "Prevailing wage",
              marker: {
                color: [
                  "rgb(56, 189, 248)", // L1 - blueish
                  "rgb(34, 197, 94)",  // L2 - greenish
                  "rgb(250, 204, 21)", // L3 - yellow‑orange
                  "rgb(248, 113, 113)", // L4 - orange‑red
                ],
              },
            },
            {
              x: [levels[0], levels[levels.length - 1]],
              y: [userSalaryAnnual, userSalaryAnnual],
              type: "scatter",
              mode: "lines",
              name: "Your salary",
              line: { color: "rgb(0, 0, 0)", width: 3, dash: "dash" },
              hoverinfo: "y+name",
            },
          ]}
          layout={{
            autosize: true,
            height: 360,
            paper_bgcolor: "rgba(255,255,255,1)",
            plot_bgcolor: "rgba(255,255,255,1)",
            font: { color: "#111827" },
            margin: { l: 60, r: 20, t: 40, b: 40 },
            xaxis: { title: "Wage Level" },
            yaxis: { title: "Annual wage (USD)" },
            legend: {
              orientation: "h",
              yanchor: "bottom",
              y: 1.02,
              xanchor: "right",
              x: 1,
            },
          }}
          config={{
            responsive: true,
            displaylogo: false,
          }}
          style={{ width: "100%", height: "100%" }}
        />
      </div>
    </div>
  );
}
