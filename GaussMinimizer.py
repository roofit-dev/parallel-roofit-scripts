import ROOT

w = ROOT.RooWorkspace()
w.factory('Gaussian::g(x[-5,5],mu[-3,3],sigma[1])')
x = w.var('x')
pdf = w.pdf('g')
data = pdf.generate(ROOT.RooArgSet(x),10000)
mu = w.var('mu')
nll = pdf.createNLL(data)
print "trying nominal calculation"
m0 = ROOT.RooMinimizer(nll)
m0.migrad()
m0.hesse()
m0.minos()
print "nominal mu fit is,",mu.getVal()

mu.setVal(-2.9)
print 'trying GaussMinimizer'
m1  = ROOT.RooGaussMinimizer(nll)
m1.migrad()
print "migrad worked with mu of ",mu.getVal()
m1.hesse()
print "hesse worked with mu of ",mu.getVal()
m1.minos()
print "minos worked with mu of ",mu.getVal()
print "Made and minimised an nll with 2 Gradient Function"
