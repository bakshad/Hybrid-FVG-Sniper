"""
score_engine.py

Combines FVG and Structure scores into a
single normalized score out of 100.

FVG Engine:
    0 - 60

Structure Engine:
    0 - 40

Final:
    0 - 100
"""


class ScoreEngine:

    MONSTER = 95
    JACKPOT = 90
    ELITE = 85
    A_PLUS = 80

    @staticmethod
    def calculate(fvg_score: float,
                  structure_score: float) -> float:
        """
        Returns final score out of 100
        """

        score = round(
            float(fvg_score) +
            float(structure_score),
            2
        )

        return min(score, 100)

    @staticmethod
    def get_grade(score: float) -> str:

        if score >= ScoreEngine.MONSTER:
            return "MONSTER"

        if score >= ScoreEngine.JACKPOT:
            return "JACKPOT"

        if score >= ScoreEngine.ELITE:
            return "ELITE"

        if score >= ScoreEngine.A_PLUS:
            return "A+"

        return "IGNORE"

    @staticmethod
    def is_tradeable(score: float,
                     minimum_score: float = 85) -> bool:

        return score >= minimum_score

    @staticmethod
    def rank_signals(signals):
        """
        Sort signals by score descending.

        Input:
        [
            {...},
            {...}
        ]

        Output:
        Highest score first.
        """

        return sorted(
            signals,
            key=lambda x: x.get("Score", 0),
            reverse=True
        )

    @staticmethod
    def build_signal(
        symbol,
        side,
        fvg_result,
        structure_result
    ):
        """
        Create final signal object
        consumed by trade manager.
        """

        fvg_score = fvg_result["score"]
        structure_score = structure_result["score"]

        final_score = ScoreEngine.calculate(
            fvg_score,
            structure_score
        )

        grade = ScoreEngine.get_grade(
            final_score
        )

        return {
            "Symbol": symbol,
            "Side": side,
            "Score": final_score,
            "Grade": grade,
            "FVGScore": fvg_score,
            "StructureScore": structure_score,
            "FVG": fvg_result,
            "Structure": structure_result
        }
