import json
from typing import Any, Dict, List

from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import HuggingFacePipeline

from app.core.logger import logger


class LangChainQueryService:
    """Service for structuring queries using LangChain."""

    def __init__(self):
        logger.info("initializing_langchain_service")
        
        # Define prompt template for structured responses
        self.query_template = PromptTemplate(
            input_variables=["context", "question", "image_descriptions"],
            template="""Given the following context and image descriptions, answer the question in a structured JSON format.

Context: {context}

Image Descriptions:
{image_descriptions}

Question: {question}

Provide a structured response with the following fields:
- summary: A brief summary of the answer
- details: Detailed explanation
- relevant_images: List of relevant image IDs
- confidence: Confidence score (0.0 to 1.0)

Response (JSON format):""",
        )

        self.comparison_template = PromptTemplate(
            input_variables=["image_1_desc", "image_2_desc", "question"],
            template="""Compare these two images and answer the question.

Image 1: {image_1_desc}
Image 2: {image_2_desc}

Question: {question}

Provide a structured comparison with:
- changes: List of observed changes
- summary: Overall comparison summary
- confidence: Confidence score (0.0 to 1.0)

Response (JSON format):""",
        )

    async def structure_query_response(
        self, context: str, question: str, image_descriptions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Structure a query response using LangChain."""
        try:
            # Format image descriptions
            formatted_descriptions = "\n".join(
                [
                    f"- Image {i+1} (ID: {desc.get('image_id', 'unknown')}): {desc.get('text_description', 'No description')}"
                    for i, desc in enumerate(image_descriptions)
                ]
            )

            # Create structured response manually (without LLM for now)
            # In production, you could use a local LLM or API
            response = {
                "summary": self._generate_summary(question, image_descriptions),
                "details": f"Based on {len(image_descriptions)} image(s) in the project.",
                "relevant_images": [desc.get("image_id") for desc in image_descriptions],
                "confidence": self._calculate_confidence(image_descriptions),
            }

            logger.info("query_structured", image_count=len(image_descriptions))
            return response

        except Exception as e:
            logger.error("query_structuring_error", error=str(e))
            return {
                "summary": "Error processing query",
                "details": str(e),
                "relevant_images": [],
                "confidence": 0.0,
            }

    async def structure_comparison_response(
        self, image_1_desc: str, image_2_desc: str, question: str
    ) -> Dict[str, Any]:
        """Structure a comparison response."""
        try:
            # Create structured comparison
            changes = self._detect_changes(image_1_desc, image_2_desc)

            response = {
                "changes": changes,
                "summary": f"Comparing images: Image 1 shows {image_1_desc}. Image 2 shows {image_2_desc}.",
                "image_1_description": image_1_desc,
                "image_2_description": image_2_desc,
                "confidence": 0.85,
            }

            logger.info("comparison_structured")
            return response

        except Exception as e:
            logger.error("comparison_structuring_error", error=str(e))
            return {
                "changes": [],
                "summary": "Error processing comparison",
                "image_1_description": "",
                "image_2_description": "",
                "confidence": 0.0,
            }

    def _generate_summary(self, question: str, descriptions: List[Dict[str, Any]]) -> str:
        """Generate a summary based on question and descriptions."""
        if not descriptions:
            return "No images found for this project."

        if "compare" in question.lower() and len(descriptions) >= 2:
            return f"Comparison of {len(descriptions)} images in the project."
        elif "latest" in question.lower() or "recent" in question.lower():
            return f"Latest image shows: {descriptions[-1].get('text_description', 'No description')}"
        else:
            return f"Analysis of {len(descriptions)} image(s) in the project."

    def _calculate_confidence(self, descriptions: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on available data."""
        if not descriptions:
            return 0.0

        # Simple confidence calculation based on description availability
        has_descriptions = sum(1 for d in descriptions if d.get("text_description"))
        confidence = has_descriptions / len(descriptions) if descriptions else 0.0

        return min(confidence * 0.9, 0.95)  # Cap at 0.95

    def _detect_changes(self, desc_1: str, desc_2: str) -> List[Dict[str, str]]:
        """Detect changes between two descriptions."""
        changes = []

        # Simple keyword-based change detection
        words_1 = set(desc_1.lower().split())
        words_2 = set(desc_2.lower().split())

        added = words_2 - words_1
        removed = words_1 - words_2

        if added:
            changes.append({
                "type": "addition",
                "description": f"New elements detected: {', '.join(list(added)[:5])}",
            })

        if removed:
            changes.append({
                "type": "removal",
                "description": f"Elements removed: {', '.join(list(removed)[:5])}",
            })

        if not changes:
            changes.append({
                "type": "similar",
                "description": "Images appear similar with no major changes detected.",
            })

        return changes


# Singleton instance
_langchain_service = None


def get_langchain_service() -> LangChainQueryService:
    """Get or create LangChain service singleton."""
    global _langchain_service
    if _langchain_service is None:
        _langchain_service = LangChainQueryService()
    return _langchain_service
