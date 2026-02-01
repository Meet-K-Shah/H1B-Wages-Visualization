import { NextResponse } from "next/server";
import { collection, getDocs, query, limit } from "firebase/firestore";
import { db } from "@/lib/firebaseClient";

export async function GET() {
  try {
    const colRef = collection(db, "h1bwages_data");
    const q = query(colRef, limit(5));
    const snapshot = await getDocs(q);

    const docs = snapshot.docs.map((doc) => ({
      id: doc.id,
      ...doc.data(),
    }));

    return NextResponse.json({ ok: true, count: docs.length, docs });
  } catch (error: any) {
    console.error("Firestore test error:", error);
    return NextResponse.json(
      { ok: false, error: error.message ?? "Unknown error" },
      { status: 500 }
    );
  }
}
