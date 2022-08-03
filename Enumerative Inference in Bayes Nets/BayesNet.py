################################################################
#
#                           BayesNet.py
#
#     Assignment 04:  Enumerative Inference for Bayes Nets
#     Author       :  Gun Yang (gyang04)
#     Date         :  July 31th 2022
#
#     Purpose      : This program is an implementation of
#                    an enumerative query algorithm for Bayes Nets
#
#                    Bayes Net is a probabilistic graphical model
#                    that represents a set of variables and
#                    their conditional dependencies via
#                    a directed acyclic graph (DAG)
#
################################################################

import sys
import re
import copy
from re import search
from tkinter import Variable
from collections import defaultdict

################ global variables ################
'''
before we start our inference by enumeration
we need to topologically sort the variables

during the sorting process,
we do not directly add the variables into the sorting list
but add the index of each variable

(we index variables in the order of appearance,
 as we read in the input file line by line)
 
we use "var_index_dict" to assign each variable an index value

and inside "ENUMERATE-ALL" function
we use "index_var_dict" to access variables by index values
'''
var_index_dict = {}
index_var_dict = {}
var_index_counter = 0
##################################################

# a class that represents a Bayes Net (Bayesian Network)
class bayes_net:
    def __init__(self):
       self.variables = list()
       # a dictionary that stores all the elements in the above list for an easier access
       self.var_dict = {}
       self.topological_graph = None
       
'''
referenced GeeksforGeeks on topological sorting
(https://www.geeksforgeeks.org/python-program-for-topological-sorting/)
'''
# a class that represents a directedf acyclic graph (DAG) to topologically sort Bayes Net variables
class directed_acyclic_graph:
    def __init__(self, vertices):
        self.graph = defaultdict(list)
        # number of variables in graph
        self.vertices = vertices
        self.result_stack = None
        
    def add_edge(self, parent, child):
        self.graph[parent].append(child)

    # a recursive function for topological sorting
    def topological_sort_helper(self, variable, visited, stack):

        # mark the current variable (a node in our graph) as visited
        visited[variable] = True

        # recursively sort all the vertices that are adjacent to the current node
        for vertex in self.graph[variable]:
            if not visited[vertex]:
                self.topological_sort_helper(vertex, visited, stack)

        # push current vertex to our stack
        stack.insert(0, variable)

    # a wrapper function for topological sorting
    def topological_sort(self):
        # mark all the vertices as not visited
        visited = [False] * self.vertices
        # a stack to store the result of topological sorting
        stack = []

        # sort recursively by calling helper function
        for i in range(self.vertices):
            if not visited[i]:
                self.topological_sort_helper(i, visited, stack)

        # store the result
        self.result_stack = stack

# a class that represents a variable in Bayes Net
class var:
    def __init__(self, name = None, values = list()):
       self.name = name
       self.values = values
       self.parents = None
       # conditional probability table for this variable
       self.CPT = list()
       
    def __str__(self):
        return self.name

# a class that represents each cell
# in conditional probability table of a variable
class CPT_cell:
    def __init__(self):
       # key: variable, value: value (e.g., Burglary = T)
       self.var_val_dic = {}
       self.probability = 0.0
       # a string that stores the combination of
       # values of a variable and its parents for each cell
       # (e.g., Burglary = T, Earthquake = T, Alarm = T)
       # mainly for debugging purpose
       self.string = ""

# a class that represents a query from user
class query:
    def __init__(self, variable = None, evidences = {}):
       # a variable that user wants to know its probability
       self.variable = variable
       # if there is no evidence,
       # output will be in the form of a distribution over
       # all the values of the query variable.
       self.evidences = evidences

# a class that represents an evidence             
class evidence:
    def __init__(self, variable = None, value = None):
       self.variable = variable
       self.value = value

