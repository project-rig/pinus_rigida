#pragma once

namespace SynapseProcessor
{
namespace Plasticity
{
//-----------------------------------------------------------------------------
// SynapseProcessor::Plasticity::PostEventHistoryNearest
//-----------------------------------------------------------------------------
template<unsigned int NumEntries>
class PostEventHistoryNearest
{
public:
  //-----------------------------------------------------------------------------
  // Window
  //-----------------------------------------------------------------------------
  class Window
  {
  public:
    Window(uint32_t prevTime, const uint32_t *nextTime, unsigned int numEvents)
      : m_PrevTime(prevTime), m_NextTime(nextTime), m_NumEvents(numEvents)
    {
    }

    //-----------------------------------------------------------------------------
    // Public API
    //-----------------------------------------------------------------------------
    void Next(uint32_t delayed_time)
    {
      // Update previous time and increment next time
      m_PrevTime = delayed_time;

      // Go onto next event
      m_NextTime++;

      // Decrement remining events
      m_NumEvents--;
    }

    uint32_t GetPrevTime() const
    {
      return m_PrevTime;
    }

    uint32_t GetNextTime() const
    {
      return *m_NextTime;
    }

    unsigned int GetNumEvents() const
    {
      return m_NumEvents;
    }

  private:
    //-----------------------------------------------------------------------------
    // Members
    //-----------------------------------------------------------------------------
    uint32_t m_PrevTime;
    const uint32_t *m_NextTime;
    unsigned int m_NumEvents;
  };

  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  Window GetWindow(uint32_t beginTime, uint32_t endTime)
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

    return Window(*eventTime, nextTime, numEvents);
  }

  void Add(uint32_t time)
  {
    // If there is space in the history
    if (m_CountMinusOne < (NumEntries - 1))
    {
      // If there's still space, store time at current end
      // and increment count minus 1
      m_Times[++m_CountMinusOne] = time;
    }
    else
    {
        // Otherwise Shuffle down elements
        // **NOTE** 1st element is always an entry at time 0
        for (uint32_t e = 2; e < NumEntries; e++)
        {
            m_Times[e - 1] = m_Times[e];
        }

        // Stick new time at end
        m_Times[NumEntries - 1] = time;
    }
  }

  uint32_t GetLastTime() const
  {
    return m_Times[m_CountMinusOne];
  }

private:
  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  uint32_t m_CountMinusOne;
  uint32_t m_Times[NumEntries];
};
}
}