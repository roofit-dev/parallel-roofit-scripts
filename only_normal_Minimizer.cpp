// GradMinimizer: test RooGradMinimizer class
//
// call from command line like, for instance:
// root -l 'GradMinimizer.cpp()'

R__LOAD_LIBRARY(libRooFit)

#include <iostream>
// #include <exception>

using namespace RooFit;

void only_normal_Minimizer() {
  // produce the same random stuff every time
  gRandom->SetSeed(1);

  RooWorkspace w = RooWorkspace();

  w.factory("Gaussian::g(x[-5,5],mu[-3,3],sigma[1])");

  auto x = w.var("x");
  RooAbsPdf * pdf = w.pdf("g");
  RooRealVar * mu = w.var("mu");

  RooDataSet * data = pdf->generate(RooArgSet(*x), 10000);
  mu->setVal(-2.9);

  auto nll = pdf->createNLL(*data);

  // save initial values for the start of all minimizations
  RooArgSet values = RooArgSet(*mu, *pdf, *nll);
  
  std::cout << std::endl << std::endl;
  values.Print("v");
  mu->Print("v");
  std::cout << std::endl << std::endl;

  // RooArgSet* savedValues = dynamic_cast<RooArgSet*>(values.snapshot());
  // if (savedValues == nullptr) {
  //   throw std::runtime_error("params->snapshot() cannot be casted to RooArgSet!");
  // }

  // std::cout << "trying nominal calculation" << std::endl;
  RooMinimizer m0(*nll);
  m0.setPrintLevel(0);
  m0.setVerbose();

  m0.migrad();

  std::cout << std::endl << std::endl;
  values.Print("v");
  mu->Print("v");
  std::cout << std::endl << std::endl;

  // // m0.hesse();

  // // m0.minos();

  // std::cout << "nominal mu fit is," << mu->getVal() << std::endl;

  // // reset initial values
  // std::cout << std::endl << std::endl;
  // values.Print("v");
  // mu->Print("v");
  // std::cout << "\n === reset initial values === \n" << std::endl;
  // values = *savedValues;
  // values.Print("v");
  // mu->Print("v");
  // std::cout << std::endl << std::endl;

  // std::cout << "trying GradMinimizer" << std::endl;
  // RooGradMinimizer m1(*nll);
  // m1.setVerbose();

  // std::cout << "RooGradMinimizer created" << std::endl;

  // m1.migrad();
    
  // m1.hesse();
  // std::cout << "hesse done" << std::endl;
  
  // m1.minos();
  // std::cout << "minos done" << std::endl;

  // std::cout << std::endl << std::endl;
  // values.Print("v");
  // mu->Print("v");
  // std::cout << std::endl << std::endl;

}
