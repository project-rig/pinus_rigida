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

#ifndef BIT_FIELD_H
#define BIT_FIELD_H

// Standard includes
#include <stdint.h>
#include <stdbool.h>

// Sark includes
#include <sark.h>

//-----------------------------------------------------------------------------
// Typedefines
//-----------------------------------------------------------------------------
typedef uint32_t *bit_field_t;

//-----------------------------------------------------------------------------
// Inline functions
//-----------------------------------------------------------------------------
//! \brief This function tests a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The size of the bit_field.
//! \return The function returns true if the bit is set or false otherwise.
static inline bool bit_field_test_bit(bit_field_t b, uint n)
{
    return ((b [n >> 5] & (1 << (n & 0x1F))) != 0); 
}

//! \brief This function clears a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The size of the bit_field.
static inline void bit_field_clear_bit(bit_field_t b, uint n)
{
    b [n >> 5] &= ~(1 << (n & 0x1F)); 
}

//! \brief This function sets a particular bit of a bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] n The bit in the bit_field of interest.
static inline void bit_field_set_bit(bit_field_t b, uint n)
{ 
    b [n >> 5] |= (1 << (n & 0x1F)); 
}

//! \brief This function negates the bits of an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
static inline void bit_field_flip(bit_field_t b, uint s)
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
static inline void bit_field_and(bit_field_t b1, bit_field_t b2, uint s)
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
static inline void bit_field_or(bit_field_t b1, bit_field_t b2, uint s)
{ 
    for ( ; s > 0; s--) 
    {
        b1 [s-1] |= b2 [s-1]; 
    }
}

//! \brief This function clears an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
static inline void bit_field_clear(bit_field_t b, uint s)
{ 
    for ( ; s > 0; s--) 
    {
        b [s-1] = 0; 
    }
}

//! \brief This function sets an entire bit_field.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
static inline void bit_field_set(bit_field_t b, uint s)
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
static inline bool bit_field_is_empty(bit_field_t b, uint s)
{
    bool empty = true;

    for ( ; s > 0; s--)
    {
        empty = empty && (b [s-1] == 0);
    }
    
    return (empty);
}

//! \brief Testing whether a bit_field is non-empty, _i.e._ if there is at
//! least one bit set.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
//! \return The function returns true if at least one bit is set; otherwise false.
static inline bool bit_field_is_nonempty(bit_field_t b, uint s)
{
    return !bit_field_is_empty(b, s); 
}

//! \brief A function that calculates the size of a bit_field to hold 'bits'
//! bits.
//! \param[in] bits The number of bits required for this bit_field.
//! \return The size (or number of words) in the bit_field.
static inline uint bit_field_get_word_size(uint bits)
{
    // **NOTE** in floating point terms this is ceil(num_neurons / 32)
    const uint bits_to_words_shift = 5;
    const uint bits_to_words_remainder = (1 << bits_to_words_shift) - 1;

    // Down shift number of bits to words
    uint words = bits >> bits_to_words_shift;

    // If there was a remainder, add an extra word
    if ((bits & bits_to_words_remainder) != 0)
    {
        words++;
    }

    return words;
}

//! \brief Prints a bit_field as ones and zeros.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
void bit_field_print_bits(bit_field_t b, uint s);

//! \brief Prints a bit_field as a sequence of hexadecimal characters.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.

void bit_field_print(bit_field_t b, uint s);

#endif // BIT_FIELD_H
