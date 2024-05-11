from Emitter import Emitter, Zcode
from functools import reduce

from Frame import Frame
from abc import ABC
from Visitor import *
from AST import * # fix this when finish


class Foo:
    def __init__(self, partype, rettype):
        self.partype = partype
        self.rettype = rettype

    def __str__(self):
        return 'Foo({},{})'.format(
            ','.join([str(x) for x in self.partype]),
            str(self.rettype)
        )

class Symbol:
    def __init__(self, name, ztype, value=None):
        self.name = name
        self.ztype = ztype
        self.value = value

    def __str__(self):
        return 'Symbol({},{},{})'.format(
            self.name,
            str(self.ztype),
            str(self.value)
        )
    
class IdExtend(Id):
    def __init__(self, name, sym: Symbol):
        super().__init__(name)
        self.sym = sym


class CodeGenerator:
    def __init__(self):
        self.libName = "io"


    def gen(self, ast, path):
        # ast: AST
        # dir_: String

        gc = CodeGenVisitor(ast, path)
        gc.visit(ast, None)


class SubBody():
    def __init__(self, frame, sym):
        self.frame = frame
        self.sym = sym
        self.isGen = False


class Access():
    def __init__(self, frame, sym, isLeft, isFirst=False):
        self.frame = frame
        self.sym = sym
        self.isLeft = isLeft
        self.isFirst = isFirst


class Val(ABC):
    pass


class Index(Val):
    def __init__(self, value):
        self.value = value


class CName(Val):
    def __init__(self, value):
        self.value = value


def haveType(param):
    if param is None:
        return False
    elif type(param) is ArrayType and type(param.eleType) is None:
        return haveType(param.eleType)
    return True

