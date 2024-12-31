/* An efficient implementation of the adler32 checksum algorithm.

   Scalar version courtesy of
   http://stackoverflow.com/questions/421419/good-choice-for-a-lightweight-checksum-algorithm

   WARNING: adler32 is wickedly fast, but has several significant
   weaknesses [1]. Perhaps the most troubling one for our purposes is
   the fact that it performs poorly for small inputs (where "small" is
   sub-kB range).

   [1] http://guru.multimedia.cx/crc32-vs-adler32/
 */

#include "adler.h"

#include "sm-defs.h"
#include "sm-exceptions.h"

struct adler32_nop_op {
  template <typename T>
  void operator()(T) {}
};

struct adler32_memcpy_op {
  char *_dest;
  adler32_memcpy_op(char *dest, char const *src) : _dest(dest) {
    int dalign = 0xf & (uintptr_t)dest;
    int salign = 0xf & (uintptr_t)src;
    THROW_IF(dalign != salign, illegal_argument,
             "Incompatible relative alignment between src and dest buffers (%d "
             "vs %d)",
             salign, dalign);
  }

  template <typename T>
  void operator()(T data) {
    *(T *)_dest = data;
    _dest += sizeof(T);
  }
};

static uint64_t const MOD_ADLER = 65521;

template <typename Op>
void adler32_single(uint64_t &a, uint64_t &b, char const *data, Op &op) {
  op(*data);
  a += (uint8_t)*data;
  b += a;
}

template <typename Op>
uint32_t 
#ifndef __clang__
__attribute__((optimize("unroll-loops")))
#endif
adler32_finish(uint64_t a, uint64_t b, char const *data, size_t i,
               size_t nbytes, Op &op) {
#ifdef __clang__
#pragma clang loop unroll(enable)
#endif
  for (; i < nbytes; i++) adler32_single(a, b, data + i, op);

  a %= MOD_ADLER;
  b %= MOD_ADLER;
  return (b << 16) | a;
}

uint32_t adler32_merge(uint32_t left, uint32_t right, size_t right_size) {
  uint64_t a = left & 0xffff;
  uint64_t b = left >> 16;
  uint64_t d1 = right & 0xffff;
  uint64_t d2 = right >> 16;
  adler32_nop_op op;

  /* Gotcha: if two sums were computed independently, the one on the
     right wrongly included an initial value of a=1 (rather than the
     true [a] we're now inheriting from the one on the left).
   */
  a += MOD_ADLER - 1;
  b += right_size * a + d2;
  a += d1;
  return adler32_finish(a, b, 0, 0, 0, op);
}

template <typename Op>
uint32_t
#ifndef __clang__
__attribute__((optimize("unroll-loops")))
#endif
adler32_vanilla(char const *data, size_t nbytes, uint32_t sofar, Op &op) {
  return adler32_finish(sofar & 0xffff, sofar >> 16, data, 0, nbytes, op);
}

uint32_t __attribute__((flatten))
adler32_vanilla(char const *data, size_t nbytes, uint32_t sofar) {
  adler32_nop_op op;
  return adler32_vanilla(data, nbytes, sofar, op);
}

uint32_t __attribute__((flatten))
adler32_memcpy_vanilla(char *dest, char const *src, size_t nbytes,
                       uint32_t sofar) {
  adler32_memcpy_op op(dest, src);
  return adler32_vanilla(src, nbytes, sofar, op);
}

#warning SSSE3 not available, falling back to vanilla implementation
uint32_t adler32(char const *data, size_t nbytes, uint32_t sofar) {
  return adler32_vanilla(data, nbytes, sofar);
}
uint32_t adler32_memcpy(char *dest, char const *src, size_t nbytes,
                        uint32_t sofar) {
  return adler32_memcpy_vanilla(dest, src, nbytes, sofar);
}