# a function to read an input file which will be our Bayes Net
def parse_bayes_net_file(bayes_net_file):
    '''
    The file given into this program should have the following specific format of three distinct sections
    
    1. First, it shows each variable, with its possible values (e.g., T / F).
    
    2. Following the # Parents tag, we have the name of each variable, followed by its parents.
    
    3. Following the # Tables tag, we have the CPTs for each variable.
    '''
    
    # boolean instances to see which part of the file we are looking at
    create_vars = False
    assign_parents = False
    
    global var_index_dict
    global var_index_counter
    global index_var_dict
    
    bn = bayes_net()
    
    # a regular expression to read a variable and its values
    var_val_regex = re.compile(r"(?P<variable>^.+?(?=\s)) "
                               r"(?P<value>.*)"
                              )
    
    # a regular expression to read a child and its parents
    parent_child_regex = re.compile(r"(?P<child>^.+?(?=\s)) "
                                    r"(?P<parent>.*)"
                                   )
    
    bn_file = open(bayes_net_file, "r")
    bn_line = bn_file.readline().rstrip()
    
    while bn_line:
        # if we see the Parents tag,
        # we are done with initializing the variables in our Bayes Net
        if bn_line == "# Parents":
            create_vars = True
            bn_line = bn_file.readline().rstrip()
            total_num_vars = len(bn.variables)
            bn.topological_graph = directed_acyclic_graph(total_num_vars)
            
        # if we see the Tables tag,
        # we are done with connecting nodes (variables) in our Bayes Net model
        if bn_line == "# Tables":
            assign_parents = True
            bn_line = bn_file.readline().rstrip()
            
        # process the first section of the input: variable initialization
        if create_vars == False:

            var_and_val = var_val_regex.search(bn_line)
        
            if var_and_val != None:
                variable = var_and_val.group('variable')
                value_set = var_and_val.group('value')

                value = value_set.split()

                new_var = var(variable, value)
                
                # insert this new variable to our Bayes Net
                bn.variables.append(new_var)
                bn.var_dict[str(new_var)] = new_var
                var_index_dict[str(new_var)] = var_index_counter
                index_var_dict[var_index_counter] = new_var
                var_index_counter += 1
                bn_line = bn_file.readline().rstrip()

        # process the second section of the input: connecting variables
        elif assign_parents == False:

            parent_and_child = parent_child_regex.search(bn_line)
        
            if parent_and_child != None:

                child = parent_and_child.group('child')
                parent_set = parent_and_child.group('parent')
                
                parents = parent_set.split()
                
                if child in bn.var_dict:
                    curr_var = bn.var_dict[child]
                    curr_var.parents = parents
                    
                    child_index = var_index_dict[child]
                    
                    for parent in curr_var.parents:
                        parent_index = var_index_dict[parent]
                        bn.topological_graph.add_edge(parent_index, child_index)
                    
                else:
                    print("Wrong input file format")
                
                bn_line = bn_file.readline().rstrip()
                
        # process the third section of the input: create CPTs
        else:
            line_contents = bn_line.split()
            # an instance to accumulate the probability for each value of a variable
            sum = 0
            
            # current line has only one word (string)
            if len(line_contents) == 1:
                # and it is a variable in our Bayes Net
                if line_contents[0] in bn.var_dict:
                    curr_var = bn.var_dict[line_contents[0]]
                    curr_parents = curr_var.parents
                    curr_vals = curr_var.values
                    
                    # process CPT info for this variable
                    if (curr_parents == None):
                        
                        # if this variable does not have any parents,
                        # that means we do not have to care about a joint probability.
                        # so we just iterate over a 'values' list and assign probability for each value
                        
                        bn_line = bn_file.readline().rstrip()
                        line_contents = bn_line.split()

                        string_constructor = ""
                        
                        # we loop until one number short of its domain size (d),
                        # because our file only contain numbers for the first (d − 1) values of the variable
                        for i in range(len(curr_vals) - 1):
                            string_for_curr_val = string_constructor
                            string_for_curr_val += str(curr_var) + " = " + curr_vals[i]
                            
                            new_CPT_cell = CPT_cell()
                            new_CPT_cell.var_val_dic[str(curr_var)] = curr_vals[i]
                            new_CPT_cell.probability = float(line_contents[i])
                            new_CPT_cell.string = string_for_curr_val
                            
                            curr_var.CPT.append(new_CPT_cell)

                            sum += float(line_contents[i])

                        # process the last value for the variable, which is not given in the input file
                        last_val_index = len(curr_vals) - 1
                        string_constructor += str(curr_var) + " = " + str(curr_vals[last_val_index])
                        new_CPT_cell = CPT_cell()
                        new_CPT_cell.var_val_dic[str(curr_var)] = curr_vals[last_val_index]
                        new_CPT_cell.probability = 1 - sum
                        new_CPT_cell.string = string_constructor
                        curr_var.CPT.append(new_CPT_cell)

                        
                    # current variable has parent(s)
                    else:           
                        num_parents = len(curr_parents)
                        parents_combination_accumulator = 1
                        
                        # decide how many next lines we are going to read
                        '''
                        For example, if the current variable has two parents
                        and they all have two values T / F
                        then there would be 2 * 2 = 4 lines
                        that would specify the probabilities for each combination
                        T T
                        T F
                        F T
                        F F
                        '''
                        for parent in curr_parents:
                            parents_combination_accumulator *= len(bn.var_dict[parent].values)

                        while parents_combination_accumulator > 0:
                            bn_line = bn_file.readline().rstrip()
                            line_contents = bn_line.split()
                            parents_combination_accumulator -= 1
                            
                            string_constructor = ""
                            base_CPT_cell = CPT_cell()
                            
                            for i in range(num_parents):
                                string_constructor += str(curr_parents[i]) + " = " + line_contents[i] + ", "
                                base_CPT_cell.var_val_dic[str(curr_parents[i])] = line_contents[i]

                            index = num_parents

                            for i in range(len(curr_vals) - 1):
                                string_for_curr_val = string_constructor
                                string_for_curr_val += str(curr_var) + " = " + str(curr_vals[i])
                              
                                new_CPT_cell = copy.deepcopy(base_CPT_cell)
                                new_CPT_cell.var_val_dic[str(curr_var)] = curr_vals[i]
                                new_CPT_cell.probability = float(line_contents[index])
                                new_CPT_cell.string = string_for_curr_val

                                curr_var.CPT.append(new_CPT_cell)
                                
                                sum += float(line_contents[index])
                                index += 1
                            # process the last value for the variable, which is not given in the input file
                            last_val_index = len(curr_vals) - 1
                            string_constructor += str(curr_var) + " = " + curr_vals[last_val_index]

                            new_CPT_cell = copy.deepcopy(base_CPT_cell)
                            new_CPT_cell.var_val_dic[str(curr_var)] = curr_vals[last_val_index]
                            new_CPT_cell.probability = 1 - sum
                            new_CPT_cell.string = string_constructor
                            
                            curr_var.CPT.append(new_CPT_cell)
                            # set sum to 0 before reading the next line
                            sum = 0
                            
            elif len(line_contents) > 1:
                print("error occured. Wrong input file format")

            bn_line = bn_file.readline().rstrip()
    
    bn_file.close()        
    return bn

