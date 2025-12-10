from pysat.card import CardEnc
from utils import Grid, is_crossing
from pysat.formula import CNF

class CNFBuilder:
    def __init__(self, grid: Grid):
        self.grid = grid
        self.var_manager = {} # Map (island_u_id, island_v_id, bridge_count) -> int ID
        self.next_var = 1
        # Cache để lưu biến "có ít nhất 1 cầu" nhằm tái sử dụng cho phần connectivity
        self.edge_vars = {} 
        self.cnf = CNF()

    def get_var(self, u, v, k):
        """Lấy ID biến cho cạnh u-v với k cầu (k=1 hoặc 2)"""   
        # Chuẩn hóa để u luôn nhỏ hơn v (tránh trùng lặp hướng)
        if u.id > v.id: u, v = v, u
        key = (u.id, v.id, k)
        if key not in self.var_manager:
            self.var_manager[key] = self.next_var
            self.next_var += 1
        return self.var_manager[key]

    def build_basic_constraints(self):
        """các ràng buộc cơ bản """
        # Ràng buộc tổng số cầu (Degree Constraints)
        for isl in self.grid.islands:
            adj_vars = []
            for (u, v) in self.grid.potential_edges:
                if u == isl or v == isl:
                    v1 = self.get_var(u, v, 1) # Có ít nhất 1 cầu
                    v2 = self.get_var(u, v, 2) # Có 2 cầu
                    
                    # Lưu cache v1 để dùng cho connectivity
                    edge_key = tuple(sorted((u.id, v.id)))
                    self.edge_vars[edge_key] = v1
                    # Logic: Nếu có 2 cầu (v2=True) thì tính là 2, 
                    # Coi v1 là "có ít nhất 1 cầu", v2 là "có tồn tại cầu thứ 2".
                    # Số cầu = (1 nếu v1) + (1 nếu v2).
                    # Ràng buộc: v2 -> v1 (Nếu có 2 cầu thì phải có ít nhất 1 cầu)
                    # self.solver.add_clause([-v2, v1]) 
                    self.cnf.append([-v2, v1])
                    adj_vars.extend([v1, v2])
            
            # CardEnc: Tổng số cầu == Giá trị đảo
            cnf = CardEnc.equals(lits=adj_vars, bound=isl.value, top_id=self.next_var)
            # self.solver.append_formula(cnf.clauses)
            self.cnf.extend(cnf.clauses)
            self.next_var = cnf.nv + 1

        # 3. Ràng buộc: Không được cắt nhau (Crossing)
        # Hai cạnh (u, v) và (p, q) cắt nhau nếu 1 cái ngang, 1 cái dọc và giao tọa độ
        for i in range(len(self.grid.potential_edges)):
            for j in range(i + 1, len(self.grid.potential_edges)):
                u1, v1 = self.grid.potential_edges[i]
                u2, v2 = self.grid.potential_edges[j]
                if is_crossing(u1, v1, u2, v2):
                    # Không thể đồng thời có cầu ở cả 2 cạnh
                    # v1_1 là biến "ít nhất 1 cầu" của cạnh 1
                    var1 = self.get_var(u1, v1, 1)
                    var2 = self.get_var(u2, v2, 1)
                    # self.solver.add_clause([-var1, -var2])
                    self.cnf.append([-var1, -var2])

    def add_connectivity_constraints(self):
        """
        Thêm ràng buộc liên thông sử dụng Level (Depth) Encoding.
        Biến: level[u][k] -> Đảo u nằm ở độ sâu k so với Root.
        Độ phức tạp biến: O(N^2)
        """
        islands = self.grid.islands
        n = len(islands)
        if n <= 1: return # Luôn liên thông nếu chỉ có 0 hoặc 1 đảo

        # Chọn đảo đầu tiên làm Root
        root = islands[0]

        # Quản lý biến level: level_vars[island_index][depth]
        # Depth từ 0 đến n-1
        level_vars = [[0] * n for _ in range(n)]

        # Tạo biến level
        for i in range(n):
            for k in range(n):
                level_vars[i][k] = self.next_var
                self.next_var += 1

        # 1. Ràng buộc Root: Root luôn ở level 0
        # self.solver.add_clause([level_vars[0][0]]) 
        self.cnf.append([level_vars[0][0]])
        for k in range(1, n):
            self.cnf.append([-level_vars[0][k]])
            # self.solver.add_clause([-level_vars[0][k]]) # Root không thể ở level > 0

        # 2. Các đảo khác: Mỗi đảo có đúng 1 level độ sâu (từ 1 đến n-1)
        # Root chiếm level 0, nên các đảo khác không được ở level 0
        for i in range(1, n):
            # self.solver.add_clause([-level_vars[i][0]]) 
            self.cnf.append([-level_vars[i][0]])
            # Sử dụng CardEnc để đảm bảo mỗi đảo chỉ có đúng 1 level k (k in 1..n-1)
            possible_levels = [level_vars[i][k] for k in range(1, n)]
            cnf = CardEnc.equals(lits=possible_levels, bound=1, top_id=self.next_var)
            # self.solver.append_formula(cnf.clauses)
            self.cnf.extend(cnf.clauses)
            self.next_var = cnf.nv + 1

        # 3. Ràng buộc lan truyền (Propagation Constraint)
        # Nếu đảo u ở level k, nó phải có một hàng xóm v được nối cầu và v ở level k-1
        # Logic: Level[u][k] => OR( HasBridge(u,v) AND Level[v][k-1] ) với mọi neighbor v
        # CNF: ~Level[u][k] OR Aux_v1 OR Aux_v2 ...
        
        for i in range(1, n): # Với mọi đảo u (trừ root)
            u = islands[i]
            neighbors = self.grid.get_potential_neighbors(u)
            
            for k in range(1, n): # Với mọi level k
                clauses_or = [-level_vars[i][k]] # Bắt đầu mệnh đề: ~L(u,k) v ...
                
                valid_neighbors = []
                for v in neighbors:
                    # Tìm index của v trong list islands
                    try:
                        v_idx = islands.index(v)
                    except ValueError: continue

                    # Lấy biến cầu nối (u, v) - chỉ cần có ít nhất 1 cầu
                    edge_key = tuple(sorted((u.id, v.id)))
                    if edge_key not in self.edge_vars: continue
                    bridge_var = self.edge_vars[edge_key]

                    # Biến level của v tại k-1
                    prev_level_var = level_vars[v_idx][k-1]

                    # Tạo biến phụ trợ P đại diện cho (Bridge(u,v) AND Level(v, k-1))
                    # P <=> Bridge & Level
                    # Ta chỉ cần chiều P => Bridge & Level để dùng trong mệnh đề OR
                    # Tức là: ~P v Bridge  VÀ  ~P v Level
                    # Và mệnh đề chính là: ~Level(u,k) v P1 v P2 ...
                    
                    p_var = self.next_var
                    self.next_var += 1
                    
                    # Định nghĩa P: P chỉ được True nếu cả cầu và level k-1 thỏa mãn
                    # P -> Bridge
                    self.cnf.append([-p_var, bridge_var])
                    # self.solver.add_clause([-p_var, bridge_var])
                    # P -> Level(v, k-1)
                    self.cnf.append([-p_var, prev_level_var])
                    # self.solver.add_clause([-p_var, prev_level_var])
                    
                    clauses_or.append(p_var)
                
                # Thêm mệnh đề chính: Nếu u ở level k, phải có ít nhất 1 P_var đúng
                # self.solver.add_clause(clauses_or)
                self.cnf.append(clauses_or)

    def decode_model(self, model):
        bridges = {}
        model_set = set(model)
        for (u, v) in self.grid.potential_edges:
            v1 = self.get_var(u, v, 1)
            v2 = self.get_var(u, v, 2)
            count = 0
            if v2 in model_set: count = 2
            elif v1 in model_set: count = 1
            if count > 0:
                bridges[(u, v)] = count
        return bridges