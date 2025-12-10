import time
from utils import Grid, is_crossing

class BlindSolver:
    def __init__(self, grid: Grid):
        self.grid = grid
    
    def solve_bruteforce_with_connectivity(self):
        start_time = time.time()
        E = len(self.grid.potential_edges)
        islands = self.grid.islands
        edge_list = self.grid.potential_edges

        island_index = {isl.id: i for i, isl in enumerate(islands)}
        n_islands = len(islands)

        result = None

        def is_connected(assign):
            adj = [[] for _ in range(n_islands)]

            for i, cnt in enumerate(assign):
                if cnt > 0:
                    u, v = edge_list[i]
                    ui = island_index[u.id]
                    vi = island_index[v.id]
                    adj[ui].append(vi)
                    adj[vi].append(ui)

            start = 0
            visited = set([start])
            stack = [start]

            while stack:
                cur = stack.pop()
                for nx in adj[cur]:
                    if nx not in visited:
                        visited.add(nx)
                        stack.append(nx)

            return len(visited) == n_islands

        def dfs(eid, assign):
            nonlocal result

            if result is not None:
                return

            if eid == E:
                island_count = {isl.id: 0 for isl in islands}

                for idx, cnt in enumerate(assign):
                    u, v = edge_list[idx]
                    island_count[u.id] += cnt
                    island_count[v.id] += cnt

                for isl in islands:
                    if island_count[isl.id] != isl.value:
                        return

                if not is_connected(assign):
                    return

                result = {edge_list[i]: assign[i] for i in range(E) if assign[i] > 0}
                return

            for cnt in [0, 1, 2]:
                assign[eid] = cnt
                dfs(eid + 1, assign)
                if result is not None:
                    return

        dfs(0, [0]*E)
        return result, time.time() - start_time

    
    def solve_backtracking(self):
        start_time = time.time()

        initial_assign = {}
        
        current_island_counts = {isl.id: 0 for isl in self.grid.islands}

        if self._backtrack_recursive(0, initial_assign, current_island_counts):
            final_bridges = {}
            for i, count in initial_assign.items():
                if count > 0:
                    final_bridges[self.grid.potential_edges[i]] = count
            return final_bridges, time.time() - start_time
            
        return None, time.time() - start_time

    def _backtrack_recursive(self, idx, assign, island_counts):
        if idx == len(self.grid.potential_edges):
            for isl in self.grid.islands:
                if island_counts[isl.id] != isl.value:
                    return False
            graph = {isl.id: [] for isl in self.grid.islands}

            for i, count in assign.items():
                if count > 0:
                    u, v = self.grid.potential_edges[i]
                    graph[u.id].append(v.id)
                    graph[v.id].append(u.id)

            start = self.grid.islands[0].id
            visited = set([start])
            stack = [start]

            while stack:
                node = stack.pop()
                for nei in graph[node]:
                    if nei not in visited:
                        visited.add(nei)
                        stack.append(nei)

            return len(visited) == len(self.grid.islands) 

        u, v = self.grid.potential_edges[idx]
        
        for val in [0, 1, 2]:
            if island_counts[u.id] + val > u.value or island_counts[v.id] + val > v.value:
                continue

            if val > 0:
                if self.is_crossing_with_assigned(self.grid.potential_edges[idx], assign):
                    continue

            assign[idx] = val
            island_counts[u.id] += val
            island_counts[v.id] += val

            if self._backtrack_recursive(idx + 1, assign, island_counts):
                return True

            island_counts[u.id] -= val
            island_counts[v.id] -= val
            del assign[idx]

        return False
    
    def is_crossing_with_assigned(self, current_edge, assign):
        u1, v1 = current_edge
        for i, count in assign.items():
            if count > 0:
                u2, v2 = self.grid.potential_edges[i]
                if is_crossing(u1, v1, u2, v2):
                    return True
        return False