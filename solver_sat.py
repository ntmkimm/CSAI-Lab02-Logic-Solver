from pysat.solvers import Glucose3
from utils import Grid
from cnf_builder import CNFBuilder

class SATSolver(CNFBuilder):
    def __init__(self, grid: Grid):
        super().__init__(grid)    
        self.solver = Glucose3()

    def solve(self):
        # tạo ràng buộc cơ bản (Tổng số cầu + sức chứa đảo + Không cắt nhau)
        # Hàm này cũng sẽ khởi tạo self.edge_vars (v1) để dùng cho ràng buộc liên thông 
        self.build_basic_constraints()

        # ràng buộc đảm bảo liên thông
        self.add_connectivity_constraints()

        # Giải và trả về kết quả
        self.solver.append_formula(self.cnf.clauses)
        if self.solver.solve():
            return self.decode_model(self.solver.get_model())
        return None

    