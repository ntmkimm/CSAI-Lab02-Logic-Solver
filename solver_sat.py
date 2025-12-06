from pysat.solvers import Glucose3
from pysat.card import CardEnc
from utils import Grid

class SATSolver:
    def __init__(self, grid: Grid):
        self.grid = grid
        self.solver = Glucose3()
        self.var_manager = {} # Map (island_u_id, island_v_id, bridge_count) -> int ID
        self.next_var = 1
        self.potential_edges = []

    def get_var(self, u, v, k):
        """Lấy ID biến cho cạnh u-v với k cầu (k=1 hoặc 2)"""
        # Chuẩn hóa để u luôn nhỏ hơn v (tránh trùng lặp hướng)
        if u.id > v.id: u, v = v, u
        key = (u.id, v.id, k)
        if key not in self.var_manager:
            self.var_manager[key] = self.next_var
            self.next_var += 1
        return self.var_manager[key]

    def solve(self):
        # 1. Xác định các cạnh tiềm năng
        for isl in self.grid.islands:
            neighbors = self.grid.get_potential_neighbors(isl)
            for nb in neighbors:
                if isl.id < nb.id: # Chỉ lưu 1 lần cho mỗi cặp
                    self.potential_edges.append((isl, nb))

        # 2. Tạo ràng buộc: Tổng số cầu mỗi đảo phải đúng
        for isl in self.grid.islands:
            adj_vars = []
            # Tìm tất cả cạnh nối với đảo này
            for (u, v) in self.potential_edges:
                if u == isl or v == isl:
                    # Var cho 1 cầu
                    v1 = self.get_var(u, v, 1)
                    # Var cho 2 cầu
                    v2 = self.get_var(u, v, 2)
                    
                    # Logic: Nếu có 2 cầu (v2=True) thì tính là 2, 
                    # nhưng CardEnc chỉ đếm số biến True.
                    # Mẹo: Tạo biến phụ để đếm tổng trọng số hoặc dùng CardEnc với trọng số (nếu thư viện hỗ trợ tốt),
                    # Cách đơn giản cho CNF thuần:
                    # Coi v1 là "có ít nhất 1 cầu", v2 là "có 2 cầu".
                    # Số cầu = (1 nếu v1) + (1 nếu v2).
                    # Ràng buộc: v2 -> v1 (Nếu có 2 cầu thì phải có ít nhất 1 cầu)
                    self.solver.add_clause([-v2, v1]) 
                    
                    adj_vars.append(v1)
                    adj_vars.append(v2)
            
            # Sử dụng CardEnc để bắt buộc tổng số biến True == isl.value
            cnf = CardEnc.equals(lits=adj_vars, bound=isl.value, top_id=self.next_var)
            self.solver.append_formula(cnf.clauses)
            self.next_var = cnf.nv + 1

        # 3. Ràng buộc: Không được cắt nhau (Crossing)
        # Hai cạnh (u, v) và (p, q) cắt nhau nếu 1 cái ngang, 1 cái dọc và giao tọa độ
        for i in range(len(self.potential_edges)):
            for j in range(i + 1, len(self.potential_edges)):
                u1, v1 = self.potential_edges[i]
                u2, v2 = self.potential_edges[j]
                
                if self.is_crossing(u1, v1, u2, v2):
                    # Không thể đồng thời có cầu ở cả 2 cạnh
                    # v1_1 là biến "ít nhất 1 cầu" của cạnh 1
                    var1 = self.get_var(u1, v1, 1)
                    var2 = self.get_var(u2, v2, 1)
                    self.solver.add_clause([-var1, -var2])

        # 4. Giải
        if self.solver.solve():
            model = self.solver.get_model()
            return self.decode_model(model)
        else:
            return None

    def is_crossing(self, u1, v1, u2, v2):
        # Kiểm tra cắt nhau đơn giản (giả sử đảo thẳng hàng grid)
        # Cạnh 1: Ngang (row1, c_min -> c_max)
        # Cạnh 2: Dọc (r_min -> r_max, col2)
        # Cắt nhau nếu row1 nằm giữa r_min, r_max VÀ col2 nằm giữa c_min, c_max
        
        # Xác định hướng
        h1 = (u1.r == v1.r) # True nếu ngang
        h2 = (u2.r == v2.r)
        
        if h1 == h2: return False # Cùng hướng song song không cắt (vì đã check lân cận)
        
        # Gán nhãn ngang/dọc
        horz = (u1, v1) if h1 else (u2, v2)
        vert = (u2, v2) if h1 else (u1, v1)
        
        r_h = horz[0].r
        c_h_min, c_h_max = min(horz[0].c, horz[1].c), max(horz[0].c, horz[1].c)
        
        c_v = vert[0].c
        r_v_min, r_v_max = min(vert[0].r, vert[1].r), max(vert[0].r, vert[1].r)
        
        return (r_v_min < r_h < r_v_max) and (c_h_min < c_v < c_h_max)

    def decode_model(self, model):
        bridges = {}
        model_set = set(model)
        for (u, v) in self.potential_edges:
            v1 = self.get_var(u, v, 1)
            v2 = self.get_var(u, v, 2)
            count = 0
            if v2 in model_set: count = 2
            elif v1 in model_set: count = 1
            
            if count > 0:
                bridges[(u, v)] = count
        return bridges