#!/usr/bin/python3
import sys
from enum import Enum


class RockstarSyntaxError(Exception):
    """ An error indicating invalid Rockstar syntax. """

    def __init__(self, message):
        self.message = message
        self.filename = "- Unkown -"
        self.line = "-"
        self.source = "..."

    def add_info(self, filename, line, source):
        """ Adds critical information to the parsing. """
        self.filename = filename
        self.line = line
        self.source = source

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "{}\n{}\n{}({}): SyntaxError {}".format(self.source,
                                                       "^" * len(self.source),
                                                       self.filename,
                                                       self.line,
                                                       self.message)


class TokenType(Enum):
    VARIABLE = 1
    ASSIGNMENT = 2
    EXPRESSION = 3
    CONSTANT = 8
    OUTPUT = 5
    INPUT = 6
    END = 7
    IF = 10
    LOOP = 13
    OPERATOR = 11
    TURN = 12
    STRING = 9
    FUNCTION = 14
    CALL = 16
    RETURN = 15


def is_simple_variable(token):
    """ Checks if a token is a simple variable name """
    if not token:
        return False
    return token.islower()


def is_proper_variable(token):
    """ Checks if a token is a part of a proper variable name """
    return token.istitle()


def is_pronoun(token):
    """ Checks if a token is a valid pronoun """
    return token.lower() in ["it", "he", "she", "him", "her", "they",
                             "them", "ze", "hir", "zie", "zir", "xe",
                             "xem", "ve", "ver"]


last_parsed_variable = None
def try_parse_variable_name(tokens):
    """ Tries to parse the next tokens as variables, if they aren't,
        the tokens are returned, otherwise the tokens are eaten and
        the variable name is returned. """
    global last_parsed_variable
    variable_name = None
    if tokens:
        valid_prefixes = ["a", "an", "the", "my", "your"]
        if is_pronoun(tokens[0]):
            variable_name = last_parsed_variable
            tokens = tokens[1:]
        elif tokens[0] in valid_prefixes:
            if len(tokens) > 1 and is_simple_variable(tokens[1]):
                variable_name = (tokens[0] + "#" + tokens[1])
                tokens = tokens[2:]
        elif is_proper_variable(tokens[0]):
            proper = []
            while tokens:
                if is_proper_variable(tokens[0]):
                    proper.append(tokens[0])
                else:
                    break
                tokens = tokens[1:]
            variable_name = "_".join(proper)
        elif is_simple_variable(tokens[0]):
            variable_name = tokens[0]
            tokens = tokens[1:]

    if variable_name is None:
        return None, tokens
    else:
        last_parsed_variable = variable_name.lower()
        return (TokenType.VARIABLE, variable_name.lower()), tokens


def is_assignment(token):
    """ Returns true if the passed in token is an assignemnt alias. """
    return token.lower() in ["is", "are", "was", "were"]


def parse_poetic_number_literals(tokens):
    """ Parses a series of tokens as a poetic number literal """
    num = 0
    while tokens:
        t = tokens[0]
        tokens = tokens[1:]
        num *= 10
        num += sum(map(lambda c: c.isalpha() or c == "-", t)) % 10
        if "." in t:
            break

    decimal = 0
    points = 0
    while tokens:
        t = tokens[0]
        tokens = tokens[1:]
        points += 1
        decimal *= 10
        decimal += sum(map(lambda c: c.isalpha() or c == "-", t)) % 10

    return TokenType.CONSTANT, num + (decimal * 10 ** -points)


def try_parse_string_literal(tokens):
    """ Tries to parse out a string literal from the tokens. """
    if tokens and tokens[0].startswith("\"") and tokens[0].startswith("\""):
        return (TokenType.CONSTANT, tokens[0]), tokens[1:]
    return None, tokens


