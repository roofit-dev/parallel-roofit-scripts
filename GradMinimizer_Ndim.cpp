// GradMinimizer_Ndim: test RooGradMinimizer class with simple N-dimensional pdf
//
// call from command line like, for instance:
// root -l 'GradMinimizer_Ndim.cpp()'

// R__LOAD_LIBRARY(libRooFit)
#pragma cling load("libRooFit")

#include <iostream>
#include <sstream>

using namespace RooFit;

void GradMinimizer_Ndim(int n = 3, int N_events = 1000) {
  // produce the same random stuff every time
  gRandom->SetSeed(1);

  RooWorkspace w("w", kFALSE);

  RooArgSet obs_set;

  // create gaussian parameters
  float mean[n], sigma[n];
  for (int ix = 0; ix < n; ++ix) {
    mean[ix] = gRandom->Gaus(0, 2);
    sigma[ix] = 0.1 + abs(gRandom->Gaus(0, 2));
  }

  // create gaussians and also the observables and parameters they depend on
  for (int ix = 0; ix < n; ++ix) {
    std::cout << ix << std::endl;
    std::ostringstream os;
    // int ix_p = (ix/2) % N_parameters;
    os << "Gaussian::g" << ix
       << "(x" << ix << "[-10,10],"
       << "m" << ix << "[" << mean[ix] << ",-10,10],"
       << "s" << ix << "[" << sigma[ix] << ",0.1,10])";
    w.factory(os.str().c_str());
  }

  // create uniform background signals on each observable
  for (int ix = 0; ix < n; ++ix) {
    {
      std::ostringstream os;
      os << "Uniform::u" << ix << "(x" << ix << ")";
      w.factory(os.str().c_str());
    }

    // gather the observables in a list for data generation below
    {
      std::ostringstream os;
      os << "x" << ix;
      obs_set.add(*w.arg(os.str().c_str()));
    }
  }

  RooArgSet pdf_set = w.allPdfs();

  // create event counts for all pdfs
  RooArgSet count_set;

  // ... for the gaussians
  for (int ix = 0; ix < n; ++ix) {
    std::stringstream os, os2;
    os << "Nsig" << ix;
    os2 << "#signal events comp " << ix;
    RooRealVar a(os.str().c_str(), os2.str().c_str(), 100, 0., 10*N_events);
    w.import(a);
    // gather in count_set
    count_set.add(*w.arg(os.str().c_str()));
  }
  // ... and for the uniform background components
  for (int ix = 0; ix < n; ++ix) {
    std::stringstream os, os2;
    os << "Nbkg" << ix;
    os2 << "#background events comp " << ix;
    RooRealVar a(os.str().c_str(), os2.str().c_str(), 100, 0., 10*N_events);
    w.import(a);
    // gather in count_set
    count_set.add(*w.arg(os.str().c_str()));
  }

  RooAddPdf sum("sum", "gaussians+uniforms", pdf_set, count_set);

  // --- Generate a toyMC sample from composite PDF ---
  RooDataSet *data = sum.generate(obs_set, N_events);

  auto nll = sum.createNLL(*data);

  // set values randomly so that they actually need to do some fitting
  for (int ix = 0; ix < n; ++ix) {
    {
      std::ostringstream os;
      os << "m" << ix;
      dynamic_cast<RooRealVar *>(w.arg(os.str().c_str()))->setVal(gRandom->Gaus(0, 2));
    }
    {
      std::ostringstream os;
      os << "s" << ix;
      dynamic_cast<RooRealVar *>(w.arg(os.str().c_str()))->setVal(0.1 + abs(gRandom->Gaus(0, 2)));
    }
  }

  // gather all values of parameters, observables, pdfs and nll here for easy
  // saving and restoring
  RooArgSet some_values = RooArgSet(obs_set, pdf_set, "some_values");
  RooArgSet all_values = RooArgSet(some_values, count_set, "all_values");
  all_values.add(*nll);
  all_values.add(sum);
  for (int ix = 0; ix < n; ++ix) {
    {
      std::ostringstream os;
      os << "m" << ix;
      all_values.add(*w.arg(os.str().c_str()));
    }
    {
      std::ostringstream os;
      os << "s" << ix;
      all_values.add(*w.arg(os.str().c_str()));
    }
  }

  // save initial values for the start of all minimizations  
  RooArgSet* savedValues = dynamic_cast<RooArgSet*>(all_values.snapshot());
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


  std::cout << " ====================================== " << std::endl;
  // --------

  std::cout << " ======== reset initial values ======== " << std::endl;
  all_values = *savedValues;

  // --------
  std::cout << " ====================================== " << std::endl;


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

  // std::cout << "\n === reset initial values === \n" << std::endl;
  // values = *savedValues;

  // // --------


  // std::cout << "trying nominal calculation AGAIN" << std::endl;

  // RooMinimizer m2(*nll);
  // m2.setMinimizerType("Minuit2");

  // m2.setStrategy(0);
  // // m2.setVerbose();
  // m2.setPrintLevel(0);

  // wtimer.start();
  // m2.migrad();
  // wtimer.stop();

  // std::cout << "  -- second nominal calculation wall clock time: " << wtimer.timing_s() << "s" << std::endl;

  // m2.hesse();

  // m2.minos();


}
