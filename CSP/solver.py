################################################################
#
#                           solver.py
#
#     Assignment 02:  Constraint Satisfaction Solver
#     Author       :  Gun Yang (gyang04)
#     Date         :  June 30th 2022
#
#     Purpose      : a program that uses CSP techniques to
#                    attempt to find a combination of words
#                    from the dictionary that will fill in 
#                    the crossword grid
#
################################################################

from curses.ascii import isalpha
import sys
import re
from collections import deque

################ global variables ################
recursion_counter = 0
height = 0
width = 0
# a 2D array of size height x width that contains all the grids for the given puzzle
puzzle_board = []
# a list that contains all the word-variables
words = []
# a set of grids where intersection between word-variables happens
constraints = set()
# a dictionary of english words to be used to solve the crossword puzzle (key: word length)
dictionary = {}
##################################################

# a class that represents a Constraint Satisfaction Problem to be solved
class csp:
    def __init__(self, unassigned_var = [], constraints = set()):
        self.unassigned_var = unassigned_var.copy()
        self.constraints = constraints.copy()
          
# a class that represents an arc (edge) between two word-variables (Xi, Xj)
# Xi index / Xj index indicate where the intersection happens
class arc:
    def __init__(self, Xi = None, Xj = None, Xi_idx = 0, Xj_idx = 0):
        self.Xi = Xi
        self.Xj = Xj
        self.Xi_idx = Xi_idx
        self.Xj_idx = Xj_idx

    def __str__(self):
        arc_name = str(self.Xi) + " " + str(self.Xj)
        return arc_name

# a class to represent each word-variable
class word:
    def __init__(self, number = 0, direction = "across", word = "NO_VALUE",
                 start_coord = (0, 0), length = 0, domain_size = 0,
                 constraining_power = 0):
        self.number = number
        self.direction = direction
        self.word = word
        self.start_coord = start_coord
        # list of all the grids that this variable uses in the board
        self.grid_positions = []
        self.length = length
        self.domain = []
        self.domain_size = domain_size
        # list of other word-variables that this variable intersects with
        self.neighbors = []
        self.constraining_power = constraining_power
        
    def __lt__(self, other):
        return self.domain_size < other.domain_size
    
    def __str__(self):
        full_name = (self.number, self.direction)
        return str(full_name)
    
# a class to represent each coordinates of a puzzle board
class grid:
    def __init__(self, coordinates = (0, 0)):
        self.coordinates = coordinates
        self.character = None
        self.black_square = False
        # list of word-variables that occupy this grid
        self.occupied = []
        
    def __lt__(self, other):
        return len(self.occupied) < len(other.occupied)
    
    def __str__(self):
        return str(self.coordinates)

# a function to create a word dictionary from a given word file
def create_dictionary(second_input):
    dictionary_file = open(second_input)
    # read the input file line by line
    for line in dictionary_file.readlines():
        new_word = line.rstrip()
        word_length = len(new_word)
        # store each word in the dictionary, using its length as a key
        if word_length in dictionary:
            dictionary[word_length].append(new_word)
        else:
            dictionary[word_length] = [new_word]


# a function to decide word-varible's direction
# ("across" words always have a puzzle edge or a black square to the left of their number)
def check_across(row, col):
    return (col == 0) or (puzzle_board[row][col - 1].black_square)

# a function to decide word-varible's direction
# ("down" words always have a puzzle edge or a black square above their number)
def check_down(row, col):
    return (row == 0) or (puzzle_board[row - 1][col].black_square)

