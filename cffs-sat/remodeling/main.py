import itertools
import sys
import math
import os
import json
import time
import jsbeautifier
import psutil
import multiprocessing
import timeit
from multiprocessing import Pool, Lock, Value, Array
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


def _run_solver_task(args):
    name, clauses = args
    try:
        solver = Solver(name=name, bootstrap_with=clauses)
        sol = solver.solve()
        model = solver.get_model() if sol else None
        try:
            solver.delete()
        except Exception:
            pass
        return (name, sol, model)
    except MemoryError:
        return (name, None, 'OUTOFMEMORY')
    except Exception as e:
        return (name, None, f'ERROR:{type(e).__name__}:{e}')


class CFFSATSolver:
    def __init__(self, k, d, t=None, n=None):
        self.k = k
        self.d = d
        if t is None:
            self.t = math.ceil(d*1.5)
        else:
            self.t = t
        if n is None:
            self.n = self.t
        else:
            self.n = n
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
        objInData = [obj for obj in data if obj['d'] == self.d and obj['t'] == self.t and obj['n'] == self.n and obj['k'] == self.k]

        if len(objInData) != 0 and isinstance(objInData[0]['solution'], list) and len(objInData[0]['solution']) != 0:
            print('Solution already in json\n')
            self.solutionExists.value = 1.0
            return True
        elif len(objInData) != 0 and objInData[0]['solution'] == 'UNSAT':
            print('Solution already in json\n')
            self.solutionExists.value = -1.0
            return True
        elif len(objInData) != 0 and (objInData[0]['solution'] == 'TIMEOUT' or objInData[0]['solution'] == 'OUTOFMEMORY'):
            if objInData[0]['time'] < self.timeout:
                self.solutionExists.value = -3.0 if objInData[0]['solution'] == 'TIMEOUT' else -4.0
                return False
            else:
                print('Solution already in json\n')
                self.solutionExists.value = -3.0 if objInData[0]['solution'] == 'TIMEOUT' else -4.0
                return True
        else:
            return False

    def SwitchToSingleSolver(self, create_clauses_fn):
        """
        Keep behavior: switch to the single solver name (self.singleSolverName).
        This implementation simply sets solverNames and will run FindOneNoMemReset
        with concurrency reduced to 1 in a subsequent step.
        """
        self.outofmemory = True
        self.solverNames = [self.singleSolverName]
        # No process list to terminate now (we use pool approach); prepare to run single-solver next
        # recreate clauses so the single-solver run uses a fresh set
        create_clauses_fn()

    def FindOneNoMemReset(self, create_clauses_fn):
        """
        Pool-based orchestration with wall-clock timeout (no exceptions),
        early termination on first solution, and graceful OUTOFMEMORY/ERROR handling.
        """
        self._set_filename(create_clauses_fn.__name__)
        create_clauses_fn()  # fills self.clauses

        print("Finding solution for k:", self.k, 'd:', self.d, 't:', self.t, 'n:', self.n,)

        self.timer = timeit.default_timer()
        if self.SolutionCached():
            return

        # init state
        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * (self.n * self.t))

        # choose concurrency according to mem pressure & CPU
        mempercent = psutil.virtual_memory()[2]
        cpu_count = max(1, os.cpu_count() or 1)
        desired = min(len(self.solverNames), cpu_count)
        if mempercent > 70.0:
            concurrency = 1
        elif mempercent > 50.0:
            concurrency = max(1, desired // 2)
        else:
            concurrency = desired

        worker_args = [(name, list(self.clauses)) for name in self.solverNames]

        saw_unsat = False
        saw_outofmemory = False
        saw_error = False

        pool = Pool(processes=concurrency, maxtasksperchild=1)
        async_results = [pool.apply_async(_run_solver_task, (args,)) for args in worker_args]

        try:
            deadline = self.timer + self.timeout
            pending = list(async_results)

            # poll loop (no exceptions)
            while pending:
                # timeout check
                if timeit.default_timer() >= deadline:
                    self.solutionExists.value = -3.0  # TIMEOUT
                    pool.terminate()
                    pool.join()
                    self.time = timeit.default_timer() - self.timer
                    self.PrintSolution()
                    self.UpdateJson()
                    print()
                    return

                # check any finished tasks
                progressed = False
                for ar in pending[:]:
                    if ar.ready():
                        progressed = True
                        try:
                            solver_name, sol, model_or_error = ar.get()
                        except MemoryError:
                            solver_name, sol, model_or_error = ("<unknown>", None, "OUTOFMEMORY")
                        except Exception as e:
                            solver_name, sol, model_or_error = ("<unknown>", None, f"ERROR:{type(e).__name__}:{e}")

                        # handle OUTOFMEMORY
                        if model_or_error == 'OUTOFMEMORY':
                            saw_outofmemory = True
                            if not self.outofmemory:
                                self.SwitchToSingleSolver(create_clauses_fn)
                                pool.terminate()
                                pool.join()
                                self.solutionExists.value = -4.0
                                return
                            pending.remove(ar)
                            continue

                        # handle generic error
                        if isinstance(model_or_error, str) and model_or_error.startswith('ERROR:'):
                            saw_error = True
                            pending.remove(ar)
                            continue

                        # solution found
                        if sol is True and model_or_error:
                            model = model_or_error
                            count = min(len(model), self.n * self.t)
                            self.solution = Array('i', [0] * (self.n * self.t))
                            for i in range(count):
                                try:
                                    self.solution[i] = model[i]
                                except Exception:
                                    self.solution[i] = int(model[i]) if isinstance(model[i], int) else 0
                            self.solutionExists.value = 1.0
                            pool.terminate()
                            pool.join()
                            self.time = timeit.default_timer() - self.timer
                            self.PrintSolution()
                            self.UpdateJson()
                            print()
                            return

                        # explicit UNSAT from this backend
                        if sol is False:
                            saw_unsat = True

                        pending.remove(ar)

                if not progressed:
                    # avoid busy-wait if nothing ready yet
                    time.sleep(0.02)

        finally:
            try:
                pool.close()
            except Exception:
                pass
            try:
                pool.join()
            except Exception:
                pass

        # no solver produced a model; decide outcome
        if self.solutionExists.value != 1.0:
            if saw_outofmemory:
                self.solutionExists.value = -4.0
            elif saw_unsat:
                self.solutionExists.value = -1.0
            elif saw_error:
                self.solutionExists.value = -2.0
            else:
                self.solutionExists.value = -2.0  # UNKNOWN

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

    def FindOneSingleSolver(self, create_clauses_fn, solver_name=None, timeout_seconds=None):
        """
        Run exactly one solver in a separate process and enforce a wall-clock timeout.
        Uses self.timeout when timeout_seconds is None.
        """
        self._set_filename(create_clauses_fn.__name__)
        create_clauses_fn()

        print("Finding solution (single solver) for k:", self.k, 'd:', self.d, 't:', self.t, 'n:', self.n)

        self.timer = timeit.default_timer()
        if self.SolutionCached():
            return

        self.solutionExists.value = 0.0
        self.solution = Array('i', [0] * (self.n * self.t))

        if solver_name is None:
            solver_name = self.singleSolverName

        # prefer explicit argument, otherwise use self.timeout
        timeout = self.timeout if timeout_seconds is None else timeout_seconds
        # small safety: ensure timeout is positive
        if timeout is None or timeout <= 0:
            timeout = 1200

        result_queue = multiprocessing.Queue()

        def worker(q, name, clauses):
            q.put(_run_solver_task((name, clauses)))

        p = multiprocessing.Process(target=worker, args=(result_queue, solver_name, list(self.clauses)))
        p.start()
        p.join(timeout)

        if p.is_alive():
            # solver didn't finish in time
            p.terminate()
            p.join()
            self.solutionExists.value = -3.0  # TIMEOUT
            self.time = timeit.default_timer() - self.timer
            self.PrintSolution()
            self.UpdateJson()
            print()
            return
        else:
            # process finished — try to read result (wait up to 1s for the queue)
            try:
                name, sol, model_or_error = result_queue.get(timeout=1.0)
            except Exception:
                # nothing in queue or other error
                self.solutionExists.value = -2.0  # ERROR
                self.time = timeit.default_timer() - self.timer
                self.PrintSolution()
                self.UpdateJson()
                print()
                return

            # interpret result same way as pool version
            if model_or_error == 'OUTOFMEMORY':
                self.solutionExists.value = -4.0
            elif isinstance(model_or_error, str) and model_or_error.startswith("ERROR:"):
                self.solutionExists.value = -2.0
            elif sol is True and model_or_error:
                model = model_or_error
                for i in range(min(len(model), self.n * self.t)):
                    try:
                        self.solution[i] = int(model[i])
                    except Exception:
                        self.solution[i] = 0
                self.solutionExists.value = 1.0
            elif sol is False:
                self.solutionExists.value = -1.0
            else:
                self.solutionExists.value = -2.0

        self.time = timeit.default_timer() - self.timer
        self.PrintSolution()
        self.UpdateJson()
        print()


    def FindAllSingleSolver(self, create_clauses_fn, solver_name='glucose4'):
        """
        Sequential search like FindAll, but always runs one solver only.
        Uses self.timeout for each single-solver run (so TIMEOUT will be observed).
        """
        self.solverNames = [solver_name or self.singleSolverName]
        self.outofmemory = False
        self.outofmemorySingleSolver = False

        while not self.outofmemorySingleSolver:
            # pass self.timeout so the single-solver run uses the same timeout you configured
            self.FindOneSingleSolver(create_clauses_fn, solver_name, timeout_seconds=self.timeout)

            if self.solutionExists.value == 1.0:
                self.n += 1
            else:
                self.t += 1
                self.n = self.t

            if self.t == 40:
                break


if __name__ == '__main__':
    solver = CFFSATSolver(0, 2, 25)
    solver.timeout = 60
    try:
        solver.FindAll(solver.CreateClausesDisjunctMatrices)
        # solver.FindAllSingleSolver(solver.CreateClausesDisjunctMatrices)
        # solver.FindOne()
    except KeyboardInterrupt:
        print("\n[!] Interrupted by user, saving JSON before exit...")
        # solver.UpdateJson()
        sys.exit(0)
