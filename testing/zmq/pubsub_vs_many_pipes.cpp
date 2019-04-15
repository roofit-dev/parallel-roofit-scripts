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

class receive_exception : public std::exception {
 public:
  receive_exception(int attempts) : attempts(attempts) {}
  const char * what () const throw () {
    std::stringstream ss;
    ss << "receive failed after " << attempts << " attempts\n";
    return ss.str().c_str();
  }
 private:
  int attempts;
};


std::string receive(zmq::socket_t& socket, bool* more = nullptr, int tries = 1) {
  // receive message
  zmq::message_t msg;
  int attempts = 0;
  bool done;
  do {
    done = socket.recv(&msg);
  } while (!done && ++attempts < tries);

  if (!done && attempts == tries) {
    throw receive_exception(attempts);
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


template <int stop_pubs=5>
std::tuple<double, double, double, double> pub_sub(int N_children, int iterations, bool verbose) {
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
//    bind_socket(publisher, "tcp://*:5555");
    bind_socket(publisher, "ipc:///tmp/zmq_socket_tests_publisher.ipc");

    zmq::socket_t subscribers_syncer {context, zmq::socket_type::pull};
//    bind_socket(subscribers_syncer, "tcp://*:5556");
    bind_socket(subscribers_syncer, "ipc:///tmp/zmq_socket_tests_subscriber.ipc");

    // wait with sending until all subscribers are connected
    int countdown = N_children;
    while (countdown > 0) {
      try {
        receive(subscribers_syncer);
      } catch (const receive_exception& e) {
        continue;
      }
      --countdown;
    }

    decltype(get_time()) t1, t2;

    t1 = get_time();
    for (int i = 0; i < iterations; ++i) {
      // Our protocol: multi-part messages, first part is a follow number (i
      // here) and second part is the actual message; at the end a few -1's
      // with empty messages are sent as signals for the subscribers to stop
      // listening.
      auto follow = to_string_with_precision(i);
      publisher.send({follow.c_str(), follow.size()}, ZMQ_SNDMORE);
      publisher.send({"extra,extra", 11});
    }
    for (int i = 0; i < stop_pubs; ++i) {
      auto follow = to_string_with_precision(-1);
      publisher.send({follow.c_str(), follow.size()}, ZMQ_SNDMORE);
      publisher.send({"", 0});
    }
    t2 = get_time();

    double parent_time = (t2 - t1)/1.e9;
    if (verbose) std::cout << "pub_sub PARENT took " << parent_time << " seconds\n";

    // again wait for all children to be finished before killing them off
    countdown = N_children;
    std::vector<double> initial_times(N_children), rest_times(N_children), mean_times(N_children);
    if (verbose) std::cerr << "receive timings\n";

    while (countdown-- > 0) {
      if (verbose) std::cerr << "tick.";
      initial_times[countdown] = from_string<double>(receive(subscribers_syncer));
      if (verbose) std::cerr << ".";
      rest_times[countdown] = from_string<double>(receive(subscribers_syncer));
      if (verbose) std::cerr << ".";
      mean_times[countdown] = from_string<double>(receive(subscribers_syncer));
      if (verbose) std::cerr << "tock\n";
    }
    if (verbose) std::cerr << "received timings\n";

    // averages
    double initial_time {0}, rest_time {0}, mean_time {0};
    int N_successful = 0;
    for (int i = 0; i < N_children; ++i) {
      if (initial_times[i] != -1) {  // don't count failed runs
        initial_time += initial_times[i];
        rest_time += rest_times[i];
        mean_time += mean_times[i];
        ++N_successful;
      }
    }
    if (N_successful == 0) {
      initial_time = -1;
      rest_time = -1;
      mean_time = -1;
    } else {
      initial_time /= N_successful;
      rest_time /= N_successful;
      mean_time /= N_successful;
    }

    if (verbose) std::cout << "pub_sub " << N_children << " CHILDREN (of which " << N_successful << " ran successfully) took on average " << rest_time << " seconds (plus " << initial_time << " seconds on the first receive, " << mean_time << " seconds average per receive)\n";

    // close things manually here as well to make sure we don't prematurely kill the children
    subscribers_syncer.setsockopt(ZMQ_LINGER, 0);
    subscribers_syncer.close();
    publisher.setsockopt(ZMQ_LINGER, 0);
    publisher.close();
    context.close();

    for (int i = 0; i < N_children; ++i) {
      wait_for_child(child_pids[i], true, 5, 500);
    }

    return {parent_time, initial_time, rest_time, mean_time};


    // end of parent


  } else { // child


    zmq::context_t context {};

    zmq::socket_t subscriber {context, zmq::socket_type::sub};
    subscriber.setsockopt(ZMQ_SUBSCRIBE, "", 0);
    int timeout = 1000;  // milliseconds
    subscriber.setsockopt(ZMQ_RCVTIMEO, &timeout, sizeof(timeout));
//    subscriber.connect("tcp://127.0.0.1:5555");
    subscriber.connect("ipc:///tmp/zmq_socket_tests_publisher.ipc");

    // announce to the parent that we're subscribed
    zmq::socket_t announcer {context, zmq::socket_type::push};
//    announcer.connect("tcp://127.0.0.1:5556");
    announcer.connect("ipc:///tmp/zmq_socket_tests_subscriber.ipc");
    zmq::message_t message {"", 0};
    announcer.send(message);

    // and go!
    int received = 0;

    std::vector<decltype(get_time())> t1, t2;
    t1.reserve(iterations);
    t2.reserve(iterations);

    bool failed = false;
    for (int i = 0; i < iterations; ++i) {
      t1.push_back(get_time());
      // Our protocol: multi-part messages, first part is a follow number (i
      // here) and second part is the actual message; at the end a few -1's
      // with empty messages are sent as signals for the subscribers to stop
      // listening.
      int follow;
      try {
        follow = std::stoi(receive(subscriber));
      } catch (const receive_exception& e) {
        std::cerr << "child PID " << getpid() << " stopped after receiving " << received << " messages, missed " << iterations - received << "!\n";
        failed = true;
        break;
      }
      if (follow == -1) {
        std::cerr << "child PID " << getpid() << " stopped after receiving " << received << " messages, missed " << iterations - received << "!\n";
        failed = true;
        break;
      }
      std::string s;
      try {
        s = receive(subscriber);
      } catch (const receive_exception& e) {
        std::cerr << "child PID " << getpid() << " stopped after receiving " << received << " and a half (the follow number) messages, missed " << iterations - received << "!\n";
        failed = true;
        break;
      }
      // note that this check has negligible cost, try commenting it out if you don't believe me ;)
      if (s != "extra,extra") {
        if (verbose) std::cerr << "ohnoes, it's " << s << "\n";
      } else {
        ++received;
      }
      t2.push_back(get_time());
    }

    double initial_time, rest_time, mean_time;
    if (!failed) {
      initial_time = (t2[0] - t1[0]) / 1.e9;
      rest_time = (t2[t2.size() - 1] - t1[1]) / 1.e9;
      mean_time = rest_time/(t2.size() - 1);
    } else {
      initial_time = -1.;
      rest_time = -1.;
      mean_time = -1.;
    }

    auto s = to_string_with_precision(initial_time, 10);
    if (verbose) std::cerr << "first send PID " << getpid() << "\n";
    announcer.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(rest_time, 10);
    if (verbose) std::cerr << "second send PID " << getpid() << "\n";
    announcer.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(mean_time, 10);
    if (verbose) std::cerr << "third send PID " << getpid() << "\n";
    announcer.send({s.c_str(), s.length()});
    if (verbose) std::cerr << "done sending PID " << getpid() << "\n";

    // note: closing the sockets is apparently still necessary here!
    // well, not strictly necessary, but otherwise the program will hang
    // too long and it has to be sent a SIGKILL, if you close them manually
    // instead of relying on some magic in the context, it exits cleanly.
    announcer.setsockopt(ZMQ_LINGER, 0);
    announcer.close();
    subscriber.setsockopt(ZMQ_LINGER, 0);
    subscriber.close();
    // and finally close the context as well
    context.close();
    _Exit(0);
  }
}



template <int stop_pubs=5>
std::tuple<double, double, double, double> many_pipes(int N_children, int iterations, bool verbose) {
  std::vector<pid_t> child_pids(N_children);
  pid_t this_child_pid {0};
  int child_id = -1;  // parent
  for (int child = 0; child < N_children; ++child) {
    this_child_pid = 0;
    do {
      this_child_pid = fork();
    } while (this_child_pid == -1);  // retry if fork fails
    if (this_child_pid == 0) {
      child_id = child;
      // don't continue creating children on child processes
      break;
    } else {
      child_pids[child] = this_child_pid;
    }
  }

  if (this_child_pid > 0) { // parent
    zmq::context_t context {};
    std::vector<zmq::socket_t> sockets;
    for (int child = 0; child < N_children; ++child) {
      sockets.emplace_back(context, zmq::socket_type::pair);
      std::stringstream address;
//      address << "tcp://*:" << (5555 + child);
      address << "ipc:///tmp/zmq_socket_tests_" << child << ".ipc";
      bind_socket(sockets.back(), address.str().c_str());
    }

    decltype(get_time()) t1, t2;

    t1 = get_time();
    for (int i = 0; i < iterations; ++i) {
      for (int child = 0; child < N_children; ++child) {
        sockets[child].send({"extra,extra", 11});
      }
    }
    t2 = get_time();

    double parent_time = (t2 - t1)/1.e9;
    if (verbose) std::cout << "many_pairs PARENT took " << parent_time << " seconds\n";

    // again wait for all children to be finished before killing them off
    std::vector<double> initial_times(N_children), rest_times(N_children), mean_times(N_children);
    if (verbose) std::cerr << "receive timings\n";

    for (int child = 0; child < N_children; ++child) {
      if (verbose) std::cerr << "tick.";
      initial_times[child] = from_string<double>(receive(sockets[child]));
      if (verbose) std::cerr << ".";
      rest_times[child] = from_string<double>(receive(sockets[child]));
      if (verbose) std::cerr << ".";
      mean_times[child] = from_string<double>(receive(sockets[child]));
      if (verbose) std::cerr << "tock\n";
    }
    if (verbose) std::cerr << "received timings\n";

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

    if (verbose) std::cout << "many_pipes " << N_children << " CHILDREN took on average " << rest_time << " seconds (plus " << initial_time << " seconds on the first receive, " << mean_time << " seconds average per receive)\n";

    // close things manually here as well to make sure we don't prematurely kill the children
    for (int child = 0; child < N_children; ++child) {
      sockets[child].setsockopt(ZMQ_LINGER, 0);
      sockets[child].close();
    }
    context.close();

    for (int child = 0; child < N_children; ++child) {
      wait_for_child(child_pids[child], true, 5, 500);
    }

    return {parent_time, initial_time, rest_time, mean_time};


    // end of parent


  } else { // child


    zmq::context_t context {};

    zmq::socket_t socket {context, zmq::socket_type::pair};
    std::stringstream address;
//    address << "tcp://127.0.0.1:" << (5555 + child_id);
    address << "ipc:///tmp/zmq_socket_tests_" << child_id << ".ipc";
    socket.connect(address.str());

    // and go!
    int received = 0;

    std::vector<decltype(get_time())> t1, t2;
    t1.reserve(iterations);
    t2.reserve(iterations);

    for (int i = 0; i < iterations; ++i) {
      t1.push_back(get_time());
      std::string s;
      try {
        s = receive(socket);
      } catch (const receive_exception& e) {
        std::cerr << "child PID " << getpid() << " stopped after receiving " << received << " and a half (the follow number) messages, missed " << iterations - received << "!\n";
        t2.push_back(get_time());
        break;
      }
      // note that this check has negligible cost, try commenting it out if you don't believe me ;)
      if (s != "extra,extra") {
        if (verbose) std::cerr << "ohnoes, it's " << s << "\n";
      } else {
        ++received;
      }
      t2.push_back(get_time());
    }

    double initial_time = (t2[0] - t1[0]) / 1.e9;
    double rest_time = (t2[t2.size() - 1] - t1[1]) / 1.e9;
    double mean_time = rest_time/(t2.size() - 1);

    auto s = to_string_with_precision(initial_time, 10);
    if (verbose) std::cerr << "first send PID " << getpid() << "\n";
    socket.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(rest_time, 10);
    if (verbose) std::cerr << "second send PID " << getpid() << "\n";
    socket.send({s.c_str(), s.length()}, ZMQ_SNDMORE);
    s = to_string_with_precision(mean_time, 10);
    if (verbose) std::cerr << "third send PID " << getpid() << "\n";
    socket.send({s.c_str(), s.length()});
    if (verbose) std::cerr << "done sending PID " << getpid() << "\n";

    // note: closing the sockets is apparently still necessary here!
    // well, not strictly necessary, but otherwise the program will hang
    // too long and it has to be sent a SIGKILL, if you close them manually
    // instead of relying on some magic in the context, it exits cleanly.
    socket.setsockopt(ZMQ_LINGER, 0);
    socket.close();
    // and finally close the context as well
    context.close();
    _Exit(0);
  }
}



int main(int argc, char const *argv[]) {
  int repeats = 100;
  int iterations = 1000;  // per repeat
  int max_children = 4;

  std::vector<std::tuple<double, double, double, double>> pub_sub_results(repeats);
  std::vector<std::tuple<double, double, double, double>> many_pipes_results(repeats);

  std::vector<std::tuple<double, double, double, double>> pub_sub_means;
  std::vector<std::tuple<double, double, double, double>> many_pipes_means;

  std::cout << " === PUB-SUB ===\n";

  for (std::size_t children = 1; children <= max_children; ++children) {
    for (std::size_t i = 0; i < repeats; ++i) {
      pub_sub_results[i] = pub_sub(children, iterations, false);
    }

    double parent = 0, init = 0, rest = 0, mean = 0;
    int successes = 0;
    for (int i = 0; i < repeats; ++i) {
      if (std::get<1>(pub_sub_results[i]) != -1) {
        parent += std::get<0>(pub_sub_results[i]);
        init += std::get<1>(pub_sub_results[i]);
        rest += std::get<2>(pub_sub_results[i]);
        mean += std::get<3>(pub_sub_results[i]);
        ++successes;
      }
    }
    parent /= successes;
    init /= successes;
    rest /= successes;
    mean /= successes;

    pub_sub_means.emplace_back(parent, init, rest, mean);
    std::cout << "-- mean over " << successes << " successful repeats:\n"
              << "PARENT: " << parent << "\n"
              << children << " CHILDREN: " << rest << " (plus initial " << init << " = " << (rest + init) << " total); mean per receive: " << mean
              << "\n";
  }

  std::cout << "\n === MANY PIPES ===\n";
  for (std::size_t children = 1; children <= max_children; ++children) {
    for (int i = 0; i < repeats; ++i) {
      many_pipes_results[i] = many_pipes(children, iterations, false);
    }

    double parent = 0, init = 0, rest = 0, mean = 0;
    int successes = 0;
    for (int i = 0; i < repeats; ++i) {
      if (std::get<1>(many_pipes_results[i]) != -1) {
        parent += std::get<0>(many_pipes_results[i]);
        init += std::get<1>(many_pipes_results[i]);
        rest += std::get<2>(many_pipes_results[i]);
        mean += std::get<3>(many_pipes_results[i]);
        ++successes;
      }
    }
    parent /= successes;
    init /= successes;
    rest /= successes;
    mean /= successes;

    many_pipes_means.emplace_back(parent, init, rest, mean);
    std::cout << "-- mean over " << successes << " successful repeats:\n"
              << "PARENT: " << parent << "\n"
              << children << " CHILDREN: " << rest << " (+ initial " << init << " = " << (rest + init) << " total); mean per receive: " << mean
              << "\n";
  }


  std::cout << "\n === SPEED-UP " << iterations << " send/receives: MANY-PIPES/PUB-SUB (how much faster would using PUB-SUB be compared to many pipes) ===\n";

  for (std::size_t c = 0; c < max_children; ++c) {
    double parent = std::get<0>(many_pipes_means[c])/std::get<0>(pub_sub_means[c]);
    double init = std::get<1>(many_pipes_means[c])/std::get<1>(pub_sub_means[c]);
    double rest = std::get<2>(many_pipes_means[c])/std::get<2>(pub_sub_means[c]);
    double mean = std::get<3>(many_pipes_means[c])/std::get<3>(pub_sub_means[c]);

    double total = (std::get<1>(many_pipes_means[c]) + std::get<2>(many_pipes_means[c])) /
        (std::get<1>(pub_sub_means[c]) + std::get<2>(pub_sub_means[c]));
    std::cout << "PARENT: " << parent << "\n"
              << c + 1 << " CHILDREN: " << rest << " (+ initial " << init << " = " << total << " total); mean per receive: " << mean
              << "\n";
  }
}