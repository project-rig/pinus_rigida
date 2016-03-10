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

#include "bit_field.h"

// Common includes
#include "spinnaker.h"

//-----------------------------------------------------------------------------
// Common::BitField
//-----------------------------------------------------------------------------
namespace Common
{
namespace BitField
{
//! \brief This function prints out an individual word of a bit_field,
// as a sequence of ones and zeros.
//! \param[in] e The word of a bit_field to be printed.
void PrintWord(char *stream, uint32_t e)
{
    for (unsigned int i = 32 ; i > 0; i--)
    {
      io_printf(stream, "%c", ((e & 0x1) == 0) ? '0': '1');
      e = e >> 1;
    }
}

//! \brief This function prints out an entire bit_field,
// as a sequence of ones and zeros.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
void PrintBits(char *stream, uint32_t *b, unsigned int s)
{
    for(unsigned int i = 0; i < s; i++)
    {
      PrintWord(stream, b[i]);
    }
}

//! \brief This function prints out an entire bit_field,
// as a sequence of hexadecimal numbers, one per line.
//! \param[in] b The sequence of words representing a bit_field.
//! \param[in] s The size of the bit_field.
void Print(char *stream, uint32_t *b, unsigned int s)
{
    for(unsigned int i = 0; i < s; i++)
    {
      io_printf(stream, "%08x",b[i]);
    }
}
} // namespace BitField
} // namespace Common
