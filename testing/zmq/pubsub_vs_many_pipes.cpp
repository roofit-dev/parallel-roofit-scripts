#include <chrono>
#include <unistd.h> // fork, usleep
#include <iostream>

#include "zmq.hxx"

// for wait_for_child:
#include <csignal> // kill, SIGKILL
#include <iostream> // cerr, and indirectly WNOHANG, EINTR, W* macros
#include <stdexcept> // runtime_error
#include <sys/wait.h>  // waitpid
#include <string>   // to_string
#include <tuple>    // tuple, tie
#include <sstream>  // stringstream
#include <vector>

auto get_time = [](){return std::chrono::duration_cast<std::chrono::nanoseconds>(std::chrono::high_resolution_clock::now().time_since_epoch()).count();};

// copy pasted stuff from RooFitZMQ

int wait_for_child(pid_t child_pid, bool may_throw, int retries_before_killing, int wait_usec = 0) {
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

std::string decode(const zmq::message_t& msg) {
  std::string r(msg.size() + 1, char{});
  r.assign(static_cast<const char*>(msg.data()), msg.size());
  return r;
}

std::string receive(zmq::socket_t& socket, bool* more = nullptr) {
  // receive message
  zmq::message_t msg;
  auto nbytes = socket.recv(&msg);
  if (0 == nbytes) {
    std::cerr << "NULL BYTES NOOOES\n";
    exit(1);
  }
  if (more) *more = msg.more();

  // decode message
  return decode(msg);
}


// END of copy pasted stuff from RooFitZMQ

void bind_socket(zmq::socket_t& socket, const char * address) {
  while (true) {
    try {
      socket.bind(address);
      break;
    } catch (zmq::error_t &e) {
      if (e.num() == EADDRINUSE) {
        std::cout << e.what() << ", retrying in 1 second\n";
        sleep(1);
        continue;
      } else {
        throw e;
      }
    }
  }
}

// from https://stackoverflow.com/a/16606128/1199693
template <typename T>
std::string to_string_with_precision(const T a_value, const int n = 6) {
  std::ostringstream out;
  out.precision(n);
  out << std::fixed << a_value;
  return out.str();
}


template <typename T>
T from_string(const std::string s) {
  std::stringstream out;
  out << s;
  T value;
  out >> value;
  return value;
}


template <int iterations = 400>
std::tuple<double, double, double, double> pub_sub(int N_children, bool verbose) {
  std::vector<pid_t> child_pids(N_children);
  pid_t this_child_pid {0};
  for (int i = 0; i < N_children; ++i) {
    this_child_pid = 0;
    do {
      this_child_pid = fork();
    } while (this_child_pid == -1);  // retry if fork fails
    if (this_child_pid == 0) {
      // don't continue creating children on child processes
      break;
    } else {
      child_pids[i] = this_child_pid;
    }
  }

  if (this_child_pid > 0) { // parent
    zmq::context_t context {};
    zmq::socket_t publisher {context, zmq::socket_type::pub};

    bind_socket(publisher, "tcp://*:5555");

    // wait with sending until all subscribers are connected
    zmq::socket_t subscribers_syncer {context, zmq::socket_type::pull};
    bind_socket(subscribers_syncer, "tcp://*:5556");

    int countdown = N_children;
    while (countdown > 0) {
      receive(subscribers_syncer);
      --countdown;
    }

    decltype(get_time()) t1, t2;

    t1 = get_time();
    for (int i = 0; i < iterations; ++i) {
      publisher.send({"extra,extra", 11});
    }
    t2 = get_time();

    double parent_time = (t2 - t1)/1.e9;
    if (verbose) std::cout << "pub_sub PARENT took " << parent_time << " seconds\n";

    // again wait for all children to be finished before killing them off
    countdown = N_children;
    std::vector<double> initial_times(N_children), rest_times(N_children), mean_times(N_children);
    while (countdown-- > 0) {
      initial_times[countdown] = from_string<double>(receive(subscribers_syncer));
      rest_times[countdown] = from_string<double>(receive(subscribers_syncer));
      mean_times[countdown] = from_string<double>(receive(subscribers_syncer));
    }

    // averages
    double initial_time {0}, rest_time {0}, mean_time {0};
    for (int i = 0; i < N_children; ++i) {
      initial_time += initial_times[i];
      rest_time += rest_times[i];
      mean_time += mean_times[i];
    }
    initial_time /= N_children;
    rest_time /= N_children;
    mean_time /= N_children;

    if (verbose) std::cout << "pub_sub " << N_children << " CHILDREN took on average " << rest_time << " seconds (plus " << initial_time << " seconds on the first receive, " << mean_time << " seconds average per receive)\n";

    for (int i = 0; i < N_children; ++i) {
      wait_for_child(child_pids[i], true, 5, 500);
    }

    return {parent_time, initial_time, rest_time, mean_time};
  } else { // child
    zmq::context_t context {};
    zmq::socket_t subscriber {context, zmq::socket_type::sub};
    subscriber.setsockopt(ZMQ_SUBSCRIBE, "", 0);

    subscriber.connect("tcp://127.0.0.1:5555");

    // announce to the parent that we're subscribed
    zmq::socket_t announcer {context, zmq::socket_type::push};
    announcer.connect("tcp://127.0.0.1:5556");
    zmq::message_t message {"", 0};
    announcer.send(message);

    int received = 0;

    std::vector<decltype(get_time())> t1(iterations), t2(iterations);

    for (int i = 0; i < iterations; ++i) {
      t1[i] = get_time();
      auto s = receive(subscriber);
      // note that this check has negligible cost, try commenting it out if you don't believe me ;)
      if (s != "extra,extra") {
        std::cerr << "ohnoes, it's " << s << "\n";
      } else {
        ++received;
      }
      t2[i] = get_time();
    }

    double initial_time = (t2[0] - t1[0]) / 1.e9;
    double rest_time = (t2[iterations-1] - t1[1]) / 1.e9;
    double mean_time = rest_time/(iterations-1);

    auto s = to_string_with_precision(initial_time, 10);
    announcer.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(rest_time, 10);
    announcer.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(mean_time, 10);
    announcer.send({s.c_str(), s.length()});

    // note: closing the sockets is apparently still necessary here!
    // well, not strictly necessary, but otherwise the program will hang
    // too long and it has to be sent a SIGKILL, if you close them manually
    // instead of relying on some magic in the context, it exits cleanly.
    announcer.close();
    subscriber.close();
    // and finally close the context as well
    context.close();
    _Exit(0);
  }
}


int main(int argc, char const *argv[]) {
  int repeats = 50;
  std::vector<std::tuple<double, double, double, double>> pub_sub_results (repeats);

//  for (std::size_t children = 1; children <= 8; ++children) {
  for (std::size_t children = 8; children >= 1; --children) {
    for (int i = 0; i < repeats; ++i) {
      pub_sub_results[i] = pub_sub<100>(children, false);
    }

    double parent = 0, init = 0, rest = 0, mean = 0;
    for (int i = 0; i < repeats; ++i) {
      parent += std::get<0>(pub_sub_results[i]);
      init += std::get<1>(pub_sub_results[i]);
      rest += std::get<2>(pub_sub_results[i]);
      mean += std::get<3>(pub_sub_results[i]);
    }
    parent /= repeats;
    init /= repeats;
    rest /= repeats;
    mean /= repeats;

    std::cout << "-- mean over " << repeats << " repeats:\n"
              << "PARENT: " << parent << "\n"
              << children << " CHILDREN: " << rest << " (plus initial " << init << "); mean per receive: " << mean << "\n";
  }

//  t1 = get_time();
//  for (int i = 0; i < repeats; ++i) {
//    many_pipes();
//  }
//  t2 = get_time();
//
//  std::cout << "many pipes, t1 = " << t1 << " t2 = " << t2 << "\n";

}