# a function to parse the query that user entered
def parse_query_command(query_var):

    # a regular expression to read a variable and a set of evidence
    var_regex = re.compile(r"(?P<variable>^.+?(?=\s))")
    evidence_regex = re.compile(r"(?P<evidence>(?<=\|)[^.\n]*)")

    # if there is '|' character in the query string,
    # we know that user also typed evidences for the query variable
    if query_var.find("|") != -1:

        variable_chunk = var_regex.search(query_var)
        evidence_chunk = evidence_regex.search(query_var)
        
        if variable_chunk and evidence_chunk != None:

            variable = variable_chunk.group('variable')
            evidence_set = evidence_chunk.group('evidence')

            evidences = evidence_set.split()
            
            index = 0
            evidence_dict = {}
            new_evidence = None
            
            for elem in evidences:
                '''
                since input will be in the format of
                "Burglary = T, Earthquake = F"
                after spliting,
                we know that variables are divisible by 3
                '''
                if index % 3 == 0:
                    new_evidence = evidence(elem)
                    evidence_dict[str(new_evidence.variable)] = new_evidence
                    
                elif index % 3 == 2:
                    # remove the possible ',' in the value chunk
                    value = elem.strip(',')
                    evidence_dict[str(new_evidence.variable)].value = value
        
                index += 1
           
            target = query(variable, evidence_dict)
            return target

    # if there is no '|', then no evidences are given
    else:
        variable = query_var.strip()
        target = query(variable)
        return target

# a function to return a distribution over X
def enumeration_ask(target, bn):

    query_var = bn.var_dict[target.variable]
    sorted_vars = bn.topological_graph.result_stack
    first_index = 0
    list_length = len(sorted_vars)
    evidences = target.evidences

    Q_of_X = list()
    
    for Xi in query_var.values:
        # we assign the current value (Xi) to the query variable
        # and put it in the evidence set
        evidences[str(query_var)] = evidence(query_var, Xi)
        # run Enumerate_All with the changed evidence set
        Q_of_Xi = enumerate_all(sorted_vars, first_index, list_length, evidences)
        # remove the current value (Xi)
        # so that we can assign other values of the query variable next round 
        del evidences[str(query_var)]
        
        Q_of_X.append(Q_of_Xi)  

    evidence_probability = enumerate_all(sorted_vars, first_index, list_length, evidences)

    P_of_X = list()
    
    for Xi in Q_of_X:
        P_of_X.append(Xi / evidence_probability)

    return P_of_X
    
