import argparse
from utils import read_input, write_output, format_output
from solver_sat import SATSolver
from solver_search import SearchSolver
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Hashiwokakero Solver")
    parser.add_argument("--input", type=str, required=True, help="Path to input file")
    parser.add_argument("--output", type=str, required=True, help="Path to output file")
    parser.add_argument("--method", type=str, default="sat", choices=["sat", "astar", "backtrack"], help="Method: sat, astar, backtrack")
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Input file `{args.input}` not found.")
        return

    print(f"Reading {args.input}...")
    grid = read_input(args.input)
    
    bridges = {}
    duration = 0
    
    if args.method == "sat":
        print("Solving using PySAT (CNF)...")
        solver = SATSolver(grid)
        import time
        t0 = time.time()
        bridges = solver.solve()
        duration = time.time() - t0
        
    elif args.method == "astar":
        print("Solving using A*...")
        searcher = SearchSolver(grid)
        bridges, duration = searcher.solve_astar()
        
    elif args.method == "backtrack": 
        print("Solving using Backtracking...")
        searcher = SearchSolver(grid)
        bridges, duration = searcher.solve_astar() 

    if bridges:
        print(f"Solved in {duration:.4f} seconds.")
        result_str = format_output(grid, bridges)
        write_output(args.output, result_str)
        print(f"Output written to {args.output}")
        print(result_str)
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()