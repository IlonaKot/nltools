import os
import numpy as np
import nibabel as nb
import pandas as pd
import glob
from nltools.simulator import Simulator
from nltools.data import Adjacency, Design_Matrix
from nltools.stats import threshold, align
from sklearn.metrics import pairwise_distances
import matplotlib
import matplotlib.pyplot as plt
import networkx as nx
import six
from scipy.stats import pearsonr
from scipy.linalg import block_diag

def test_type_single(sim_adjacency_single):
    assert sim_adjacency_single.matrix_type is 'distance'
    dat_single2 = Adjacency(1-sim_adjacency_single.squareform())
    assert dat_single2.matrix_type is 'similarity'
    assert sim_adjacency_single.issymmetric

def test_type_directed(sim_adjacency_directed):
    assert not sim_adjacency_directed.issymmetric

def test_length(sim_adjacency_multiple):
    assert len(sim_adjacency_multiple) == sim_adjacency_multiple.data.shape[0]
    assert len(sim_adjacency_multiple[0]) == 1

def test_indexing(sim_adjacency_multiple):
    assert len(sim_adjacency_multiple[0]) == 1
    assert len(sim_adjacency_multiple[0:4]) == 4
    assert len(sim_adjacency_multiple[0, 2, 3]) == 3

def test_arithmetic(sim_adjacency_directed):
    assert(sim_adjacency_directed+5).data[0] == sim_adjacency_directed.data[0]+5
    assert(sim_adjacency_directed-.5).data[0] == sim_adjacency_directed.data[0]-.5
    assert(sim_adjacency_directed*5).data[0] == sim_adjacency_directed.data[0]*5
    assert np.all(np.isclose((sim_adjacency_directed+
                              sim_adjacency_directed).data,
                            (sim_adjacency_directed*2).data))
    assert np.all(np.isclose((sim_adjacency_directed*2-
                              sim_adjacency_directed).data,
                             sim_adjacency_directed.data))

def test_copy(sim_adjacency_multiple):
    assert np.all(sim_adjacency_multiple.data == sim_adjacency_multiple.copy().data)

def test_squareform(sim_adjacency_multiple):
    assert len(sim_adjacency_multiple.squareform()) == len(sim_adjacency_multiple)
    assert sim_adjacency_multiple[0].squareform().shape == sim_adjacency_multiple[0].square_shape()

def test_write_multiple(sim_adjacency_multiple, tmpdir):
    sim_adjacency_multiple.write(os.path.join(str(tmpdir.join('Test.csv'))),
                        method='long')
    dat_multiple2 = Adjacency(os.path.join(str(tmpdir.join('Test.csv'))),
                        matrix_type='distance_flat')
    assert np.all(np.isclose(sim_adjacency_multiple.data, dat_multiple2.data))

def test_write_directed(sim_adjacency_directed, tmpdir):
    sim_adjacency_directed.write(os.path.join(str(tmpdir.join('Test.csv'))),
                                 method='long')
    dat_directed2 = Adjacency(os.path.join(str(tmpdir.join('Test.csv'))),
                              matrix_type='directed_flat')
    assert np.all(np.isclose(sim_adjacency_directed.data, dat_directed2.data))

def test_mean(sim_adjacency_multiple):
    assert isinstance(sim_adjacency_multiple.mean(axis=0), Adjacency)
    assert len(sim_adjacency_multiple.mean(axis=0)) == 1
    assert len(sim_adjacency_multiple.mean(axis=1)) == len(np.mean(sim_adjacency_multiple.data,
                axis=1))

def test_std(sim_adjacency_multiple):
    assert isinstance(sim_adjacency_multiple.std(axis=0), Adjacency)
    assert len(sim_adjacency_multiple.std(axis=0)) == 1
    assert len(sim_adjacency_multiple.std(axis=1)) == len(np.std(sim_adjacency_multiple.data,
                axis=1))

def test_similarity(sim_adjacency_multiple):
    assert len(sim_adjacency_multiple.similarity(
                sim_adjacency_multiple[0].squareform(),perm_type='1d' )) == len(sim_adjacency_multiple)
    assert len(sim_adjacency_multiple.similarity(sim_adjacency_multiple[0].squareform(),perm_type='1d',
                metric='pearson',n_permute=1000)) == len(sim_adjacency_multiple)
    assert len(sim_adjacency_multiple.similarity(sim_adjacency_multiple[0].squareform(),perm_type='1d',
                metric='kendall',n_permute=1000)) == len(sim_adjacency_multiple)

def test_distance(sim_adjacency_multiple):
    assert isinstance(sim_adjacency_multiple.distance(), Adjacency)
    assert sim_adjacency_multiple.distance().square_shape()[0] == len(sim_adjacency_multiple)

