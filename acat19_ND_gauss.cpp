// call from command line like, for instance:
// root -l 'acat19_ND_gauss.cpp()'

R__LOAD_LIBRARY(libRooFit)

#include <chrono>
#include <iostream>

using namespace RooFit;

// return two unique_ptrs, the first because nll is a pointer,
// the second because RooArgSet doesn't have a move ctor
std::tuple<std::unique_ptr<RooAbsReal>, std::unique_ptr<RooArgSet>>
generate_ND_gaussian_pdf_nll(RooWorkspace &w, unsigned int n, unsigned long N_events) {
  RooArgSet obs_set;

  // create gaussian parameters
  double mean[n], sigma[n];
  for (unsigned ix = 0; ix < n; ++ix) {
    mean[ix] = RooRandom::randomGenerator()->Gaus(0, 2);
    sigma[ix] = 0.1 + abs(RooRandom::randomGenerator()->Gaus(0, 2));
  }

  // create gaussians and also the observables and parameters they depend on
  for (unsigned ix = 0; ix < n; ++ix) {
    std::ostringstream os;
    os << "Gaussian::g" << ix
       << "(x" << ix << "[-10,10],"
       << "m" << ix << "[" << mean[ix] << ",-10,10],"
       << "s" << ix << "[" << sigma[ix] << ",0.1,10])";
    w.factory(os.str().c_str());
  }

  // create uniform background signals on each observable
  for (unsigned ix = 0; ix < n; ++ix) {
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
  for (unsigned ix = 0; ix < n; ++ix) {
    std::stringstream os, os2;
    os << "Nsig" << ix;
    os2 << "#signal events comp " << ix;
    RooRealVar a(os.str().c_str(), os2.str().c_str(), N_events/10, 0., 10*N_events);
    w.import(a);
    // gather in count_set
    count_set.add(*w.arg(os.str().c_str()));
  }
  // ... and for the uniform background components
  for (unsigned ix = 0; ix < n; ++ix) {
    std::stringstream os, os2;
    os << "Nbkg" << ix;
    os2 << "#background events comp " << ix;
    RooRealVar a(os.str().c_str(), os2.str().c_str(), N_events/10, 0., 10*N_events);
    w.import(a);
    // gather in count_set
    count_set.add(*w.arg(os.str().c_str()));
  }

  RooAddPdf* sum = new RooAddPdf("sum", "gaussians+uniforms", pdf_set, count_set);
  w.import(*sum);  // keep sum around after returning

  // --- Generate a toyMC sample from composite PDF ---
  RooDataSet *data = sum->generate(obs_set, N_events);

  std::unique_ptr<RooAbsReal> nll {sum->createNLL(*data)};

  // set values randomly so that they actually need to do some fitting
  for (unsigned ix = 0; ix < n; ++ix) {
    {
      std::ostringstream os;
      os << "m" << ix;
      dynamic_cast<RooRealVar *>(w.arg(os.str().c_str()))->setVal(RooRandom::randomGenerator()->Gaus(0, 2));
    }
    {
      std::ostringstream os;
      os << "s" << ix;
      dynamic_cast<RooRealVar *>(w.arg(os.str().c_str()))->setVal(0.1 + abs(RooRandom::randomGenerator()->Gaus(0, 2)));
    }
  }

  // gather all values of parameters, pdfs and nll here for easy
  // saving and restoring
  std::unique_ptr<RooArgSet> all_values = std::make_unique<RooArgSet>(pdf_set, count_set, "all_values");
  all_values->add(*nll);
  all_values->add(*sum);
  for (unsigned ix = 0; ix < n; ++ix) {
    {
      std::ostringstream os;
      os << "m" << ix;
      all_values->add(*w.arg(os.str().c_str()));
    }
    {
      std::ostringstream os;
      os << "s" << ix;
      all_values->add(*w.arg(os.str().c_str()));
    }
  }

  return std::make_tuple(std::move(nll), std::move(all_values));
}

////////////////////////////////////////////////////////////////////////////////////////////////////
// timing_flag is used to activate only selected timing statements [1-7]
// num_cpu: -1 is special option -> compare overhead communication protocol (wrt 1 cpu)
// parallel_interleave: 0 = blocks of equal size, 1 = interleave, 2 = simultaneous pdfs mode
//                      { BulkPartition=0, Interleave=1, SimComponents=2, Hybrid=3 }
////////////////////////////////////////////////////////////////////////////////////////////////////

void acat19_ND_gauss(std::size_t n_param) {
    RooMsgService::instance().deleteStream(0);
    RooMsgService::instance().deleteStream(0);

    RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Benchmarking1));
    RooMsgService::instance().addStream(RooFit::DEBUG, RooFit::Topic(RooFit::Benchmarking2));

    std::size_t seed = 1;
    RooRandom::randomGenerator()->SetSeed(seed);

    RooWorkspace w = RooWorkspace();

    // the Gaussians themselves have 4 parameters per "dimension", so divide by 4
    std::size_t n_dim = n_param/4;

    std::unique_ptr<RooAbsReal> nll;
    std::unique_ptr<RooArgSet> values;
    std::tie(nll, values) = generate_ND_gaussian_pdf_nll(w, n_dim, 1000);

    RooFit::MultiProcess::GradMinimizer m(*nll, 8);

    m.setPrintLevel(-1);
    m.setStrategy(0);
    m.setProfile(false);
    m.optimizeConst(2);
    m.setMinimizerType("Minuit2");
    // m.setVerbose(kTRUE);

    auto get_time = [](){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();};

    auto start = std::chrono::high_resolution_clock::now();
    std::cout << "start migrad at " << get_time() << std::endl;
    m.migrad();
    std::cout << "end migrad at " << get_time() << std::endl;
    auto end = std::chrono::high_resolution_clock::now();
    auto elapsed_seconds =
        std::chrono::duration_cast<std::chrono::duration<double>>(
            end - start).count();
    std::cout << "migrad: " << elapsed_seconds << "s" << std::endl;
}
