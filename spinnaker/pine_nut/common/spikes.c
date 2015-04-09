/*
 * spikes.c
 *
 *
 *  SUMMARY
 *    Incoming spike handling for SpiNNaker neural modelling
 *
 *    The essential feature of the buffer used in this impementation is that it
 *    requires no critical-section interlocking --- PROVIDED THERE ARE ONLY TWO
 *    PROCESSES: a producer/consumer pair. If this is changed, then a more
 *    intricate implementation will probably be required, involving the use
 *    of enable/disable interrupts.
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *    
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "common-impl.h"
#include "spikes_impl.h"

#ifdef DEBUG
#include "spin-print.h"
#endif /*DEBUG*/

spike_t*   buffer;
uint buffer_size;

index_t   output;
index_t   input;
counter_t overflows;
counter_t underflows;

// initialize_spike_buffer
//
// This function initializes the input spike buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.

void initialize_spike_buffer (uint size)
{
  buffer = (spike_t *) sark_alloc(1, size * sizeof(spike_t));
  buffer_size = size;
  input      = size - 1;
  output     = 0;
  overflows  = 0;
  underflows = 0;
}

#ifdef DEBUG
void print_buffer (void)
{
  counter_t n = allocated();
  index_t   a;

  printf ("buffer: input = %3u, output = %3u elements = %3u\n",
	  input, output, n);
  printf ("------------------------------------------------\n");
  
  for ( ; n > 0; n--) {
    a = (input + n) % IN_SPIKE_SIZE;
    printf ("  %3u: %08x\n", a, buffer [a]);
  }
 
  printf ("------------------------------------------------\n");
}
#endif /*DEBUG*/