def try_parse_numeric_constant(tokens):
    """ Tries to parse out a numeric constant from the tokens. """
    #TODO(ed) : Should null be 0 ?
    if tokens[0] in ["null", "nothing", "nowhere", "nobody", "empty", "gone"]:
        return (TokenType.CONSTANT, 0), tokens[1:]
    if tokens[0] in ["true", "right", "yes", "ok", "truth"]:
        return (TokenType.CONSTANT, True), tokens[1:]
    if tokens[0] in ["false", "wrong", "no", "lies"]:
        return (TokenType.CONSTANT, False), tokens[1:]
    try:
        n = int(tokens[0])
        return (TokenType.CONSTANT, n), tokens[1:]
    except ValueError:
        return None, tokens


def try_parse_operator(tokens):
    token = tokens[0]
    if token in ["plus", "with"]:
        return (TokenType.OPERATOR, "add"), tokens[1:]
    if token in ["minus", "without"]:
        return (TokenType.OPERATOR, "sub"), tokens[1:]
    if token in ["times", "of"]:
        return (TokenType.OPERATOR, "mul"), tokens[1:]
    if token in ["over"]:
        return (TokenType.OPERATOR, "div"), tokens[1:]
    if token == "is":
        # It's a comparison!
        if len(tokens) > 2:
            if tokens[1] == "not":
                return (TokenType.OPERATOR, "neq"), tokens[2:]
        if len(tokens) > 3:
            if tokens[2] in ["then", "than"]:
                if tokens[1] in ["higher", "greater", "bigger", "stronger"]:
                    return (TokenType.OPERATOR, "gt"), tokens[3:]
                if tokens[1] in ["lower", "less", "smaller", "weaker"]:
                    return (TokenType.OPERATOR, "lt"), tokens[3:]

        if len(tokens) > 4:
            if tokens[1] == "as" and tokens[3] == "as":
                if tokens[2] in ["high", "great", "big", "strong"]:
                    return (TokenType.OPERATOR, "geq"), tokens[4:]
                if tokens[2] in ["low", "little", "small", "weak"]:
                    return (TokenType.OPERATOR, "leq"), tokens[4:]
        return (TokenType.OPERATOR, "eq"), tokens[1:]
    if token == "isnt":
        return (TokenType.OPERATOR, "neq"), tokens[1:]
    if token == "aint":
        return (TokenType.OPERATOR, "neq"), tokens[1:]
    return None, tokens


def try_parse_expression(tokens):
    """ Parses an expression from the next of the tokens. """
    # TODO(ed): This is what's next...
    expression = []
    while tokens:
        if len(tokens) > 1 and tokens[1] == "taking":
            name = tokens[0]
            tokens = tokens[2:]
            arguments = []
            while tokens:
                chunk = []
                while tokens:
                    if tokens and tokens[0] in [",", "and", "n"]:
                        tokens = tokens[1:]
                        if tokens and tokens[0] == "and":
                            tokens = tokens[1:]
                        break
                    chunk.append(tokens[0])
                    tokens = tokens[1:]
                var, _ = try_parse_expression(chunk)
                if var[1]:
                    arguments.append(var)
            call = TokenType.CALL, name, arguments
            expression.append(call)
            continue
        op, tokens = try_parse_operator(tokens)
        if op is not None:
            expression.append(op)
            continue
        literal, tokens = try_parse_string_literal(tokens)
        if literal:
            expression.append(literal)
            continue
        num, tokens = try_parse_numeric_constant(tokens)
        if num is not None:
            expression.append(num)
            continue
        var, tokens = try_parse_variable_name(tokens)
        if var is not None:
            expression.append(var)
            continue
    return (TokenType.EXPRESSION, expression), tokens


def try_parse_output(tokens):
    if tokens:
        if tokens[0].lower() in ["say", "shout", "whisper", "scream"]:
            expr, tokens = try_parse_expression(tokens[1:])
            if expr is not None:
                return (TokenType.OUTPUT, expr), tokens
            else:
                raise RockstarSyntaxError("Expected expression after output command")
    return None, tokens


def try_parse_input(tokens):
    if len(tokens) > 2 and tokens[0].lower() == "listen" and tokens[1] == "to":
        varname, tokens = try_parse_variable_name(tokens[2:])
        if varname is not None:
            return (TokenType.INPUT, varname), tokens
        else:
            raise RockstarSyntaxError("Expected variable after output command")
    return None, tokens


