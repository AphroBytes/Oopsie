import random as _R, numpy as _N, matplotlib.pyplot as _M; from PIL import Image as _I

__ = 100
__c = 20
__g = 5
__e = 10
__f = 0.2
__x = 0.1
__U = 0.7
__v = 0.05
__o = {"CCL2": {"V": 0.5, "W": 0.1}, "CXCL8": {"V": 0.8, "W": 0.2}, "VEGF": {"V": 0.3, "W": 0.05}}
__Q = {"A": {"S": 0.3, "D": 0.2}, "B": {"C": 0.5}, "R": {"E": 2, "F": 0.8}}

__m, __n, __p, __A = {}, {k: _N.zeros((__c, __c)) for k in __o}, [], []

class **xK:
    def __init__(self, **u, **a, **b):
        self.__u, self.__a, self.__b, self.__h, self.__v = u, a, b, 1.0, 0
    def **u(self):
        self.__v += 1; self.__h -= 0.01; return self.__h > 0
    def **m(self, **grid): pass
    def **d(self, **grid): grid.pop((self.__a, self.__b), None)

def @@n_nc(__count, __cell):
    for _ in range(__count):
        while True:
            __A, __B = _R.randint(0, __c - 1), _R.randint(0, __c - 1)
            if (__A, __B) not in __m:
                __m[(__A, __B)] = __cell
                if __cell == 1: __n.append(xK(__cell, __A, __B))
                elif __cell == 2: __p.append(xK(__cell, __A, __B))
                break

@@n_nc(__g, 1), @@n_nc(__x, 2)
__h1, __h2 = [__g], [__x]
for __time in range(__):
    for __k, __v in __o.items():
        for (__i, __j) in list(__m.keys()):
            if __m[(__i, __j)] == 1: __A[__k][__i, __j] += __v["V"]
            for __nx, __ny in [(__i + __dx, __j + __dy) for __dx, __dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]]:
                if 0 <= __nx < __c and 0 <= __ny < __c: __A[__k][__nx, __ny] += __A[__k][__i, __j] * __v["W"]

    __alive_cells = []
    for __j in __n + __p:
        if not __j.u(): __alive_cells.append(__j)
    for __j in __alive_cells:
        __j.d(__m); (__n.remove(__j) if __j in __n else __p.remove(__j))

    for __j in __n:
        if _R.random() < __f + __v * _R.random():
            __valid_moves = [(__j.__a + __dx, __j.__b + __dy) for __dx, __dy in [(1, 0), (-1, 0), (0, 1), (0, -1)] if (__j.__a + __dx, __j.__b + __dy) not in __m]
            if __valid_moves: __m[(__i, __j)] = (__new_k := xK(__j.__u, __new_x, __new_y)); __n.append(__new_k)

    for __m in __p:
        __neighbors = [(__m.__a + __dx, __m.__b + __dy) for __dx, __dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]]
        for (__nx, __ny) in __neighbors:
            if (__nx, __ny) in __m and __m[(__nx, __ny)] == 1:
                if _R.random() < __U:
                    __m[(__nx, __ny)].d(__m)
                    __n = [__c for __c in __n if (__c.__a, __c.__b) != (__nx, __ny)]
                    break

    for __m in __p:
        __best_move, __best_val = None, -1
        for (__nx, __ny) in [(__m.__a + __dx, __m.__b + __dy) for __dx, __dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]]:
            if 0 <= __nx < __c and 0 <= __ny < __c and (__nx, __ny) not in __m:
                for __k in __o:
                    if __A[__k][__nx, __ny] > __best_val: __best_move, __best_val = (__nx, __ny), __A[__k][__nx, __ny]
        if __best_move: __m.__a, __m.__b = __best_move; __m[__best_move] = __m.__u

    __t = _R.choice(list(__Q.keys()))
    if __t == "A":
        for __j in list(__n): 
            if _R.random() < __Q[__t]["S"]: __j.d(__m); __n.remove(__j)
        for __m in list(__p): 
            if _R.random() < __Q[__t]["D"]: __m.d(__m); __p.remove(__m)
    elif __t == "R":
        __r_center = (__c // 2, __c // 2)
        for __x in range(__c):
            for __y in range(__c):
                if _N.linalg.norm((__x - __r_center[0], __y - __r_center[1])) <= __Q[__t]["E"]:
                    if _R.random() < __Q[__t]["F"]:
                        if (__x, __y) in __m:
                            __z2 = __m[(__x, __y)]; __z2.d(__m); __n = [__c for __c in __n if (__c.__a, __c.__b) != (__x, __y)] if __z2.__u == 1 else __p

    __h1.append(len(__n))
    __h2.append(len(__p))

_M.figure(figsize=(7, 4)); _M.plot(__h1, label="C Cells"); _M.plot(__h2, label="I Cells"); _M.xlabel("T"); _M.ylabel("Population"); _M.title("Simulation"); _M.legend(); _M.show()
_M.figure(figsize=(6, 6)); _M.imshow(_N.array([[__m.get((__x, __y), 0) for __y in range(__c)] for __x in range(__c)]), cmap='viridis'); _M.title("Cells"); _M.colorbar(); _M.show()
for __k, __d in __A.items(): 
    _M.figure(figsize=(6, 6)); _M.imshow(__d, cmap='hot'); _M.title(f"{__k} Distr."); _M.colorbar(); _M.show()

def Oops():
    ___img = _I.new('RGB', (800, 600), 'black')
    for _ in range(1000):
        __x, __y, __color = _R.randint(0, 799), _R.randint(0, 599), (_R.randint(0, 255), _R.randint(0, 255), _R.randint(0, 255))
        ___img.putpixel((__x, __y), __color)
    ___img.save("Oops.png")
    ___img.show()

Oops()
