import itertools
import json
import jsbeautifier
import psutil
import time
import timeit

from multiprocessing import Process, Lock, Value, Array
from pysat.solvers import *
from operator import itemgetter


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
    def __init__(self):
        self.d = 2
        self.t = 1
        self.n = 1
        self.clauses = []
        self.timeout = 60*10
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

    def CreateClauses(self):
        t = self.t
        n = self.n
        d = self.d

        clauses = []
        m = []
        x = 1
        for row in range(t):
            v = []
            for column in range(n):
                v.append(x)
                x += 1
            m.append(v)

        w = x

        columns_combinations = itertools.combinations(range(n), d + 1)
        for selected_columns in columns_combinations:
            w_m = [[0 for _ in range(n)] for _ in range(t)]
            for w_r in range(t):
                for w_c in selected_columns:
                    w_m[w_r][w_c] = w
                    w += 1

            for row_ind in range(t):
                for col_ind in selected_columns:
                    for cursor in selected_columns:
                        if cursor == col_ind:
                            clauses.append(
                                [-w_m[row_ind][col_ind], m[row_ind][cursor]])
                        else:
                            clauses.append(
                                [-w_m[row_ind][col_ind], -m[row_ind][cursor]])

            for col_ind in selected_columns:
                ws = []
                for row_ind in range(t):
                    ws.append(w_m[row_ind][col_ind])
                clauses.append(ws[:])

        self.clauses = clauses

    def PrintSolution(self):
        if self.solutionExists.value == 1.0:
            blocks = [[] for _ in range(self.n)]

            for x in self.solution[0:self.n*self.t]:
                if x > 0:
                    blocks[(x-1) % self.n].append(((x-1) // self.n) + 1)

            # print("Is cff:", is_cff(blocks, self.d))
            blocks = sorted(blocks, key=lambda x: sum(x))
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

    def UpdateJson(self):
        blocks = []
        if self.solutionExists.value == 1.0:
            blocks = [[] for _ in range(self.n)]

            for x in self.solution[0:self.n*self.t]:
                if x > 0:
                    blocks[(x-1) % self.n].append(((x-1) // self.n) + 1)

            blocks = sorted(blocks, key=lambda x: sum(x))

        filename = 'cffdata.json'
        try:
            with open(filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []

        objInData = [obj for obj in data if obj['d'] ==
                     self.d and obj['t'] == self.t and obj['n'] == self.n]

        if len(objInData) == 0:
            newdata = {
                'd': self.d,
                't': self.t,
                'n': self.n
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

        data = sorted(data, key=itemgetter('d', 't', 'n'))

        with open(filename, 'w') as jsonFile:
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
        filename = 'cffdata.json'
        try:
            with open(filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []
        objInData = [obj for obj in data if obj['d'] ==
                     self.d and obj['t'] == self.t and obj['n'] == self.n]
        if len(objInData) != 0 and isinstance(objInData[0]['solution'], list) and len(objInData[0]['solution']) != 0:
            print('d:', self.d, 't:',
                  self.t, 'n:', self.n)
            print('Solution already in json\n')
            self.solutionExists.value = 1.0
            return True
        elif len(objInData) != 0 and objInData[0]['solution'] == 'UNSAT':
            print('d:', self.d, 't:',
                  self.t, 'n:', self.n)
            print('Solution already in json\n')
            self.solutionExists.value = -1.0
            return True
        else:
            return False

    def SetKwargsOne(self, **kwargs):
        if 'd' in kwargs:
            self.d = kwargs['d']
        if 't' in kwargs:
            self.t = kwargs['t']
        if 'n' in kwargs:
            self.n = kwargs['n']

    def SetKwargsAll(self, **kwargs):
        if 'd' in kwargs:
            self.d = kwargs['d']
        else:
            self.d = 2
        if 't' in kwargs:
            self.t = kwargs['t']
        else:
            self.t = 1
        if 'n' in kwargs:
            self.n = kwargs['n']
        else:
            self.n = 1

    def SwitchToSingleSolver(self):
        self.outofmemory = True
        self.solverNames = [self.singleSolverName]
        self.TerminateProcesses()
        self.CreateClauses()
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.n * self.t)
        self.processes = []
        p = Process(target=_FindParallel, args=(self.singleSolverName,
                                                self.lock, self.solution, self.solutionExists, self.clauses))
        self.processes.append(p)
        p.start()
        self.clauses = []

    def FindOneNoMemReset(self, **kwargs):
        self.timer = timeit.default_timer()
        # if self.SolutionCached():
        #     return

        self.CreateClauses()
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.n * self.t)
        print('d:', self.d, 't:', self.t, 'n:', self.n,
              'len(clauses):', len(self.clauses))
        self.processes = []

        for name in self.solverNames:
            p = Process(target=_FindParallel, args=(name, self.lock,
                                                    self.solution, self.solutionExists, self.clauses))
            self.processes.append(p)
            p.start()
            if psutil.virtual_memory()[2] > 90.0:
                break
        self.clauses = []

        currentTime = 0.0
        while self.solutionExists.value == 0.0:
            time.sleep(0.1)
            currentTime += 0.1
            mempercent = psutil.virtual_memory()[2]
            if (mempercent > 95.0 and not self.outofmemory):
                self.SwitchToSingleSolver()
            elif (mempercent > 95.0 and self.outofmemory):
                self.TerminateProcesses()
                self.solutionExists.value = -4.0
                self.outofmemorySingleSolver = True
            elif currentTime >= self.timeout:
                self.TerminateProcesses()
                self.solutionExists.value = -3.0

        self.TerminateProcesses()
        print('Time: ', timeit.default_timer() - self.timer)
        self.PrintSolution()
        self.UpdateJson()
        print()

    def FindOne(self, **kwargs):
        self.SetKwargsOne(**kwargs)
        self.solverNames = self.defaultSolverNames
        self.outofmemory = False
        self.outofmemorySingleSolver = False
        self.FindOneNoMemReset(**kwargs)

    def FindAll(self, **kwargs):
        self.SetKwargsAll(**kwargs)
        if self.t <= self.d:
            self.t = self.d + 1
        if self.n < self.t:
            self.n = self.t

        self.solverNames = self.defaultSolverNames
        self.outofmemory = False
        self.outofmemorySingleSolver = False

        while not self.outofmemorySingleSolver:
            self.FindOneNoMemReset()
            if self.solutionExists.value == 1.0:
                self.n += 1
            else:
                self.t += 1
                self.n = self.t

    def SolveForSetOfValues(self, values):
        for t, n in values:
            self.n = n
            self.t = t
            print(f"Calculating solution for t={t}, n={n}")
            self.FindOne()


if __name__ == '__main__':
    solver = CFFSATSolver()
    solver.timeout = 60 * 60
    # solver.t = 9
    # solver.n = 12
    # solver.d = 2

    values = [
        (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
        (8, 8), (9, 12), (10, 13), (11, 17), (12, 20),
        (13, 26), (14, 28), (15, 34), (16, 34), (17, 36),
        (18, 43), (19, 44), (20, 50), (21, 56), (22, 57),
        (23, 62), (24, 72), (25, 76), (26, 79), (27, 89),
        (28, 99), (29, 107), (30, 116), (31, 117), (32, 116)
    ]
    solver.SolveForSetOfValues(values)

    # solver.FindAll()
    # solver.FindOne()