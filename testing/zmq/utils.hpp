/*
 * zmq_testing
 * Copyright (c) 2019, Patrick Bos
 * Distributed under the terms of the BSD 3-Clause License.
 *
 * The full license is in the file LICENSE, distributed with this software.
 */

#ifndef ZMQ_TESTING_UTILS_HPP
#define ZMQ_TESTING_UTILS_HPP

// copy pasted stuff from RooFitZMQ

int wait_for_child(pid_t child_pid, bool may_throw, int retries_before_killing, int wait_usec = 0);

#endif //ZMQ_TESTING_UTILS_HPP
