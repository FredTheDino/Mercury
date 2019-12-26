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
    STRING = 9

def is_simple_variable(token):
    """ Checks if a token is a simple variable name """
    if not token: return False
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
                variable_name = (tokens[0] + tokens[1])
                tokens = tokens[2:]
        elif is_proper_variable(tokens[0]):
            proper = [x for x in tokens if is_proper_variable(x)]
            tokens = tokens[len(proper):]
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
        num += sum(map(lambda c: c.isalpha() or c == "-", t))  % 10
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

    return num + (decimal * 10 ** -points)


def try_parse_string_literal(tokens):
    """ Tries to parse out a string literal from the tokens. """
    if tokens and tokens[0].startswith("\"") and tokens[0].startswith("\""):
        return tokens[0], tokens[1:]
    return None, tokens


def try_parse_numeric_constant(tokens):
    """ Tries to parse out a numeric constant from the tokens. """
    try:
        n = int(tokens[0])
        return n, tokens[1:]
    except ValueError:
        return None, tokens


def try_parse_expression(tokens):
    """ Parses an expression. """
    # TODO(ed): This is what's next...
    literal, tokens = try_parse_string_literal(tokens)
    if literal:
        return (TokenType.CONSTANT, literal), tokens
    num, tokens = try_parse_numeric_constant(tokens)
    if num is not None:
        return (TokenType.CONSTANT, num), tokens
    return (TokenType.CONSTANT, -1), []
    # return (TokenType.EXPRESSION, -1), []


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
# loops, while / until
# how to do poetic number literals
# functions
# arrays
# strings
def parse_line(source):
    """ Parse a single line of source code. """
    if source and source[0].islower():
        raise RockstarSyntaxError("Line doesn't start with capital letter")

    # TODO(ed): Can this be made neater somehow?
    if "(" in source or ")" in source:
        if "(" in source and ")" in source:
            start = source.index("(")
            end = source.index(")")
            if start < end:
                source = source[:start] + source[end+1:]
            else:
                raise RockstarSyntaxError("Invalid comment")
        else:
            raise RockstarSyntaxError("Invalid comment")

    source = source.replace("'s ", " is ")
    source = source.replace("'", "")

    # TODO(ed): This can be made a lot better...
    tokens = tokenize(source)
    if not tokens: return (TokenType.END, )
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
        exprs, tokens = try_parse_expression(tokens)
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

    if tokens[0] == "If":
        tokens = tokens[1:]
        expr, tokens = try_parse_expression(tokens)
        if expr is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        return TokenType.IF, expr

    # TODO(ed): Let syntax is confusing in the spec, what is a valid assignment?
    varname, tokens = try_parse_variable_name(tokens)
    if varname is not None:
        if tokens[0] not in ["be", "is", "are", "were", "was"]:
            raise RockstarSyntaxError("Expected 'be' in assignemnt.")
        tokens = tokens[1:]

        if not tokens:
            raise RockstarSyntaxError("Expected expression in assignment. Not end of line.")

        exprs, tokens = try_parse_expression(tokens)
        if exprs is None:
            raise RockstarSyntaxError("Expected expression in assignment.")
        if tokens:
            raise RockstarSyntaxError("Unexpected tokens at end of line")
        return TokenType.ASSIGNMENT, varname, exprs
    raise RockstarSyntaxError("Cannot parse line")


def index_of_all(string, sym):
    """ Returns the index of all symbols in the given string. """
    return [i for i, c in string if c == sym]


def treeify(statements):
    ast = []
    while statements:
        first = statements[0]
        statements = statements[1:]
        if type_is(first, TokenType.END):
            break
        if type_is(first, TokenType.IF):
            t, expr = first
            block, statements = treeify(statements)
            first = t, expr, block
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


def eval_statement(statement, variables):
    """ Evaluates a statement. """
    if type_is(statement, TokenType.ASSIGNMENT):
        eval_assignment(statement[1], statement[2], variables)
    elif type_is(statement, TokenType.OUTPUT):
        print(eval_expression(statement[1], variables))
    elif type_is(statement, TokenType.IF):
        # Assumes true... pretty bad if-statements.
        res = eval_expression(statement[1], variables)
        print("EVAL: ", statement[1], res)
        if res:
            print("true!")
            eval_statements(statement[2], variables)
    else:
        print(statement)
        raise ValueError("Invalid statement")


def type_is(exprs, typ):
    return exprs[0] == typ


def eval_expression(expression, variables):
    """ Evaluates an expression. """
    t, expr = expression
    if t == TokenType.CONSTANT:
        return expr
    if t == TokenType.VARIABLE:
        return variables[expr]
    # assert expression[0] == TokenType.EXPRESSION, "Invalid expression"
    assert False, "Invalid expression!"


def eval_assignment(variable, expression, variables):
    # ...
    variables[variable[1]] = eval_expression(expression, variables)


def eval_statements(statements, variables):
    for statement in statements:
        eval_statement(statement, variables)


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
