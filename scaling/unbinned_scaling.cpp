#include <chrono>
#include <iostream>
#include <sstream>

using namespace RooFit;

void unbinned_scaling() {
  int N_gaussians(20);
  int N_observables(5);
  int N_parameters(12);  // must be even, means and sigmas have diff ranges
  int N_events(1000);

  int obs_plot_x(3);
  int obs_plot_y(2);
  int obs_plot_x_px(1200);
  int obs_plot_y_px(800);

  // int N_timing_loops(1);
  // int printlevel(3);
  int optimizeConst(2);

  if (N_parameters % 2 != 0) {
    std::cout << "set N_parameters to an even number!" << std::endl;
    exit(2);
  }

  RooWorkspace w("w",1) ;

  RooArgSet obs_set;

  // create gaussian parameters
  float mean[N_parameters/2], sigma[N_parameters/2];
  for (int ix = 0; ix < N_parameters/2; ++ix) {
    mean[ix] = gRandom->Gaus(0, 2);
    sigma[ix] = 0.1 + abs(gRandom->Gaus(0, 2));
  }

  // create gaussians and also the observables and parameters they depend on
  for (int ix = 0; ix < N_gaussians; ++ix) {
    std::cout << ix << std::endl;
    std::ostringstream os;
    // int ix_p = (ix/2) % N_parameters;
    int ix_p = ix % (N_parameters / 2);
    os << "Gaussian::g" << ix << "(x" << ix % N_observables << "[-10,10],"
                              << "m" << ix_p << "[" << mean[ix_p] << ",-10,10],"
                              << "s" << ix_p << "[" << sigma[ix_p] << ",0.1,10])";
    std::string s = os.str();
    w.factory(s.c_str());
  }

  // create uniform background signals on each observable
  for (int ix = 0; ix < N_observables; ++ix) {
    {
      std::ostringstream os;
      os << "Uniform::u" << ix << "(x" << ix << ")";
      std::string s = os.str();
      w.factory(s.c_str()); 
    }

    // gather the observables in a list for data generation below
    {
      std::ostringstream os;
      os << "x" << ix;
      std::string s = os.str();
      obs_set.add(*w.arg(s.c_str()));
    }
  }

  RooArgSet pdf_set = w.allPdfs();

  // create event counts for all pdfs
  RooArgSet count_set;

  // ... for the gaussians
  for (int ix = 0; ix < N_gaussians; ++ix) {
    std::stringstream os, os2;
    os << "Nsig" << ix;
    std::string s = os.str();
    os2 << "#signal events comp " << ix;
    std::string s2 = os2.str();
    RooRealVar a(s.c_str(), s2.c_str(), 100, 0., 10000);
    w.import(a);
  }
  // gather them in count_set
  for (int ix = 0; ix < N_gaussians; ++ix) {
    std::stringstream os, os2;
    os << "Nsig" << ix;
    std::string s = os.str();
    count_set.add(*w.arg(s.c_str()));
  }
  // ... and for the uniform background components
  for (int ix = 0; ix < N_observables; ++ix) {
    std::stringstream os, os2;
    os << "Nbkg" << ix;
    std::string s = os.str();
    os2 << "#background events comp " << ix;
    std::string s2 = os2.str();
    RooRealVar a(s.c_str(), s2.c_str(), 100, 0., 10000);
    w.import(a);
  }
  // gather them in count_set
  for (int ix = 0; ix < N_observables; ++ix) {
    std::stringstream os, os2;
    os << "Nbkg" << ix;
    std::string s = os.str();
    count_set.add(*w.arg(s.c_str()));
  }

  RooAddPdf sum("sum", "gaussians+uniforms", pdf_set, count_set);

  // --- Generate a toyMC sample from composite PDF ---
  RooDataSet *data = sum.generate(obs_set, N_events);
/*
  // OR reload previously written out sample:
  // wegschrijven:
  data.write("roofit_demo_random_data_values.dat");
  // om het weer in te lezen:
  RooDataSet *data = RooDataSet::read("../roofit_demo_random_data_values.dat", RooArgList(mes));
*/


  // --- Perform extended ML fit of composite PDF to toy data ---
  // sum.fitTo(*data,"Extended") ;
  // instead of full fitTo, only do the fit, leave out error matrix, using
  // run style of run_higgs.C
  RooAbsReal* nll = sum.createNLL(*data,"Extended");
  RooMinimizer m(*nll) ;
  // m.setVerbose(1) ;
  m.setStrategy(0) ;
  m.setProfile(1) ;
  m.optimizeConst(optimizeConst) ;

  auto begin = std::chrono::high_resolution_clock::now();
  // m.hesse();

  m.minimize("Minuit2","migrad") ;

  auto end = std::chrono::high_resolution_clock::now();
  std::cout << std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count() / 1e9  << "s" << std::endl;

  // print the "true" values for comparison
  std::cout << "--- values of PDF parameters used for data generation:" << std::endl;
  for (int ix = 0; ix < N_parameters/2; ++ix) {
    std::cout << "    gauss " << ix << ": m = " << mean[ix] << ", s = " << sigma[ix] << std::endl;
  }

  // --- Plot toy data and composite PDF overlaid ---
  TCanvas* c = new TCanvas("unbinned_scaling","unbinned_scaling",obs_plot_x_px,obs_plot_y_px) ;
  c->Divide(obs_plot_x, obs_plot_y) ;
  // c->cd(1) ; gPad->SetLeftMargin(0.15) ; x0frame->GetYaxis()->SetTitleOffset(1.4) ; x0frame->Draw() ;
  // c->cd(2) ; gPad->SetLeftMargin(0.15) ; x1frame->GetYaxis()->SetTitleOffset(1.4) ; x1frame->Draw() ;
  for (int ix = 0; ix < N_observables && ix < obs_plot_x * obs_plot_y; ++ix) {
    std::ostringstream os;
    os << "x" << ix;
    std::string s = os.str();
    RooPlot* frame = w.var(s.c_str())->frame() ;
    data->plotOn(frame) ;
    sum.plotOn(frame) ;
    c->cd(ix+1) ; frame->Draw() ;
  }
}
