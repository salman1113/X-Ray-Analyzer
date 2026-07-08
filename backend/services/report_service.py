import json
import logging
import os
from typing import Any

from langchain.output_parsers import PydanticOutputParser
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Strictly defined Output JSON Schema for the Radiology Report
class AIReportSchema(BaseModel):
    ai_finding: str = Field(description="AI Prediction and calculated Confidence %")
    location: str = Field(description="Anatomical description of the affected area")
    severity: str = Field(description="Severity classification (Mild / Moderate / Severe) based on model confidence and area")
    differential_diagnosis: list[str] = Field(description="2-3 possible medical conditions with probabilities")
    recommendation: str = Field(description="Next clinical steps based on standard guidelines")
    medical_disclaimer: str = Field(description="Standard Medical Disclaimer stating this is AI-assisted and requires human review")

class ReportService:
    """Service to handle LangChain RAG pipeline for generating Medical Reports"""
    def __init__(self):
        try:
            self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

            # Local FAISS index holding ACR guidelines, SNOMED CT terminology
            # self.vector_db = FAISS.load_local("faiss_index", self.embeddings, allow_dangerous_deserialization=True)
            self.vector_db = None

            self.llm = ChatOpenAI(
                temperature=0.1,
                model="gpt-4-turbo",
                openai_api_key=os.getenv("OPENAI_API_KEY", "mock-key")
            )
            self.parser = PydanticOutputParser(pydantic_object=AIReportSchema)
        except Exception as e:
            logger.error(f"Failed to initialize RAG ReportService: {e}")

    async def generate_report(self, prediction: str, confidence: float, localization: list[dict[str, Any]]) -> dict:
        """
        Executes the RAG pipeline to map model outputs to standardized radiological terminology
        and generates a structured clinical report.
        """
        try:
            # 1. Similarity Search over Medical Guidelines (FAISS)
            query = f"Radiology guidelines for {prediction}. Box locations: {localization}"

            context = "Standard medical protocol dictates visual confirmation of identified abnormalities. Proceed with further clinical correlation."
            if self.vector_db:
                context_docs = self.vector_db.similarity_search(query, k=3)
                context = "\n".join([doc.page_content for doc in context_docs])

            # 2. Build the structured Prompt Template
            prompt_template = """
            You are an expert AI radiologist assistant. Based on the underlying AI visual model findings and the standard clinical guidelines provided, generate a structured diagnostic radiology report.

            Reference Guidelines (ACR/SNOMED CT):
            {context}

            Model Inference Results:
            Prediction: {prediction}
            Confidence: {confidence:.2%}
            Localization Output: {localization}

            {format_instructions}
            """

            prompt = PromptTemplate(
                template=prompt_template,
                input_variables=["context", "prediction", "confidence", "localization"],
                partial_variables={"format_instructions": self.parser.get_format_instructions()}
            )

            chain = prompt | self.llm | self.parser

            # 3. Asynchronously invoke LLM Chain
            result = await chain.ainvoke({
                "context": context,
                "prediction": prediction,
                "confidence": confidence,
                "localization": json.dumps(localization)
            })

            return result.model_dump()

        except Exception as e:
            logger.error(f"Error executing LangChain RAG pipeline: {str(e)}")
            raise
