/*
* @Author: pbos
* @Date:   2018-07-30 08:35:09
* @Last Modified by:   pbos
* @Last Modified time: 2018-07-30 08:51:46
*/

// Compile as
// clang++ --std=c++11 pointer_member_initialization_mysterious_null.cpp -o pointer_member_initialization_mysterious_null.x

#include <iostream>

struct Guy {
  Guy() {
    std::cout << "this Guy: " << this << std::endl;
  }
};

struct Daughter {
  Guy* partner;

  explicit Daughter(Guy * the_partner): partner(the_partner) {
    std::cout << "this Daugther: " << this << " and her partner: " << partner << " (input as " << the_partner << ")" << std::endl;
  }
};

class Mom {
  Guy johnny;
  Daughter grace;

public:
  Mom() : johnny(), grace(&johnny) {
    std::cout << "Mom's Daugther: " << &grace << " and some Guy johnny: " << &johnny << std::endl;
  }
};

int main() {
  // in the case this is based on (see Zim notes 30 July 2018 and week before),
  // the Guy johnny gets created in the initialization list, the pointer is
  // passed correctly to Daughter grace, but grace's Guy partner is NULL inside
  // the Daughter ctor and only turns into johnny's pointer after exiting the
  // grace ctor... why?!
  Mom bethany;

  // in this case apparently everything goes well
}
