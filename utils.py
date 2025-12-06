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

    def get_island_at(self, r, c):
        for isl in self.islands:
            if isl.r == r and isl.c == c:
                return isl
        return None

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
    """
    Tạo output theo format yêu cầu:
    | : 1 dọc, $ : 2 dọc
    - : 1 ngang, = : 2 ngang
    """
    # Khởi tạo bảng output với giá trị gốc (số hoặc 0)
    out_map = [[str(grid.map_data[r][c]) for c in range(grid.cols)] for r in range(grid.rows)]
    
    for (u, v), count in bridges.items():
        if count == 0: continue
        
        # Xác định hướng và ký tự
        r1, c1 = u.r, u.c
        r2, c2 = v.r, v.c
        
        if r1 == r2: # Ngang
            char = "-" if count == 1 else "="
            c_start, c_end = min(c1, c2) + 1, max(c1, c2)
            for c in range(c_start, c_end):
                out_map[r1][c] = char
        else: # Dọc
            char = "|" if count == 1 else "$"
            r_start, r_end = min(r1, r2) + 1, max(r1, r2)
            for r in range(r_start, r_end):
                out_map[r][c1] = char
                
    # Format thành string list style như đề bài
    result_lines = []
    for row in out_map:
        line_str = "[ " + " , ".join([f'"{x}"' for x in row]) + " ]"
        result_lines.append(line_str)
    return "\n".join(result_lines)

def write_output(file_path, content):
    with open(file_path, 'w') as f:
        f.write(content)