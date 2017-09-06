#ifndef __CINT__
#include "RooGlobalFunc.h"
#endif
#include "RooStats/HistFactory/Measurement.h"
#include "RooStats/HistFactory/HistoToWorkspaceFactoryFast.h"
#include "RooLinkedListIter.h"
#include "TFile.h"
#include "TROOT.h"
#include "RooWorkspace.h"
#include "RooRealSumPdf.h"
#include "TFile.h"
#include "TH1.h"
#include "TRandom.h"
#include "math.h"
using namespace RooStats ;
using namespace HistFactory ;

Sample addVariations(Sample asample, int nnps, bool channel_crosstalk, int channel){
  for (int nuis = 0; nuis <nnps; ++nuis){
    TRandom *R = new TRandom(channel*nuis/nnps);
    Double_t random = R->Rndm();
    double uncertainty_up = (1+random)/sqrt(100);
    double uncertainty_down = (1-random)/sqrt(100);
    cout<<"in channel "<<channel<<"nuisance +/- ["<<uncertainty_up<<","<<uncertainty_down<<"]"<<endl;
    std::string nuis_name = "norm_uncertainty_"+std::to_string(nuis);
    if (!channel_crosstalk){
      nuis_name = nuis_name+"_channel_"+std::to_string(channel);
    }
    asample.AddOverallSys(nuis_name, uncertainty_up, uncertainty_down);
  }
  return asample;
}



Channel makeChannel(int channel, int nnps, bool channel_crosstalk){
  std::string channel_name = "Region" +std::to_string(channel);
  Channel chan( channel_name );
  auto Signal_Hist = new TH1F("Signal","Signal",100,0,100);
  auto Background_Hist = new TH1F("Background","Background",100,0,100);
  auto Data_Hist = new TH1F("Data","Data",100,0,100);
  int nbins = Signal_Hist->GetXaxis()->GetNbins();
  for (Int_t bin = 1; bin <= nbins; ++bin ) {
    for (Int_t i = 0; i <= bin; ++i ) {
      Signal_Hist->Fill(bin+0.5);
      Data_Hist->Fill(bin+0.5);
    }
    for (Int_t i = 0; i <= 100; ++i ) {
      Background_Hist->Fill(bin+0.5);
      Data_Hist->Fill(bin+0.5);
    }
  }
  chan.SetData( Data_Hist );
  Sample background("background");
  background.SetNormalizeByTheory(false);
  background.SetHisto( Background_Hist );
  background.ActivateStatError();
  Sample signal("signal");
  signal.SetNormalizeByTheory(false);
  signal.SetHisto( Signal_Hist );
  signal.ActivateStatError();
  signal.AddNormFactor("SignalStrength",1,0,3);

  if (nnps > 0){
    signal = addVariations(signal, nnps, true, channel); 
    background = addVariations(background, nnps, false, channel) ;
  }

  chan.AddSample( background );
  chan.AddSample( signal );  
  return chan;
}

void buildBinnedTest3(){
  int n_channels = 1;
  bool channel_crosstalk = true;
  int nnps = 0;
  Measurement meas("meas","meas");
  meas.SetPOI( "SignalStrength" );
  meas.SetLumi( 1.0 );
  meas.SetLumiRelErr( 0.10 );
  meas.AddConstantParam("Lumi");

  Channel chan;
  for (int channel=0; channel < n_channels; ++channel){
    chan = makeChannel(channel, nnps, channel_crosstalk);
    meas.AddChannel( chan );
  }
  HistoToWorkspaceFactoryFast hist2workspace(meas);
  RooWorkspace *ws;
  if (n_channels < 2){
    ws = hist2workspace.MakeSingleChannelModel( meas, chan );
  }
  else{
    ws = hist2workspace.MakeCombinedModel( meas);
  }

  RooFIter iter = ws->components().fwdIterator() ;
  RooAbsArg* arg ;
  while((arg=iter.next())) {
    if (arg->IsA()==RooRealSumPdf::Class()) {
      arg->setAttribute("BinnedLikelihood") ;
      cout << "component " << arg->GetName() << " is a binned likelihood" << endl ;
    }
  }
  ws->SetName("BinnedWorkspace");
  ws->writeToFile("workspace.root");
}
