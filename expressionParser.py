# %%
from __future__ import annotations
from typing import Callable, Union, List, Dict
from enum import Enum
from math import factorial, log, pi
from datetime import datetime, timedelta
from dateutil.relativedelta  import *
import re

PassedData = Union[float, int, str, bool, None]
ExecResponse = Callable[[Dict[str, PassedData]],
                        Callable[[Dict[str, PassedData]], float]]


class NodeType(Enum):
    STRING = "STRING"
    VARIABLE = "VARIABLE"
    TOKEN_GROUP = "TOKEN_GROUP"
    OPERATOR = "OPERATOR"
    COMPARATOR = "COMPARATOR"
    FUNCTION = "FUNCTION"
    CONSTANT = "CONSTANT"
    NUMBER = "NUMBER"


class Node():
    value: Union[str, None] = None
    type: Union[NodeType, None] = None
    node_a: Node = None
    node_b: Node = None

    def __init__(self, value: Union[str, None] = None):
        self.value = value

    def __str__(self):
        '{type}: {value}'.format(type=str(self.type), value=str(self.exec()))

    def exec(self) -> ExecResponse:
        raise Exception("Can not execute on an empty node")


class StringNode(Node):
    type = NodeType.STRING

    def __init__(self, value: Union[str, None] = None):
        value = re.sub('^\"|\"$', '', value)
        super().__init__(value)

    def exec(self) -> ExecResponse:
        return lambda **kwargs: str(self.value)


class NumberNode(Node):
    type = NodeType.NUMBER

    def exec(self) -> ExecResponse:
        return lambda **kwargs: float(self.value)


class ConstantNode(Node):
    type = NodeType.CONSTANT

    def __str__(self):
        return 'Constant {value} = {ex}'.format(value=self.value, ex=str(self.exec()))

    def exec(self) -> ExecResponse:
        if self.value == 'pi':
            return lambda **kwargs: pi
        raise Exception(
            '{value} is not a defined constant'.format(value=self.value))


class VariableNode(Node):
    type = NodeType.VARIABLE

    def exec(self) -> ExecResponse:
        return lambda **kwargs: kwargs.get(self.value, None)


operators = [
    ('ADD', '+', 0),
    ('SUBTRACT', '-', 0),
    ('MULTIPLY', '*', 1),
    ('DIVIDE', '/', 1),
    ('MODULUS', '%', 1),
    ('INT_DIVIDE', '//', 1),
    ('FACTORIAL', '!', 3),
    ('EXPONENTIAL', '^', 2)
]

operatorMap = {o[1]: o[0] for o in operators}
operatorWeightMap = {o[1]: o[2] for o in operators}
OperatorType = Enum('OperatorType', dict(map(lambda x: x[:2], operators)))


class OperatorNode(Node):
    type = NodeType.OPERATOR
    operator: OperatorType
    weight: int = 0

    def __init__(self, value):
        super().__init__(value)
        if operatorMap.get(value, None):
            self.operator = OperatorType(value)
            self.weight = operatorWeightMap[value]
        else:
            raise Exception('Invalid Operator: {op}'.format(op=value))

    def __str__(self):
        '{node_a} {operator} {node_b}'.format(
            node_a=str(self.node_a), operator=self.operator, node_b=str(self.node_b))

    def exec(self) -> ExecResponse:
        if self.node_a is None and self.node_b is None:
            raise Exception("Both targets on opperand are None")

        # Operations where only 1 node needs to be defined
        if self.operator is OperatorType.ADD:
            if self.node_a is None:
                return lambda **kwargs: abs(self.node_b.exec()(**kwargs))
            return lambda **kwargs: self.node_a.exec()(**kwargs) + self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.SUBTRACT:
            if self.node_a is None or self.node_a.value is None:
                return lambda **kwargs: -1 * self.node_b.exec()(**kwargs)
            return lambda **kwargs: self.node_a.exec()(**kwargs) - self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.FACTORIAL:
            if self.node_b is None:
                return lambda **kwargs: factorial(self.node_a.exec()(**kwargs))
            raise Exception('Factorial Operand can not have second target')

        if self.node_a is None or self.node_b is None:
            raise Exception("One target on opperand is None")

        # Operations where both nodes need to be defined
        if self.operator is OperatorType.MULTIPLY:
            return lambda **kwargs: self.node_a.exec()(**kwargs) * self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.DIVIDE:
            return lambda **kwargs: self.node_a.exec()(**kwargs) / self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.MODULUS:
            return lambda **kwargs: self.node_a.exec()(**kwargs) % self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.INT_DIVIDE:
            return lambda **kwargs: self.node_a.exec()(**kwargs) // self.node_b.exec()(**kwargs)

        if self.operator is OperatorType.EXPONENTIAL:
            return lambda **kwargs: self.node_a.exec()(**kwargs) ** self.node_b.exec()(**kwargs)


comparators = [
    ('EQUAL', '=='),
    ('LT', '<'),
    ('LTE', '<='),
    ('GT', '>'),
    ('GTE', '>='),
    ('NOT_EQUAL', '!='),
    ('OR', '|'),
    ('STRICT_OR', '||'),
    ('AND', '&'),
    ('STRICT_AND', '&&')
]