def tokenize(source):
    """ Converts a string, to a list of strings. """
    class State(Enum):
        NORMAL = 0,
        IN_COMMENT = 1,
        IN_STRING = 2
    tokens = []
    state = State.NORMAL
    last_token_start = 0
    for i, c in enumerate(source):
        if state == State.NORMAL:
            if c.isspace():
                tokens.append(source[last_token_start:i].strip())
                last_token_start = i + 1
            if c == ",":
                tokens.append(source[last_token_start:i].strip())
                tokens.append(",")
                last_token_start = i + 1
            if c == "(":
                state = State.IN_COMMENT
                tokens.append(source[last_token_start:i].strip())
                last_token_start = i + 1
            if c == "\"":
                state = State.IN_STRING
                tokens.append(source[last_token_start:i].strip())
                last_token_start = i
        elif state == State.IN_STRING:
            if c == "\"":
                state = State.NORMAL
                tokens.append(source[last_token_start:i + 1])
                last_token_start = i + 1
        elif state == State.IN_COMMENT:
            if c == ")":
                state = State.NORMAL
                last_token_start = i + 1
    tokens.append(source[last_token_start:].strip())
    return list(filter(lambda x: x, tokens))


# TODO:
# functions
# arrays
# strings
def parse_line(source):
    """ Parse a single line of source code. """
    if source and source[0].islower():
        raise RockstarSyntaxError("Line doesn't start with capital letter")

    # TODO(ed): Can this be made neater somehow?
    mod = source[:]
    if "(" in mod or ")" in mod:
        if "(" in mod and ")" in mod:
            start = mod.index("(")
            end = mod.index(")")
            if start < end:
                mod = mod[:start] + mod[end+1:]
            else:
                raise RockstarSyntaxError("Invalid comment")
        else:
            raise RockstarSyntaxError("Invalid comment")

    mod = mod.replace("'s ", " is ")
    mod = mod.replace("'", "")

    # TODO(ed): This can be made a lot better...
    tokens = tokenize(mod)
    if not tokens:
        return (TokenType.END, )
    output, tokens = try_parse_output(tokens)
    if output is not None:
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return output

    inpu, tokens = try_parse_input(tokens)
    if inpu is not None:
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return inpu

    if tokens[0] == "Put":
        tokens = tokens[1:]
        expr_tokens = tokens[:tokens.index("into")]
        tokens = tokens[tokens.index("into"):]
        exprs, _ = try_parse_expression(expr_tokens)
        if exprs is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        if tokens[0] != "into":
            raise RockstarSyntaxError("Expected \"into\" after variable in assignment.")
        tokens = tokens[1:]
        varname, tokens = try_parse_variable_name(tokens)
        if varname is None:
            raise RockstarSyntaxError("Expected variable in assignment.")
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return TokenType.ASSIGNMENT, varname, exprs

    if tokens[0] == "Let":
        tokens = tokens[1:]
        varname, tokens = try_parse_variable_name(tokens)
        if varname is None:
            raise RockstarSyntaxError("Expected variable in assignment.")
        if tokens[0] not in ["be", "is", "are", "were", "was"]:
            raise RockstarSyntaxError("Expected \"into\" after variable in assignment.")

        tokens = tokens[1:]
        exprs, tokens = try_parse_expression(tokens)
        if exprs is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return TokenType.ASSIGNMENT, varname, exprs

    if tokens[0] == "If":
        tokens = tokens[1:]
        expr, tokens = try_parse_expression(tokens)
        if expr is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        return TokenType.IF, expr

    if tokens[0] == "Until":
        tokens = tokens[1:]
        expr, tokens = try_parse_expression(tokens)
        if expr is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        return TokenType.LOOP, False, expr

    if tokens[0] == "While":
        tokens = tokens[1:]
        expr, tokens = try_parse_expression(tokens)
        if expr is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        return TokenType.LOOP, True, expr

    if tokens[0] == "Turn":
        tokens = tokens[1:]
        if tokens[0] in ["down", "up"]:
            way = tokens[0]
            var, tokens = try_parse_variable_name(tokens[1:])
        else:
            var, tokens = try_parse_variable_name(tokens)
            way = tokens[0]
            tokens = tokens[1:]
        if way not in ["down", "up"]:
            raise RockstarSyntaxError("Expected \"up\" or \"down\" for turn statement.")
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return TokenType.TURN, way, var

    if tokens[1] == "takes":
        # It's a function definition
        name = tokens[0]
        tokens = tokens[2:]
        arguments = []
        while tokens:
            var, tokens = try_parse_variable_name(tokens)
            if var is None:
                raise RockstarSyntaxError("Failed to read argument list.")
            arguments.append(var)
            if tokens and tokens[0] in [",", "and", "n"]:
                tokens = tokens[1:]
                if tokens and tokens[0] == "and":
                    tokens = tokens[1:]
            elif tokens:
                raise RockstarSyntaxError("Invalid syntax for function {}".format(name))
        return TokenType.FUNCTION, name, arguments

    if tokens[0] == "Give":
        # Maybe allow more syntax here?
        if tokens[1] != "back":
            raise RockstarSyntaxError("Invalid \"Give back\" statement")
        expr, tokens = try_parse_expression(tokens[2:])
        if expr is None:
            raise RockstarSyntaxError("Expected expression in \"Give back\" statement")
        return TokenType.RETURN, expr

    # TODO(ed): Assumes that if nothing is said, it's poetic.
    varname, tokens = try_parse_variable_name(tokens)
    if varname is not None:
        if tokens[0] in ["be", "is", "are", "were", "was"]:
            tokens = tokens[1:]

            exprs = parse_poetic_number_literals(tokens)
            if exprs is None:
                raise RockstarSyntaxError("Expected expression in assignment.")

            return TokenType.ASSIGNMENT, varname, (TokenType.EXPRESSION, [exprs])

        if tokens[0] in ["says", "shouts", "screams", "wispers"]:
            # Poetic string literals
            literal = source.split(tokens[0])[1][1:]
            expr = (TokenType.CONSTANT, literal)
            return TokenType.ASSIGNMENT, varname, (TokenType.EXPRESSION, [expr])
    raise RockstarSyntaxError("Cannot parse line")


