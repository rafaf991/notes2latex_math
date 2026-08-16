"""Tests for LaTeX-to-Mathematica post-processing."""

from document.mathematica import latex_body_to_mathematica


class TestLatexBodyToMathematica:
    def test_equation_line(self):
        latex = "x = y"
        assert (
            latex_body_to_mathematica(latex)
            == 'ToExpression["x", TeXForm] = ToExpression["y", TeXForm]\n'
        )

    def test_expression_without_equal_sign(self):
        latex = r"\sin(x)"
        assert latex_body_to_mathematica(latex) == 'ToExpression["\\\\sin(x)", TeXForm]\n'

    def test_align_environment_rows(self):
        latex = "\n".join(
            [
                "% ====== Page 1 ======",
                r"\begin{align*}",
                r"x &= y \\",
                r"\frac{1}{2} &= z",
                r"\end{align*}",
            ]
        )
        assert latex_body_to_mathematica(latex) == "\n".join(
            [
                "(* ====== Page 1 ====== *)",
                'ToExpression["x", TeXForm] = ToExpression["y", TeXForm]',
                'ToExpression["\\\\frac{1}{2}", TeXForm] = ToExpression["z", TeXForm]',
                "",
            ]
        )

    def test_multiple_align_rows_on_one_line(self):
        latex = "\n".join(
            [
                r"\begin{align}",
                r"x &= y \\ z &= w",
                r"\end{align}",
            ]
        )
        assert latex_body_to_mathematica(latex) == "\n".join(
            [
                'ToExpression["x", TeXForm] = ToExpression["y", TeXForm]',
                'ToExpression["z", TeXForm] = ToExpression["w", TeXForm]',
                "",
            ]
        )