comparatorMap = {c[1]: c[0] for c in comparators}
ComparatorType = Enum('ComparatorType', dict(
    map(lambda x: x[:2], comparators)))


class ComparatorNode(Node):
    type = NodeType.COMPARATOR
    comparator: ComparatorType

    def __init__(self, value):
        super().__init__(value)
        if comparatorMap.get(value, None):
            self.comparator = ComparatorType(value)
        else:
            raise Exception('Invalid Comparator: {com}'.format(com=value))

    def __str__(self):
        '{node_a} {comparator} {node_b}'.format(
            node_a=str(self.node_a), comparator=self.comparator, node_b=str(self.node_b))

    def exec(self) -> ExecResponse:
        if self.node_a is None or self.node_b is None:
            raise Exception("1 of 2 targets on comparator is None")

        if self.comparator is ComparatorType.EQUAL:
            return lambda **kwargs: self.node_a.exec()(**kwargs) == self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.NOT_EQUAL:
            return lambda **kwargs: self.node_a.exec()(**kwargs) != self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.LT:
            return lambda **kwargs: self.node_a.exec()(**kwargs) < self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.LTE:
            return lambda **kwargs: self.node_a.exec()(**kwargs) <= self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.GT:
            return lambda **kwargs: self.node_a.exec()(**kwargs) > self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.GTE:
            return lambda **kwargs: self.node_a.exec()(**kwargs) >= self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.NOT_EQUAL:
            return lambda **kwargs: self.node_a.exec()(**kwargs) >= self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.OR:
            return lambda **kwargs: self.node_a.exec()(**kwargs) or self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.STRICT_OR:
            return lambda **kwargs: bool(self.node_a.exec()(**kwargs)) or bool(self.node_b.exec()(**kwargs))

        if self.comparator is ComparatorType.AND:
            return lambda **kwargs: self.node_a.exec()(**kwargs) and self.node_b.exec()(**kwargs)

        if self.comparator is ComparatorType.STRICT_AND:
            return lambda **kwargs: bool(self.node_a.exec()(**kwargs)) and bool(self.node_b.exec()(**kwargs))

        raise Exception('Invalid comparator {comparator}'.format(
            comparator=self.comparator))


# TODO work out comma spaced argument functions
functions = [
    ('TODAY','today'),
    ('AS_DATE','asDate'),
    ('SECONDS', 'seconds'),
    ('MINUTES', 'minutes'),
    ('HOURS','hours'),
    ('DAYS', 'days'),
    ('WEEKS','weeks'),
    ('MONTHS','months'),
    ('YEARS','years'),
    ('SUM','sum'),
    ('AVG','avg'),
    ('LOG10', 'log10'),
    ('NATURAL_LOG', 'ln'),
    ('LOG', 'log'),
    ('SQUARE_ROOT', 'sqrt'),
    ('CHAR_LENGTH', 'nchar'),
    ('NULL','isNull'),
    ('IN','in')
]

functionMap = {v: k for k, v in functions}
FunctionType = Enum('FunctionType', dict(functions))

