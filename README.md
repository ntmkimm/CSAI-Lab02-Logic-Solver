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
│   ├── output-01_astar.txt     
|   └── ...
├── main.py              # Entry point of the program
├── solver_sat.py        # SAT Solver logic (CNF generation)
├── solver_search.py     # Search algorithms (A*, Backtracking)
├── utils.py             # Helper functions (I/O, Grid parsing)
└── requirements.txt     # Python dependencies
```
## 3. Input/Output Format
### Input
A text file where numbers represent islands (1-8) and 0 represents empty water cells.
Examples:
```
0, 2, 0, 5, 0, 0, 2
0, 0, 0, 0, 0, 0, 0
4, 0, 2, 0, 2, 0, 4
0, 0, 0, 0, 0, 0, 0
0, 1, 0, 5, 0, 2, 0
0, 0, 0, 0, 0, 0, 0
4, 0, 0, 0, 0, 0, 3
```
### Output
The final grid with bridges represented by special characters:
  - `|` : Single vertical bridge
  - `$`: Double vertical bridge
  - `-` : Single horizontal bridge
  - `=` : Double horizontal bridge
  - `1..8` : Island value

Example:
```
[ "0" , "2" , "=" , "5" , "-" , "-" , "2" ]
[ "0" , "0" , "0" , "$" , "0" , "0" , "|" ]
[ "4" , "=" , "2" , "$" , "2" , "=" , "4" ]
[ "$" , "0" , "0" , "$" , "0" , "0" , "|" ]
[ "$" , "1" , "-" , "5" , "=" , "2" , "|" ]
[ "$" , "0" , "0" , "0" , "0" , "0" , "|" ]
[ "4" , "=" , "=" , "=" , "=" , "=" , "3" ]
```

## 4. How to Run
### Set up enviroment
```
pip install -r requirements.txt
```
### Run 
Run the program via terminal using main.py.
```
python main.py --input <input_file_path> --method <algorithm>
```
Arguments:
- input: Path to the input text file (e.g., Inputs/input-01.txt).
- method: The algorithm to use. Options: `sat` - Logic-based solver using CNF (Recommended, fastest); `astar` - Heuristic search using A* Algorithm; `backtrack` - Brute-force/Backtracking algorithm (for comparison).

Output file will be placed at `Outputs` folder, with filename as "input_file_stem_method.txt"

Examples
```
python main.py --input Inputs/input-01.txt --method sat
# output as `./Outputs/output-01_sat.txt`
python main.py --input Inputs/input-02.txt --method astar
# output as `./Outputs/output-02_astar.txt`
python main.py --input Inputs/input-03.txt --method backtrack
# output as `./Outputs/output-03_backtrack.txt`
```
