"""End-to-end smoke test of the full Sahayak flow using the FastAPI TestClient.

Runs the demo personas through capture → consistency → eligibility → fill →
teach-back → consent → PDF, asserting the differentiated features actually fire.
"""
from fastapi.testclient import TestClient

from app.db import init_db
from app.main import app

init_db()
c = TestClient(app)


def banner(t):
    print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)


def run_persona(persona, expect_surprise=False, expect_mismatch=False):
    banner(f"PERSONA: {persona}")
    lang = "en"
    sid = c.post("/api/session", json={"language": lang}).json()["id"]
    print("session:", sid)

    cap = c.post(f"/api/session/{sid}/capture", json={"persona": persona}).json()
    print("captured docs:", [d["type"] for d in cap["documents"]])
    print("mismatches:", [(m["field"], [v["value"] for v in m["values"]]) for m in cap["mismatches"]])
    if expect_mismatch:
        assert cap["mismatches"], "expected a consistency mismatch!"
        # resolve to the first value
        field = cap["mismatches"][0]["field"]
        chosen = cap["mismatches"][0]["values"][0]["value"]
        c.post(f"/api/session/{sid}/resolve", json={"resolutions": {field: chosen}})
        print(f"resolved {field} -> {chosen}")

    elig = c.get(f"/api/session/{sid}/eligibility").json()
    print("QUALIFIES:", [(r["scheme_id"], r["why"]) for r in elig["qualifies"]])
    print("NEEDS PREREQ:", [(r["scheme_id"]) for r in elig["needs_prerequisite"]])
    print("SURPRISES (didn't ask, qualifies):", [r["scheme_id"] for r in elig["surprises"]])
    print("DEPENDENCY CHAINS:",
          [(d["scheme_id"], [n["scheme_id"] for n in d["needs"]], d["needs_documents"])
           for d in elig["dependencies"]])
    if expect_surprise:
        assert elig["surprises"], "expected a discovery surprise!"

    # Pick a scheme to fill: prefer one we qualify for, else the asked scheme.
    target = elig["qualifies"][0]["scheme_id"] if elig["qualifies"] else \
        (elig["needs_prerequisite"][0]["scheme_id"] if elig["needs_prerequisite"] else None)
    if not target:
        print("nothing to fill; skipping")
        return
    sel = c.post(f"/api/session/{sid}/select-form", json={"scheme_id": target}).json()
    print(f"\nFILLING form '{sel['form_id']}' for scheme '{target}':")
    for f in sel["filled"]:
        mark = {"green": "✓", "amber": "?", "red": "!"}.get(f["tier"], " ")
        print(f"  [{mark}] {f['label']}: {f['value']}  ({f['source']})")
    print("MISSING (gap questions):", [(m["key"], m["question"]) for m in sel["missing"]])

    # Answer any missing required by voice.
    if sel["missing"]:
        answers = {m["key"]: _demo_answer(m["key"]) for m in sel["missing"]}
        c.post(f"/api/session/{sid}/answer", json={"answers": answers})
        sel = c.post(f"/api/session/{sid}/select-form", json={"scheme_id": target}).json()
        print("after answering, still missing:", [m["key"] for m in sel["missing"]])

    tb = c.get(f"/api/session/{sid}/teachback").json()
    print("\nTEACH-BACK script:\n ", tb["script"][:240], "...")

    out = c.post(f"/api/session/{sid}/consent", json={"confirmed": True, "method": "voice"}).json()
    print("\nPDF:", out["pdf_url"])
    print("CHECKLIST:", [f"{i['instruction']} {i['label']}" for i in out["checklist"]])
    print("WHERE:", out["output"]["submit_to"])
    print("FAIR PRICE:", out["output"]["fair_price"])
    assert out["pdf_url"], "no PDF produced!"

    # Verify the PDF is actually served and is a real PDF.
    pdf = c.get(out["pdf_url"])
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF", "PDF not served correctly"
    print(f"PDF served OK ({len(pdf.content)} bytes)")

    # Track: set a reference number.
    tr = c.post(f"/api/tracking/{out['tracking_id']}/reference",
                json={"reference_number": "ACK/2026/00123"}).json()
    print("TRACKING:", tr["status"], tr["reference_number"], "reminders:", tr["reminders"])


def _demo_answer(key):
    return {
        "citizenship": "indian", "mobile": "9876543210", "institution": "Govt PU College",
        "bpl": True, "bank_account": "0000xxxx0000", "ifsc": "SBIN0000001",
        "income": 140000, "household_income": 90000, "household_size": 4,
        "is_govt_employee": False, "is_income_tax_payer": False,
        "owns_cultivable_land": True, "no_existing_lpg": True, "marital_status": "widow",
    }.get(key, "NA")


if __name__ == "__main__":
    print("health:", c.get("/api/health").json())
    run_persona("ramesh", expect_surprise=True)
    run_persona("priya", expect_surprise=False)
    run_persona("priya_missing_certs")
    run_persona("imran", expect_mismatch=True)
    run_persona("lakshmi", expect_surprise=True)
    banner("ALL PERSONAS PASSED ✓")
