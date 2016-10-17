using namespace RooFit ;

void histpdf()
{
  
  // Make workspace met parent distributions
  RooWorkspace w("w",1) ;
  w.factory("Gaussian::g(x[-10,10],0,3)") ;
  w.factory("Uniform::u(x)") ;

  // Sample twee histogrammen van parent distributions
  RooDataHist* h_g = w.pdf("g")->generateBinned(*w.var("x"),1000) ;
  RooDataHist* h_u = w.pdf("u")->generateBinned(*w.var("x"),1000) ;

  // Make 2 pdfs die histogram als onderliggende implementatie hebben
  RooHistPdf hp_g("hp_g","hp_g",*w.var("x"),*h_g) ;
  RooHistPdf hp_u("hp_u","hp_u",*w.var("x"),*h_u) ;

  // Construct pdf als som van twee histogram-based pdf
  RooRealVar frac("frac","frac",0,1) ;
  RooAddPdf model("model","model",RooArgList(hp_g,hp_u),frac) ;

  // Sample toy data van gezamenlijk model
  RooDataHist* toyData = model.generateBinned(*w.var("x"),1000) ;
  
  // Fit toy daya
  model.fitTo(*toyData) ;
  
  // EGP: toegevoegd, aangepast uit roofit_demo.cpp
  // --- Plot toy data and composite PDF overlaid ---
  RooPlot* frame = w.var("x")->frame() ;
  toyData->plotOn(frame) ;
  model.plotOn(frame) ;
  model.plotOn(frame, Components(hp_g), LineStyle(kDashed), LineColor(kRed)) ;
  model.plotOn(frame, Components(hp_u), LineStyle(kDashed), LineColor(kGreen)) ;

  frame->Draw();

}
