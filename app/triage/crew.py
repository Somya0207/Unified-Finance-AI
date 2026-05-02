import requests
import os
import json
import re
from dotenv import load_dotenv
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


def run_crew(query: str):
    prompt = f"""
You are a finance support AI assistant.

Perform:
1. Classify intent (fraud, refund, payment_issue, general)
2. Extract key details (amount, date, transaction info)
3. Decide urgency (low, medium, high)
4. Generate response

Return ONLY valid JSON (no text before/after):
{{
    "intent": "",
    "urgency": "",
    "entities": {{}},
    "response": ""
}}

Query: {query}
"""

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
       
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "FinTriage"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
 
        response = requests.post(
            url,
            headers=headers,
            json=data,
            timeout=20
        )

        print("STATUS CODE:", response.status_code)

        if response.status_code != 200:
            print("ERROR RESPONSE:", response.text)

        response.raise_for_status()

        result = response.json()

        content = result["choices"][0]["message"]["content"]

        print("\nRAW LLM RESPONSE:\n", content)

        json_match = re.search(r"\{.*\}", content, re.DOTALL)

        if not json_match:
            raise ValueError("No valid JSON found in LLM response")

        parsed = json.loads(json_match.group())

        return {
            "intent": parsed.get("intent", "general"),
            "urgency": parsed.get("urgency", "low"),
            "entities": parsed.get("entities", {}),
            "response": parsed.get("response", "No response generated")
        }

    except Exception as e:
        print("OpenRouter Error:", e)

        query_lower = query.lower()

        return {
            "intent": "fraud" if "unauthorized" in query_lower or "fraud" in query_lower
                    else "payment_issue" if "charged" in query_lower or "transaction" in query_lower
                    else "refund" if "refund" in query_lower
                    else "general",

            "urgency": "high" if "unauthorized" in query_lower or "fraud" in query_lower
                    else "medium" if "charged" in query_lower or "failed" in query_lower
                    else "low",

            "entities": {},

            "response": "We are reviewing your request and will resolve it shortly. Our support team will contact you if needed."
    }