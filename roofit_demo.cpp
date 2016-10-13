#include <chrono>
#include <iostream>

using namespace RooFit ;

void roofit_demo() {
  // --- Observable ---
  RooRealVar mes("mes","m_{ES} (GeV)",5.20,5.30) ;

  // --- Build Gaussian signal PDF ---
  RooRealVar sigmean("sigmean","B^{#pm} mass",5.28,5.20,5.30) ;
  RooRealVar sigwidth("sigwidth","B^{#pm} width",0.0027,0.001,1.) ;
  RooGaussian gauss("gauss","gaussian PDF",mes,sigmean,sigwidth) ;

  // --- Build Argus background PDF ---
  RooRealVar argpar("argpar","argus shape parameter",-20.0,-100.,-1.) ;
  RooConstVar m0("m0", "resonant mass", 5.291);
  RooArgusBG argus("argus","Argus PDF",mes,m0,argpar) ;

  // --- Construct signal+background PDF ---
  RooRealVar nsig("nsig","#signal events",200,0.,10000) ;
  RooRealVar nbkg("nbkg","#background events",800,0.,10000) ;
  RooAddPdf sum("sum","g+a",RooArgList(gauss,argus),RooArgList(nsig,nbkg)) ;

  // --- Generate a toyMC sample from composite PDF ---
/*  RooDataSet *data = sum.generate(mes,2000) ;
  // OR reload previously written out sample:

  // wegschrijven:
  data.write("roofit_demo_random_data_values.dat");
*/
  // om het weer in te lezen:
  RooDataSet *data = RooDataSet::read("../roofit_demo_random_data_values.dat", RooArgList(mes));

  auto begin = std::chrono::high_resolution_clock::now();

  // --- Perform extended ML fit of composite PDF to toy data ---
  sum.fitTo(*data,"Extended") ;

  auto end = std::chrono::high_resolution_clock::now();
  std::cout << std::chrono::duration_cast<std::chrono::nanoseconds>(end-begin).count() / 1e9  << "s" << std::endl;

  // --- Plot toy data and composite PDF overlaid ---
  RooPlot* mesframe = mes.frame() ;
  data->plotOn(mesframe) ;
  sum.plotOn(mesframe) ;
  sum.plotOn(mesframe,Components(argus),LineStyle(kDashed)) ;

  mesframe->Draw();
}
