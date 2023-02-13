# author: Johan van Bruggen
# optimization library: PuLP

# import
import random
random.seed(10)             # let random numbers be the same every run
from pulp import *          # linear optimization
import time

# Start time
start_time = time.time()

########################################################
## Setup model

# setup model for maximizing
model = LpProblem(name="voorkeurenpuzzel", sense=LpMaximize)        

# modes:
# there are three different modes.
# if you would summarize 'a student having their preferences met' to 'a student being happy, then:
# the first mode just maximizes the happines of all students added up (freedom)
# the second mode maximizes on the group with lowest happiness to be as happy as possible
# the third group maximizes on the least happy student as happy as possible (equality)
m = 1               
if m == 1:
    mode = "brutalmax"                          
elif m == 2:
    mode = "maxongrouplowerbound"
elif m == 3:
    mode = "maxonindividuallowerbound"          

########################################################
## Define the decision variables
n_students = 9      # number of students in total
n_groups = 3        # number of groups

# groupsize
groupsize = n_students / n_groups

# indices for x_ij, x_ik, y_ijk
Indices_ij = ((i, j) for i in range(1, n_students+1) for j in range(1, n_students+1))
Indices_ik = ((i, k) for i in range(1, n_students+1) for k in range(1, n_groups+1))
Indices_ijk = ((i, j, k) for i in range(1, n_students+1) for j in range(1, n_students+1) for k in range(1, n_groups+1))

# variables
x_ij = pulp.LpVariable.dicts("x_ij", Indices_ij, cat="Binary")      # 1 if student i is a group with student j, 0 otherwise
x_ik = pulp.LpVariable.dicts("x_ik", Indices_ik, cat="Binary")      # 1 if student i is in group k, 0 otherwise
y_ijk = pulp.LpVariable.dicts("y_ijk", Indices_ijk, cat="Binary")   # 1 if student i and student j are in group k, 0 otherwise
if mode == "maxongrouplowerbound" or "maxonindividuallowerbound":   # maximizing on preference gives always a positive value
    lowerbound = pulp.LpVariable("lowerbound", lowBound=0, cat="Integer")

########################################################
## Parameters

# preferences-matrix
# A prefrence matrix is randomly generated. The matrix has a size n * n where n is the total number of students
# every student listed vertically gives his/her preference for every other student listed horizontally.

n_matrix = n_students           # matrix as big as there are students
                                # number of preference points that a student can give to other students,
                                # a bit random, a bit not
points_to_give = int(2.5 * int(0.6 * n_matrix) + (n_matrix - 2 - int(0.6 * n_matrix)) * 7.5 + 1 + 5.5)

preferences_matrix = []
i = 0
# while not yet every student has given their preference
while len(preferences_matrix) < n_students:

    x = 0
    preference = []
    # one student giving 60% of students a preference between 1 and 5
    for j in range(int(0.6 * n_matrix)):
        x = random.randint(1, 5)
        preference.append(x)            # add preference
    # and the same student giving 'all students minus 2 students minus 60% of all students' a preference between 6 and 9
    for j in range(n_matrix - 2 - int(0.6 * n_matrix)):
        x = random.randint(6, 9)
        preference.append(x)            # add preference
    # if, with a bit of luck, the number of preference points he still has left minus 1 is in between 1 and 9
    if (1 <= (points_to_give - sum(preference) - 1) <= 9):
        preference.append(points_to_give - sum(preference) - 1)     # add preference (left over points minus 1)
        random.shuffle(preference)                                  # shuffle
        preference.insert(i, 1)                                     # giving himself a preference of 1
        # add this preference of one student having for other students to the matrix
        preferences_matrix.append(preference)               
        i += 1

# actiontypes-matrix

