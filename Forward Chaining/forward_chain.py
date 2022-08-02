################################################################
#
#                        forward_chain.py
#
#     Assignment 03:  Forward Chaining for Propositional Inference
#     Author       :  Gun Yang (gyang04)
#     Date         :  July 15th 2022
#
#     Purpose      : This program is an implementation of
#                    the forward-chaining inference procedure 
#                    for propositional logic
#                    
#                   It prompts the user for a query,                   
#                   and then indicates whether the given input is
#                   entailed by the knowledge-base.
#
################################################################

import sys
import re
import heapq

################ global variables ################
'''
a dictionary that keeps track of symbols
we have seen during the forward-chaining process.
("is_entailed" function)

once we take a symbol out from the symbol queue,
we add that symbol to this dictionary
in order to prevent infinite loop of querying
the same symbol over and over again
'''
inferred = {}
##################################################

class knowledge_base:
    def __init__(self):
       self.conditional_clauses = list()
       self.propositional_symbols = list()

class clause:
    def __init__(self, original_string = None):
        self.original_string = original_string
        self.premise = list()
        # a count of the number of symbols in the premise
        self.premise_counter = 0
        self.conclusion = None
        
    def __lt__(self, other_clause):
        return self.premise_counter < other_clause.premise_counter

# a function to read an input file which will be our knowledge base
def parse_knowledge_base_file(knowledge_base_file):
    
    kb = knowledge_base()

    '''
    a propositional symbol is in the form "pX",
    where X is some positive integer value.
    (i.e., p3)
    '''
    # a regular expression to read a single propositional symbol
    single_regex = re.compile(r"(?P<single>^[p]\d(?=$))")
        
    '''
    a conditional clause consists of a tail,
    (a conjunction of propositional symbols using “AND” as our conjunction operator)
    followed by the conditional operator “THEN”,
    and a head consisting of a single propositional symbol.
    (i.e., p4 AND p5 THEN p6)
    '''
    # a regular expression to read head and tail of a conditional clause
    tail_regex = re.compile(r"(?P<tail>.+?(?=THEN))")
    head_regex = re.compile(r"(?P<head>(?<= THEN )[^.\s]*)")

    kb_file = open(knowledge_base_file)
    
    for line in kb_file.readlines():
        # check if the current line holds a conditional clause
        tail = tail_regex.search(line)
        head = head_regex.search(line)
        # check if the current line holds a propositional symbol
        propositional_symbol = single_regex.search(line)
    
        if (tail and head) != None:
            # create a new clause variable with the given string
            new_clause = clause(line)
            
            premise = tail.group('tail')
            premise_symbols = premise.split()

            for symbol in premise_symbols:
                # add all the propositional symbols in the premise
                if symbol != "AND":
                    new_clause.premise.append(symbol)
            new_clause.premise_counter = len(new_clause.premise)

            conclusion = head.group('head')
            new_clause.conclusion = conclusion
            
            # store current clause in our knowledge base
            kb.conditional_clauses.append(new_clause)
            
        elif propositional_symbol != None:
            new_symbol = propositional_symbol.group('single')
            # store current symbol in our knowledge base
            kb.propositional_symbols.append(new_symbol)
    
    return kb

# a querying function using forward-chaining algorithm
def is_entailed(kb, query):
    # if the query symbol already exists in our symbol database, just return true
    if query in kb.propositional_symbols:
        return True
    
    # a queue of symbols (initially just the propositional symbols in our knowledge-base)
    symbol_queue = kb.propositional_symbols.copy()
    heapq.heapify(symbol_queue)
    
    while (symbol_queue):
        symbol = heapq.heappop(symbol_queue)
        # if the current symbol is the query symbol, return true
        if symbol == query:
            return True
        
        global inferred
        # check if we have seen this symbol before
        if symbol not in inferred:
            # now that we have seen it, add this symbol to the dictionary
            inferred[symbol] = True
            # check if any clause in our knowledge-base contains the current symbol in its premise
            for clause in kb.conditional_clauses:
                if symbol in clause.premise:
                    # if it does, decrease its premise counter by 1
                    clause.premise_counter -= 1
                    # if the counter is down to 0, add the conclusion symbol to the symbol queue
                    if clause.premise_counter == 0:
                        heapq.heappush(symbol_queue, clause.conclusion)
                        # also update our knowledge-base (so that we don't have to repeat this process next round)
                        kb.propositional_symbols.append(clause.conclusion)
        
    return False

# the main driver of the forward chaining
def main():
    # create our knowledge-base from the given knowledge-base file
    kb_file = sys.argv[1]
    kb = parse_knowledge_base_file(kb_file)

    # print out how many clauses and symbols exist in the knowledge base
    print("KB has {} conditional clauses and {} propositional symbols.\n"
          .format(len(kb.conditional_clauses), len(kb.propositional_symbols)))

    # print out every conditional clause
    if len(kb.conditional_clauses) == 0:
        print("   Clauses: NONE")
    else:
        for i in range(len(kb.conditional_clauses)):
            if i == 0:
                print("   Clauses: {}".format(kb.conditional_clauses[i].original_string), end = '')
            else:
                print("            {}".format(kb.conditional_clauses[i].original_string), end = '')
    
    # print out every propositional symbol    
    if len(kb.propositional_symbols) == 0:
        print("\n   Symbols: NONE\n")
    elif len(kb.propositional_symbols) == 1:
        print("   Symbols: {}\n".format(kb.propositional_symbols[0]))        
    else:
        last_index = len(kb.propositional_symbols) - 1
        for i in range(len(kb.propositional_symbols)):
            if i == 0:
                print("   Symbols: {}, ".format(kb.propositional_symbols[i]), end = '')
            elif i == last_index:
                print("{}\n".format(kb.propositional_symbols[i]))
            else:
                print("{}, ".format(kb.propositional_symbols[i]), end = '')                


    while(True):
        # a propositional symbol in which user is interested
        query = input("Query symbol (or end): ")
        # if user entered "end", quit the program
        if query == "end":
            sys.exit()    

        answer = is_entailed(kb, query)
        
        if answer:
            print("Yes! {} is entailed by our knowledge-base.\n".format(query))
        else:
            print("No. {} is not entailed by our knowledge-base.\n".format(query))
    
main()