void numint_diag()
{
  // Create dummy pdf
  RooWorkspace w("w") ;
  // x*x dwingt af dat analytische uniform integral niet meer werkt
w.factory("SUM::model(fsig[0,1]*Gaussian::sig(x[-10,10],0,3),Uniform::bkg(expr::xprime('x*x',x)))") ;
  RooAbsPdf* pdf = w.pdf("model") ;
  RooArgSet obs(*w.var("x")) ;

  //---- ALGORITHM BEGINS HERE ---

  //*** Find all numerical integrals in pdf ***
  RooArgSet numIntSet ;

  // Get list of branch nodes in expression
  RooArgSet blist ; // model, sig & bkg
  pdf->branchNodeServerList(&blist) ;

  // Interator over branch nodes
  RooFIter iter = blist.fwdIterator() ;
  RooAbsArg* node ;
  while(node = iter.next()) {
    RooAbsPdf* pdfNode = dynamic_cast<RooAbsPdf*>(node) ;
        if (!pdfNode) continue ; 
    // Skip self-normalized nodes. Call to getNormIntegral will construct
    // an explicit integral object, but it is never used (may need to fix this in getNormIntegral...)
    // sommige pdfs zoals add, of product, zijn self-normalised, want componenten normalised
    if (pdfNode->isSelfNormalized()) continue ;

    // Retrieve normalization integral object for branch nodes that are pdfs
    // kunnen vershillende cached normalisatie integralen zijn, omdat dat verschilt per observable definitie
    RooAbsReal* normint = pdfNode->getNormIntegral(obs) ;

    // Integral expressions can be composite objects (in case of disjoint normalization ranges)
    // Therefore: retrieve list of branch nodes of integral expression
    if (!normint) continue ;

    RooArgList bi ;
    normint->branchNodeServerList(&bi) ;
    RooFIter ibiter = bi.fwdIterator() ;
    RooAbsArg* inode ;
    while(inode = ibiter.next()) {
      // If a RooRealIntegal component is found...
      if (inode->IsA()==RooRealIntegral::Class()) {
    // Retrieve the number of real dimensions that is integrated numerically,
    RooRealIntegral* rri = (RooRealIntegral*)inode ;
    Int_t numIntDim = rri->numIntRealVars().getSize() ;
    // .. and add to list if numeric integration occurs
    if (numIntDim>0) {
      numIntSet.add(*rri) ;
    }
      }
    }
  }

  // --- ALGORITHM ENDS HERE

  cout << "list of numeric integral objects" << endl ;
  numIntSet.Print() ; // DE DINGEN DIE HIER IN STAAN MOETEN DUS GETIMED WORDEN!

  // vlaggetje aanzetten in die dingen, kan voorlopig on the fly. Elke rooabsarg kan boolean attribute; raa.setAttribute("timing_on")
  // in RRI in evaluate() if (getAttribute("timing_on"), iets met timing doen)
  // RATS::evaluatePartition() regel 398, daar ook
  // 
  // RooTrace
  // std::map (namen van de objecten) -> timings
  // eentje per class (rats / rri)?
  // timer voor elke likelihood component en elke numerieke integraal
  // alles aanzetten voor de fork? hoef je dat iig niet meer te communiceren...
  // wil je het dynamisch aan/uit kunnen zetten? kunt ook nog een global flag hebben "timing_off" en die or'en met de lokale flag
  // hoe ga je timings harvesten aan einde van evaluate?
  // voordeel van meteen in global list schrijven: alleen maar list doorsturen

  // caveat: er zijn situatie waar num int voor elk event wordt uitgerekened, typsisch als je conditional pdfs gebruikt
  //    bijv in b-fysica, waar pdf parameter afh is van event
  // maar ja, das gewoon duur

  // TODO DUS:
  // twee lijsten, 1 voor numints en 1 voor likelis
  // flag aanzetten op elk server proces
  // timings harvesten
  // bij harvest van likelihood ook even coderen in naam van likelihood (in map) welke partitie hij uitrekent
}
