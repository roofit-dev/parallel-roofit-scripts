// GradMinimizer_Ndim_hierarchical: test RooGradMinimizer class with an
// N-dimensional pdf that forms a tree of Gaussians, where one Gaussian is the
// parameter of a higher level Gaussian
//
// call from command line like, for instance:
// root -l 'GradMinimizer_Ndim_hierarchical.cpp()'

// R__LOAD_LIBRARY(libRooFit)
#pragma cling load("libRooFit")

#include <iostream>
#include <sstream>

using namespace RooFit;

void GradMinimizer_Ndim_hierarchical(int N_events = 1000) {
  // produce the same random stuff every time
  gRandom->SetSeed(1);

  RooWorkspace w("w", 1) ;

  // 3rd level
  w.factory("Gaussian::g0_0_0(v[-10,10],m0_0_0[0.6,-10,10],ga1_0)"); // two branch pdf, one up a level to different 1st level branch
  w.factory("Gamma::ga0_0_1(u[-10,10],k0_0_1[3,2,10],theta0_0_1[5,0.1,10])"); // leaf pdf

  // 2nd level
  w.factory("Gaussian::g0_0(g0_0_0,m0_0[6,-10,10],ga0_0_1)"); // branch pdf
  w.factory("Gamma::ga1_0(z[0,20],k1_0[4,2,10],theta1_0[3,0.1,10])"); // leaf pdf

  // 1st level
  w.factory("Gaussian::g0(x[-10,10],g0_0,s0[3,0.1,10])"); // branch pdf
  w.factory("Gaussian::g1(y[-10,10],m1[-2,-10,10],ga1_0)"); // branch pdf
  RooArgSet level1_pdfs;
  level1_pdfs.add(*w.arg("g0"));
  level1_pdfs.add(*w.arg("g1"));

  // event counts for 1st level pdfs
  RooRealVar a("N_g0", "#events g0", 100, 0., 10*N_events);
  RooRealVar b("N_g1", "#events g1", 100, 0., 10*N_events);  
  w.import(a);
  w.import(b);
  // gather in count_set
  RooArgSet level1_counts;
  level1_counts.add(a);
  level1_counts.add(b);

  // finally, sum the top level pdfs
  RooAddPdf sum("sum", "gaussian tree", level1_pdfs, level1_counts);

  // gather observables
  RooArgSet obs_set;
  obs_set.add(*w.arg("x"));
  obs_set.add(*w.arg("y"));
  obs_set.add(*w.arg("z"));
  obs_set.add(*w.arg("u"));
  obs_set.add(*w.arg("v"));

  // --- Generate a toyMC sample from composite PDF ---
  RooDataSet *data = sum.generate(obs_set, N_events);

  auto nll = sum.createNLL(*data);

  // set parameter values randomly so that they actually need to do some fitting
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
