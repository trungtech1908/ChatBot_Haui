"""Tool Compute (ARCHITECTURE mục 2.8): biểu thức số học và so sánh trên biến lấy từ bước trước.

Đánh giá bằng duyệt AST với danh sách nút cho phép — không eval/exec. Dùng cho câu hỏi giả định
("nếu em đăng ký X tín chỉ thì…"); phép tính cố định đã có sẵn trong view.
"""
import ast
import math
import operator

_BIN = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow,
}
_UNARY = {ast.USub: operator.neg, ast.UAdd: operator.pos, ast.Not: operator.not_}
_CMP = {
    ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt, ast.GtE: operator.ge,
    ast.Eq: operator.eq, ast.NotEq: operator.ne,
}
_FUNCS = {"round": round, "min": min, "max": max, "abs": abs, "ceil": math.ceil, "floor": math.floor}
MAX_EXPR_LEN = 300
MAX_ABS = 1e15  # chặn số khổng lồ (VD 10 ** 10 ** 10)


class ComputeError(ValueError):
    pass


def evaluate(expr: str, variables: dict[str, float]) -> float | bool:
    if len(expr) > MAX_EXPR_LEN:
        raise ComputeError("Biểu thức quá dài")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise ComputeError(f"Biểu thức sai cú pháp: {expr}") from e

    def ev(node):
        match node:
            case ast.Expression(body=body):
                return ev(body)
            case ast.Constant(value=v) if isinstance(v, (int, float)) and not isinstance(v, bool):
                return v
            case ast.Name(id=name):
                if name not in variables:
                    raise ComputeError(f"Biến chưa có giá trị: {name}")
                return variables[name]
            case ast.BinOp(left=l, op=op, right=r) if type(op) in _BIN:
                a, b = ev(l), ev(r)
                if isinstance(op, ast.Pow) and (abs(b) > 10 or abs(a) > 1e6):
                    raise ComputeError("Lũy thừa quá lớn")
                if isinstance(op, (ast.Div, ast.FloorDiv, ast.Mod)) and b == 0:
                    raise ComputeError("Chia cho 0")
                result = _BIN[type(op)](a, b)
                if abs(result) > MAX_ABS:
                    raise ComputeError("Kết quả vượt giới hạn")
                return result
            case ast.UnaryOp(op=op, operand=x) if type(op) in _UNARY:
                return _UNARY[type(op)](ev(x))
            case ast.BoolOp(op=ast.And(), values=vals):
                return all(ev(v) for v in vals)
            case ast.BoolOp(op=ast.Or(), values=vals):
                return any(ev(v) for v in vals)
            case ast.Compare(left=left, ops=ops, comparators=comps) if all(type(o) in _CMP for o in ops):
                a = ev(left)
                for o, c in zip(ops, comps):
                    b = ev(c)
                    if not _CMP[type(o)](a, b):
                        return False
                    a = b
                return True
            case ast.Call(func=ast.Name(id=fn), args=args, keywords=[]) if fn in _FUNCS:
                return _FUNCS[fn](*(ev(a) for a in args))
        raise ComputeError(f"Không hỗ trợ phần tử '{ast.dump(node)[:60]}' trong biểu thức")

    return ev(tree)