# a function to create a puzzle board from a given puzzle spec file
def process_grid(first_input):
    # regular expression to read height and width of a puzzle board
    grid_size_regex = re.compile(r"(?P<height>[0-9]+) "
                                 r"(?P<width>[0-9]+)"
                                )
    
    first_line_checker = True
    row_counter = 0
    col_counter = 0
    
    # a variable to check whether the current grid is being occupied by two word-variables
    # i.e.) grid (0, 0) is used by 1-across / 1-down
    intersect_checker = 0
    
    puzzle_file = open(first_input, "r")
    puzzle_line = puzzle_file.readline().rstrip()
    
    while puzzle_line:
        if first_line_checker == True:
            grid_spec = grid_size_regex.search(puzzle_line)
            
            if grid_spec != None:
                global height
                global width
                height = int(grid_spec.group('height'))
                width = int(grid_spec.group('width'))
                # creates a puzzle board using height and width
                initialize_grid(height, width)
                
            first_line_checker = False
            puzzle_line = puzzle_file.readline().rstrip()
        else:
            elem = puzzle_line.split()
            for i in elem:
                # if current character is a number, create a word-variable
                if i.isnumeric():
                    if (check_across(row_counter, col_counter)):
                        intersect_checker += 1
                        new_word = word(int(i), "across", start_coord = (row_counter, col_counter))
                        # add it to a "words" list
                        words.append(new_word)
                        # add it to a corresponding coordinates' occupied list
                        puzzle_board[row_counter][col_counter].occupied.append((new_word, 0))
                        
                    if (check_down(row_counter, col_counter)):
                        new_word = word(int(i), "down", start_coord = (row_counter, col_counter))
                        # add it to a "words" list
                        words.append(new_word)
                        intersect_checker += 1
                        if intersect_checker == 2:
                            # if current character creates two word-variables ("across" and "down"),
                            # add current coordinates to a "constraints" set
                            constraints.add(puzzle_board[row_counter][col_counter])
                        # add it to a corresponding coordinates' occupied list   
                        puzzle_board[row_counter][col_counter].occupied.append((new_word, 0))
                        
                    intersect_checker = 0
                # if current character is an alphabet, treat it as a black square ('X')     
                elif isalpha(i):
                    puzzle_board[row_counter][col_counter].character = " "
                    puzzle_board[row_counter][col_counter].black_square = True
                  
                col_counter += 1
                
            row_counter += 1
            col_counter = 0

            puzzle_line = puzzle_file.readline().rstrip()
            
    puzzle_file.close()

# a function to create a 2D array of grids (a puzzle board)
def initialize_grid(height, width):
    
    for i in range(height):
        single_row = []
        for j in range(width):
            single_square = grid((i, j))
            single_row.append(single_square)
        puzzle_board.append(single_row)

# a function to update each word-variable's length
def update_words_len():
    for puzzle_word in words:
        x = puzzle_word.start_coord[0]
        y = puzzle_word.start_coord[1]
        # add the starting coordinates to the "grid_positions" list
        puzzle_word.grid_positions.append(puzzle_board[x][y])
        
        word_index = 1
        
        # if the direction is "across", traverse in y direction (vertical)
        # until the max width or a black square has reached
        if puzzle_word.direction == "across":
            y += 1
            while (y < width) and (not puzzle_board[x][y].black_square):
                puzzle_word.grid_positions.append(puzzle_board[x][y])
                # check if a word-variable already exists before we append current word variable
                curr_intersection_counter = len(puzzle_board[x][y].occupied)
                puzzle_board[x][y].occupied.append((puzzle_word, word_index))

                # if there was, we've found an intersection, so add the current coordinates to the "constraints" set
                if curr_intersection_counter == 1:
                    constraints.add(puzzle_board[x][y])
                         
                word_index += 1
                y += 1
                
        # if the direction is "down", traverse in x direction (horizontal)
        # until the max height or a black square has reached                
        else:
            x += 1
            while (x < height) and (not puzzle_board[x][y].black_square):
                puzzle_word.grid_positions.append(puzzle_board[x][y])
                # check if a word-variable already exists before we append current word variable
                curr_intersection_counter = len(puzzle_board[x][y].occupied)
                puzzle_board[x][y].occupied.append((puzzle_word, word_index))
                
                # if there was, we've found an intersection, so add the current coordinates to the "constraints" set
                if curr_intersection_counter == 1:
                        constraints.add(puzzle_board[x][y])
                        
                word_index += 1
                x += 1
        
        # update the word-variable's length
        puzzle_word.length = len(puzzle_word.grid_positions)

# a function to update each word-variable's domain and constraining power
def update_domain_and_constraints():
    for puzzle_word in words:
        # if our dictionary has a key of current word-variable's length
        # copy that value (vocabulary list) to current word-variable's domain
        if puzzle_word.length in dictionary:
            puzzle_word.domain = dictionary[puzzle_word.length].copy()
            domain_size = len(puzzle_word.domain)
            puzzle_word.domain_size = domain_size
            
        # for each square that this word-variable occupies, check whether it intersects with another word-variable
        for character in puzzle_word.grid_positions:
            # if current coordinates is found in the "constraints" set, increment constraining power by 1
            if character in constraints:
                puzzle_word.constraining_power += 1

