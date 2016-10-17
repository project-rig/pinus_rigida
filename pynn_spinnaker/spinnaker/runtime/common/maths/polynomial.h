#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../arm_intrinsics.h"

// Namespaces
using namespace Common::ARMIntrinsics;

/*! \file
 *
 *  \brief Fast polynomial evaluation, using ARM DSP instructions.
 *
 *    Each function takes three arguments: the polynomial coefficients,
 *    the point at which we are evaluating the polynomial, and the order
 *    of the polynomial.
 *
 *    Assume that we have (note the "reverse order"):
 *
 *       int a [] = { a_4, a_3, a_2, a_1, a_0 };
 *
 *    This represents the function:
 *
 *       a_0 + x * (a_1 + x * (a_2 + x * (a_3 + x * a_4)))
 *
 *    To use the fast DSP instructions we use an "odd" representation
 *    of x: s0.16. If we are using the usual s0.15 fract type, then
 *    we are restricted to x lying in the range [0.5, 0.5).
 *
 *    In the above example (because we have a quartic polynomial) n = 4.
 *
 *    The other point to note is that the addition in the evaluation
 *    may overflow. In the code that follows, we use the Q-bit to
 *    detect if this has happened. One sure-fire case in which there
 *    is no overflow is if the polynomial is alternating.
 *
 *  \author Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  \copyright
 *    Copyright (c) Dave Lester and The University of Manchester, 2014.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  \date 13 December, 2014
 *
 *  DETAILS
 *    Created on       : 13 December 2014
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#define assert(X)

//-----------------------------------------------------------------------------
// Common::Maths
//-----------------------------------------------------------------------------
namespace Common
{
namespace Maths
{
//! \brief Horner evaluation of a polynomial of signed accum at
//! a point given by the lower (signed) 16-bits of x.
//! \param[in] a The 32-bit signed polynomial coefficients. These can
//! be treated as either accum or long fract (or any other signed 32-bit
//! quantity).
//! \param[in] x The point at which the polynomial is to be evaluated
//! is given by treating the lower 16-bits of the argument as s0.16.
//! Note this is not a fract (s0.15), thus, if we are using a fract here,
//! we must treat the fract value of -1.0 as if it were only -0.5.
//! \param[in] n The number of coeficients in the polynomial.
//! \return The result as a signed 32-bit quantity.
inline int HornerIntB(const int *a, int x, int n)
{
    register int r = *a++;

    assert (!__reset_and_saturation_occurred ());

    for ( ; n > 0; n--)
    {
      r = __smlawb (r, x, *a++);
    }

    assert (!__saturation_occurred ());

    return r;
}

//! \brief Horner evaluation of a polynomial of signed accum at
//! a point given by the upper (signed) 16-bits of x.
//! \param[in] a The 32-bit signed polynomial coefficients. These can
//! be treated as either accum or long fract (or any other signed 32-bit
//! quantity.
//! \param[in] x The point at which the polynomial is to be evaluated
//! is given by treating the upper 16-bits of the argument as s0.16.
//! Note this is not a fract (s0.15), thus, if we are using a fract here,
//! we must treat the fract value of -1.0 as if it were only -0.5.
//! \param[in] n The number of coeficients in the polynomial.
//! \return The result as a signed 32-bit quantity.
inline int HornerIntT (const int *a, int x, int n)
{
  register int r = *a++;

  assert (!__reset_and_saturation_occurred ());

  for ( ; n > 0; n--)
  {
    r = __smlawt (r, x, *a++);
  }

  assert (!__saturation_occurred ());

  return r;
}
} // Maths
} // Common