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

  RooWorkspace w("w", kFALSE);

  // 3rd level
  w.factory("Gamma::ga0_0_1(k0_0_1[3,2,10],u[1,20],1,0)"); // leaf pdf
  // Gamma(mu,N+1,1,0) ~ Pois(N,mu), so this is a "continuous Poissonian"

  // 2nd level that will be linked to from 3rd level
  w.factory("Gamma::ga1_0(k1_0[4,2,10],z[1,20],1,0)"); // leaf pdf

  // rest of 3rd level
  w.factory("Gaussian::g0_0_0(v[-10,10],m0_0_0[0.6,-10,10],ga1_0)"); // two branch pdf, one up a level to different 1st level branch

  // rest of 2nd level
  w.factory("Gaussian::g0_0(g0_0_0,m0_0[6,-10,10],ga0_0_1)"); // branch pdf

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
  for (auto obs : {"x", "y", "z", "u", "v"}) {
    obs_set.add(*w.arg(obs));
  }
  
  // --- Generate a toyMC sample from composite PDF ---
  RooDataSet *data = sum.generate(obs_set, N_events);

  auto nll = sum.createNLL(*data);

  // gather all values of parameters, observables, pdfs and nll here for easy
  // saving and restoring
  RooArgSet some_values = RooArgSet(obs_set, w.allPdfs(), "some_values");
  RooArgSet most_values = RooArgSet(some_values, level1_counts, "most_values");
  most_values.add(*nll);
  most_values.add(sum);

  RooArgSet * param_set = nll->getParameters(obs_set);

  RooArgSet all_values = RooArgSet(most_values, *param_set, "all_values");

  // set parameter values randomly so that they actually need to do some fitting
  auto it = all_values.fwdIterator();
  while (RooRealVar * val = dynamic_cast<RooRealVar *>(it.next())) {
    val->setVal(gRandom->Uniform(val->getMin(), val->getMax()));
  }

  // save initial values for the start of all minimizations  
  RooArgSet* savedValues = dynamic_cast<RooArgSet*>(all_values.snapshot());
  if (savedValues == nullptr) {
    throw std::runtime_error("params->snapshot() cannot be casted to RooArgSet!");
  }

  // --------

  RooWallTimer wtimer;

  // --------

  std::cout << "trying nominal calculation" << std::endl;

  RooMinimizer m0(*nll);
  m0.setMinimizerType("Minuit2");

  m0.setStrategy(0);
  m0.setPrintLevel(0);

  wtimer.start();
  m0.migrad();
  wtimer.stop();

  std::cout << "  -- nominal calculation wall clock time:        " << wtimer.timing_s() << "s" << std::endl;


  std::cout << " ====================================== " << std::endl;
  // --------

  std::cout << " ======== reset initial values ======== " << std::endl;
  all_values = *savedValues;

  // --------
  std::cout << " ====================================== " << std::endl;


  std::cout << "trying GradMinimizer" << std::endl;

  RooGradMinimizer m1(*nll);

  m1.setStrategy(0);
  m1.setPrintLevel(0);

  wtimer.start();
  m1.migrad();
  wtimer.stop();

  std::cout << "  -- GradMinimizer calculation wall clock time:  " << wtimer.timing_s() << "s" << std::endl;


// N_g0    = 494.514  +/-  18.8621 (limited)
// N_g1    = 505.817  +/-  24.6705 (limited)
// k0_0_1    = 2.96883  +/-  0.00561152  (limited)
// k1_0    = 4.12068  +/-  0.0565994 (limited)
// m0_0    = 8.09563  +/-  1.30395 (limited)
// m0_0_0    = 0.411472   +/-  0.183239  (limited)
// m1    = -1.99988   +/-  0.00194089  (limited)
// s0    = 3.04623  +/-  0.0982477 (limited)

}
