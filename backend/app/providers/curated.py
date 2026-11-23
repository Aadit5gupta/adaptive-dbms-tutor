"""Offline tutor that presents reviewed source material with task-specific prompts."""

from app.providers.contracts import ProviderAnswer, TutorContext


class CuratedProvider:
    async def respond(self, context: TutorContext) -> ProviderAnswer:
        passage = context.passages[0]
        excerpt = (
            passage.text[:540].rsplit(" ", 1)[0] + "…" if len(passage.text) > 540 else passage.text
        )
        mode = context.request.mode
        if mode == "hint" and context.request.hint_level == 1:
            answer = "Restate what the result should include. Which concept in this topic controls that behavior?"
        elif mode == "hint" and context.request.hint_level == 2:
            answer = (
                f"Use this idea as a clue, then trace it through one row or example.\n\n{excerpt}"
            )
        elif mode == "hint":
            answer = f"Make a small example by hand, then use this passage to check each step.\n\n{excerpt}"
        elif mode == "sql_feedback":
            answer = f"Compare the rows you expected with the rows your query returned. Check the columns, duplicate counts, and missing values.\n\n{excerpt}"
        elif mode == "example":
            answer = f"Work through the reviewed passage using a two-row example of your own.\n\n{excerpt}"
        elif mode == "simpler":
            leading = excerpt.split(". ", 1)[0]
            answer = leading if leading == excerpt else leading + "."
        else:
            answer = excerpt
        return ProviderAnswer(answer, (passage.citation.id,))