# Vertical you can see students 1 till 9 having characteristics put horizontally:
# E = extravert, I = introvert, N = intuition, S = sensing,
# T = thinking, F = feeling, J = judging, P = perceiving
actiontype_matrix = [
#   [E, I, N, S, T, F, J, P]
    [0, 1, 0, 0, 0, 0, 0, 0], #1
    [0, 1, 0, 0, 0, 0, 0, 0], #2
    [0, 1, 0, 0, 0, 0, 0, 0], #3
    [1, 0, 0, 0, 0, 0, 0, 0], #4
    [0, 1, 0, 0, 0, 0, 0, 0], #5
    [1, 0, 0, 0, 0, 0, 0, 0], #6
    [0, 1, 0, 0, 0, 0, 0, 0], #7
    [1, 0, 0, 0, 0, 0, 0, 0], #8
    [1, 0, 0, 0, 0, 0, 0, 0]  #9
]

# programming experience matrix

# Vertical you can see students 1 till 9 having programming experience put horizontally:
# if a student has programming experience level 5, then column 1 until 5 are 1's and the rest are 0's.
programming_experience_matrix = [
#   [1, 2, 3, 4, 5, 6, 7, 8]
    [1, 1, 1, 1, 1, 1, 0, 0], #1
    [1, 1, 1, 1, 1, 1, 1, 0], #2
    [1, 1, 1, 1, 0, 0, 0, 0], #3
    [1, 1, 1, 0, 0, 0, 0, 0], #4
    [1, 1, 1, 0, 0, 0, 0, 0], #5
    [1, 1, 0, 0, 0, 0, 0, 0], #6
    [1, 1, 1, 1, 1, 1, 1, 1], #7
    [1, 1, 1, 1, 0, 0, 0, 0], #8
    [1, 1, 1, 1, 1, 1, 0, 0]  #9
]

########################################################
# Set the objective function
# objective function

if mode == "brutalmax":
    model += lpSum([preferences_matrix[i - 1][j - 1] * x_ij[(i, j)] for i in range(1, n_students + 1) for j in
                    range(1, n_students + 1)])

elif mode == "maxongrouplowerbound":
    model += lowerbound     # set a lowerbound, you want this lower bound as high as possible, but all solutions have to be above it
    for k in range(1, n_groups + 1):
        model += lpSum([preferences_matrix[i - 1][j - 1] * y_ijk[(i, j, k)] for i in range(1, n_students + 1) for j in
                        range(1, n_students + 1)]) >= lowerbound

elif mode == "maxonindividuallowerbound":
    model += lowerbound     # set a lowerbound, you want this lower bound as high as possible, but all solutions have to be above it
    for i in range(1, n_students + 1):
        for j in range(1, n_students + 1):
            model += preferences_matrix[i - 1][j - 1] * x_ij[(i, j)] >= lowerbound

########################################################
## Set logical and trivial constraints
# enforcing the relation: y_ijk = x_ij*x_jk
for i in range(1, n_students+1):
    for j in range(1, n_students+1):
        for k in range(1, n_groups+1):
            model += y_ijk[(i, j, k)] - x_ij[(i, j)] <= 0
            model += y_ijk[(i, j, k)] - x_ik[(i, k)] <= 0
            model += x_ij[(i, j)] + x_ik[(i, k)] - y_ijk[(i, j, k)] <= 1

# every student can be in only one group
for i in range(1, n_students+1):
    model += pulp.lpSum(x_ik[(i, k)] for k in range(1, n_groups+1)) == 1

# enforcing groupsize
for k in range(1, n_groups+1):
    model += pulp.lpSum(x_ik[(i, k)] for i in range(1, n_students+1)) >= groupsize
    model += pulp.lpSum(x_ik[(i, k)] for i in range(1, n_students+1)) <= groupsize

# every student is always with himself (triviaL)
for i in range(1, n_students+1):
    model += x_ij[(i, i)] == 1

for k in range(1, n_groups+1):
    model += pulp.lpSum(y_ijk[(i, i, k)] for i in range(1, n_students+1)) == groupsize

# if a first student joins a second student, then the second student joins the first student (trivial)
for i in range(1, n_students+1):
    for j in range(1, n_students+1):
        model += x_ij[(i, j)] - x_ij[(j, i)] == 0
        model += y_ijk[(i, j, k)] - y_ijk[(j, i, k)] == 0

