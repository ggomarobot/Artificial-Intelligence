################################################################
#
#                        astar_search.py
#                        (non-optimized version)
#
#     Assignment 01:  Heuristic A* Search
#     Author       :  Gun Yang (gyang04)
#     Date         :  June 17th 2022
#
#     Purpose      : a program that searches for shortest paths
#                    between two cities using A* search.
#                    
#                    This basic implementation of A* search
#                    allows a single city to repeat multiple times
#                    during a search path (which causes inefficiency)
#
################################################################

import sys
import re
import heapq
import math

# global variables
start_city = None
goal_city = None
cities = {}
city_count = 0
node_count = None
frontier_count = None

# a class to store information of cities from input file
class city_info:
    def __init__(self, latitude, longitude):
       self.latitude = latitude
       self.longitude = longitude
       self.neighbors = {}

# heuristic function for A* algorithm
def haversine(start, goal):    
    
    # longitude and latitude of the starting point    
    start_lon = cities[start].longitude
    start_lat = cities[start].latitude
    # longitude and latitude of the end point
    goal_lon = cities[goal].longitude
    goal_lat = cities[goal].latitude

    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [start_lon, start_lat, goal_lon, goal_lat])

    # haversine formula (in miles)
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.pow(math.sin(dlat/2),2) + math.cos(lat1) * math.cos(lat2) * math.pow(math.sin(dlon/2),2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = 3961 * c
    
    return distance

# a class to store each city as a node (to populate a search graph)
class city_node:
    def __init__(self, name = None, g_cost= 0, parent = None):
        self.name = name
        self.children = cities[self.name].neighbors
        self.g_cost = g_cost
        self.h_cost = haversine(self.name, goal_city)
        self.f_cost = self.g_cost + self.h_cost
        self.parent = parent
        
    def __lt__(self, next_node):
        return self.f_cost < next_node.f_cost
    
    def __str__(self):
        return str(self.name)

    def isGoal(self):
        global goal_city
        return str(self) == str(goal_city)
    

# a function to read an input file that contains information of cities
def parse_city_data_file(data_file):

    city_data_regex = re.compile(r"(?P<city>^.+) "
                                 r"(?P<lat>-*\d+\.\d+) "
                                 r"(?P<lon>-*\d+\.\d+)"
                                 )

    city_distance_regex = re.compile(r"(?P<city1>^.+), "
                                     r"(?P<city2>.+): "
                                     r"(?P<dist>-?\d+.\d+)"
                                    )

    global city_count
    global cities
    
    city_file = open(data_file)
    # read the input file line by line
    for line in city_file.readlines():
        city_result = city_data_regex.search(line)
        city_distance_result = city_distance_regex.search(line)
        
        if city_result != None:
            city_name = city_result.group('city')
            latitude = float(city_result.group('lat'))
            longitude = float(city_result.group('lon'))
    
            city_count = city_count + 1
            # create a key value pair that matches a city name with its lat / lon values
            new_city = city_info(latitude, longitude)
            # store it in the dictionary
            cities[city_name] = new_city

        elif city_distance_result != None:
            city1_name = city_distance_result.group('city1')
            city2_name = city_distance_result.group('city2')
            distance = float(city_distance_result.group('dist'))

            cities[city1_name].neighbors[city2_name] = distance
            cities[city2_name].neighbors[city1_name] = distance

    print('Reading city data... Done.\n')
    print('Number of cities: ' + str(city_count))

# a function to get starting city / goal city from user    
def prompt_user():
    
    global start_city
    start_city = input("Please enter name of start city (0 to quit): ")
    # repeat until the user enters a valid city name
    while (start_city not in cities) and (start_city != "0"):
        print("City not found from the input file. please enter a valid city name.")
        start_city = input("Please enter name of start city (0 to quit): ")
    # if the user enters the number 0, terminate the program
    if start_city == "0":
        sys.exit("Goodbye.") 
 
    global goal_city
    goal_city = input("Please enter name of end city (0 to quit)  : ")
    # repeat until the user enters a valid city name
    while (goal_city not in cities) and (goal_city!= "0"):
        print("City not found from the input file. please enter a valid city name.")
        goal_city = input("Please enter name of end city (0 to quit)  : ")
    # if the user enters the number 0, terminate the program
    if goal_city == "0":
        sys.exit("Goodbye.")

# a function to perfrom A* search
def astar_search(start_city, goal_city):
    
    print("\nSearching for path from {} to {}...".format(start_city, goal_city))
    print("Target found: {} {} {}\n".format(goal_city, cities[goal_city].latitude, cities[goal_city].longitude))
    # populate a graph using the given starting / goal cities
    start = city_node(start_city, 0)
    frontier = [start]
    heapq.heapify(frontier)
    reached = {str(start): start}

    global node_count
    global frontier_count
    node_count = 1

    while frontier:
    
        node = heapq.heappop(frontier)

        if node.isGoal():
            frontier_count = len(frontier)
            return node
        
        for city in node.children:
            child = city_node(city, node.g_cost + node.children[city], node)
            heapq.heappush(frontier, child)
            node_count += 1
    
    frontier_count = len(frontier)
    return None

# a function to nicely print out the result
def printSolution(solution_node):

    if solution_node == None:
        print("NO PATH")
        print("Distance: -1 miles\n")
        return
    
    solution_path = [solution_node]
    parent = solution_node.parent
    
    while parent != None:
        solution_path.insert(0, parent)
        parent = parent.parent

    number_of_nodes = len(solution_path)
    
    if number_of_nodes == 1:
        print("Route found: Started at goal; no travel necessary!")       
        
    else:
        print("Route found: {}".format(str(solution_path[0])), end = '')
        
        for i in range(1, len(solution_path)):
            print(" -> {}".format(str(solution_path[i])), end = '')
        
        print("")
        
    print("Distance: {0:.1f} miles\n".format(solution_node.f_cost))

    
# the main driver of this A* search program
def main():
    # read in filename
    filename = sys.argv[1]
    # process city data in that file
    parse_city_data_file(filename)

    while(True):
        # prompt user for input
        prompt_user()
        # A* search begins
        solution = astar_search(start_city, goal_city)
        # print out the result
        printSolution(solution)
        print("Total nodes generated : {}".format(node_count))
        print("Nodes left in frontier: {}".format(frontier_count))
        
        print("\n-----------------------------")
        continue_search = input("Enter 0 to quit, or any other keys to search again: ")
        
        if continue_search == "0":
            sys.exit("\nGoodbye.")
        
        print("-----------------------------\n")

main()