# a function to return a distribution over X
def enumerate_all(vars, curr_index, list_length, evidences):
    # if the current index reaches the length of the list, stop the recursion
    if (curr_index >= list_length):
        return 1.0
    
    target = vars[curr_index]
    curr_var = index_var_dict[target]
    # check if the current variable is in the evidence set
    if str(curr_var) in evidences:

        value = evidences[str(curr_var)].value
        conditional_probability_for_val = 0.0
        
        # if the current variable has parents,
        # then we also need to check parents' values for the conditional probability
        if curr_var.parents != None:
            for cell in curr_var.CPT:
                # check if the value of the variable in the current cell matches
                # the value of the variable in the evidence set
                if cell.var_val_dic[str(curr_var)] == value:
                    
                    table_checker = True
                    
                    for parent in curr_var.parents:
                        if evidences[str(parent)].value != cell.var_val_dic[str(parent)]:
                            table_checker = False
                    # check if the values of the parents in the current cell match
                    # the values of the parents in the evidence set
                    if table_checker == True:
                        conditional_probability_for_val += cell.probability
                        
        # if the current variable has no parents
        # simply check the value of the variable
        else:
            for cell in curr_var.CPT:
                if cell.var_val_dic[str(curr_var)] == value:
                    conditional_probability_for_val += cell.probability
        
        return conditional_probability_for_val * enumerate_all(vars, curr_index + 1, list_length, evidences)
    

    # if the current variable is not in the evidence set
    # perform marginalization
    else:
        '''
        Marginalisation is a method that requires summing over the possible values of one variable
        to determine the marginal contribution of another
        '''
        summing_over_val = 0.0

        for value in curr_var.values:
            # we assign the current value to the marginalization target
            # and put it in the evidence set
            evidences[str(curr_var)] = evidence(curr_var, value)

            value = evidences[str(curr_var)].value
            conditional_probability_for_val = 0.0
            
            # if the current variable has parents,
            # then we also need to check parents' values for the conditional probability
            if curr_var.parents != None:
                for cell in curr_var.CPT:
                    # check if the value of the variable in the current cell matches
                    # the value of the variable in the evidence set
                    if cell.var_val_dic[str(curr_var)] == value:
                        
                        table_checker = True
                        
                        for parent in curr_var.parents:
                            if evidences[str(parent)].value != cell.var_val_dic[str(parent)]:
                                table_checker = False
                        # check if the values of the parents in the current cell match
                        # the values of the parents in the evidence set                        
                        if table_checker == True:
                            conditional_probability_for_val += cell.probability
                            
            # if the current variable has no parents
            # simply check the value of the variable
            else:
                for cell in curr_var.CPT:
                    if cell.var_val_dic[str(curr_var)] == value:
                        conditional_probability_for_val += cell.probability
            
            summing_over_val += conditional_probability_for_val * enumerate_all(vars, curr_index + 1, list_length, evidences)
            # remove the current value
            # so that we can assign other values of the marginalization target next round             
            del evidences[str(curr_var)]

        return summing_over_val

    
# the main driver of the Bayes Net program
def main():
    # create our Bayes Net from the given file
    bn_file = sys.argv[1]
    print("Loading file \"{}\"\n".format(bn_file))
    
    bn = parse_bayes_net_file(bn_file)
    bn.topological_graph.topological_sort()
    while(True):
        # a query variable of which user wants to know the conditional probability
        query_var = input()
        # if user entered "quit", quit the program
        if query_var == "quit":
            sys.exit()    

        target = parse_query_command(query_var)
        result = enumeration_ask(target, bn)

        target_var = bn.var_dict[target.variable]
        
        for i in range(len(result)):
            curr_val = target_var.values[i]
            P_of_Xi = float("%0.3f" % (result[i]))
            if (i == len(result) - 1):
                print("P({}) = {}\n".format(curr_val, P_of_Xi))
            else:
                print("P({}) = {}, ".format(curr_val, P_of_Xi), end = '')                

main()
