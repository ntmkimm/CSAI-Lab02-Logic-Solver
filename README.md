# Project 02: Hashiwokakero Solver

**Course:** CSC14003 - Introduction to Artificial Intelligence  
**Institution:** University of Science - VNUHCM  

---

## 1. Group Members

| Student ID | Full Name             | 
|:----------:|:----------------------|
| 23122003   | Nguyễn Văn Linh       | 
| 23122022   | Trần Hoàng Gia Bảo    | 
| 23122026   | Trần Chấn Hiệp        | 
| 23122040   | Nguyễn Thị Mỹ Kim     |

---

## 2. Project Structure
The directory is organized as follows:

```text

├── Inputs/              # Input test cases (.txt)
│   ├── input-01.txt     
|   └── ...
├── Outputs/             # Generated solutions (.txt)
│   ├── output-01-astar.txt     
|   └── ...
├── main.py              # Entry point of the program
├── solver_sat.py        # SAT Solver logic (CNF generation)
├── solver_search.py     # Search algorithms (A*, Backtracking)
├── utils.py             # Helper functions (I/O, Grid parsing)
└── requirements.txt     # Python dependencies

## 3. Input/Output Format
A text file where numbers represent islands (1-8) and 0 represents empty water cells.
Examples:
```
0, 2, 0
0, 0, 0
2, 0, 2
```
After running solver, the result grid with bridges represented by special characters:
| : Single vertical bridge
$ : Double vertical bridge
- : Single horizontal bridge
= : Double horizontal bridge
"number" : Island value

Example:
```
[ "0" , "2" , "0" ]
[ "0" , "|" , "0" ]
[ "2" , "-" , "2" ]
```

## 4. How to Run
Run the program via the command line using main.py.
```
python main.py --input <input_file_path> --output <output_file_path> --method <algorithm>
```
Arguments:
--input: Path to the input text file (e.g., Inputs/input-01.txt).
--output: Path where the solution will be saved (e.g., Outputs/output-01.txt).
--method: The algorithm to use. Options are:
    sat : Logic-based solver using CNF (Recommended, fastest).
    astar : Heuristic search using A* Algorithm.
    backtrack: Brute-force/Backtracking algorithm (for comparison).

Examples
```
python main.py --input Inputs/input-01.txt --output Outputs/output-01_sat.txt --method sat
python main.py --input Inputs/input-02.txt --output Outputs/output-02_astar.txt --method astar
python main.py --input Inputs/input-03.txt --output Outputs/output-03_bt.txt --method backtrack
```