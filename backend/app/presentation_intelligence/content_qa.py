"""Deterministic Content Quality Assurance and Deck Rhetoric Evaluation Engine."""

import re
from backend.app.domain.enums import (
    ContentIssueType,
    ContentSeverity,
    NarrativeRole,
    VisualType,
)
from backend.app.domain.presentation import Presentation, Slide
from backend.app.presentation_intelligence.models import (
    ContentQAIssue,
    ContentQAResult,
    PresentationQualityScore,
    SlideContentQAResult,
)

GENERIC_TITLE_PATTERNS = [
    re.compile(r"^(Phase\s*\d+|Step\s*\d+|Slide\s*\d+|Topic\s*\d+)$", re.IGNORECASE),
    re.compile(r"^(Overview|Introduction|Summary|Conclusion|Next Steps|Details)$", re.IGNORECASE),
    re.compile(r":\s*Phase\s*\d+$", re.IGNORECASE),
]

GENERIC_BULLET_PATTERNS = [
    re.compile(r"\b(it improves efficiency|it is widely used|it has many advantages|application in many fields)\b", re.IGNORECASE),
    re.compile(r"\b(strategic domain analysis and implementation mechanics)\b", re.IGNORECASE),
]


class ContentQAEngine:
    """Deterministic Content QA Engine scoring presentation depth, narrative clarity, and visual variety."""

    def evaluate_slide(self, slide: Slide, previous_subtitles: set[str]) -> SlideContentQAResult:
        """Evaluate content quality for a single slide."""
        issues: list[ContentQAIssue] = []
        score = 100.0

        title = slide.title.strip()
        words = title.split()
        title_word_count = len(words)

        # 1. Title Quality Evaluation
        if slide.slide_number > 1:
            for pat in GENERIC_TITLE_PATTERNS:
                if pat.search(title):
                    issues.append(
                        ContentQAIssue(
                            slide_number=slide.slide_number,
                            issue_type=ContentIssueType.GENERIC_TITLE,
                            severity=ContentSeverity.WARNING,
                            description=f"Slide has generic formulaic title: '{title}'",
                            recommendation="Replace with an action or insight-driven headline summarizing the slide's key thesis.",
                        )
                    )
                    score -= 15.0
                    break

            if title_word_count < 3:
                issues.append(
                    ContentQAIssue(
                        slide_number=slide.slide_number,
                        issue_type=ContentIssueType.GENERIC_TITLE,
                        severity=ContentSeverity.INFO,
                        description=f"Slide title is very short ({title_word_count} words).",
                        recommendation="Expand title into a complete, informative message.",
                    )
                )
                score -= 5.0

        # 2. Subtitle Differentiation Evaluation
        subtitle = (slide.subtitle or "").strip()
        if subtitle:
            if subtitle in previous_subtitles and slide.slide_number > 1:
                issues.append(
                    ContentQAIssue(
                        slide_number=slide.slide_number,
                        issue_type=ContentIssueType.DUPLICATE_CONTENT,
                        severity=ContentSeverity.WARNING,
                        description=f"Duplicate subtitle across multiple slides: '{subtitle}'",
                        recommendation="Generate a distinct subtitle explaining this specific slide's narrative context.",
                    )
                )
                score -= 15.0
            previous_subtitles.add(subtitle)

        # 3. Takeaway Presence Check (for body slides)
        has_takeaway = bool(slide.takeaway and len(slide.takeaway.strip()) >= 10)
        if not has_takeaway and slide.slide_number > 1 and slide.narrative_role != NarrativeRole.TITLE:
            issues.append(
                ContentQAIssue(
                    slide_number=slide.slide_number,
                    issue_type=ContentIssueType.MISSING_TAKEAWAY,
                    severity=ContentSeverity.WARNING,
                    description="Slide is missing an explicit executive takeaway callout.",
                    recommendation="Add an actionable takeaway summarizing the core conclusion of this slide.",
                )
            )
            score -= 10.0

        # 4. Content Depth Check
        bullet_count = len(slide.elements)
        is_card_grid = bool(
            slide.visual_plan and slide.visual_plan.visual_type == VisualType.CARD_GRID
        )

        for elem in slide.elements:
            text = (elem.card_content.body if elem.card_content else (elem.text_content.text if elem.text_content else ""))
            for g_pat in GENERIC_BULLET_PATTERNS:
                if g_pat.search(text):
                    issues.append(
                        ContentQAIssue(
                            slide_number=slide.slide_number,
                            issue_type=ContentIssueType.SHALLOW_CONTENT,
                            severity=ContentSeverity.WARNING,
                            description="Slide contains generic filler phrases.",
                            recommendation="Replace with concrete domain mechanisms, metrics, or examples.",
                        )
                    )
                    score -= 10.0
                    break

        score = max(0.0, min(100.0, score))
        passed = score >= 70.0 and not any(i.severity == ContentSeverity.CRITICAL for i in issues)

        return SlideContentQAResult(
            slide_number=slide.slide_number,
            score=score,
            passed=passed,
            title=title,
            title_word_count=title_word_count,
            bullet_count=bullet_count,
            has_takeaway=has_takeaway,
            is_card_grid=is_card_grid,
            issues=issues,
        )

    def evaluate_presentation(self, presentation: Presentation) -> ContentQAResult:
        """Evaluate content quality, deck visual variety, and narrative coherence across entire presentation."""
        slide_results: list[SlideContentQAResult] = []
        all_issues: list[ContentQAIssue] = []
        previous_subtitles: set[str] = set()

        card_grid_count = 0
        body_slide_count = 0

        for slide in presentation.slides:
            res = self.evaluate_slide(slide, previous_subtitles)
            slide_results.append(res)
            all_issues.extend(res.issues)

            if slide.slide_number > 1:
                body_slide_count += 1
                if res.is_card_grid:
                    card_grid_count += 1

        # Calculate card grid ratio
        card_grid_ratio = card_grid_count / max(1, body_slide_count)
        if card_grid_ratio > 0.40 and body_slide_count >= 3:
            all_issues.append(
                ContentQAIssue(
                    slide_number=1,
                    issue_type=ContentIssueType.EXCESSIVE_CARDS,
                    severity=ContentSeverity.WARNING,
                    description=f"Deck-level card grid ratio is {round(card_grid_ratio * 100)}% (exceeds 30% target).",
                    recommendation="Diversify visual representations using ProcessFlows, Timelines, Architecture, Tables, and Charts.",
                )
            )

        # Presentation-level average score
        avg_score = sum(s.score for s in slide_results) / len(slide_results) if slide_results else 100.0
        if card_grid_ratio > 0.40:
            avg_score = max(0.0, avg_score - 10.0)

        critical_count = sum(1 for i in all_issues if i.severity == ContentSeverity.CRITICAL)
        error_count = sum(1 for i in all_issues if i.severity == ContentSeverity.ERROR)
        warning_count = sum(1 for i in all_issues if i.severity == ContentSeverity.WARNING)

        passed = avg_score >= 70.0 and critical_count == 0

        return ContentQAResult(
            passed=passed,
            quality_score=round(avg_score, 2),
            total_issues=len(all_issues),
            critical_issues=critical_count,
            errors=error_count,
            warnings=warning_count,
            card_grid_ratio=round(card_grid_ratio, 2),
            narrative_coherence_score=round(avg_score, 2),
            slide_results=slide_results,
            issues=all_issues,
        )

    evaluate = evaluate_presentation


# Global default content QA engine
default_content_qa = ContentQAEngine()
