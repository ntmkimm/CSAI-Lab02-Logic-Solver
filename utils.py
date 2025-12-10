class Island:
    def __init__(self, r, c, value):
        self.r = r
        self.c = c
        self.value = value
        self.current_bridges = 0
        self.id = f"{r}_{c}"

    def __repr__(self):
        return f"Island({self.r}, {self.c}, val={self.value})"

class Grid:
    def __init__(self, raw_data):
        self.rows = len(raw_data)
        self.cols = len(raw_data[0])
        self.islands = []
        self.map_data = raw_data # 0 or value
        
        for r in range(self.rows):
            for c in range(self.cols):
                if raw_data[r][c] > 0:
                    self.islands.append(Island(r, c, raw_data[r][c]))
        
        self.get_potential_edges()

    def get_potential_neighbors(self, island):
        """Tìm các đảo có thể kết nối với đảo hiện tại (thẳng hàng, không bị chặn)"""
        neighbors = []
        # Directions: (dr, dc)
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)] 
        
        for dr, dc in dirs:
            r, c = island.r + dr, island.c + dc
            while 0 <= r < self.rows and 0 <= c < self.cols:
                if self.map_data[r][c] > 0:
                    neighbors.append(self.get_island_at(r, c))
                    break
                r += dr
                c += dc
                
        return neighbors
    
    def get_potential_edges(self):
        self.potential_edges = []
        for isl in self.islands:
            neighbors = self.get_potential_neighbors(isl)
            for nb in neighbors:
                if isl.id < nb.id:
                    self.potential_edges.append((isl, nb))

    def get_island_at(self, r, c):
        for isl in self.islands:
            if isl.r == r and isl.c == c:
                return isl
        return None

def is_crossing(u1: Island, v1: Island, u2: Island, v2: Island):
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

def read_input(file_path):
    data = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            # Loại bỏ dấu phẩy và khoảng trắng thừa, parse thành int
            parts = line.strip().split(',')
            row = [int(x.strip()) if x.strip().isdigit() else 0 for x in parts]
            if row:
                data.append(row)
    return Grid(data)

def format_output(grid, bridges):
    # 1. Tạo bản đồ nền chứa giá trị đảo
    out_map = [["0"] * grid.cols for _ in range(grid.rows)]
    for isl in grid.islands:
        out_map[isl.r][isl.c] = str(isl.value)

    # 2. Vẽ cầu
    for (u, v), count in bridges.items():
        if count == 0: continue
        
        # Xác định ký tự
        is_horz = (u.r == v.r)
        if is_horz:
            char = "-" if count == 1 else "="
            r = u.r
            c_min, c_max = min(u.c, v.c), max(u.c, v.c)
            # CHỈ vẽ vào khoảng giữa, không vẽ đè lên đảo đầu và đảo cuối
            for c in range(c_min + 1, c_max):
                if out_map[r][c] == "0": # Chỉ vẽ nếu ô đang trống
                    out_map[r][c] = char
        else:
            char = "|" if count == 1 else "$"
            c = u.c
            r_min, r_max = min(u.r, v.r), max(u.r, v.r)
            for r in range(r_min + 1, r_max):
                if out_map[r][c] == "0":
                    out_map[r][c] = char

    # 3. Chuyển thành chuỗi theo format đề bài
    result_lines = []
    for row in out_map:
        # Format từng phần tử thành "x"
        formatted_row = [f'"{x}"' for x in row]
        line_str = "[ " + " , ".join(formatted_row) + " ]"
        result_lines.append(line_str)
        
    return "\n".join(result_lines)

def write_output(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)