class FunctionNode(Node):
    type: NodeType = NodeType.FUNCTION
    function: FunctionType
    arguments: List[TokenGroupNode] = []

    def __init__(self, value):
        super().__init__(value)
        if functionMap.get(value, None):
            self.function = FunctionType(value)
        else:
            raise Exception(
                'Invalid Function: {function}'.format(function=value))

    def __str__(self):
        '{function}({arguments})'.format(
            arguments=str(self.arguments), function=self.function)

    def exec(self) -> ExecResponse:

        if self.function is FunctionType.TODAY:
            return lambda : datetime.now()

        if len(self.arguments) == 0:
            raise Exception("Function argument is None")

        if self.function is FunctionType.AS_DATE:
            return lambda **kwargs: datetime.strptime(self.arguments[0].exec()(**kwargs),self.arguments[1].exec()(**kwargs) if len(self.arguments) > 1 else '%m/%d/%Y')
        
        if self.function is FunctionType.SECONDS:
            return lambda **kwargs: timedelta(seconds=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.MINUTES:
            return lambda **kwargs: timedelta(minutes=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.HOURS:
            return lambda **kwargs: timedelta(hours=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.DAYS:
            return lambda **kwargs: timedelta(days=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.WEEKS:
            return lambda **kwargs: timedelta(weeks=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.MONTHS:
            return lambda **kwargs: relativedelta(months=self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.YEARS:
            return lambda **kwargs: relativedelta(years=self.arguments[0].exec()(**kwargs))

        if self.function is FunctionType.SUM:
            return lambda **kwargs: sum(map(lambda a: a.exec()(**kwargs),self.arguments))
        
        if self.function is FunctionType.AVG:
            return lambda **kwargs: sum(map(lambda a: a.exec()(**kwargs),self.arguments))/(len(self.arguments) or 1)

        if self.function is FunctionType.LOG10:
            return lambda **kwargs: log(self.arguments[0].exec()(**kwargs), 10)

        if self.function is FunctionType.NATURAL_LOG:
            return lambda **kwargs: log(self.arguments[0].exec()(**kwargs))

        if self.function is FunctionType.LOG:
            return lambda **kwargs: log(self.arguments[0].exec()(**kwargs), self.arguments[1].exec()(**kwargs) if len(self.arguments) > 1 else 10)

        if self.function is FunctionType.SQUARE_ROOT:
            return lambda **kwargs: self.arguments[0].exec()(**kwargs) ** 0.5

        if self.function is FunctionType.CHAR_LENGTH:
            return lambda **kwargs: len(self.arguments[0].exec()(**kwargs))
        
        if self.function is FunctionType.NULL:
            return lambda **kwargs: self.arguments[0].exec()(**kwargs) in [None,''] 
        
        if self.function is FunctionType.IN:
            return lambda **kwargs: self.arguments[0].exec()(**kwargs) in map(lambda a: a.exec()(**kwargs),self.arguments[1:]) 


class TokenGroupNode(Node):
    type: NodeType = NodeType.TOKEN_GROUP

    def __init__(self, value):
        super().__init__(value)

    def exec(self) -> ExecResponse:
        tree = createExpressionTree(Node(), extractNodes(self.value))
        return lambda **kwargs: tree.exec()(**kwargs)

    def split(self) -> List[TokenGroupNode]:
        return [TokenGroupNode(v) for v in re.split(r",\s*(?![^()]*\))", self.value)]


tokenRegex = ("((?<=\").+(?=\"))"
              + "|((?<=\[)[a-z_]+(?=\]))"
              + "|(\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\))"
              + "|(==|!=|<=|<|>=|>|\|\||\||&&|&)"
              + "|([a-z][a-z_0-9]+(?=\())"
              + "|([a-z][a-z_0-9]+)"
              + "|([0-9.]+)"
              + "|([^a-z0-9\[\]\(\)\"\s]+)")

nodeTypes = {
    1: NodeType.STRING,
    2: NodeType.VARIABLE,
    3: NodeType.TOKEN_GROUP,
    4: NodeType.COMPARATOR,
    5: NodeType.FUNCTION,
    6: NodeType.CONSTANT,
    7: NodeType.NUMBER,
    8: NodeType.OPERATOR,
}


def createToken(t: NodeType, v: str) -> Node:
    if t is NodeType.STRING:
        return StringNode(v)
    elif t is NodeType.VARIABLE:
        return VariableNode(v)
    elif t is NodeType.TOKEN_GROUP:
        return TokenGroupNode(v)
    elif t is NodeType.COMPARATOR:
        return ComparatorNode(v)
    elif t is NodeType.OPERATOR:
        return OperatorNode(v)
    elif t is NodeType.FUNCTION:
        return FunctionNode(v)
    elif t is NodeType.CONSTANT:
        return ConstantNode(v)
    elif t is NodeType.NUMBER:
        return NumberNode(v)
    else:
        return Node(v)


def extractNodes(expression: str) -> List[Node]:
    matches = re.finditer(tokenRegex, expression, re.MULTILINE | re.IGNORECASE)
    nodes = []
    for match in matches:
        for groupNum, group in enumerate(match.groups(), start=1):
            if group:
                value = expression[match.start(
                    groupNum):match.end(groupNum)]
                if nodeTypes[groupNum] is NodeType.TOKEN_GROUP:
                    value = re.sub('^\(+|\)+$', '', value)
                    if value == '':
                        continue
                nodes.append(createToken(nodeTypes[groupNum], value))
    return nodes


def createExpressionTree(base: Node, nodes: List[Node]):
    if len(nodes) == 0:
        return base

    node = nodes.pop(0)
    if node.type is NodeType.OPERATOR:
        if base.type is NodeType.OPERATOR and node.weight > base.weight:
            node.node_a = base.node_b
            base.node_b = createExpressionTree(node, nodes)
        else:
            node.node_a = base
            return createExpressionTree(node, nodes)
    elif node.type is NodeType.COMPARATOR:
        node.node_a = base
        node.node_b = createExpressionTree(
            nodes.pop(0) if len(nodes) > 0 else Node(), nodes)
    elif node.type is NodeType.TOKEN_GROUP:
        if base.node_b and base.node_b.type is NodeType.FUNCTION:
            base.node_b.arguments = node.split()
        elif base.node_a and base.node_a.type is NodeType.FUNCTION:
            base.node_a.arguments = node.split()
        elif base.type is NodeType.FUNCTION:
            base.arguments = node.split()
        elif base.node_a is None:
            base.node_a = node
        elif base.node_b is None:
            base.node_b = node
        else:
            raise Exception('Invalid Syntax')
    elif base.value is None:
        base = node
    elif base.node_a is None:
        base.node_a = node
    elif base.node_b is None:
        base.node_b = node
    else:
        raise Exception('Invalid Syntax')

    return createExpressionTree(base, nodes)


# %%
expression = 'asDate("1995-02-14","%Y-%m-%d") + months(2)'
nodes = extractNodes(expression)
print(nodes)
tree = createExpressionTree(Node(), nodes)
print(tree.exec()())
# %%
