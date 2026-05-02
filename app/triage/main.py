from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .crew import run_crew
from .schemas import QueryRequest
from .database import collection
from datetime import datetime
from bson import ObjectId
from typing import Optional


app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/triage")
def triage(req: QueryRequest):
    raw_result = run_crew(req.query)

    # ✅ FIX: direct dict usage (instead of tasks_output)
    parsed = {
        "category": raw_result.get("intent"),
        "urgency": raw_result.get("urgency"),
        "amount": raw_result.get("entities", {}).get("amount"),
    }

    response_output = raw_result.get("response")

    # Save to DB
    ticket = {
        "query": req.query,
        "parsed": parsed,
        "response": response_output,
        "status": "PROCESSING",
        "created_at": datetime.utcnow()
    }

    result = collection.insert_one(ticket)

    return {
        "ticket_id": str(result.inserted_id),
        "status": ticket["status"]
    }


@app.get("/api/v1/tickets")
def list_tickets(
    page: int = 1,
    per_page: int = 10,
    status: Optional[str] = None,
    category: Optional[str] = None,
    urgency: Optional[str] = None,
):
    skip = (page - 1) * per_page
    query = {}

    if status:
        query["status"] = status

    if category:
        query["parsed.category"] = category

    if urgency:
        query["parsed.urgency"] = urgency

    cursor = (
        collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(per_page)
    )

    tickets = []
    for t in cursor:
        parsed = t.get("parsed") or {}

        tickets.append({
            "id": str(t.get("_id")),
            "query": t.get("query"),
            "status": t.get("status"),

            "category": parsed.get("category"),
            "urgency": parsed.get("urgency"),
            "risk_level": parsed.get("risk_level"),
            "amount": parsed.get("amount"),

            "date": t.get("created_at").isoformat() if t.get("created_at") else None,
        })

    total = collection.count_documents(query)
    total_pages = max(1, (total + per_page - 1) // per_page)

    return {
        "tickets": tickets,
        "total_pages": total_pages
    }


@app.get("/api/v1/stats")
def get_stats():
    total = collection.count_documents({})
    high = collection.count_documents({"parsed.urgency": "high"})
    medium = collection.count_documents({"parsed.urgency": "medium"})
    low = collection.count_documents({"parsed.urgency": "low"})

    return {
        "total": total,
        "high": high,
        "medium": medium,
        "low": low
    }


@app.get("/api/v1/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    try:
        obj_id = ObjectId(ticket_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ticket id")

    t = collection.find_one({"_id": obj_id})
    if not t:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = {
        "id": str(t.get("_id")),
        "query": t.get("query"),
        "status": t.get("status"),
        "parsed": t.get("parsed"),
        "ai_response": t.get("response"),
        "created_at": t.get("created_at").isoformat() if t.get("created_at") else None,
    }

    return ticket