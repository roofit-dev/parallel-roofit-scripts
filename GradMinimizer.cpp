// GradMinimizer: test RooGradMinimizer class
//
// call from command line like, for instance:
// root -l 'GradMinimizer.cpp()'

// R__LOAD_LIBRARY(libRooFit)

#include <iostream>

using namespace RooFit;

void GradMinimizer() {
  RooWorkspace w = RooWorkspace();

  w.factory("Gaussian::g(x[-5,5],mu[-3,3],sigma[1])");

  auto x = w.var("x");
  RooAbsPdf * pdf = w.pdf("g");
  RooRealVar * mu = w.var("mu");

  RooDataSet * data = pdf->generate(RooArgSet(*x), 10000);

  auto nll = pdf->createNLL(*data);

  // set mu to same value at the start of all minimizations
  mu->setVal(-2.9);

  std::cout << "trying nominal calculation" << std::endl;
  RooMinimizer m0(*nll);

  m0.migrad();

  m0.hesse();

  m0.minos();

  std::cout << "nominal mu fit is," << mu->getVal() << std::endl;

  // set mu to same value at the start of both minimizations
  mu->setVal(-2.9);

  std::cout << "trying GradMinimizer" << std::endl;
  RooGradMinimizer m1(*nll);

  std::cout << "RooGradMinimizer created" << std::endl;

  m1.migrad();
  std::cout << "migrad worked with mu of " << mu->getVal() << std::endl;
    
  // m1.hesse();
  // std::cout << "hesse done" << std::endl;
  
  // m1.minos();
  // std::cout << "minos done" << std::endl;
}
