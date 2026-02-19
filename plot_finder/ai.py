from __future__ import annotations

from typing import TYPE_CHECKING

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from plot_finder.report import PlotReport


class PlotAI:
    """AI-powered plot analysis using OpenAI.

    Parameters
    ----------
    report : PlotReport
        The report to analyze.
    api_key : str
        OpenAI API key.
    model : str
        OpenAI model to use.
    """

    def __init__(
        self,
        report: PlotReport,
        *,
        api_key: str,
        model: str = "gpt-4o-mini",
    ) -> None:
        if openai is None:
            raise ImportError(
                "openai is required for AI analysis. "
                "Install it with: pip install plot-finder[ai]"
            )
        self._context = report.model_dump_json()
        self._api_key = api_key
        self._model = model

    def _chat(self, system: str, user: str) -> str:
        client = openai.OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    def summary(self) -> str:
        """Natural language summary of the plot and surroundings."""
        return self._chat(
            "You are a real-estate analyst. Summarize the plot data below in "
            "clear, concise natural language. Mention location, nearby "
            "infrastructure, transport, nature, air quality, and sunlight.",
            self._context,
        )

    def rate(self, purpose: str = "living") -> str:
        """Rate the plot 1-10 for a given purpose with explanation."""
        return self._chat(
            "You are a real-estate analyst. Rate the plot 1-10 for the "
            f"purpose of **{purpose}**. Provide the rating and a short "
            "explanation covering pros and cons.",
            self._context,
        )

    def advantages(self) -> str:
        """Key advantages of this location."""
        return self._chat(
            "You are a real-estate analyst. List the key advantages of "
            "this location based on the data. Be specific and concise.",
            self._context,
        )

    def disadvantages(self) -> str:
        """Key disadvantages and risks of this location."""
        return self._chat(
            "You are a real-estate analyst. List the key disadvantages and "
            "risks of this location based on the data. Be specific and concise.",
            self._context,
        )

    def ask(self, question: str) -> str:
        """Freeform Q&A about the plot."""
        return self._chat(
            "You are a real-estate analyst. Answer the user's question "
            "about the plot based on the data below.\n\n" + self._context,
            question,
        )
