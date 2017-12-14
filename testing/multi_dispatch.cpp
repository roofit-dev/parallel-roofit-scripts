#include <iostream>

/*
 * In this test, we want to simulate and understand the situation we had on 
 * 14 Dec 2017 with using MnSeedGenerator::operator(). These are overloaded for
 * two classes: GradientCalculator and AnalyticalGradientCalculator. I was
 * unpleasantly surprised that a call on an ExternalInternalGradientCalculator,
 * which is a subclass of AGC, was dispatched to the GC function. To be precise,
 * I was calling the function on a dereferenced pointer to an EIGC, i.e.
 * something like EIGC *e; fct(*e);. The GC function is above the AGC one in the
 * source file, so I figured order may have something to do with it; overload
 * resolution just taking the first function that matches for the type for which
 * the function is not explicitly overloaded. In this file I want to test that
 * hypothesis and find a solution that does work.
 *
 * Actually, a further complication is present: the operator()s are virtual
 * class methods.
 */

class A {};

class B : public A {};

class C : public B {};

class activeX {
public:
  virtual void f(const A&) const = 0;
  virtual void f(const B&) const = 0;
};

class activeY : public activeX {
public:
  activeY() {}

  virtual void f(const A&) const {
    std::cout << "activeY::f(const A&)" << std::endl;
  }
  virtual void f(const B&) const {
    std::cout << "activeY::f(const B&)" << std::endl;
  }
};


void f(A*) {
  std::cout << "f(A*)" << std::endl;
}

void f(B*) {
  std::cout << "f(B*)" << std::endl;
}

// We leave out the subsubclass overloads, see explanation above.

void f(const A&) {
  std::cout << "f(const A&)" << std::endl;
}

void f(const B&) {
  std::cout << "f(const B&)" << std::endl;
}


int main() {
  std::cout << "These all work as expected, since the static and dynamic types match up:" << std::endl;

  activeY y;

  A* a = new A;
  B* b = new B;
  C* c = new C;

  f(a);
  f(b);
  f(c);

  f(*a);
  f(*b);
  f(*c);

  std::cout << "... but these don't:" << std::endl;

  A* bA = new B;
  A* cA = new C;
  B* cB = new C;

  std::cout << "... here we'd like to see a call to f(B*):" << std::endl;
  f(bA);
  std::cout << "... here we'd like to see a call to f(C*):" << std::endl;
  f(cA);
  std::cout << "... and here again to f(C*):" << std::endl;
  f(cB);

  std::cout << "... here to f(const B&):" << std::endl;
  f(*bA);
  std::cout << "... here to f(const C&):" << std::endl;
  f(*cA);
  std::cout << "... and here to f(const C&):" << std::endl;
  f(*cB);

  y.f(*a);
  y.f(*b);
  y.f(*c);
  y.f(*bA);
  y.f(*cA);
  y.f(*cB);

  /*
   * This is all not going as expected... in particular I was expecting the *cB
   * call to go to activeY::f(const A&).
   *
   * BUT never mind, turns out it was just a wrong print in the AGC operator()..
   * it was printing that it was GC instead of AGC. Oops.
   */
}