def treeify(statements, in_func=False):
    ast = []
    while statements:
        first = statements[0]
        statements = statements[1:]
        if type_is(first, TokenType.END):
            break
        if type_is(first, TokenType.RETURN):
            if not in_func:
                raise RockstarSyntaxError("\"Give back\" statement has to be in function")
            ast.append(first)
            break
        if type_is(first, TokenType.IF):
            t, expr = first
            block, statements = treeify(statements)
            first = t, expr, block

        if type_is(first, TokenType.LOOP):
            t, res, expr = first
            block, statements = treeify(statements)
            first = t, res, expr, block

        if type_is(first, TokenType.FUNCTION):
            t, name, args = first
            block, statements = treeify(statements, True)
            first = t, name, args, block

        ast.append(first)
    return ast, statements


def parse_source(source, source_file_name):
    """ Parses a source file into an AST for the Rockstar language. """
    success = True
    tokens = []
    for line_nr, line in enumerate(source.split("\n")):
        try:
            if tokenized := parse_line(line):
                tokens.append(tokenized)
        except RockstarSyntaxError as e:
            e.add_info(source_file_name, line_nr, line)
            # TODO(ed): Add some form of loggin? Print to stderr?
            success = False
            print(str(e))
    if not success:
        return None, success
    # Restructure the list into an actual tree..
    left = tokens
    ast = []
    while left:
        statement, left = treeify(left)
        if statement:
            ast += statement
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(ast)
    return ast, success


# EVAL BELLOW HERE.


