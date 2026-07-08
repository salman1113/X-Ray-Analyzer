import json
import logging

import httpx

from core.settings import settings

logger = logging.getLogger(__name__)


async def generate_llm_explanations(
    body_part: str,
    body_part_label: str,
    prediction: str,
    confidence: float,
    probabilities: dict,
    local_patient_summary: dict,
    local_clinical_explanation: str,
) -> tuple[dict, str]:
    """
    Calls the Groq API to rewrite/improve:
    1. The clinical notes (clinical explanation).
    2. The structured patient summary (JSON matching the UI schema).

    If GROQ_API_KEY is not set or the request fails, falls back to local templates.

    Returns:
        tuple of (patient_summary_dict, clinical_explanation_str)
    """
    if not settings.GROQ_API_KEY:
        logger.info("GROQ_API_KEY not configured — using local templates.")
        return local_patient_summary, local_clinical_explanation

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    patient_summary = local_patient_summary
    clinical_explanation = local_clinical_explanation

    try:
        # Prompt for Patient Summary
        patient_prompt = f"""
You are an expert AI radiologist communicating with a patient.
The patient had an X-ray scan of their '{body_part_label}'.
The AI model predicted the finding as '{prediction}' with {round(confidence * 100)}% confidence.
All class probabilities: {probabilities}

Based on this, rewrite the patient explanation at a 6th-grade reading level (easy to understand, empathetic, no medical jargon).
You must output a JSON object with the following fields:
- headline: A short, clear one-line title/summary (e.g. "Possible lung infection detected")
- emoji: A relevant single emoji (e.g. "🚨" for urgent, "⚠️" for soon, "🦵" for knee)
- what_found: What the AI model found on the X-ray in extremely simple words.
- what_it_means: What this means for the patient's health, explain clearly and empathetically.
- what_to_do: Practical, simple actions the patient should take next.
- urgency: One of: "good" | "watch" | "soon" | "urgent"
- confidence_text: A simple explanation of how confident the AI is (e.g. "The AI is very confident in this result (98%).")
- body_part_label: "{body_part_label}"
- prediction: "{prediction}"

Output ONLY a valid JSON object. Do not include any backticks or additional text outside of the JSON block.
"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful medical assistant that outputs JSON.",
                        },
                        {"role": "user", "content": patient_prompt},
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.3,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                patient_summary = json.loads(content)
                logger.info("Successfully generated patient summary via Groq LLM.")
            else:
                logger.error("Groq API error for patient summary: %s", resp.text)
    except Exception as e:
        logger.exception("Failed to generate patient summary via Groq LLM, using fallback: %s", e)

    try:
        # Prompt for Clinical Notes
        clinical_prompt = f"""
You are an expert thoracic and skeletal radiologist writing clinical notes for the referring physician.
Scan Target: {body_part_label}
AI Model Prediction: {prediction} (Confidence: {round(confidence * 100)}%)
Full Probability Map: {probabilities}

Write a professional, structured clinical note summary based on this AI prediction.
You MUST format each section using short, concise bullet points (list format) and keep it extremely brief and high-yield. Do not write paragraphs.

Structure the note exactly as:
### Findings Summary
- State the primary prediction and its confidence level.
- Highlight any secondary key metrics or class exclusions.

### Differential Diagnosis & Significance
- Clinical interpretation of the primary findings.
- Note any potential differential considerations.

### Recommendations
- Practical, short diagnostic/therapeutic next steps.
- Timeline or correlation suggestion.

Keep the language professional, clinical, and scientific. Format in clean markdown lists with bullet points.
"""
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                url,
                headers=headers,
                json={
                    "model": settings.GROQ_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional clinical radiologist.",
                        },
                        {"role": "user", "content": clinical_prompt},
                    ],
                    "temperature": 0.2,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                clinical_explanation = data["choices"][0]["message"]["content"].strip()
                logger.info("Successfully generated clinical notes via Groq LLM.")
            else:
                logger.error("Groq API error for clinical notes: %s", resp.text)
    except Exception as e:
        logger.exception("Failed to generate clinical notes via Groq LLM, using fallback: %s", e)

    return patient_summary, clinical_explanation
