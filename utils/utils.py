import numpy as np
from math import exp, log

def gaussian_kernel(size, sigma=1.2):
    seq = np.array([[i, j] for i in range(size) for j in range(size)], dtype='int32')
    points = np.array(seq, dtype='float32') + 0.5
    center = np.array([0.5 * size, 0.5 * size])
    d = np.linalg.norm(points-center, axis=1)
    kern1d = 1.0/(sigma * (2*np.pi)**0.5) * np.exp(-1.0 * np.power(d, 2) / (2.0 * sigma**2))
    kern = kern1d.reshape([size, size]) / np.sum(kern1d)
    return kern

def pairwise_distance(X, Y):
    assert len(X.shape) == len(Y.shape)
    N = X.shape[0]
    M = Y.shape[0]
    D = len(X.shape)
    Xe = np.repeat(np.expand_dims(X, axis=0), M, axis=0)
    Ye = np.repeat(np.expand_dims(Y, axis=1), N, axis=1)
    return np.linalg.norm(Xe-Ye, axis=D)

def gaussian_radial_basis(X, beta=2.0):
    PD = pairwise_distance(X, X)
    return np.exp(-0.5 * np.power(PD/beta, 2))

def init_sigma2(X, Y):
    N = float(X.shape[0])
    M = float(Y.shape[0])
    t1 = M * np.trace(np.dot(np.transpose(X), X))
    t2 = N * np.trace(np.dot(np.transpose(Y), Y))
    t3 = 2.0 * np.dot(np.sum(X, axis=0), np.transpose(np.sum(Y, axis=0)))
    return (t1 + t2 -t3)/(M*N*2.0)

def match(PD):
    seq = np.arange(PD.shape[0])
    amin1 = np.argmin(PD, axis=1)
    C = np.array([seq, amin1]).transpose()
    min1 = PD[seq, amin1]
    mask = np.zeros_like(PD)
    mask[seq, amin1] = 1
    masked = np.ma.masked_array(PD, mask)
    min2 = np.amin(masked, axis=1)
    return C, np.array(min2/min1)

def compute(X, Y, T_old, Pm, sigma2, omega):
    N = X.shape[0]
    M = Y.shape[0]
    T = T_old

    Te = np.repeat(np.expand_dims(T, axis=1), N, axis=1)
    Xe = np.repeat(np.expand_dims(T, axis=0), M, axis=0)
    Pmxn = (1-omega) * Pm * np.exp(
        -(1 / (2 * sigma2)) * np.sum(np.power(Xe-Te, 2), axis=2) )

    Pxn = np.sum(Pmxn, axis=0) + omega/N
    Po = Pmxn / np.repeat(np.expand_dims(Pxn, axis=0), M, axis=0)

    Np = np.dot(np.dot(np.ones([1, M]), Po), np.ones([N, 1]))[0, 0]
    P1 = np.squeeze(np.dot(Po, np.ones([N, 1])))
    Px = np.diag(np.squeeze(np.dot(Po.transpose(), np.ones([M, 1]))))
    Py = np.diag(P1)
    t1 = np.trace(np.dot(np.dot(X.transpose(), Px), X))
    t2 = np.trace(np.dot(np.dot(T.transpose(), Po), X))
    t3 = np.trace(np.dot(np.dot(T.transpose(), Py), T))
    tmp =  t1 - 2.0*t2 + t3
    Q = Np * log(sigma2) + tmp/(2.0*sigma2)
    return Po, P1, Np, tmp, Q

def convert_feature(X, XS0, DXS0):
    DXS = np.ones([14 * 14, 128]) * np.mean(DXS0)
    Xmap = [[] for _ in range(14 * 14)]
    for i in range(len(XS0)):
        Xmap[int(XS0[i, 0] / 32.0) * 14 + int(XS0[i, 1] / 32.0)].append(i)

    # # method 1
    # for i in range(14 * 14):
    #     mindis = float('Inf')
    #     minind = -1
    #     for j in range(len(Xmap[i])):
    #         dis = np.linalg.norm(XS0[Xmap[i][j], :] - X[i, :])
    #         if dis < mindis:
    #             mindis = dis
    #             minind = j
    #     if minind != -1:
    #         X[i, :] = XS0[Xmap[i][j], :]
    #         DXS[i, :] = DXS0[Xmap[i][j], :]

    # method 2
    for i in range(14 * 14):
        if len(Xmap[i]) > 0:
            DXS[i, :] = np.mean(DXS0[Xmap[i], :], axis=0)

    return X, DXS
