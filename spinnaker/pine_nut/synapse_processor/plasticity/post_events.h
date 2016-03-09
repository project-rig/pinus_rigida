#pragma once

namespace SynapseProcessor
{
namespace Plasticity
{
//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::PostEventWindow
//-----------------------------------------------------------------------------
template<T>
class PostEventWindow
{
public:
  PostEventWindow(T prevTrace, uint32_t prevTime, const T *nextTrace, const uint32_t *nextTime, unsigned int numEvents)
    : m_PrevTrace(prevTrace), m_PrevTime(prevTime), m_NextTrace(nextTrace), m_NextTime(nextTime), m_NumEvents(numEvents)
  {
  }

  //-----------------------------------------------------------------------------
  // Public API
  //-----------------------------------------------------------------------------
  void Next(uint32_t delayed_time)
  {
    // Update previous time and increment next time
    m_PrevTime = delayed_time;
    m_PrevTrace = *m_NextTrace++;

    // Go onto next event
    m_NextTime++;

    // Decrement remining events
    m_NumEvents--;
  }

  T GetPrevTrace() const
  {
    return m_PrevTrace;
  }

  uint32_t GetPrevTime() const
  {
    return m_PrevTime;
  }

  T GetNextTrace() const
  {
    return *m_NextTrace;
  }

  uint32_t GetNextTime() const
  {
    return m_NextTime;
  }

  unsigned int GetNumEvents() const
  {
    return m_NumEvents;
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  T m_PrevTrace;
  uint32_t m_PrevTime;
  const T *m_NextTrace;
  const uint32_t *m_NextTime;
  unsigned int m_NumEvents;
};

//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::PostEventHistory
//-----------------------------------------------------------------------------
template<T, N>
class PostEventHistory
{
public:

  PostEventWindow<T> GetWindow(uint32_t beginTime, uint32_t endTime)
  {
    // Start at end event - beyond end of post-event history
    const uint32_t count = m_CountMinusOne + 1;
    const uint32_t *endEventTime = m_Times + count;
    const uint32_t *eventTime = endEventTime;

    const uint32_t *nextTime;
    do
    {
      // Cache pointer to this event as potential
      // Next event and go back one event
      // **NOTE** next_time can be invalid
      nextTime = eventTime--;

      // If this event is still in the future, set it as the end
      if (*eventTime > endTime)
      {
        endEventTime = eventTime;
      }
    }
    // Keep looping while event occured after start
    // Of window and we haven't hit beginning of array
    while (*eventTime > beginTime && eventTime != m_Times);

    // Calculate number of events
    unsigned int numEvents = (endEventTime - nextTime);
    return PostEventWindow(*(window.next_trace - 1), *eventTime,
                           (end_event_trace - numEvents),
                           nextTime, numEvents);
  }

  void Add(uint32_t time, T trace)
  {
    if (m_CountMinusOne < (N - 1))
    {
      // If there's still space, store time at current end
      // and increment count minus 1
      const uint32_t new_index = ++m_CountMinusOne;
      m_Times[new_index] = time;
      m_Traces[new_index] = trace;
    }
    else
    {
        // Otherwise Shuffle down elements
        // **NOTE** 1st element is always an entry at time 0
        for (uint32_t e = 2; e < N; e++)
        {
            m_Times[e - 1] = m_Times[e];
            m_Traces[e - 1] = m_Traces[e];
        }

        // Stick new time at end
        m_Times[N - 1] = time;
        m_Traces[N - 1] = trace;
    }
  }
private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_CountMinusOne;
  uint32_t m_Times[N];
  T m_Traces[N];
};
}
}