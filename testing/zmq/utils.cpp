/*
 * zmq_testing
 * Copyright (c) 2019, Patrick Bos
 * Distributed under the terms of the BSD 3-Clause License.
 *
 * The full license is in the file LICENSE, distributed with this software.
 */

// copy pasted stuff from RooFitZMQ

// for wait_for_child:
#include <unistd.h> // usleep
#include <csignal> // kill, SIGKILL
#include <iostream> // cerr, and indirectly WNOHANG, EINTR, W* macros
#include <stdexcept> // runtime_error
#include <sys/wait.h>  // waitpid
#include <string>   // to_string

int wait_for_child(pid_t child_pid, bool may_throw, int retries_before_killing, int wait_usec) {
  int status = 0;
  int patience = retries_before_killing;
  pid_t tmp;
  do {
    if (patience-- < 1) {
      ::kill(child_pid, SIGKILL);
    }
    tmp = waitpid(child_pid, &status, WNOHANG);
    usleep(wait_usec);
  } while (
      tmp == 0 // child has not yet changed state, try again
      || (-1 == tmp && EINTR == errno) // retry on interrupted system call
      );

  if (patience < 1) {
    std::cerr << "Had to send PID " << child_pid << " " << (-patience+1) << " SIGKILLs\n";
  }

  if (0 != status) {
    if (WIFEXITED(status)) {
      printf("exited, status=%d\n", WEXITSTATUS(status));
    } else if (WIFSIGNALED(status)) {
      printf("killed by signal %d\n", WTERMSIG(status));
    } else if (WIFSTOPPED(status)) {
      printf("stopped by signal %d\n", WSTOPSIG(status));
    } else if (WIFCONTINUED(status)) {
      printf("continued\n");
    }
  }

  if (-1 == tmp && may_throw) throw std::runtime_error(std::string("waitpid, errno ") + std::to_string(errno));

  return status;
}
