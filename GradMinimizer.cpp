// GradMinimizer: test RooGradMinimizer class
//
// call from command line like, for instance:
// root -l 'GradMinimizer.cpp()'

// R__LOAD_LIBRARY(libRooFit)

#include <iostream>
// #include <exception>

using namespace RooFit;

void GradMinimizer() {
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
  
  RooArgSet* savedValues = dynamic_cast<RooArgSet*>(values.snapshot());
  if (savedValues == nullptr) {
    throw std::runtime_error("params->snapshot() cannot be casted to RooArgSet!");
  }

  // --------

  RooWallTimer wtimer;
  // RooCPUTimer ctimer 

  // --------

  std::cout << "trying nominal calculation" << std::endl;

  RooMinimizer m0(*nll);
  m0.setMinimizerType("Minuit2");

  m0.setStrategy(0);
  // m0.setVerbose();
  m0.setPrintLevel(0);

  wtimer.start();
  m0.migrad();
  wtimer.stop();

  std::cout << "  -- nominal calculation wall clock time:        " << wtimer.timing_s() << "s" << std::endl;

  // m0.hesse();

  // m0.minos();


  // --------

  std::cout << "\n === reset initial values === \n" << std::endl;
  values = *savedValues;

  // --------


  std::cout << "trying GradMinimizer" << std::endl;

  RooGradMinimizer m1(*nll);

  m1.setStrategy(0);
  // m1.setVerbose();
  m1.setPrintLevel(0);

  wtimer.start();
  m1.migrad();
  wtimer.stop();

  std::cout << "  -- GradMinimizer calculation wall clock time:  " << wtimer.timing_s() << "s" << std::endl;


  // std::cout << "run hesse" << std::endl;
  // m1.hesse();
  // std::cout << "hesse done" << std::endl;
  
  // m1.minos();
  // std::cout << "minos done" << std::endl;

  // std::cout << std::endl << std::endl;
  // values.Print("v");
  // mu->Print("v");
  // std::cout << std::endl << std::endl;


  // --------

  std::cout << "\n === reset initial values === \n" << std::endl;
  values = *savedValues;

  // --------


  std::cout << "trying nominal calculation AGAIN" << std::endl;

  RooMinimizer m2(*nll);
  m2.setMinimizerType("Minuit2");

  m2.setStrategy(0);
  // m2.setVerbose();
  m2.setPrintLevel(0);

  wtimer.start();
  m2.migrad();
  wtimer.stop();

  std::cout << "  -- second nominal calculation wall clock time: " << wtimer.timing_s() << "s" << std::endl;

  // m2.hesse();

  // m2.minos();


}
