from .xml_engine import XmlEngine
from .xml_edits import NodeDeletion, NodeReplacement, NodeInsertion, NodeMoving
from .xml_edits import TextSetting, TextWrapping

from .srcml_engine import SrcmlEngine
from .srcml_edits import XmlLineReplacement, XmlLineInsertion, XmlLineDeletion, XmlLineMoving
from .srcml_edits import StmtReplacement, StmtInsertion, StmtDeletion, StmtMoving, StmtSwap
from .srcml_edits import BreakDeletion, ContinueDeletion, DeclStmtDeletion, DoDeletion, ExprStmtDeletion, ForDeletion, GotoDeletion, IfDeletion, ReturnDeletion, SwitchDeletion, WhileDeletion
from .srcml_edits import BreakReplacement, ContinueReplacement, DeclStmtReplacement, DoReplacement, ExprStmtReplacement, ForReplacement, GotoReplacement, IfReplacement, ReturnReplacement, SwitchReplacement, WhileReplacement
from .srcml_edits import BreakInsertion, ContinueInsertion, DeclStmtInsertion, DoInsertion, ExprStmtInsertion, ForInsertion, GotoInsertion, IfInsertion, ReturnInsertion, SwitchInsertion, WhileInsertion
from .srcml_edits import ExprReplacement
from .srcml_edits import ComparisonOperatorSetting, ArithmeticOperatorSetting
from .srcml_edits import NumericSetting, RelativeNumericSetting

# "final" engines only
engines = [
    XmlEngine,
    SrcmlEngine,
]

# "final" edits only
edits = [
    XmlLineReplacement, XmlLineInsertion, XmlLineDeletion, XmlLineMoving,
    StmtReplacement, StmtInsertion, StmtDeletion, StmtMoving, StmtSwap,
    BreakDeletion, ContinueDeletion, DeclStmtDeletion, DoDeletion, ExprStmtDeletion, ForDeletion, GotoDeletion, IfDeletion, ReturnDeletion, SwitchDeletion, WhileDeletion,
    BreakReplacement, ContinueReplacement, DeclStmtReplacement, DoReplacement, ExprStmtReplacement, ForReplacement, GotoReplacement, IfReplacement, ReturnReplacement, SwitchReplacement, WhileReplacement,
    BreakInsertion, ContinueInsertion, DeclStmtInsertion, DoInsertion, ExprStmtInsertion, ForInsertion, GotoInsertion, IfInsertion, ReturnInsertion, SwitchInsertion, WhileInsertion,
    ExprReplacement,
    ComparisonOperatorSetting, ArithmeticOperatorSetting,
    NumericSetting, RelativeNumericSetting,
]