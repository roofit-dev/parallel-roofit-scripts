#include <chrono>
#include <iostream>
#include <sstream>

using namespace RooFit;

void printDataHistPyDict(RooDataHist *hist) {
  // EGP: write out data in Python dict format
  std::cout << "hist size = " << hist->numEntries() << std::endl ;
  std::cout << "[" << std::endl;
  for (Int_t i=0 ; i<hist->numEntries() ; i++) {
    std::cout << "  {'x_bin': " << hist->get(i)->getRealValue("x")
              << ", 'weight': " << hist->weight()
              << ", 'vol': " << hist->binVolume()
              << "}," << std::endl;
  }
  std::cout << "]" << std::endl;

}

void hist_scaling()
{
  int N_gaussians = 10;
  int N_observables = 2;
  int N_timing_loops = 1;
  int printlevel = 3;

  // Make workspace met parent distributions
  RooWorkspace w("w",1) ;
  for (int ix = 0; ix < N_gaussians; ++ix) {
    ostringstream gs, us;
    gs << "Gaussian::g" << ix << "(x" << ix % N_observables << "[-10,10],0,3)";
    us << "Uniform::u" << ix << "(x" << ix % N_observables << ")";
    w.factory(gs.str());
    w.factory(us.str());
  }

  // Sample twee histogrammen van parent distributions
  RooDataHist* h_g = w.pdf("g")->generateBinned(*w.var("x"),1000) ;
  RooDataHist* h_u = w.pdf("u")->generateBinned(*w.var("x"),1000) ;

  // std::cout << "GAUSSIAN SAMPLE" << std::endl;
  // printDataHistPyDict(h_g);
  // std::cout << "UNIFORM SAMPLE" << std::endl;
  // printDataHistPyDict(h_u);

  // Make 2 pdfs die histogram als onderliggende implementatie hebben
  RooHistPdf hp_g("hp_g","hp_g",*w.var("x"),*h_g) ;
  RooHistPdf hp_u("hp_u","hp_u",*w.var("x"),*h_u) ;

  // Construct pdf als som van twee histogram-based pdf
  RooRealVar frac("frac","frac",0,1) ;
  RooAddPdf model("model","model",RooArgList(hp_g,hp_u),frac) ;

  // Sample toy data van gezamenlijk model
  RooDataHist* toyData = model.generateBinned(*w.var("x"),1000) ;
  
  // std::cout << "COMBINED SAMPLE" << std::endl;
  // printDataHistPyDict(toyData);

  // Fit toy daya
  unsigned int duration_ns;
  unsigned int total_duration_ns(0);
  unsigned int min_duration_ns;

  for (int i = 0; i < N_timing_loops; ++i) {
    auto begin = std::chrono::high_resolution_clock::now();
    model.fitTo(*toyData, PrintLevel(printlevel)) ;    
    auto end = std::chrono::high_resolution_clock::now();

    frac = 0.5;
    duration_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count();
    total_duration_ns += duration_ns;
    if (i==0) {
      min_duration_ns = duration_ns;
    } else {
      min_duration_ns = min(min_duration_ns, duration_ns);
    }
  }
  
  std::cout << std::endl
            << N_timing_loops << " loops" << std::endl
            << total_duration_ns / 1e9 << "s total duration" << std::endl
            << total_duration_ns / 1e9 / N_timing_loops << "s average per loop" << std::endl
            << min_duration_ns / 1e9 << "s fastest loop" << std::endl << std::endl;

  // EGP: toegevoegd, aangepast uit roofit_demo.cpp
  // --- Plot toy data and composite PDF overlaid ---
  RooPlot* frame = w.var("x")->frame() ;
  toyData->plotOn(frame) ;
  model.plotOn(frame) ;
  model.plotOn(frame, Components(hp_g), LineStyle(kDashed), LineColor(kRed)) ;
  model.plotOn(frame, Components(hp_u), LineStyle(kDashed), LineColor(kGreen)) ;

  frame->Draw();

}