# if two students join each other in a group, then they are in the same group (trivial)
for i in range(1, n_students+1):
    for j in range(1, n_students+1):
        for k in range(1, n_groups+1):
            model += y_ijk[(i, j, k)] - x_ik[(i, k)] <= 0
            model += y_ijk[(i, j, k)] - x_ik[(j, k)] <= 0
            model += x_ik[(i, k)] + x_ik[(j, k)] - y_ijk[(i, j, k)] <= 1

########################################################
## Set additional constraints
# changing the below variable adds more or less additional constraints, only in the order below,
# but if for example only the second constraint is wished to be active, then this code can be (easily) adapted

desired_number_of_additional_constraints = 0

if desired_number_of_additional_constraints >= 1:
    # every group has at least one person with 'extravert'-actiontype                                                       MIN 1 EXTRAVERT
    # =====
    for k in range(1, n_groups+1):
        model += lpSum([actiontype_matrix[i-1][0]*x_ik[(i, k)] for i in range(1, n_students+1)]) >= 1

if desired_number_of_additional_constraints >= 2:
    # every group has at least one person with programming level 5 or higher                                                MIN 1 PL 5 of hoger
    # =====
    for k in range(1, n_groups+1):
        model += lpSum([programming_experience_matrix[i-1][4] * x_ik[(i, k)] for i in range(1, n_students + 1)]) >= 1

if desired_number_of_additional_constraints >= 3:
    # every group has no more than one person with programming level 3 or lower                                             MAX 1 PL 3 of lager   
    # which is equivalent to 'students per group minus one have level 4 or higher', so similar as above
    # =====
    for k in range(1, n_groups+1):
        model += lpSum([programming_experience_matrix[i-1][3] * x_ik[(i, k)] for i in range(1, n_students + 1)]) >= 2

if desired_number_of_additional_constraints >= 4:
    # enforcing selected students to be in the same group                                                                   1 en 5 bij elkaar
    model += x_ij[(1,5)] == 1

if desired_number_of_additional_constraints >= 5:
    # enforcing selected students to be NOT in the same group                                                               1 en 8 niet bij elkaar
    model += x_ij[(1,8)] == 0

########################################################
## Solve model
model.solve()
# PULP_CBC_CMD(msg=0) tussen de haakjes hierboven laat geen tussentijdse berekeningen zien, laat die achterwege

# End time
end_time = time.time()

# computation_time = end_time - start_time
computation_time = 0.001 * int(1000 * (end_time - start_time))

########################################################
## Print input and output
print("---------------------")
print("INPUT:")
print("   ")
print("Number of students: " + str(n_students))
print("Number of groups: " + str(n_groups))
print("Points to give: " + str(points_to_give))
print("---------------------")
print("   ")
print("Preferences_matrix:")
for i in range(len(preferences_matrix)):
    print(preferences_matrix[i])
print("---------------------")
print("   ")
print("ActionType_matrix:")
print("[E, I, N, S, T, F, J, P]")
print(" ~  ~  ~  ~  ~  ~  ~  ~")
for i in range(len(actiontype_matrix)):
    print(actiontype_matrix[i])
print("---------------------")
print("   ")
print("ProgrammingExperience_matrix:")
print("[1, 2, 3, 4, 5, 6, 7, 8]")
print(" ~  ~  ~  ~  ~  ~  ~  ~")
for i in range(len(programming_experience_matrix)):
    print(programming_experience_matrix[i])
print("---------------------")
print("   ")
print("OUTPUT:")
print("   ")
print("Computation time: " + str(computation_time) + " [sec]")
print("Objective value: " + str(model.objective.value()))
print("---------------------")
print("   ")
print("These are the groups:")
for k in range(1, n_groups+1):
    string = "Group " + str(k) + ", consists of students: "
    for i in range(1, n_students+1):
        if x_ik[(i, k)].value() > 0:
            string += str(i) + ", "
    print(string)
print("---------------------")
print("   ")


    


