/*
 * zmq_testing
 * Copyright (c) 2019, Patrick Bos
 * Distributed under the terms of the BSD 3-Clause License.
 *
 * The full license is in the file LICENSE, distributed with this software.
 */

#include "zmq.hxx"
#include <unistd.h>  // fork
#include "utils.hpp"

// like added test in TestZMQ.java in https://github.com/zeromq/jeromq/pull/142/files
int main(int argc, char const *argv[]) {
  zmq::context_t context;

  zmq::socket_t socket1{context, zmq::socket_type::req};
  zmq::socket_t socket2{context, zmq::socket_type::req};
  socket1.bind("tcp://*:63343");
  try {
    socket2.bind("tcp://*:63343");
  } catch (const zmq::error_t & e) {
    if (e.num() == EADDRINUSE) {
      std::cout << "success: address in use, as it should be" << std::endl;
    } else {
      throw e;
    }
  }
  socket1.close();
  socket2.close();

  // now try doing this from multiple processes and see how that works out
  pid_t child_pid = 0;
  do {
    child_pid = fork();
  } while (child_pid == -1);  // retry if fork fails
  if (child_pid > 0) {  // parent
    zmq::socket_t socket3{context, zmq::socket_type::req};
//    sleep(1);
    try {
      socket3.bind("tcp://*:63344");
    } catch (const zmq::error_t & e) {
      if (e.num() == EADDRINUSE) {
        std::cout << "address in use on parent" << std::endl;
      } else {
        throw e;
      }
    }
//    sleep(1);
    wait_for_child(child_pid, true, 5, 500);
  } else {              // child
    zmq::socket_t socket3{context, zmq::socket_type::req};
    try {
      socket3.bind("tcp://*:63344");
    } catch (const zmq::error_t & e) {
      if (e.num() == EADDRINUSE) {
        std::cout << "address in use on child" << std::endl;
      } else {
        throw e;
      }
    }
  }
}