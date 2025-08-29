import itertools
import math
import os
import json
import jsbeautifier
import psutil
import time
import timeit

from multiprocessing import Process, Lock, Value, Array
from pysat.solvers import *


def is_subset(block1, block2):
    block2_set = set(block2)
    for elem in block1:
        if elem not in block2_set:
            return False
    return True


def union(blocks):
    union_set = set()
    for block in blocks:
        union_set.update(block)
    return list(union_set)


def is_cff(blocks, d):
    n = len(blocks)
    for i in range(n):
        for j in range(1 << n):
            selected_blocks = []
            for k in range(n):
                if (j & (1 << k)) != 0 and k != i:
                    selected_blocks.append(blocks[k])
            if len(selected_blocks) == d:
                if is_subset(blocks[i], union(selected_blocks)):
                    return False
    return True


def _FindParallel(name, lock, solution, solutionExists, clauses):
    solver = Solver(name=name, bootstrap_with=clauses)
    sol = None
    clauses = None
    sol = solver.solve()
    model = solver.get_model()

    lock.acquire()
    try:
        if model != None and len(model) > 0:
            for i in range(len(solution)):
                solution[i] = model[i]
        if solutionExists.value == 0.0:
            if sol != None and sol:
                solutionExists.value = 1.0
            elif sol != None and not sol:
                solutionExists.value = -1.0
            else:
                solutionExists.value = -2.0
    finally:
        lock.release()


