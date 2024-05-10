from ZCodeVisitor import ZCodeVisitor
from ZCodeParser import ZCodeParser
from AST import *


class ASTGeneration(ZCodeVisitor):

    def visitProgram(self, ctx: ZCodeParser.ProgramContext):
        return Program(self.visit(ctx.manydecl()))

    def visitManydecl(self, ctx: ZCodeParser.ManydeclContext):
        return [self.visit(ctx.decl())] + self.visit(ctx.manydecl()) if ctx.manydecl() else [self.visit(ctx.decl())]

    def visitDecl(self, ctx: ZCodeParser.DeclContext):
        if ctx.vardecl():
            return self.visit(ctx.vardecl())
        return self.visit(ctx.funcdecl())

    def visitVardecl(self, ctx: ZCodeParser.VardeclContext):
        if ctx.scalar_decl():
            return self.visit(ctx.scalar_decl())
        return self.visit(ctx.array_decl())

    def visitScalar_decl(self, ctx: ZCodeParser.Scalar_declContext):
        if ctx.implicit_decl():
            return self.visit(ctx.implicit_decl())
        return self.visit(ctx.type_decl())

    def visitImplicit_decl(self, ctx: ZCodeParser.Implicit_declContext):
        if ctx.VAR():
            return VarDecl(Id(ctx.IDENTIFIER().getText()), None, 'var', self.visit(ctx.expr()))
        init = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(Id(ctx.IDENTIFIER().getText()), None, 'dynamic', init)

    def visitType_decl(self, ctx: ZCodeParser.Type_declContext):
        init = self.visit(ctx.expr()) if ctx.expr() else None
        return VarDecl(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.primitive_type()), None, init)

    def visitArray_decl(self, ctx: ZCodeParser.Array_declContext):
        init = self.visit(ctx.expr()) if ctx.expr() else None
        arrtype = ArrayType(self.visit(ctx.dim_list()), self.visit(ctx.primitive_type()))
        return VarDecl(Id(ctx.IDENTIFIER().getText()), arrtype, None, init)

    def visitDim_list(self, ctx: ZCodeParser.Dim_listContext):
        return [float(ctx.NUM_LIT().getText())] + self.visit(ctx.dim_list()) if ctx.dim_list() else [float(ctx.NUM_LIT().getText())]

    def visitFuncdecl(self, ctx: ZCodeParser.FuncdeclContext):
        return FuncDecl(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.param_list()), self.visit(ctx.body()))

    def visitParam_list(self, ctx: ZCodeParser.Param_listContext):
        return self.visit(ctx.param_prime()) if ctx.param_prime() else []

    def visitParam_prime(self, ctx: ZCodeParser.Param_primeContext):
        return [self.visit(ctx.param())] + self.visit(ctx.param_prime()) if ctx.param_prime() else [self.visit(ctx.param())]

    def visitParam(self, ctx: ZCodeParser.ParamContext):
        if ctx.dim_list():
            arrtype = ArrayType(self.visit(ctx.dim_list()), self.visit(ctx.primitive_type()))
            return VarDecl(Id(ctx.IDENTIFIER().getText()), arrtype, None, None)
        return VarDecl(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.primitive_type()), None, None)

    def visitBody(self, ctx: ZCodeParser.BodyContext):
        if ctx.return_stmt():
            return self.visit(ctx.return_stmt())
        if ctx.block_stmt():
            return self.visit(ctx.block_stmt())

    def visitReturn_stmt(self, ctx: ZCodeParser.Return_stmtContext):
        expr = self.visit(ctx.expr()) if ctx.expr() else None
        return Return(expr)

    def visitBlock_stmt(self, ctx: ZCodeParser.Block_stmtContext):
        return Block(self.visit(ctx.manystmt()))

    def visitManystmt(self, ctx: ZCodeParser.ManystmtContext):
        return self.visit(ctx.manystmt_prime()) if ctx.manystmt_prime() else []

    def visitManystmt_prime(self, ctx: ZCodeParser.Manystmt_primeContext):
        return [self.visit(ctx.stmt())] + self.visit(ctx.manystmt_prime()) if ctx.manystmt_prime() else [self.visit(ctx.stmt())]

    def visitStmt(self, ctx: ZCodeParser.StmtContext):
        return self.visit(ctx.getChild(0))

    def visitAssign_stmt(self, ctx: ZCodeParser.Assign_stmtContext):
        return Assign(self.visit(ctx.lhs()), self.visit(ctx.expr()))

    def visitLhs(self, ctx: ZCodeParser.LhsContext):
        if ctx.expr_list():
            return ArrayCell(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.expr_list()))
        return Id(ctx.IDENTIFIER().getText())

    def visitIf_stmt(self, ctx: ZCodeParser.If_stmtContext):
        else_stmt = self.visit(ctx.else_stmt()) if ctx.else_stmt() else None
        return If(self.visit(ctx.expr()), self.visit(ctx.stmt()), self.visit(ctx.elif_list()), else_stmt)

    def visitElif_list(self, ctx: ZCodeParser.Elif_listContext):
        return [self.visit(ctx.elif_stmt())] + self.visit(ctx.elif_list()) if ctx.elif_list() else []

    def visitElif_stmt(self, ctx: ZCodeParser.Elif_stmtContext):
        return (self.visit(ctx.expr()), self.visit(ctx.stmt()))

    def visitElse_stmt(self, ctx: ZCodeParser.Else_stmtContext):
        return self.visit(ctx.stmt())

    def visitFor_stmt(self, ctx: ZCodeParser.For_stmtContext):
        return For(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.expr(0)), self.visit(ctx.expr(1)), self.visit(ctx.stmt()))

    def visitContinue_stmt(self, ctx: ZCodeParser.Continue_stmtContext):
        return Continue()

    def visitBreak_stmt(self, ctx: ZCodeParser.Break_stmtContext):
        return Break()

    def visitFunccall_stmt(self, ctx: ZCodeParser.Funccall_stmtContext):
        return self.visit(ctx.funccall())

    def visitFunccall(self, ctx: ZCodeParser.FunccallContext):
        return CallStmt(Id(ctx.IDENTIFIER().getText()), self.visit(ctx.args_list()))

    def visitArgs_list(self, ctx: ZCodeParser.Args_listContext):
        return self.visit(ctx.argsprime()) if ctx.argsprime() else []

    def visitArgsprime(self, ctx: ZCodeParser.ArgsprimeContext):
        return [self.visit(ctx.expr())] + self.visit(ctx.argsprime()) if ctx.argsprime() else [self.visit(ctx.expr())]

    def visitExpr(self, ctx: ZCodeParser.ExprContext):
        if ctx.getChildCount() == 3:
            return BinaryOp(ctx.CONCAT().getText(), self.visit(ctx.expr0(0)),self.visit(ctx.expr0(1)))
        return self.visit(ctx.expr0(0))

    def visitExpr0(self, ctx: ZCodeParser.Expr0Context):
        if ctx.getChildCount() == 3:
            return BinaryOp(ctx.getChild(1).getText(), self.visit(ctx.expr1(0)), self.visit(ctx.expr1(1)))
        return self.visit(ctx.expr1(0))

    def visitExpr1(self, ctx: ZCodeParser.Expr1Context):
        if ctx.getChildCount() == 3:
            return BinaryOp(ctx.getChild(1).getText(), self.visit(ctx.expr1()), self.visit(ctx.expr2()))
        return self.visit(ctx.expr2())

    def visitExpr2(self, ctx: ZCodeParser.Expr2Context):
        if ctx.getChildCount() == 3:
            return BinaryOp(ctx.getChild(1).getText(), self.visit(ctx.expr2()), self.visit(ctx.expr3()))
        return self.visit(ctx.expr3())

    def visitExpr3(self, ctx: ZCodeParser.Expr3Context):
        if ctx.getChildCount() == 3:
            return BinaryOp(ctx.getChild(1).getText(), self.visit(ctx.expr3()), self.visit(ctx.expr4()))
        return self.visit(ctx.expr4())

    def visitExpr4(self, ctx: ZCodeParser.Expr4Context):
        if ctx.getChildCount() == 2:
            return UnaryOp(ctx.NOT().getText(), self.visit(ctx.expr4()))
        return self.visit(ctx.expr5())

    def visitExpr5(self, ctx: ZCodeParser.Expr5Context):
        if ctx.getChildCount() == 2:
            return UnaryOp(ctx.MINUS().getText(), self.visit(ctx.expr5()))
        return self.visit(ctx.index_expr())

    def visitIndex_expr(self, ctx: ZCodeParser.Index_exprContext):
        if ctx.index_prefix():
            return ArrayCell(self.visit(ctx.index_prefix()), self.visit(ctx.index_operators()))
        return self.visit(ctx.factor())

    def visitIndex_prefix(self, ctx: ZCodeParser.Index_prefixContext):
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())
        call_stmt = self.visit(ctx.funccall())
        return CallExpr(call_stmt.name, call_stmt.args) # cast CallStmt to CallExpr

    def visitIndex_operators(self, ctx: ZCodeParser.Index_operatorsContext):
        return [self.visit(ctx.expr())] + self.visit(ctx.index_operators()) if ctx.index_operators() else [self.visit(ctx.expr())]

    def visitFactor(self, ctx: ZCodeParser.FactorContext):
        if ctx.expr():
            return self.visit(ctx.expr())
        if ctx.IDENTIFIER():
            return Id(ctx.IDENTIFIER().getText())
        if ctx.funccall():
            call_stmt = self.visit(ctx.funccall())
            return CallExpr(call_stmt.name, call_stmt.args) # cast CallStmt to CallExpr
        return self.visit(ctx.getChild(0))

    def visitLiteral(self, ctx: ZCodeParser.LiteralContext):
        if ctx.NUM_LIT():
            return NumberLiteral(float(ctx.NUM_LIT().getText()))
        if ctx.STR_LIT():
            return StringLiteral(ctx.STR_LIT().getText())
        if ctx.BOOL_LIT():
            return BooleanLiteral(ctx.BOOL_LIT().getText() == 'true')
        return self.visit(ctx.array_literal())

    def visitArray_literal(self, ctx: ZCodeParser.Array_literalContext):
        return ArrayLiteral(self.visit(ctx.expr_list()))

    def visitExpr_list(self, ctx: ZCodeParser.Expr_listContext):
        return [self.visit(ctx.expr())] + self.visit(ctx.expr_list()) if ctx.expr_list() else [self.visit(ctx.expr())]

    def visitPrimitive_type(self, ctx: ZCodeParser.Primitive_typeContext):
        if ctx.NUM():
            return NumberType()
        if ctx.STR():
            return StringType()
        return BoolType()

