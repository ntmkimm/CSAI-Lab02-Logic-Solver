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
        # Cache để lưu biến "có ít nhất 1 cầu" nhằm tái sử dụng cho phần connectivity
        self.edge_vars = {} 

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
        # 1. Xác định các cạnh tiềm năng (u, v) sao cho u.id < v.id
        # xác định self.potential_edges trước khi xây dựng các ràng buộc
        self.potential_edges = []
        for isl in self.grid.islands:
            neighbors = self.grid.get_potential_neighbors(isl)
            for nb in neighbors:
                if isl.id < nb.id:
                    self.potential_edges.append((isl, nb))

        # 2. tạo ràng buộc cơ bản (Tổng số cầu + sức chứa đảo + Không cắt nhau)
        # Hàm này cũng sẽ khởi tạo self.edge_vars (v1) để dùng cho ràng buộc liên thông 
        self.build_basic_constraints()

        # ràng buộc đảm bảo liên thông
        self.add_connectivity_constraints()

        # 4. Giải và trả về kết quả
        if self.solver.solve():
            return self.decode_model(self.solver.get_model())
        return None

    def build_basic_constraints(self):
        """các ràng buộc cơ bản """
        # Ràng buộc tổng số cầu (Degree Constraints)
        for isl in self.grid.islands:
            adj_vars = []
            for (u, v) in self.potential_edges:
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
                    self.solver.add_clause([-v2, v1]) 
                    adj_vars.append(v1)
                    adj_vars.append(v2)
            
            # CardEnc: Tổng số cầu == Giá trị đảo
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
        self.solver.add_clause([level_vars[0][0]]) 
        for k in range(1, n):
            self.solver.add_clause([-level_vars[0][k]]) # Root không thể ở level > 0

        # 2. Các đảo khác: Mỗi đảo có đúng 1 level độ sâu (từ 1 đến n-1)
        # Root chiếm level 0, nên các đảo khác không được ở level 0
        for i in range(1, n):
            self.solver.add_clause([-level_vars[i][0]]) 
            
            # Sử dụng CardEnc để đảm bảo mỗi đảo chỉ có đúng 1 level k (k in 1..n-1)
            possible_levels = [level_vars[i][k] for k in range(1, n)]
            cnf = CardEnc.equals(lits=possible_levels, bound=1, top_id=self.next_var)
            self.solver.append_formula(cnf.clauses)
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
                    self.solver.add_clause([-p_var, bridge_var])
                    # P -> Level(v, k-1)
                    self.solver.add_clause([-p_var, prev_level_var])
                    
                    clauses_or.append(p_var)
                
                # Thêm mệnh đề chính: Nếu u ở level k, phải có ít nhất 1 P_var đúng
                self.solver.add_clause(clauses_or)

    def is_crossing(self, u1, v1, u2, v2):
        # Xác định hướng: True là Ngang, False là Dọc
        h1 = (u1.r == v1.r)
        h2 = (u2.r == v2.r)
        
        # Nếu cùng hướng (cùng ngang hoặc cùng dọc) -> Không bao giờ cắt (do đã check lân cận)
        if h1 == h2: return False
        
        # Gán nhãn ngang/dọc
        horz = (u1, v1) if h1 else (u2, v2)
        vert = (u2, v2) if h1 else (u1, v1)
        
        # Tọa độ Ngang: Dòng r_h, Cột từ c_h_min đến c_h_max
        r_h = horz[0].r
        c_h_min, c_h_max = min(horz[0].c, horz[1].c), max(horz[0].c, horz[1].c)
        
        # Tọa độ Dọc: Cột c_v, Dòng từ r_v_min đến r_v_max
        c_v = vert[0].c
        r_v_min, r_v_max = min(vert[0].r, vert[1].r), max(vert[0].r, vert[1].r)
        
        # ĐIỀU KIỆN CẮT NHAU 
        # Dòng của cầu ngang phải nằm GIỮA 2 đầu cầu dọc
        # Cột của cầu dọc phải nằm GIỮA 2 đầu cầu ngang
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