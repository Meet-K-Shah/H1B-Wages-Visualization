import { NextRequest, NextResponse } from "next/server";
import { collection, getDocs, query, where } from "firebase/firestore";
import { db } from "@/lib/firebaseClient";

const COLLECTION_NAME = "h1bwages_data";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const type = searchParams.get("type");

  try {
    if (type === "states") {
      const colRef = collection(db, COLLECTION_NAME);
      const snapshot = await getDocs(colRef);

      const statesSet = new Set<string>();
      snapshot.forEach((doc) => {
        const data = doc.data() as { state?: string };
        if (data.state) statesSet.add(data.state);
      });

      const states = Array.from(statesSet).sort();
      return NextResponse.json({ ok: true, states });
    }

    if (type === "counties") {
      const state = searchParams.get("state");
      if (!state) {
        return NextResponse.json(
          { ok: false, error: "Missing 'state' parameter" },
          { status: 400 }
        );
      }

      const colRef = collection(db, COLLECTION_NAME);
      const qState = query(colRef, where("state", "==", state));
      const snapshot = await getDocs(qState);

      const countiesSet = new Set<string>();
      snapshot.forEach((doc) => {
        const data = doc.data() as { county?: string };
        if (data.county) countiesSet.add(data.county);
      });

      const counties = Array.from(countiesSet).sort();
      return NextResponse.json({ ok: true, state, counties });
    }

    if (type === "occupations") {
      const colRef = collection(db, COLLECTION_NAME);
      const snapshot = await getDocs(colRef);

      type Occupation = { soc_code: string; job_title: string };

      const keySet = new Set<string>();
      const occupations: Occupation[] = [];

      snapshot.forEach((doc) => {
        const data = doc.data() as Partial<Occupation>;
        if (!data.soc_code || !data.job_title) return;

        const key = `${data.soc_code}::${data.job_title}`;
        if (!keySet.has(key)) {
          keySet.add(key);
          occupations.push({
            soc_code: data.soc_code,
            job_title: data.job_title,
          });
        }
      });

      occupations.sort((a, b) =>
        a.job_title.localeCompare(b.job_title, "en", { sensitivity: "base" })
      );

      return NextResponse.json({ ok: true, occupations });
    }

    return NextResponse.json(
      { ok: false, error: "Invalid or missing type parameter" },
      { status: 400 }
    );
  } catch (error: any) {
    console.error("Filters API error:", error);
    return NextResponse.json(
      { ok: false, error: error.message ?? "Unknown error" },
      { status: 500 }
    );
  }
}
