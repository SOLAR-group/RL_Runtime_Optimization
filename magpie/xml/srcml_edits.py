from .xml_edits import NodeDeletion, NodeReplacement, NodeInsertion, NodeMoving, NodeSwap
from .xml_edits import TextSetting, TextWrapping

class XmlLineDeletion(NodeDeletion):
    NODE_TYPE = 'line'

class XmlLineReplacement(NodeReplacement):
    NODE_TYPE = 'line'

class XmlLineInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'unit'
    NODE_TYPE = 'line'

class XmlLineMoving(NodeMoving):
    NODE_PARENT_TYPE = 'unit'
    NODE_TYPE = 'line'

class StmtDeletion(NodeDeletion):
    NODE_TYPE = 'stmt'

# Deletion: break continue decl_stmt do expr_stmt for goto if return switch while
# Note NODE_TYPE is the node type in the target file
class BreakDeletion(NodeDeletion):
    NODE_TYPE = 'break'

class ContinueDeletion(NodeDeletion):
    NODE_TYPE = 'continue'

class DeclStmtDeletion(NodeDeletion):
    NODE_TYPE = 'decl_stmt'

class DoDeletion(NodeDeletion):
    NODE_TYPE = 'do'

class ExprStmtDeletion(NodeDeletion):
    NODE_TYPE = 'expr_stmt'

class ForDeletion(NodeDeletion):
    NODE_TYPE = 'for'

class GotoDeletion(NodeDeletion):
    NODE_TYPE = 'goto'

class IfDeletion(NodeDeletion):
    NODE_TYPE = 'if'

class ReturnDeletion(NodeDeletion):
    NODE_TYPE = 'return'

class SwitchDeletion(NodeDeletion):
    NODE_TYPE = 'switch'

class WhileDeletion(NodeDeletion):
    NODE_TYPE = 'while'

# Replacement: break continue decl_stmt do expr_stmt for goto if return switch while
# Note: NODE_TYPE is the node type in the target file, while the ingredient for replacement is any statement node ('stmt')
class BreakReplacement(NodeReplacement):
    NODE_TYPE = 'break'

class ContinueReplacement(NodeReplacement):
    NODE_TYPE = 'continue'

class DeclStmtReplacement(NodeReplacement):
    NODE_TYPE = 'decl_stmt'

class DoReplacement(NodeReplacement):
    NODE_TYPE = 'do'

class ExprStmtReplacement(NodeReplacement):
    NODE_TYPE = 'expr_stmt'

class ForReplacement(NodeReplacement):
    NODE_TYPE = 'for'

class GotoReplacement(NodeReplacement):
    NODE_TYPE = 'goto'

class IfReplacement(NodeReplacement):
    NODE_TYPE = 'if'

class ReturnReplacement(NodeReplacement):
    NODE_TYPE = 'return'

class SwitchReplacement(NodeReplacement):
    NODE_TYPE = 'switch'

class WhileReplacement(NodeReplacement):
    NODE_TYPE = 'while'

# Insertion: break continue decl_stmt do expr_stmt for goto if return switch while
# Note: NODE_TYPE is the node type in the ingredient file
class BreakInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'break'

class ContinueInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'continue'

class DeclStmtInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'decl_stmt'

class DoInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'do'

class ExprStmtInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'expr_stmt'

class ForInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'for'

class GotoInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'goto'

class IfInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'if'

class ReturnInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'return'

class SwitchInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'switch'

class WhileInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'while'

class StmtReplacement(NodeReplacement):
    NODE_TYPE = 'stmt'

class StmtInsertion(NodeInsertion):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'stmt'

class StmtMoving(NodeMoving):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'stmt'

class StmtSwap(NodeSwap):
    NODE_PARENT_TYPE = 'block'
    NODE_TYPE = 'stmt'

class ConditionReplacement(NodeReplacement):
    NODE_TYPE = 'condition'

class ExprReplacement(NodeReplacement):
    NODE_TYPE = 'expr'

class ComparisonOperatorSetting(TextSetting):
    NODE_TYPE = 'operator_comp'
    CHOICES = ['==', '!=', '<', '<=', '>', '>=']

class ArithmeticOperatorSetting(TextSetting):
    NODE_TYPE = 'operator_arith'
    CHOICES = ['+', '-', '*', '/', '%']

class NumericSetting(TextSetting):
    NODE_TYPE = 'number'
    CHOICES = ['-1', '0', '1']

class RelativeNumericSetting(TextWrapping):
    NODE_TYPE = 'number'
    CHOICES = [('(', '+1)'), ('(', '-1)'), ('(', '/2)'), ('(', '*2)'), ('(', '*3/2)'), ('(', '*2/3)')]