# a recursive function to find a solution to Constraint Satisfaction Problem 
def backtrack(empty_puzzle, assignment):
    global recursion_counter
    recursion_counter += 1
    
    if (not empty_puzzle.unassigned_var):
        # return assignment
        return True, assignment
    
    # if the queue is not empty, pop the next word-variable off the queue    
    curr_word = empty_puzzle.unassigned_var[0]
    curr_word.domain_size = len(curr_word.domain)
    # if no possible english word candidates are left to test, return false
    if curr_word.domain_size == 0:
        return False, []
    
    # if not, check if a word candidate satisfies all the existing constraints in the current branch
    for idx in range(len(curr_word.domain)):
        candidate = curr_word.domain[idx]
        satisfied = True
        
        for i in range(curr_word.length):
            # check if any of the coordinates is shared with another word variable
            if len(curr_word.grid_positions[i].occupied) > 1:
                intersection = curr_word.grid_positions[i].occupied
                
                #if it does, find another word variable and check if constraints exist in the current branch
                for j in range(len(intersection)):
                    if (str(intersection[j][0]) != str(curr_word)):
                        other_word = intersection[j][0]
                        other_char_index = intersection[j][1]

                        if other_word in empty_puzzle.constraints:
                            if candidate[i] != other_word.word[other_char_index]:
                                satisfied = False
                                
        # after iterating through all the grid locations for the candidate
        # if the candidate satisfies all the constraints, assign it to the current word-variable
        if satisfied == True:    
            curr_word.word = candidate
            assignment.add(curr_word)
            empty_puzzle.unassigned_var.pop(0)
            empty_puzzle.constraints.add(curr_word)
            # move to the next word-variable
            success, result = backtrack(empty_puzzle, assignment)
            # if the result was success, return true
            if success:
                return True, result
            # if not, reset the assignment / constraints for the current word-variable, and try other candidates 
            else:
                assignment.remove(curr_word)
                empty_puzzle.unassigned_var.insert(0, curr_word)
                empty_puzzle.constraints.remove(curr_word)
                
    # if the function reaches this line, that means there is no possible solution
    return False, []

# Arc Consistency Algorithm #3 to pre-process constraint satisfaction problem 
def AC3_preprocess(empty_puzzle):
    arc_queue = deque()
    arc_dict = {}
    
    # create all the arcs in csp
    for idx in range(len(empty_puzzle.unassigned_var)):
        Xi = empty_puzzle.unassigned_var[idx]
        for i in range(Xi.length):
            if len(Xi.grid_positions[i].occupied) > 1:
                intersection = Xi.grid_positions[i].occupied
                for j in range(len(intersection)):
                    if (str(intersection[j][0]) != str(Xi)):
                        Xj = intersection[j][0]
                        Xj_idx = intersection[j][1]
                        
                        Xi_idx = i
                        # add Xj to Xi's neighbors for easier access
                        Xi.neighbors.append(Xj)
                        # create a new arc with the given information
                        new_arc = arc(Xi, Xj, Xi_idx, Xj_idx)
                        # store this arc in arc dictionary for easier access
                        arc_dict[str(new_arc)] = new_arc
                        # add it to the arc queue
                        arc_queue.append(new_arc)
             
    while arc_queue:
        # get next arc in the queue
        curr_arc = arc_queue.pop()
        # if we need to revise Xi's domain,
        # add Xi's neighbors(except Xj)' arcs back to the arc queue
        if revise(curr_arc):
            Xi = curr_arc.Xi
            Xj = curr_arc.Xj
            
            if Xi.domain_size == 0:
                return False
            
            for i in range(len(Xi.neighbors)):
                if Xi.neighbors[i] != Xj:
                    Xk = Xi.neighbors[i]
                    # construct Xk's corresponding arc dictionary key
                    dict_key = str(Xk) + " " + str(Xi)
                    # grab its value
                    Xk_arc = arc_dict[str(dict_key)]
                    arc_queue.append(Xk_arc)
                    
    return True

