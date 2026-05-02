from crewai import Task

def get_tasks(agents, query):
    classifier, extractor, decision, validator, responder = agents

    t1 = Task(
        description=f"""
        Classify query into:
        fraud, refund, payment_issue, general

        Query: {query}

        Output ONLY one word.
        """,
        expected_output="One of: fraud, refund, payment_issue, general",
        agent=classifier
    )

    t2 = Task(
        description=f"""
        Extract details.

        Query: {query}

        Output STRICT JSON:
        {{
          "amount": "",
          "date": "",
          "transaction_id": ""
        }}
        """,
        expected_output="JSON with amount, date, transaction_id",
        agent=extractor
    )

    t3 = Task(
        description=f"""
        Decide:

        Query: {query}

        Output STRICT JSON:
        {{
          "risk_level": "",
           "urgency": "",
           "urgency_reason": "",
          "action": ""
        }}
        """,
        expected_output="JSON with risk_level and action",
        agent=decision
    )

    t4 = Task(
        description="""
        Validate all previous outputs.
        Fix invalid JSON.

        Output ONE merged JSON:
        {
          "category": "",
          "amount": "",
          "date": "",
          "transaction_id": "",
          "risk_level": "",
           "urgency": "",
           "urgency_reason": "",
          "action": ""
        }

        NO extra text.
        """,
        expected_output="Final merged JSON with all fields",
        agent=validator
    )

    t5 = Task(
        description=f"""
        Generate final user response.

        Query: {query}

        Keep it short and professional.
        """,
        expected_output="Professional response text",
        agent=responder
    )

    return [t1, t2, t3, t4, t5]