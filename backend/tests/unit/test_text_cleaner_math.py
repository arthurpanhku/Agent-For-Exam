from app.utils.text_cleaner import protect_math_expressions, restore_math_placeholders


def test_protects_unicode_math_expression_as_single_placeholder():
    text = "Gradient descent uses α∇L(θ) to update parameters."

    protected, math_map = protect_math_expressions(text)

    assert "[MATH_EXPR_1]" in protected
    assert "α∇L(θ)" not in protected
    assert restore_math_placeholders(protected, math_map) == text


def test_protects_inline_latex_expression():
    text = "The update is $\\theta_{t+1}=\\theta_t-\\alpha\\nabla L(\\theta_t)$."

    protected, math_map = protect_math_expressions(text)

    assert "[MATH_EXPR_1]" in protected
    assert restore_math_placeholders(protected, math_map) == text
