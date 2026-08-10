"""A scalar reverse-mode autodiff engine: the mechanism behind `.backward()`.

Every operation on a `Value` records its inputs and a local backward
function. `backward()` topologically sorts the resulting graph and walks it
in reverse, applying each node's local rule and accumulating (`+=`, never
`=`) into every input's `.grad` — accumulation, not overwrite, is what makes
a value used twice (once directly, once through a longer path) receive both
contributions correctly, per the multivariate chain rule.

No numpy, no torch: gradients are one Python float per node.
"""

from __future__ import annotations

import math


class Value:
    def __init__(self, data: float, children: tuple[Value, ...] = (), op: str = ""):
        self.data = float(data)
        self.grad = 0.0
        self._backward = lambda: None
        self._prev = set(children)
        self._op = op

    def __add__(self, other) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other), "+")

        def _backward():
            self.grad += out.grad
            other.grad += out.grad

        out._backward = _backward
        return out

    def __mul__(self, other) -> Value:
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other), "*")

        def _backward():
            self.grad += other.data * out.grad
            other.grad += self.data * out.grad

        out._backward = _backward
        return out

    def tanh(self) -> Value:
        t = math.tanh(self.data)
        out = Value(t, (self,), "tanh")

        def _backward():
            self.grad += (1 - t * t) * out.grad

        out._backward = _backward
        return out

    def __radd__(self, other) -> Value:
        return self + other

    def __rmul__(self, other) -> Value:
        return self * other

    def __neg__(self) -> Value:
        return self * -1

    def __sub__(self, other) -> Value:
        return self + (-other)

    def backward(self) -> None:
        topo: list[Value] = []
        visited: set[int] = set()

        def build(v: Value) -> None:
            if id(v) not in visited:
                visited.add(id(v))
                for child in v._prev:
                    build(child)
                topo.append(v)

        build(self)
        self.grad = 1.0
        for v in reversed(topo):
            v._backward()

    def __repr__(self) -> str:
        return f"Value(data={self.data}, grad={self.grad})"


def diamond_expression(a: Value, b: Value, c: Value) -> Value:
    """f = (a*b + c) * a, L = tanh(f) -- 'a' is consumed twice, on purpose.

    This is the load-bearing test case: an autodiff engine that assigns
    (rather than accumulates) gradients would silently drop one of the two
    contributions to `a.grad` here.
    """
    d = a * b
    e = d + c
    f = e * a
    return f.tanh()


if __name__ == "__main__":
    a, b, c = Value(0.7), Value(-0.5), Value(1.2)
    loss = diamond_expression(a, b, c)
    loss.backward()
    print(f"L = {loss.data:.10f}")
    print(f"dL/da = {a.grad:.10f}")
    print(f"dL/db = {b.grad:.10f}")
    print(f"dL/dc = {c.grad:.10f}")
