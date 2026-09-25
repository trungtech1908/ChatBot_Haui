import pytest

from chatbot_haui.ai.tools.compute import ComputeError, evaluate


@pytest.mark.parametrize("expr, variables, expected", [
    ("18 * he_so * don_gia", {"he_so": 1.0, "don_gia": 700000}, 12600000),
    ("round(tb * 10) / 10", {"tb": 3.26}, 3.3),
    ("tb >= 2.5 and rl >= 80", {"tb": 3.1, "rl": 79}, False),
    ("2.0 <= tb < 3.2", {"tb": 2.9}, True),
    ("max(a, b) - min(a, b)", {"a": 3, "b": 7}, 4),
    ("-x + 2 ** 3", {"x": 1}, 7),
])
def test_arithmetic_and_comparison(expr, variables, expected):
    assert evaluate(expr, variables) == pytest.approx(expected)


@pytest.mark.parametrize("expr", [
    "__import__('os').system('ls')",
    "open('/etc/passwd').read()",
    "x.__class__",
    "[i for i in range(10)]",
    "lambda: 1",
    "10 ** 10 ** 10",
    "1 / 0",
    "chua_co_bien + 1",
    "'chuỗi' * 3",
    "x if x else 1",
])
def test_rejects_anything_outside_whitelist(expr):
    with pytest.raises(ComputeError):
        evaluate(expr, {"x": 1})
