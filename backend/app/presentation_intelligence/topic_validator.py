"""Semantic Topic Isolation and Content Disinfectant Layer.

Ensures generated presentations strictly maintain domain topic boundaries and
completely prevents internal presentation-generator mechanics, tech stack details,
or diagnostic terms from leaking into user slides.
"""

import re
from typing import Any
from backend.app.domain.presentation import Presentation, Slide
from backend.app.presentation_intelligence.models import ContentQAIssue, ContentSeverity, ContentIssueType


FORBIDDEN_LEAKAGE_TERMS = [
    # Generator tech stack
    r"\b(react\s*(?:19|18|native)?)\b",
    r"\b(vite)\b",
    r"\b(tailwind\s*(?:css)?(?:\s*v4|\s*v3)?)\b",
    r"\b(fastapi)\b",
    r"\b(python-pptx)\b",
    r"\b(openxml(?:\s*shapes)?)\b",
    r"\b(lucide(?:\s*icons)?)\b",
    # Generator internals & algorithms
    r"\b(1920x1080(?:\s*constraint\s*solver)?)\b",
    r"\b(deterministic\s*1920x1080)\b",
    r"\b(layout\s*engine)\b",
    r"\b(constraint\s*solver)\b",
    r"\b(correlation\s*ids?)\b",
    r"\b(zero\s*rasterization)\b",
    r"\b(slide_shape_tree)\b",
    r"\b(basearchetyperesolver)\b",
    r"\b(threepasscorrectionengine)\b",
    r"\b(presenai)\b",
    r"\b(visual\s*qa\s*3-pass)\b",
]

COMPILED_LEAKAGE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_LEAKAGE_TERMS]


class SemanticTopicValidator:
    """Validates topic relevance and strictly enforces topic isolation against generator leakage."""

    @classmethod
    def is_generator_leakage(cls, text: str, user_topic: str = "") -> bool:
        """Check if text contains forbidden generator implementation terms.
        
        Exempt terms if the user explicitly requested them in user_topic.
        """
        if not text:
            return False
        topic_lower = user_topic.lower()
        if "presentation generator" in topic_lower or "presenai" in topic_lower or "pptx generator" in topic_lower:
            return False

        for pat in COMPILED_LEAKAGE_PATTERNS:
            match = pat.search(text)
            if match:
                matched_str = match.group(0).lower().strip()
                # If the matched keyword was explicitly mentioned in the user's topic, it is legitimate
                if matched_str and matched_str in topic_lower:
                    continue
                return True

        return False

    @classmethod
    def sanitize_text(cls, text: str, user_topic: str = "", replacement: str = "System Component") -> str:
        """Purge any leaked generator terms from a text string, preserving legitimate terms."""
        if not text:
            return text
        topic_lower = user_topic.lower()
        if "presentation generator" in topic_lower or "presenai" in topic_lower or "pptx generator" in topic_lower:
            return text

        sanitized = text
        for pat in COMPILED_LEAKAGE_PATTERNS:
            match = pat.search(sanitized)
            if match:
                matched_str = match.group(0).lower().strip()
                if matched_str and matched_str in topic_lower:
                    continue
                sanitized = pat.sub(replacement, sanitized)
        return sanitized

    @classmethod
    def sanitize_presentation(cls, presentation: Presentation) -> tuple[Presentation, int]:
        """Disinfect presentation in place and return (presentation, leak_count)."""
        count = cls.disinfect_presentation(presentation)
        return presentation, count

    @classmethod
    def validate_slide(cls, slide: Slide, user_topic: str = "") -> list[ContentQAIssue]:
        """Inspect a slide for forbidden context leakage and return QA issues."""
        issues: list[ContentQAIssue] = []

        # Check title and subtitle
        if cls.is_generator_leakage(slide.title, user_topic):
            issues.append(
                ContentQAIssue(
                    slide_number=slide.slide_number,
                    issue_type=ContentIssueType.TOPIC_LEAKAGE,
                    severity=ContentSeverity.CRITICAL,
                    description=f"Slide title contains leaked presentation generator terms: '{slide.title}'",
                    recommendation="Remove internal system jargon and replace with topic-aligned title.",
                )
            )

        if slide.subtitle and cls.is_generator_leakage(slide.subtitle, user_topic):
            issues.append(
                ContentQAIssue(
                    slide_number=slide.slide_number,
                    issue_type=ContentIssueType.TOPIC_LEAKAGE,
                    severity=ContentSeverity.CRITICAL,
                    description=f"Slide subtitle contains leaked presentation generator terms: '{slide.subtitle}'",
                    recommendation="Replace with topic-aligned contextual subtitle.",
                )
            )

        # Check elements
        for elem in slide.elements:
            t_content = elem.text_content.text if elem.text_content else ""
            c_title = elem.card_content.title if elem.card_content else ""
            c_body = elem.card_content.body if elem.card_content else ""

            for field_val in [t_content, c_title, c_body]:
                if field_val and cls.is_generator_leakage(field_val, user_topic):
                    issues.append(
                        ContentQAIssue(
                            slide_number=slide.slide_number,
                            issue_type=ContentIssueType.TOPIC_LEAKAGE,
                            severity=ContentSeverity.CRITICAL,
                            description=f"Slide element '{elem.id}' contains leaked generator terminology: '{field_val[:60]}...'",
                            recommendation="Disinfect content with topic-appropriate mechanisms.",
                        )
                    )
                    break

        return issues

    @classmethod
    def disinfect_presentation(cls, presentation: Presentation) -> int:
        """In-place disinfection of all presentation slides, replacing any leaked strings with topic-safe content."""
        leak_count = 0
        topic = presentation.metadata.topic if presentation.metadata else ""

        for slide in presentation.slides:
            if cls.is_generator_leakage(slide.title, topic):
                slide.title = cls.sanitize_text(slide.title, topic, "System Architecture & Core Mechanics")
                leak_count += 1

            if slide.subtitle and cls.is_generator_leakage(slide.subtitle, topic):
                slide.subtitle = cls.sanitize_text(slide.subtitle, topic, "Technical specifications and domain components")
                leak_count += 1

            if slide.takeaway and cls.is_generator_leakage(slide.takeaway, topic):
                slide.takeaway = cls.sanitize_text(slide.takeaway, topic, "Robust architecture ensures high reliability and security.")
                leak_count += 1

            for elem in slide.elements:
                if elem.text_content and cls.is_generator_leakage(elem.text_content.text, topic):
                    elem.text_content.text = cls.sanitize_text(elem.text_content.text, topic, "Core Architecture Component")
                    leak_count += 1

                if elem.card_content:
                    if cls.is_generator_leakage(elem.card_content.title, topic):
                        elem.card_content.title = cls.sanitize_text(elem.card_content.title, topic, "Domain Architecture Layer")
                        leak_count += 1
                    if cls.is_generator_leakage(elem.card_content.body, topic):
                        elem.card_content.body = cls.sanitize_text(elem.card_content.body, topic, "Implements core domain protocols, security boundaries, and validation workflows.")
                        leak_count += 1

        return leak_count
