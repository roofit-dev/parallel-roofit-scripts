#include <memory>
#include <iostream>

struct A {
    int stuff = 42;
};

int main(int argc, char const *argv[])
{
    A* a_raw = new A;
    std::shared_ptr<A> a(std::shared_ptr<A>(nullptr), a_raw);

    std::cout << "bool: " << (bool)a << std::endl;
    std::cout << "use_count: " << a.use_count() << std::endl;
    std::cout << "get: " << a.get() << std::endl;

    std::shared_ptr<A> a_copy(a);

    std::cout << "bool: " << (bool)a_copy << std::endl;
    std::cout << "use_count: " << a_copy.use_count() << std::endl;
    std::cout << "get: " << a_copy.get() << std::endl;

    return 0;
}
