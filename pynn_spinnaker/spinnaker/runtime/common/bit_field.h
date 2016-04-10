/*! \file
 *
 *  \brief Bit field manipulation.
 *
 *  \details A bit field is a vector of machine words which is
 *    treated as a vector of bits.
 *
 *    For SpiNNAker each machine word is 32 bits, and so a
 *    bit_field for each neuron (assuming 256 neurons)
 *    would be 8 words long.
 *
 *    The API includes:
 *
 *     - bit_field_test (b, n)
 *         returns true of false depending on whether bit n is set or clear
 *     - bit_field_set (b, n) / bit_field_clear (b, n)
 *         used to set or clear bit n
 *     - not_bit_field (b, s)
 *         logically inverts a bit field of size s.
 *     - and_bit_field / or_bit_field
 *         logically ands/ors two bit_fields together. Requires size.
 *     - clear_bit_field/set_bit_field
 *         Initializes bit_field with all false (= clear) or true (= set).
 *         Requires size.
 *
 *    There are also support functions for:
 *
 *     - printing
 *     - randomly setting up a bit field
 *
 *  \author
 *    Dave Lester (david.r.lester@manchester.ac.uk),
 *    Jamie Knight (knightj@cs.man.ac.uk)
 *
 *  \copyright
 *    Copyright (c) Dave Lester, Jamie Knight and The University of Manchester,
 *    2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  \date 12 December, 2013
 *
 *  DETAILS
 *    Created on       : 12 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */
#pragma once

// Standard includes
#include <cstdint>

//-----------------------------------------------------------------------------
// Common::BitField
//-----------------------------------------------------------------------------
namespace Common
{
namespace BitField
{
//! \brief This function tests a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The index of the bit.
//! \return The function returns true if the bit is set or false otherwise.
inline bool TestBit(const uint32_t *b, unsigned int i)
{
  return ((b [i >> 5] & (1 << (i & 0x1F))) != 0);
}

//! \brief This function clears a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The index of the bit.
inline void ClearBit(uint32_t *b, unsigned int n)
{
  b [n >> 5] &= ~(1 << (n & 0x1F));
}

//! \brief This function sets a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The index of the bit.
inline void SetBit(uint32_t *b, unsigned int n)
{
  b [n >> 5] |= (1 << (n & 0x1F));
}

//! \brief This function negates the bits of an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
inline void Flip(uint32_t *b, unsigned int s)
{
  for ( ; s > 0; s--)
  {
    b [s-1] = ~ (b [s-1]);
  }
}

//! \brief This function ands two bit_fields together.
//! \param[in,out] b1 The sequence of words representing the first bit_field;
//! the result is returned in this parameter.
//! \param[in] b2 The sequence of words representing the second bit_field.
//! \param[in] s The size of the bit_field.
inline void And(uint32_t *b1, const uint32_t *b2, unsigned int s)
{
    for ( ; s > 0; s--)
    {
      b1 [s-1] &= b2 [s-1];
    }
}

//! \brief This function ors two bit_fields together.
//! \param[in,out] b1 The sequence of words representing the first bit_field;
//! the result is returned in this parameter.
//! \param[in] b2 The sequence of words representing the second bit_field.
//! \param[in] s The size of the bit_field.
inline void Or(uint32_t *b1, const uint32_t *b2, unsigned int s)
{
    for ( ; s > 0; s--)
    {
        b1 [s-1] |= b2 [s-1];
    }
}

//! \brief This function clears an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
inline void Clear(uint32_t *b, unsigned int s)
{
    for ( ; s > 0; s--)
    {
        b [s-1] = 0;
    }
}

//! \brief This function sets an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
inline void Set(uint32_t *b, unsigned int s)
{
    for ( ; s > 0; s--)
    {
        b [s-1] = 0xFFFFFFFF;
    }
}

//! \brief This function tests whether a bit_field is all zeros.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
//! \return The function returns true if every bit is zero, or false otherwise.
inline bool IsEmpty(const uint32_t *b, unsigned int s)
{
    bool empty = true;
Prints a bit_field as ones and zeros.
    for ( ; s > 0; s--)
    {
        empty = empty && (b [s-1] == 0);
    }

    return empty;
}

//! \brief Testing whether a bit_field is non-empty, _i.e._ if there is at
//! least one bit set.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
//! \return The function returns true if at least one bit is set; otherwise false.
inline bool IsNonEmpty(const uint32_t *b, unsigned int s)
{
    return !IsEmpty(b, s);
}

//! \brief A function that calculates the size of a bit_field to hold 'bits'
//! bits.
//! \param[in] bits The number of bits required for this bit_field.
//! \return The size (or number of words) in the bit_field.
inline unsigned int GetWordSize(unsigned int bits)
{
    // Down shift number of bits to words
    unsigned int words = bits >> 5;

    // If there was a remainder, add an extra word
    if ((bits & 0x1F) != 0)
    {
        words++;
    }

    return words;
}

//! \brief Loops through bitfield and calls function-like for each bit which is set
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
//! \param[in] processBitFunction Function-like to call whenever a set bit is encountered
template<typename F>
inline void ForEach(const uint32_t *b, unsigned int s, F processBitFunction)
{
  // While we have bits left to process
  unsigned int remaining_bits = s;
  while (remaining_bits > 0)
  {
    // Determine how many bits are in the next word of the bitfield.
    unsigned int remaining_word_bits = (remaining_bits > 32) ? 32 : remaining_bits;

    // Load the next word of the bitfield
    uint32_t word = *b++;

    // While there are still bits left
    while (remaining_word_bits > 0)
    {
      // Work out how many bits we can skip
      // XXX: The GCC documentation claims that `__builtin_clz(0)` is
      // undefined, but the ARM instruction it uses is defined such that:
      // CLZ 0x00000000 is 32
      unsigned int skip = __builtin_clz(word);

      // If `skip` is NOT less than `reamining_word_bits` then there are
      // either no bits left in the word (`skip` == 32) or the first
      // `1` in the word is beyond the range of bits we care about anyway.
      if (skip < remaining_word_bits)
      {
        // Call process bit function
        processBitFunction(s - remaining_bits);

        // Prepare to test the bit after the one we just processed.
        skip++;                       // Skip the bit we just decoded
        remaining_bits -= skip;       // Reduce the number of bits left
        remaining_word_bits -= skip;  // and the number left in this word.
        word <<= skip;                // Shift out processed bits
      }
      // Otherwise, there are no bits left in this word
      else
      {
        remaining_bits -= remaining_word_bits;  // Reduce the number of remaining bits
        break;
      }
    }
  }
}

//! \brief Prints a bit_field as ones and zeros.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
void PrintBits(char *stream, uint32_t *b, unsigned int s);

//! \brief Prints a bit_field as a sequence of hexadecimal characters.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.

void Print(char *stream, uint32_t *b, unsigned int s);
} // namespace BitField
} // namespace Common