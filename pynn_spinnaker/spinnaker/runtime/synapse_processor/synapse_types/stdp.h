#pragma once

// Standard includes
#include <cstdint>

// Common includes
#include "../../common/log.h"

//-----------------------------------------------------------------------------
// SynapseProcessor::SynapseTypes::STDP
//-----------------------------------------------------------------------------
namespace SynapseProcessor
{
namespace SynapseTypes
{
template<typename C, typename W, unsigned int D, unsigned int I,
         typename Timing, typename Weight, typename SynapseStructure,
         unsigned int T>
class STDP
{
public:
  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  // One word for a synapse-count and 1024 synapses
  static const unsigned int MaxRowWords = 1025;

  //-----------------------------------------------------------------------------
  // Public methods
  //-----------------------------------------------------------------------------
  template<typename F, typename E>
  bool ProcessRow(uint tick, uint32_t (&dmaBuffer)[MaxRowWords], bool flush,
                  F applyInputFunction, E addDelayRowFunction)
  {
    LOG_PRINT(LOG_LEVEL_TRACE, "\tProcessing STDP row with %u synapses",
              dmaBuffer[0]);

    // If this row has a delay extension, call function to add it
    if(dmaBuffer[1] != 0)
    {
      addDelayRowFunction(dmaBuffer[1] + tick, dmaBuffer[2]);
    }

    // Get last pre-synaptic event from event history
    const uint32_t lastPreTick = dmaBuffer[3];
    const Timing::PreTrace lastPreTrace = dmaBuffer[4];

    // Calculate new pre-trace
    const auto newPreTrace = m_Timing.UpdatePreTrace(tick, lastPreTrace,
                                                     lastPreTick, flush);

    const C *controlWords = //(T*)&dmaBuffer[3];
    SynapseStructure::PlasticSynapse *plasticWords = //(
    const uint32_t count = dmaBuffer[0];
    for(; count > 0; count--)
    {
      // Get the next control word from the synaptic_row
      // (should autoincrement pointer in single instruction)
      const uint32_t controlWord = *controlWords++;

      // Extract control word components
      const uint32_t delayDendritic = GetDelay(controlWord);
      const uint32_t delayAxonal = 0;
      const uint32_t postIndex = GetIndex(controlWord);

      // Create update state from next plastic word
      SynapseStructure updateState(*plasticWords);

      // Apply axonal delay to last presynaptic spike tick
      const uint32_t delayedLastPreTick = lastPreTick + delayAxonal;

      // Get the post-synaptic window of events to be processed
      const uint32_t windowBeginTick = (delayedLastPreTick >= delayDendritic) ?
        (delayedLastPreTick - delayDendritic) : 0;
      const uint32_t windowEndTick = tick + delayAxonal - delayDendritic;

      // Get post event history within this window
      auto postWindow = m_PostEventHistory[postIndex].GetWindow(windowBeginTick,
                                                                windowEndTick);

      //log_debug("\tPerforming deferred synapse update at time:%u", time);
      //log_debug("\t\tbegin_time:%u, end_time:%u - prev_time:%u, num_events:%u",
      //    window_begin_time, window_end_time, post_window.prev_time,
      //    post_window.num_events);

      // Process events in post-synaptic window
      while (postWindow.GetNumEvents() > 0)
      {
        const uint32_t delayedPostTick = postWindow.GetNextTime() + delayDendritic;

        //log_debug("\t\tApplying post-synaptic event at delayed time:%u\n",
        //     delayed_post_time);

        // Apply post-synaptic spike to state
        m_Timing.ApplyPostSpike(updateState,
                                delayedPostTick, postWindow.GetNextTrace(),
                                delayedLastPreTick, lastPreTrace,
                                postWindow.GetPrevTime(), postWindow.GetPrevTrace());

        // Go onto next event
        postWindow.Next(delayedPostTick);
      }

      // If this isn't a flush, apply spike to state
      if(!flush)
      {
          const uint32_t delayedPreTick = tick + delayAxonal;
          //log_debug("\t\tApplying pre-synaptic event at time:%u last post time:%u\n",
          //          delayed_pre_time, post_window.prev_time);

          // Apply pre-synaptic spike to state
          m_Timing.ApplyPreSpike(updateState,
                                 delayedPreTick, newPreTrace,
                                 delayedLastPreTick, lastPreTrace,
                                 postWindow.GetPrevTime(), postWindow.GetPrevTrace());
      }


      // Calculate final state after all updates
      auto finalState = updateState.CalculateFinalState(m_Weight);

      // If this isn't a flush, add weight to ring-buffer
      if(!flush)
      {
        applyInputFunction(delay + tick,
          index, finalState.GetWeight());

      }
      
      // Write back updated synaptic word to plastic region
      *plasticWords++ = finalState.GetPlasticSynapse();
    }

    return true;
  }

  unsigned int GetRowWords(unsigned int rowSynapses)
  {
    // Three header word and a synapse
    //return 3 + ((rowSynapses * sizeof(T)) / 4);
  }

private:
  //-----------------------------------------------------------------------------
  // Typedefines
  //-----------------------------------------------------------------------------
  typedef PostEventHistoryBase<Timing::PostTrace, T> PostEventHistory;

  //-----------------------------------------------------------------------------
  // Constants
  //-----------------------------------------------------------------------------
  static const C DelayMask = ((1 << D) - 1);
  static const C IndexMask = ((1 << I) - 1);

  //-----------------------------------------------------------------------------
  // Private static methods
  //-----------------------------------------------------------------------------
  static C GetIndex(C word){ return (word & IndexMask); }
  static C GetDelay(C word){ return ((word >> I) & DelayMask); }

  //-----------------------------------------------------------------------------
  // Members
  //-----------------------------------------------------------------------------
  Timing m_Timing;
  Weight m_Weight;

  PostEventHistory<Timing::PostTrace, T> m_PostEventHistory[MaxNeurons];
};
} // SynapseTypes
} // SynapseProcessor