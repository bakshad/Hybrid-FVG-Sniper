"""
score_engine.py

Combines FVG and Structure scores into a
single normalized score out of 100.

Expected Inputs:

FVG Score:
    0 - 60

Structure Score:
    0 - 40

Final Score:
    0 - 100
"""


class ScoreEngine:

    # =========================
    # Grade Thresholds
    # =========================

    MONSTER = 95
    JACKPOT = 90
    ELITE = 85
    A_PLUS = 80
    A = 75
    B = 70

    # =========================
    # Final Score
    # =========================

    @staticmethod
    def calculate(
        fvg_score,
        structure_score
    ):
        """
        Returns normalized score
        capped at 100
        """

        score = round(
            float(fvg_score)
            + float(structure_score),
            2
        )

        return min(score, 100)

    # =========================
    # Grade
    # =========================

    @staticmethod
    def get_grade(score):
    
        if score >= 95:
            return "MONSTER"
    
        if score >= 90:
            return "JACKPOT"
    
        if score >= 85:
            return "ELITE"
    
        if score >= 80:
            return "A+"
    
        if score >= 75:
            return "A"
    
        if score >= 70:
            return "B"
    
        return "IGNORE"

    # =========================
    # Trade Qualification
    # =========================

    @staticmethod
    def is_tradeable(
        score,
        minimum_score=85
    ):

        return score >= minimum_score

    # =========================
    # Ranking
    # =========================

    @staticmethod
    def rank_signals(signals):
        """
        Sort highest score first
        """

        return sorted(
            signals,
            key=lambda x: x.get(
                "Score",
                0
            ),
            reverse=True
        )

    # =========================
    # Build Signal Object
    # =========================

    @staticmethod
    def build_signal(
        symbol,
        side,
        fvg_result,
        structure_result
    ):

        fvg_score = float(
            fvg_result["score"]
        )

        structure_score = float(
            structure_result["score"]
        )

        final_score = (
            ScoreEngine.calculate(
                fvg_score,
                structure_score
            )
        )

        grade = (
            ScoreEngine.get_grade(
                final_score
            )
        )

        return {

            "Symbol":
                symbol,

            "Side":
                side,

            "Score":
                final_score,

            "Grade":
                grade,

            "FVGScore":
                fvg_score,

            "StructureScore":
                structure_score,

            "FVG":
                fvg_result,

            "Structure":
                structure_result
        }

    # =========================
    # Daily Selection
    # =========================

    @staticmethod
    def select_top_signals(
        signals,
        max_signals=3
    ):
        """
        Used by main.py

        Example:
        Take only top 3 signals
        per day
        """

        ranked = (
            ScoreEngine.rank_signals(
                signals
            )
        )

        return ranked[:max_signals]
