#include <unistd.h> // pid stuff, pipe, fork
#include <cerrno>  // errno
#include <csignal> // kill, SIG*
#include <cstdio>  // printf
#include <cstring> // strlen
#include <cstdlib> // malloc

// build with clang++ --std=c++11 fork_pipe_illegal_instruction.cpp -o fork_pipe_illegal_instruction.x
// run in lldb/gdb to catch the SIGTRAP

int main() {
  pid_t parentpid = getpid();
  pid_t mypid = parentpid;

  int fds[2];
  if (::pipe(&fds[0]) != 0) {
    printf("pipe error!");
    _exit(errno);
  }

  size_t len = 28;

  // TEST 1: write from child, read at parent

  pid_t childpid = ::fork();

  if (childpid == 0) {  // child
    // ignore SIGTRAP to really emulate debugger conditions
    signal(SIGTRAP, SIG_IGN);
    // then trigger it to see what happens when the child also has a breakpoint
    kill(childpid, SIGTRAP);
    // it should just continue
    mypid = childpid;
    sleep(1); // wait for parent to suspend itself
    const char *buf = "hi parent, it's me, your child!";
    printf("%s\n", buf);
    write(fds[1], reinterpret_cast<const void *>(buf), len);
    _exit(0);
  } else {              // parent
    kill(parentpid, SIGTRAP);  // suspend the parent, i.e. "trigger breakpoint"
    char *buf = reinterpret_cast<char *>(malloc(len));
    read(fds[0], buf, len);
    printf("heard my child say: \"%s\"\n", buf);
    // while(true) {}
  }

  // TEST 2: read from child, write at parent

  childpid = ::fork();

  if (childpid == 0) {  // child
    // ignore SIGTRAP to really emulate debugger conditions
    signal(SIGTRAP, SIG_IGN);
    // then trigger it to see what happens when the child also has a breakpoint
    kill(childpid, SIGTRAP);
    // it should just continue
    mypid = childpid;
    sleep(1); // wait for parent to suspend itself
    char *buf = reinterpret_cast<char *>(malloc(len));
    read(fds[0], buf, len);
    printf("heard my parent say: \"%s\"\n", buf);
    _exit(0);
  } else {              // parent
    kill(parentpid, SIGTRAP);  // suspend the parent, i.e. "trigger breakpoint"
    const char *buf = "hello child, how fareth thee?";
    printf("%s\n", buf);
    write(fds[1], reinterpret_cast<const void *>(buf), len);
    // while(true) {}
  }

}