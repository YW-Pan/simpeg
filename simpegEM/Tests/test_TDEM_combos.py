import unittest
from SimPEG import *
import simpegEM as EM

plotIt = False

def getProb(meshType='CYL',rxTypes='bx,bz',nTx=1):
    cs = 5.
    ncx = 20
    ncy = 6
    npad = 20
    hx = [(cs,ncx), (cs,npad,1.3)]
    hy = [(cs,npad,-1.3), (cs,ncy), (cs,npad,1.3)]
    mesh = Mesh.CylMesh([hx,1,hy], '00C')

    active = mesh.vectorCCz<0.
    activeMap = Maps.ActiveCells(mesh, active, np.log(1e-8), nC=mesh.nCz)
    mapping = Maps.ComboMap(mesh, [Maps.ExpMap, Maps.Vertical1DMap, activeMap])

    rxOffset = 40.

    txs = []
    for ii in range(nTx):
        rxs = [EM.TDEM.RxTDEM(np.array([[rxOffset, 0., 0.]]), np.logspace(-4,-3, 20 + ii), rxType) for rxType in rxTypes.split(',')]
        txs += [EM.TDEM.TxTDEM(np.array([0., 0., 0.]), 'VMD_MVP', rxs)]

    survey = EM.TDEM.SurveyTDEM(txs)

    prb = EM.TDEM.ProblemTDEM_b(mesh, mapping=mapping)
    # prb.timeSteps = [1e-5]
    prb.timeSteps = [(1e-05, 10), (5e-05, 10), (2.5e-4, 10)]
    # prb.timeSteps = [(1e-05, 100)]

    sigma = np.ones(mesh.nCz)*1e-8
    sigma[mesh.vectorCCz<0] = 1e-1
    sigma = np.log(sigma[active])

    prb.pair(survey)
    return prb, mesh, sigma

def dotestJvec(prb, mesh, sigma):
    prb.timeSteps = [(1e-05, 10), (0.0001, 10), (0.001, 10)]
    # d_sig = 0.8*sigma #np.random.rand(mesh.nCz)
    d_sig = 10*np.random.rand(prb.mapping.nP)
    derChk = lambda m: [prb.survey.dpred(m), lambda mx: prb.Jvec(sigma, mx)]
    return Tests.checkDerivative(derChk, sigma, plotIt=False, dx=d_sig, num=2, eps=1e-20)

def dotestAdjoint(prb, mesh, sigma):
    m = np.random.rand(prb.mapping.nP)
    d = np.random.rand(prb.survey.nD)

    V1 = d.dot(prb.Jvec(sigma, m))
    V2 = m.dot(prb.Jtvec(sigma, d))
    print 'AdjointTest', V1, V2
    return np.abs(V1-V2)/np.abs(V1), 1e-6

class TDEM_bDerivTests(unittest.TestCase):

    def test_Jvec_bx(self): self.assertTrue(dotestJvec(*getProb(rxTypes='bx')))
    def test_Adjoint_bx(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='bx')))

    def test_Jvec_bxbz(self): self.assertTrue(dotestJvec(*getProb(rxTypes='bx,bz')))
    def test_Adjoint_bxbz(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='bx,bz')))

    def test_Jvec_bxbz_2tx(self): self.assertTrue(dotestJvec(*getProb(rxTypes='bx,bz',nTx=2)))
    def test_Adjoint_bxbz_2tx(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='bx,bz',nTx=2)))

    def test_Jvec_bxbzbz(self): self.assertTrue(dotestJvec(*getProb(rxTypes='bx,bz,bz')))
    def test_Adjoint_bxbzbz(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='bx,bz,bz')))

    def test_Jvec_dbxdt(self): self.assertTrue(dotestJvec(*getProb(rxTypes='dbxdt')))
    def test_Adjoint_dbxdt(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='dbxdt')))

    def test_Jvec_dbzdt(self): self.assertTrue(dotestJvec(*getProb(rxTypes='dbzdt')))
    def test_Adjoint_dbzdt(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='dbzdt')))

    def test_Jvec_dbxdtbz(self): self.assertTrue(dotestJvec(*getProb(rxTypes='dbxdt,bz')))
    def test_Adjoint_dbxdtbz(self): self.assertLess(*dotestAdjoint(*getProb(rxTypes='dbxdt,bz')))


if __name__ == '__main__':
    unittest.main()
