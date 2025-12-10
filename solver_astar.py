import time
from heapq import heappush, heappop
from utils import Grid
from cnf_builder import CNFBuilder

class AStarSolver(CNFBuilder):
    def __init__(self, grid: Grid):
        super().__init__(grid)
        
    def solve_astar_cnf(self):
        start_time = time.time()
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
        for (u, v) in self.grid.potential_edges:
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
                return self.decode_model(assign), time.time() - start_time

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

    