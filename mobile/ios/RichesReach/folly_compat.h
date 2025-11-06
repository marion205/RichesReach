// Compatibility header for RCT-Folly C++17 deprecated features
// This file provides compatibility shims for deprecated C++ standard library features

#ifndef FOLLY_COMPAT_H
#define FOLLY_COMPAT_H

#include <functional>
#include <memory>

// Compatibility shims for deprecated std::unary_function and std::binary_function
#if __cplusplus >= 201703L
namespace std {
  // Forward declarations for deprecated function objects
  template<class Arg, class Result>
  struct unary_function {
    typedef Arg argument_type;
    typedef Result result_type;
  };

  template<class Arg1, class Arg2, class Result>
  struct binary_function {
    typedef Arg1 first_argument_type;
    typedef Arg2 second_argument_type;
    typedef Result result_type;
  };
}

// Compatibility for std::auto_ptr (deprecated in C++17)
namespace std {
  template<class T>
  class auto_ptr {
  private:
    T* ptr;
  public:
    explicit auto_ptr(T* p = 0) : ptr(p) {}
    ~auto_ptr() { delete ptr; }
    auto_ptr(const auto_ptr& other) : ptr(other.release()) {}
    auto_ptr& operator=(const auto_ptr& other) {
      if (this != &other) {
        delete ptr;
        ptr = other.release();
      }
      return *this;
    }
    T& operator*() const { return *ptr; }
    T* operator->() const { return ptr; }
    T* get() const { return ptr; }
    T* release() {
      T* tmp = ptr;
      ptr = 0;
      return tmp;
    }
    void reset(T* p = 0) {
      if (ptr != p) {
        delete ptr;
        ptr = p;
      }
    }
  };
}
#endif

#endif // FOLLY_COMPAT_H

