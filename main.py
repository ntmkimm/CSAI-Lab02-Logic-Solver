import argparse
from utils import read_input, write_output, format_output
from solver_sat import SATSolver
from solver_astar import AStarSolver
from solver_blind import BlindSolver
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description="Hashiwokakero Solver")
    parser.add_argument("--input", type=str, required=True, help="Path to input file")
    parser.add_argument("--method", type=str, default="sat", choices=["sat", "astar", "backtrack", "bruteforce"], help="Method: sat, astar, backtrack, bruteforce")
    
    args = parser.parse_args()
    input_file = Path(args.input)
    output_dir = Path('./Outputs')
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / (input_file.stem + f"_{args.method}.txt")
    
    if not input_file.exists():
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
        searcher = AStarSolver(grid)
        bridges, duration = searcher.solve_astar_cnf()
        
    elif args.method == "backtrack": 
        print("Solving using Backtracking...")
        searcher = BlindSolver(grid)
        bridges, duration = searcher.solve_backtracking() 
    elif args.method == "bruteforce":
        print("Solving using Bruteforce DFS")
        searcher = BlindSolver(grid)
        bridges, duration = searcher.solve_bruteforce_with_connectivity()

    if bridges:
        print(f"Solved in {duration:.4f} seconds.")
        result_str = format_output(grid, bridges)
        write_output(output_file, result_str)
        print(f"Output written to {str(output_file)}")
        print(result_str)
    else:
        print("No solution found.")

if __name__ == "__main__":
    main()