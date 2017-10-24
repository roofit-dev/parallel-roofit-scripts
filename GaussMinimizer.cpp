// GaussMinimizer: test RooGaussMinimizer class
//
// call from command line like, for instance:
// root -l 'GaussMinimizer.cpp()'

R__LOAD_LIBRARY(libRooFit)

#include <iostream>

using namespace RooFit;

void GaussMinimizer() {
  RooWorkspace w = RooWorkspace();

  w.factory("Gaussian::g(x[-5,5],mu[-3,3],sigma[1])");

  auto x = w.var("x");
  RooAbsPdf * pdf = w.pdf("g");
  RooRealVar * mu = w.var("mu");

  RooDataSet * data = pdf->generate(RooArgSet(*x), 10000);

  auto nll = pdf->createNLL(*data);

  std::cout << "trying nominal calculation" << std::endl;
  RooMinimizer m0(*nll);

  m0.migrad();
  m0.hesse();
  m0.minos();

  std::cout << "nominal mu fit is," << mu->getVal() << std::endl;

  mu->setVal(-2.9);

  std::cout << "trying GaussMinimizer" << std::endl;
  RooGaussMinimizer m1(*nll);

  m1.migrad();
  std::cout << "migrad worked with mu of " << mu->getVal() << std::endl;
  m1.hesse();
  std::cout << "hesse worked with mu of " << mu->getVal() << std::endl;
  m1.minos();
  std::cout << "minos worked with mu of " << mu->getVal() << std::endl;

  std::cout << "Made and minimised an nll with 2 Gradient Function" << std::endl;
}