class CFFSATSolver:
    def __init__(self, k, d):
        self.k = k
        self.d = d
        self.t = math.ceil(d*1.5)
        self.n = self.t
        self.outputFolder = 'cffdata'
        self.filename = 'cffdata0.json'
        self.clauses = []
        self.timeout = 60
        self.timer = timeit.default_timer()
        self.lock = Lock()
        self.solutionExists = Value('d', 0.0)
        self.solution = Array('i', [])
        self.processes = []
        self.defaultSolverNames = ['glucose4', 'glucose3',
                                   'maplechrono', 'maplecm', 'maplesat', 'lingeling']
        self.outofmemory = False
        self.outofmemorySingleSolver = False
        self.singleSolverName = 'glucose4'
        self.solverNames = self.defaultSolverNames

    def CreateClausesDisjunctMatrices(self):
        self.clauses = []

        # Create cff representation matrix.
        m = []
        x = 1
        for row in range(self.t):
            v = []
            for column in range(self.n):
                v.append(x)
                x += 1
            m.append(v)

        # Initialize w variable.
        w = x

        # Get all combinations of columns, d + 1 by d + 1.
        columns_combinations = itertools.combinations(range(self.n), self.d+1)

        # For each combination of columns.
        for selected_columns in columns_combinations:
            # Create and fill auxilar matrix.
            w_m = [[0 for _ in range(self.n)] for _ in range(self.t)]
            for w_r in range(self.t):
                for w_c in selected_columns:
                    w_m[w_r][w_c] = w
                    w += 1

            # For each row.
            for row_ind in range(self.t):
                # For each column in selected columns.
                for col_ind in selected_columns:
                    # Iterate through selected columns.
                    for cursor in selected_columns:
                        if cursor == col_ind:
                            # w_m[row_ind][col_ind] => m[row_ind][cursor]
                            self.clauses.append(
                                [-w_m[row_ind][col_ind], m[row_ind][cursor]])
                        else:
                            # w_m[row_ind][col_ind] => -m[row_ind][cursor]
                            self.clauses.append(
                                [-w_m[row_ind][col_ind], -m[row_ind][cursor]])

            # For each column in selected columns.
            for col_ind in selected_columns:
                ws = []
                # For each row.
                for row_ind in range(self.t):
                    ws.append(w_m[row_ind][col_ind])
                self.clauses.append(ws[:])

    def CreateClausesWeightedK(self):
        self.clauses = []

        # Create cff representation matrix.
        m = []
        x = 1
        for row in range(self.t):
            v = []
            for column in range(self.n):
                v.append(x)
                x += 1
            m.append(v)

        # Initialize w variable.
        w = x

        # Get all combinations of columns, d + 1 by d + 1.
        columns_combinations = itertools.combinations(range(self.n), self.d+1)

        # For each combination of columns.
        for selected_columns in columns_combinations:
            # Create and fill auxilar matrix.
            w_m = [[0 for _ in range(self.n)] for _ in range(self.t)]
            for w_r in range(self.t):
                for w_c in selected_columns:
                    w_m[w_r][w_c] = w
                    w += 1

            # For each row.
            for row_ind in range(self.t):
                # For each column in selected columns.
                for col_ind in selected_columns:
                    # Iterate through selected columns.
                    for cursor in selected_columns:
                        if cursor == col_ind:
                            # w_m[row_ind][col_ind] => m[row_ind][cursor]
                            self.clauses.append(
                                [-w_m[row_ind][col_ind], m[row_ind][cursor]])
                        else:
                            # w_m[row_ind][col_ind] => -m[row_ind][cursor]
                            self.clauses.append(
                                [-w_m[row_ind][col_ind], -m[row_ind][cursor]])

            # For each column in selected columns.
            for col_ind in selected_columns:
                ws = []
                # For each row.
                for row_ind in range(self.t):
                    ws.append(w_m[row_ind][col_ind])
                self.clauses.append(ws[:])

        # Initialize z variable.
        z = w

        for row in range(self.t):
            zs = []
            columns_possibilities = itertools.combinations(
                range(self.n), self.n - self.k)
            for columns_posibility in columns_possibilities:
                zs.append(z)
                for column in columns_posibility:
                    self.clauses.append([-z, -m[row][column]])
                z += 1
            self.clauses.append(zs[:])

    def CreateClausesCyclicConstruction(self):
        self.clauses = []

        # Create cff representation matrix.
        m = []
        x = 1
        for row in range(self.t):
            v = []
            for column in range(self.n):
                v.append(x)
                x += 1
            m.append(v)

        # Get all combinations of columns, d by d.
        columns_combinations = []
        for i in range(self.n):
            combination = []
            for j in range(self.d):
                combination.append((i + j) % self.n)
            columns_combinations.append(combination[:])

        # Initialize y variable.
        y = x

        # The d columns dont cover themselves.
        for columns_combination in columns_combinations:
            for column in columns_combination:
                coveringColumns = columns_combination[:]
                coveringColumns.remove(column)

                # y means that the m[row][column] is not covered for a given combination.
                ys = []
                for row in range(self.t):
                    ys.append(y)
                    # If m[row][column] is false then it is covered.
                    self.clauses.append([m[row][column], -y])
                    for coveringColumn in coveringColumns:
                        # If m[row][coveringColumn] is true then it is covered.
                        self.clauses.append(
                            [-m[row][coveringColumn], -y])
                    y += 1
                self.clauses.append(ys)

        # The d columns dont cover any column.
        for coveringColumns in columns_combinations:
            otherColumns = [i for i in range(
                self.n) if i not in coveringColumns]
            for column in otherColumns:

                # y means that the m[row][column] is not covered for a given combination.
                ys = []
                for row in range(self.t):
                    ys.append(y)
                    # If m[row][column] is false then it is covered.
                    self.clauses.append([m[row][column], -y])
                    for coveringColumn in coveringColumns:
                        # If m[row][coveringColumn] is true then it is covered.
                        self.clauses.append(
                            [-m[row][coveringColumn], -y])
                    y += 1
                self.clauses.append(ys)

    def PrintSolution(self):
        print("k:", self.k, 'd:', self.d, 't:', self.t, 'n:', self.n, 
              'len(clauses):', len(self.clauses), "time:", self.time)

        if self.solutionExists.value == 1.0:
            blocks = [[] for _ in range(self.n)]

            for x in self.solution[0:self.n*self.t]:
                if x > 0:
                    blocks[(x-1) % self.n].append(((x-1) // self.n) + 1)

            # print("Is cff:", is_cff(blocks, self.d))
            # blocks = sorted(blocks, key=lambda x: sum(x))
            print('blocks:')
            for block in blocks:
                print(block, end=" ")
            print()

        elif self.solutionExists.value == -1.0:
            print('UNSAT')
        elif self.solutionExists.value == -2.0:
            print('UNKNOWN')
        elif self.solutionExists.value == -3.0:
            print('TIMEOUT')
        elif self.solutionExists.value == -4.0:
            print('OUTOFMEMORY')
        else:
            print('ERROR')

    def _set_filename(self, method_name):
        """
        Dynamically set filename based on the clause creation method and parameters.
        Example: cffdata/CreateClausesMehtodName/data_k_0_d_2.json
        """
        folder = os.path.join(self.outputFolder, method_name)
        os.makedirs(folder, exist_ok=True)
        self.filename = os.path.join(folder, f"data_k_{self.k}_d_{self.d}.json")

    def UpdateJson(self):
        blocks = []
        if self.solutionExists.value == 1.0:
            blocks = [[] for _ in range(self.n)]

            for x in self.solution[0:self.n*self.t]:
                if x > 0:
                    blocks[(x-1) % self.n].append(((x-1) // self.n) + 1)

            # blocks = sorted(blocks, key=lambda x: sum(x))

        try:
            with open(self.filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []

        objInData = [obj for obj in data if obj['d'] ==
                     self.d and obj['t'] == self.t and obj['n'] == self.n and obj['k'] == self.k]

        if len(objInData) == 0:
            newdata = {
                'k': self.k,
                'd': self.d,
                't': self.t,
                'n': self.n,
                'clauses': len(self.clauses),
                'time': self.time,    
            }

            if self.solutionExists.value == 1.0:
                newdata['solution'] = blocks
            elif self.solutionExists.value == -1.0:
                newdata['solution'] = 'UNSAT'
            elif self.solutionExists.value == -2.0:
                newdata['solution'] = 'UNKNOWN'
            elif self.solutionExists.value == -3.0:
                newdata['solution'] = 'TIMEOUT'
            elif self.solutionExists.value == -4.0:
                newdata['solution'] = 'OUTOFMEMORY'
            else:
                newdata['solution'] = 'ERROR'
            data.append(newdata)
        elif self.solutionExists.value == 1.0:
            sol = objInData[0]['solution']
            if sol != 'UNSAT':
                objInData[0]['solution'] = blocks
        elif self.solutionExists.value == -1.0:
            sol = objInData[0]['solution']
            if sol != 'UNSAT':
                objInData[0]['solution'] = 'UNSAT'

        data = sorted(data, key=lambda x: (x['k'], x['d'], x['t'], -x['n']))

        with open(self.filename, 'w') as jsonFile:
            opts = jsbeautifier.default_options()
            opts.indent_size = 2
            jsonFile.write(jsbeautifier.beautify(json.dumps(data), opts))

    def TerminateProcesses(self):
        self.lock.acquire()
        try:
            for p in self.processes:
                p.terminate()
        finally:
            self.lock.release()

    def SolutionCached(self):
        try:
            with open(self.filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []
        objInData = [obj for obj in data if obj['d'] ==
                     self.d and obj['t'] == self.t and obj['n'] == self.n and obj['k'] == self.k]

        if len(objInData) != 0 and isinstance(objInData[0]['solution'], list) and len(objInData[0]['solution']) != 0:
            print('d:', self.d, 'n:', self.n, 't:', self.t, 'k:', self.k)
            print('Solution already in json\n')
            self.solutionExists.value = 1.0
            return True
        elif len(objInData) != 0 and objInData[0]['solution'] == 'UNSAT':
            print('d:', self.d, 'n:', self.n, 't:', self.t, 'k:', self.k)
            print('Solution already in json\n')
            self.solutionExists.value = -1.0
            return True
        elif len(objInData) != 0 and (objInData[0]['solution'] == 'TIMEOUT' or objInData[0]['solution'] == 'OUTOFMEMORY'):
            if objInData[0]['time'] < self.timeout:
                return False
            else:
                print('d:', self.d, 'n:', self.n, 't:', self.t, 'k:', self.k)
                print('Solution already in json\n')
                return True
        else:
            return False

    def SwitchToSingleSolver(self, create_clauses_fn):
        self.outofmemory = True
        self.solverNames = [self.singleSolverName]
        self.TerminateProcesses()
        create_clauses_fn()
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.n * self.t)
        self.processes = []
        p = Process(target=_FindParallel, args=(self.singleSolverName,
                                                self.lock, self.solution, self.solutionExists, self.clauses))
        self.processes.append(p)
        p.start()

    def FindOneNoMemReset(self, create_clauses_fn):
        self._set_filename(create_clauses_fn.__name__)
        create_clauses_fn() 

        self.timer = timeit.default_timer()
        if self.SolutionCached():
            return

        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.n * self.t)
        self.processes = []

        for name in self.solverNames:
            p = Process(target=_FindParallel, args=(name, self.lock,
                                                    self.solution, self.solutionExists, self.clauses))
            self.processes.append(p)
            p.start()
            if psutil.virtual_memory()[2] > 90.0:
                break

        currentTime = 0.0
        while self.solutionExists.value == 0.0:
            time.sleep(0.1)
            currentTime += 0.1
            mempercent = psutil.virtual_memory()[2]
            if (mempercent > 95.0 and not self.outofmemory):
                self.SwitchToSingleSolver(create_clauses_fn)
            elif (mempercent > 95.0 and self.outofmemory):
                self.TerminateProcesses()
                self.solutionExists.value = -4.0
                self.outofmemorySingleSolver = True
            elif currentTime >= self.timeout:
                self.TerminateProcesses()
                self.solutionExists.value = -3.0

        self.TerminateProcesses()
        self.time = timeit.default_timer() - self.timer
        self.PrintSolution()
        self.UpdateJson()
        print()

    def FindOne(self, create_clauses_fn):
        self.solverNames = self.defaultSolverNames
        self.outofmemory = False
        self.outofmemorySingleSolver = False
        self.FindOneNoMemReset(create_clauses_fn)

    def FindAll(self, create_clauses_fn):
        self.solverNames = self.defaultSolverNames
        self.outofmemory = False
        self.outofmemorySingleSolver = False

        while not self.outofmemorySingleSolver:
            self.FindOneNoMemReset(create_clauses_fn)

            if self.solutionExists.value == 1.0:
                self.n += 1
            else:
                self.t += 1
                self.n = self.t

            if self.t == 40:
                break

if __name__ == '__main__':
    solver = CFFSATSolver(0, 3)
    # solver.FindOne()
    solver.FindAll(solver.CreateClausesCyclicConstruction)
