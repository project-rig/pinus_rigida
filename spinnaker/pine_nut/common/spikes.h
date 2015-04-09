#ifndef SPIKES_IMPL_H
#define SPIKES_IMPL_H

extern spike_t*   buffer;
extern uint buffer_size;

extern index_t   output;
extern index_t   input;
extern counter_t overflows;
extern counter_t underflows;


// The following two functions are used to access the locally declared
// variables.

static inline counter_t buffer_overflows() { return (overflows);  }
static inline counter_t buffer_underflows() { return (underflows); }

// unallocated
//
// Returns the number of buffer slots currently unallocated

static inline counter_t unallocated ()
{ 
  return ((input - output) % buffer_size); 
}

// allocated
//
// Returns the number of buffer slots currently allocated

static inline counter_t allocated ()
{ 
  return ((output - input - 1) % buffer_size); 
}

// The following two functions are used to determine whether a
// buffer can have an element extracted/inserted respectively.

static inline bool non_empty()
{ 
  return (allocated() > 0);
}

static inline bool non_full()
{
  return (unallocated () > 0); 
}

#define peek_next(a) ((a - 1) % buffer_size)

#define next(a) do {(a) = peek_next(a);} while (false)

static inline bool add_spike(spike_t e)
{
  bool success = non_full();

  if (success) {
    buffer [input] = e;
    next (input);
  }
  else
    overflows++;

  return (success);
}

static inline bool next_spike (spike_t* e)
{
  bool success = non_empty();

  if (success) {
    next (output);
    *e = buffer [output];
  }
  else
    underflows++;

  return (success);
}

static inline bool get_next_spike_if_equals(spike_t s)
{
  if (non_empty()) 
  {
    uint peek_output = peek_next(output);
    if (buffer [peek_output] == s) 
    {
      output = peek_output;
      return true;
    }
  }
  return false;
}

#endif  // SPIKES_IMPL_H