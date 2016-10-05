// run as
// root -l -b -q  lydia1_print_params_observs.C > lydia1_params_observs.txt

using namespace RooFit ;


void lydia1_print_params_observs()
{

        TFile *_file0 = TFile::Open("/user/pbos/lydia/lydia1.root");
        // TFile *_file0 = TFile::Open("/home/patrick/projects/apcocsm/lydia/lydia1.root");
        RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("Run2GGF"));
        RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
        RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName()) ;

        RooAbsData * data = w->data("asimovData");

        RooArgSet* params = pdf->getParameters(data);
        RooAbsCollection* const_params = params->selectByAttrib("Constant",kTRUE);
        RooAbsCollection* var_params = params->selectByAttrib("Constant",kFALSE);
        RooArgSet* observs = pdf->getObservables(data);

        // params->Print()
        // params->Print("v")
        const_params->Print();
        var_params->Print();
        observs->Print();

        // const_params->writeToFile("lydia2_const_params.txt")
        // var_params->writeToFile("lydia2_var_params.txt")
        // observs->writeToFile("lydia2_observs.txt")
}