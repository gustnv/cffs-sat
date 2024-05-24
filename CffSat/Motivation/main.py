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
    solver = Solver(name = name, bootstrap_with = clauses)
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
        self.delta = 2
        self.colors = 1
        self.sets = 1
        self.clauses = []
        self.timeout = 60*10
        self.timer = timeit.default_timer()
        self.lock = Lock()
        self.solutionExists = Value('d', 0.0)
        self.solution = Array('i', [])
        self.processes = []
        self.defaultSolverNames = ['glucose4', 'glucose3', 'maplechrono', 'maplecm', 'maplesat', 'cadical', 'lingeling'] # 'minisat22', 'minisat-gh' and 'minicard' seem to fail/crash while solving on some values. For example delta = 2, colors = 7 and sets = 8
        self.outofmemory = False
        self.outofmemorySingleSolver = False
        self.singleSolverName = 'glucose4'
        self.solverNames = self.defaultSolverNames
        self.ordered = False

    def CreateClauses(self):
        self.clauses = []
        matrix = []
        i = 1
        for row in range(self.sets):
            variables = []
            for column in range(self.colors):
                variables.append(i)
                i += 1
            matrix.append(variables)

        for row in list(range(self.sets)):
            otherRows = list(range(self.sets))
            otherRows.remove(row)
            for coveringRows in itertools.combinations(otherRows, self.delta):
                variables = []
                for column in range(self.colors):
                    variables.append(i)
                    self.clauses.append([matrix[row][column], -i])
                    for coveringRow in coveringRows:
                        if not self.ordered or coveringRow < row:
                            self.clauses.append([-matrix[coveringRow][column], -i])
                    i += 1
                self.clauses.append(variables)

    def PrintSolution(self):
        sets = []
        current = []
        if self.solutionExists.value == 1.0:
            for row in self.solution[0:self.sets*self.colors]:
                if row > 0 and row%self.colors == 0:
                    current.append(self.colors)
                elif row > 0:
                    current.append(row%self.colors)
                if row%self.colors == 0:
                    sets.append(current)
                    current = []
            sets = sorted(sets, key=lambda x: sum(x))
            print('Sets:')
            for s in range(len(sets)):
                if len(sets[s]) > 0:
                    if s == len(sets) - 1:
                        print(sets[s])
                    else:
                        print(sets[s], end=', ')
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
        sets = []
        current = []
        if self.solutionExists.value == 1.0:
            for row in self.solution[0:self.sets*self.colors]:
                if row > 0 and row%self.colors == 0:
                    current.append(self.colors)
                elif row > 0:
                    current.append(row%self.colors)
                if row%self.colors == 0:
                    sets.append(current)
                    current = []
            sets = sorted(sets, key=lambda x: sum(x))

        filename = 'cffdata.json'
        if self.ordered:
            filename = 'cffdataord.json'
        try:
            with open(filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []

        objInData = [obj for obj in data if obj['delta'] == self.delta and obj['colors'] == self.colors and obj['sets'] == self.sets]

        if len(objInData) == 0:
            newdata =  {
                'delta': self.delta,
                'colors': self.colors,
                'sets': self.sets
            }
            if self.solutionExists.value == 1.0:
                newdata['solution'] = sets
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
                objInData[0]['solution'] = sets
        elif self.solutionExists.value == -1.0:
            sol = objInData[0]['solution']
            if sol != 'UNSAT':
                objInData[0]['solution'] = 'UNSAT'

        data = sorted(data, key=itemgetter('delta', 'colors', 'sets'))

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
        if self.ordered:
            filename = 'cffdataord.json'
        try:
            with open(filename, 'r') as jsonFile:
                data = json.load(jsonFile)
        except FileNotFoundError:
            data = []
        objInData = [obj for obj in data if obj['delta'] == self.delta and obj['colors'] == self.colors and obj['sets'] == self.sets]
        if len(objInData) != 0 and isinstance(objInData[0]['solution'], list) and len(objInData[0]['solution']) != 0:
            print('Delta:', self.delta, 'Colors:', self.colors, 'Sets:', self.sets)
            print('Solution already in json\n')
            self.solutionExists.value = 1.0
            return True
        elif len(objInData) != 0 and objInData[0]['solution'] == 'UNSAT':
            print('Delta:', self.delta, 'Colors:', self.colors, 'Sets:', self.sets)
            print('Solution already in json\n')
            self.solutionExists.value = -1.0
            return True
        else:
            return False

    def SetKwargsOne(self, **kwargs):
        if 'delta' in kwargs:
            self.delta = kwargs['delta']
        if 'colors' in kwargs:
            self.colors = kwargs['colors']
        if 'sets' in kwargs:
            self.sets = kwargs['sets']

    def SetKwargsAll(self, **kwargs):
        if 'delta' in kwargs:
            self.delta = kwargs['delta']
        else:
            self.delta = 2
        if 'colors' in kwargs:
            self.colors = kwargs['colors']
        else:
            self.colors = 1
        if 'sets' in kwargs:
            self.sets = kwargs['sets']
        else:
            self.sets = 1

    def SwitchToSingleSolver(self):
        self.outofmemory = True
        self.solverNames = [self.singleSolverName]
        self.TerminateProcesses()
        self.CreateClauses()
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.sets * self.colors)
        self.processes = []
        p = Process(target = _FindParallel, args = (self.singleSolverName, self.lock, self.solution, self.solutionExists, self.clauses))
        self.processes.append(p)
        p.start()
        self.clauses = []

    def FindOneNoMemReset(self, **kwargs):
        self.timer = timeit.default_timer()
        if self.SolutionCached():
            return

        self.CreateClauses()
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * self.sets * self.colors)
        print('Delta:', self.delta, 'Colors:', self.colors, 'Sets:', self.sets, 'len(clauses):', len(self.clauses), 'Ordered:', self.ordered)
        self.processes = []

        for name in self.solverNames:
            p = Process(target = _FindParallel, args = (name, self.lock, self.solution, self.solutionExists, self.clauses))
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
        if self.colors <= self.delta:
            self.colors = self.delta + 1
        if self.sets < self.colors:
            self.sets = self.colors

        self.solverNames = self.defaultSolverNames
        self.outofmemory = False
        self.outofmemorySingleSolver = False

        while not self.outofmemorySingleSolver:
            self.FindOneNoMemReset()
            if self.solutionExists.value == 1.0:
                self.sets += 1
            else:
                self.colors += 1
                self.sets = self.colors

if __name__ == '__main__':
    solver = CFFSATSolver()
    solver.timeout = 60 * 60
    solver.ordered = True
    solver.FindOne(delta = 2)