class CodeGenVisitor(BaseVisitor):
    def __init__(self, astTree, path):
        self.astTree = astTree
        self.path = path
        self.className = "ZCodeClass"
        self.emit = Emitter(self.path + "/" + self.className + ".j")
        self.currentFunc = None
        self.ret = False
        self.gen = False
        self.globe = False
        self.libName = "io"
        self.funcList = {
            "readNumber" :Symbol("readNumber", Foo(list(), NumberType()), CName(self.libName)),
            "readBool" :Symbol("readBool", Foo(list(),BoolType()), CName(self.libName)),
            "writeNumber": Symbol("writeNumber", Foo([NumberType()], VoidType()), CName(self.libName)),
            "writeBool": Symbol("writeBool", Foo([BoolType()], VoidType()), CName(self.libName)),
            "writeString": Symbol("writeString", Foo([StringType()], VoidType()), CName(self.libName))
        }

    def setType(self, operand: Symbol, typ):
        if type(operand.ztype) is Foo:
            operand.ztype.rettype = typ
        else:
            operand.ztype = typ

    def setArray(self, base, rhs):
        if len(base.size) == 1:
            for x in rhs:
                self.setType(x, base.eleType)
        else:
            for x in rhs:
                if type(x) is list:
                    self.setArray(ArrayType(base.size[1:], base.eleType), x)
                else:
                    self.setType(x, ArrayType(base.size[1:], base.eleType))


    def inferType(self, l, r):
        if isinstance(l, Symbol) and isinstance(r, Symbol):
            raise "No Type T_T"
        if type(r) is list:
            self.setArray(l, r)
        elif isinstance(l, Symbol):
            self.setType(l, r)
        elif isinstance(r, Symbol):
            self.setType(r, l)

    def visitProgram(self, ast, c):
        self.emit.printout(self.emit.emitPROLOG(self.className,"java.lang.Object"))

        
        # infer type first
        e = [[]]
        for x in ast.decl:
            self.visit(x, e)
        
        # generate global variable
        self.gen = True
        for x in ast.decl:
            if isinstance(x, VarDecl):
                print(x.name.sym)
                self.emit.printout(self.emit.emitATTRIBUTE(x.name.name, x.name.sym.ztype, False, self.className))
                x.name.sym.value = CName(self.className)


        frame = Frame("<clinit>", VoidType)
        self.emit.printout(self.emit.emitMETHOD("<clinit>", Foo([], VoidType()), True, frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        self.globe = True
        for x in ast.decl:
            if isinstance(x, VarDecl) and (x.varInit or type(x.name.sym.ztype) is ArrayType):
                self.visit(x, Access(frame, None, False))
        self.globe = False
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame)) 
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()

        # generate method
        for x in ast.decl:
            if isinstance(x, FuncDecl):
                self.visit(x, None)

        
        # generate default constructor
        frame = Frame("<init>", VoidType)
        self.emit.printout(self.emit.emitMETHOD(lexeme="<init>", in_=Foo([], VoidType()), isStatic=False, frame=frame))
        frame.enterScope(True)
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        self.emit.printout(self.emit.emitVAR(frame.getNewIndex(), "this", Zcode(), frame.getStartLabel(), frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitREADVAR("this", self.className, 0, frame))
        self.emit.printout(self.emit.emitINVOKESPECIAL(frame))
        self.emit.printout(self.emit.emitRETURN(VoidType(), frame))   
        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
    
   
        self.emit.emitEPILOG()
        print(''.join(self.emit.buff))
        return c


    def visitVarDecl(self, ast: VarDecl, param):
        if not self.gen:
            param[0].append(Symbol(ast.name.name, ast.varType, None))
            ast.name.__class__ = IdExtend
            ast.name.sym = param[0][-1]

            if ast.varInit:
                rhs = self.visit(ast.varInit, param)
                lhs = self.visit(ast.name, param)
                self.inferType(lhs, rhs)

        else:
            if self.globe:
                code = ""
                if ast.varInit:
                    frame = param.frame
                    code += self.visit(ast.varInit, Access(frame, None, False))[0]
                    code += self.visit(ast.name, Access(frame, None, True))[0]
                else:
                    code += self.initARRAY(ast, param)

                self.emit.printout(code)
            else:
                print("vardecl",ast.name.name)
                frame = param.frame
                idx = frame.getNewIndex()
                code = self.emit.emitVAR(
                    idx, 
                    ast.name.name, 
                    ast.name.sym.ztype, 
                    frame.getStartLabel(), 
                    frame.getEndLabel(), 
                    frame
                )
                ast.name.sym.value = Index(idx)
                if ast.varInit is None and type(ast.name.sym.ztype) is ArrayType:
                    code += self.initARRAY(ast, param)
                self.emit.printout(code)
                if ast.varInit:
                    code = self.visit(ast.varInit, Access(frame, None, isLeft=False))[0]
                    code += self.visit(ast.name, Access(frame, None, isLeft=True))[0]
                    self.emit.printout(code)
    
    def visitFuncDecl(self, ast: FuncDecl, param):
        if not self.gen:
            if ast.body is None:
                foo = Foo(list(map(lambda x: x.varType, ast.param)), None)
                self.funcList[ast.name.name] = Symbol(ast.name, foo, None)
            else:
                env = [[]] + param
                for x in ast.param:
                    self.visit(x, env)
 
                self.ret = False
                method = self.funcList.get(ast.name.name)
                if method:
                    if haveType(method.foo.rettype):
                        return
                    else:
                        self.currentFunc = method
                else:
                    self.currentFunc = Symbol(ast.name.name, Foo(list(map(lambda x: x.varType, ast.param)), None), CName(self.className))    
                    self.funcList[ast.name.name] = self.currentFunc
                self.visit(ast.body, env)
                if not self.ret: self.currentFunc.ztype.rettype = VoidType()         
        else:
            func = self.funcList.get(ast.name.name)
            if func is None:
                raise "No function"
            frame = Frame(ast.name.name, func.ztype.rettype)
            self.genMETHOD(ast, param, frame)

    def visitId(self, ast, param):
        if not self.gen:
            for env in param:
                for x in env:
                    if x.name == ast.name:
                        if not isinstance(ast, IdExtend):
                            ast.__class__ = IdExtend
                            ast.sym = x
                        if haveType(x.ztype):
                            return x.ztype
                        else:
                            return x
            raise "No variable"
        else:
            sym = ast.sym
            if param.isLeft:
                if type(sym.value) is Index:
                    return self.emit.emitWRITEVAR(sym.name, sym.ztype, sym.value.value, param.frame), sym.ztype
                else:
                    return self.emit.emitPUTSTATIC(f"{sym.value.value}.{sym.name}", sym.ztype, param.frame), sym.ztype
            else:
                if type(sym.value) is Index:
                    return self.emit.emitREADVAR(sym.name, sym.ztype, sym.value.value, param.frame), sym.ztype
                else:
                    return self.emit.emitGETSTATIC(f"{sym.value.value}.{sym.name}", sym.ztype, param.frame), sym.ztype

    def genCall(self, ast, param):
        func = self.funcList.get(ast.name.name)
        if func is None:
            raise "No function"
        code = ""
        for x in ast.args:
            code += self.visit(x, Access(param.frame, None, False))[0]
        code += self.emit.emitINVOKESTATIC(f"{func.value.value}/{func.name}", func.ztype, param.frame)
        return code, func.ztype.rettype

    def visitCallExpr(self, ast: CallExpr, param):
        if not self.gen:
            func = self.funcList.get(ast.name.name)
            args = [self.visit(arg, param) for arg in ast.args]
            for x,y in zip(args, func.ztype.partype):
                if isinstance(x, Symbol):
                    x.ztype = y

            return func.ztype.rettype if func.ztype.rettype else func
        else:
            return self.genCall(ast, param)
            
    def visitCallStmt(self, ast: CallStmt, param):
        if not self.gen:
            func = self.funcList.get(ast.name.name)
            args = [self.visit(arg, param) for arg in ast.args]
            for x,y in zip(args, func.ztype.partype):
                if isinstance(x, Symbol):
                    x.ztype = y
            return VoidType()
        else:
            self.emit.printout(self.genCall(ast, param)[0])
            
            
    def visitIf(self, ast, param):
        if not self.gen:
            cond = self.visit(ast.expr, param)
            if isinstance(cond, Symbol):
                cond.ztype = BoolType()
            self.visit(ast.thenStmt, param)

            for x,y in ast.elifStmt:
                cond = self.visit(x, param)
                if isinstance(cond, Symbol):
                    cond.ztype = BoolType()
                self.visit(y, param)
    
            if ast.elseStmt:
                self.visit(ast.elseStmt, param)
        else:
            frame = param.frame
            haveElse = True if ast.elseStmt else False
            haveElif = True if len(ast.elifStmt) != 0 else False
            code = self.visit(ast.expr, Access(frame, None, False))[0]
            
            exitIf = frame.getNewLabel()
            elifLabel = frame.getNewLabel() if haveElif else None
            elseLabel = frame.getNewLabel() if haveElse else None
            if haveElse or haveElif:
                code += self.emit.emitIFTRUE(elifLabel if elifLabel else elseLabel, frame)
            else:
                code += self.emit.emitIFTRUE(exitIf, frame)

            self.emit.printout(code)
            self.visit(ast.thenStmt, Access(frame, None, False))
            self.emit.printout(self.emit.emitGOTO(exitIf, frame))

            if haveElif:
                self.emit.printout(self.emit.emitLABEL(elifLabel, frame))
                for i in range(len(ast.elifStmt)-1):
                    cond, stmt = ast.elifStmt[i]
                    nextIf = frame.getNewLabel()
                    
                    code = self.visit(cond, Access(frame, None, False))[0]
                    code += self.emit.emitIFTRUE(nextIf, frame)

                    self.emit.printout(code)
                    self.visit(stmt, Access(frame, None, False))

                    code += self.emit.emitGOTO(exitIf, frame)
                    code += self.emit.emitLABEL(nextIf, frame)
                    self.emit.printout(code)
                cond, stmt = ast.elifStmt[-1]   
                code = self.visit(cond, Access(frame, None, False))[0]
                code += self.emit.emitIFTRUE(elseLabel if elseLabel else exitIf, frame)
                self.emit.printout(code)
                self.visit(stmt, Access(frame, None, False))
                self.emit.printout(self.emit.emitGOTO(exitIf, frame))
            
            if haveElse:
                self.emit.printout(self.emit.emitLABEL(elseLabel, frame))
                self.visit(ast.elseStmt, Access(frame, None, False))

            self.emit.printout(self.emit.emitLABEL(exitIf, frame))

            
            
    def visitFor(self, ast: For, param):
        if not self.gen:
            counter = self.visit(ast.name, param)
            if isinstance(counter, Symbol):
                counter.ztype = NumberType()

            cond = self.visit(ast.condExpr, param)
            if isinstance(cond, Symbol):
                cond.ztype = BoolType()

            upd = self.visit(ast.updExpr, param)
            if isinstance(upd, Symbol):
                upd.ztype = NumberType()

            self.visit(ast.body, param)

        else:
            frame = param.frame
            frame.enterLoop()
            cont = frame.getContinueLabel()
            brk = frame.getBreakLabel()
            cond = frame.getNewLabel()
            
            idx = frame.getNewIndex()
            code = self.visit(ast.name, Access(param.frame, None, False))[0]
            code += self.emit.emitDUP(frame)
            code += self.emit.emitWRITEVAR("tmp", NumberType(), idx, frame)

            code += self.emit.emitLABEL(cond, frame)
            code += self.visit(ast.condExpr, Access(frame, None, False))[0]
            code += self.emit.emitIFTRUE(brk, frame)
            self.emit.printout(code)

            self.visit(ast.body, SubBody(frame, None))
            
            self.emit.printout(self.emit.emitLABEL(cont, frame))
            updExpr = Assign(ast.name, BinaryOp("+", ast.name, ast.updExpr))
            self.visit(updExpr, Access(frame, None, False))
            code = self.emit.emitGOTO(cond, frame)

            code += self.emit.emitLABEL(brk, frame)
            frame.exitLoop()
            code += self.emit.emitREADVAR("tmp", NumberType(), idx, frame)
            code += self.visit(ast.name, Access(frame, None, True))[0]
            self.emit.printout(code)

    def visitReturn(self, ast: Return, param):
        if not self.gen:
            self.ret = True
            rettype = self.visit(ast.expr, param) if ast.expr else VoidType()

            if isinstance(rettype, Symbol):
                rettype.ztype = self.currentFunc.ztype.rettype
            if self.currentFunc.ztype.rettype is None:
                self.currentFunc.ztype.rettype = rettype
        else:
            code = self.visit(ast.expr, Access(param.frame, None, False))[0]
            code += self.emit.emitRETURN(param.frame.returnType, param.frame)
            self.emit.printout(code)
 
    def visitAssign(self, ast: Assign, param):
        if not self.gen:
            rhs = self.visit(ast.rhs, param)
            lhs = self.visit(ast.lhs, param)
            self.inferType(lhs, rhs)
        else:
            if type(ast.lhs) is ArrayCell:
                left, typ = self.visit(ast.lhs, Access(param.frame, None, True))
                right = self.visit(ast.rhs, Access(param.frame, None, False))[0]
                code = left + right
                code += self.emit.emitASTORE(typ, param.frame)
                self.emit.printout(code)
            else:
                code = self.visit(ast.rhs, Access(param.frame, None, False))[0]
                code += self.visit(ast.lhs, Access(param.frame, None, True))[0]
                self.emit.printout(code)

    def visitBinaryOp(self, ast: BinaryOp, param):
        op = ast.op
        if not self.gen:
            l = self.visit(ast.left, param)
            r = self.visit(ast.right, param)
            if op in ['+', '-', '*', '/', '%']:
                self.inferType(l, NumberType())
                self.inferType(r, NumberType())
                return NumberType()
            elif op in ['=', '!=', '<', '>', '>=', '<=']:
                self.inferType(l, NumberType())
                self.inferType(r, NumberType())
                return BoolType()
            elif op in ['and', 'or']:
                self.inferType(l, BoolType())
                self.inferType(r, BoolType())
                return BoolType()
            elif op in ['==']:
                self.inferType(l, StringType())
                self.inferType(r, StringType())
                return BoolType()
            elif op in ['...']:
                self.inferType(l, StringType())
                self.inferType(r, StringType())
                return StringType()
        else:
            code = self.visit(ast.left, param)[0]
            code += self.visit(ast.right, param)[0]
            ret = None
            if op in ['+', '-']:
                code += self.emit.emitADDOP(op, NumberType(), param.frame)
                ret = NumberType()
            elif op in ["*", "/"]:
                code += self.emit.emitMULOP(op, NumberType(), param.frame)
                ret = NumberType()
            elif op in ["%"]:
                code += self.emit.emitMOD(param.frame) # implement mod
                ret = NumberType()
            elif op in ["and"]:
                code += self.emit.emitANDOP(param.frame)
                ret = BoolType()
            elif op in ["or"]:
                code += self.emit.emitOROP(param.frame)
                ret = BoolType()
            elif op in ['=', '!=', '<', '>', '>=', '<=']:
                code += self.emit.emitREOP(op, NumberType(), param.frame)
                ret = BoolType()
            elif op in ['==']:
                code += self.emit.emitINVOKEVIRTUAL("java/lang/String.equals", Foo([StringType()],BoolType()), param.frame)
                ret = BoolType()
            elif op in ['...']:
                code += self.emit.emitINVOKEVIRTUAL("java/lang/String.concat", Foo([StringType()],StringType()), param.frame)
                ret = StringType()
            return code, ret


    def visitUnaryOp(self, ast: UnaryOp, param):
        if not self.gen:
            if ast.op == '-':
                self.inferType(ast.operand, NumberType())
                return NumberType()
            elif ast.op == 'not':
                self.inferType(ast.operand, BoolType())
                return BoolType()
        else:
            if ast.op == '-':
                return self.visit(ast.operand, param)[0] + self.emit.emitNEGOP(NumberType(), param.frame), NumberType()
            elif ast.op == 'not':
                return self.visit(ast.operand, param)[0] + self.emit.emitNOT(param.frame), BoolType()

    def visitArrayLiteral(self, ast: ArrayLiteral, param):
        if not self.gen:
            base = None
            for x in ast.value:
                tmp = self.visit(x, param)
                if base is None and isinstance(tmp, (BoolType, StringType, NumberType, ArrayType)):
                    base = tmp
                    break

            if base is None:
                return [self.visit(x, param) for x in ast.value]
            
            for x in ast.value:
                self.inferType(x, base)

        
            if isinstance(base, (BoolType, StringType, NumberType)):
                return ArrayType([len(ast.value)], base)
            return ArrayType([float(len(ast.value))] + base.size, base.eleType)
        else:
            base = None
            param.isLeft = False
            for x in ast.value:
                _,tmp = self.visit(x, param)
                if base is None and isinstance(tmp, (BoolType, StringType, NumberType, ArrayType)):
                    base = tmp
                    break

            if base is None:
                raise "No type"
            
            if isinstance(base, (BoolType, StringType, NumberType)):
                code = self.emit.emitPUSHICONST(len(ast.value), param.frame)
                code += self.emit.emitNEWARRAY(base, param.frame)
                for idx, x in enumerate(ast.value):
                    code += self.emit.emitDUP(param.frame)
                    code += self.emit.emitPUSHICONST(idx, param.frame)
                    code += self.visit(x, param)[0]
                    code += self.emit.emitASTORE(base, param.frame)
                return code, ArrayType([len(ast.value)], base)
            else:
                code = self.emit.emitPUSHICONST(len(ast.value), param.frame)
                code += self.emit.emitANEWARRAY(base, param.frame)
                for idx, x in enumerate(ast.value):
                    code += self.emit.emitDUP(param.frame)
                    code += self.emit.emitPUSHICONST(idx, param.frame)
                    code += self.visit(x, param)[0]
                    print("base",base)
                    code += self.emit.emitASTORE(base, param.frame) # fix please
                return code, ArrayType([len(ast.value)] + base.size, base.eleType)
    
    def visitArrayCell(self, ast: ArrayCell, param):
        if not self.gen:
            arr = self.visit(ast.arr, param)
            for idx in ast.idx:
                self.inferType(idx, NumberType())
            if len(ast.idx) == len(arr.size):
                return arr.eleType
            else:
                return ArrayType(arr.size[len(ast.idx):], arr.eleType)
        else:
            c1, base = self.visit(ast.arr, Access(param.frame, None, False))
            for i in range(len(ast.idx)-1):
                c1 += self.visit(ast.idx[i], Access(param.frame, None, False))[0]
                c1 += self.emit.emitF2I(param.frame)
                c1 += self.emit.emitALOAD(ArrayType([],None), param.frame)
            c1 += self.visit(ast.idx[-1], Access(param.frame, None, False))[0]
            c1 += self.emit.emitF2I(param.frame)
            if param.isLeft:
                if len(ast.idx) == len(base.size):
                    return c1, base.eleType
                else:
                    return c1, ArrayType(base.size[len(ast.idx):], base.eleType)
            else:
                if len(ast.idx) == len(base.size):
                    c1 += self.emit.emitALOAD(base.eleType, param.frame)
                    return c1, base.eleType
                else:
                    c1 += self.emit.emitALOAD(ArrayType([],None), param.frame)
                    return c1, ArrayType(base.size[len(ast.idx):], base.eleType)

    
    def visitBlock(self, ast: Block, param):
        if not self.gen:
            env = [[]] + param
            for x in ast.stmt:
                self.visit(x, env)
        else:
            param.frame.enterScope(False)
            self.emit.printout(self.emit.emitLABEL(param.frame.getStartLabel(), param.frame))
            for x in ast.stmt:
                self.visit(x, SubBody(param.frame, None))
            self.emit.printout(self.emit.emitLABEL(param.frame.getEndLabel(), param.frame))
            param.frame.exitScope()

    def visitBreak(self, ast: Break, param):
        if not self.gen:
            return
        else:
            self.emit.printout(self.emit.emitGOTO(param.frame.getBreakLabel(), param.frame))

    def visitContinue(self, ast: Continue, param):
        if not self.gen:
            return
        else:
            self.emit.printout(self.emit.emitGOTO(param.frame.getContinueLabel(), param.frame))
    
    def visitNumberType(self, ast: NumberType, param):
        if not self.gen:
            return ast
        else:
            pass

    def visitBoolType(self, ast: BoolType, param):
        if not self.gen:
            return ast
        else:
            pass

    def visitStringType(self, ast: StringType, param):
        if not self.gen:
            return ast
        else:
            pass

    def visitArrayType(self, ast: ArrayType, param):
        if not self.gen:
            return ast
        else:
            pass

    def visitNumberLiteral(self, ast: NumberLiteral, param):
        if not self.gen:
            return NumberType()
        else:
            return self.emit.emitPUSHCONST(ast.value, NumberType(), param.frame), NumberType()

    def visitStringLiteral(self, ast: StringLiteral, param):
        if not self.gen:
            return StringType()
        else:
            return self.emit.emitPUSHCONST(f'"{ast.value}"', StringType(), param.frame), StringType()

    def visitBooleanLiteral(self, ast: BooleanLiteral, param):
        if not self.gen:
            return BoolType()
        else:
            return self.emit.emitPUSHCONST(ast.value, BoolType(), param.frame), BoolType()
        
    def visitIdExtend(self, ast, param):
        return self.visitId(ast, param)
    
    def initARRAY(self, ast, param):
        sym = ast.name.sym
        code = ""
        if len(sym.ztype.size) == 1:
            code = self.emit.emitPUSHICONST(int(sym.ztype.size[0]), param.frame)
            code += self.emit.emitNEWARRAY(sym.ztype.eleType, param.frame)
        else:
            for i in sym.ztype.size:
                code += self.emit.emitPUSHICONST(int(i), param.frame)
            code += self.emit.emitMULTIANEWARRAY(sym.ztype, param.frame)

        if type(sym.value) is Index:
            code += self.emit.emitWRITEVAR(sym.name, sym.ztype, sym.value.value, param.frame)
        else:
            code += self.emit.emitPUTSTATIC(f"{sym.value.value}.{sym.name}", sym.ztype, param.frame)
        return code

    
    def genMETHOD(self, consdecl: FuncDecl, o, frame):
        sym = self.funcList.get(consdecl.name.name)
        if sym is None:
            raise "No function"
        returnType = sym.ztype.rettype
        isMain = consdecl.name.name == "main" and len(
                consdecl.param) == 0 and type(sym.ztype.rettype) is VoidType

        print("genMETHOD", consdecl.name.name, returnType)
        if not isMain:
            self.emit.printout(
                self.emit.emitMETHOD(
                    consdecl.name.name, 
                    sym.ztype, 
                    True, 
                    frame
                )
            )
        else:
            self.emit.printout(
                self.emit.emitMETHOD(
                    consdecl.name.name, 
                    Foo([ArrayType([1], StringType())], VoidType()),
                    True, 
                    frame
                )
            )

        frame.enterScope(True)

        # Generate code for parameter declarations
        if isMain:
            self.emit.printout(
                self.emit.emitVAR(
                    frame.getNewIndex(), 
                    "args", 
                    ArrayType([], StringType()),
                    frame.getStartLabel(), 
                    frame.getEndLabel(), 
                    frame
                )
            )

        body = consdecl.body
        self.emit.printout(self.emit.emitLABEL(frame.getStartLabel(), frame))
        
        if not isMain:
            for x in consdecl.param:
                idx = frame.getNewIndex()
                code = self.emit.emitVAR(
                    idx, 
                    x.name.name, 
                    x.name.sym.ztype, 
                    frame.getStartLabel(), 
                    frame.getEndLabel(), 
                    frame
                )
                self.emit.printout(code)
                x.name.sym.value = Index(idx)

        # Generate code for statements
        self.visit(body, SubBody(frame, None))

        self.emit.printout(self.emit.emitLABEL(frame.getEndLabel(), frame))
        if type(returnType) is VoidType:
            self.emit.printout(self.emit.emitRETURN(VoidType(), frame))
        self.emit.printout(self.emit.emitENDMETHOD(frame))
        frame.exitScope()
