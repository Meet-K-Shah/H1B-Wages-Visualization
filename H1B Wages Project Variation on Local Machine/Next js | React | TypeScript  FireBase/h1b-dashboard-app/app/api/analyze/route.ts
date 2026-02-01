import { NextRequest, NextResponse } from "next/server";
import { collection, getDocs, query, where, limit } from "firebase/firestore";
import { db } from "@/lib/firebaseClient";

const COLLECTION_NAME = "h1bwages_data";

// Helper to convert annual ↔ hourly
function toAnnual(salary: number, mode: "annual" | "hourly"): number {
  if (mode === "annual") return salary;
  // assuming 2080 hours/year
  return salary * 2080;
}

function toHourly(salaryAnnual: number): number {
  return salaryAnnual / 2080;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();

    const state = body.state as string | undefined;
    const county = body.county as string | undefined;
    const soc_code = body.soc_code as string | undefined;
    const salary_value = Number(body.salary_value);
    const mode = (body.mode as "annual" | "hourly") || "annual";

    if (!state || !county || !soc_code || !salary_value || isNaN(salary_value)) {
      return NextResponse.json(
        { ok: false, error: "Missing or invalid state, county, soc_code, or salary_value" },
        { status: 400 }
      );
    }

    const userSalaryAnnual = toAnnual(salary_value, mode);

    // Fetch matching Firestore document
    const colRef = collection(db, COLLECTION_NAME);
    const qDoc = query(
      colRef,
      where("state", "==", state),
      where("county", "==", county),
      where("soc_code", "==", soc_code),
      limit(1)
    );
    const snapshot = await getDocs(qDoc);

    if (snapshot.empty) {
      return NextResponse.json(
        {
          ok: false,
          error: "No matching wage record found for given filters",
        },
        { status: 404 }
      );
    }

    const doc = snapshot.docs[0];
    const data = doc.data() as {
      l1_wage: number;
      l2_wage: number;
      l3_wage: number;
      l4_wage: number;
      job_title?: string;
      state?: string;
      county?: string;
      soc_code?: string;
    };

    const levels = [
      { key: "L1", wageAnnual: data.l1_wage },
      { key: "L2", wageAnnual: data.l2_wage },
      { key: "L3", wageAnnual: data.l3_wage },
      { key: "L4", wageAnnual: data.l4_wage },
    ];

    const table = levels.map((lvl) => {
    const ratio = userSalaryAnnual / lvl.wageAnnual;
    let status: "below" | "meets" | "exceeds";

    if (ratio < 1) status = "below";
    else if (ratio >= 1 && ratio < 1.1) status = "meets";
    else status = "exceeds";

    const diffAnnual =
      status === "below" ? lvl.wageAnnual - userSalaryAnnual : 0;

    return {
      level: lvl.key,
      annual_wage: lvl.wageAnnual,
      hourly_wage: toHourly(lvl.wageAnnual),
      ratio,
      status,
      toReachAnnual: diffAnnual,
    };
  });


    const response = {
      ok: true,
      input: {
        state,
        county,
        soc_code,
        job_title: data.job_title ?? null,
        salary_value,
        mode,
        salary_annual: userSalaryAnnual,
        salary_hourly: toHourly(userSalaryAnnual),
      },
      wages: {
        l1: data.l1_wage,
        l2: data.l2_wage,
        l3: data.l3_wage,
        l4: data.l4_wage,
      },
      chart: {
        levels: ["L1", "L2", "L3", "L4"],
        wagesAnnual: levels.map((l) => l.wageAnnual),
        userSalaryAnnual,
      },
      table,
    };

    return NextResponse.json(response);
  } catch (error: any) {
    console.error("/api/analyze error:", error);
    return NextResponse.json(
      { ok: false, error: error.message ?? "Unknown error" },
      { status: 500 }
    );
  }
}
