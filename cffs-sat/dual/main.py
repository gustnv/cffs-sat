import itertools
import json
import jsbeautifier
import psutil
import time
import timeit

from multiprocessing import Process, Lock, Value, Array
from operator import itemgetter
from pysat.solvers import *


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
        # 'minisat22', 'minisat-gh' and 'minicard' seem to fail/crash while solving on some values. For example d = 2, t = 7 and n = 8
        self.defaultSolverNames = [
            'glucose4', 'glucose3', 'maplechrono', 'maplecm', 'maplesat', 'lingeling']
        self.outofmemory = False
        self.outofmemorySingleSolver = False
        self.singleSolverName = 'glucose4'
        self.solverNames = self.defaultSolverNames

    def CreateClauses(self):
        self.clauses = []
        m = []
        x = 1
        for row in range(self.t):
            v = []
            for column in range(self.n):
                v.append(x)
                x += 1
            m.append(v)

        y = x

        for column in range(self.n):
            otherColumns = list(range(self.n))
            otherColumns.remove(column)

            combinations = itertools.combinations(otherColumns, self.d)

            for coveringColumns in combinations:
                ys = []
                for row in range(self.t):
                    ys.append(y)
                    self.clauses.append([m[row][column], -y])
                    for coveringColumn in coveringColumns:
                        self.clauses.append(
                            [-m[row][coveringColumn], -y])
                    y += 1
                self.clauses.append(ys)

    def PrintSolution(self):
        if self.solutionExists.value == 1.0:
            blocks = [[] for _ in range(self.n)]

            for x in self.solution[0:self.n*self.t]:
                if x > 0:
                    blocks[x % self.n].append(x // self.n + 1)

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
                    blocks[x % self.n].append(x // self.n + 1)

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


if __name__ == '__main__':
    solver = CFFSATSolver()
    solver.timeout = 60 * 60
    solver.t = 9
    solver.n = 12
    solver.d = 2
    solver.CreateClauses()
    solver.FindOne()