# a helper function for AC-3 to check if the domain of Xi needs to be changed
def revise(curr_arc):
    revision = False
    
    Xi = curr_arc.Xi
    Xi_idx = curr_arc.Xi_idx
    Xj = curr_arc.Xj
    Xj_idx = curr_arc.Xj_idx

    new_domain = []
    
    for i in range(len(Xi.domain)):
        match = False
        for j in range(len(Xj.domain)):
            if Xi.domain[i][Xi_idx] == Xj.domain[j][Xj_idx]:
                # if there is a possible solution, do not search anymore and break the loop
                match = True
                break
        # if the current candidate couldn't satisfy the constraints, we need to remove it from Xi's domain
        if match == False:
            revision = True
        # if the current candidate passed all the constraints tests, we keep it in Xi's domain
        else:
            new_domain.append(Xi.domain[i])

    # update Xi's domain
    Xi.domain = new_domain
    Xi.domain_size = len(new_domain)
    
    return revision

# the main driver of the Puzzle Solver program
def main():
    arg_len = len(sys.argv)
    
    if arg_len == 3:
        # puzzle specification file
        first_input = sys.argv[1]
        # word file
        second_input = sys.argv[2]

        create_dictionary(second_input)
        process_grid(first_input)
        update_words_len()
        update_domain_and_constraints()

        print("\n{} words".format(len(words)))
        print("{} constraints\n".format(len(constraints)))

        print("Initial assignment and domain sizes:")
        for puzzle_word in words:
            print("{}-{} = {} ({} values possible)".format(puzzle_word.number, puzzle_word.direction, puzzle_word.word, puzzle_word.domain_size))

        empty_puzzle = csp(words)
        
        # sort variables using the Most-Constrained Variable heuristic
        # additionally, use the Most Constraining Variable heuristic to break ties
        unassigned_var = sorted(empty_puzzle.unassigned_var, key=lambda k: (k.domain_size, k.constraining_power * -1))
        empty_puzzle.unassigned_var = unassigned_var
        
        assignment = set()
        validity_checker, solution = backtrack(empty_puzzle, assignment)  
        
        if (validity_checker):
            print("\nSUCCESS! Solution found after {} recursive calls to search.\n".format(recursion_counter))

            while (solution):
                current_variable = solution.pop()
                for i in range(len(current_variable.word)):
                    current_variable.grid_positions[i].character = current_variable.word[i]
            
            for row in range(height):
                for col in range(width):
                    print("{}".format(puzzle_board[row][col].character),end = "")
                print("")
            print("")
        else:
            print("\nFAIL: No solution found after {} recursive calls to search.\n".format(recursion_counter))
        
    elif arg_len == 4:
        # puzzle specification file
        first_input = sys.argv[1]
        # word file
        second_input = sys.argv[2]
    
        create_dictionary(second_input)
        process_grid(first_input)
        update_words_len()
        update_domain_and_constraints()

        print("\n{} words".format(len(words)))
        print("{} constraints\n".format(len(constraints)))

        print("Initial assignment and domain sizes:")
        for puzzle_word in words:
            print("{}-{} = {} ({} values possible)".format(puzzle_word.number, puzzle_word.direction, puzzle_word.word, puzzle_word.domain_size))
            
        empty_puzzle = csp(words)

        print("\nDoing arc-consistency pre-processing...\n")

        AC3_result = AC3_preprocess(empty_puzzle)

        print("Initial assignment with pre-processed domain sizes:")        
        for processed_word in empty_puzzle.unassigned_var:
            print("{}-{} = {} ({} values possible)".format(processed_word.number, processed_word.direction, processed_word.word, processed_word.domain_size))

        # sort variables using the Most-Constrained Variable heuristic
        # additionally, use the Most Constraining Variable heuristic to break ties
        unassigned_var = sorted(empty_puzzle.unassigned_var, key=lambda k: (k.domain_size, k.constraining_power * -1))

        if AC3_result:
            empty_puzzle.unassigned_var = unassigned_var
            assignment = set()
            
            validity_checker, solution = backtrack(empty_puzzle, assignment)  
            
            if (validity_checker):
                print("\nSUCCESS! Solution found after {} recursive calls to search.\n".format(recursion_counter))
                
                while (solution):
                    current_variable = solution.pop()
                    for i in range(len(current_variable.word)):
                        current_variable.grid_positions[i].character = current_variable.word[i]
                
                for row in range(height):
                    for col in range(width):
                        print("{}".format(puzzle_board[row][col].character),end = "")
                    print("")
                print("")
            else:
                print("\nFAIL: No solution found after {} recursive calls to search.\n".format(recursion_counter))
        else:
            print("\nFAIL: Did not pass the AC-3 pre-processing step. No solution exists.\n")
    else:
        print("failed to proceed. please provide correct number of arguments.\n")

main()