def eval_statement(statement, variables, function_table):
    """ Evaluates a statement. """
    if type_is(statement, TokenType.ASSIGNMENT):
        eval_assignment(statement[1], statement[2], variables, function_table)
    elif type_is(statement, TokenType.OUTPUT):
        print(eval_expression(statement[1], variables, function_table))
    elif type_is(statement, TokenType.INPUT):
        variables[statement[1][1]] = input()
    elif type_is(statement, TokenType.IF):
        res = eval_expression(statement[1], variables, function_table)
        if res:
            eval_statements(statement[2], variables)
    elif type_is(statement, TokenType.LOOP):
        _, comp, expr, rest = statement
        while eval_expression(expr, variables, function_table) == comp:
            eval_statements(rest, variables)

    elif type_is(statement, TokenType.TURN):
        _, kind, var = statement
        val = eval_evalable(var, variables)
        if kind == "up":
            val = round(val + 0.5)
        else:
            val = round(val - 0.5)
        variables[var[1]] = val
    else:
        print(statement)
        raise ValueError("Invalid statement")


def type_is(exprs, typ):
    return exprs[0] == typ


def eval_evalable(evalable, variables):
    t, evl = evalable
    if t == TokenType.CONSTANT:
        return evl
    if t == TokenType.VARIABLE:
        if evl not in variables:
            raise ValueError("Variable used before asignment {}".format(evl))
        return variables[evl]
    raise ValueError("Cannot eval of type {}".format(t))


def eval_function_call(call, variables, function_table):
    """ Run a function and return the result. """
    if call[1] not in function_table:
        raise ValueError("Cannot find function of name {}".format(call[1]))
    func = function_table[call[1]]
    local_vars = {k[1]: eval_expression(v, variables, function_table)
                   for (k, v) in zip(func[2], call[2])}
    return eval_statements(func[3], local_vars, function_table.copy())


def eval_expression(expression, variables, function_table):
    """ Evaluates an expression. """
    # TODO(ed): This is far from enough complexity to evaluate.
    # There needs to be some way to do the order of operations easily for this.
    assert type_is(expression, TokenType.EXPRESSION), "Cannot eval non-expression ({})".format(expression)
    _, expr = expression
    if type_is(expr[0], TokenType.CALL):
        left = eval_function_call(expr[0], variables, function_table)
    else:
        left = eval_evalable(expr[0], variables)
    expr = expr[1:]
    while expr:
        op = expr[0]
        expr = expr[1:]

        if type_is(expr[0], TokenType.CALL):
            right = eval_function_call(expr[0], variables, function_table)
        else:
            right = eval_evalable(expr[0], variables)

        expr = expr[1:]
        assert type_is(op, TokenType.OPERATOR), "Invalid syntax tree"
        if op[1] == "add":
            left += right
        if op[1] == "sub":
            left -= right
        if op[1] == "mul":
            left *= right
        if op[1] == "div":
            left /= right
        if op[1] == "eq":
            left = left == right
        if op[1] == "neq":
            left = left != right
        if op[1] == "lt":
            left = left < right
        if op[1] == "leq":
            left = left <= right
        if op[1] == "gt":
            left = left > right
        if op[1] == "geq":
            left = left >= right
    return left


def eval_assignment(variable, expression, variables, function_table):
    # ...
    variables[variable[1]] = eval_expression(expression, variables, function_table)


def eval_statements(statements, variables={}, function_table={}):
    for statement in statements:
        # TODO(ed): This is kinda messy... I was thinking of
        # splitting this into a different step but I don't know.
        if type_is(statement, TokenType.FUNCTION):
            function_table[statement[1]] = statement
        elif type_is(statement, TokenType.RETURN):
            return eval_expression(statement[1], variables, function_table)
        else:
            eval_statement(statement, variables, function_table)


def run_program(ast):
    """ Runs a rockstar program. """
    variables = {}
    eval_statements(ast, variables)
    return variables

if __name__ == "__main__":
    print("args: ", sys.argv)
    filename = sys.argv[1]
    with open(filename) as source_file:
        ast, success = parse_source(source_file.read(), filename)
        if not success:
            print("Failed to parse input file")
        else:
            # print("\n".join(str(x) for x in ast))
            print("-------------------")
            state = run_program(ast)
            print("-------------------")
            print("state: ", state)
