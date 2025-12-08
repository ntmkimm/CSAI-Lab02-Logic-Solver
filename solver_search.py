import copy
import time
from heapq import heappush, heappop

class SearchSolver:
    def __init__(self, grid):
        self.grid = grid
        # Tiền xử lý: Tìm neighbors cho mỗi đảo để tra cứu nhanh
        self.adj = {}
        for isl in self.grid.islands:
            self.adj[isl.id] = self.grid.get_potential_neighbors(isl)
        self.islands_list = self.grid.islands
        self.edges = self.get_all_edges()

    def solve_backtracking(self):
        """Cài đặt Backtracking (DFS) đệ quy"""
        start_time = time.time()
        
        # State: edge_index -> count (0, 1, 2)
        initial_assign = {}
        
        # State phụ: Theo dõi số cầu hiện tại của mỗi đảo để cắt tỉa nhánh nhanh (Pruning)
        # Map: island_id -> current_bridge_count
        current_island_counts = {isl.id: 0 for isl in self.grid.islands}
        
        # Bắt đầu đệ quy từ cạnh thứ 0
        if self._backtrack_recursive(0, initial_assign, current_island_counts):
            # Nếu tìm thấy, format lại kết quả
            final_bridges = {}
            for i, count in initial_assign.items():
                if count > 0:
                    final_bridges[self.edges[i]] = count
            return final_bridges, time.time() - start_time
            
        return None, time.time() - start_time

    def _backtrack_recursive(self, idx, assign, island_counts):
        # 1. Base case: Đã duyệt hết tất cả các cạnh tiềm năng
        if idx == len(self.edges):
            # Kiểm tra xem tất cả các đảo đã đủ chỉ tiêu chưa (Goal Check)
            for isl in self.grid.islands:
                if island_counts[isl.id] != isl.value:
                    return False
            # (Tùy chọn) Kiểm tra tính liên thông (Connectivity) ở đây nếu cần
            graph = {isl.id: [] for isl in self.grid.islands}

            for i, count in assign.items():
                if count > 0:
                    u, v = self.edges[i]
                    graph[u.id].append(v.id)
                    graph[v.id].append(u.id)

            # 3. DFS/BFS từ một đảo bất kỳ
            start = self.grid.islands[0].id
            visited = set([start])
            stack = [start]

            while stack:
                node = stack.pop()
                for nei in graph[node]:
                    if nei not in visited:
                        visited.add(nei)
                        stack.append(nei)

            # 4. Kiểm tra visited == tổng số đảo
            return len(visited) == len(self.grid.islands) 
            # return True

        # 2. Lấy cạnh hiện tại đang xét
        u, v = self.edges[idx]
        
        # 3. Thử các giá trị: 0 (không cầu), 1 (1 cầu), 2 (2 cầu)
        # Mẹo heuristic: Thử giá trị lớn trước có thể giúp đảo mau đầy (greedy), 
        # nhưng thử 0 trước an toàn hơn cho backtracking. Ở đây ta thử 0, 1, 2.
        for val in [0, 1, 2]:
            
            # --- CẮT TỈA (PRUNING) ---
            
            # A. Kiểm tra sức chứa (Capacity Constraint)
            # Nếu thêm val cầu mà vượt quá số lượng yêu cầu của đảo -> Bỏ qua
            if island_counts[u.id] + val > u.value or island_counts[v.id] + val > v.value:
                continue
                
            # B. Kiểm tra cắt nhau (Crossing Constraint)
            # Chỉ cần kiểm tra nếu val > 0. Nếu val = 0 thì không thể cắt ai.
            if val > 0:
                if self.is_crossing_with_assigned(self.edges[idx], val, assign):
                    continue
            
            # --- HÀNH ĐỘNG (ACTION) ---
            
            assign[idx] = val
            island_counts[u.id] += val
            island_counts[v.id] += val
            
            # --- ĐỆ QUY (RECURSE) ---
            if self._backtrack_recursive(idx + 1, assign, island_counts):
                return True # Tìm thấy solution, thoát ngay lập tức
            
            # --- QUAY LUI (BACKTRACK) ---
            # Hoàn trả lại trạng thái cũ để thử giá trị khác
            island_counts[u.id] -= val
            island_counts[v.id] -= val
            del assign[idx]

        return False
    
    def get_all_edges(self):
        edges = []
        seen = set()
        for isl in self.grid.islands:
            for nb in self.adj[isl.id]:
                edge = tuple(sorted((isl.id, nb.id)))
                if edge not in seen:
                    seen.add(edge)
                    # Tìm object island từ ID
                    u = self.grid.get_island_at(int(edge[0].split('_')[0]), int(edge[0].split('_')[1]))
                    v = self.grid.get_island_at(int(edge[1].split('_')[0]), int(edge[1].split('_')[1]))
                    edges.append((u, v))
        return edges

    def solve_astar(self):
        """Cài đặt A* Search"""
        start_time = time.time()
        
        # State: (f_score, index_edge, counter, current_assignment_dict)
        # Counter dùng để tie-break khi f_score và index bằng nhau
        
        initial_assign = {} 
        pq = []
        
        # Biến đếm để đảm bảo tính duy nhất
        counter = 0 
        
        # Structure: (f, idx, unique_id, assignment)
        heappush(pq, (0, 0, counter, initial_assign))
        
        while pq:
            # Lấy ra 4 giá trị (bỏ qua biến counter bằng dấu _)
            f, idx, _, assign = heappop(pq)
            
            # Kiểm tra hợp lệ cục bộ (pruning)
            if not self.is_partial_valid(assign):
                continue
            
            # Goal check
            if idx == len(self.edges):
                if self.check_goal(assign):
                    final_bridges = {}
                    for i, count in assign.items():
                        if count > 0:
                            final_bridges[self.edges[i]] = count
                    return final_bridges, time.time() - start_time
                continue

            # Expand
            for val in [0, 1, 2]:
                # Check crossing sơ bộ
                if val > 0 and self.is_crossing_with_assigned(self.edges[idx], val, assign):
                    continue
                
                new_assign = assign.copy()
                new_assign[idx] = val
                
                # Heuristic
                h = self.heuristic(new_assign)
                g = sum(new_assign.values())
                
                # Tăng counter lên để đảm bảo unique
                counter += 1
                
                # Push thêm counter vào tuple
                heappush(pq, (g + h, idx + 1, counter, new_assign))
                
        return None, time.time() - start_time

    # Helper functions cho Search
    def is_crossing_with_assigned(self, current_edge, val, assign):
        u1, v1 = current_edge
        # Check với các cạnh đã có trong assign mà > 0
        for i, count in assign.items():
            if count > 0:
                u2, v2 = self.edges[i]
                # Reuse logic check crossing từ SAT solver hoặc viết lại nhanh
                if self.check_cross(u1, v1, u2, v2):
                    return True
        return False

    def check_cross(self, u1, v1, u2, v2):
         # Logic tương tự solver_sat.is_crossing
        h1 = (u1.r == v1.r)
        h2 = (u2.r == v2.r)
        if h1 == h2: return False
        
        horz = (u1, v1) if h1 else (u2, v2)
        vert = (u2, v2) if h1 else (u1, v1)
        
        r_h = horz[0].r
        c_h_min, c_h_max = min(horz[0].c, horz[1].c), max(horz[0].c, horz[1].c)
        c_v = vert[0].c
        r_v_min, r_v_max = min(vert[0].r, vert[1].r), max(vert[0].r, vert[1].r)
        
        return (r_v_min < r_h < r_v_max) and (c_h_min < c_v < c_h_max)

    def is_partial_valid(self, assign):
        # Kiểm tra xem có đảo nào bị Overload số cầu không
        island_counts = {isl.id: 0 for isl in self.grid.islands}
        for idx, count in assign.items():
            u, v = self.edges[idx]
            island_counts[u.id] += count
            island_counts[v.id] += count
            
        for isl in self.grid.islands:
            if island_counts[isl.id] > isl.value:
                return False
        return True

    def check_goal(self, assign):
        # Check exact sum
        island_counts = {isl.id: 0 for isl in self.grid.islands}
        for idx, count in assign.items():
            u, v = self.edges[idx]
            island_counts[u.id] += count
            island_counts[v.id] += count
            
        for isl in self.grid.islands:
            if island_counts[isl.id] != isl.value:
                return False
        
        # Check connectivity (BFS) - Optional but recommended
        graph = {isl.id: [] for isl in self.grid.islands}

        for i, count in assign.items():
            if count > 0:
                u, v = self.edges[i]
                graph[u.id].append(v.id)
                graph[v.id].append(u.id)

        # 3. DFS/BFS từ một đảo bất kỳ
        start = self.grid.islands[0].id
        visited = set([start])
        stack = [start]

        while stack:
            node = stack.pop()
            for nei in graph[node]:
                if nei not in visited:
                    visited.add(nei)
                    stack.append(nei)

        # 4. Kiểm tra visited == tổng số đảo
        return len(visited) == len(self.grid.islands) 

    def heuristic(self, assign):
        # Heuristic: Tổng số cầu còn thiếu của tất cả các đảo / 2 (vì 1 cầu nối 2 đảo)
        island_current = {isl.id: 0 for isl in self.grid.islands}
        for idx, count in assign.items():
            u, v = self.edges[idx]
            island_current[u.id] += count
            island_current[v.id] += count
            
        h_val = 0
        for isl in self.grid.islands:
            diff = isl.value - island_current[isl.id]
            if diff > 0: h_val += diff
        return h_val / 2