def test_ttest(sim_adjacency_multiple):
    out = sim_adjacency_multiple.ttest()
    assert len(out['t']) == 1
    assert len(out['p']) == 1
    assert out['t'].shape()[0] == sim_adjacency_multiple.shape()[1]
    assert out['p'].shape()[0] == sim_adjacency_multiple.shape()[1]
    out = sim_adjacency_multiple.ttest(permutation=True, n_permute=1000)
    assert len(out['t']) == 1
    assert len(out['p']) == 1
    assert out['t'].shape()[0] == sim_adjacency_multiple.shape()[1]
    assert out['p'].shape()[0] == sim_adjacency_multiple.shape()[1]

def test_threshold(sim_adjacency_directed):
    assert np.sum(sim_adjacency_directed.threshold(upper=.8).data == 0) == 10
    assert sim_adjacency_directed.threshold(upper=.8, binarize=True).data[0]
    assert np.sum(sim_adjacency_directed.threshold(upper='70%', binarize=True).data) == 5
    assert np.sum(sim_adjacency_directed.threshold(lower=.4, binarize=True).data) == 6

def test_graph_directed(sim_adjacency_directed):
    assert isinstance(sim_adjacency_directed.to_graph(), nx.DiGraph)

def test_graph_single(sim_adjacency_single):
    assert isinstance(sim_adjacency_single.to_graph(), nx.Graph)

def test_append(sim_adjacency_single):
    a = Adjacency()
    a = a.append(sim_adjacency_single)
    assert a.shape() == sim_adjacency_single.shape()
    a = a.append(a)
    assert a.shape() == (2, 6)

def test_bootstrap(sim_adjacency_multiple):
    n_samples = 3
    b = sim_adjacency_multiple.bootstrap('mean', n_samples=n_samples)
    assert isinstance(b['Z'], Adjacency)
    b = sim_adjacency_multiple.bootstrap('std', n_samples=n_samples)
    assert isinstance(b['Z'], Adjacency)

def test_plot(sim_adjacency_multiple):
    f = sim_adjacency_multiple[0].plot()
    assert isinstance(f, plt.Figure)
    f = sim_adjacency_multiple.plot()
    assert isinstance(f, plt.Figure)

def test_plot_mds(sim_adjacency_single):
    f = sim_adjacency_single.plot_mds()
    assert isinstance(f, plt.Figure)

def test_similarity_conversion(sim_adjacency_single):
    np.testing.assert_approx_equal(-1,pearsonr(sim_adjacency_single.data,sim_adjacency_single.distance_to_similarity().data)[0],significant=1)
    np.testing.assert_approx_equal(-1,pearsonr(sim_adjacency_single.distance_to_similarity().data,sim_adjacency_single.distance_to_similarity().similarity_to_distance().data)[0],significant=1)

def test_cluster_mean():
    test_dat = Adjacency(block_diag(np.ones((4,4)),np.ones((4,4))*2,np.ones((4,4))*3),matrix_type='similarity')
    test_labels = np.concatenate([np.ones(4)*x for x in range(1,4)])
    out = test_dat.within_cluster_mean(clusters=test_labels)
    assert np.sum(np.array([1,2,3])-np.array([out[x] for x in out]))==0

def test_regression():
    # Test Adjacency Regression
    m1 = block_diag(np.ones((4,4)),np.zeros((4,4)),np.zeros((4,4)))
    m2 = block_diag(np.zeros((4,4)),np.ones((4,4)),np.zeros((4,4)))
    m3 = block_diag(np.zeros((4,4)),np.zeros((4,4)),np.ones((4,4)))
    Y = Adjacency(m1*1+m2*2+m3*3,matrix_type='similarity')
    X = Adjacency([m1,m2,m3],matrix_type='similarity')

    stats = Y.regress(X)
    assert np.allclose(stats['beta'],np.array([1,2,3]))

    # Test Design_Matrix Regression
    n = 10
    d = Adjacency([block_diag(np.ones((4,4))+np.random.randn(4,4)*.1,np.zeros((8,8))) for x in range(n)],
                  matrix_type='similarity')
    X = Design_Matrix(np.ones(n))
    stats = d.regress(X)
    out = stats['beta'].within_cluster_mean(clusters=['Group1']*4 + ['Group2']*8)
    assert np.allclose(np.array([out['Group1'],out['Group2']]),np.array([1,0]), rtol=1e-01)# np.allclose(np.sum(stats['beta']-np.array([1,2,3])),0)

    # # Test stats_label_distance - FAILED - Need to sort this out
    # labels = np.array(['group1','group1','group2','group2'])
    # stats = dat_multiple[0].stats_label_distance(labels)
    # assert np.isclose(stats['group1']['mean'],-1*stats['group2']['mean'])

def test_matrix_permutation():
    dat = np.random.multivariate_normal([2, 6], [[.5, 2], [.5, 3]], 190)
    x = Adjacency(dat[:, 0])
    y = Adjacency(dat[:, 1])
    stats = x.similarity(y,perm_type='2d',n_permute=1000)
    assert (stats['correlation'] > .4) & (stats['correlation']<.85) & (stats['p'] <.001)
    stats = x.similarity(y,perm_type=None)
    assert (stats['correlation'] > .4) & (stats['correlation']<.85)
