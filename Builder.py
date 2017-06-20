import ROOT
ROOT.RooMsgService.instance().setGlobalKillBelow(5)

def get_workspace(nchannels = 1, events = 1000, nbins = 1, nnps = 0):
    nevents = events *.9/nbins 
    meas = ROOT.RooStats.HistFactory.Measurement( "meas", "meas" )
    meas.SetPOI( "SignalStrength" )
    meas.SetLumi( 1.0 )
    meas.SetLumiRelErr( 0.02 )
    meas.AddConstantParam( "Lumi" )

    for channel in range(nchannels):
        chan = ROOT.RooStats.HistFactory.Channel( "Region{}".format(channel) )
        chan.SetStatErrorConfig(0.05, "Poisson")

        data_hist = ROOT.TH1D("observed{}".format(channel),"observed", nbins, 0, nbins)
        signal_hist = ROOT.TH1D("above_expected{}".format(channel),"above_expected", nbins, 0, nbins)
        model_hist = ROOT.TH1D("expected{}".format(channel),"expected", nbins, 0, nbins)
        for bin in range(nbins):
            int(nevents*.1*(bin+1))

            for i in range( int(nevents*.1*(bin+1))):
                signal_hist.Fill(bin + 0.5)
                data_hist.Fill(bin + 0.5)
            for i in range( int(nevents)):
                data_hist.Fill(bin + 0.5)
                model_hist.Fill(bin + 0.5)

        chan.SetData( data_hist )
        model = ROOT.RooStats.HistFactory.Sample( "model" )
        model.SetNormalizeByTheory( False )
        model.SetHisto( model_hist )

        signal = ROOT.RooStats.HistFactory.Sample( "signal" )
        signal.SetNormalizeByTheory( False )
        signal.SetHisto( signal_hist )
        
        signal.AddNormFactor( "SignalStrength", 1, 0, 3)


        if nnps > 0:
            for np in range(nnps):
                print "this uncertainty is {}".format(np)
                uncertainty_up   = nevents * 1.1
                uncertainty_down = nevents * 0.9
                signal.AddOverallSys( "signal_norm_uncertainty_{}".format(np),  uncertainty_down*.1, uncertainty_up*.1 )
                model.AddOverallSys( "background_norm_uncertainty_{}".format(np),  uncertainty_down, uncertainty_up )
                
                sig_np_up = signal_hist.Clone()
                sig_np_down = signal_hist.Clone()
                bkg_np_up = model_hist.Clone()
                bkg_np_down = model_hist.Clone()
                for b in range(1,sig_np_up.GetNbinsX()+1):
                    sig_np_up.SetBinContent(b, sig_np_up.GetBinContent(b) + sig_np_up.GetBinContent(b) * .1 * b)
                    sig_np_down.SetBinContent(b, sig_np_down.GetBinContent(b) - sig_np_down.GetBinContent(b) * 0.1 * b)
                    bkg_np_up.SetBinContent(b, bkg_np_up.GetBinContent(b) + bkg_np_up.GetBinContent(b) * .1 * b)
                    bkg_np_down.SetBinContent(b, bkg_np_down.GetBinContent(b) - bkg_np_down.GetBinContent(b) * 0.1 * b)



                signal_shape = ROOT.RooStats.HistFactory.HistoSys("signal_shape_{}".format(np))
                signal_shape.SetHistoHigh( sig_np_up )
                signal_shape.SetHistoLow( sig_np_down )
                signal.AddHistoSys( signal_shape )

                background_shape = ROOT.RooStats.HistFactory.HistoSys("background_shape_{}".format(np))
                background_shape.SetHistoHigh( bkg_np_up )
                background_shape.SetHistoLow( bkg_np_down )
                model.AddHistoSys( background_shape )


        chan.AddSample( model )
        chan.AddSample( signal )
        meas.AddChannel( chan )


    hist2workspace = ROOT.RooStats.HistFactory.HistoToWorkspaceFactoryFast(meas)
    if nchannels < 2:
        return hist2workspace.MakeSingleChannelModel( meas, chan )
    else:
        return hist2workspace.MakeCombinedModel(meas)
