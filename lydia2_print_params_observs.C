// run as
// root -l -b -q  lydia2_print_params_observs.C > lydia2_params_observs.txt

using namespace RooFit ;


void lydia2_print_params_observs()
{

        // TFile *_file0 = TFile::Open("/user/pbos/lydia/lydia2.root");
        TFile *_file0 = TFile::Open("/Users/pbos/projects/apcocsm/lydia/lydia2.root");
        RooWorkspace* w = static_cast<RooWorkspace*>(gDirectory->Get("combined"));
        RooStats::ModelConfig* mc = static_cast<RooStats::ModelConfig*>(w->genobj("ModelConfig"));
        RooAbsPdf* pdf = w->pdf(mc->GetPdf()->GetName()) ;

        RooAbsData * data = w->data("combData");

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
