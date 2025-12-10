import copy
import time
from heapq import heappush, heappop
from pysat.card import CardEnc
from pysat.formula import CNF

class SearchSolver:
    def __init__(self, grid):
        self.grid = grid
        self.adj = {isl.id: self.grid.get_potential_neighbors(isl) for isl in self.grid.islands}
        self.islands_list = self.grid.islands
        self.potential_edges = self.get_all_edges()
        self.var_manager = {}  # Map (u,v,k) -> var ID
        self.edge_vars = {}    # Map (u.id, v.id) -> var "ít nhất 1 cầu"
        self.next_var = 1
        self.cnf = CNF()

    def get_var(self, u, v, k):
        if u.id > v.id:
            u, v = v, u
        key = (u.id, v.id, k)
        if key not in self.var_manager:
            self.var_manager[key] = self.next_var
            self.next_var += 1
        return self.var_manager[key]

    def get_all_edges(self):
        edges = []
        seen = set()
        for isl in self.grid.islands:
            for nb in self.adj[isl.id]:
                edge = tuple(sorted((isl.id, nb.id)))
                if edge not in seen:
                    seen.add(edge)
                    u = self.grid.get_island_at(int(edge[0].split('_')[0]), int(edge[0].split('_')[1]))
                    v = self.grid.get_island_at(int(edge[1].split('_')[0]), int(edge[1].split('_')[1]))
                    edges.append((u, v))
        return edges

    def build_basic_constraints(self):
        for isl in self.grid.islands:
            adj_vars = []
            for (u, v) in self.potential_edges:
                if u == isl or v == isl:
                    v1 = self.get_var(u, v, 1)
                    v2 = self.get_var(u, v, 2)
                    edge_key = tuple(sorted((u.id, v.id)))
                    self.edge_vars[edge_key] = v1
                    self.cnf.append([-v2, v1])
                    adj_vars.extend([v1, v2])
            cnf_card = CardEnc.equals(lits=adj_vars, bound=isl.value, top_id=self.next_var)
            self.cnf.extend(cnf_card.clauses)
            self.next_var = cnf_card.nv + 1

        for i in range(len(self.potential_edges)):
            for j in range(i+1, len(self.potential_edges)):
                u1, v1 = self.potential_edges[i]
                u2, v2 = self.potential_edges[j]
                if self.is_crossing(u1, v1, u2, v2):
                    var1 = self.get_var(u1, v1, 1)
                    var2 = self.get_var(u2, v2, 1)
                    self.cnf.append([-var1, -var2])

    def add_connectivity_constraints(self):
        islands = self.grid.islands
        n = len(islands)
        if n <= 1: return
        root = islands[0]
        level_vars = [[0]*n for _ in range(n)]
        for i in range(n):
            for k in range(n):
                level_vars[i][k] = self.next_var
                self.next_var += 1
        
        self.cnf.append([level_vars[0][0]])
        for k in range(1, n):
            self.cnf.append([-level_vars[0][k]])
        
        for i in range(1, n):
            self.cnf.append([-level_vars[i][0]])
            levels = [level_vars[i][k] for k in range(1, n)]
            cnf_card = CardEnc.equals(lits=levels, bound=1, top_id=self.next_var)
            self.cnf.extend(cnf_card.clauses)
            self.next_var = cnf_card.nv + 1

        for i in range(1, n):
            u = islands[i]
            neighbors = self.grid.get_potential_neighbors(u)
            for k in range(1, n):
                clause_or = [-level_vars[i][k]]
                for v in neighbors:
                    try:
                        v_idx = islands.index(v)
                    except ValueError:
                        continue
                    edge_key = tuple(sorted((u.id, v.id)))
                    if edge_key not in self.edge_vars: continue
                    bridge_var = self.edge_vars[edge_key]
                    prev_level_var = level_vars[v_idx][k-1]
                    p_var = self.next_var
                    self.next_var += 1
                    self.cnf.append([-p_var, bridge_var])
                    self.cnf.append([-p_var, prev_level_var])
                    clause_or.append(p_var)
                self.cnf.append(clause_or)

    def is_crossing(self, u1, v1, u2, v2):
        h1 = (u1.r == v1.r)
        h2 = (u2.r == v2.r)
        if h1 == h2: return False
        horz = (u1,v1) if h1 else (u2,v2)
        vert = (u2,v2) if h1 else (u1,v1)
        r_h = horz[0].r
        c_h_min, c_h_max = min(horz[0].c, horz[1].c), max(horz[0].c, horz[1].c)
        c_v = vert[0].c
        r_v_min, r_v_max = min(vert[0].r, vert[1].r), max(vert[0].r, vert[1].r)
        return (r_v_min < r_h < r_v_max) and (c_h_min < c_v < c_h_max)

    def solve_astar_cnf(self):
        start_time = time.time()
        self.cnf = CNF()
        self.build_basic_constraints()
        self.add_connectivity_constraints()
        
        clauses = [tuple(c) for c in self.cnf.clauses]

        var_to_clauses = {}
        all_vars = set()
        
        literal_scores = {} 
        
        for idx, clause in enumerate(clauses):
            length = len(clause)
            weight = 2 ** (-length)
            for lit in clause:
                var = abs(lit)
                all_vars.add(var)
                
                if var not in var_to_clauses:
                    var_to_clauses[var] = []
                var_to_clauses[var].append(idx)
                
                literal_scores[lit] = literal_scores.get(lit, 0) + weight

        priority_vars = []
        for (u, v) in self.potential_edges:
            v1 = self.get_var(u, v, 1)
            v2 = self.get_var(u, v, 2)
            s1 = literal_scores.get(v1, 0) + literal_scores.get(-v1, 0)
            s2 = literal_scores.get(v2, 0) + literal_scores.get(-v2, 0)
            priority_vars.append((-s2, v2)) 
            priority_vars.append((-s1, v1))
        
        priority_vars.sort() 
        decision_order = [v for _, v in priority_vars]
        
        initial_assign = {}

        if not self._unit_propagate(initial_assign, clauses, var_to_clauses):
            return None, time.time() - start_time

        h_start = self._calculate_unsat_count(initial_assign, clauses)

        g_start = len(initial_assign)
        pq = [(h_start, g_start, tuple(sorted(initial_assign.items())))]
        
        visited = set()

        while pq:
            h, g, assign_tuple = heappop(pq)
            assign = dict(assign_tuple)

            if h == 0:
                return self._extract_solution(assign), time.time() - start_time

            if assign_tuple in visited:
                continue
            visited.add(assign_tuple)

            next_var = None
            for var in decision_order:
                if var not in assign:
                    next_var = var
                    break

            if next_var is None:
                remaining = all_vars - set(assign.keys())
                if not remaining: continue
                next_var = list(remaining)[0]

            score_true = literal_scores.get(next_var, 0)
            score_false = literal_scores.get(-next_var, 0)
            
            vals = [True, False] if score_true >= score_false else [False, True]
            
            for val in vals:
                new_assign = assign.copy()
                new_assign[next_var] = val
                if self._unit_propagate(new_assign, clauses, var_to_clauses):
                    new_h = self._calculate_unsat_count(new_assign, clauses)
                    new_g = len(new_assign)
                    heappush(pq, (new_h, new_g, tuple(sorted(new_assign.items()))))
        return None, time.time() - start_time

    def _unit_propagate(self, assign, clauses, var_to_clauses):
        queue = list(assign.keys())
        idx = 0
        while idx < len(queue):
            changed = False

            for i, clause in enumerate(clauses):
                unknown_lits = []
                is_sat = False
                for lit in clause:
                    var = abs(lit)
                    val = assign.get(var, None)
                    if val is not None:
                        if (lit > 0 and val) or (lit < 0 and not val):
                            is_sat = True
                            break
                    else:
                        unknown_lits.append(lit)
                
                if is_sat:
                    continue
                
                if len(unknown_lits) == 0:
                    return False 
                
                if len(unknown_lits) == 1:
                    forced_lit = unknown_lits[0]
                    var = abs(forced_lit)
                    val = (forced_lit > 0)
                    if var in assign and assign[var] != val:
                        return False
                    if var not in assign:
                        assign[var] = val
                        changed = True
            
            if not changed:
                break
        return True

    def _calculate_unsat_count(self, assign, clauses):
        count = 0
        for clause in clauses:
            sat = False

            for lit in clause:
                var = abs(lit)
                val = assign.get(var, None)
                if val is not None:
                    if (lit > 0 and val) or (lit < 0 and not val):
                        sat = True
                        break
            
            if not sat:
                count += 1
        return count

    def _extract_solution(self, assign):
        solution = {}
        for u, v in self.potential_edges:
            cnt = 0
            v1 = self.get_var(u, v, 1)
            v2 = self.get_var(u, v, 2)
            if assign.get(v1, False): cnt += 1
            if assign.get(v2, False): cnt += 1
            if cnt > 0:
                solution[(u, v)] = cnt
        return solution

    def solve_bruteforce_with_connectivity(self):
        start_time = time.time()
        E = len(self.potential_edges)
        islands = self.grid.islands
        edge_list = self.potential_edges

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
                    final_bridges[self.potential_edges[i]] = count
            return final_bridges, time.time() - start_time
            
        return None, time.time() - start_time

    def _backtrack_recursive(self, idx, assign, island_counts):
        if idx == len(self.potential_edges):
            for isl in self.grid.islands:
                if island_counts[isl.id] != isl.value:
                    return False
            graph = {isl.id: [] for isl in self.grid.islands}

            for i, count in assign.items():
                if count > 0:
                    u, v = self.potential_edges[i]
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

        u, v = self.potential_edges[idx]
        
        for val in [0, 1, 2]:
            if island_counts[u.id] + val > u.value or island_counts[v.id] + val > v.value:
                continue

            if val > 0:
                if self.is_crossing_with_assigned(self.potential_edges[idx], val, assign):
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
    
    def is_crossing_with_assigned(self, current_edge, val, assign):
        u1, v1 = current_edge
        for i, count in assign.items():
            if count > 0:
                u2, v2 = self.potential_edges[i]
                if self.check_cross(u1, v1, u2, v2):
                    return True
        return False

    def check_cross(self, u1, v1, u2, v2):
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
