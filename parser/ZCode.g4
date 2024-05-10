// STUDENT ID: 2153650
grammar ZCode;

@lexer::header {
from lexererr import *
}

options {
    language=Python3;
}

program: NEWLINE* manydecl EOF;

newlines
    : NEWLINE newlines
    | NEWLINE
    ;

manydecl
    : decl manydecl
    | decl
    ;

decl
    : vardecl
    | funcdecl
    ;

// variable declare
vardecl
    : scalar_decl newlines
    | array_decl newlines
    ;

array_decl
    : primitive_type IDENTIFIER LB dim_list RB (ASSIGN expr)?
    ;

dim_list
    : NUM_LIT COMMA dim_list
    | NUM_LIT
    ;

scalar_decl
    : implicit_decl
    | type_decl
    ;

type_decl
    : primitive_type IDENTIFIER (ASSIGN expr)?
    ;

implicit_decl
    : VAR IDENTIFIER ASSIGN expr
    | DYNAMIC IDENTIFIER (ASSIGN expr)?
    ;

// fucntion declare
funcdecl
    : FUNC IDENTIFIER LPAR param_list RPAR body
    ;

param_list
    : param_prime
    |
    ;

param_prime
    : param COMMA param_prime
    | param
    ;

param
    : primitive_type IDENTIFIER
    | primitive_type IDENTIFIER LB dim_list RB
    ;

body
    : newlines? (return_stmt | block_stmt)
    | newlines
    ;

block_stmt
    : BEGIN newlines manystmt END newlines
    ;

manystmt
    : manystmt_prime
    |
    ;

manystmt_prime
    : stmt manystmt_prime
    | stmt
    ;

// stmt
stmt
    : vardecl
    | assign_stmt
    | if_stmt
    | for_stmt
    | break_stmt
    | continue_stmt
    | return_stmt
    | funccall_stmt
    | block_stmt
    ;

assign_stmt
    : lhs ASSIGN expr newlines
    ;

lhs
    : IDENTIFIER
    | IDENTIFIER LB expr_list RB
    ;

// if stmt
if_stmt
    : (IF LPAR expr RPAR newlines? stmt) elif_list else_stmt?
    ;

elif_list
    : elif_stmt elif_list
    |
    ;


elif_stmt
    : ELIF LPAR expr RPAR newlines? stmt
    ;

else_stmt
    : ELSE newlines? stmt
    ;
// endif

for_stmt
    : FOR IDENTIFIER UNTIL expr BY expr newlines? stmt
    ;

continue_stmt
    : CONTINUE newlines
    ;

break_stmt
    : BREAK newlines
    ;

return_stmt
    : RET expr? newlines
    ;

// funccall stmt
funccall_stmt
    : funccall newlines
    ;

funccall
    : IDENTIFIER LPAR args_list RPAR
    ;

args_list
    : argsprime
    |
    ;

argsprime
    : expr COMMA argsprime
    | expr
    ;
// end funccall

// expression
expr
    : expr0 CONCAT expr0
    | expr0
    ;

expr0
    : expr1 (EQ | CMPSTR | NEQ | GT | LT | GE | LE) expr1
    | expr1
    ;

expr1
    : expr1 (AND | OR) expr2
    | expr2
    ;

expr2
    : expr2 (PLUS | MINUS) expr3
    | expr3
    ;

expr3
    : expr3 (STAR | DIV | MOD) expr4
    | expr4
    ;

expr4
    : NOT expr4
    | expr5
    ;

expr5
    : MINUS expr5
    | index_expr
    ;

index_expr
    : index_prefix LB index_operators RB
    | factor
    ;

factor
    : literal
    | IDENTIFIER
    | LPAR expr RPAR
    | funccall
    ;

index_prefix
    : IDENTIFIER
    | funccall
    ;

index_operators
    : expr COMMA index_operators
    | expr
    ;
// end of expression

primitive_type
    : NUM
    | STR
    | BOOL
    ;

literal
    : NUM_LIT
    | STR_LIT
    | BOOL_LIT
    | array_literal
    ;

array_literal
    : LB expr_list RB
    ;

expr_list
    : expr COMMA expr_list
    | expr
    ;

/*---------------------------------Lexer--------------------------------- */
// Separators
LPAR
    : '('
    ;

RPAR
    : ')'
    ;

LB
    : '['
    ;

RB
    : ']'
    ;

COMMA
    : ','
    ;

// Keywords
NUM
    : 'number'
    ;

BOOL
    : 'bool'
    ;

STR
    : 'string'
    ;

RET
    : 'return'
    ;

VAR
    : 'var'
    ;

DYNAMIC
    : 'dynamic'
    ;

FUNC
    : 'func'
    ;

FOR
    : 'for'
    ;

UNTIL
    : 'until'
    ;

BY
    : 'by'
    ;

BREAK
    : 'break'
    ;

CONTINUE
    : 'continue'
    ;

IF
    : 'if'
    ;

ELSE
    : 'else'
    ;

ELIF
    : 'elif'
    ;

BEGIN
    : 'begin'
    ;

END
    : 'end'
    ;

NOT
    : 'not'
    ;

AND
    : 'and'
;

OR
    : 'or'
    ;

// Operators
MINUS
    : '-'
    ;

PLUS
    : '+'
    ;

STAR
    : '*'
    ;

DIV
    : '/'
    ;

MOD
    : '%'
    ;

CONCAT
    : '...'
    ;

EQ
    : '='
    ;

NEQ
    : '!='
    ;

LT
    : '<'
    ;

GT
    : '>'
    ;

LE
    : '<='
    ;

GE
    : '>='
    ;

CMPSTR
    : '=='
    ;

ASSIGN
    : '<-'
    ;

COMMENT
    : '##' ~[\r\n]* -> skip
    ;

// Literals
NUM_LIT
    : DIGIT+ ('.' DIGIT*)? EXP?
    ;

STR_LIT
    : ["] (STR_CHAR)* ["]
    {
        self.text = self.text[1:-1]
    }
    ;

BOOL_LIT
    : 'true'
    | 'false'
    ;

fragment DIGIT
    : [0-9]
    ;

fragment EXP
    : [eE] [+-]? DIGIT+
    ;

fragment ESCAPE_STRING
    : '\\' ['bfrnt\\]
    ;

fragment STR_CHAR
    : ~[\r\n\\"]
    | ESCAPE_STRING
    | [']["]
    ;

IDENTIFIER
    : [a-zA-Z_] [a-zA-Z0-9_]*
    ;

NEWLINE
    : ('\n' | '\r\n')
    {
        self.text = '\n'
    }
    ;

// white spaces
WS : [ \t\f\b]+ -> skip;
// Errors

UNCLOSE_STRING
    : '"' STR_CHAR* ('\r\n' | '\n' | EOF)
    {
        if self.text[-1] == '\n':
            raise UncloseString(self.text[1:-1])
        else:
            raise UncloseString(self.text[1:])
    };

ILLEGAL_ESCAPE
    : '"' STR_CHAR* ESCAPE_ILLEGAL
    {
        raise IllegalEscape(self.text[1:])
    }
    ;

ERROR_CHAR
    : .
    {raise ErrorToken(self.text)}
    ;

fragment ESCAPE_ILLEGAL
    : '\\' ~['bfrnt\\]
    | '\r'
    ;