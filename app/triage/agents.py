from crewai import Agent
from .config import llm

def get_agents():

    classifier = Agent(
        role="Classifier",
        goal="Classify finance queries into intent and urgency",
        backstory="You are an expert financial support classifier. Only classify the query. Do not explain.",
        llm=llm,
        verbose=True
    )

    extractor = Agent(
        role="Extractor",
        goal="Extract financial entities like amount, account ID, transaction ID, and dates in JSON format",
        backstory="You extract structured financial data strictly in JSON. No explanations.",
        llm=llm
    )

    decision = Agent(
        role="Decision Maker",
        goal="Determine risk level and required action based on extracted data",
        backstory="You analyze financial queries and output only JSON decisions with risk and action.",
        llm=llm
    )

    validator = Agent(
        role="Validator",
        goal="Validate and correct JSON outputs",
        backstory="You strictly validate JSON structure and fix errors if needed. No extra text.",
        llm=llm
    )

    responder = Agent(
        role="Responder",
        goal="Generate a professional response to the user",
        backstory="You are a professional financial support assistant. Respond clearly and politely.",
        llm=llm
    )

    return classifier, extractor, decision, validator, responder